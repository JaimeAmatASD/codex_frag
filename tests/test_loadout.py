"""Tests del loadout. Usan embeddings con codificador falso determinista (regla 5)."""

import logging

import numpy as np

from codex.embeddings import Embeddings
from codex.loadout import calcular_loadout, detectar_tensiones
from codex.memetario import Memetario
from codex.modelos import MemeVivo, Ser, TipoMeme
from codex.persistencia import Persistencia


def _embeddings(p, vectores: dict[str, list[float]]) -> Embeddings:
    def encode(textos):
        return [np.asarray(vectores[t], dtype=np.float32) for t in textos]
    return Embeddings(p, encoder=encode)


def _embeddings_caidos(p) -> Embeddings:
    """Embeddings que simulan a fastembed ausente, sin intentar cargarlo."""
    emb = Embeddings(p)
    emb._intento_carga = True
    emb.disponible = False
    return emb


SER = {
    "ser_id": "pescador",
    "mana_max": 30,
    "memes": [
        {"id": "PF-mar", "tipo": "fundacional", "texto": "El mar cobra lo que se le debe.", "peso_inicial": 9.0},
        {"id": "tormenta", "tipo": "operativo", "texto": "Un avistaje anuncia tormenta.", "peso_inicial": 5.0, "costo": 20},
        {"id": "negocio", "tipo": "operativo", "texto": "Una oportunidad de ganar plata.", "peso_inicial": 5.0, "costo": 20},
    ],
}


def test_pf_siempre_entra_y_es_gratis(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)
    emb = _embeddings(p, {
        "hay algo raro en el agua": [1.0, 0.0],
        "Un avistaje anuncia tormenta.": [0.9, 0.1],
        "Una oportunidad de ganar plata.": [0.0, 1.0],
    })

    lo = calcular_loadout(m, "hay algo raro en el agua", emb)

    # La PF está, y no consumió mana (mana solo se gasta en operativos).
    assert "PF-mar" in lo.ids
    # Con mana_max=30 y costo 20 c/u, entra un solo operativo: el más cercano a la situación.
    assert "tormenta" in lo.ids
    assert "negocio" not in lo.ids
    assert lo.mana_usado == 20


def test_la_situacion_cambia_la_seleccion(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)
    emb = _embeddings(p, {
        "quiero hacer plata": [0.0, 1.0],
        "Un avistaje anuncia tormenta.": [0.9, 0.1],
        "Una oportunidad de ganar plata.": [0.0, 1.0],
    })

    lo = calcular_loadout(m, "quiero hacer plata", emb)

    # Misma estructura, otra situación: ahora gana 'negocio'.
    assert "negocio" in lo.ids
    assert "tormenta" not in lo.ids


def test_mana_limita_la_cantidad(tmp_path):
    datos = dict(SER, mana_max=100)  # ahora entran los dos operativos
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**datos), p)
    emb = _embeddings(p, {
        "algo pasa": [0.5, 0.5],
        "Un avistaje anuncia tormenta.": [0.9, 0.1],
        "Una oportunidad de ganar plata.": [0.1, 0.9],
    })

    lo = calcular_loadout(m, "algo pasa", emb)

    assert {"tormenta", "negocio"} <= set(lo.ids)
    assert lo.mana_usado == 40
    assert lo.mana_usado <= datos["mana_max"]


def test_sin_similitud_degrada_y_loguea(tmp_path, caplog):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)
    emb = _embeddings_caidos(p)

    with caplog.at_level(logging.WARNING):
        lo = calcular_loadout(m, "lo que sea", emb)

    # Sin similitud, el score es solo peso histórico: igual selecciona, pero avisa.
    assert "PF-mar" in lo.ids
    assert any("degradado" in r.message.lower() for r in caplog.records)


def test_bias_escala_los_scores(tmp_path):
    """El bias (multiplicador por tipo) escala el score. Es el enchufe del bias
    circadiano: a igual peso y similitud, la hora puede favorecer a un tipo de meme."""
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER), p)
    emb = _embeddings(p, {
        "neutro": [0.5, 0.5],
        "Un avistaje anuncia tormenta.": [0.5, 0.5],
        "Una oportunidad de ganar plata.": [0.5, 0.5],
    })

    base = calcular_loadout(m, "neutro", emb)
    con_bias = calcular_loadout(m, "neutro", emb, bias=lambda t: 2.0 if t == TipoMeme.OPERATIVO else 1.0)

    assert con_bias.scores["tormenta"] == base.scores["tormenta"] * 2.0


# ----- El detector de tensiones (código puro sobre los seleccionados) -----

def _vivo(id, peso, tensiones=(), tipo="operativo"):
    return MemeVivo(id=id, tipo=tipo, texto=f"texto de {id}", costo=0,
                    peso=peso, tensiones=list(tensiones))


def test_tension_con_pesos_parejos_se_detecta():
    grietas = detectar_tensiones([_vivo("deber", 9.0, tensiones=["familia"]),
                                  _vivo("familia", 8.0)])

    assert len(grietas) == 1
    g = grietas[0]
    assert {g.meme_a, g.meme_b} == {"deber", "familia"}
    assert g.texto_a and g.texto_b
    assert g.intensidad == 8.0 / 9.0   # el menor de los dos pesos normalizados


def test_tension_con_pesos_dispares_no_es_grieta():
    # 3/9 contra 9/9: la diferencia normalizada (0.67) supera el umbral. Uno gana
    # de sobra, no hay tironeo que narrar.
    assert detectar_tensiones([_vivo("deber", 9.0, tensiones=["familia"]),
                               _vivo("familia", 3.0)]) == []


def test_la_tension_es_simetrica_aunque_un_solo_lado_la_declare():
    unilateral = detectar_tensiones([_vivo("a", 5.0, tensiones=["b"]), _vivo("b", 5.0)])
    bilateral = detectar_tensiones([_vivo("a", 5.0, tensiones=["b"]),
                                    _vivo("b", 5.0, tensiones=["a"])])

    assert len(unilateral) == 1
    assert unilateral == bilateral   # declarada de los dos lados, no se duplica


def test_sin_tensiones_declaradas_lista_vacia():
    assert detectar_tensiones([_vivo("a", 5.0), _vivo("b", 5.0)]) == []


def test_tension_con_meme_fuera_del_loadout_no_cuenta():
    assert detectar_tensiones([_vivo("a", 5.0, tensiones=["ausente"])]) == []


def test_las_pf_participan_del_detector():
    grietas = detectar_tensiones([
        _vivo("PF-hogar", 9.0, tensiones=["deber"], tipo="fundacional"),
        _vivo("deber", 8.0),
    ])
    assert len(grietas) == 1


def test_el_loadout_trae_sus_tensiones(tmp_path):
    datos = {
        "ser_id": "partido", "mana_max": 100,
        "memes": [
            {"id": "PF-familia", "tipo": "fundacional",
             "texto": "Nunca abandones a tu familia.", "peso_inicial": 9.0,
             "tensiones": ["deber"]},
            {"id": "deber", "tipo": "operativo",
             "texto": "El deber está por encima de todo.", "peso_inicial": 8.0, "costo": 20},
        ],
    }
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**datos), p)
    emb = _embeddings(p, {
        "te llaman a la guerra": [1.0, 0.0],
        "El deber está por encima de todo.": [0.9, 0.1],
    })

    lo = calcular_loadout(m, "te llaman a la guerra", emb)

    assert len(lo.tensiones) == 1
    assert {lo.tensiones[0].meme_a, lo.tensiones[0].meme_b} == {"PF-familia", "deber"}
