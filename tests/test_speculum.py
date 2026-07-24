"""El SPECULUM mínimo, parte 1: el esquema y su fricción (mejora 05).

Deterministas, sin red (regla 5). Cubren las reglas que el doc de la mejora
exige de la validación: el degradé (delta acotado), las PF intocables, los
ids nuevos bien formados y sin colisión, y el tope de propuestas por mirada.
La consulta de trayectoria y el flujo aprobar/rechazar tienen sus propios
tests en los pasos siguientes.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codex.llm import ErrorLLM, MockClient
from codex.modelos import EstadoMeme, Meme, Ser
from codex.speculum import (
    DELTA_MAXIMO,
    MINIMO_MOVILIZACIONES,
    Mirada,
    PropuestaAjuste,
    consultar_trayectoria,
    mirarse,
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


# ----- La trayectoria -----

def _estado(movilizadas_oido: int = 12) -> dict[str, EstadoMeme]:
    return {
        "pf_casa": EstadoMeme(meme_id="pf_casa", peso=9.0, veces_en_loadout=15,
                              veces_movilizado=3),
        "oido_fino": EstadoMeme(meme_id="oido_fino", peso=7.5, veces_en_loadout=14,
                                veces_movilizado=movilizadas_oido),
    }


def test_la_trayectoria_muestra_deriva_silencio_y_suma_movilizaciones():
    ser = _ser()
    ser.memes.append(Meme(id="rencor_viejo", tipo="operativo",
                          texto="No perdono una deuda.", peso_inicial=5.0, costo=10))
    estado = _estado()
    estado["rencor_viejo"] = EstadoMeme(meme_id="rencor_viejo", peso=5.0,
                                        veces_en_loadout=6, veces_movilizado=0)

    t = consultar_trayectoria(ser, estado, [])

    assert t.movilizaciones == 15   # 3 + 12 + 0: el total del ser, no por meme
    assert "peso 6 → 7.5" in t.texto                      # la deriva se ve
    assert "piedra fundacional" in t.texto
    # El silencio se marca solo en el meme llevado y nunca usado.
    linea_rencor = next(l for l in t.texto.splitlines() if "rencor" in l.lower() or "deuda" in l)
    assert "nunca la usaste" in linea_rencor
    assert "nunca la usaste" not in next(l for l in t.texto.splitlines() if "Escucho" in l)


def test_las_grietas_repetidas_se_cuentan_desde_la_bitacora():
    tension = {"meme_a": "oido_fino", "meme_b": "pf_casa",
               "texto_a": "Escucho más de lo que digo.",
               "texto_b": "Esta taberna es mi casa.", "intensidad": 0.6}
    bitacora = [
        {"tipo": "dialogo", "terminos": {"tensiones": [tension]}},
        {"tipo": "transmision", "entrada": "x", "salida": "y",
         "terminos": {"tensiones": [tension], "distancia_raiz": 1}},
        {"tipo": "score", "terminos": {}},
    ]

    t = consultar_trayectoria(_ser(), _estado(), bitacora)

    assert "«Escucho más de lo que digo.» ⇄ «Esta taberna es mi casa.» — 2 veces" in t.texto


def test_las_deformaciones_recientes_entran_recortadas_y_con_distancia():
    bitacora = [{
        "tipo": "transmision",
        "entrada": "El faro se apagó una noche entera. " * 20,   # larguísima
        "salida": "Dicen que el faro parpadeó, pero yo no vi nada.",
        "terminos": {"distancia_raiz": 2},
    }]

    t = consultar_trayectoria(_ser(), _estado(), bitacora)

    assert "vos contás: «Dicen que el faro parpadeó" in t.texto
    assert "(distancia 2)" in t.texto
    assert "…" in t.texto   # la entrada larga quedó recortada


# ----- La mirada -----

def _mirada_json(**extra) -> str:
    return json.dumps({
        "reflexion": "Escucho más de lo que digo.",
        "propuestas": [{"tipo": "ajustar_peso", "meme_id": "oido_fino",
                        "delta": 1.0, "justificacion": "usada 12 veces de 14"}],
        **extra,
    })


def test_sin_material_suficiente_no_se_llama_al_cliente():
    cliente = MockClient(respuesta_por_defecto=_mirada_json())
    t = consultar_trayectoria(_ser(), _estado(movilizadas_oido=2), [])
    assert not t.suficiente

    mirada, reintento = mirarse(_ser(), t, cliente)

    assert mirada is None and reintento is False
    assert cliente.llamadas == []   # ni una llamada: sin material, el espejo calla


def test_el_camino_feliz_devuelve_la_mirada_y_el_prompt_lleva_todo():
    cliente = MockClient(respuesta_por_defecto=_mirada_json())
    t = consultar_trayectoria(_ser(), _estado(), [])
    assert t.movilizaciones >= MINIMO_MOVILIZACIONES

    mirada, reintento = mirarse(_ser(), t, cliente)

    assert mirada is not None and reintento is False
    assert mirada.propuestas[0].meme_id == "oido_fino"
    prompt = cliente.llamadas[-1]
    assert "Esta taberna es mi casa." in prompt      # las PF
    assert "llevada 14, usada 12" in prompt          # la trayectoria
    assert "máximo 2 puntos" in prompt               # el tope real, no un placeholder


def test_una_propuesta_invalida_se_reintenta_con_feedback():
    invalida = _mirada_json(propuestas=[{"tipo": "ajustar_peso", "meme_id": "pf_casa",
                                         "delta": -1.0, "justificacion": "tambalea"}])
    cliente = MockClient(respuestas=[invalida, _mirada_json()])
    t = consultar_trayectoria(_ser(), _estado(), [])

    mirada, reintento = mirarse(_ser(), t, cliente)

    assert mirada is not None and reintento is True
    assert "piedra fundacional" in cliente.llamadas[-1]   # el error viajó como feedback


def test_error_de_infraestructura_degrada_sin_reintentar(caplog):
    class ClienteCaido:
        def __init__(self):
            self.llamadas = 0
        def responder(self, prompt):
            self.llamadas += 1
            raise ErrorLLM("cuota agotada")

    cliente = ClienteCaido()
    t = consultar_trayectoria(_ser(), _estado(), [])

    mirada, _ = mirarse(_ser(), t, cliente)

    assert mirada is None
    assert cliente.llamadas == 1   # sin reintento: el feedback no arregla la red
    assert "cuota agotada" in caplog.text


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
