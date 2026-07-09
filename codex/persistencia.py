"""Persistencia unificada: la ÚNICA puerta de lectura/escritura del estado de un mundo.

Reglas 1 y 2 (nacen de bugs reales de Fray Tomás):
  - Regla 1: cada dato vive en un solo lugar. Las definiciones de memes están en el
    JSON del ser; el estado vivo (pesos, activaciones) está en SQLite. No se duplican.
  - Regla 2: ningún otro módulo escribe en disco. Todos pasan por esta clase. Eso hace
    imposible, por construcción, el desfase que aplanó la identidad de Fray Tomás.

Regla 3: cuando algo se degrada (un meme que no existe, un movilizado fuera del
loadout), se registra con `logging` en vez de fallar en silencio.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from .modelos import EstadoMeme, Ser

logger = logging.getLogger(__name__)


class Persistencia:
    """Maneja el estado de un mundo: su `estado.db` (SQLite) y los `seres/*.json`."""

    def __init__(self, carpeta_mundo: Path | str):
        self.carpeta = Path(carpeta_mundo)
        self.carpeta_seres = self.carpeta / "seres"
        self.db_path = self.carpeta / "estado.db"
        # El nombre de la carpeta ES el id del mundo (ADR-007): es el `origen` default
        # de toda entidad nativa. El id compuesto (mundo:entidad) no se usa acá dentro.
        self.mundo_id = self.carpeta.name

        self.carpeta.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._crear_tablas()

    def _crear_tablas(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                -- Fuente ÚNICA de la verdad para pesos. Se siembra una vez desde el JSON.
                CREATE TABLE IF NOT EXISTS memes_estado (
                    ser_id            TEXT NOT NULL,
                    meme_id           TEXT NOT NULL,
                    peso              REAL NOT NULL,
                    ultima_activacion TEXT,
                    veces_en_loadout  INTEGER NOT NULL DEFAULT 0,
                    veces_movilizado  INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (ser_id, meme_id)
                );

                -- Log de activaciones. Regla 4: separa "estuvo en el loadout" de "se usó".
                CREATE TABLE IF NOT EXISTS activaciones (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    ser_id       TEXT NOT NULL,
                    meme_id      TEXT NOT NULL,
                    momento      TEXT NOT NULL,
                    situacion    TEXT,
                    en_loadout   INTEGER NOT NULL,
                    movilizado   INTEGER NOT NULL,
                    co_activados TEXT
                );

                -- Caché de vectores: reusa cálculos de embeddings dentro del mundo.
                CREATE TABLE IF NOT EXISTS embeddings_cache (
                    texto_hash TEXT PRIMARY KEY,
                    vector     BLOB NOT NULL
                );
                """
            )

    # ----- Definiciones de seres (JSON, solo lectura) -----

    def cargar_ser(self, ser_id: str) -> Ser:
        """Lee y valida la definición de un ser desde `seres/<ser_id>.json`."""
        ruta = self.carpeta_seres / f"{ser_id}.json"
        if not ruta.exists():
            raise FileNotFoundError(f"No existe la definición del ser: {ruta}")
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        ser = Ser(**datos)
        if not ser.origen:                 # nativo: su origen es este mundo (ADR-007)
            ser.origen = self.mundo_id
        return ser

    # ----- Siembra del estado vivo -----

    def sembrar_ser(self, ser: Ser) -> None:
        """Crea el estado vivo de cada meme con su peso inicial. Idempotente:
        si el meme ya tiene estado, no lo pisa (no perdemos pesos ya evolucionados)."""
        with self._conn:
            for meme in ser.memes:
                self._conn.execute(
                    "INSERT OR IGNORE INTO memes_estado (ser_id, meme_id, peso) VALUES (?, ?, ?)",
                    (ser.ser_id, meme.id, meme.peso_inicial),
                )

    # ----- Lectura del estado vivo -----

    def leer_estado(self, ser_id: str) -> dict[str, EstadoMeme]:
        """Devuelve {meme_id: EstadoMeme} con el estado vivo de todos los memes del ser."""
        filas = self._conn.execute(
            "SELECT meme_id, peso, ultima_activacion, veces_en_loadout, veces_movilizado "
            "FROM memes_estado WHERE ser_id = ?",
            (ser_id,),
        ).fetchall()
        return {
            f["meme_id"]: EstadoMeme(
                meme_id=f["meme_id"],
                peso=f["peso"],
                ultima_activacion=f["ultima_activacion"],
                veces_en_loadout=f["veces_en_loadout"],
                veces_movilizado=f["veces_movilizado"],
            )
            for f in filas
        }

    # ----- Escritura de pesos (decaimiento / refuerzo) -----

    def actualizar_pesos(self, ser_id: str, pesos: dict[str, float]) -> None:
        """Aplica nuevos pesos. Único punto de escritura de pesos del sistema."""
        with self._conn:
            for meme_id, peso in pesos.items():
                cur = self._conn.execute(
                    "UPDATE memes_estado SET peso = ? WHERE ser_id = ? AND meme_id = ?",
                    (peso, ser_id, meme_id),
                )
                if cur.rowcount == 0:
                    logger.warning(
                        "Se intentó actualizar el peso de un meme sin estado: %s/%s",
                        ser_id, meme_id,
                    )

    # ----- Registro de activaciones (regla 4) -----

    def registrar_activaciones(
        self,
        ser_id: str,
        momento: str,
        situacion: str,
        loadout_ids: list[str],
        movilizados_ids: list[str],
    ) -> None:
        """Registra un pensamiento: qué memes entraron al loadout y cuáles se usaron
        de verdad. La `ultima_activacion` y el contador de movilizados solo cuentan
        los efectivamente usados (regla 4: no contaminar el decaimiento ni los clusters)."""
        movilizados = set(movilizados_ids)
        fuera = movilizados - set(loadout_ids)
        if fuera:
            logger.warning(
                "Memes movilizados que no estaban en el loadout (se registran igual): %s",
                fuera,
            )

        with self._conn:
            for meme_id in loadout_ids:
                co_activados = [m for m in loadout_ids if m != meme_id]
                fue_movilizado = 1 if meme_id in movilizados else 0
                self._conn.execute(
                    "INSERT INTO activaciones "
                    "(ser_id, meme_id, momento, situacion, en_loadout, movilizado, co_activados) "
                    "VALUES (?, ?, ?, ?, 1, ?, ?)",
                    (ser_id, meme_id, momento, situacion, fue_movilizado, json.dumps(co_activados)),
                )
                self._conn.execute(
                    "UPDATE memes_estado SET veces_en_loadout = veces_en_loadout + 1 "
                    "WHERE ser_id = ? AND meme_id = ?",
                    (ser_id, meme_id),
                )
            for meme_id in movilizados:
                self._conn.execute(
                    "UPDATE memes_estado SET veces_movilizado = veces_movilizado + 1, "
                    "ultima_activacion = ? WHERE ser_id = ? AND meme_id = ?",
                    (momento, ser_id, meme_id),
                )

    # ----- Grafo de información (paso 2) -----
    #
    # El grafo es la única fuente de quién sabe qué (regla 1) y se guarda como
    # node-link JSON de networkx (ADR-003: formato portable, nunca pickle) en
    # `grafo.json` dentro de la carpeta del mundo.

    def guardar_grafo(self, grafo: "nx.MultiDiGraph") -> None:
        """Serializa el grafo de información del mundo. Única escritura del grafo."""
        import networkx as nx

        datos = nx.node_link_data(grafo, edges="edges")
        ruta = self.carpeta / "grafo.json"
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    def cargar_grafo(self) -> "nx.MultiDiGraph":
        """Lee el grafo de información del mundo; vacío si todavía no existe."""
        import networkx as nx

        ruta = self.carpeta / "grafo.json"
        if not ruta.exists():
            return nx.MultiDiGraph()
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return nx.node_link_graph(datos, edges="edges", multigraph=True, directed=True)

    # ----- Caché de embeddings -----

    def leer_vector(self, texto_hash: str) -> bytes | None:
        fila = self._conn.execute(
            "SELECT vector FROM embeddings_cache WHERE texto_hash = ?", (texto_hash,)
        ).fetchone()
        return fila["vector"] if fila else None

    def guardar_vector(self, texto_hash: str, vector: bytes) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO embeddings_cache (texto_hash, vector) VALUES (?, ?)",
                (texto_hash, vector),
            )

    def cerrar(self) -> None:
        self._conn.close()
