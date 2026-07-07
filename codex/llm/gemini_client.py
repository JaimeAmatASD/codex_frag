"""GeminiClient: el cliente LLM real mínimo del paso 2.

Un solo proveedor barato (línea de base del ADR-005), una clase, un método. Sin
router de tiers todavía: eso llega en pasos posteriores. Habla con la API REST de
Gemini vía urllib (sin SDK: una dependencia menos para una llamada HTTP simple).

Configuración por variables de entorno:
  - GEMINI_API_KEY   (obligatoria)
  - CODEX_LLM_MODELO (opcional; default "gemini-2.0-flash")
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

# Alias que Google mantiene apuntando al Flash vigente: los modelos con versión fija
# se retiran de la API (gemini-2.0-flash ya devuelve 404) y el alias sobrevive.
MODELO_POR_DEFECTO = "gemini-flash-latest"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
TIMEOUT_SEGUNDOS = 60


class GeminiClient:
    """Cliente real contra Gemini, implementa la interfaz `ClienteLLM`."""

    def __init__(self, api_key: str | None = None, modelo: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Falta la API key de Gemini: pasala como argumento o definí GEMINI_API_KEY."
            )
        self.modelo = modelo or os.environ.get("CODEX_LLM_MODELO", MODELO_POR_DEFECTO)

    def responder(self, prompt: str) -> str:
        pedido = urllib.request.Request(
            f"{URL_BASE}/{self.modelo}:generateContent",
            data=json.dumps(
                {"contents": [{"parts": [{"text": prompt}]}]}
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
        )
        try:
            with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # El cuerpo del error dice el porqué (modelo retirado, key inválida, cuota);
            # urllib lo esconde y sin esto el diagnóstico es a ciegas (regla 3).
            logger.error("Error HTTP %s de Gemini: %s", e.code, e.read().decode("utf-8", "replace"))
            raise

        try:
            partes = datos["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in partes)
        except (KeyError, IndexError):
            # Respuesta sin texto (bloqueo de seguridad, etc.): no lo escondemos (regla 3).
            logger.error("Gemini devolvió una respuesta sin texto: %s", datos)
            return ""
