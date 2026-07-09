"""Demo del paso 3: el primer Score jugable, con LLM REAL (Gemini) y embeddings reales.

Corre así, desde la raíz del proyecto (necesita la API key):
    GEMINI_API_KEY=... ./venv/bin/python demos/prueba_paso3.py

La misma acción con riesgo la intentan dos seres distintos: convencer al patrón
del muelle de zarpar con el mar picado. El motor calcula posición y efecto desde
el cristal de cada uno (ADR-002: Blades del lado del enchufe), tira los dados de
verdad, aplica los efectos por la puerta única y el LLM narra el resultado que el
motor decidió. Después, el pescador empuja una tirada pagando stress.

El instrumento de medición de este paso es tu lectura: ¿los términos de la tirada
cuentan algo de quién actúa? ¿La narración respeta la categoría y delata al
personaje? Si no: iterar templates/narracion_score.txt (no el motor).
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

from codex.blades import HojaMecanica, SistemaBlades, narrar_resolucion
from codex.clocks import Clock
from codex.embeddings import Embeddings
from codex.llm import GeminiClient
from codex.memetario import Memetario
from codex.persistencia import Persistencia
from codex.reglas import AccionDeclarada, Empuje, aplicar_efectos, contexto_para

CLOCK_AMENAZA = Clock(
    id="mar-enturbiado",
    nombre="El mar se enturbia contra el pueblo",
    segmentos_total=6,
)

DECLARACION = (
    "Convencer al patrón del muelle de que igual conviene zarpar hoy, "
    "con el mar picado y los rumores dando vueltas."
)


def _preparar_mundo() -> Path:
    """Copia los seres a una carpeta temporal limpia y devuelve su ruta."""
    origen = RAIZ / "mundos" / "prueba" / "seres"
    work = Path(tempfile.mkdtemp(prefix="codex_demo3_"))
    # Cada ser es una carpeta autocontenida (ADR-007): se copia el árbol entero.
    shutil.copytree(origen, work / "seres")
    return work


def _score(ser_id, blades, persistencia, embeddings, cliente, empuje=None):
    memetario = Memetario.cargar(ser_id, persistencia)
    accion = AccionDeclarada(ser_id=ser_id, accion="persuadir", descripcion=DECLARACION)
    contexto = contexto_para(accion, memetario, embeddings)

    evaluacion = blades.evaluar(accion, contexto)
    print(f"\n  {ser_id} lo intenta.")
    print(
        f"    términos (los ve antes de tirar): posición {evaluacion.posicion.value}, "
        f"efecto {evaluacion.efecto.value}, {evaluacion.dados} dado(s)"
    )
    print(f"    por qué: {evaluacion.detalles}")
    if empuje is not None:
        print(f"    empuja pagando stress: {empuje.value}")

    resolucion = blades.tirar(evaluacion, contexto, empuje=empuje)
    aplicar_efectos(resolucion.efectos, persistencia)
    print(f"    dados: {resolucion.dados_tirados} → {resolucion.categoria.value}")

    print(f"\n    {narrar_resolucion(cliente, resolucion, contexto)}")

    stress = persistencia.leer_estado_reglas(ser_id).get("stress", 0.0)
    clock = persistencia.cargar_clock(CLOCK_AMENAZA.id)
    print(f"\n    stress de {ser_id}: {stress:.0f}/9")
    print(
        f"    clock «{clock.nombre}»: {clock.segmentos_actuales}/{clock.segmentos_total}"
        f"{'  ¡COMPLETADO!' if clock.estado == 'completado' else ''}"
    )


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit(
            "Falta GEMINI_API_KEY en el entorno.\n"
            "Conseguí una key en https://aistudio.google.com/apikey y corré:\n"
            "    GEMINI_API_KEY=... ./venv/bin/python demos/prueba_paso3.py"
        )

    mundo = _preparar_mundo()
    persistencia = Persistencia(mundo)
    print("Cargando el modelo de embeddings (la primera vez baja ~90 MB)...")
    embeddings = Embeddings(persistencia)
    cliente = GeminiClient()
    persistencia.guardar_clock(CLOCK_AMENAZA)

    hojas = {
        ser_id: HojaMecanica(**persistencia.cargar_hoja_reglas(ser_id))
        for ser_id in ("pescador_supersticioso", "comerciante_esceptico")
    }
    blades = SistemaBlades(hojas=hojas, clock_amenaza_id=CLOCK_AMENAZA.id)

    print(f"\n[LLM: {cliente.modelo}]")
    print(f"\nLA ACCIÓN DECLARADA (la misma para los dos):\n  «{DECLARACION}»")

    print("\n" + "=" * 70)
    print("EL MISMO RIESGO, DOS CRISTALES (posición y efecto salen del memetario)")
    print("=" * 70)
    _score("pescador_supersticioso", blades, persistencia, embeddings, cliente)
    _score("comerciante_esceptico", blades, persistencia, embeddings, cliente)

    print("\n" + "=" * 70)
    print("EL EMPUJE: el pescador insiste, pagando stress por un dado extra")
    print("=" * 70)
    _score(
        "pescador_supersticioso", blades, persistencia, embeddings, cliente,
        empuje=Empuje.DADO_EXTRA,
    )

    print("\n" + "=" * 70)
    print("Criterio de éxito (lo juzgás leyendo): ¿los términos cuentan quién actúa?")
    print("¿La narración respeta la categoría y delata al personaje?")
    print("Si no: iterar templates/narracion_score.txt (no el motor).")
    shutil.rmtree(mundo, ignore_errors=True)


if __name__ == "__main__":
    main()
