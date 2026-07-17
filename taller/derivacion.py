"""La derivación de seres: el relato del autor se vuelve la propuesta de un ser.

Es el flujo del jardinero aplicado a seres: plantás una descripción, crece una
estructura, podás. El LLM propone, el motor valida (estos modelos), el autor
cura: la propuesta cae en el formulario del Taller y JAMÁS se guarda sola.

El prompt vive en templates/derivar_ser.txt (editable desde el Taller). El ciclo
validar-reintentar-degradar es el de codex/transmision.py: un reintento con
feedback del error; si vuelve a fallar, mensaje claro al autor y log.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from string import Template
from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, model_validator

from codex.llm import ClienteLLM, ErrorLLM
from codex.modelos import Meme, TipoMeme

logger = logging.getLogger(__name__)

TEMPLATE_DERIVAR = Path(__file__).parent.parent / "templates" / "derivar_ser.txt"
INTENTOS = 2  # el original + un reintento con feedback; después se degrada.

# Los ids DERIVADOS van cortos, en minúsculas, sin espacios (los escritos a mano
# pueden ser lo que el autor quiera; esta regla es solo para lo que propone el LLM).
ID_DERIVADO = re.compile(r"^[a-z0-9_]+$")


class HojaDerivada(BaseModel):
    """La hoja mecánica propuesta (sin ser_id: se completa al guardar)."""

    stress_max: int = 9
    acciones: dict[str, Annotated[int, Field(ge=0, le=4)]]


class SerDerivado(BaseModel):
    """La propuesta completa del LLM, validada con los modelos reales del motor."""

    ser_id: str
    mana_max: int
    memes: list[Meme]   # tipo, funcion y tensiones los valida el modelo del motor
    hoja: HojaDerivada

    @model_validator(mode="after")
    def _bien_formado(self):
        if not ID_DERIVADO.match(self.ser_id):
            raise ValueError(f"ser_id inválido (minúsculas y guiones bajos): {self.ser_id!r}")
        for m in self.memes:
            if not ID_DERIVADO.match(m.id):
                raise ValueError(f"id de meme inválido (minúsculas, sin espacios): {m.id!r}")
        ids = {m.id for m in self.memes}
        for m in self.memes:
            for t in m.tensiones:
                if t not in ids:
                    raise ValueError(f"la tensión de {m.id!r} apunta a un meme que no existe: {t!r}")
        if not any(m.tipo == TipoMeme.FUNDACIONAL for m in self.memes):
            raise ValueError("el ser necesita al menos una piedra fundacional")
        return self


def armar_prompt_derivacion(descripcion: str) -> str:
    template = Template(TEMPLATE_DERIVAR.read_text(encoding="utf-8"))
    return template.substitute(descripcion=descripcion)


def _parsear_propuesta(cruda: str) -> SerDerivado:
    """Extrae el primer bloque JSON (tolerante a texto alrededor) y lo valida.
    Levanta ValueError/ValidationError si no sirve (patrón de transmision.py)."""
    inicio, fin = cruda.find("{"), cruda.rfind("}")
    if inicio == -1 or fin <= inicio:
        raise ValueError("la respuesta no contiene un bloque JSON")
    return SerDerivado(**json.loads(cruda[inicio : fin + 1]))


def derivar_ser(cliente: ClienteLLM, descripcion: str) -> tuple[SerDerivado | None, bool]:
    """Deriva la propuesta de un ser desde el relato. Devuelve (propuesta,
    hubo_reintento); propuesta None si ambos intentos fallaron (se degrada con
    log y el Taller le avisa al autor). Acá no se guarda NADA: curar es de James."""
    prompt = armar_prompt_derivacion(descripcion)
    actual = prompt
    for intento in range(1, INTENTOS + 1):
        try:
            cruda = cliente.responder(actual)
        except ErrorLLM as e:
            # Fallo de infraestructura: el reintento con feedback no ayuda (ADR-005).
            logger.warning("El LLM falló derivando un ser, no se reintenta: %s", e)
            return None, intento > 1
        try:
            return _parsear_propuesta(cruda), intento > 1
        except (ValueError, ValidationError) as e:
            logger.warning("Propuesta de ser inválida (intento %d): %s", intento, e)
            actual = (
                f"{prompt}\n\nTu respuesta anterior no fue válida porque: {e}\n"
                "Respondé SOLO con el JSON pedido, sin texto antes ni después."
            )
    return None, True
