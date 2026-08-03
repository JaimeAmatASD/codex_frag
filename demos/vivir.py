"""Vivir N días de rutina: el latido con embeddings reales y CERO LLM.

    ./venv/bin/python demos/vivir.py --mundo prueba --ser el_que_no_muere --dias 30
    ./venv/bin/python demos/vivir.py --mundo prueba --ser el_que_no_muere --dias 30 --semilla 42

Imprime el resumen (mayores subas y bajadas de peso, cuántos pendientes
quedaron) y la lista de pendientes. No los persiste: la cola de curaduría vive
en el Taller; esto es la corrida de mesa.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

from codex.embeddings import Embeddings
from codex.memetario import Memetario
from codex.persistencia import Persistencia
from codex.reloj import RelojSimple
from codex.vida import cargar_rutina, vivir


def main() -> None:
    parser = argparse.ArgumentParser(description="El latido: días de vida ordinaria, sin LLM.")
    parser.add_argument("--mundo", required=True)
    parser.add_argument("--ser", required=True)
    parser.add_argument("--dias", type=int, required=True)
    parser.add_argument("--semilla", type=int, default=None)
    args = parser.parse_args()

    carpeta = RAIZ / "mundos" / args.mundo
    if not carpeta.is_dir():
        sys.exit(f"No existe el mundo: {args.mundo}")
    p = Persistencia(carpeta)
    try:
        memetario = Memetario.cargar(args.ser, p)
        rutina = cargar_rutina(p, args.ser)
        if rutina is None:
            sys.exit(f"El ser {args.ser} no tiene rutina.json: no late.")

        momento = p.leer_momento_mundo()
        if momento is None:
            momento = "2026-01-01T00:00:00"
            print(f"Aviso: el mundo no tiene hora fijada; arranco en {momento}.")

        resumen = vivir(
            args.dias, memetario, rutina, RelojSimple(datetime.fromisoformat(momento)),
            p, Embeddings(p), random.Random(args.semilla),
        )

        print(f"\n{args.ser} vivió {len(resumen.dias)} día(s) en {args.mundo}.\n")
        deltas = sorted(resumen.deltas.items(), key=lambda kv: kv[1], reverse=True)
        for meme_id, delta in deltas:
            print(f"  {resumen.pesos_inicio[meme_id]:6.2f} → {resumen.pesos_fin[meme_id]:6.2f}  "
                  f"({delta:+.2f})  {meme_id}")

        print(f"\nPendientes calientes: {len(resumen.pendientes)}")
        for m in resumen.pendientes:
            print(f"  · {m.momento} — «{m.situacion}»")
    finally:
        p.cerrar()


if __name__ == "__main__":
    main()
