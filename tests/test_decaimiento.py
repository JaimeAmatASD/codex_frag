"""Tests de decaimiento y refuerzo. Puro cálculo, deterministas."""

from codex.decaimiento import (
    PISO,
    TECHO,
    aplicar_decaimiento,
    decaer,
    reforzar,
    reforzar_movilizados,
)
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia

SER = {
    "ser_id": "pescador",
    "mana_max": 100,
    "memes": [
        {"id": "PF-mar", "tipo": "fundacional", "texto": "El mar cobra.", "peso_inicial": 9.0},
        {"id": "tormenta", "tipo": "operativo", "texto": "Tormenta.", "peso_inicial": 5.0, "costo": 20},
    ],
}


def test_decaer_baja_pero_no_cruza_el_piso():
    p = decaer(5.0)
    assert PISO < p < 5.0


def test_decaer_nunca_llega_a_cero():
    peso = 5.0
    for _ in range(10_000):
        peso = decaer(peso)
    assert peso > 0          # asíntota: nunca cero
    assert peso >= PISO * 0.99  # se queda pegado al piso, no por debajo


def test_reforzar_sube_pero_no_pasa_el_techo():
    p = reforzar(5.0)
    assert 5.0 < p <= TECHO
    muy_reforzado = 5.0
    for _ in range(1_000):
        muy_reforzado = reforzar(muy_reforzado)
    assert muy_reforzado <= TECHO


def test_pf_no_decae_pero_los_demas_si(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)

    aplicar_decaimiento(m, p)

    estado = p.leer_estado("pescador")
    assert estado["PF-mar"].peso == 9.0      # la PF no se movió
    assert estado["tormenta"].peso < 5.0      # el operativo decayó


def test_reforzar_solo_los_movilizados_y_no_las_pf(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)

    # Movilizamos la PF y el operativo: solo el operativo debe subir.
    reforzar_movilizados(m, p, ["PF-mar", "tormenta"])

    estado = p.leer_estado("pescador")
    assert estado["PF-mar"].peso == 9.0       # la PF no se refuerza
    assert estado["tormenta"].peso > 5.0       # el operativo usado sube
