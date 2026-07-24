"""El SPECULUM mínimo: el ser que mira su propia trayectoria (mejora 05).

El órgano de la identidad del núcleo irrenunciable (docs/VISION_FASE0.md),
adaptado del prototipo de Fray Tomás (speculum.py + la fricción de
cambio_biografico.py). El ser lee su trayectoria REGISTRADA —qué memes
movilizó y cuánto, qué tensiones se le repiten, qué recibió y cómo lo
deformó— y produce dos cosas: una reflexión breve en primera persona
(quién estoy siendo) y PROPUESTAS tipadas de cambio chico.

La fricción heredada, en tres reglas que este módulo hace cumplir:
  - El degradé: ningún ajuste mueve más de DELTA_MAXIMO puntos por propuesta.
  - Las PF son INTOCABLES por esta vía: si una piedra tambalea, la reflexión
    puede DECIRLO (material para futuras crisis biográficas), jamás proponer
    cambiarla.
  - El LLM propone, el motor valida (estos modelos), el autor dispone: nada
    se aplica sin aprobación explícita en el Taller.

El prompt vive en templates/speculum.txt, editable como los demás.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path
from string import Template
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from .llm import ClienteLLM, ErrorLLM
from .modelos import EstadoMeme, Ser, TipoMeme
from .prompts import anotar_funcion

logger = logging.getLogger(__name__)

TEMPLATE_SPECULUM = Path(__file__).parent.parent / "templates" / "speculum.txt"
INTENTOS = 2      # el original + un reintento con feedback (patrón de derivacion.py)
RECORTE = 160     # las citas de la bitácora entran recortadas: evidencia, no archivo
TRANSMISIONES_RECIENTES = 5   # cuántas deformaciones recientes ve el espejo

# La regla del degradé de Fray Tomás: nadie se refunda en una noche.
DELTA_MAXIMO = 2.0
# Un experimental nace humilde: es una sospecha sobre uno mismo, no una certeza.
PESO_MAX_EXPERIMENTAL = 3.0
# Mirarse no es refundarse: pocas propuestas por mirada.
MAX_PROPUESTAS = 3
# Umbral de material: sin esta acumulación de uso real, la reflexión es humo
# y el Taller no llama al LLM (movilizaciones totales del ser, no por meme).
MINIMO_MOVILIZACIONES = 10

# Los ids que propone el LLM van cortos, en minúsculas, sin espacios (misma
# regla que la derivación de seres; se repite acá porque codex no importa
# de taller, la capa va al revés).
ID_PROPUESTO = re.compile(r"^[a-z0-9_]+$")


class PropuestaAjuste(BaseModel):
    """Subir o bajar el peso VIVO de un meme existente, poco (el degradé)."""

    tipo: Literal["ajustar_peso"]
    meme_id: str
    delta: float
    justificacion: str = Field(min_length=1)   # citando la evidencia de la trayectoria

    @field_validator("delta")
    @classmethod
    def _delta_acotado(cls, v: float) -> float:
        if v == 0:
            raise ValueError("un ajuste de 0 no propone nada")
        if abs(v) > DELTA_MAXIMO:
            raise ValueError(
                f"el degradé no permite mover más de {DELTA_MAXIMO} puntos por propuesta"
            )
        return v


class PropuestaExperimental(BaseModel):
    """Un meme experimental NUEVO para probarse: una sospecha, no una certeza."""

    tipo: Literal["proponer_experimental"]
    meme_id: str
    texto: str = Field(min_length=1)
    peso_inicial: float = Field(gt=0, le=PESO_MAX_EXPERIMENTAL)
    costo: int = Field(ge=0)
    justificacion: str = Field(min_length=1)

    @field_validator("meme_id")
    @classmethod
    def _id_bien_formado(cls, v: str) -> str:
        if not ID_PROPUESTO.match(v):
            raise ValueError(f"id inválido (minúsculas y guiones bajos): {v!r}")
        return v


Propuesta = Annotated[
    PropuestaAjuste | PropuestaExperimental, Field(discriminator="tipo")
]


class Mirada(BaseModel):
    """La respuesta completa del espejo: quién estoy siendo + qué me ajustaría.

    Cero propuestas es válido: si la evidencia no pide cambios, no se inventan."""

    reflexion: str = Field(min_length=1)   # primera persona, sale de la evidencia
    propuestas: list[Propuesta] = Field(default_factory=list, max_length=MAX_PROPUESTAS)


def validar_contra_ser(mirada: Mirada, ser: Ser) -> None:
    """Lo que el esquema solo no puede chequear: que cada propuesta hable de
    ESTE ser. Levanta ValueError con mensaje claro (alimenta el reintento con
    feedback, patrón de derivacion.py). No toca nada: solo valida."""
    memes = {m.id: m for m in ser.memes}
    for p in mirada.propuestas:
        if p.tipo == "ajustar_peso":
            meme = memes.get(p.meme_id)
            if meme is None:
                raise ValueError(f"la propuesta ajusta un meme que el ser no tiene: {p.meme_id!r}")
            if meme.tipo == TipoMeme.FUNDACIONAL:
                raise ValueError(
                    f"{p.meme_id!r} es una piedra fundacional: intocable por esta vía "
                    "(si tambalea, decilo en la reflexión)"
                )
        else:   # proponer_experimental
            if p.meme_id in memes:
                raise ValueError(f"el id propuesto ya existe en el ser: {p.meme_id!r}")


# ----- La trayectoria: lo ya registrado, vuelto espejo -----


class Trayectoria(BaseModel):
    """La materia prima de la mirada: el registro del ser, formateado y contado.

    `movilizaciones` es el total de usos reales del ser (regla 4: movilizado,
    no solo llevado); el umbral de material se mide sobre eso."""

    movilizaciones: int
    texto: str

    @property
    def suficiente(self) -> bool:
        return self.movilizaciones >= MINIMO_MOVILIZACIONES


def _recortar(texto: str) -> str:
    return texto if len(texto) <= RECORTE else texto[: RECORTE - 1] + "…"


def consultar_trayectoria(
    ser: Ser, estado: dict[str, EstadoMeme], bitacora_ser: list[dict]
) -> Trayectoria:
    """Arma el bloque $trayectoria con lo YA registrado — nada se registra acá.

    Tres secciones: el uso real de cada meme (peso semilla → actual, llevado vs
    usado, con el silencio marcado), las grietas que se le repiten (contadas
    sobre las tensiones que la bitácora ya guarda por entrada), y cómo deformó
    lo que le contaron (las transmisiones recientes de su bitácora)."""
    lineas = ["TUS IDEAS Y SU USO REAL (peso al nacer → peso hoy; veces llevada / veces usada):"]
    for m in ser.memes:
        e = estado.get(m.id) or EstadoMeme(meme_id=m.id, peso=m.peso_inicial)
        marca = " — piedra fundacional" if m.tipo == TipoMeme.FUNDACIONAL else ""
        silencio = (
            "  ← la llevás encima y nunca la usaste"
            if e.veces_en_loadout > 0 and e.veces_movilizado == 0
            else ""
        )
        lineas.append(
            f"- «{m.texto}»{marca} — peso {m.peso_inicial:g} → {e.peso:g}; "
            f"llevada {e.veces_en_loadout}, usada {e.veces_movilizado}{silencio}"
        )

    # Las grietas: cada entrada de bitácora ya guarda las tensiones detectadas
    # en ese momento; contar el par (sin importar el orden) da las repetidas.
    conteo: Counter[tuple[str, str]] = Counter()
    textos: dict[tuple[str, str], tuple[str, str]] = {}
    for entrada in bitacora_ser:
        for t in entrada.get("terminos", {}).get("tensiones", []):
            par = tuple(sorted((t["meme_a"], t["meme_b"])))
            conteo[par] += 1
            textos[par] = (t["texto_a"], t["texto_b"])
    lineas.append("")
    lineas.append("TUS GRIETAS (dos ideas tuyas tironeando a la vez, y cuántas veces se registró):")
    if conteo:
        for par, veces in conteo.most_common():
            a, b = textos[par]
            lineas.append(f"- «{a}» ⇄ «{b}» — {veces} veces")
    else:
        lineas.append("- (ninguna registrada)")

    transmisiones = [e for e in bitacora_ser if e.get("tipo") == "transmision"]
    lineas.append("")
    lineas.append("LO QUE TE CONTARON Y CÓMO LO CONTASTE VOS (tu deformación, con la distancia a la verdad):")
    if transmisiones:
        for e in transmisiones[:TRANSMISIONES_RECIENTES]:
            distancia = e.get("terminos", {}).get("distancia_raiz")
            lineas.append(
                f"- te dijeron: «{_recortar(e['entrada'])}»\n"
                f"  vos contás: «{_recortar(e['salida'])}» (distancia {distancia})"
            )
    else:
        lineas.append("- (nadie te contó nada todavía)")

    movilizaciones = sum(e.veces_movilizado for e in estado.values())
    return Trayectoria(movilizaciones=movilizaciones, texto="\n".join(lineas))


# ----- La mirada: el LLM propone, el motor valida -----


def armar_prompt_speculum(ser: Ser, trayectoria: Trayectoria) -> str:
    """Rellena el template. Los topes ($delta_maximo, $peso_max_experimental)
    salen de las constantes de este módulo: template y validación no se desfasan."""
    pf = [m for m in ser.memes if m.tipo == TipoMeme.FUNDACIONAL]
    template = Template(TEMPLATE_SPECULUM.read_text(encoding="utf-8"))
    return template.substitute(
        ser_id=ser.ser_id,
        pf="\n".join(f"- {m.texto}{anotar_funcion(m)}" for m in pf) or "- (ninguna)",
        trayectoria=trayectoria.texto,
        delta_maximo=f"{DELTA_MAXIMO:g}",
        peso_max_experimental=f"{PESO_MAX_EXPERIMENTAL:g}",
    )


def _parsear_mirada(cruda: str, ser: Ser) -> Mirada:
    """Extrae el primer bloque JSON, valida el esquema y valida contra el ser.
    Levanta ValueError/ValidationError con mensaje claro (alimenta el reintento)."""
    inicio, fin = cruda.find("{"), cruda.rfind("}")
    if inicio == -1 or fin <= inicio:
        raise ValueError("la respuesta no contiene un bloque JSON")
    mirada = Mirada(**json.loads(cruda[inicio : fin + 1]))
    validar_contra_ser(mirada, ser)
    return mirada


def mirarse(
    ser: Ser, trayectoria: Trayectoria, cliente: ClienteLLM
) -> tuple[Mirada | None, bool]:
    """El ser se mira: devuelve (mirada, hubo_reintento); mirada None si no se
    pudo (se degrada con log, regla 3). Sin material suficiente NO se llama al
    LLM: la reflexión sin acumulación es humo. Acá no se aplica NADA: las
    propuestas son solo propuestas hasta que el autor disponga en el Taller."""
    if not trayectoria.suficiente:
        logger.info(
            "El SPECULUM de %s no corre: %d movilizaciones (mínimo %d)",
            ser.ser_id, trayectoria.movilizaciones, MINIMO_MOVILIZACIONES,
        )
        return None, False
    prompt = armar_prompt_speculum(ser, trayectoria)
    actual = prompt
    for intento in range(1, INTENTOS + 1):
        try:
            cruda = cliente.responder(actual)
        except ErrorLLM as e:
            # Fallo de infraestructura: reintentar con feedback no ayuda (ADR-005).
            logger.warning("El LLM falló en el SPECULUM de %s: %s", ser.ser_id, e)
            return None, intento > 1
        try:
            return _parsear_mirada(cruda, ser), intento > 1
        except (ValueError, ValidationError) as e:
            logger.warning("Mirada inválida de %s (intento %d): %s", ser.ser_id, intento, e)
            actual = (
                f"{prompt}\n\nTu respuesta anterior no fue válida porque: {e}\n"
                "Respondé SOLO con el JSON pedido, sin texto antes ni después."
            )
    return None, True
