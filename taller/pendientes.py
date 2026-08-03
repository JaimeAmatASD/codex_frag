"""La cola de momentos calientes del latido: workflow autoral, fuera del motor.

Cada corrida de vida (POST /vida) apila acá los ticks escalados, un JSONL por
mundo (mismo patrón que la bitácora). No van a `estado.db` porque no son estado
diegético del mundo: son la lista de curaduría de James. El autor deja de
inventar situaciones y pasa a curar las que la vida trajo; jugado o descartado,
se marca en el mismo JSONL.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

CARPETA_POR_DEFECTO = Path(__file__).parent / "pendientes"

ESTADOS = ("pendiente", "jugado", "descartado")


def _ruta(carpeta: Path, mundo: str) -> Path:
    return carpeta / f"{mundo}.jsonl"


def registrar(carpeta: Path, mundo: str, momentos: list[dict]) -> list[dict]:
    """Apila momentos calientes nuevos a la cola del mundo. Cada uno gana un id
    propio, estado 'pendiente' y la fecha real (como la bitácora)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    nuevos = [
        {
            "id": uuid.uuid4().hex[:12],
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "estado": "pendiente",
            **m,
        }
        for m in momentos
    ]
    with open(_ruta(carpeta, mundo), "a", encoding="utf-8") as f:
        for n in nuevos:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    return nuevos


def leer(carpeta: Path, mundo: str) -> list[dict]:
    """Toda la cola del mundo, la más reciente primero (pendientes y marcados:
    lo ya curado también se puede repasar)."""
    ruta = _ruta(carpeta, mundo)
    if not ruta.exists():
        return []
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in reversed(lineas) if linea.strip()]


def marcar(carpeta: Path, mundo: str, pendiente_id: str, estado: str) -> dict:
    """Marca un momento como jugado o descartado, reescribiendo su línea."""
    if estado not in ("jugado", "descartado"):
        raise ValueError(f"Un pendiente se marca 'jugado' o 'descartado', no '{estado}'.")
    ruta = _ruta(carpeta, mundo)
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    entradas = [json.loads(l) for l in lineas if l.strip()]
    for entrada in entradas:
        if entrada.get("id") == pendiente_id:
            entrada["estado"] = estado
            ruta.write_text(
                "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entradas),
                encoding="utf-8",
            )
            return entrada
    raise ValueError(f"No hay un pendiente con id {pendiente_id} en {mundo}.")
