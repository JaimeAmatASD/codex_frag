"""El latido: la vida cotidiana de un ser, sin LLM.

Hoy un ser solo existe cuando el autor le presta atención, y eso sesga la
personalidad: la experiencia es 100% picos autorados. El latido arregla la base
de esa distribución con ticks de vida ordinaria, baratos y deterministas: el
memetario se activa contra situaciones de rutina (`rutina.json` del ser), los
memes usados reciben un micro-refuerzo, y el equilibrio entre decaimiento y
rutina pasa a ser el estado de reposo de la personalidad.

Principio rector: este módulo NO importa ningún cliente LLM y ninguna de sus
firmas acepta uno. Los picos siguen existiendo: 1 de cada N ticks se marca
"caliente" y entra a una cola (`pendientes`); resolverla es trabajo de afuera
(el Taller, y en fase 2 un modo auto). Cero tokens por construcción.

Todas las funciones son puras respecto de sus dependencias inyectadas (regla 5):
embeddings, persistencia, reloj y `rng: random.Random` entran por parámetro.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel, field_validator

from .bias import BiasCircadiano
from .decaimiento import TASA_REFUERZO_RUTINA, aplicar_decaimiento, reforzar_movilizados
from .embeddings import Embeddings
from .loadout import calcular_loadout
from .memetario import Memetario
from .modelos import Loadout, TipoMeme
from .persistencia import Persistencia
from .reloj import RelojSimple

logger = logging.getLogger(__name__)

TICKS_POR_DIA = 3          # provisional: mañana / tarde / noche
PROB_INTERFERENCIA = 0.05  # provisional: el meme no convocado que irrumpe (el pensamiento de ducha)
PROB_ESCALADA = 0.05       # provisional: 1 de cada 20 ticks se marca caliente
# Franjas horarias (provisional): mañana 6-12, tarde 12-20, noche 20-6.
HORAS_DE_TICK = (9, 15, 22)  # provisional: la hora del tick de cada franja


# ----- La rutina: contenido, no motor (vive en la carpeta del ser, ADR-007) -----

class PlantillaRutina(BaseModel):
    id: str
    texto: str                      # la situación, en el lenguaje que el loadout va a embeddear
    franja: Literal["mañana", "tarde", "noche", "cualquiera"] = "cualquiera"
    peso: float = 1.0               # frecuencia relativa dentro de su franja

    @field_validator("texto")
    @classmethod
    def _texto_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("el texto de una plantilla de rutina no puede estar vacío")
        return v


class Rutina(BaseModel):
    plantillas: list[PlantillaRutina]

    @field_validator("plantillas")
    @classmethod
    def _validar_plantillas(cls, v: list[PlantillaRutina]) -> list[PlantillaRutina]:
        if not 3 <= len(v) <= 20:
            raise ValueError(f"una rutina lleva entre 3 y 20 plantillas (tiene {len(v)})")
        ids = [p.id for p in v]
        if len(set(ids)) != len(ids):
            raise ValueError("hay ids de plantilla repetidos en la rutina")
        return v


def cargar_rutina(persistencia: Persistencia, ser_id: str) -> Rutina | None:
    """La rutina validada del ser, o None si no tiene (un ser sin rutina no late)."""
    datos = persistencia.cargar_rutina(ser_id)
    return Rutina(**datos) if datos is not None else None


# ----- Los resultados del latido -----

class ResultadoTick(BaseModel):
    """Lo que pasó en un momento de vida ordinaria."""

    momento: str                # reloj del mundo en ISO
    situacion_id: str
    situacion: str
    loadout_ids: list[str]
    movilizados: list[str]      # incluye la irrupción, si la hubo
    irrupcion: str | None = None
    escalado: bool = False      # marcado caliente: entra a la cola de pendientes


class ResumenDia(BaseModel):
    """Un día vivido: sus ticks y los pesos al cierre (tras el decaimiento)."""

    fecha: str                  # el día del mundo (YYYY-MM-DD)
    ticks: list[ResultadoTick]
    pesos_fin_de_dia: dict[str, float]


class MomentoCaliente(BaseModel):
    """Un tick escalado, esperando en la cola. El tick no lo resuelve: resolverlo
    ES jugarlo con las herramientas de siempre (transmitir, Score, diálogo)."""

    ser_id: str
    momento: str            # reloj del mundo en el tick
    situacion: str          # el texto de la plantilla
    loadout_ids: list[str]  # el cristal que estaba despierto en ese momento


class ResumenVida(BaseModel):
    """El saldo de una corrida de días vividos."""

    ser_id: str
    dias: list[ResumenDia]
    pesos_inicio: dict[str, float]
    pesos_fin: dict[str, float]
    pendientes: list[MomentoCaliente]

    @property
    def deltas(self) -> dict[str, float]:
        """Cuánto movió la vida cada peso, inicio → fin."""
        return {
            mid: self.pesos_fin[mid] - peso
            for mid, peso in self.pesos_inicio.items()
            if mid in self.pesos_fin
        }


# ----- El latido -----

def franja_de(hora: int) -> str:
    """Mapea la hora del reloj del mundo a su franja."""
    if 6 <= hora < 12:
        return "mañana"
    if 12 <= hora < 20:
        return "tarde"
    return "noche"


def elegir_situacion(
    rutina: Rutina, reloj: RelojSimple, rng: random.Random
) -> PlantillaRutina:
    """Filtra las plantillas por la franja actual (más las `cualquiera`) y
    muestrea ponderado por `peso`."""
    franja = franja_de(reloj.ahora().hour)
    candidatas = [p for p in rutina.plantillas if p.franja in (franja, "cualquiera")]
    if not candidatas:
        # Degradación anotada (regla 3): una rutina sin plantillas para esta
        # franja vive igual, con lo que tenga.
        logger.warning("La rutina no tiene plantillas para la franja '%s'; uso todas.", franja)
        candidatas = list(rutina.plantillas)
    return rng.choices(candidatas, weights=[p.peso for p in candidatas], k=1)[0]


def movilizar(loadout: Loadout, rng: random.Random) -> list[str]:
    """Movilización estocástica ponderada por el score de cada meme del loadout:
    1 o 2 memes sin reemplazo (provisional). Nada de argmax: el argmax cava
    surcos y fosiliza la personalidad. Las PF no se movilizan por rutina (no se
    refuerzan ni decaen: su presencia en el loadout ya quedó registrada)."""
    pool = [m for m in loadout.seleccionados if m.tipo != TipoMeme.FUNDACIONAL]
    if not pool:
        return []
    cuantos = min(rng.randint(1, 2), len(pool))
    elegidos: list[str] = []
    for _ in range(cuantos):
        pesos = [max(loadout.scores.get(m.id, 0.0), 0.0) for m in pool]
        if sum(pesos) > 0:
            elegido = rng.choices(pool, weights=pesos, k=1)[0]
        else:
            elegido = rng.choice(pool)   # todos con score nulo: uniforme
        elegidos.append(elegido.id)
        pool.remove(elegido)
    return elegidos


def interferir(
    memetario: Memetario, loadout: Loadout, rng: random.Random
) -> str | None:
    """Con probabilidad `PROB_INTERFERENCIA`, un meme vivo NO fundacional que
    quedó fuera del loadout irrumpe (la interferencia productiva pendiente del
    mapa de reuso de Fray Tomás). Elección uniforme: la irrupción no respeta
    jerarquías. Devuelve su id para movilizarlo, o None si no irrumpió nada."""
    if rng.random() >= PROB_INTERFERENCIA:
        return None
    en_loadout = set(loadout.ids)
    afuera = [
        m for m in memetario.memes_vivos()
        if m.tipo != TipoMeme.FUNDACIONAL and m.id not in en_loadout
    ]
    if not afuera:
        return None
    return rng.choice(afuera).id


def tick_de_vida(
    memetario: Memetario,
    rutina: Rutina,
    reloj: RelojSimple,
    persistencia: Persistencia,
    embeddings: Embeddings,
    rng: random.Random,
) -> ResultadoTick:
    """Un momento de vida ordinaria: situación → cristal → uso → micro-refuerzo.
    El tick no resuelve la escalada; solo la marca."""
    situacion = elegir_situacion(rutina, reloj, rng)
    loadout = calcular_loadout(
        memetario, situacion.texto, embeddings, bias=BiasCircadiano(reloj)
    )
    movilizados = movilizar(loadout, rng)
    irrupcion = interferir(memetario, loadout, rng)
    todos = movilizados + ([irrupcion] if irrupcion else [])

    reforzar_movilizados(memetario, persistencia, todos, tasa=TASA_REFUERZO_RUTINA)

    momento = reloj.ahora().isoformat()
    persistencia.registrar_activaciones(
        memetario.ser.ser_id, momento, situacion.texto,
        loadout_ids=loadout.ids, movilizados_ids=movilizados, regimen="rutina",
    )
    if irrupcion:
        # La irrupción va en su propio registro: no estaba en el cristal
        # convocado, y la tabla no puede mentir sobre cómo llegó.
        persistencia.registrar_activaciones(
            memetario.ser.ser_id, momento, situacion.texto,
            loadout_ids=[irrupcion], movilizados_ids=[irrupcion],
            regimen="interferencia",
        )

    return ResultadoTick(
        momento=momento,
        situacion_id=situacion.id,
        situacion=situacion.texto,
        loadout_ids=loadout.ids,
        movilizados=todos,
        irrupcion=irrupcion,
        escalado=rng.random() < PROB_ESCALADA,
    )


def dia_de_vida(
    memetario: Memetario,
    rutina: Rutina,
    reloj: RelojSimple,
    persistencia: Persistencia,
    embeddings: Embeddings,
    rng: random.Random,
) -> ResumenDia:
    """Un día del mundo: `TICKS_POR_DIA` ticks (uno por franja) y al cierre UN
    ciclo de decaimiento. Acá vive el equilibrio: lo que la rutina toca resiste
    el decaimiento; lo que no toca, decae hacia el piso."""
    fecha = reloj.ahora().date()
    ticks: list[ResultadoTick] = []
    for hora in HORAS_DE_TICK[:TICKS_POR_DIA]:
        reloj.fijar(datetime.combine(fecha, time(hour=hora)))
        ticks.append(tick_de_vida(memetario, rutina, reloj, persistencia, embeddings, rng))
    aplicar_decaimiento(memetario, persistencia, ciclos=1.0)
    # El día termina: el reloj queda al comienzo del siguiente.
    reloj.fijar(datetime.combine(fecha + timedelta(days=1), time(0)))
    return ResumenDia(
        fecha=fecha.isoformat(),
        ticks=ticks,
        pesos_fin_de_dia={m.id: m.peso for m in memetario.memes_vivos()},
    )


def vivir(
    dias: int,
    memetario: Memetario,
    rutina: Rutina | None,
    reloj: RelojSimple,
    persistencia: Persistencia,
    embeddings: Embeddings,
    rng: random.Random,
) -> ResumenVida | None:
    """El bucle de días. Si el ser no tiene rutina, no late: se salta con un
    warning (regla 3: toda degradación queda anotada). Devuelve los pesos
    inicio→fin, el resumen por día y la cola de pendientes calientes."""
    if rutina is None:
        logger.warning("El ser %s no tiene rutina.json: no late.", memetario.ser.ser_id)
        return None

    pesos_inicio = {m.id: m.peso for m in memetario.memes_vivos()}
    resumenes: list[ResumenDia] = []
    pendientes: list[MomentoCaliente] = []
    for _ in range(dias):
        resumen = dia_de_vida(memetario, rutina, reloj, persistencia, embeddings, rng)
        resumenes.append(resumen)
        pendientes.extend(
            MomentoCaliente(
                ser_id=memetario.ser.ser_id,
                momento=t.momento,
                situacion=t.situacion,
                loadout_ids=t.loadout_ids,
            )
            for t in resumen.ticks
            if t.escalado
        )

    return ResumenVida(
        ser_id=memetario.ser.ser_id,
        dias=resumenes,
        pesos_inicio=pesos_inicio,
        pesos_fin={m.id: m.peso for m in memetario.memes_vivos()},
        pendientes=pendientes,
    )
