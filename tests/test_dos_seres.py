"""La prueba del paso 1: dos seres con memetarios distintos, ante la MISMA noticia,
arman loadouts distintos y coherentes con quiénes son.

Es determinista: carga los seres reales de mundos/prueba/seres pero usa un codificador
de vectores controlado, para no depender de la descarga del modelo (regla 5). El demo
demos/prueba_paso1.py hace lo mismo con embeddings reales.
"""

import json
from pathlib import Path

import numpy as np

from codex.embeddings import Embeddings
from codex.loadout import calcular_loadout
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia

SERES_DIR = Path(__file__).parent.parent / "mundos" / "prueba" / "seres"
NOTICIA = "Corre la noticia de un avistamiento extraño en la bahía."

# Vectores 2D: eje x = "presagio / agua", eje y = "comercio / razón".
# La noticia tira hacia x; en cada ser resuena el meme más cercano a la noticia.
VECTORES = {
    NOTICIA: [1.0, 0.0],
    "Un avistaje extraño en el agua anuncia tormenta o desgracia.": [0.95, 0.05],
    "Las viejas historias del puerto suelen decir la verdad.": [0.6, 0.4],
    "Quizás conviene ofrecer algo al mar para calmarlo.": [0.7, 0.3],
    "Un rumor extraño puede mover el mercado y conviene aprovecharlo.": [0.9, 0.1],
    "No creo en presagios: busco la causa real detrás del hecho.": [0.55, 0.45],
    "Tal vez todo esto sea una oportunidad de negocio.": [0.5, 0.5],
}


def _cargar_ser(nombre: str) -> Ser:
    return Ser(**json.loads((SERES_DIR / nombre / "ser.json").read_text(encoding="utf-8")))


def test_dos_seres_misma_noticia_distinto_loadout(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    emb = Embeddings(
        p, encoder=lambda textos: [np.asarray(VECTORES[t], dtype=np.float32) for t in textos]
    )

    pescador = Memetario(_cargar_ser("pescador_supersticioso"), p)
    comerciante = Memetario(_cargar_ser("comerciante_esceptico"), p)

    lo_pescador = calcular_loadout(pescador, NOTICIA, emb)
    lo_comerciante = calcular_loadout(comerciante, NOTICIA, emb)

    # Cada uno activa algo coherente con quién es:
    assert "avistaje-presagio" in lo_pescador.ids       # el pescador lee un presagio
    assert "rumor-mercado" in lo_comerciante.ids        # el comerciante ve el mercado

    # Las PF de cada uno entran siempre.
    assert "PF-mar-habla" in lo_pescador.ids
    assert "PF-todo-precio" in lo_comerciante.ids

    # Misma noticia, dos mentes: los loadouts son distintos.
    assert set(lo_pescador.ids) != set(lo_comerciante.ids)
