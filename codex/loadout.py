"""Cálculo del loadout: dado un ser y una situación, qué memes se activan.

Reglas del paso 1:
  - Las Piedras Fundacionales entran SIEMPRE y son gratis (no gastan mana).
  - Cada meme no fundacional recibe un score:
        score = (0.6 * peso_histórico_normalizado + 0.4 * similitud_semántica) * bias
    El peso se normaliza a 0..1 (dividiendo por el peso máximo entre los candidatos)
    para poder combinarlo con la similitud, que ya vive en ese rango.
  - Se ordena por score y se llena hasta el límite de mana del ser.

Si los embeddings no están disponibles, la similitud vale 0.0 y el score queda solo
con el peso histórico: degradamos, pero lo dejamos anotado en el log (regla 3). Es el
escenario que Fray Tomás escondía.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from .embeddings import Embeddings
from .memetario import Memetario
from .modelos import Loadout, MemeVivo, TensionInterna, TipoMeme

logger = logging.getLogger(__name__)

PESO_HISTORICO = 0.6
SIMILITUD = 0.4

# Dos memes en tensión declarada están EN TENSIÓN ACTIVA cuando sus pesos
# normalizados difieren menos que esto: pesan parecido y ninguno gana.
# Umbral inicial, calibrable con juego real.
UMBRAL_TENSION = 0.25


def detectar_tensiones(seleccionados: list[MemeVivo]) -> list[TensionInterna]:
    """Los pares del loadout en tensión declarada y de peso parejo: las grietas.

    Las PF participan igual que los operativos (una PF en tensión con un operativo
    fuerte es de las grietas más dramáticas). La tensión es simétrica: basta que
    un lado la declare. La intensidad es el menor de los dos pesos normalizados."""
    por_id = {m.id: m for m in seleccionados}
    peso_max = max((m.peso for m in seleccionados), default=0.0)

    pares = {
        frozenset((m.id, otro))
        for m in seleccionados
        for otro in m.tensiones
        if otro in por_id and otro != m.id
    }

    grietas = []
    for par in pares:
        a, b = sorted(par)
        norm_a = (por_id[a].peso / peso_max) if peso_max > 0 else 0.0
        norm_b = (por_id[b].peso / peso_max) if peso_max > 0 else 0.0
        if abs(norm_a - norm_b) <= UMBRAL_TENSION:
            grietas.append(
                TensionInterna(
                    meme_a=a, meme_b=b,
                    texto_a=por_id[a].texto, texto_b=por_id[b].texto,
                    intensidad=min(norm_a, norm_b),
                )
            )
    return sorted(grietas, key=lambda t: (t.meme_a, t.meme_b))


def costo_efectivo(meme: MemeVivo) -> int:
    """Mana que cuesta activar el meme.

    Punto de extensión (paso posterior): el lugar donde está el ser podrá modificar
    este costo. En el paso 1 no hay lugares, así que el costo es el del meme."""
    return meme.costo


def calcular_loadout(
    memetario: Memetario,
    situacion: str,
    embeddings: Embeddings,
    bias: Callable[[TipoMeme], float] | None = None,
) -> Loadout:
    """Selecciona los memes que se activan para `situacion`. `bias` es un multiplicador
    por tipo de meme (el bias circadiano); por defecto es neutral (1.0)."""
    if bias is None:
        bias = lambda _tipo: 1.0

    memes = memetario.memes_vivos()
    fundacionales = [m for m in memes if m.tipo == TipoMeme.FUNDACIONAL]
    candidatos = [m for m in memes if m.tipo != TipoMeme.FUNDACIONAL]

    # Normalización del peso a 0..1 sobre los candidatos.
    peso_max = max((m.peso for m in candidatos), default=0.0)

    scores: dict[str, float] = {}
    for m in candidatos:
        peso_norm = (m.peso / peso_max) if peso_max > 0 else 0.0
        sim = embeddings.similitud(situacion, m.texto)
        scores[m.id] = (PESO_HISTORICO * peso_norm + SIMILITUD * sim) * bias(m.tipo)

    if not embeddings.disponible:
        logger.warning(
            "Loadout de '%s' degradado: sin similitud semántica, solo peso histórico.",
            memetario.ser.ser_id,
        )

    # Las PF entran siempre, gratis.
    seleccionados: list[MemeVivo] = list(fundacionales)
    mana_restante = memetario.ser.mana_max
    mana_usado = 0

    # Candidatos por score descendente; se agregan los que entren en el mana disponible.
    for m in sorted(candidatos, key=lambda x: scores[x.id], reverse=True):
        costo = costo_efectivo(m)
        if costo <= mana_restante:
            seleccionados.append(m)
            mana_restante -= costo
            mana_usado += costo

    return Loadout(
        ser_id=memetario.ser.ser_id,
        seleccionados=seleccionados,
        mana_usado=mana_usado,
        scores=scores,
        tensiones=detectar_tensiones(seleccionados),
    )
