"""El diálogo directo: hablarle a un ser sin secreto ni emisor (El Taller).

A diferencia de `transmitir` (que exige un Hecho/Version ya registrado y un
emisor que lo cuenta), acá el "situación" es la charla misma: cualquier texto
libre -una escena narrada, una pregunta, una línea de otro personaje- activa
el cristal del receptor tal como está AHORA, y el LLM responde en su voz.

Es de solo lectura sobre el cristal: no crea Hecho ni Version, no registra
activaciones (regla 4) ni aplica contradicciones. Sirve para probarle la voz
al personaje sin dejar huella en su memoria ni mover un peso -eso es el modo
editar del Taller, que usa la puerta única (`Persistencia.actualizar_pesos`)
a propósito, aparte de esto.

El prompt vive en templates/dialogo.txt, mismo mecanismo que mutación y Score.
"""

from __future__ import annotations

import logging
from pathlib import Path
from string import Template

from .embeddings import Embeddings
from .llm import ClienteLLM, ErrorLLM
from .loadout import Loadout, calcular_loadout
from .memetario import Memetario
from .modelos import TipoMeme
from .prompts import anotar_funcion, seccion_tension

logger = logging.getLogger(__name__)

TEMPLATE_DIALOGO = Path(__file__).parent.parent / "templates" / "dialogo.txt"
# En el diálogo la grieta debe notarse en cómo responde, no en cómo entiende
# (mutación) ni en cómo actúa bajo riesgo (Score): es su propio $donde.
DONDE_TENSION = "cómo responde"


def _historial_legible(historial: list[dict], ser_id: str) -> str:
    """La charla completa, línea a línea, con el nombre de quien habla."""
    if not historial:
        return "(todavía no le dijiste nada; esto es lo primero que oye)"
    return "\n".join(
        f"{'Vos' if t['quien'] == 'vos' else ser_id}: {t['texto']}" for t in historial
    )


def armar_prompt(ser_id: str, historial: list[dict], loadout: Loadout) -> str:
    """Rellena el template de diálogo con el cristal ACTUAL del ser."""
    pf = [m for m in loadout.seleccionados if m.tipo == TipoMeme.FUNDACIONAL]
    activos = [m for m in loadout.seleccionados if m.tipo != TipoMeme.FUNDACIONAL]
    template = Template(TEMPLATE_DIALOGO.read_text(encoding="utf-8"))
    return template.substitute(
        ser_id=ser_id,
        pf="\n".join(f"- {m.texto}{anotar_funcion(m)}" for m in pf) or "- (ninguna)",
        memes_activos="\n".join(f"- {m.texto}{anotar_funcion(m)}" for m in activos)
        or "- (ninguno)",
        tension=seccion_tension(loadout.tensiones, DONDE_TENSION),
        historial=_historial_legible(historial, ser_id),
    )


def responder_dialogo(
    memetario: Memetario,
    historial: list[dict],
    cliente: ClienteLLM,
    embeddings: Embeddings,
) -> tuple[str, Loadout]:
    """El cristal actual del ser reacciona a la charla acumulada (regla que
    eligió James: cada turno mira toda la charla, no solo el último mensaje).
    Devuelve su respuesta y el loadout usado (memes activos + tensiones, para
    mostrar el cristal reaccionando sin necesidad de que el LLM las reporte).

    Nunca toca el estado vivo: ni activaciones ni pesos. Si el LLM falla por
    infraestructura, degrada con un aviso visible en vez de silencio (regla 3)."""
    situacion = _historial_legible(historial, memetario.ser.ser_id)
    loadout = calcular_loadout(memetario, situacion, embeddings)
    prompt = armar_prompt(memetario.ser.ser_id, historial, loadout)
    try:
        respuesta = cliente.responder(prompt)
    except ErrorLLM as e:
        logger.warning(
            "El diálogo con %s no pudo responder por infraestructura: %s",
            memetario.ser.ser_id, e,
        )
        respuesta = "(no responde: se cortó la comunicación con el modelo)"
    return respuesta.strip(), loadout
