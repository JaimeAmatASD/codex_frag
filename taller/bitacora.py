"""La bitácora del taller: pulir es comparar.

Cada prueba (transmisión o Score) queda registrada en un JSONL dentro de la
carpeta del mundo (`taller_bitacora.jsonl`): viaja con el mundo (ADR-003) y no es
estado del motor — es el registro autoral de James, con fecha real. El reset del
estado vivo NO la borra: las iteraciones anteriores son justo lo que se compara.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ARCHIVO = "taller_bitacora.jsonl"


def registrar(carpeta_mundo: Path, entrada: dict) -> None:
    entrada = {"fecha": datetime.now().isoformat(timespec="seconds"), **entrada}
    with open(carpeta_mundo / ARCHIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def leer(carpeta_mundo: Path) -> list[dict]:
    """Las entradas del mundo, la más reciente primero."""
    ruta = carpeta_mundo / ARCHIVO
    if not ruta.exists():
        return []
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in reversed(lineas) if linea.strip()]
