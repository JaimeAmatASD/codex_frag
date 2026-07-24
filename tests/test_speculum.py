"""El SPECULUM mínimo, parte 1: el esquema y su fricción (mejora 05).

Deterministas, sin red (regla 5). Cubren las reglas que el doc de la mejora
exige de la validación: el degradé (delta acotado), las PF intocables, los
ids nuevos bien formados y sin colisión, y el tope de propuestas por mirada.
La consulta de trayectoria y el flujo aprobar/rechazar tienen sus propios
tests en los pasos siguientes.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codex.modelos import Meme, Ser
from codex.speculum import (
    DELTA_MAXIMO,
    Mirada,
    PropuestaAjuste,
    validar_contra_ser,
)


def _ser():
    return Ser(
        ser_id="tabernero",
        mana_max=40,
        memes=[
            Meme(id="pf_casa", tipo="fundacional", texto="Esta taberna es mi casa.",
                 peso_inicial=9.0),
            Meme(id="oido_fino", tipo="operativo", texto="Escucho más de lo que digo.",
                 peso_inicial=6.0, costo=15),
        ],
    )


def _mirada(**propuesta) -> Mirada:
    return Mirada(reflexion="Estoy siendo el que escucha.", propuestas=[propuesta])


# ----- El esquema solo -----

def test_el_degrade_rechaza_deltas_grandes():
    with pytest.raises(ValidationError, match="degradé"):
        PropuestaAjuste(tipo="ajustar_peso", meme_id="oido_fino",
                        delta=DELTA_MAXIMO + 0.5, justificacion="me lo merezco")


def test_un_ajuste_de_cero_no_propone_nada():
    with pytest.raises(ValidationError, match="no propone nada"):
        PropuestaAjuste(tipo="ajustar_peso", meme_id="oido_fino",
                        delta=0, justificacion="por las dudas")


def test_un_experimental_nace_humilde_y_con_id_bien_formado():
    with pytest.raises(ValidationError):
        _mirada(tipo="proponer_experimental", meme_id="sospecha_nueva",
                texto="Quizás hablo de más.", peso_inicial=8.0, costo=10,
                justificacion="peso demasiado alto para nacer")
    with pytest.raises(ValidationError, match="id inválido"):
        _mirada(tipo="proponer_experimental", meme_id="Sospecha Nueva",
                texto="Quizás hablo de más.", peso_inicial=2.0, costo=10,
                justificacion="el id trae mayúsculas y espacios")


def test_mirarse_no_es_refundarse_tope_de_propuestas():
    ajuste = {"tipo": "ajustar_peso", "meme_id": "oido_fino", "delta": 1.0,
              "justificacion": "lo uso siempre"}
    with pytest.raises(ValidationError):
        Mirada(reflexion="quiero cambiarlo todo", propuestas=[ajuste] * 4)


def test_cero_propuestas_es_una_respuesta_valida():
    mirada = Mirada(reflexion="La evidencia no me pide cambios.")
    assert mirada.propuestas == []


# ----- Contra el ser concreto -----

def test_las_pf_son_intocables_por_esta_via():
    mirada = _mirada(tipo="ajustar_peso", meme_id="pf_casa", delta=-2.0,
                     justificacion="ya no siento que sea mi casa")
    with pytest.raises(ValueError, match="piedra fundacional"):
        validar_contra_ser(mirada, _ser())


def test_no_se_ajusta_un_meme_que_el_ser_no_tiene():
    mirada = _mirada(tipo="ajustar_peso", meme_id="valentia", delta=1.0,
                     justificacion="me gustaría tenerla")
    with pytest.raises(ValueError, match="no tiene"):
        validar_contra_ser(mirada, _ser())


def test_un_experimental_no_puede_pisar_un_id_existente():
    mirada = _mirada(tipo="proponer_experimental", meme_id="oido_fino",
                     texto="Escucho para juzgar.", peso_inicial=2.0, costo=10,
                     justificacion="ya existe")
    with pytest.raises(ValueError, match="ya existe"):
        validar_contra_ser(mirada, _ser())


def test_una_mirada_valida_pasa_entera():
    mirada = Mirada(
        reflexion="Escucho más de lo que digo, y el registro lo confirma.",
        propuestas=[
            {"tipo": "ajustar_peso", "meme_id": "oido_fino", "delta": 1.5,
             "justificacion": "movilizado en casi todas las situaciones registradas"},
            {"tipo": "proponer_experimental", "meme_id": "sospecha_del_silencio",
             "texto": "Callar también es una forma de mentir.", "peso_inicial": 2.0,
             "costo": 10, "justificacion": "las tensiones repetidas giran en torno a lo que callo"},
        ],
    )
    validar_contra_ser(mirada, _ser())   # no levanta
