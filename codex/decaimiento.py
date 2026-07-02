"""Decaimiento y refuerzo de los pesos de los memes.

Tres reglas del paso 1:
  - El peso decae de forma ASINTÓTICA hacia un piso > 0: nunca llega a cero. Un meme
    que se deja de usar pierde fuerza, pero no desaparece.
  - Se refuerza por ACTIVACIÓN, y activación significa "movilizado" (usado de verdad),
    no "estuvo en el loadout" (regla 4). Reforzar por loadout inflaría memes que solo
    se consideraron sin usarse.
  - Las Piedras Fundacionales NO decaen (su fuerza es estructural) y tampoco se refuerzan:
    su peso es constante.

Todas las escrituras pasan por la persistencia (regla 2). Las funciones puras `decaer`
y `reforzar` no tocan disco y son fáciles de testear y de razonar.
"""

from __future__ import annotations

import logging

from .memetario import Memetario
from .modelos import TipoMeme
from .persistencia import Persistencia

logger = logging.getLogger(__name__)

PISO = 0.1                # El peso decae hacia acá, nunca por debajo (asíntota > 0).
TECHO = 10.0              # El refuerzo acerca a acá, nunca por encima.
TASA_DECAIMIENTO = 0.05   # Fracción del camino al piso que se recorre por ciclo.
TASA_REFUERZO = 0.20      # Fracción del camino al techo que se recorre por activación.


def decaer(peso: float, piso: float = PISO, tasa: float = TASA_DECAIMIENTO) -> float:
    """Acerca el peso al piso una fracción `tasa`. Como solo recorre una fracción del
    camino restante, nunca alcanza el piso (asíntota), y por eso nunca llega a cero."""
    return piso + (peso - piso) * (1 - tasa)


def reforzar(peso: float, techo: float = TECHO, tasa: float = TASA_REFUERZO) -> float:
    """Acerca el peso al techo una fracción `tasa`. Nunca lo supera."""
    return peso + (techo - peso) * tasa


def aplicar_decaimiento(memetario: Memetario, persistencia: Persistencia) -> dict[str, float]:
    """Decae todos los memes no fundacionales del ser (un ciclo de decaimiento).
    Devuelve los pesos nuevos. Las PF quedan intactas."""
    nuevos = {
        m.id: decaer(m.peso)
        for m in memetario.memes_vivos()
        if m.tipo != TipoMeme.FUNDACIONAL
    }
    if nuevos:
        persistencia.actualizar_pesos(memetario.ser.ser_id, nuevos)
    return nuevos


def reforzar_movilizados(
    memetario: Memetario, persistencia: Persistencia, movilizados_ids: list[str]
) -> dict[str, float]:
    """Refuerza el peso de los memes efectivamente usados. Las PF no se tocan."""
    movilizados = set(movilizados_ids)
    vivos = memetario.memes_vivos()

    desconocidos = movilizados - {m.id for m in vivos}
    if desconocidos:
        logger.warning(
            "Refuerzo pedido para memes que no existen en el ser %s: %s",
            memetario.ser.ser_id, desconocidos,
        )

    nuevos = {
        m.id: reforzar(m.peso)
        for m in vivos
        if m.id in movilizados and m.tipo != TipoMeme.FUNDACIONAL
    }
    if nuevos:
        persistencia.actualizar_pesos(memetario.ser.ser_id, nuevos)
    return nuevos
