"""Tests del memetario. Deterministas, sin LLM ni embeddings."""

import json
import logging

import pytest
from pydantic import ValidationError

from codex.memetario import Memetario
from codex.modelos import Meme, Ser, TipoMeme
from codex.persistencia import Persistencia

SER_EJEMPLO = {
    "ser_id": "pescador",
    "mana_max": 100,
    "memes": [
        {"id": "PF-mar", "tipo": "fundacional", "texto": "El mar cobra lo que se le debe.",
         "peso_inicial": 9.0, "conexiones": ["presagio"]},
        {"id": "presagio", "tipo": "operativo", "texto": "Un avistaje anuncia tormenta.",
         "peso_inicial": 5.0, "costo": 20},
    ],
}


def test_construye_grafo_con_nodos_aristas_y_atributos(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER_EJEMPLO), p)

    assert set(m.grafo.nodes) == {"PF-mar", "presagio"}
    assert ("PF-mar", "presagio") in m.grafo.edges
    assert m.grafo.nodes["PF-mar"]["tipo"] == TipoMeme.FUNDACIONAL
    assert m.grafo.nodes["presagio"]["costo"] == 20


def test_vista_viva_combina_definicion_y_estado(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    m = Memetario(Ser(**SER_EJEMPLO), p)

    # Recién sembrado: el peso vivo arranca en el peso inicial.
    por_id = {mv.id: mv for mv in m.memes_vivos()}
    assert por_id["PF-mar"].peso == 9.0
    assert por_id["PF-mar"].texto == "El mar cobra lo que se le debe."

    # Si el peso vivo cambia, la vista lo refleja (definición + estado, coherentes).
    p.actualizar_pesos("pescador", {"PF-mar": 6.3})
    por_id = {mv.id: mv for mv in m.memes_vivos()}
    assert por_id["PF-mar"].peso == 6.3


def test_conexion_a_meme_inexistente_loguea_y_no_rompe(tmp_path, caplog):
    datos = {
        "ser_id": "x", "mana_max": 50,
        "memes": [{"id": "a", "tipo": "operativo", "texto": "t", "peso_inicial": 1.0,
                   "conexiones": ["fantasma"]}],
    }
    p = Persistencia(tmp_path / "mundo")

    with caplog.at_level(logging.WARNING):
        m = Memetario(Ser(**datos), p)

    assert ("a", "fantasma") not in m.grafo.edges
    assert any("fantasma" in r.message for r in caplog.records)


def test_las_aristas_del_grafo_saben_si_refuerzan_o_tensionan(tmp_path):
    datos = {
        "ser_id": "x", "mana_max": 50,
        "memes": [
            {"id": "a", "tipo": "operativo", "texto": "ta", "peso_inicial": 5.0,
             "conexiones": ["b"], "tensiones": ["c"]},
            {"id": "b", "tipo": "operativo", "texto": "tb", "peso_inicial": 5.0},
            {"id": "c", "tipo": "operativo", "texto": "tc", "peso_inicial": 5.0},
        ],
    }
    m = Memetario(Ser(**datos), Persistencia(tmp_path / "mundo"))

    assert m.grafo.edges["a", "b"]["tipo"] == "refuerzo"
    assert m.grafo.edges["a", "c"]["tipo"] == "tension"


def test_tension_a_meme_inexistente_loguea_y_no_rompe(tmp_path, caplog):
    datos = {
        "ser_id": "x", "mana_max": 50,
        "memes": [{"id": "a", "tipo": "operativo", "texto": "t", "peso_inicial": 1.0,
                   "tensiones": ["fantasma"]}],
    }
    with caplog.at_level(logging.WARNING):
        m = Memetario(Ser(**datos), Persistencia(tmp_path / "mundo"))

    assert ("a", "fantasma") not in m.grafo.edges
    assert any("fantasma" in r.message for r in caplog.records)


def test_ser_viejo_sin_tensiones_ni_funcion_carga_igual():
    # SER_EJEMPLO no declara los campos nuevos: retrocompatibilidad total, sin migración.
    ser = Ser(**SER_EJEMPLO)
    assert ser.memes[0].tensiones == []
    assert ser.memes[0].funcion is None


def test_funcion_invalida_es_rechazada():
    with pytest.raises(ValidationError):
        Meme(id="x", tipo="operativo", texto="t", peso_inicial=1.0, funcion="mistica")


def test_la_vista_viva_lleva_tensiones_y_funcion(tmp_path):
    datos = {
        "ser_id": "x", "mana_max": 50,
        "memes": [
            {"id": "a", "tipo": "operativo", "texto": "ta", "peso_inicial": 5.0,
             "tensiones": ["b"], "funcion": "moral"},
            {"id": "b", "tipo": "operativo", "texto": "tb", "peso_inicial": 5.0},
        ],
    }
    m = Memetario(Ser(**datos), Persistencia(tmp_path / "mundo"))

    por_id = {mv.id: mv for mv in m.memes_vivos()}
    assert por_id["a"].tensiones == ["b"]
    assert por_id["a"].funcion == "moral"
    assert por_id["b"].tensiones == []


def test_cargar_desde_json(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    (p.carpeta_seres / "pescador").mkdir(parents=True, exist_ok=True)
    (p.carpeta_seres / "pescador" / "ser.json").write_text(json.dumps(SER_EJEMPLO), encoding="utf-8")

    m = Memetario.cargar("pescador", p)

    assert m.ser.ser_id == "pescador"
    assert len(m.memes_vivos()) == 2
