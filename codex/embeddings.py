"""Embeddings para la similitud semántica del loadout.

En producción usa fastembed con ONNX y el modelo all-MiniLM-L6-v2: local, en CPU,
liviano y gratis (heredado de Fray Tomás). Los vectores se cachean en SQLite a través
de la capa de persistencia, así no se recalculan.

Dos decisiones de diseño:
  - El codificador es INYECTABLE (`encoder`). En los tests le pasamos uno falso y
    determinista; no hace falta descargar el modelo (regla 5: tests sin red).
  - Si fastembed no carga, NO fallamos en silencio (regla 3): se registra un error y
    la similitud queda deshabilitada (devuelve 0.0). El loadout, al ver `disponible`
    en False, degrada a peso histórico y lo deja anotado en el log — justo el bug que
    Fray Tomás escondía.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable, Sequence

import numpy as np

logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "sentence-transformers/all-MiniLM-L6-v2"

# Un codificador toma una lista de textos y devuelve un vector por texto.
Encoder = Callable[[Sequence[str]], Sequence[np.ndarray]]


def coseno(a: np.ndarray, b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores. 0.0 si alguno es nulo."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class Embeddings:
    """Calcula y cachea vectores de texto, y mide similitud entre ellos."""

    def __init__(self, persistencia, modelo: str = MODELO_POR_DEFECTO, encoder: Encoder | None = None):
        self.persistencia = persistencia
        self.modelo = modelo
        self._encoder = encoder
        self._intento_carga = False
        # Queda en False si fastembed no carga. El loadout lo consulta para degradar.
        self.disponible = True

    def _asegurar_encoder(self) -> None:
        """Carga fastembed perezosamente, la primera vez que se necesita de verdad."""
        if self._encoder is not None or self._intento_carga:
            return
        self._intento_carga = True
        try:
            from fastembed import TextEmbedding

            modelo = TextEmbedding(model_name=self.modelo)
            self._encoder = lambda textos: list(modelo.embed(list(textos)))
            logger.info("fastembed cargado (modelo=%s).", self.modelo)
        except Exception as e:  # ImportError o fallo al bajar/cargar el modelo
            self.disponible = False
            logger.error(
                "No se pudo cargar fastembed (%s). La similitud semántica queda "
                "deshabilitada; el loadout degradará a peso histórico.", e,
            )

    def vector(self, texto: str) -> np.ndarray | None:
        """Devuelve el vector del texto (desde caché si existe), o None si no hay codificador."""
        clave = hashlib.sha256(f"{self.modelo}::{texto}".encode("utf-8")).hexdigest()
        blob = self.persistencia.leer_vector(clave)
        if blob is not None:
            return np.frombuffer(blob, dtype=np.float32)

        self._asegurar_encoder()
        if self._encoder is None:
            return None

        vec = np.asarray(self._encoder([texto])[0], dtype=np.float32)
        self.persistencia.guardar_vector(clave, vec.tobytes())
        return vec

    def similitud(self, texto_a: str, texto_b: str) -> float:
        """Similitud coseno entre dos textos. 0.0 si la similitud está deshabilitada."""
        va = self.vector(texto_a)
        vb = self.vector(texto_b)
        if va is None or vb is None:
            return 0.0
        return coseno(va, vb)
