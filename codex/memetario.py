"""Memetario de un ser: el grafo de sus memes, unido a su estado vivo.

Se instancia UNO por ser (parametrizado por el ser y por la persistencia del mundo).
El grafo (NetworkX) guarda la estructura estática —tipos, textos, conexiones—; el peso
vivo lo lee de la persistencia. La clave del diseño es `memes_vivos()`: devuelve la
vista coherente (definición + peso actual) que el loadout consume. Esa unión es lo que
le faltaba a Fray Tomás, donde definición y uso vivían separados y se desincronizaban.

Las conexiones se cargan en el grafo pero todavía no se usan en el paso 1: quedan listas
para los clusters de co-activación de pasos posteriores.
"""

from __future__ import annotations

import logging

import networkx as nx

from .modelos import MemeVivo, Ser
from .persistencia import Persistencia

logger = logging.getLogger(__name__)


class Memetario:
    """El grafo de memes de un ser y su acceso al estado vivo."""

    def __init__(self, ser: Ser, persistencia: Persistencia):
        self.ser = ser
        self.persistencia = persistencia
        self.grafo = self._construir_grafo(ser)
        # Asegura que cada meme tenga estado vivo (idempotente: no pisa pesos existentes).
        persistencia.sembrar_ser(ser)

    @classmethod
    def cargar(cls, ser_id: str, persistencia: Persistencia) -> "Memetario":
        """Construye el memetario leyendo la definición del ser desde su JSON."""
        return cls(persistencia.cargar_ser(ser_id), persistencia)

    def _construir_grafo(self, ser: Ser) -> nx.DiGraph:
        grafo = nx.DiGraph()
        for meme in ser.memes:
            grafo.add_node(
                meme.id,
                tipo=meme.tipo,
                texto=meme.texto,
                costo=meme.costo,
                peso_inicial=meme.peso_inicial,
            )
        for meme in ser.memes:
            # Las dos clases de arista, con su signo: la conexión refuerza, la
            # tensión parte al medio. Nada las consume aún: quedan para inspección.
            for destino, tipo in [(d, "refuerzo") for d in meme.conexiones] + [
                (d, "tension") for d in meme.tensiones
            ]:
                if destino in grafo:
                    grafo.add_edge(meme.id, destino, tipo=tipo)
                else:
                    logger.warning(
                        "%s a un meme inexistente, se ignora: %s -> %s (ser %s)",
                        tipo.capitalize(), meme.id, destino, ser.ser_id,
                    )
        return grafo

    def memes_vivos(self) -> list[MemeVivo]:
        """Vista coherente de todos los memes: definición + peso vivo actual."""
        estado = self.persistencia.leer_estado(self.ser.ser_id)
        vivos: list[MemeVivo] = []
        for meme in self.ser.memes:
            est = estado.get(meme.id)
            if est is None:
                # No debería pasar (sembrar corre en __init__), pero no lo escondemos.
                logger.warning(
                    "Meme sin estado vivo, uso su peso inicial: %s (ser %s)",
                    meme.id, self.ser.ser_id,
                )
            vivos.append(
                MemeVivo(
                    id=meme.id,
                    tipo=meme.tipo,
                    texto=meme.texto,
                    costo=meme.costo,
                    peso=est.peso if est else meme.peso_inicial,
                    ultima_activacion=est.ultima_activacion if est else None,
                    veces_movilizado=est.veces_movilizado if est else 0,
                    tensiones=meme.tensiones,
                    funcion=meme.funcion,
                    aprendizaje=meme.aprendizaje,
                )
            )
        return vivos
