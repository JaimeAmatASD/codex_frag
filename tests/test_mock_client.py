"""Tests del MockClient: determinista, sin red, conforme a la interfaz ClienteLLM."""

from codex.llm import ClienteLLM, MockClient


def test_es_determinista_y_registra_llamadas():
    a = MockClient(respuesta_por_defecto="ok")
    b = MockClient(respuesta_por_defecto="ok")

    assert a.responder("hola") == b.responder("hola") == "ok"
    assert a.llamadas == ["hola"]


def test_respuestas_guionadas_en_orden_y_luego_defecto():
    cliente = MockClient(respuestas=["uno", "dos"], respuesta_por_defecto="fin")

    assert cliente.responder("a") == "uno"
    assert cliente.responder("b") == "dos"
    assert cliente.responder("c") == "fin"  # se agotó el guion


def test_conforma_la_interfaz_cliente_llm():
    assert isinstance(MockClient(), ClienteLLM)
