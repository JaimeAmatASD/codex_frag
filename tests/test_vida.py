"""Tests del latido (codex/vida.py): la vida cotidiana, sin LLM.

Todos corren con encoder falso y `random.Random(semilla)` (regla 5). En ninguno
existe un cliente LLM: que el flujo entero funcione sin cliente ES la prueba
del principio rector.
"""

import ast
import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from codex import vida
from codex.decaimiento import PISO, TASA_REFUERZO, TASA_REFUERZO_RUTINA, reforzar_movilizados
from codex.embeddings import Embeddings
from codex.memetario import Memetario
from codex.persistencia import Persistencia
from codex.reloj import RelojSimple
from codex.vida import (
    Rutina,
    cargar_rutina,
    elegir_situacion,
    franja_de,
    tick_de_vida,
    vivir,
)

# ----- Piezas de mundo: encoder falso con afinidades controladas -----

VEC = {
    # memes
    "El trabajo de las manos ordena el día.": [1, 0, 0, 0],
    "Vigilar a los otros llena los huecos.": [0, 1, 0, 0],
    "Los rezos de la noche calman.": [0, 0, 1, 0],
    "Una charla en el mercado vale un jornal.": [0, 0, 0, 1],
    # situaciones ordinarias (afines al oficio)
    "Sale al campo con la azada al hombro.": [1, 0, 0, 0],
    "Remienda los cercos rotos de la tarde.": [1, 0, 0, 0],
    "Junto al fuego repasa el trabajo del día.": [1, 0, 0, 0],
    # situaciones ordinarias (afines a la charla)
    "Cruza el mercado saludando a los de siempre.": [0, 0, 0, 1],
    "Conversa del tiempo con un vecino.": [0, 0, 0, 1],
    # situaciones de anomalía (afines a la vigilancia)
    "Descubre un hueco donde ayer había un recuerdo.": [0, 1, 0, 0],
    "Revisa sus anotaciones para confirmar algo que ya no recuerda.": [0, 1, 0, 0],
}


def _encoder(textos):
    return [np.asarray(VEC.get(t, [0.25, 0.25, 0.25, 0.25]), dtype=np.float32) for t in textos]


SER = {
    "ser_id": "morador",
    "mana_max": 20,   # dos candidatos de costo 10: siempre queda uno afuera
    "memes": [
        {"id": "PF-tierra", "tipo": "fundacional", "peso_inicial": 5.0,
         "texto": "Esta tierra me conoce."},
        {"id": "oficio", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "El trabajo de las manos ordena el día."},
        {"id": "vigilancia", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "Vigilar a los otros llena los huecos."},
        {"id": "rezo", "tipo": "operativo", "peso_inicial": 3.0, "costo": 10,
         "texto": "Los rezos de la noche calman."},
    ],
}

RUTINA_ORDINARIA = {
    "plantillas": [
        {"id": "amanecer", "texto": "Sale al campo con la azada al hombro.", "franja": "mañana"},
        {"id": "faena", "texto": "Remienda los cercos rotos de la tarde.", "franja": "tarde"},
        {"id": "repaso", "texto": "Junto al fuego repasa el trabajo del día.", "franja": "noche"},
    ]
}


def _mundo(tmp_path, nombre="mundo", ser=SER, rutina=RUTINA_ORDINARIA):
    """Un mundo con su ser sembrado, su rutina y embeddings falsos."""
    p = Persistencia(tmp_path / nombre)
    carpeta = p.carpeta_seres / ser["ser_id"]
    carpeta.mkdir(parents=True)
    (carpeta / "ser.json").write_text(json.dumps(ser), encoding="utf-8")
    if rutina is not None:
        (carpeta / "rutina.json").write_text(json.dumps(rutina), encoding="utf-8")
    memetario = Memetario.cargar(ser["ser_id"], p)
    return p, memetario, Embeddings(p, encoder=_encoder)


def _reloj(hora=9):
    return RelojSimple(datetime(2026, 3, 1, hora, 0))


# ----- La rutina como contenido -----

def test_rutina_carga_y_valida(tmp_path):
    p, _, _ = _mundo(tmp_path)
    rutina = cargar_rutina(p, "morador")
    assert [pl.id for pl in rutina.plantillas] == ["amanecer", "faena", "repaso"]


def test_ser_sin_rutina_no_late(tmp_path, caplog):
    p, memetario, emb = _mundo(tmp_path, rutina=None)
    assert cargar_rutina(p, "morador") is None
    resumen = vivir(3, memetario, None, _reloj(), p, emb, random.Random(1))
    assert resumen is None
    assert "no late" in caplog.text


def test_rutina_malformada_da_error_claro():
    with pytest.raises(Exception) as e:
        Rutina(plantillas=[{"id": "a", "texto": "x"}, {"id": "a", "texto": "y"},
                           {"id": "b", "texto": "z"}])
    assert "repetidos" in str(e.value)


def test_rutina_de_ejemplo_del_mundo_de_prueba():
    """La rutina real del que no muere carga y valida (parte 2 del prompt)."""
    datos = json.loads(
        (Path(__file__).parent.parent / "mundos/prueba/seres/el_que_no_muere/rutina.json")
        .read_text(encoding="utf-8")
    )
    rutina = Rutina(**datos)
    assert 3 <= len(rutina.plantillas) <= 20


# ----- Test 1: reproducibilidad -----

def test_misma_semilla_misma_vida(tmp_path):
    """Misma semilla → misma secuencia de ticks, movilizados y escalados."""
    resumenes = []
    for nombre in ("a", "b"):
        p, memetario, emb = _mundo(tmp_path, nombre=nombre)
        resumenes.append(
            vivir(5, memetario, cargar_rutina(p, "morador"), _reloj(),
                  p, emb, random.Random(7))
        )
    assert resumenes[0].model_dump() == resumenes[1].model_dump()


# ----- Test 3: la tasa de rutina es señal débil -----

def test_tasa_rutina_sube_diez_veces_menos(tmp_path):
    """El mismo meme movilizado por vivencia y por rutina: la rutina mueve ~10
    veces menos (0.02 vs 0.20, ambos hacia el mismo techo)."""
    p, memetario, _ = _mundo(tmp_path)

    antes = {m.id: m.peso for m in memetario.memes_vivos()}
    reforzar_movilizados(memetario, p, ["oficio"])                            # vivencia
    reforzar_movilizados(memetario, p, ["vigilancia"], tasa=TASA_REFUERZO_RUTINA)  # rutina
    despues = {m.id: m.peso for m in memetario.memes_vivos()}

    delta_vivencia = despues["oficio"] - antes["oficio"]
    delta_rutina = despues["vigilancia"] - antes["vigilancia"]
    # Ambos partían del mismo peso (4.0), así que el cociente es exactamente
    # el de las tasas: 0.20 / 0.02 = 10.
    assert delta_vivencia / delta_rutina == pytest.approx(TASA_REFUERZO / TASA_REFUERZO_RUTINA)


# ----- Test 4: la regla 4 sigue intacta bajo el régimen de rutina -----

def test_regla_4_intacta_con_regimen_correcto(tmp_path, monkeypatch):
    monkeypatch.setattr(vida, "PROB_INTERFERENCIA", 0.0)
    p, memetario, emb = _mundo(tmp_path)
    rutina = cargar_rutina(p, "morador")

    resultado = tick_de_vida(memetario, rutina, _reloj(9), p, emb, random.Random(3))

    filas = p._conn.execute(
        "SELECT meme_id, en_loadout, movilizado, regimen FROM activaciones"
    ).fetchall()
    # Una fila por meme del loadout, todas 'rutina', y movilizado solo los usados.
    assert {f["meme_id"] for f in filas} == set(resultado.loadout_ids)
    assert all(f["en_loadout"] == 1 and f["regimen"] == "rutina" for f in filas)
    por_id = {f["meme_id"]: f["movilizado"] for f in filas}
    for meme_id in resultado.loadout_ids:
        assert por_id[meme_id] == (1 if meme_id in resultado.movilizados else 0)
    assert por_id["PF-tierra"] == 0   # las PF no se movilizan por rutina
    assert 1 <= len(resultado.movilizados) <= 2


# ----- Test 5: interferencia -----

def test_interferencia_moviliza_un_meme_de_afuera(tmp_path, monkeypatch):
    """Con la probabilidad forzada a 1, el meme que quedó fuera del loadout
    irrumpe, queda movilizado y su fila dice 'interferencia'."""
    monkeypatch.setattr(vida, "PROB_INTERFERENCIA", 1.0)
    p, memetario, emb = _mundo(tmp_path)
    rutina = cargar_rutina(p, "morador")

    resultado = tick_de_vida(memetario, rutina, _reloj(9), p, emb, random.Random(3))

    # A la mañana el loadout es oficio + vigilancia: el de afuera es el rezo.
    assert resultado.irrupcion == "rezo"
    assert "rezo" in resultado.movilizados
    filas = p._conn.execute(
        "SELECT meme_id, movilizado FROM activaciones WHERE regimen = 'interferencia'"
    ).fetchall()
    assert [(f["meme_id"], f["movilizado"]) for f in filas] == [("rezo", 1)]


def test_sin_interferencia_no_pasa_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(vida, "PROB_INTERFERENCIA", 0.0)
    p, memetario, emb = _mundo(tmp_path)
    rutina = cargar_rutina(p, "morador")

    resultado = tick_de_vida(memetario, rutina, _reloj(9), p, emb, random.Random(3))

    assert resultado.irrupcion is None
    filas = p._conn.execute(
        "SELECT COUNT(*) AS n FROM activaciones WHERE regimen = 'interferencia'"
    ).fetchone()
    assert filas["n"] == 0


# ----- Test 6: las franjas se respetan -----

def test_franja_de_mapea_las_horas():
    assert franja_de(6) == "mañana" and franja_de(11) == "mañana"
    assert franja_de(12) == "tarde" and franja_de(19) == "tarde"
    assert franja_de(20) == "noche" and franja_de(23) == "noche"
    assert franja_de(0) == "noche" and franja_de(5) == "noche"


def test_a_la_noche_no_salen_plantillas_de_manana():
    rutina = Rutina(plantillas=[
        {"id": "alba", "texto": "El alba.", "franja": "mañana"},
        {"id": "velas", "texto": "Las velas.", "franja": "noche"},
        {"id": "siempre", "texto": "Lo de siempre.", "franja": "cualquiera"},
    ])
    rng = random.Random(11)
    de_noche = {elegir_situacion(rutina, _reloj(22), rng).id for _ in range(100)}
    assert de_noche == {"velas", "siempre"}   # nada de mañana; las 'cualquiera' sí
    de_manana = {elegir_situacion(rutina, _reloj(9), rng).id for _ in range(100)}
    assert de_manana == {"alba", "siempre"}


# ----- Tests 7 y 8: equilibrio y pureza -----

SER_EQUILIBRIO = {
    "ser_id": "morador",
    "mana_max": 10,   # UN candidato entra: el de la rutina; el otro queda afuera siempre
    "memes": [
        {"id": "PF-tierra", "tipo": "fundacional", "peso_inicial": 5.0,
         "texto": "Esta tierra me conoce."},
        {"id": "oficio", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "El trabajo de las manos ordena el día."},
        {"id": "olvidado", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "Los rezos de la noche calman."},
    ],
}


def test_equilibrio_rutina_sostiene_y_ausencia_decae(tmp_path, monkeypatch):
    """Tras 30 días: lo que la rutina toca resiste (el refuerzo compensa el
    decaimiento); lo que no toca decae hacia PISO sin alcanzarlo (asíntota)."""
    monkeypatch.setattr(vida, "PROB_INTERFERENCIA", 0.0)   # sin regalos para el olvidado
    p, memetario, emb = _mundo(tmp_path, ser=SER_EQUILIBRIO)
    resumen = vivir(30, memetario, cargar_rutina(p, "morador"), _reloj(),
                    p, emb, random.Random(5))

    assert resumen.pesos_fin["oficio"] >= resumen.pesos_inicio["oficio"]
    assert resumen.pesos_fin["olvidado"] < resumen.pesos_inicio["olvidado"]
    assert resumen.pesos_fin["olvidado"] > PISO
    # La PF ni decae ni se refuerza.
    assert resumen.pesos_fin["PF-tierra"] == resumen.pesos_inicio["PF-tierra"]


def test_pureza_treinta_dias_sin_ningun_cliente_llm(tmp_path):
    """El principio rector, por construcción: vida.py no importa ningún cliente
    LLM, y 30 días corren de punta a punta sin que exista uno en el test."""
    fuente = (Path(__file__).parent.parent / "codex/vida.py").read_text(encoding="utf-8")
    importados = [
        nombre
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, (ast.Import, ast.ImportFrom))
        for nombre in ([a.name for a in nodo.names] + [getattr(nodo, "module", None) or ""])
    ]
    assert not any("llm" in nombre for nombre in importados)

    p, memetario, emb = _mundo(tmp_path)
    resumen = vivir(30, memetario, cargar_rutina(p, "morador"), _reloj(),
                    p, emb, random.Random(9))
    assert len(resumen.dias) == 30
    assert len(resumen.dias[0].ticks) == vida.TICKS_POR_DIA
    # La cola es la primitiva: los calientes son serializables tal cual.
    for m in resumen.pendientes:
        json.dumps(m.model_dump())


# ----- Criterio de aceptación: el drift test -----
#
# Un ser con un meme operativo de vigilancia/control en la semilla (fixture
# propia: la semilla del mundo de prueba no se toca). Corrida A con la rutina
# completa (incluidas las dos plantillas de anomalía, afines a la vigilancia);
# corrida B, control, sin esas dos. La paranoia se construye tick a tick.

SER_VIGIA = {
    "ser_id": "vigia",
    "mana_max": 40,   # los cuatro candidatos entran al loadout: compiten por score
    "memes": [
        {"id": "PF-tierra", "tipo": "fundacional", "peso_inicial": 5.0,
         "texto": "Esta tierra me conoce."},
        {"id": "oficio", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "El trabajo de las manos ordena el día."},
        {"id": "charla", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "Una charla en el mercado vale un jornal."},
        {"id": "rezo", "tipo": "operativo", "peso_inicial": 4.0, "costo": 10,
         "texto": "Los rezos de la noche calman."},
        {"id": "vigilancia", "tipo": "operativo", "peso_inicial": 2.0, "costo": 10,
         "texto": "Vigilar a los otros llena los huecos."},
    ],
}

ORDINARIAS = [
    {"id": "amanecer", "texto": "Sale al campo con la azada al hombro.", "franja": "mañana"},
    {"id": "mercado", "texto": "Cruza el mercado saludando a los de siempre.", "franja": "mañana"},
    {"id": "faena", "texto": "Remienda los cercos rotos de la tarde.", "franja": "tarde"},
    {"id": "vecino", "texto": "Conversa del tiempo con un vecino.", "franja": "tarde"},
    {"id": "repaso", "texto": "Junto al fuego repasa el trabajo del día.", "franja": "noche"},
    {"id": "charla_noche", "texto": "Conversa del tiempo con un vecino.", "franja": "noche"},
]

ANOMALIAS = [
    {"id": "hueco", "texto": "Descubre un hueco donde ayer había un recuerdo.",
     "franja": "cualquiera"},
    {"id": "anotaciones", "texto": "Revisa sus anotaciones para confirmar algo que ya no recuerda.",
     "franja": "cualquiera"},
]


def test_drift_la_paranoia_se_construye_tick_a_tick(tmp_path):
    """Dos corridas de 60 días: con las plantillas de anomalía (A) la vigilancia
    sube estrictamente por encima del control sin ellas (B), donde se mantiene
    aproximadamente estable. Cero tokens."""
    finales = {}
    for nombre, plantillas in (("a", ORDINARIAS + ANOMALIAS), ("b", ORDINARIAS)):
        rutina = {"plantillas": [dict(pl) for pl in plantillas]}
        p, memetario, emb = _mundo(tmp_path, nombre=nombre, ser=SER_VIGIA, rutina=rutina)
        resumen = vivir(60, memetario, cargar_rutina(p, "vigia"), _reloj(),
                        p, emb, random.Random(23))
        finales[nombre] = resumen.pesos_fin["vigilancia"]

    inicial = 2.0
    assert finales["a"] > finales["b"]
    # Tolerancia del control: sin anomalías la vigilancia vive de migajas (las
    # movilizaciones estocásticas raras compensan más o menos el decaimiento),
    # así que oscila alrededor del peso de semilla sin despegar ni desplomarse.
    # Observado entre semillas: B termina en 1.8-2.7 (±0.8 de la semilla),
    # mientras A gana entre +1.0 y +1.9.
    assert abs(finales["b"] - inicial) < 0.8
