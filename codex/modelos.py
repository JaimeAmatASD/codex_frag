"""Modelos de datos del motor cognitivo, validados con pydantic.

Separamos dos cosas que en Fray Tomás se mezclaron y se desincronizaron (regla 1):

  - La DEFINICIÓN de un meme (texto, tipo, conexiones, peso inicial). No cambia;
    vive en el JSON del ser, legible a mano. La representan `Meme` y `Ser`.
  - El ESTADO VIVO de un meme (peso actual, cuántas veces se usó). Cambia todo el
    tiempo; vive en SQLite. Lo representa `EstadoMeme`.

El peso vivo NUNCA se guarda en el JSON: esa duplicación fue el bug de Fray Tomás.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TipoMeme(str, Enum):
    """Las tres categorías de meme del memetario."""

    FUNDACIONAL = "fundacional"   # Piedra Fundacional: nunca decae y siempre es gratis.
    OPERATIVO = "operativo"
    EXPERIMENTAL = "experimental"


class Meme(BaseModel):
    """Definición estática de un meme (la semilla, escrita a mano en el JSON del ser)."""

    id: str
    tipo: TipoMeme
    texto: str
    peso_inicial: float
    # Mana que cuesta activar el meme. Las Piedras Fundacionales lo ignoran (gratis).
    # Punto de extensión (paso posterior): el costo efectivo podrá modificarse según
    # el lugar donde esté el ser. En el paso 1 todavía no hay lugares, así que el
    # costo es fijo. La lógica de costo efectivo vivirá en el loadout, no acá.
    costo: int = 0
    conexiones: list[str] = Field(default_factory=list)


class Ser(BaseModel):
    """Un ser de la ficción: su tope de mana y la definición de todos sus memes."""

    ser_id: str
    mana_max: int
    memes: list[Meme]


class EstadoMeme(BaseModel):
    """Estado vivo de un meme para un ser concreto (un renglón de SQLite).

    `veces_en_loadout` y `veces_movilizado` son distintos a propósito (regla 4):
    estar en el loadout (seleccionado) no es lo mismo que haber sido usado de verdad.
    """

    meme_id: str
    peso: float
    ultima_activacion: str | None = None   # hora del MUNDO en ISO; None si nunca se usó.
    veces_en_loadout: int = 0
    veces_movilizado: int = 0


class MemeVivo(BaseModel):
    """Vista coherente de un meme: su definición (estática) + su estado vivo.

    Es lo que el memetario entrega al loadout: un solo objeto que junta lo que en
    Fray Tomás vivía partido entre el JSON y SQLite. Tener esta vista unificada es lo
    que evita que un meme usado a diario figure como "nunca usado"."""

    id: str
    tipo: TipoMeme
    texto: str
    costo: int
    peso: float
    ultima_activacion: str | None = None
    veces_movilizado: int = 0


class Loadout(BaseModel):
    """Resultado de una selección: qué memes se activan ante una situación.

    `scores` guarda el puntaje de cada meme NO fundacional (las PF entran siempre, sin
    puntaje), para poder inspeccionar por qué se eligió lo que se eligió."""

    ser_id: str
    seleccionados: list[MemeVivo]
    mana_usado: int
    scores: dict[str, float] = Field(default_factory=dict)

    @property
    def ids(self) -> list[str]:
        return [m.id for m in self.seleccionados]
