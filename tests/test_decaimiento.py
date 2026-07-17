"""Tests de decaimiento y refuerzo. Puro cálculo, deterministas."""

from codex.decaimiento import (
    PISO,
    TASA_EROSION,
    TECHO,
    aplicar_contradicciones,
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


# ----- Mejora 04 (EXPERIMENTO): políticas de aprendizaje -----

SER_EXPERIMENTO = {
    "ser_id": "cobaya",
    "mana_max": 100,
    "memes": [
        {"id": "PF-roca", "tipo": "fundacional", "texto": "Piedra.", "peso_inicial": 9.0,
         "aprendizaje": "se_radicaliza"},   # aunque declare política, la PF no aprende
        {"id": "terco", "tipo": "operativo", "texto": "Terco.", "peso_inicial": 5.0,
         "aprendizaje": "se_radicaliza"},
        {"id": "inmovil", "tipo": "operativo", "texto": "Inmóvil.", "peso_inicial": 5.0,
         "aprendizaje": "solo_trauma"},
        {"id": "flojo", "tipo": "operativo", "texto": "Flojo.", "peso_inicial": 5.0,
         "aprendizaje": "se_erosiona"},
        {"id": "comun", "tipo": "operativo", "texto": "Común.", "peso_inicial": 5.0},
    ],
}


def test_contradiccion_aplica_la_politica_de_cada_meme(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER_EXPERIMENTO), p)

    # Todos desafiados a la vez: cada uno responde según su política.
    cambios = aplicar_contradicciones(
        m, p, ["PF-roca", "terco", "inmovil", "flojo", "comun"])

    estado = p.leer_estado("cobaya")
    assert estado["PF-roca"].peso == 9.0                       # la PF no aprende
    assert estado["terco"].peso > 5.0                          # se atrinchera
    assert estado["inmovil"].peso == 5.0                       # solo el trauma lo movería
    assert estado["flojo"].peso == decaer(5.0, tasa=TASA_EROSION)  # cae rápido
    assert estado["flojo"].peso < decaer(5.0)                  # más que un ciclo normal
    assert estado["comun"].peso == 5.0                         # normal: la contradicción sola no lo mueve
    assert set(cambios) == {"terco", "flojo"}


def test_solo_trauma_ni_decae_ni_se_refuerza(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER_EXPERIMENTO), p)

    aplicar_decaimiento(m, p)
    reforzar_movilizados(m, p, ["inmovil"])

    estado = p.leer_estado("cobaya")
    assert estado["inmovil"].peso == 5.0      # inmune al ciclo y al uso
    assert estado["comun"].peso < 5.0         # el normal sí decayó
