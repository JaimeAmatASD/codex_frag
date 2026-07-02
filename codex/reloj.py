"""El reloj del mundo: la hora de la ficción, no la del sistema.

Regla clave del paso 1: ningún módulo llama a `datetime.now()`. La hora que importa es
la del mundo ficcional, y la define este reloj. Así el bias circadiano (y cualquier cosa
futura que dependa del tiempo) es reproducible: podemos poner el mundo a las 3 de la
mañana en un test sin esperar a que sea de madrugada de verdad.

`RelojDelMundo` es la abstracción (cualquier reloj que sepa decir su hora). `RelojSimple`
es la implementación del paso 1: una hora que se fija y se avanza a mano.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol


class RelojDelMundo(Protocol):
    """Cualquier cosa que sepa decir la hora del mundo."""

    def ahora(self) -> datetime: ...


class RelojSimple:
    """Reloj del mundo configurable: mantiene la hora ficcional y se avanza a mano."""

    def __init__(self, momento_inicial: datetime):
        self._momento = momento_inicial

    def ahora(self) -> datetime:
        return self._momento

    def avanzar(self, delta: timedelta) -> None:
        self._momento += delta

    def fijar(self, momento: datetime) -> None:
        self._momento = momento
