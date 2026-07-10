"""Tests del Taller (el dashboard autoral, docs/TALLER_DISENO.md).

Sin red ni navegador (regla 5): TestClient de FastAPI, MockClient para el LLM,
encoder de vectores falso, mundos en tmp_path. La página HTML no se testea acá
(es una vista fina); el dictado y la lectura son features del navegador.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from codex.llm import MockClient
from taller.app import crear_app

VECTORES = {}  # los tests que midan afinidades reales cargan acá sus vectores


def _encoder(textos):
    return [np.asarray(VECTORES.get(t, [0.5, 0.5]), dtype=np.float32) for t in textos]


@pytest.fixture()
def taller(tmp_path):
    """Un taller limpio sobre una carpeta de mundos vacía, con LLM guionable."""
    cliente = MockClient(respuesta_por_defecto="")
    raiz = tmp_path / "mundos"
    app = crear_app(raiz_mundos=raiz, cliente_llm=cliente, encoder=_encoder)
    with TestClient(app) as tc:
        tc.cliente_llm = cliente
        tc.raiz_mundos = raiz
        yield tc


# ----- Zona Mundo -----

def test_crear_y_listar_mundos(taller):
    assert taller.get("/mundos").json() == []

    r = taller.post("/mundos", json={"nombre": "taberna"})
    assert r.status_code == 200

    assert taller.get("/mundos").json() == ["taberna"]


def test_nombre_de_mundo_invalido_da_400(taller):
    r = taller.post("/mundos", json={"nombre": "../fuera"})
    assert r.status_code == 400
    assert "nombre" in r.json()["detail"].lower()


def test_reset_borra_el_estado_vivo_pero_no_las_semillas(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    # Sembrar algo de estado vivo y una semilla, vía la API que ya existe.
    ser = {
        "ser_id": "tabernero",
        "mana_max": 40,
        "memes": [
            {"id": "PF-casa", "tipo": "fundacional", "texto": "Mi taberna es mi reino.",
             "peso_inicial": 9.0},
        ],
        "hoja": {"stress_max": 9, "acciones": {"persuadir": 2}},
    }
    assert taller.post("/seres?mundo=taberna", json=ser).status_code == 200

    r = taller.post("/reset?mundo=taberna")
    assert r.status_code == 200

    # La semilla sigue; el estado vivo arrancó de cero.
    assert [s["ser_id"] for s in taller.get("/seres?mundo=taberna").json()] == ["tabernero"]


def test_mundo_inexistente_da_404(taller):
    assert taller.get("/seres?mundo=no-existe").status_code == 404


# ----- Zona Personajes -----

def _ser_tabernero(**extra):
    base = {
        "ser_id": "tabernero",
        "mana_max": 40,
        "memes": [
            {"id": "PF-casa", "tipo": "fundacional", "texto": "Mi taberna es mi reino.",
             "peso_inicial": 9.0},
            {"id": "oido-fino", "tipo": "operativo", "texto": "Acá se escucha todo.",
             "peso_inicial": 6.0, "costo": 20},
        ],
        "hoja": {"stress_max": 9, "acciones": {"persuadir": 2, "escuchar": 3}},
    }
    base.update(extra)
    return base


def test_crear_ser_deja_semillas_validas_y_estado_sembrado(taller):
    taller.post("/mundos", json={"nombre": "taberna"})

    r = taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    assert r.status_code == 200

    seres = taller.get("/seres?mundo=taberna").json()
    assert seres[0]["ser_id"] == "tabernero"
    assert seres[0]["origen"] == "taberna"                 # nativo por default (ADR-007)
    assert seres[0]["hoja"]["acciones"]["escuchar"] == 3

    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["PF-casa"]["peso"] == 9.0                # sembrado con el peso inicial


def test_editar_la_semilla_no_pisa_el_estado_vivo(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    # El mundo vivió: un peso evolucionó (por la puerta única, como haría el motor).
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.actualizar_pesos("tabernero", {"oido-fino": 7.5})
    p.cerrar()

    # Editar la semilla (cambia un texto) NO debe resetear los pesos ya evolucionados.
    editado = _ser_tabernero()
    editado["memes"][1]["texto"] = "Acá se escucha todo, hasta lo que no se dice."
    assert taller.post("/seres?mundo=taberna", json=editado).status_code == 200

    seres = taller.get("/seres?mundo=taberna").json()
    assert "hasta lo que no se dice" in seres[0]["memes"][1]["texto"]
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] == 7.5              # el peso vivido sobrevive


def test_ser_invalido_da_400_con_mensaje_legible(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    roto = _ser_tabernero()
    roto["memes"][0]["tipo"] = "inexistente"

    r = taller.post("/seres?mundo=taberna", json=roto)
    assert r.status_code == 400
    assert "tipo" in r.json()["detail"]


# ----- Zona Lore -----

HECHO = {
    "id": "kraken-bahia",
    "contenido": "Algo enorme rompió las redes de la barca del viejo Tomás.",
    "momento": "1850-03-01T07:00:00",
    "lugar": "la bahía",
}


def test_registrar_hecho_y_ver_su_arbol(taller):
    taller.post("/mundos", json={"nombre": "taberna"})

    r = taller.post("/hechos?mundo=taberna", json={**HECHO, "testigo": "el_viejo_tomas"})
    assert r.status_code == 200

    hechos = taller.get("/hechos?mundo=taberna").json()
    assert len(hechos) == 1
    arbol = hechos[0]
    assert arbol["hecho"]["id"] == "kraken-bahia"
    assert arbol["hecho"]["origen"] == "taberna"           # nativo (ADR-007)
    # La raíz existe, con distancia 0.0, y el testigo la conoce.
    assert arbol["versiones"][0]["distancia_raiz"] == 0.0
    assert arbol["versiones"][0]["conocida_por"] == ["el_viejo_tomas"]


def test_hecho_duplicado_da_400(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/hechos?mundo=taberna", json=HECHO)

    r = taller.post("/hechos?mundo=taberna", json=HECHO)
    assert r.status_code == 400
    assert "ya existe" in r.json()["detail"]
