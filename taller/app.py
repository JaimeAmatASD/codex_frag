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

from codex.blades import HojaMecanica
from codex.grafo_mundo import GrafoMundo
from codex.hechos import Hecho
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia

logger = logging.getLogger(__name__)

NOMBRE_VALIDO = re.compile(r"^[a-zA-Z0-9_-]+$")   # nombres de mundo: sin rutas ni sorpresas


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


def crear_app(raiz_mundos, cliente_llm=None, encoder=None, rng=None) -> FastAPI:
    """Arma la app del taller. `cliente_llm`, `encoder` y `rng` se inyectan en tests;
    si vienen en None se usan los reales (Gemini, fastembed, azar) al primer uso."""
    app = FastAPI(title="El Taller — Codex Fragmentum")
    raiz = Path(raiz_mundos)
    raiz.mkdir(parents=True, exist_ok=True)
    # Recursos compartidos entre requests (el modelo de embeddings es pesado: UNA carga).
    recursos = {"cliente": cliente_llm, "encoder": encoder, "encoder_fallo": False, "rng": rng}

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

    return app
