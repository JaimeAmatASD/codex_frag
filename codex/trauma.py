"""El desborde: cuando la barra de stress se llena, el ser propone su cicatriz.

Encarna la regla 1 (el motor manda, el LLM ilustra): el modelo escribe la escena y
sugiere la idea que le quedó, y el motor valida el esquema, recorta el peso y
chequea que no sea una herida que el ser ya tiene. Acá NO se aplica nada — la
cicatriz es una propuesta hasta que el autor disponga, como en el SPECULUM
(docs/DISENO_DESBORDE.md).

Vive pegado al memetario y a las reglas a propósito: el stress y el cristal se
hablan todo el tiempo, y separarlos en silos con interfaz limpia sería fricción
permanente. Lo único que este módulo no hace es escribir: de eso se encarga la
puerta única cuando el autor aprueba.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from string import Template

from pydantic import BaseModel, Field, ValidationError

from .embeddings import Embeddings
from .llm import ClienteLLM, ErrorLLM
from .modelos import Ser, TipoMeme
from .prompts import anotar_funcion
from .speculum import (
    INTENTOS,
    PESO_MAX_EXPERIMENTAL,
    Propuesta,
    PropuestaAjuste,
    PropuestaExperimental,
)

logger = logging.getLogger(__name__)

TEMPLATE_TRAUMA = Path(__file__).parent.parent / "templates" / "trauma.txt"

# Por encima de esta similitud, la cicatriz propuesta "ya la tiene": en vez de
# inyectar una variante nueva se refuerza la que ya está. Provisional.
UMBRAL_DUPLICADO = 0.80
# Cuánto se refuerza el meme existente cuando la herida ya estaba grabada. Dentro
# del degradé del espejo (DELTA_MAXIMO = 2.0): una noche no refunda a nadie.
DELTA_CICATRIZ = 1.0


class SituacionDesborde(BaseModel):
    """La escena congelada en el momento en que la barra se llenó.

    Es lo único que el LLM ve del desborde, así que lo que no entre acá no puede
    aparecer en la cicatriz. Un desborde sin situación (stress puesto a mano) es
    válido: los campos quedan vacíos y el prompt lo dice."""

    accion: str = ""
    descripcion: str = ""
    categoria: str = ""
    posicion: str = ""
    narracion: str = ""
    memes_movilizados: list[str] = Field(default_factory=list)
    tensiones: list[str] = Field(default_factory=list)

    def texto(self) -> str:
        """El bloque legible que entra al prompt."""
        if not (self.descripcion or self.narracion):
            return "- (no quedó registro de la escena: la barra se llenó fuera de un Score)"
        lineas = [f"- lo que intentaste: {self.descripcion} (acción: {self.accion})"]
        if self.posicion:
            lineas.append(f"- en qué posición estabas: {self.posicion}")
        if self.categoria:
            lineas.append(f"- cómo salió: {self.categoria}")
        if self.narracion:
            lineas.append(f"- lo que se narró: {self.narracion}")
        if self.memes_movilizados:
            lineas.append(f"- las ideas tuyas que usaste ahí: {', '.join(self.memes_movilizados)}")
        if self.tensiones:
            lineas.append(f"- la grieta que tenías abierta: {'; '.join(self.tensiones)}")
        return "\n".join(lineas)


class Cicatriz(BaseModel):
    """Lo que el desborde deja: la escena que se lee y la propuesta que se aprueba."""

    escena: str = Field(min_length=1)
    propuesta: Propuesta


def desbordado(estado_reglas: dict, stress_max: float) -> bool:
    """La barra llegó al techo. Un ser sin stress registrado nunca desbordó."""
    return estado_reglas.get("stress", 0.0) >= stress_max


def armar_prompt(ser: Ser, situacion: SituacionDesborde) -> str:
    """Rellena el template. Los memes van CON su id porque abajo le pedimos un id:
    si solo mostrás el texto, el modelo devuelve el texto (pasó con el SPECULUM el
    2026-07-30 y la mirada entera se perdía)."""
    pf = [m for m in ser.memes if m.tipo == TipoMeme.FUNDACIONAL]
    otros = [m for m in ser.memes if m.tipo != TipoMeme.FUNDACIONAL]
    template = Template(TEMPLATE_TRAUMA.read_text(encoding="utf-8"))
    return template.substitute(
        ser_id=ser.ser_id,
        pf="\n".join(f"- «{m.texto}»{anotar_funcion(m)}" for m in pf) or "- (ninguna)",
        memes="\n".join(f"- «{m.texto}» [id: {m.id}]{anotar_funcion(m)}" for m in otros)
        or "- (ninguna)",
        situacion=situacion.texto(),
        peso_max_experimental=f"{PESO_MAX_EXPERIMENTAL:g}",
    )


def _ya_la_tiene(texto: str, ser: Ser, embeddings: Embeddings) -> str | None:
    """El id del meme NO fundacional que ya dice casi lo mismo, o None.

    Las piedras fundacionales quedan afuera a propósito: son intocables incluso
    para el trauma (regla del SPECULUM que acá también vale). Si la herida roza
    una piedra, se loguea y la cicatriz entra como idea nueva."""
    for m in ser.memes:
        if embeddings.similitud(texto, m.texto) < UMBRAL_DUPLICADO:
            continue
        if m.tipo == TipoMeme.FUNDACIONAL:
            logger.info(
                "La cicatriz de %s roza la piedra «%s»: entra como idea nueva, la piedra no se toca.",
                ser.ser_id, m.texto,
            )
            continue
        return m.id
    return None


def _parsear(cruda: str, ser: Ser, embeddings: Embeddings) -> Cicatriz:
    """Extrae el primer bloque JSON y arma la cicatriz validada.

    Levanta ValueError/ValidationError con mensaje claro: eso alimenta el
    reintento con feedback."""
    inicio, fin = cruda.find("{"), cruda.rfind("}")
    if inicio == -1 or fin <= inicio:
        raise ValueError("la respuesta no contiene un bloque JSON")
    datos = json.loads(cruda[inicio : fin + 1])
    escena = str(datos.get("escena", "")).strip()
    if not escena:
        raise ValueError("falta la escena: el desborde tiene que poder leerse")
    cruda_cicatriz = datos.get("cicatriz")
    if not isinstance(cruda_cicatriz, dict):
        raise ValueError("falta el objeto 'cicatriz'")

    # El esquema y sus topes son los del espejo: una cicatriz nace humilde.
    nueva = PropuestaExperimental(tipo="proponer_experimental", **cruda_cicatriz)

    duplicado = _ya_la_tiene(nueva.texto, ser, embeddings)
    if duplicado is not None:
        return Cicatriz(escena=escena, propuesta=PropuestaAjuste(
            tipo="ajustar_peso",
            meme_id=duplicado,
            delta=DELTA_CICATRIZ,
            justificacion=(
                f"lo que esto le dejó ya lo creía: se le grabó más hondo. {nueva.justificacion}"
            ),
        ))
    return Cicatriz(escena=escena, propuesta=nueva)


def pedir_cicatriz(
    ser: Ser,
    situacion: SituacionDesborde,
    cliente: ClienteLLM,
    embeddings: Embeddings,
) -> tuple[Cicatriz | None, bool]:
    """El ser desbordado propone su cicatriz. Devuelve (cicatriz, hubo_reintento);
    cicatriz None si no se pudo, degradando con log visible (regla 3).

    Acá no se aplica NADA: la barra no se toca y el memetario tampoco. El autor
    dispone en el Taller, de a una propuesta, como en el espejo."""
    prompt = armar_prompt(ser, situacion)
    actual = prompt
    for intento in range(1, INTENTOS + 1):
        try:
            cruda = cliente.responder(actual)
        except ErrorLLM as e:
            # Fallo de infraestructura: reintentar con feedback no ayuda (ADR-005).
            logger.warning("El LLM falló en el desborde de %s: %s", ser.ser_id, e)
            return None, intento > 1
        try:
            return _parsear(cruda, ser, embeddings), intento > 1
        except (ValueError, ValidationError) as e:
            logger.warning(
                "Cicatriz inválida de %s (intento %d): %s", ser.ser_id, intento, e
            )
            actual = (
                f"{prompt}\n\nTu respuesta anterior no fue válida porque: {e}\n"
                "Respondé SOLO con el JSON pedido, sin texto antes ni después."
            )
    return None, True
