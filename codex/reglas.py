"""La interfaz SistemaDeReglas: el enchufe entre el núcleo y el motor de drama.

Decisión que manda (ADR-002): el sistema de reglas NO es parte del núcleo. Blades
es la primera implementación (`codex/blades.py`), no la esencia: cada autor podrá
reemplazarlo. Esta interfaz es la MÍNIMA que Blades necesita — nada de abstracción
universal de sistemas de juego; se generaliza recién cuando exista un segundo
sistema real.

El contrato tiene dos direcciones:
  - El núcleo le pasa al sistema un `ContextoAccion`: el loadout del ser ante la
    situación, la afinidad semántica de cada meme con la acción declarada, y el
    estado vivo de la capa de reglas (stress, etc.).
  - El sistema devuelve resultados tipados (`Evaluacion`, `Resolucion`) con efectos
    mecánicos a aplicar. El sistema PROPONE, el motor DISPONE (espejo del ADR-001):
    nada toca el estado salvo `aplicar_efectos`, que pasa por la puerta única.

La evaluación es visible ANTES de tirar: el jugador decide informado (ve posición,
efecto y dados, y elige tirar, empujar pagando stress, o retirarse sin costo).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from .clocks import avanzar
from .embeddings import Embeddings
from .loadout import Loadout, calcular_loadout
from .memetario import Memetario
from .persistencia import Persistencia


class AccionDeclarada(BaseModel):
    """Lo que el jugador declara en un Score: qué intenta y cómo."""

    ser_id: str
    accion: str        # nombre de la acción en la hoja mecánica (p. ej. "faenar")
    descripcion: str   # la declaración en texto libre; contra esto se mide afinidad


class Posicion(str, Enum):
    """Cuán riesgosa es la acción (qué tan graves serán las malas consecuencias)."""

    CONTROLADA = "controlada"
    ARRIESGADA = "arriesgada"
    DESESPERADA = "desesperada"


class NivelEfecto(str, Enum):
    """Cuánto cambia el mundo si la acción sale bien."""

    LIMITADO = "limitado"
    ESTANDAR = "estandar"
    GRANDE = "grande"


class CategoriaResultado(str, Enum):
    """Los tres resultados posibles: ninguna tirada puede quedar en 'no pasa nada'."""

    LIMPIO = "limpio"                      # dado más alto 6
    CON_COSTO = "con_costo"                # dado más alto 4-5
    MALA_CONSECUENCIA = "mala_consecuencia"  # dado más alto 1-3


class Empuje(str, Enum):
    """Las tres mejoras que el jugador puede comprar pagando stress (UNA por tirada)."""

    DADO_EXTRA = "dado_extra"
    MEJORAR_POSICION = "mejorar_posicion"
    MEJORAR_EFECTO = "mejorar_efecto"


class ContextoAccion(BaseModel):
    """Lo que el núcleo le entrega al sistema de reglas para resolver una acción."""

    loadout: Loadout
    afinidades: dict[str, float]                       # meme_id → similitud con la acción
    estado_reglas: dict[str, float] = Field(default_factory=dict)


class PagarStress(BaseModel):
    """El ser paga stress (la barra SUBE: pagar es acercarse al desbordamiento)."""

    tipo: Literal["pagar_stress"] = "pagar_stress"
    ser_id: str
    cantidad: int


class AvanzarClock(BaseModel):
    """Una consecuencia empuja un clock del mundo."""

    tipo: Literal["avanzar_clock"] = "avanzar_clock"
    clock_id: str
    segmentos: int = 1


EfectoMecanico = PagarStress | AvanzarClock


class Evaluacion(BaseModel):
    """Los términos de la tirada, visibles antes de tirar."""

    accion: AccionDeclarada
    posicion: Posicion
    efecto: NivelEfecto
    dados: int
    # Puntajes intermedios para inspeccionar por qué se evaluó así (patrón Loadout.scores).
    detalles: dict[str, float] = Field(default_factory=dict)


class Resolucion(BaseModel):
    """El resultado de la tirada: lo que el LLM narrará y el motor aplicará."""

    evaluacion: Evaluacion
    empuje: Empuje | None = None
    dados_tirados: list[int]
    categoria: CategoriaResultado
    efectos: list[EfectoMecanico] = Field(default_factory=list)


@runtime_checkable
class SistemaDeReglas(Protocol):
    """Lo mínimo que el núcleo le pide a un sistema de reglas."""

    def evaluar(self, accion: AccionDeclarada, contexto: ContextoAccion) -> Evaluacion: ...

    def tirar(
        self, evaluacion: Evaluacion, contexto: ContextoAccion, empuje: Empuje | None = None
    ) -> Resolucion: ...


def contexto_para(
    accion: AccionDeclarada, memetario: Memetario, embeddings: Embeddings, bias=None
) -> ContextoAccion:
    """Arma el contexto de una acción: el cristal del ser ante lo que declara
    (su loadout), la afinidad de cada meme seleccionado con la acción, y el
    estado vivo de la capa de reglas leído de la puerta única."""
    loadout = calcular_loadout(memetario, accion.descripcion, embeddings, bias=bias)
    afinidades = {
        m.id: embeddings.similitud(m.texto, accion.descripcion) for m in loadout.seleccionados
    }
    estado = memetario.persistencia.leer_estado_reglas(accion.ser_id)
    return ContextoAccion(loadout=loadout, afinidades=afinidades, estado_reglas=estado)


def aplicar_efectos(efectos: list[EfectoMecanico], persistencia: Persistencia) -> None:
    """Aplica los efectos que el sistema de reglas propuso, por la puerta única."""
    for efecto in efectos:
        if isinstance(efecto, PagarStress):
            estado = persistencia.leer_estado_reglas(efecto.ser_id)
            nuevo = estado.get("stress", 0.0) + efecto.cantidad
            persistencia.guardar_estado_reglas(efecto.ser_id, {"stress": nuevo})
        elif isinstance(efecto, AvanzarClock):
            clock = persistencia.cargar_clock(efecto.clock_id)
            if clock is None:
                raise ValueError(f"El efecto refiere a un clock inexistente: {efecto.clock_id}")
            persistencia.guardar_clock(avanzar(clock, efecto.segmentos))
