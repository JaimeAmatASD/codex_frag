"""Demo del paso 2: la mutación del rumor, con LLM REAL (Gemini) y embeddings reales.

Corre así, desde la raíz del proyecto (necesita la API key):
    GEMINI_API_KEY=... ./venv/bin/python demos/prueba_paso2.py

Primero, el mismo hecho llega al pescador y al comerciante y cada uno recuenta:
las dos versiones se imprimen lado a lado con su distancia a la verdad y los memes
que resonaron. Después, una cadena de dos saltos (raíz → pescador → comerciante)
muestra la deriva acumulada.

El instrumento de medición de este paso es tu lectura: ¿cada versión delata a su
portador? ¿La cadena cuenta una historia de deformación creíble? Si no, se itera
templates/mutacion.txt (no el motor) antes de construir nada más.
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

from codex.bias import BiasCircadiano
from codex.embeddings import Embeddings
from codex.grafo_mundo import GrafoMundo
from codex.hechos import Hecho, Version
from codex.llm import GeminiClient
from codex.memetario import Memetario
from codex.persistencia import Persistencia
from codex.reloj import RelojSimple
from codex.transmision import transmitir

HECHO = Hecho(
    id="avistamiento-bahia",
    contenido=(
        "Al amanecer, dos pescadores vieron una forma enorme y oscura moverse "
        "bajo el agua de la bahía, cerca de los botes amarrados, y desaparecer sin ruido."
    ),
    momento="1850-03-01T07:00:00",
    lugar="la bahía",
)


def _preparar_mundo() -> Path:
    """Copia los seres a una carpeta temporal limpia y devuelve su ruta."""
    origen = RAIZ / "mundos" / "prueba" / "seres"
    work = Path(tempfile.mkdtemp(prefix="codex_demo2_"))
    # Cada ser es una carpeta autocontenida (ADR-007): se copia el árbol entero.
    shutil.copytree(origen, work / "seres")
    return work


def _mostrar_version(titulo: str, version: Version) -> None:
    print(f"\n  {titulo}")
    print(f"    distancia a la verdad: {version.distancia_raiz:.3f}")
    print(f"    «{version.contenido}»")


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit(
            "Falta GEMINI_API_KEY en el entorno.\n"
            "Conseguí una key en https://aistudio.google.com/apikey y corré:\n"
            "    GEMINI_API_KEY=... ./venv/bin/python demos/prueba_paso2.py"
        )

    mundo = _preparar_mundo()
    persistencia = Persistencia(mundo)
    print("Cargando el modelo de embeddings (la primera vez baja ~90 MB)...")
    embeddings = Embeddings(persistencia)
    cliente = GeminiClient()
    reloj = RelojSimple(datetime(1850, 3, 1, 8, 0))
    bias = BiasCircadiano(reloj)

    grafo = GrafoMundo(persistencia)
    raiz = grafo.registrar_hecho(HECHO)
    grafo.registrar_conocimiento("un_testigo", raiz.id)

    pescador = Memetario.cargar("pescador_supersticioso", persistencia)
    comerciante = Memetario.cargar("comerciante_esceptico", persistencia)

    print(f"\nLA VERDAD RAÍZ ({HECHO.lugar}, {HECHO.momento}):")
    print(f"  «{HECHO.contenido}»")
    print(f"\n[LLM: {cliente.modelo}]")

    # ---- Nivel 2a: el mismo hecho llega a dos cristales distintos ----
    print("\n" + "=" * 70)
    print("EL MISMO HECHO, DOS CRISTALES (un testigo se lo cuenta a cada uno)")
    print("=" * 70)
    for memetario in (pescador, comerciante):
        version = transmitir(
            "un_testigo", memetario, raiz, grafo, embeddings, cliente, reloj, bias=bias
        )
        _mostrar_version(f"Lo que guardó {memetario.ser.ser_id}:", version)
        estado = persistencia.leer_estado(memetario.ser.ser_id)
        resonantes = [mid for mid, e in estado.items() if e.veces_movilizado > 0]
        print(f"    memes que resonaron: {resonantes or '(ninguno)'}")

    # ---- Nivel 2b: cadena de dos saltos, la deriva acumulada ----
    print("\n" + "=" * 70)
    print("CADENA DE DOS SALTOS: raíz → pescador → comerciante")
    print("=" * 70)
    reloj.avanzar(timedelta(hours=4))
    v_pescador = transmitir(
        "un_testigo", pescador, raiz, grafo, embeddings, cliente, reloj, bias=bias
    )
    reloj.avanzar(timedelta(hours=4))
    v_comerciante = transmitir(
        "pescador_supersticioso", comerciante, v_pescador, grafo, embeddings, cliente, reloj,
        bias=bias,
    )
    for i, version in enumerate(grafo.linaje(v_comerciante.id)):
        quien = version.receptor or "la verdad raíz"
        _mostrar_version(f"Salto {i} — {quien}:", version)

    print("\n" + "=" * 70)
    print("Criterio de éxito (lo juzgás leyendo): ¿cada versión delata a su portador?")
    print("¿La cadena cuenta una deformación creíble? Si no: iterar templates/mutacion.txt.")
    shutil.rmtree(mundo, ignore_errors=True)


if __name__ == "__main__":
    main()
