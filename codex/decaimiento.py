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
TASA_EROSION = 0.15       # Mejora 04: cuánto decae un meme que se erosiona por
                          # contradicción (número grueso: 3× el ciclo normal).
TASA_REFUERZO_RUTINA = 0.02  # provisional: un décimo de la vivencia (0.20); se tunea jugando
TASA_DESCARGA_STRESS = 0.3   # Stress que descarga cada día vivido en paz. Sale del
                             # criterio del diseño: un mes tranquilo vacía una barra
                             # llena (30 días × 0.3 = 9, el techo). Provisional.
                             # Sin vicio todavía, esta es la única válvula.


def decaer(
    peso: float, piso: float = PISO, tasa: float = TASA_DECAIMIENTO, ciclos: float = 1.0
) -> float:
    """Acerca el peso al piso una fracción `tasa` por ciclo. Como solo recorre una
    fracción del camino restante, nunca alcanza el piso (asíntota), y por eso nunca
    llega a cero. `ciclos` puede ser fraccionario y compone: medio ciclo dos veces
    es exactamente un ciclo (el tiempo del mundo avanza en tramos arbitrarios)."""
    return piso + (peso - piso) * (1 - tasa) ** ciclos


def reforzar(peso: float, techo: float = TECHO, tasa: float = TASA_REFUERZO) -> float:
    """Acerca el peso al techo una fracción `tasa`. Nunca lo supera."""
    return peso + (techo - peso) * tasa


def aplicar_decaimiento(
    memetario: Memetario, persistencia: Persistencia, ciclos: float = 1.0
) -> dict[str, float]:
    """Decae todos los memes no fundacionales del ser (`ciclos` ciclos de
    decaimiento). Devuelve los pesos nuevos. Las PF quedan intactas."""
    nuevos = {
        m.id: decaer(m.peso, ciclos=ciclos)
        for m in memetario.memes_vivos()
        if m.tipo != TipoMeme.FUNDACIONAL and m.aprendizaje != "solo_trauma"
    }
    if nuevos:
        persistencia.actualizar_pesos(memetario.ser.ser_id, nuevos)
    return nuevos


def reforzar_movilizados(
    memetario: Memetario,
    persistencia: Persistencia,
    movilizados_ids: list[str],
    tasa: float = TASA_REFUERZO,
) -> dict[str, float]:
    """Refuerza el peso de los memes efectivamente usados. Las PF no se tocan.
    `tasa` distingue regímenes: la vivencia usa la default; la rutina, una menor."""
    movilizados = set(movilizados_ids)
    vivos = memetario.memes_vivos()

    desconocidos = movilizados - {m.id for m in vivos}
    if desconocidos:
        logger.warning(
            "Refuerzo pedido para memes que no existen en el ser %s: %s",
            memetario.ser.ser_id, desconocidos,
        )

    nuevos = {
        m.id: reforzar(m.peso, tasa=tasa)
        for m in vivos
        if m.id in movilizados
        and m.tipo != TipoMeme.FUNDACIONAL
        and m.aprendizaje != "solo_trauma"
    }
    if nuevos:
        persistencia.actualizar_pesos(memetario.ser.ser_id, nuevos)
    return nuevos


def aplicar_contradicciones(
    memetario: Memetario, persistencia: Persistencia, desafiados_ids: list[str]
) -> dict[str, float]:
    """Aplica la política de aprendizaje de cada meme desafiado (mejora 04,
    EXPERIMENTO): el que se radicaliza se atrinchera (gana peso al ser
    contradicho); el que se erosiona decae rápido. `normal` y `solo_trauma`
    no se mueven por contradicción, y las PF no aprenden: quedan fuera siempre.
    Devuelve los pesos que cambiaron."""
    desafiados = set(desafiados_ids)
    nuevos: dict[str, float] = {}
    for m in memetario.memes_vivos():
        if m.id not in desafiados or m.tipo == TipoMeme.FUNDACIONAL:
            continue
        if m.aprendizaje == "se_radicaliza":
            nuevos[m.id] = reforzar(m.peso)
        elif m.aprendizaje == "se_erosiona":
            nuevos[m.id] = decaer(m.peso, tasa=TASA_EROSION)
    if nuevos:
        persistencia.actualizar_pesos(memetario.ser.ser_id, nuevos)
    return nuevos


def descargar_stress(persistencia: Persistencia, ser_id: str, dias: float) -> float:
    """El tiempo vivido en paz descarga la barra de stress. Devuelve el stress nuevo.

    A diferencia del peso de un meme (que decae asintóticamente y nunca alcanza su
    piso), el stress SÍ llega a cero: un ser puede quedar en paz del todo. El tiempo
    que cuenta es el VIVIDO -avanzar el reloj del mundo, vivir días de rutina-, no
    el fijado a mano: fijar la hora es teletransporte autoral, no vida (misma regla
    que ya rige para el decaimiento desde el paso 1).

    Escribe por la puerta única (regla 2). Mientras no exista el vicio, esta es la
    única válvula de la barra (docs/DISENO_DESBORDE.md)."""
    actual = persistencia.leer_estado_reglas(ser_id).get("stress", 0.0)
    if dias <= 0:
        return actual
    nuevo = max(0.0, actual - TASA_DESCARGA_STRESS * dias)
    if nuevo != actual:
        persistencia.guardar_estado_reglas(ser_id, {"stress": nuevo})
    return nuevo
