"""Demo de la prueba del paso 1, con embeddings REALES (fastembed, all-MiniLM-L6-v2).

Corre así, desde la raíz del proyecto:
    ./venv/bin/python demos/prueba_paso1.py

Carga dos seres (un pescador supersticioso y un comerciante escéptico), les da la misma
noticia, y muestra que cada uno arma un loadout coherente con quién es. Después muestra
un ciclo de uso: el ser moviliza su meme principal y su peso se refuerza (regla 4).

Usa una carpeta temporal para no ensuciar mundos/prueba ni cambiar resultados entre
corridas (los pesos arrancan siempre desde la semilla del JSON).
"""

import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

from codex.bias import BiasCircadiano
from codex.decaimiento import reforzar_movilizados
from codex.embeddings import Embeddings
from codex.loadout import calcular_loadout
from codex.memetario import Memetario
from codex.reloj import RelojSimple

NOTICIA = "Corre la noticia de un avistamiento extraño en la bahía."


def _preparar_mundo() -> Path:
    """Copia los seres a una carpeta temporal limpia y devuelve su ruta."""
    origen = RAIZ / "mundos" / "prueba" / "seres"
    work = Path(tempfile.mkdtemp(prefix="codex_demo_"))
    (work / "seres").mkdir()
    for json_ser in origen.glob("*.json"):
        shutil.copy(json_ser, work / "seres" / json_ser.name)
    return work


def _mostrar_loadout(memetario: Memetario, loadout) -> None:
    print(f"\n  {memetario.ser.ser_id}  (mana usado: {loadout.mana_usado}/{memetario.ser.mana_max})")
    for meme in loadout.seleccionados:
        score = loadout.scores.get(meme.id)
        marca = "PF (gratis)" if score is None else f"score {score:.3f}"
        print(f"    • {meme.id:<22} [{marca}]  «{meme.texto}»")


def main() -> None:
    from codex.persistencia import Persistencia

    mundo = _preparar_mundo()
    persistencia = Persistencia(mundo)
    print("Cargando el modelo de embeddings (la primera vez baja ~90 MB)...")
    embeddings = Embeddings(persistencia)

    # Reloj del mundo a las 10:00 → de día. El bias circadiano favorece lo operativo.
    bias = BiasCircadiano(RelojSimple(datetime(1850, 3, 1, 10, 0)))

    print(f"\nNOTICIA: «{NOTICIA}»")
    print("=" * 70)

    seres = ["pescador_supersticioso", "comerciante_esceptico"]
    for nombre in seres:
        memetario = Memetario.cargar(nombre, persistencia)
        loadout = calcular_loadout(memetario, NOTICIA, embeddings, bias=bias)
        _mostrar_loadout(memetario, loadout)

        # Ciclo de uso: el ser moviliza su meme operativo principal (el de mayor score).
        operativos = [m for m in loadout.seleccionados if loadout.scores.get(m.id) is not None]
        if operativos:
            principal = max(operativos, key=lambda m: loadout.scores[m.id])
            peso_antes = principal.peso
            reforzar_movilizados(memetario, persistencia, [principal.id])
            peso_despues = {m.id: m.peso for m in memetario.memes_vivos()}[principal.id]
            print(f"    → moviliza '{principal.id}': peso {peso_antes:.2f} → {peso_despues:.2f} (refuerzo)")

    print("\n" + "=" * 70)
    print("Cada ser, ante la misma noticia, activó memes distintos y coherentes con quién es.")
    shutil.rmtree(mundo, ignore_errors=True)


if __name__ == "__main__":
    main()
