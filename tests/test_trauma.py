"""Tests del desborde (docs/DISENO_DESBORDE.md): cuando la barra se llena, el ser
propone la cicatriz que le quedó. Sin red ni tokens (regla 5): MockClient con guion
y un medidor de similitud guionado."""

import json

import pytest

from codex.llm import ErrorLLM, MockClient
from codex.modelos import Meme, Ser
from codex.trauma import SituacionDesborde, desbordado, pedir_cicatriz

SITUACION = SituacionDesborde(
    accion="acechar",
    descripcion="Se queda quieto mirando el agua mientras los otros huyen.",
    categoria="mala_consecuencia",
    posicion="desesperada",
    narracion="Lo agarran del brazo y lo arrastran. No grita.",
    memes_movilizados=["la_vigilancia_como_escudo"],
    tensiones=["«el olvido» ⇄ «conozco esta tierra»"],
)


def _respuesta(texto="Gritar no sirve de nada.", meme_id="lo_que_no_se_grita", peso=2.0):
    return json.dumps({
        "escena": "Se quedó callado mucho después de que lo soltaran.",
        "cicatriz": {"meme_id": meme_id, "texto": texto, "peso_inicial": peso,
                     "costo": 10, "justificacion": "no gritó cuando lo arrastraron"},
    }, ensure_ascii=False)


@pytest.fixture()
def ser():
    return Ser(
        ser_id="el_vigilante",
        mana_max=40,
        memes=[
            Meme(id="PF-nadie-mira", tipo="fundacional",
                 texto="Nadie mira de verdad.", peso_inicial=9.0),
            Meme(id="la_vigilancia_como_escudo", tipo="operativo",
                 texto="Si miro bien, no me agarran.", peso_inicial=6.0, costo=20),
        ],
    )


@pytest.fixture()
def embeddings():
    """Medidor guionado (regla 5): solo esta pareja de textos es casi idéntica;
    todo lo demás es ajeno. Un encoder donde todo se parece a todo no probaría
    nada del chequeo de duplicado (lessons.md, 2026-07-30)."""
    class Guionado:
        disponible = True

        def similitud(self, a, b):
            pareja = {"La vigilancia me protege.", "Si miro bien, no me agarran."}
            return 0.95 if {a, b} == pareja else 0.1

    return Guionado()


class LlmCaido:
    def responder(self, prompt):
        raise ErrorLLM("sin red")


# ----- El umbral -----

def test_la_barra_llena_es_desborde():
    assert desbordado({"stress": 9.0}, stress_max=9) is True
    assert desbordado({"stress": 9.5}, stress_max=9) is True    # por si se pasó
    assert desbordado({"stress": 8.5}, stress_max=9) is False
    assert desbordado({}, stress_max=9) is False                # nunca jugó


# ----- La cicatriz -----

def test_la_cicatriz_llega_con_su_escena(ser, embeddings):
    cliente = MockClient(respuestas=[_respuesta()])

    cicatriz, reintento = pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    assert reintento is False
    assert "callado" in cicatriz.escena
    assert cicatriz.propuesta.tipo == "proponer_experimental"
    assert cicatriz.propuesta.meme_id == "lo_que_no_se_grita"
    assert cicatriz.propuesta.peso_inicial == 2.0


def test_una_cicatriz_que_el_ser_ya_tiene_llega_como_refuerzo(ser, embeddings):
    """Si la herida propuesta dice casi lo que el ser ya cree, no se inyecta una
    variante nueva: se refuerza la que ya está. Un ser no junta cinco versiones
    de la misma cicatriz."""
    cliente = MockClient(respuestas=[_respuesta(texto="La vigilancia me protege.")])

    cicatriz, _ = pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    assert cicatriz.propuesta.tipo == "ajustar_peso"
    assert cicatriz.propuesta.meme_id == "la_vigilancia_como_escudo"
    assert cicatriz.propuesta.delta > 0
    assert "callado" in cicatriz.escena          # la escena se conserva igual


def test_una_cicatriz_que_roza_una_piedra_fundacional_no_la_toca(ser, embeddings):
    """Las PF son intocables incluso para el trauma: si la herida se parece a una
    piedra, entra como experimental en vez de convertirse en un ajuste ilegal."""
    class RozaLaPiedra:
        disponible = True

        def similitud(self, a, b):
            # Solo la piedra se parece a la herida propuesta (que dice lo mismo).
            return 0.95 if a == b == "Nadie mira de verdad." else 0.1

    cliente = MockClient(respuestas=[_respuesta(texto="Nadie mira de verdad.")])

    cicatriz, _ = pedir_cicatriz(ser, SITUACION, cliente, RozaLaPiedra())

    assert cicatriz.propuesta.tipo == "proponer_experimental"


def test_el_peso_que_se_pasa_del_tope_se_rechaza_y_se_reintenta(ser, embeddings):
    """El degradé del espejo también rige acá: una cicatriz no nace fuerte."""
    cliente = MockClient(respuestas=[_respuesta(peso=9.0), _respuesta(peso=2.0)])

    cicatriz, reintento = pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    assert reintento is True
    assert cicatriz.propuesta.peso_inicial == 2.0


def test_una_respuesta_invalida_se_reintenta_una_vez(ser, embeddings):
    cliente = MockClient(respuestas=["no hay json acá", _respuesta()])

    cicatriz, reintento = pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    assert reintento is True
    assert cicatriz is not None


def test_si_el_llm_no_da_nada_valido_no_hay_cicatriz(ser, embeddings, caplog):
    cliente = MockClient(respuesta_por_defecto="nunca json")

    cicatriz, _ = pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    assert cicatriz is None
    assert "cicatriz" in caplog.text.lower()      # se loguea, no se traga (regla 3)


def test_si_el_llm_se_cae_degrada_con_aviso(ser, embeddings, caplog):
    cicatriz, _ = pedir_cicatriz(ser, SITUACION, LlmCaido(), embeddings)

    assert cicatriz is None
    assert "desborde" in caplog.text.lower()


# ----- El prompt -----

def test_el_prompt_muestra_los_ids_y_lo_que_acaba_de_pasar(ser, embeddings):
    """Si le pedimos un id, se lo mostramos (lessons.md, 2026-07-30); y la
    situación congelada tiene que llegar entera, o la cicatriz sale genérica."""
    cliente = MockClient(respuestas=[_respuesta()])

    pedir_cicatriz(ser, SITUACION, cliente, embeddings)

    prompt = cliente.llamadas[0]
    assert "la_vigilancia_como_escudo" in prompt
    assert "Se queda quieto mirando el agua" in prompt
    assert "Lo agarran del brazo" in prompt
    assert "el_vigilante" in prompt
