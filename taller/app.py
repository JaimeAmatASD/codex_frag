"""El Taller: la API del dashboard autoral (docs/TALLER_DISENO.md).

Herramienta de James, FUERA del motor (categoría `demos/`): cada endpoint envuelve
lo que el motor ya sabe hacer — Persistencia, Memetario, GrafoMundo, transmitir,
SistemaBlades — sin lógica nueva de motor. El servidor es stateless respecto del
mundo: cada request lleva `?mundo=<nombre>` y abre su Persistencia (y la cierra).

Todo es inyectable para los tests (regla 5): el cliente LLM (MockClient), el
encoder de embeddings (falso) y el RNG de los dados (guionado). En producción,
`taller/servidor.py` arma la app con los reales.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from datetime import datetime, timedelta

from codex.blades import HojaMecanica, SistemaBlades, narrar_resolucion
from codex.clocks import Clock
from codex.dialogo import responder_dialogo
from codex.embeddings import MODELO_POR_DEFECTO, Embeddings
from codex.grafo_mundo import GrafoMundo
from codex.hechos import Hecho
from codex.loadout import calcular_loadout
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia
from codex.reglas import (
    AccionDeclarada,
    ContextoAccion,
    Empuje,
    Evaluacion,
    aplicar_efectos,
    contexto_para,
)
from codex.reloj import RelojSimple
from codex.singularidades import Singularidad, chequear_singularidades
from codex.transmision import transmitir
from taller import bitacora
from taller.derivacion import derivar_ser

logger = logging.getLogger(__name__)

NOMBRE_VALIDO = re.compile(r"^[a-zA-Z0-9_-]+$")   # nombres de mundo: sin rutas ni sorpresas

RAIZ_REPO = Path(__file__).parent.parent
CARPETA_TEMPLATES = RAIZ_REPO / "templates"
# Los únicos templates editables desde el taller: los que los docs mandan
# iterar cuando las voces no revelan. Nada de rutas libres.
TEMPLATES_EDITABLES = {
    "mutacion": "mutacion.txt",
    "narracion_score": "narracion_score.txt",
    "tension": "tension.txt",
    "derivar_ser": "derivar_ser.txt",
    "dialogo": "dialogo.txt",
}
CARPETA_TESTS = RAIZ_REPO / "tests"   # el runner solo corre lo que vive acá adentro
TIMEOUT_TESTS = 300


class CuerpoMundo(BaseModel):
    nombre: str


class CuerpoHecho(BaseModel):
    """Un hecho nuevo del mundo, opcionalmente con su testigo (quién lo vio)."""

    id: str
    contenido: str
    momento: str
    lugar: str
    origen: str = ""
    testigo: str | None = None


class CuerpoSer(BaseModel):
    """Semilla completa de un ser: cuerpo cognitivo + hoja mecánica (opcional)."""

    ser_id: str
    origen: str = ""
    mana_max: int
    memes: list[dict]
    hoja: dict | None = None


class CuerpoDerivar(BaseModel):
    descripcion: str


class CuerpoSingularidad(BaseModel):
    """Semilla de una singularidad: el evento agendado que ocurre pase lo que pase."""

    id: str
    contenido: str
    momento: str    # hora del MUNDO en ISO en que ocurrirá
    lugar: str
    origen: str = ""
    testigos_iniciales: list[str] = []


class CuerpoReloj(BaseModel):
    momento: str    # hora del MUNDO en ISO


class CuerpoAvance(BaseModel):
    horas: int = 0
    dias: int = 0


class CuerpoTransmitir(BaseModel):
    emisor_id: str
    receptor_id: str
    version_id: str
    momento: str    # hora del MUNDO en ISO: la elige James en la página


class CuerpoEvaluar(BaseModel):
    ser_id: str
    accion: str
    descripcion: str


class CuerpoTirar(BaseModel):
    """Devuelve lo que /score/evaluar entregó, más el empuje elegido (o ninguno).
    El servidor no guarda nada entre los dos requests: el estado viaja con la página."""

    evaluacion: dict
    contexto: dict
    empuje: str | None = None


class CuerpoClock(BaseModel):
    id: str
    nombre: str
    segmentos_total: int


class CuerpoTemplate(BaseModel):
    texto: str


class CuerpoTests(BaseModel):
    ruta: str = "."   # relativa a la carpeta de tests del repo; default: toda la suite


class CuerpoTurno(BaseModel):
    """Un renglón de la charla: quién habló ('vos' o el ser_id) y qué dijo."""

    quien: str
    texto: str


class CuerpoDialogo(BaseModel):
    """El historial previo (sin el mensaje nuevo) + lo que decís/narrás ahora.
    El estado de la charla viaja con la página, como en Score: el servidor no
    guarda nada entre turnos."""

    ser_id: str
    historial: list[CuerpoTurno] = []
    mensaje: str


class CuerpoPesos(BaseModel):
    """El modo editar del diálogo: tocar el peso VIVO a mano, la puerta única
    (Persistencia.actualizar_pesos), aparte de la semilla en ser.json."""

    pesos: dict[str, float]


def crear_app(raiz_mundos, cliente_llm=None, encoder=None, rng=None) -> FastAPI:
    """Arma la app del taller. `cliente_llm`, `encoder` y `rng` se inyectan en tests;
    si vienen en None se usan los reales (Gemini, fastembed, azar) al primer uso."""
    app = FastAPI(title="El Taller — Codex Fragmentum")
    raiz = Path(raiz_mundos)
    raiz.mkdir(parents=True, exist_ok=True)
    # Recursos compartidos entre requests (el modelo de embeddings es pesado: UNA carga).
    recursos = {"cliente": cliente_llm, "encoder": encoder, "encoder_fallo": False, "rng": rng}

    # ----- El taller es local y de UNA persona -----
    # Una página web ajena abierta en el mismo navegador puede disparar requests
    # contra localhost (drive-by). El navegador les pone Origin: acá se rechazan.

    @app.middleware("http")
    async def _solo_origen_local(request: Request, call_next):
        origen = request.headers.get("origin")
        if origen is not None:
            host = origen.split("://")[-1].split(":")[0]
            if host not in ("127.0.0.1", "localhost"):
                return JSONResponse(status_code=403, content={"detail": "Origen no permitido."})
        return await call_next(request)

    # ----- Errores del motor → mensajes legibles en el formulario -----

    @app.exception_handler(ValidationError)
    async def _error_validacion(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def _error_valor(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # ----- Helpers -----

    def _carpeta_mundo(mundo: str) -> Path:
        carpeta = raiz / mundo
        if not NOMBRE_VALIDO.match(mundo) or not carpeta.is_dir():
            raise HTTPException(404, f"No existe el mundo: {mundo}")
        return carpeta

    def dep_persistencia(mundo: str):
        """Una Persistencia por request, siempre cerrada al final."""
        p = Persistencia(_carpeta_mundo(mundo))
        try:
            yield p
        finally:
            p.cerrar()

    def _cliente():
        """El LLM real, creado UNA vez al primer uso (o el inyectado en tests)."""
        if recursos["cliente"] is None:
            from codex.llm import GeminiClient   # import perezoso: no exige key al arrancar

            recursos["cliente"] = GeminiClient()  # sin key → ValueError → 400 legible
        return recursos["cliente"]

    def _embeddings(p: Persistencia) -> Embeddings:
        """Embeddings por mundo, compartiendo UN modelo fastembed entre requests
        (cargarlo es pesado; el caché de vectores sí es de cada mundo)."""
        if recursos["encoder"] is None and not recursos["encoder_fallo"]:
            try:
                from fastembed import TextEmbedding

                modelo = TextEmbedding(model_name=MODELO_POR_DEFECTO)
                recursos["encoder"] = lambda textos: list(modelo.embed(list(textos)))
            except Exception as e:
                recursos["encoder_fallo"] = True
                logger.error("El taller queda sin embeddings (%s); el motor degrada.", e)
        return Embeddings(p, encoder=recursos["encoder"])

    def _blades(p: Persistencia) -> SistemaBlades:
        """El sistema de reglas del mundo: todas las hojas + el clock de amenaza."""
        activos = [c for c in p.cargar_clocks() if c.estado == "activo"]
        if not activos:
            raise HTTPException(
                409, "El mundo no tiene un clock de amenaza activo: creá uno antes del Score."
            )
        hojas = {}
        if p.carpeta_seres.is_dir():
            for carpeta in p.carpeta_seres.iterdir():
                datos = p.cargar_hoja_reglas(carpeta.name)
                if datos is not None:
                    hojas[carpeta.name] = HojaMecanica(**datos)
        return SistemaBlades(hojas=hojas, clock_amenaza_id=activos[0].id, rng=recursos["rng"])

    # ----- La página -----

    @app.get("/")
    def pagina():
        from fastapi.responses import HTMLResponse

        return HTMLResponse((Path(__file__).parent / "index.html").read_text(encoding="utf-8"))

    # ----- Zona Mundo -----

    @app.get("/mundos")
    def listar_mundos() -> list[str]:
        return sorted(d.name for d in raiz.iterdir() if d.is_dir())

    @app.post("/mundos")
    def crear_mundo(cuerpo: CuerpoMundo):
        if not NOMBRE_VALIDO.match(cuerpo.nombre):
            raise HTTPException(
                400, "El nombre del mundo lleva solo letras, números, guiones y guión bajo."
            )
        if (raiz / cuerpo.nombre).exists():
            raise HTTPException(400, f"El mundo ya existe: {cuerpo.nombre}")
        Persistencia(raiz / cuerpo.nombre).cerrar()   # nace funcional (estado.db listo)
        return {"ok": True}

    @app.post("/reset")
    def resetear_estado_vivo(mundo: str):
        """Borra lo jugado (estado.db, grafo.json). Las semillas quedan intactas."""
        carpeta = _carpeta_mundo(mundo)
        for nombre in ("estado.db", "grafo.json"):
            (carpeta / nombre).unlink(missing_ok=True)
        return {"ok": True}

    @app.get("/reloj")
    def leer_reloj(p: Persistencia = Depends(dep_persistencia)):
        return {"momento": p.leer_momento_mundo()}

    @app.post("/reloj")
    def fijar_reloj(cuerpo: CuerpoReloj, p: Persistencia = Depends(dep_persistencia)):
        """Fija la hora del mundo. También chequea el destino: fijarla más allá
        del momento de una singularidad pendiente la dispara."""
        momento = datetime.fromisoformat(cuerpo.momento)   # inválida → ValueError → 400
        disparadas = chequear_singularidades(p, GrafoMundo(p), momento)
        p.guardar_momento_mundo(momento.isoformat())
        return {"momento": momento.isoformat(),
                "disparadas": [s.model_dump() for s in disparadas]}

    @app.post("/reloj/avanzar")
    def avanzar_reloj(cuerpo: CuerpoAvance, p: Persistencia = Depends(dep_persistencia)):
        """Avanza el reloj del mundo y dispara las singularidades alcanzadas."""
        actual = p.leer_momento_mundo()
        if actual is None:
            raise HTTPException(409, "El mundo no tiene hora todavía: fijala antes de avanzar.")
        if cuerpo.horas < 0 or cuerpo.dias < 0 or (cuerpo.horas == 0 and cuerpo.dias == 0):
            raise HTTPException(400, "El reloj avanza para adelante: horas o días positivos.")
        nuevo = datetime.fromisoformat(actual) + timedelta(hours=cuerpo.horas, days=cuerpo.dias)
        disparadas = chequear_singularidades(p, GrafoMundo(p), nuevo)
        p.guardar_momento_mundo(nuevo.isoformat())
        return {"momento": nuevo.isoformat(),
                "disparadas": [s.model_dump() for s in disparadas]}

    @app.get("/singularidades")
    def listar_singularidades(p: Persistencia = Depends(dep_persistencia)):
        """La semilla completa, cada una con su estado (pendiente/disparada)."""
        disparadas = p.singularidades_disparadas()
        return [
            {**s.model_dump(), "estado": "disparada" if s.id in disparadas else "pendiente"}
            for s in p.cargar_singularidades()
        ]

    @app.post("/singularidades")
    def guardar_singularidad(
        cuerpo: CuerpoSingularidad, p: Persistencia = Depends(dep_persistencia)
    ):
        """Crea o edita la semilla de una singularidad (por id). La marca de
        'ya disparada' es estado vivo y no se toca desde acá."""
        datetime.fromisoformat(cuerpo.momento)   # valida YA, no al avanzar el reloj
        nueva = Singularidad(**cuerpo.model_dump())
        lista = [s.model_dump() for s in p.cargar_singularidades() if s.id != nueva.id]
        lista.append(nueva.model_dump())
        (p.carpeta / "singularidades.json").write_text(
            json.dumps(lista, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return {"ok": True}

    # ----- Zona Personajes -----

    @app.get("/seres")
    def listar_seres(p: Persistencia = Depends(dep_persistencia)):
        seres = []
        if p.carpeta_seres.is_dir():
            for carpeta in sorted(p.carpeta_seres.iterdir()):
                if (carpeta / "ser.json").exists():
                    ser = p.cargar_ser(carpeta.name)
                    seres.append({**ser.model_dump(), "hoja": p.cargar_hoja_reglas(carpeta.name)})
        return seres

    @app.post("/seres")
    def guardar_ser(cuerpo: CuerpoSer, mundo: str, p: Persistencia = Depends(dep_persistencia)):
        """Crea o edita la semilla de un ser (y su hoja). El estado vivo no se pisa:
        la siembra es idempotente (regla 1: los pesos evolucionados son sagrados)."""
        datos = cuerpo.model_dump(exclude={"hoja"})
        datos["origen"] = datos["origen"] or mundo    # nativo por default (ADR-007)
        ser = Ser(**datos)                            # valida ANTES de escribir
        if not NOMBRE_VALIDO.match(ser.ser_id):
            # El ser_id se vuelve carpeta: sin esto, "../../lo-que-sea" escribe fuera del mundo.
            raise HTTPException(
                400, "El ser_id lleva solo letras, números, guiones y guión bajo."
            )
        hoja = HojaMecanica(**{**{"ser_id": ser.ser_id}, **(cuerpo.hoja or {})}) if cuerpo.hoja is not None else None

        carpeta = p.carpeta_seres / ser.ser_id
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "ser.json").write_text(
            json.dumps(ser.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if hoja is not None:
            (carpeta / "hoja_reglas.json").write_text(
                json.dumps(hoja.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        Memetario(ser, p)   # siembra el estado vivo inicial (INSERT OR IGNORE)
        return {"ok": True}

    @app.post("/seres/derivar")
    def derivar(cuerpo: CuerpoDerivar, p: Persistencia = Depends(dep_persistencia)):
        """Relatás al personaje y el LLM propone el ser completo. La propuesta
        CAE EN EL FORMULARIO, nunca se guarda sola: la curaduría es el punto."""
        if not cuerpo.descripcion.strip():
            raise HTTPException(400, "El relato está vacío: contá quién es.")
        propuesta, reintento = derivar_ser(_cliente(), cuerpo.descripcion)
        if propuesta is None:
            raise HTTPException(
                422, "No pude derivar un ser válido de ese relato: probá reformular la descripción."
            )
        bitacora.registrar(p.carpeta, {
            "tipo": "derivacion",
            "ser": propuesta.ser_id,
            "entrada": cuerpo.descripcion,
            "salida": json.dumps(propuesta.model_dump(), ensure_ascii=False),
            "terminos": {"reintento": reintento},
        })
        return {"propuesta": propuesta.model_dump(), "reintento": reintento}

    # ----- Zona Lore -----

    @app.get("/hechos")
    def listar_hechos(p: Persistencia = Depends(dep_persistencia)):
        """Cada hecho con su árbol de versiones: quién conoce qué, qué tan lejos
        de la verdad."""
        grafo = GrafoMundo(p)
        return [
            {
                "hecho": hecho.model_dump(),
                "versiones": [
                    {**v.model_dump(), "conocida_por": grafo.quienes_conocen(v.id)}
                    for v in grafo.versiones_de(hecho.id)
                ],
            }
            for hecho in grafo.hechos()
        ]

    @app.post("/hechos")
    def registrar_hecho(cuerpo: CuerpoHecho, p: Persistencia = Depends(dep_persistencia)):
        grafo = GrafoMundo(p)
        raiz = grafo.registrar_hecho(Hecho(**cuerpo.model_dump(exclude={"testigo"})))
        if cuerpo.testigo:
            grafo.registrar_conocimiento(cuerpo.testigo, raiz.id)
        return {"ok": True, "raiz": raiz.model_dump()}

    @app.get("/seres/{ser_id}/estado")
    def estado_ser(ser_id: str, p: Persistencia = Depends(dep_persistencia)):
        """El cristal evolucionando, solo lectura: pesos actuales y activaciones."""
        return {mid: e.model_dump() for mid, e in p.leer_estado(ser_id).items()}

    @app.post("/seres/{ser_id}/pesos")
    def editar_pesos_vivos(
        ser_id: str, cuerpo: CuerpoPesos, mundo: str, p: Persistencia = Depends(dep_persistencia)
    ):
        """Modo editar del diálogo: tocar el peso vivo a mano, por la puerta única.
        No es la semilla (regla 1): un peso ya evolucionado no se pisa por accidente
        al guardar ser.json, pero acá el autor SÍ puede moverlo a propósito."""
        p.actualizar_pesos(ser_id, cuerpo.pesos)
        return {"ok": True}

    # ----- Zona Diálogo -----

    @app.post("/dialogo")
    def dialogo(cuerpo: CuerpoDialogo, mundo: str, p: Persistencia = Depends(dep_persistencia)):
        """Hablarle directo a un ser: sin hecho, sin emisor, sin secreto. El
        cristal se calcula sobre la charla acumulada tal como está AHORA; no
        registra activaciones ni mueve pesos (eso es /seres/{id}/pesos, aparte).
        Queda en la bitácora para comparar intentos, como transmitir y Score."""
        try:
            memetario = Memetario.cargar(cuerpo.ser_id, p)
        except FileNotFoundError:
            raise HTTPException(404, f"No existe el ser: {cuerpo.ser_id}")
        historial = [t.model_dump() for t in cuerpo.historial] + [
            {"quien": "vos", "texto": cuerpo.mensaje}
        ]
        respuesta, loadout = responder_dialogo(memetario, historial, _cliente(), _embeddings(p))

        tensiones = [t.model_dump() for t in loadout.tensiones]
        memes_activos = [{"id": m.id, "texto": m.texto, "peso": m.peso} for m in loadout.seleccionados]
        bitacora.registrar(p.carpeta, {
            "tipo": "dialogo",
            "ser": cuerpo.ser_id,
            "entrada": cuerpo.mensaje,
            "salida": respuesta,
            "terminos": {"tensiones": tensiones, "memes_activos": [m["id"] for m in memes_activos]},
        })
        return {"respuesta": respuesta, "tensiones": tensiones, "memes_activos": memes_activos}

    # ----- Zona Probar -----

    @app.post("/transmitir")
    def transmitir_version(
        cuerpo: CuerpoTransmitir, mundo: str, p: Persistencia = Depends(dep_persistencia)
    ):
        """Un ser le cuenta una versión a otro, con Gemini real (o el mock en tests)."""
        grafo = GrafoMundo(p)
        version = grafo.version(cuerpo.version_id)
        receptor = Memetario.cargar(cuerpo.receptor_id, p)
        reloj = RelojSimple(datetime.fromisoformat(cuerpo.momento))

        # El cristal se calcula acá para poder MOSTRAR la grieta (tensiones de la
        # escucha); transmitir lo recibe ya hecho y no lo recalcula.
        emb = _embeddings(p)
        loadout = calcular_loadout(receptor, version.contenido, emb)
        # Pesos ANTES de escuchar: si una contradicción mueve algo (políticas de
        # aprendizaje, mejora 04), el autor lo ve sin ir a buscar el estado vivo.
        antes = {mid: e.peso for mid, e in p.leer_estado(cuerpo.receptor_id).items()}
        nueva = transmitir(
            cuerpo.emisor_id, receptor, version, grafo, emb, _cliente(), reloj,
            loadout=loadout,
        )
        pesos_movidos = {
            mid: [antes[mid], e.peso]
            for mid, e in p.leer_estado(cuerpo.receptor_id).items()
            if mid in antes and e.peso != antes[mid]
        }

        tensiones = [t.model_dump() for t in loadout.tensiones]
        bitacora.registrar(p.carpeta, {
            "tipo": "transmision",
            "ser": cuerpo.receptor_id,
            "entrada": version.contenido,
            "salida": nueva.contenido,
            "terminos": {"emisor": cuerpo.emisor_id, "distancia_raiz": nueva.distancia_raiz,
                         "tensiones": tensiones, "pesos_movidos": pesos_movidos},
        })
        return {"version": nueva.model_dump(), "tensiones": tensiones,
                "pesos_movidos": pesos_movidos}

    @app.get("/clocks")
    def listar_clocks(p: Persistencia = Depends(dep_persistencia)):
        return [c.model_dump() for c in p.cargar_clocks()]

    @app.post("/clocks")
    def crear_clock(cuerpo: CuerpoClock, p: Persistencia = Depends(dep_persistencia)):
        if p.cargar_clock(cuerpo.id) is not None:
            raise HTTPException(400, f"El clock ya existe: {cuerpo.id}")
        p.guardar_clock(Clock(**cuerpo.model_dump()))
        return {"ok": True}

    @app.post("/score/evaluar")
    def score_evaluar(
        cuerpo: CuerpoEvaluar, p: Persistencia = Depends(dep_persistencia)
    ):
        """Los términos de la tirada, ANTES de tirar: el jugador decide informado."""
        blades = _blades(p)
        accion = AccionDeclarada(**cuerpo.model_dump())
        memetario = Memetario.cargar(accion.ser_id, p)
        contexto = contexto_para(accion, memetario, _embeddings(p))
        evaluacion = blades.evaluar(accion, contexto)
        return {"evaluacion": evaluacion.model_dump(), "contexto": contexto.model_dump()}

    @app.post("/score/tirar")
    def score_tirar(cuerpo: CuerpoTirar, p: Persistencia = Depends(dep_persistencia)):
        """La tirada: dados reales, efectos por la puerta única, narración del LLM."""
        blades = _blades(p)
        evaluacion = Evaluacion(**cuerpo.evaluacion)
        contexto = ContextoAccion(**cuerpo.contexto)
        empuje = Empuje(cuerpo.empuje) if cuerpo.empuje else None

        resolucion = blades.tirar(evaluacion, contexto, empuje=empuje)
        aplicar_efectos(resolucion.efectos, p)
        narracion = narrar_resolucion(_cliente(), resolucion, contexto)

        ser_id = evaluacion.accion.ser_id
        stress = p.leer_estado_reglas(ser_id).get("stress", 0.0)
        clock = p.cargar_clock(blades.clock_amenaza_id)
        bitacora.registrar(p.carpeta, {
            "tipo": "score",
            "ser": ser_id,
            "entrada": evaluacion.accion.descripcion,
            "salida": narracion,
            "terminos": {
                "accion": evaluacion.accion.accion,
                "posicion": resolucion.evaluacion.posicion.value,
                "efecto": resolucion.evaluacion.efecto.value,
                "dados": resolucion.dados_tirados,
                "categoria": resolucion.categoria.value,
                "empuje": cuerpo.empuje,
                "tensiones": [t.model_dump() for t in contexto.loadout.tensiones],
            },
        })
        return {
            "resolucion": resolucion.model_dump(),
            "narracion": narracion,
            "stress": stress,
            "clock": clock.model_dump(),
        }

    @app.get("/bitacora")
    def leer_bitacora(mundo: str):
        return bitacora.leer(_carpeta_mundo(mundo))

    # ----- Zona Templates -----

    def _ruta_template(nombre: str) -> Path:
        if nombre not in TEMPLATES_EDITABLES:
            raise HTTPException(404, f"Ese template no se edita desde el taller: {nombre}")
        return CARPETA_TEMPLATES / TEMPLATES_EDITABLES[nombre]

    @app.get("/templates/{nombre}")
    def leer_template(nombre: str):
        return {"texto": _ruta_template(nombre).read_text(encoding="utf-8")}

    @app.put("/templates/{nombre}")
    def guardar_template(nombre: str, cuerpo: CuerpoTemplate):
        _ruta_template(nombre).write_text(cuerpo.texto, encoding="utf-8")
        return {"ok": True}

    # ----- Correr los tests -----

    @app.post("/tests")
    def correr_tests(cuerpo: CuerpoTests):
        """`pytest -q` en subproceso, con timeout. La página pinta verde o rojo.

        La ruta va relativa a la carpeta de tests del repo, sin flags: pytest
        EJECUTA el conftest de lo que se le apunte, así que una ruta libre sería
        ejecución de código arbitrario (hallazgo de la revisión de seguridad)."""
        import subprocess
        import sys

        if cuerpo.ruta.startswith("-"):
            raise HTTPException(400, "La ruta no lleva flags.")
        ruta = (CARPETA_TESTS / cuerpo.ruta).resolve()
        if not ruta.is_relative_to(CARPETA_TESTS.resolve()):
            raise HTTPException(400, "Solo se corre lo que vive en la carpeta de tests del repo.")

        proceso = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(ruta)],
            cwd=RAIZ_REPO, capture_output=True, text=True, timeout=TIMEOUT_TESTS,
        )
        salida = proceso.stdout + proceso.stderr
        return {"exito": proceso.returncode == 0, "salida": salida[-8000:]}

    return app
