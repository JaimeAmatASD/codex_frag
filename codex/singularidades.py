"""Singularidades: eventos agendados en el reloj del mundo que ocurren pase lo que pase.

Mejora 03: una singularidad fija el CONTEXTO, no el resultado — "la noche de la
luna de sangre, el Hombre Pez espera en el risco". Al llegar su momento se
registra como HECHO RAÍZ en el grafo, igual que cualquier hecho; qué historias
produce depende de quiénes estaban y a quién se lo cuentan. Le da destino al
mundo sin quitarle libertad a nadie.

La semilla vive en `mundos/<m>/singularidades.json` (se versiona y se edita);
la marca de "ya disparada" vive SOLO en el SQLite del mundo (regla 1). El reset
del mundo las vuelve pendientes sin tocar la semilla.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from .hechos import Hecho

if TYPE_CHECKING:
    from .grafo_mundo import GrafoMundo
    from .persistencia import Persistencia


class Singularidad(Hecho):
    """Un hecho agendado: mismos campos que Hecho (su `momento` es la hora del
    mundo en que ocurrirá) más los seres que lo presencian de primera mano."""

    testigos_iniciales: list[str] = Field(default_factory=list)


def chequear_singularidades(
    persistencia: Persistencia, grafo: GrafoMundo, momento_actual: datetime
) -> list[Singularidad]:
    """Dispara las singularidades pendientes cuyo momento quedó alcanzado.

    Idempotente: la marca en SQLite garantiza que ninguna dispara dos veces.
    Cada disparo registra el hecho raíz por la puerta única y, si hay testigos
    iniciales, les da a conocer la raíz; si no hay, el hecho queda sin que
    nadie lo sepa todavía (el mundo sabe cosas que nadie sabe). Devuelve las
    que dispararon en esta pasada.
    """
    ya_disparadas = persistencia.singularidades_disparadas()
    disparadas = []
    for s in persistencia.cargar_singularidades():
        if s.id in ya_disparadas or datetime.fromisoformat(s.momento) > momento_actual:
            continue
        raiz = grafo.registrar_hecho(Hecho(**s.model_dump(exclude={"testigos_iniciales"})))
        for testigo in s.testigos_iniciales:
            grafo.registrar_conocimiento(testigo, raiz.id)
        persistencia.marcar_singularidad_disparada(s.id, momento_actual.isoformat())
        disparadas.append(s)
    return disparadas
