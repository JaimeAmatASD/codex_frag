"""Bias circadiano: multiplicadores del score por tipo de meme según la hora del mundo.

La idea: a igual peso y similitud, la hora inclina la balanza. De día pesan más los
memes operativos (lo práctico); de noche, los experimentales (lo exploratorio). Las
Piedras Fundacionales no se afectan (entran siempre).

La hora la da el reloj del MUNDO, nunca el reloj del sistema. Un `BiasCircadiano` se
puede pasar directamente como el parámetro `bias` de `calcular_loadout`, porque es
invocable: `bias(tipo) -> multiplicador`.

Los valores de la tabla son un punto de partida razonable, pensados para calibrarse.
"""

from __future__ import annotations

from .modelos import TipoMeme
from .reloj import RelojDelMundo

HORA_INICIO_DIA = 6
HORA_FIN_DIA = 18

TABLA_POR_DEFECTO: dict[str, dict[TipoMeme, float]] = {
    "dia": {
        TipoMeme.OPERATIVO: 1.2,      # de día, más peso a lo práctico
        TipoMeme.EXPERIMENTAL: 0.8,
        TipoMeme.FUNDACIONAL: 1.0,
    },
    "noche": {
        TipoMeme.OPERATIVO: 0.8,
        TipoMeme.EXPERIMENTAL: 1.2,   # de noche, más espacio a lo exploratorio
        TipoMeme.FUNDACIONAL: 1.0,
    },
}


class BiasCircadiano:
    """Multiplicador por tipo de meme según la franja horaria del mundo."""

    def __init__(self, reloj: RelojDelMundo, tabla: dict[str, dict[TipoMeme, float]] | None = None):
        self.reloj = reloj
        self.tabla = tabla if tabla is not None else TABLA_POR_DEFECTO

    def franja(self) -> str:
        hora = self.reloj.ahora().hour
        return "dia" if HORA_INICIO_DIA <= hora < HORA_FIN_DIA else "noche"

    def __call__(self, tipo: TipoMeme) -> float:
        return self.tabla[self.franja()].get(tipo, 1.0)
