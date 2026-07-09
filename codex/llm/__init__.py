"""Capa LLM: la interfaz `ClienteLLM`, el MockClient para tests (regla 5) y el
cliente real mínimo (GeminiClient, paso 2). El router de tiers llega en pasos
posteriores; por ahora, un solo modelo barato configurable por entorno."""

from .gemini_client import GeminiClient
from .mock_client import ClienteLLM, ErrorLLM, MockClient

__all__ = ["ClienteLLM", "ErrorLLM", "GeminiClient", "MockClient"]
