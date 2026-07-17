"""Tests de la derivación de seres: deterministas, MockClient guionado, sin red.
El LLM propone, el motor valida, y acá no se guarda nada nunca."""

import json
import logging

import pytest
from pydantic import ValidationError

from codex.llm import ErrorLLM, MockClient
from taller.derivacion import SerDerivado, derivar_ser

PROPUESTA_VALIDA = {
    "ser_id": "veterinario",
    "mana_max": 40,
    "memes": [
        {"id": "pf_ayudar", "tipo": "fundacional",
         "texto": "Ningún ser que sufre me es ajeno.", "peso_inicial": 9.0, "costo": 0,
         "funcion": "moral", "tensiones": ["no_perdono"]},
        {"id": "no_perdono", "tipo": "operativo",
         "texto": "Lo que mi hijo hizo no tiene perdón.", "peso_inicial": 8.5, "costo": 20,
         "funcion": "emocional"},
        {"id": "miedo_soledad", "tipo": "operativo",
         "texto": "Si me quedo solo, no sé quién soy.", "peso_inicial": 6.0, "costo": 20,
         "funcion": "identitario"},
    ],
    "hoja": {"stress_max": 9, "acciones": {"curar": 4, "consolar": 2}},
}


def _respuesta(**cambios):
    return json.dumps({**PROPUESTA_VALIDA, **cambios}, ensure_ascii=False)


def test_respuesta_valida_puebla_la_estructura():
    cliente = MockClient(respuestas=[_respuesta()])

    propuesta, reintento = derivar_ser(cliente, "un veterinario de 62 años...")

    assert propuesta is not None and reintento is False
    assert propuesta.ser_id == "veterinario"
    assert any(m.tipo == "fundacional" for m in propuesta.memes)
    assert all("_" in m.id or m.id.isalnum() for m in propuesta.memes)
    assert propuesta.memes[0].funcion == "moral"
    assert propuesta.memes[0].tensiones == ["no_perdono"]
    assert propuesta.hoja.acciones["curar"] == 4
    # El relato viajó en el prompt.
    assert "un veterinario de 62 años" in cliente.llamadas[0]


def test_respuesta_invalida_reintenta_con_feedback_y_recupera():
    cliente = MockClient(respuestas=["esto no es JSON", _respuesta()])

    propuesta, reintento = derivar_ser(cliente, "relato")

    assert propuesta is not None and reintento is True
    assert "no fue válida porque" in cliente.llamadas[1]


def test_dos_invalidas_degradan_sin_guardar_nada(caplog):
    cliente = MockClient(respuestas=["nada", "tampoco"])

    with caplog.at_level(logging.WARNING):
        propuesta, reintento = derivar_ser(cliente, "relato")

    assert propuesta is None and reintento is True
    assert sum("inválida" in r.message for r in caplog.records) == 2


def test_error_de_infraestructura_no_reintenta(caplog):
    class ClienteCaido:
        def responder(self, prompt):
            raise ErrorLLM("429")

    with caplog.at_level(logging.WARNING):
        propuesta, reintento = derivar_ser(ClienteCaido(), "relato")

    assert propuesta is None and reintento is False


def test_id_de_meme_con_espacios_es_rechazado():
    memes = json.loads(json.dumps(PROPUESTA_VALIDA["memes"]))
    memes[1]["id"] = "no perdono al hijo"
    with pytest.raises(ValidationError, match="sin espacios"):
        SerDerivado(**{**PROPUESTA_VALIDA, "memes": memes})


def test_funcion_desconocida_es_rechazada():
    memes = json.loads(json.dumps(PROPUESTA_VALIDA["memes"]))
    memes[0]["funcion"] = "mistica"
    with pytest.raises(ValidationError):
        SerDerivado(**{**PROPUESTA_VALIDA, "memes": memes})


def test_tension_a_meme_ausente_es_rechazada():
    memes = json.loads(json.dumps(PROPUESTA_VALIDA["memes"]))
    memes[0]["tensiones"] = ["fantasma"]
    with pytest.raises(ValidationError, match="no existe"):
        SerDerivado(**{**PROPUESTA_VALIDA, "memes": memes})


def test_sin_piedra_fundacional_es_rechazado():
    memes = [m for m in json.loads(json.dumps(PROPUESTA_VALIDA["memes"]))
             if m["tipo"] != "fundacional"]
    with pytest.raises(ValidationError, match="fundacional"):
        SerDerivado(**{**PROPUESTA_VALIDA, "memes": memes})
