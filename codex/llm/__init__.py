"""Capa LLM. En el paso 1 solo está el MockClient (regla 5): el enchufe listo,
sin llamar a ninguna API. En pasos posteriores, un cliente real con la misma
interfaz `ClienteLLM` narrará a partir del loadout."""

from .mock_client import ClienteLLM, MockClient

__all__ = ["ClienteLLM", "MockClient"]
