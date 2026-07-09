"""Blades adaptado: la primera implementación de SistemaDeReglas (paso 3).

Vive del lado del enchufe, nunca en el núcleo (ADR-002): Codex sin Blades sigue
siendo Codex. El acoplamiento con el motor cognitivo es la gracia del sistema:
posición y efecto NO los decide el LLM ni el jugador — los calcula el motor desde
el cristal del ser (su loadout ante la acción y la afinidad de cada meme), así el
mismo riesgo es distinto para cada quien.

La tirada es la de Blades: d6, manda el dado más alto — 6 limpio, 4-5 éxito con
costo, 1-3 mala consecuencia. Ningún resultado puede ser "no pasa nada". Con rango
cero rige la regla del cero: se tiran dos dados y manda el MENOR. Antes de tirar,
el jugador puede pagar 2 de stress por UNA mejora (dado extra, posición o efecto).

Los umbrales de posición y efecto son PROVISIONALES: se tunean viendo el sistema
en juego real, no antes (por eso son constantes nombradas y los puntajes quedan en
`Evaluacion.detalles` para inspección).
"""

from __future__ import annotations

import logging
import random
from pathlib import Path
from string import Template
from typing import Annotated

from pydantic import BaseModel, Field

from .llm import ClienteLLM, ErrorLLM
from .modelos import TipoMeme
from .reglas import (
    AccionDeclarada,
    AvanzarClock,
    CategoriaResultado,
    ContextoAccion,
    EfectoMecanico,
    Empuje,
    Evaluacion,
    NivelEfecto,
    PagarStress,
    Posicion,
    Resolucion,
)

logger = logging.getLogger(__name__)

TEMPLATE_NARRACION = Path(__file__).parent.parent / "templates" / "narracion_score.txt"

# La categoría le llega al LLM como rúbrica EXPLÍCITA: sin esto tiende a narrar
# éxitos limpios siempre, porque es lo más cómodo de escribir (tiradas.md).
_RUBRICAS = {
    CategoriaResultado.LIMPIO: (
        "Resultado: éxito limpio. Narrá el logro sin costo — igual es un evento: "
        "algo cambia, algo se abre, el personaje lo siente."
    ),
    CategoriaResultado.CON_COSTO: (
        "Resultado: éxito con costo. Narrá el éxito Y la complicación que llega con "
        "él (un costo emocional, de relación, de recurso, o una huella que va a "
        "volver a morder más adelante)."
    ),
    CategoriaResultado.MALA_CONSECUENCIA: (
        "Resultado: mala consecuencia. La acción NO se logra y además hay daño: el "
        "personaje queda peor que antes y algo del mundo empieza a moverse en contra."
    ),
}

# --- Constantes provisionales del cálculo de posición y efecto (tunear jugando) ---
AFINIDAD_NEUTRA = 0.5          # un meme ni a favor ni en contra de la acción
UMBRAL_PF_CONFLICTO = 0.35     # una PF por debajo de esto choca con la acción
FACTOR_CONFLICTO_PF = 2.0      # y su choque pesa el doble: la identidad manda
CONTROLADA_DESDE = 0.5         # score de favorabilidad para posición controlada
DESESPERADA_HASTA = -0.5       # ...y para desesperada; en el medio, arriesgada
UMBRAL_MEME_RELEVANTE = 0.75   # afinidad para que un meme cuente para el efecto
RELEVANTES_PARA_GRANDE = 3     # 3+ memes relevantes → grande; 1-2 → estándar; 0 → limitado

COSTO_EMPUJE = 2               # stress que paga cada empuje (uno solo por tirada)
SEGMENTOS_MALA = 1             # cuánto avanza el clock de amenaza una mala consecuencia
SEGMENTOS_MALA_DESESPERADA = 2  # ...y cuánto si además la posición era desesperada

_ORDEN_POSICION = [Posicion.DESESPERADA, Posicion.ARRIESGADA, Posicion.CONTROLADA]
_ORDEN_EFECTO = [NivelEfecto.LIMITADO, NivelEfecto.ESTANDAR, NivelEfecto.GRANDE]


class HojaMecanica(BaseModel):
    """La hoja del sistema de reglas: semilla en `seres/<id>/hoja_reglas.json`,
    separada del cuerpo cognitivo (ADR-007: no viaja con el alma). El mundo define
    sus propias acciones; el motor no trae una lista fija."""

    ser_id: str
    stress_max: int = 9
    acciones: dict[str, Annotated[int, Field(ge=0, le=4)]]  # acción → rango (dados)


def _subir(nivel, orden):
    """Sube un nivel en la escala dada, saturando en el tope."""
    return orden[min(orden.index(nivel) + 1, len(orden) - 1)]


class SistemaBlades:
    """Implementa `SistemaDeReglas`. El RNG se inyecta para tests con dados sembrados."""

    def __init__(
        self,
        hojas: dict[str, HojaMecanica],
        clock_amenaza_id: str,
        rng: random.Random | None = None,
    ):
        self.hojas = hojas
        self.clock_amenaza_id = clock_amenaza_id
        self.rng = rng or random.Random()

    def evaluar(self, accion: AccionDeclarada, contexto: ContextoAccion) -> Evaluacion:
        """Calcula los términos de la tirada desde el cristal: los memes activos
        afines a la acción mejoran, las PF en conflicto empeoran."""
        hoja = self.hojas.get(accion.ser_id)
        if hoja is None:
            raise ValueError(f"El ser no tiene hoja mecánica, no participa de Scores: {accion.ser_id}")

        apoyo, conflicto_pf = 0.0, 0.0
        for meme in contexto.loadout.seleccionados:
            afinidad = contexto.afinidades.get(meme.id, AFINIDAD_NEUTRA)
            if meme.tipo == TipoMeme.FUNDACIONAL:
                if afinidad < UMBRAL_PF_CONFLICTO:
                    conflicto_pf += (UMBRAL_PF_CONFLICTO - afinidad) * FACTOR_CONFLICTO_PF
            else:
                apoyo += afinidad - AFINIDAD_NEUTRA

        score = apoyo - conflicto_pf
        if score >= CONTROLADA_DESDE:
            posicion = Posicion.CONTROLADA
        elif score <= DESESPERADA_HASTA:
            posicion = Posicion.DESESPERADA
        else:
            posicion = Posicion.ARRIESGADA

        relevantes = sum(
            1 for af in contexto.afinidades.values() if af >= UMBRAL_MEME_RELEVANTE
        )
        if relevantes >= RELEVANTES_PARA_GRANDE:
            efecto = NivelEfecto.GRANDE
        elif relevantes >= 1:
            efecto = NivelEfecto.ESTANDAR
        else:
            efecto = NivelEfecto.LIMITADO

        return Evaluacion(
            accion=accion,
            posicion=posicion,
            efecto=efecto,
            dados=hoja.acciones.get(accion.accion, 0),
            detalles={"apoyo": apoyo, "conflicto_pf": conflicto_pf, "score": score,
                      "memes_relevantes": float(relevantes)},
        )

    def tirar(
        self,
        evaluacion: Evaluacion,
        contexto: ContextoAccion,
        empuje: Empuje | None = None,
    ) -> Resolucion:
        """Tira los dados con los términos de la evaluación (más el empuje, si lo
        hay) y devuelve la resolución con sus efectos. No toca estado: los efectos
        los aplica el motor por la puerta única (`reglas.aplicar_efectos`)."""
        efectos: list[EfectoMecanico] = []
        if empuje is not None:
            hoja = self.hojas[evaluacion.accion.ser_id]
            stress = contexto.estado_reglas.get("stress", 0.0)
            if stress + COSTO_EMPUJE > hoja.stress_max:
                raise ValueError(
                    f"Sin stress disponible para empujar: {stress}/{hoja.stress_max}"
                )
            efectos.append(PagarStress(ser_id=evaluacion.accion.ser_id, cantidad=COSTO_EMPUJE))
            if empuje == Empuje.MEJORAR_POSICION:
                evaluacion = evaluacion.model_copy(
                    update={"posicion": _subir(evaluacion.posicion, _ORDEN_POSICION)}
                )
            elif empuje == Empuje.MEJORAR_EFECTO:
                evaluacion = evaluacion.model_copy(
                    update={"efecto": _subir(evaluacion.efecto, _ORDEN_EFECTO)}
                )

        dados = evaluacion.dados + (1 if empuje == Empuje.DADO_EXTRA else 0)
        if dados == 0:
            # Regla del cero: sin entrenamiento igual hay chance — dos dados, manda el menor.
            tirados = [self.rng.randint(1, 6), self.rng.randint(1, 6)]
            manda = min(tirados)
        else:
            tirados = [self.rng.randint(1, 6) for _ in range(dados)]
            manda = max(tirados)

        if manda == 6:
            categoria = CategoriaResultado.LIMPIO
        elif manda >= 4:
            categoria = CategoriaResultado.CON_COSTO
        else:
            categoria = CategoriaResultado.MALA_CONSECUENCIA
            segmentos = (
                SEGMENTOS_MALA_DESESPERADA
                if evaluacion.posicion == Posicion.DESESPERADA
                else SEGMENTOS_MALA
            )
            efectos.append(AvanzarClock(clock_id=self.clock_amenaza_id, segmentos=segmentos))

        return Resolucion(
            evaluacion=evaluacion,
            empuje=empuje,
            dados_tirados=tirados,
            categoria=categoria,
            efectos=efectos,
        )


def narrar_resolucion(cliente: ClienteLLM, resolucion: Resolucion, contexto: ContextoAccion) -> str:
    """Narra el resultado de la tirada. El motor ya decidió TODO (ADR-001): el LLM
    recibe la categoría como rúbrica explícita y solo pone la escena. Si el LLM
    falla, queda la crónica mecánica con log (ADR-005): la tirada ya ocurrió y sus
    efectos son reales, el Score no se pierde."""
    ev = resolucion.evaluacion
    pf = [m for m in contexto.loadout.seleccionados if m.tipo == TipoMeme.FUNDACIONAL]
    activos = [m for m in contexto.loadout.seleccionados if m.tipo != TipoMeme.FUNDACIONAL]
    prompt = Template(TEMPLATE_NARRACION.read_text(encoding="utf-8")).substitute(
        ser_id=ev.accion.ser_id,
        descripcion=ev.accion.descripcion,
        posicion=ev.posicion.value,
        efecto=ev.efecto.value,
        rubrica=_RUBRICAS[resolucion.categoria],
        pf="\n".join(f"- {m.texto}" for m in pf) or "- (ninguna)",
        memes_activos="\n".join(f"- {m.texto}" for m in activos) or "- (ninguno)",
    )
    try:
        narracion = cliente.responder(prompt).strip()
    except ErrorLLM as e:
        narracion = ""
        logger.warning("El LLM falló y el Score queda sin narración literaria: %s", e)
    if not narracion:
        # La crónica mínima: qué se intentó y qué salió, en palabras del mundo.
        categoria = resolucion.categoria.value.replace("_", " ")
        return (
            f"{ev.accion.ser_id} intenta: {ev.accion.descripcion} "
            f"(posición {ev.posicion.value}, efecto {ev.efecto.value}) — {categoria}."
        )
    return narracion
