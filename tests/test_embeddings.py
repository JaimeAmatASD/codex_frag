"""Tests de embeddings. Usan un codificador FALSO determinista: no descargan el
modelo ni tocan la red (regla 5). El caso de degradación sí prueba el camino real:
en el venv de tests fastembed no está instalado, así que cargarlo debe fallar limpio."""

import logging

import numpy as np

from codex.embeddings import Embeddings
from codex.persistencia import Persistencia


def encoder_falso(mapa: dict[str, list[float]]):
    """Codificador determinista para tests. Cuenta cuántas veces se lo llama,
    para verificar que el caché evita recomputar."""
    estado = {"llamadas": 0}

    def encode(textos):
        estado["llamadas"] += 1
        return [np.asarray(mapa[t], dtype=np.float32) for t in textos]

    encode.estado = estado
    return encode


def test_cache_evita_recomputar(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    enc = encoder_falso({"hola": [1.0, 0.0, 0.0]})
    emb = Embeddings(p, encoder=enc)

    v1 = emb.vector("hola")
    v2 = emb.vector("hola")  # debería venir del caché en SQLite

    assert enc.estado["llamadas"] == 1
    assert np.allclose(v1, v2)


def test_similitud_ordena_por_cercania(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    enc = encoder_falso({
        "mar": [1.0, 0.0],
        "oceano": [0.9, 0.1],
        "dinero": [0.0, 1.0],
    })
    emb = Embeddings(p, encoder=enc)

    assert emb.similitud("mar", "mar") == 1.0
    assert emb.similitud("mar", "oceano") > emb.similitud("mar", "dinero")


def test_sin_fastembed_degrada_con_log(tmp_path, caplog):
    """Si fastembed no está, no se rompe: devuelve None/0.0 y deja un error en el log."""
    p = Persistencia(tmp_path / "mundo")
    emb = Embeddings(p)  # sin encoder inyectado → intenta cargar fastembed (no instalado)

    with caplog.at_level(logging.ERROR):
        assert emb.vector("hola") is None
        assert emb.similitud("a", "b") == 0.0

    assert emb.disponible is False
    assert any("fastembed" in r.message.lower() for r in caplog.records)
