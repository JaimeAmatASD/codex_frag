"""El diálogo directo: hablarle a un ser sin secreto ni emisor (docs del Taller).

Determinista, sin red (regla 5): MockClient, encoder falso, un ser chico armado
a mano. Cubre el camino feliz (responde en su voz, con el cristal actual), que
no toca el estado vivo (ni activaciones ni pesos), la degradación ante un LLM
caído, y que el historial acumulado viaja completo al prompt.
"""

from __future__ import annotations

import numpy as np

from codex.dialogo import armar_prompt, responder_dialogo
from codex.embeddings import Embeddings
from codex.llm import ErrorLLM, MockClient
from codex.loadout import calcular_loadout
from codex.memetario import Memetario
from codex.modelos import Meme, Ser
from codex.persistencia import Persistencia


def _encoder(textos):
    return [np.asarray([0.5, 0.5], dtype=np.float32) for _ in textos]


def _ser():
    return Ser(
        ser_id="el_que_no_muere",
        mana_max=40,
        memes=[
            Meme(id="PF-tierra", tipo="fundacional", texto="Conosco esta tierra.",
                 peso_inicial=9.0),
            Meme(id="el-olvido", tipo="operativo", texto="Lo que olvido no me pesa.",
                 peso_inicial=6.0, costo=20),
        ],
    )


def _preparar(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    memetario = Memetario(_ser(), p)
    emb = Embeddings(p, encoder=_encoder)
    return p, memetario, emb


def test_responde_en_su_voz_sin_tocar_estado_vivo(tmp_path):
    p, memetario, emb = _preparar(tmp_path)
    cliente = MockClient(respuesta_por_defecto="Esta ruina es tan vieja como yo.")
    antes = {mid: e.peso for mid, e in p.leer_estado("el_que_no_muere").items()}

    historial = []
    respuesta, loadout = responder_dialogo(
        memetario, historial + [{"quien": "vos", "texto": "hace cuánto que está esa ruina?"}],
        cliente, emb,
    )

    assert respuesta == "Esta ruina es tan vieja como yo."
    assert loadout.ser_id == "el_que_no_muere"
    # Ni activaciones ni pesos se tocan: es exploración, no transmisión.
    despues = {mid: e.peso for mid, e in p.leer_estado("el_que_no_muere").items()}
    assert despues == antes
    assert p.leer_estado("el_que_no_muere")["PF-tierra"].veces_movilizado == 0


def test_el_prompt_no_deja_actuar_al_personaje(tmp_path):
    _, memetario, emb = _preparar(tmp_path)
    cliente = MockClient(respuesta_por_defecto="listo")

    responder_dialogo(
        memetario, [{"quien": "vos", "texto": "quién sos?"}], cliente, emb,
    )

    prompt = cliente.llamadas[-1]
    assert "No sos un actor que sabe que actúa" in prompt
    assert "quién sos?" in prompt


def test_el_historial_acumulado_viaja_completo_al_prompt(tmp_path):
    _, memetario, emb = _preparar(tmp_path)
    cliente = MockClient(respuesta_por_defecto="...")

    historial = [
        {"quien": "vos", "texto": "hace cuánto que está esa ruina?"},
        {"quien": "el_que_no_muere", "texto": "más de lo que puedo contar."},
    ]
    responder_dialogo(memetario, historial + [{"quien": "vos", "texto": "y quién la hizo?"}],
                       cliente, emb)

    prompt = cliente.llamadas[-1]
    assert "hace cuánto que está esa ruina?" in prompt
    assert "más de lo que puedo contar." in prompt
    assert "y quién la hizo?" in prompt


def test_error_de_infraestructura_degrada_con_aviso(tmp_path, caplog):
    _, memetario, emb = _preparar(tmp_path)

    class ClienteCaido:
        def responder(self, prompt):
            raise ErrorLLM("cuota agotada")

    respuesta, _loadout = responder_dialogo(
        memetario, [{"quien": "vos", "texto": "hola"}], ClienteCaido(), emb,
    )

    assert "no responde" in respuesta
    assert "cuota agotada" in caplog.text


def test_sin_historial_previo_lo_anota_como_lo_primero_que_oye(tmp_path):
    _, memetario, emb = _preparar(tmp_path)
    loadout = calcular_loadout(memetario, "hola", emb)

    prompt = armar_prompt("el_que_no_muere", [], loadout)

    assert "todavía no le dijiste nada" in prompt
