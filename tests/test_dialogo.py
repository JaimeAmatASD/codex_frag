"""El diálogo directo: hablarle a un ser sin secreto ni emisor (docs del Taller).

Determinista, sin red (regla 5): MockClient, encoder falso, un ser chico armado
a mano. Cubre el camino feliz (responde en su voz, con el cristal actual y
dejando huella: la charla es vida, regla 4), la degradación ante un LLM caído
(que NO deja huella: no hubo charla), y que el historial viaja completo al prompt.
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


def test_responde_en_su_voz_y_la_charla_deja_huella(tmp_path):
    """La charla es vida (regla 4): los memes que resuenan con ella se movilizan
    y el uso los refuerza. Las PF se cuentan pero no cambian de peso. Con el
    encoder por defecto todo texto es afín a todo: ambos memes resuenan."""
    p, memetario, emb = _preparar(tmp_path)
    cliente = MockClient(respuesta_por_defecto="Esta ruina es tan vieja como yo.")
    antes = {mid: e.peso for mid, e in p.leer_estado("el_que_no_muere").items()}

    historial = []
    respuesta, loadout = responder_dialogo(
        memetario, historial + [{"quien": "vos", "texto": "hace cuánto que está esa ruina?"}],
        cliente, emb, momento="1850-03-01T09:00:00",
    )

    assert respuesta == "Esta ruina es tan vieja como yo."
    assert loadout.ser_id == "el_que_no_muere"
    estado = p.leer_estado("el_que_no_muere")
    assert estado["el-olvido"].veces_movilizado == 1
    assert estado["PF-tierra"].veces_movilizado == 1
    assert estado["el-olvido"].peso > antes["el-olvido"]      # el uso refuerza
    assert estado["PF-tierra"].peso == antes["PF-tierra"]     # la PF no se mueve
    assert estado["el-olvido"].ultima_activacion == "1850-03-01T09:00:00"


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


def test_error_de_infraestructura_degrada_con_aviso_y_sin_huella(tmp_path, caplog):
    p, memetario, emb = _preparar(tmp_path)

    class ClienteCaido:
        def responder(self, prompt):
            raise ErrorLLM("cuota agotada")

    respuesta, _loadout = responder_dialogo(
        memetario, [{"quien": "vos", "texto": "hola"}], ClienteCaido(), emb,
    )

    assert "no responde" in respuesta
    assert "cuota agotada" in caplog.text
    # Si el ser no llegó a responder, la charla no ocurrió: nada se registra.
    estado = p.leer_estado("el_que_no_muere")
    assert all(e.veces_movilizado == 0 for e in estado.values())


def test_una_charla_larga_moviliza_los_mas_afines_aunque_ninguno_sea_muy_afin(tmp_path):
    """El bug del 2026-07-30: una charla larga diluye la afinidad de todo meme
    (el vector de 8.000 caracteres promedia muchos temas), así que un umbral
    absoluto alto nunca se cruza y la charla no deja huella. Medido en el mundo
    `prueba`: el meme más afín del pescador llegó a 0.606 sobre un umbral de
    0.75, en una charla que hablaba justamente de su tema. La charla es vida:
    siempre se moviliza lo más afín del loadout, sin piso absoluto."""
    ser = Ser(
        ser_id="el_que_no_muere",
        mana_max=90,
        memes=[
            Meme(id="cercano", tipo="operativo", texto="meme cercano", peso_inicial=5.0, costo=20),
            Meme(id="medio", tipo="operativo", texto="meme medio", peso_inicial=5.0, costo=20),
            Meme(id="lejano", tipo="operativo", texto="meme lejano", peso_inicial=5.0, costo=20),
        ],
    )
    # Encoder por ángulo: ninguna afinidad con la charla llega a 0.75, pero hay
    # un orden claro (cercano 0.71 > medio 0.50 > lejano 0.26).
    angulos = {"meme cercano": 45.0, "meme medio": 60.0, "meme lejano": 75.0}

    def encoder(textos):
        vs = []
        for t in textos:
            g = np.radians(angulos.get(t, 0.0))
            vs.append(np.asarray([np.cos(g), np.sin(g)], dtype=np.float32))
        return vs

    p = Persistencia(tmp_path / "mundo")
    memetario = Memetario(ser, p)
    emb = Embeddings(p, encoder=encoder)
    cliente = MockClient(respuesta_por_defecto="te escucho.")

    responder_dialogo(
        memetario, [{"quien": "vos", "texto": "una charla larga sobre muchas cosas"}],
        cliente, emb, momento="1850-03-01T09:00:00",
    )

    estado = p.leer_estado("el_que_no_muere")
    assert estado["cercano"].veces_movilizado == 1
    assert estado["medio"].veces_movilizado == 1
    assert estado["lejano"].veces_movilizado == 0   # el menos afín queda afuera


def test_sin_historial_previo_lo_anota_como_lo_primero_que_oye(tmp_path):
    _, memetario, emb = _preparar(tmp_path)
    loadout = calcular_loadout(memetario, "hola", emb)

    prompt = armar_prompt("el_que_no_muere", [], loadout)

    assert "todavía no le dijiste nada" in prompt
