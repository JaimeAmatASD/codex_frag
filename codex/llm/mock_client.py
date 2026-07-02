"""MockClient: un cliente LLM falso y determinista (regla 5).

No llama a ninguna API. Cumple dos propósitos en el paso 1:
  - Deja listo el "enchufe" del LLM: define la interfaz `ClienteLLM` que el cliente
    real (Gemini, Claude, lo que sea) implementará en pasos posteriores para narrar.
  - Permite testear flujos que en el futuro pasarán por el LLM, sin costo, sin red y
    sin respuestas aleatorias.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClienteLLM(Protocol):
    """Lo mínimo que el motor le pide a un LLM: dado un prompt, devolver texto."""

    def responder(self, prompt: str) -> str: ...


class MockClient:
    """Cliente LLM determinista para tests y para tener el enchufe listo."""

    def __init__(self, respuestas: list[str] | None = None, respuesta_por_defecto: str = ""):
        # Si se le da una lista, entrega esas respuestas en orden (guion); cuando se
        # agotan, usa la respuesta por defecto. Útil para tests reproducibles.
        self._guion = list(respuestas) if respuestas else []
        self._i = 0
        self.respuesta_por_defecto = respuesta_por_defecto
        self.llamadas: list[str] = []  # historial de prompts recibidos, para inspección.

    def responder(self, prompt: str) -> str:
        self.llamadas.append(prompt)
        if self._i < len(self._guion):
            respuesta = self._guion[self._i]
            self._i += 1
            return respuesta
        return self.respuesta_por_defecto or f"[mock] {prompt[:40]}"
