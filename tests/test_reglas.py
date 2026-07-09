"""Tests de la interfaz SistemaDeReglas (ADR-002): el contexto que el núcleo arma
para el enchufe, y los efectos mecánicos que el motor aplica por la puerta única.
El enchufe propone, el motor dispone (espejo del ADR-001)."""

import json

import numpy as np
import pytest

from codex.clocks import Clock
from codex.embeddings import Embeddings
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia
from codex.reglas import AccionDeclarada, AvanzarClock, PagarStress, aplicar_efectos, contexto_para

SER = {
    "ser_id": "pescador",
    "mana_max": 40,
    "memes": [
        {"id": "PF-mar", "tipo": "fundacional", "texto": "El mar cobra lo que se le debe.", "peso_inicial": 9.0},
        {"id": "leer-aguas", "tipo": "operativo", "texto": "Sé leer las aguas antes de faenar.", "peso_inicial": 6.0, "costo": 20},
    ],
}

VECTORES = {
    "Salir a faenar con el mar picado.": [1.0, 0.0],
    "El mar cobra lo que se le debe.": [0.9, 0.1],
    "Sé leer las aguas antes de faenar.": [0.95, 0.05],
}


def _encoder(textos):
    return [np.asarray(VECTORES.get(t, [0.5, 0.5]), dtype=np.float32) for t in textos]


def test_contexto_para_arma_loadout_afinidades_y_estado(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    emb = Embeddings(p, encoder=_encoder)
    pescador = Memetario(Ser(**SER), p)
    p.guardar_estado_reglas("pescador", {"stress": 3.0})
    accion = AccionDeclarada(ser_id="pescador", accion="faenar",
                             descripcion="Salir a faenar con el mar picado.")

    ctx = contexto_para(accion, pescador, emb)

    # El cristal ante la acción, con la afinidad de CADA meme del loadout medida.
    assert set(ctx.afinidades) == set(ctx.loadout.ids)
    assert ctx.afinidades["leer-aguas"] > 0.9
    # Y el estado vivo de la capa de reglas, tal cual está en la puerta única.
    assert ctx.estado_reglas == {"stress": 3.0}


def test_pagar_stress_se_acumula_en_el_estado(tmp_path):
    p = Persistencia(tmp_path / "mundo")

    aplicar_efectos([PagarStress(ser_id="pescador", cantidad=2)], p)
    aplicar_efectos([PagarStress(ser_id="pescador", cantidad=2)], p)

    assert p.leer_estado_reglas("pescador")["stress"] == 4.0


def test_avanzar_clock_persiste_y_completa(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    p.guardar_clock(Clock(id="amenaza", nombre="El mar se enturbia", segmentos_total=4))

    aplicar_efectos([AvanzarClock(clock_id="amenaza", segmentos=3)], p)
    assert p.cargar_clock("amenaza").segmentos_actuales == 3

    aplicar_efectos([AvanzarClock(clock_id="amenaza")], p)
    assert p.cargar_clock("amenaza").estado == "completado"


def test_avanzar_un_clock_inexistente_se_rechaza(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    with pytest.raises(ValueError):
        aplicar_efectos([AvanzarClock(clock_id="no-existe")], p)
