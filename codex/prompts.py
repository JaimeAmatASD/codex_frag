"""Piezas del armado de prompts que la mutación y la narración comparten.

La sección de la grieta vive en templates/tension.txt (texto plano iterable a
mano, como los otros dos templates); cada camino le pone su `$donde` — en la
mutación la tensión debe notarse en cómo entiende, en el Score en cómo actúa.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

from .modelos import LENTE_POR_FUNCION, MemeVivo, TensionInterna

TEMPLATE_TENSION = Path(__file__).parent.parent / "templates" / "tension.txt"


def seccion_tension(tensiones: list[TensionInterna], donde: str) -> str:
    """La sección de la grieta para el prompt: una copia por tensión detectada,
    rodeada de líneas en blanco. String vacío si no hay tensiones (sin residuo)."""
    if not tensiones:
        return ""
    template = Template(TEMPLATE_TENSION.read_text(encoding="utf-8"))
    parrafos = "\n\n".join(
        template.substitute(texto_a=t.texto_a, texto_b=t.texto_b, donde=donde).strip()
        for t in tensiones
    )
    return f"\n{parrafos}\n"


def anotar_funcion(meme: MemeVivo) -> str:
    """' (lente moral)' si el meme declara función; '' si no."""
    return f" ({LENTE_POR_FUNCION[meme.funcion]})" if meme.funcion else ""
