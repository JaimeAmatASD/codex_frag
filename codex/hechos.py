"""Modelos del grafo de información: hechos, versiones y la respuesta de mutación.

Es la base del paso 2 (la mutación del rumor, ADR-004): cada hecho del mundo es la
raíz de un árbol de versiones. Cada vez que un ser le cuenta algo a otro, nace una
versión nueva, deformada por el cristal del receptor, con linaje rastreable.

Dos decisiones de diseño:
  - La raíz es una Version más, sin padre, sin emisor ni receptor: la verdad objetiva
    existe aunque nadie la conozca. Quién la conoce (el testigo) se registra como
    relación en el grafo, no acá (regla 1: cada dato en un solo lugar).
  - `distancia_raiz` es DISTANCIA de verdad (1 - similitud coseno con la raíz): vale
    0.0 en la raíz y crece a medida que el rumor se deforma.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Hecho(BaseModel):
    """La verdad raíz: algo que objetivamente ocurrió en el mundo,
    exista o no quien lo conozca completo (ADR-004)."""

    id: str
    contenido: str
    momento: str   # hora del MUNDO en ISO (viene del RelojDelMundo, nunca datetime.now()).
    lugar: str     # string simple; el sistema de lugares llega en pasos posteriores.


class Version(BaseModel):
    """Cada forma en que un hecho circula. La raíz es la versión cero:
    contenido idéntico al Hecho, sin padre, sin emisor ni receptor."""

    id: str
    hecho_id: str
    contenido: str
    version_padre: str | None = None   # None = es la raíz.
    emisor: str | None = None          # None en la raíz.
    receptor: str | None = None        # None en la raíz.
    momento: str                       # hora del mundo en que nació esta versión.
    distancia_raiz: float              # 1 - similitud coseno con la raíz; 0.0 en la raíz.


class RespuestaMutacion(BaseModel):
    """Lo único que el LLM puede devolver en una transmisión. El LLM propone, el
    motor dispone (ADR-001): nada entra al grafo sin validar contra este esquema.

    `memes_resonantes` son los ids de memes del loadout del receptor que tiñeron su
    comprensión: los "movilizados" de la regla 4. Los ids que no estén en el loadout
    se descartan con log en la transmisión."""

    contenido_entendido: str = Field(min_length=1)
    memes_resonantes: list[str] = Field(default_factory=list)
