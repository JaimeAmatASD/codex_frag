"""Tests del cliente Gemini real. Sin red: la respuesta HTTP se simula."""

import io
import urllib.error

import pytest

from codex.llm import ErrorLLM, GeminiClient


def test_error_http_se_traduce_a_error_llm(monkeypatch):
    """Un fallo de la API (p. ej. 429 de cuota) sale como ErrorLLM: el motor no
    conoce urllib, y la transmisión sabe degradar ante ErrorLLM (ADR-005)."""

    def _urlopen_caido(pedido, timeout):
        raise urllib.error.HTTPError(
            pedido.full_url, 429, "Too Many Requests", None, io.BytesIO(b"cuota agotada")
        )

    monkeypatch.setattr("urllib.request.urlopen", _urlopen_caido)
    cliente = GeminiClient(api_key="clave-de-prueba")

    with pytest.raises(ErrorLLM):
        cliente.responder("hola")
