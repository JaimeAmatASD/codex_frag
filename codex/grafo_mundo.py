"""El grafo de información de un mundo: hechos, versiones y quién conoce qué.

Un MultiDiGraph de NetworkX por mundo (ADR-004). Cada hecho es la raíz de un árbol
de versiones; cada transmisión agrega una versión derivada. El grafo es la ÚNICA
fuente de quién sabe qué (regla 1), y toda su escritura a disco pasa por la puerta
única (regla 2: `Persistencia.guardar_grafo`).

Estructura interna:
  - Nodos con atributo `tipo`: "hecho" (atributos de Hecho), "version" (atributos
    de Version) y "ser" (solo el id; los seres viven en sus JSON, acá son referencia).
  - Aristas: version_padre -"deriva"-> version_hija (el árbol de mutación), y
    ser -"conoce"-> version (el conocimiento). La arista "deriva" refleja el campo
    `version_padre` de la Version; ambos se escriben juntos en `registrar_version`,
    el único punto de entrada, así no pueden desfasarse.
"""

from __future__ import annotations

import logging

import networkx as nx

from .hechos import Hecho, Version
from .persistencia import Persistencia

logger = logging.getLogger(__name__)


class GrafoMundo:
    """El grafo de información de un mundo y sus operaciones mínimas del paso 2."""

    def __init__(self, persistencia: Persistencia):
        self.persistencia = persistencia
        self._g = persistencia.cargar_grafo()

    # ----- Registro (todas las escrituras persisten vía la puerta única) -----

    def registrar_hecho(self, hecho: Hecho) -> Version:
        """Registra un hecho y crea su versión raíz (misma verdad, distancia 0.0).
        Devuelve la raíz, que es lo que un testigo puede conocer y transmitir."""
        if self._g.has_node(hecho.id):
            raise ValueError(f"El hecho ya existe en el grafo: {hecho.id}")

        raiz = Version(
            id=f"{hecho.id}-raiz",
            hecho_id=hecho.id,
            contenido=hecho.contenido,
            momento=hecho.momento,
            distancia_raiz=0.0,
        )
        self._g.add_node(hecho.id, tipo="hecho", **hecho.model_dump(exclude={"id"}))
        self._g.add_node(raiz.id, tipo="version", **raiz.model_dump(exclude={"id"}))
        self.persistencia.guardar_grafo(self._g)
        return raiz

    def registrar_version(self, version: Version) -> None:
        """Registra una versión derivada: el nodo, su arista de linaje y el
        conocimiento del receptor. Único punto de entrada de versiones nuevas."""
        if self._g.has_node(version.id):
            raise ValueError(f"La versión ya existe en el grafo: {version.id}")
        if not self._g.has_node(version.hecho_id):
            raise ValueError(f"La versión refiere a un hecho desconocido: {version.hecho_id}")
        if version.version_padre is None or not self._g.has_node(version.version_padre):
            raise ValueError(
                f"La versión derivada necesita un padre existente: {version.version_padre}"
            )

        self._g.add_node(version.id, tipo="version", **version.model_dump(exclude={"id"}))
        self._g.add_edge(version.version_padre, version.id, key="deriva")
        if version.receptor is not None:
            self.registrar_conocimiento(version.receptor, version.id, _guardar=False)
        self.persistencia.guardar_grafo(self._g)

    def registrar_conocimiento(self, ser_id: str, version_id: str, _guardar: bool = True) -> None:
        """Registra que un ser conoce una versión (p. ej. el testigo conoce la raíz)."""
        if not self._g.has_node(version_id) or self._g.nodes[version_id].get("tipo") != "version":
            raise ValueError(f"No existe la versión: {version_id}")
        if not self._g.has_node(ser_id):
            self._g.add_node(ser_id, tipo="ser")
        self._g.add_edge(ser_id, version_id, key="conoce")
        if _guardar:
            self.persistencia.guardar_grafo(self._g)

    # ----- Consultas -----

    def version(self, version_id: str) -> Version:
        """Reconstruye una Version validada desde su nodo."""
        if not self._g.has_node(version_id) or self._g.nodes[version_id].get("tipo") != "version":
            raise ValueError(f"No existe la versión: {version_id}")
        datos = self._g.nodes[version_id]
        return Version(id=version_id, **{k: v for k, v in datos.items() if k != "tipo"})

    def version_raiz(self, hecho_id: str) -> Version:
        """La versión raíz de un hecho (la verdad contra la que se mide la distancia)."""
        return self.version(f"{hecho_id}-raiz")

    def versiones_conocidas(self, ser_id: str, hecho_id: str | None = None) -> list[Version]:
        """Qué versión(es) conoce un ser; opcionalmente filtradas por hecho.
        Pueden ser varias del mismo hecho: le llegó por más de una boca (ADR-004)."""
        if not self._g.has_node(ser_id):
            return []
        conocidas = [
            self.version(destino)
            for _, destino, clave in self._g.out_edges(ser_id, keys=True)
            if clave == "conoce"
        ]
        if hecho_id is not None:
            conocidas = [v for v in conocidas if v.hecho_id == hecho_id]
        return conocidas

    def linaje(self, version_id: str) -> list[Version]:
        """La cadena de deformación de una versión, ordenada raíz → versión."""
        cadena = [self.version(version_id)]
        while cadena[-1].version_padre is not None:
            cadena.append(self.version(cadena[-1].version_padre))
        cadena.reverse()
        return cadena
