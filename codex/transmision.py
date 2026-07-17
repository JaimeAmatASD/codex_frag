"""La transmisión: cuando un ser le cuenta algo a otro, y el rumor muta.

Es la operación central del paso 2. El ciclo completo de `transmitir`:
el receptor escucha con su cristal activo (su loadout ante lo oído), el LLM propone
cómo lo entendió, el motor valida y registra la versión nueva en el grafo con su
linaje y su distancia a la verdad raíz.

Principio rector (ADR-001): el LLM no decide qué pasó; recibe lo oído y el cristal
del receptor, y devuelve CÓMO ese receptor lo entendió. Si su respuesta no valida
(dos intentos), degradamos con log a "transmisión sin deformación": el receptor
guarda lo que oyó tal cual (regla 3: toda degradación queda anotada).

El prompt vive en templates/mutacion.txt como texto plano con placeholders de
`string.Template` ($nombre): se puede iterar a mano, con llaves y JSON adentro,
sin tocar código ni romper ningún format().
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from string import Template

from pydantic import ValidationError

from .decaimiento import aplicar_contradicciones
from .embeddings import Embeddings
from .grafo_mundo import GrafoMundo
from .hechos import DISTANCIA_NO_MEDIDA, RespuestaMutacion, Version
from .llm import ClienteLLM, ErrorLLM
from .loadout import Loadout, calcular_loadout
from .memetario import Memetario
from .modelos import TipoMeme
from .prompts import anotar_funcion, seccion_tension
from .reloj import RelojDelMundo

logger = logging.getLogger(__name__)

TEMPLATE_MUTACION = Path(__file__).parent.parent / "templates" / "mutacion.txt"
INTENTOS = 2  # el original + un reintento con feedback; después se degrada.
# En la mutación, la grieta debe notarse acá (el $donde de templates/tension.txt).
DONDE_TENSION = "cómo entiende lo que oyó y cómo lo recuenta"


def armar_prompt(receptor_id: str, emisor_id: str, contenido_oido: str, loadout: Loadout) -> str:
    """Rellena el template de mutación con el cristal activo del receptor.

    Los memes no fundacionales se listan con su id entre corchetes porque el LLM
    debe devolver esos ids en `memes_resonantes` (alimentan la regla 4)."""
    pf = [m for m in loadout.seleccionados if m.tipo == TipoMeme.FUNDACIONAL]
    activos = [m for m in loadout.seleccionados if m.tipo != TipoMeme.FUNDACIONAL]
    template = Template(TEMPLATE_MUTACION.read_text(encoding="utf-8"))
    return template.substitute(
        receptor_id=receptor_id,
        emisor_id=emisor_id,
        contenido_oido=contenido_oido,
        pf="\n".join(f"- {m.texto}{anotar_funcion(m)}" for m in pf) or "- (ninguna)",
        memes_activos="\n".join(
            f"- [{m.id}] {m.texto}{anotar_funcion(m)}" for m in activos
        ) or "- (ninguno)",
        tension=seccion_tension(loadout.tensiones, DONDE_TENSION),
    )


def _parsear_respuesta(cruda: str) -> RespuestaMutacion:
    """Extrae el primer bloque JSON de la respuesta (tolerante a texto alrededor)
    y lo valida contra el esquema. Levanta ValueError/ValidationError si no sirve."""
    inicio, fin = cruda.find("{"), cruda.rfind("}")
    if inicio == -1 or fin <= inicio:
        raise ValueError("la respuesta no contiene un bloque JSON")
    return RespuestaMutacion(**json.loads(cruda[inicio : fin + 1]))


def _solo_del_loadout(
    reportados: list[str], loadout: Loadout, receptor_id: str, etiqueta: str
) -> list[str]:
    """Filtra ids reportados por el LLM a los que estaban en el loadout. Se
    normalizan porque el modelo a veces copia los corchetes del template
    ("[avistaje-presagio]"); eso es formato, no un meme inventado."""
    limpios = [m.strip().strip("[]") for m in reportados]
    validos = [m for m in limpios if m in loadout.ids]
    inventados = set(limpios) - set(validos)
    if inventados:
        logger.warning(
            "El LLM reportó memes %s fuera del loadout de %s, se descartan: %s",
            etiqueta, receptor_id, inventados,
        )
    return validos


def _pedir_mutacion(cliente: ClienteLLM, prompt: str) -> RespuestaMutacion | None:
    """Llama al LLM y valida. Reintenta UNA vez con feedback del error (el modelo
    suele corregir si sabe qué falló). Devuelve None si ambos intentos fallan."""
    actual = prompt
    for intento in range(1, INTENTOS + 1):
        try:
            cruda = cliente.responder(actual)
        except ErrorLLM as e:
            # Fallo de infraestructura (cuota, red): no es culpa del contenido, así
            # que el reintento con feedback no ayuda. Se degrada ya (ADR-005).
            logger.warning("El LLM falló por infraestructura, no se reintenta: %s", e)
            return None
        try:
            return _parsear_respuesta(cruda)
        except (ValueError, ValidationError) as e:
            logger.warning("Respuesta de mutación inválida (intento %d): %s", intento, e)
            actual = (
                f"{prompt}\n\nTu respuesta anterior no fue válida porque: {e}\n"
                "Respondé SOLO con el JSON pedido, sin texto antes ni después."
            )
    return None


def transmitir(
    emisor_id: str,
    receptor: Memetario,
    version: Version,
    grafo: GrafoMundo,
    embeddings: Embeddings,
    cliente: ClienteLLM,
    reloj: RelojDelMundo,
    bias: Callable[[TipoMeme], float] | None = None,
    loadout: Loadout | None = None,
) -> Version:
    """Un ser le cuenta una versión a otro. Devuelve la versión que el receptor guardó.

    `version` es la versión que el emisor conoce y cuenta (puede ser la raíz, si el
    emisor fue testigo). El refuerzo de pesos NO ocurre acá: la transmisión registra
    activaciones (regla 4) y el decaimiento/refuerzo siguen siendo ciclos aparte.

    `loadout` permite pasar un cristal ya calculado (el Taller lo usa para mostrar
    las tensiones de la escucha); si viene None se calcula acá, como siempre."""
    contenido_oido = version.contenido

    # El cristal con el que el receptor escucha: su loadout ante lo que oye.
    if loadout is None:
        loadout = calcular_loadout(receptor, contenido_oido, embeddings, bias=bias)

    prompt = armar_prompt(receptor.ser.ser_id, emisor_id, contenido_oido, loadout)
    respuesta = _pedir_mutacion(cliente, prompt)

    if respuesta is None:
        # Degradación elegante (ADR-005): sin deformación, pero nunca en silencio.
        logger.warning(
            "Transmisión sin deformación (%s → %s, versión %s): el LLM no produjo "
            "una mutación válida; el receptor guarda lo que oyó tal cual.",
            emisor_id, receptor.ser.ser_id, version.id,
        )
        respuesta = RespuestaMutacion(contenido_entendido=contenido_oido)

    # El LLM propone, el motor dispone: solo cuentan los memes que estaban en el loadout.
    resonantes = _solo_del_loadout(
        respuesta.memes_resonantes, loadout, receptor.ser.ser_id, "resonantes"
    )
    desafiados = _solo_del_loadout(
        respuesta.memes_desafiados, loadout, receptor.ser.ser_id, "desafiados"
    )

    raiz = grafo.version_raiz(version.hecho_id)
    # `similitud` primero: recién después de intentar calcularla `disponible` es confiable.
    similitud = embeddings.similitud(respuesta.contenido_entendido, raiz.contenido)
    if embeddings.disponible:
        distancia = 1.0 - similitud
    else:
        # Sin embeddings la similitud vale 0.0 y la distancia daría 1.0: un dato falso
        # que quedaría en el grafo para siempre. Se marca con el centinela (regla 3).
        distancia = DISTANCIA_NO_MEDIDA
        logger.warning(
            "Sin embeddings: la distancia a la raíz de esta versión queda sin medir "
            "(centinela %s); se puede recalcular después desde el contenido.",
            DISTANCIA_NO_MEDIDA,
        )
    momento = reloj.ahora().isoformat()
    nueva = Version(
        id=f"v-{uuid.uuid4().hex[:12]}",
        hecho_id=version.hecho_id,
        contenido=respuesta.contenido_entendido,
        version_padre=version.id,
        emisor=emisor_id,
        receptor=receptor.ser.ser_id,
        momento=momento,
        distancia_raiz=distancia,
    )
    grafo.registrar_version(nueva)

    # Regla 4: el loadout completo estuvo "en consideración"; los resonantes se usaron.
    receptor.persistencia.registrar_activaciones(
        ser_id=receptor.ser.ser_id,
        momento=momento,
        situacion=contenido_oido,
        loadout_ids=loadout.ids,
        movilizados_ids=resonantes,
    )
    # Mejora 04 (experimento): los memes desafiados aplican su política de
    # aprendizaje. Con las políticas default no se mueve ningún peso — el
    # refuerzo por USO sigue siendo un ciclo aparte; esto reacciona al CONTENIDO.
    if desafiados:
        aplicar_contradicciones(receptor, receptor.persistencia, desafiados)
    return nueva
