"""Nivel 1 de la prueba del paso 2: el flujo completo de transmisión con MockClient.

Determinista, sin red ni tokens (regla 5): seres reales de mundos/prueba/seres,
codificador de vectores controlado, LLM guionado. Cubre el camino feliz (la versión
queda en el grafo con linaje y distancia, activaciones con regla 4), el degradado
(dos respuestas inválidas → sin deformación, con log) y el LLM que inventa memes.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from codex.embeddings import Embeddings
from codex.grafo_mundo import GrafoMundo
from codex.hechos import Hecho
from codex.llm import MockClient
from codex.memetario import Memetario
from codex.modelos import Ser
from codex.persistencia import Persistencia
from codex.reloj import RelojSimple
from codex.transmision import transmitir

SERES_DIR = Path(__file__).parent.parent / "mundos" / "prueba" / "seres"

HECHO = Hecho(
    id="avistamiento-bahia",
    contenido="Corre la noticia de un avistamiento extraño en la bahía.",
    momento="1850-03-01T07:00:00",
    lugar="la bahía",
)

ENTENDIDO = "El mar mandó una señal: algo enorme se mostró en la bahía, y eso nunca es gratis."

# Encoder falso y determinista (patrón de test_dos_seres): 2D, eje x = presagio/agua.
VECTORES = {
    HECHO.contenido: [1.0, 0.0],
    ENTENDIDO: [0.8, 0.2],
    "Un avistaje extraño en el agua anuncia tormenta o desgracia.": [0.95, 0.05],
    "Las viejas historias del puerto suelen decir la verdad.": [0.6, 0.4],
    "Quizás conviene ofrecer algo al mar para calmarlo.": [0.7, 0.3],
}


def _encoder(textos):
    return [np.asarray(VECTORES.get(t, [0.5, 0.5]), dtype=np.float32) for t in textos]


def _preparar(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    emb = Embeddings(p, encoder=_encoder)
    grafo = GrafoMundo(p)
    raiz = grafo.registrar_hecho(HECHO)
    ser = Ser(**json.loads((SERES_DIR / "pescador_supersticioso.json").read_text(encoding="utf-8")))
    pescador = Memetario(ser, p)
    reloj = RelojSimple(datetime(1850, 3, 1, 8, 0))
    return p, emb, grafo, raiz, pescador, reloj


def _respuesta_valida() -> str:
    return json.dumps(
        {"contenido_entendido": ENTENDIDO, "memes_resonantes": ["avistaje-presagio"]},
        ensure_ascii=False,
    )


def test_transmision_feliz_deja_version_linaje_y_activaciones(tmp_path):
    p, emb, grafo, raiz, pescador, reloj = _preparar(tmp_path)
    cliente = MockClient(respuestas=[_respuesta_valida()])

    nueva = transmitir("un_testigo", pescador, raiz, grafo, emb, cliente, reloj)

    # La versión guardada es la deformada, con su linaje y metadatos correctos.
    assert nueva.contenido == ENTENDIDO
    assert nueva.version_padre == raiz.id
    assert nueva.emisor == "un_testigo"
    assert nueva.receptor == "pescador_supersticioso"
    assert nueva.momento == "1850-03-01T08:00:00"

    # Distancia a la raíz = 1 - coseno entre lo entendido y la verdad raíz.
    esperada = 1.0 - emb.similitud(ENTENDIDO, HECHO.contenido)
    assert abs(nueva.distancia_raiz - esperada) < 1e-6
    assert 0.0 < nueva.distancia_raiz < 1.0

    # El grafo sabe quién conoce qué y reconstruye la cadena raíz → versión.
    assert grafo.versiones_conocidas("pescador_supersticioso") == [nueva]
    assert grafo.linaje(nueva.id) == [raiz, nueva]

    # Regla 4: todo el loadout suma "en loadout", solo el resonante suma "movilizado".
    estado = p.leer_estado("pescador_supersticioso")
    assert estado["avistaje-presagio"].veces_movilizado == 1
    assert estado["avistaje-presagio"].veces_en_loadout == 1
    movilizados = {mid for mid, e in estado.items() if e.veces_movilizado > 0}
    assert movilizados == {"avistaje-presagio"}
    en_loadout = {mid for mid, e in estado.items() if e.veces_en_loadout > 0}
    assert len(en_loadout) > 1  # las PF y algún otro meme también estuvieron en el loadout


def test_respuesta_invalida_reintenta_con_feedback(tmp_path):
    p, emb, grafo, raiz, pescador, reloj = _preparar(tmp_path)
    cliente = MockClient(respuestas=["esto no es JSON", _respuesta_valida()])

    nueva = transmitir("un_testigo", pescador, raiz, grafo, emb, cliente, reloj)

    assert nueva.contenido == ENTENDIDO
    assert len(cliente.llamadas) == 2
    # El reintento le cuenta al modelo qué falló.
    assert "no fue válida" in cliente.llamadas[1]


def test_dos_fallos_degradan_a_transmision_sin_deformacion(tmp_path, caplog):
    p, emb, grafo, raiz, pescador, reloj = _preparar(tmp_path)
    cliente = MockClient(respuestas=["basura", '{"campo_inventado": true}'])

    with caplog.at_level(logging.WARNING):
        nueva = transmitir("un_testigo", pescador, raiz, grafo, emb, cliente, reloj)

    # El receptor guarda lo que oyó tal cual, y la degradación queda anotada (regla 3).
    assert nueva.contenido == HECHO.contenido
    assert len(cliente.llamadas) == 2
    assert any("sin deformación" in r.message for r in caplog.records)

    # La versión igual entra al grafo con su linaje, y nadie quedó como "movilizado".
    assert grafo.linaje(nueva.id) == [raiz, nueva]
    estado = p.leer_estado("pescador_supersticioso")
    assert all(e.veces_movilizado == 0 for e in estado.values())


def test_ids_con_corchetes_del_template_se_normalizan(tmp_path):
    # El modelo a veces devuelve "[id]" copiando el formato del template: es el mismo meme.
    p, emb, grafo, raiz, pescador, reloj = _preparar(tmp_path)
    respuesta = json.dumps(
        {"contenido_entendido": ENTENDIDO, "memes_resonantes": ["[avistaje-presagio]"]},
        ensure_ascii=False,
    )
    cliente = MockClient(respuestas=[respuesta])

    transmitir("un_testigo", pescador, raiz, grafo, emb, cliente, reloj)

    estado = p.leer_estado("pescador_supersticioso")
    assert estado["avistaje-presagio"].veces_movilizado == 1


def test_memes_resonantes_fuera_del_loadout_se_descartan(tmp_path, caplog):
    p, emb, grafo, raiz, pescador, reloj = _preparar(tmp_path)
    respuesta = json.dumps(
        {"contenido_entendido": ENTENDIDO, "memes_resonantes": ["meme-inventado"]},
        ensure_ascii=False,
    )
    cliente = MockClient(respuestas=[respuesta])

    with caplog.at_level(logging.WARNING):
        transmitir("un_testigo", pescador, raiz, grafo, emb, cliente, reloj)

    # El LLM propone, el motor dispone: el meme inventado no cuenta como movilizado.
    assert any("fuera del loadout" in r.message for r in caplog.records)
    estado = p.leer_estado("pescador_supersticioso")
    assert all(e.veces_movilizado == 0 for e in estado.values())
