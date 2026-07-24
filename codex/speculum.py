"""El SPECULUM mínimo: el ser que mira su propia trayectoria (mejora 05).

El órgano de la identidad del núcleo irrenunciable (docs/VISION_FASE0.md),
adaptado del prototipo de Fray Tomás (speculum.py + la fricción de
cambio_biografico.py). El ser lee su trayectoria REGISTRADA —qué memes
movilizó y cuánto, qué tensiones se le repiten, qué recibió y cómo lo
deformó— y produce dos cosas: una reflexión breve en primera persona
(quién estoy siendo) y PROPUESTAS tipadas de cambio chico.

La fricción heredada, en tres reglas que este módulo hace cumplir:
  - El degradé: ningún ajuste mueve más de DELTA_MAXIMO puntos por propuesta.
  - Las PF son INTOCABLES por esta vía: si una piedra tambalea, la reflexión
    puede DECIRLO (material para futuras crisis biográficas), jamás proponer
    cambiarla.
  - El LLM propone, el motor valida (estos modelos), el autor dispone: nada
    se aplica sin aprobación explícita en el Taller.

El prompt vive en templates/speculum.txt, editable como los demás.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from .modelos import Ser, TipoMeme

# La regla del degradé de Fray Tomás: nadie se refunda en una noche.
DELTA_MAXIMO = 2.0
# Un experimental nace humilde: es una sospecha sobre uno mismo, no una certeza.
PESO_MAX_EXPERIMENTAL = 3.0
# Mirarse no es refundarse: pocas propuestas por mirada.
MAX_PROPUESTAS = 3
# Umbral de material: sin esta acumulación de uso real, la reflexión es humo
# y el Taller no llama al LLM (movilizaciones totales del ser, no por meme).
MINIMO_MOVILIZACIONES = 10

# Los ids que propone el LLM van cortos, en minúsculas, sin espacios (misma
# regla que la derivación de seres; se repite acá porque codex no importa
# de taller, la capa va al revés).
ID_PROPUESTO = re.compile(r"^[a-z0-9_]+$")


class PropuestaAjuste(BaseModel):
    """Subir o bajar el peso VIVO de un meme existente, poco (el degradé)."""

    tipo: Literal["ajustar_peso"]
    meme_id: str
    delta: float
    justificacion: str = Field(min_length=1)   # citando la evidencia de la trayectoria

    @field_validator("delta")
    @classmethod
    def _delta_acotado(cls, v: float) -> float:
        if v == 0:
            raise ValueError("un ajuste de 0 no propone nada")
        if abs(v) > DELTA_MAXIMO:
            raise ValueError(
                f"el degradé no permite mover más de {DELTA_MAXIMO} puntos por propuesta"
            )
        return v


class PropuestaExperimental(BaseModel):
    """Un meme experimental NUEVO para probarse: una sospecha, no una certeza."""

    tipo: Literal["proponer_experimental"]
    meme_id: str
    texto: str = Field(min_length=1)
    peso_inicial: float = Field(gt=0, le=PESO_MAX_EXPERIMENTAL)
    costo: int = Field(ge=0)
    justificacion: str = Field(min_length=1)

    @field_validator("meme_id")
    @classmethod
    def _id_bien_formado(cls, v: str) -> str:
        if not ID_PROPUESTO.match(v):
            raise ValueError(f"id inválido (minúsculas y guiones bajos): {v!r}")
        return v


Propuesta = Annotated[
    PropuestaAjuste | PropuestaExperimental, Field(discriminator="tipo")
]


class Mirada(BaseModel):
    """La respuesta completa del espejo: quién estoy siendo + qué me ajustaría.

    Cero propuestas es válido: si la evidencia no pide cambios, no se inventan."""

    reflexion: str = Field(min_length=1)   # primera persona, sale de la evidencia
    propuestas: list[Propuesta] = Field(default_factory=list, max_length=MAX_PROPUESTAS)


def validar_contra_ser(mirada: Mirada, ser: Ser) -> None:
    """Lo que el esquema solo no puede chequear: que cada propuesta hable de
    ESTE ser. Levanta ValueError con mensaje claro (alimenta el reintento con
    feedback, patrón de derivacion.py). No toca nada: solo valida."""
    memes = {m.id: m for m in ser.memes}
    for p in mirada.propuestas:
        if p.tipo == "ajustar_peso":
            meme = memes.get(p.meme_id)
            if meme is None:
                raise ValueError(f"la propuesta ajusta un meme que el ser no tiene: {p.meme_id!r}")
            if meme.tipo == TipoMeme.FUNDACIONAL:
                raise ValueError(
                    f"{p.meme_id!r} es una piedra fundacional: intocable por esta vía "
                    "(si tambalea, decilo en la reflexión)"
                )
        else:   # proponer_experimental
            if p.meme_id in memes:
                raise ValueError(f"el id propuesto ya existe en el ser: {p.meme_id!r}")
