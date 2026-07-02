"""Tests del reloj del mundo y del bias circadiano, incluido su enchufe al loadout."""

from datetime import datetime, timedelta

import numpy as np

from codex.bias import BiasCircadiano
from codex.embeddings import Embeddings
from codex.loadout import calcular_loadout
from codex.memetario import Memetario
from codex.modelos import Ser, TipoMeme
from codex.persistencia import Persistencia
from codex.reloj import RelojSimple


def test_reloj_devuelve_la_hora_del_mundo_no_la_del_sistema():
    # Una fecha lejana y fija: si devolviera la hora del sistema, esto fallaría.
    momento = datetime(1850, 3, 1, 9, 0)
    reloj = RelojSimple(momento)
    assert reloj.ahora() == momento


def test_reloj_avanza():
    reloj = RelojSimple(datetime(1850, 3, 1, 9, 0))
    reloj.avanzar(timedelta(hours=5))
    assert reloj.ahora().hour == 14


def test_bias_de_dia_favorece_operativos():
    reloj = RelojSimple(datetime(1850, 3, 1, 10, 0))  # 10:00 → día
    bias = BiasCircadiano(reloj)
    assert bias(TipoMeme.OPERATIVO) > bias(TipoMeme.EXPERIMENTAL)


def test_bias_de_noche_favorece_experimentales():
    reloj = RelojSimple(datetime(1850, 3, 1, 23, 0))  # 23:00 → noche
    bias = BiasCircadiano(reloj)
    assert bias(TipoMeme.EXPERIMENTAL) > bias(TipoMeme.OPERATIVO)


def test_el_bias_circadiano_cambia_el_loadout_segun_la_hora(tmp_path):
    """La misma situación, a distinta hora del mundo, elige distinto meme."""
    datos = {
        "ser_id": "soñador",
        "mana_max": 20,  # solo entra UN meme: el bias desempata
        "memes": [
            {"id": "tarea", "tipo": "operativo", "texto": "Hacer la tarea concreta.", "peso_inicial": 5.0, "costo": 20},
            {"id": "sueño", "tipo": "experimental", "texto": "Imaginar algo nuevo.", "peso_inicial": 5.0, "costo": 20},
        ],
    }
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**datos), p)
    # Mismo vector para todo → peso y similitud empatan; solo el bias decide.
    emb = Embeddings(p, encoder=lambda textos: [np.asarray([0.5, 0.5], dtype=np.float32) for _ in textos])

    reloj = RelojSimple(datetime(1850, 3, 1, 10, 0))  # día
    de_dia = calcular_loadout(m, "algo", emb, bias=BiasCircadiano(reloj))

    reloj.fijar(datetime(1850, 3, 1, 23, 0))           # noche
    de_noche = calcular_loadout(m, "algo", emb, bias=BiasCircadiano(reloj))

    assert "tarea" in de_dia.ids
    assert "sueño" in de_noche.ids
