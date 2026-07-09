"""Clocks de progreso: la presión narrativa hecha visible (paso 3, versión mínima).

Un clock es un círculo de segmentos que se llena; al completarse, algo pasa en el
mundo. Es el mecanismo nativo de Codex para todo lo que cambia gradualmente. En el
paso 3 existe UN clock de amenaza que avanza con las malas consecuencias de los
Scores; tipos, visibilidad y triggers llegan en pasos posteriores.

El clock completado NO se borra: queda como memoria del mundo (con qué presiones
vivió un personaje se reconstruye desde acá). Su estado vive en SQLite y toda
escritura pasa por la puerta única (regla 2: `Persistencia.guardar_clock`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Clock(BaseModel):
    """Un proceso del mundo en marcha: cuánto avanzó y cuánto le falta."""

    id: str
    nombre: str
    segmentos_total: Literal[4, 6, 8, 12]   # la magnitud del proceso (Blades)
    segmentos_actuales: int = 0
    estado: Literal["activo", "completado"] = "activo"


def avanzar(clock: Clock, segmentos: int = 1) -> Clock:
    """Devuelve el clock avanzado (satura en el total y completa). Un clock ya
    completado no cambia: su evento ya disparó, es historia."""
    if clock.estado == "completado":
        return clock
    actuales = min(clock.segmentos_actuales + segmentos, clock.segmentos_total)
    estado = "completado" if actuales >= clock.segmentos_total else "activo"
    return clock.model_copy(update={"segmentos_actuales": actuales, "estado": estado})
