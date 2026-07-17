"""Tests de las singularidades (mejora 03): el evento inevitable.

Deterministas y sin red: semilla en tmp_path, grafo real, la hora del mundo
se mueve a mano. Cubren el contrato del doc: dispara una sola vez al alcanzar
su momento, antes no, el hecho raíz queda en el grafo, los testigos iniciales
conocen la raíz, y el reset del estado vivo la vuelve pendiente sin tocar la
semilla.
"""

import json
from datetime import datetime

from codex.grafo_mundo import GrafoMundo
from codex.persistencia import Persistencia
from codex.singularidades import chequear_singularidades

SEMILLA = [
    {
        "id": "el_hombre_pez",
        "contenido": "La noche de la primera luna de sangre, en el risco aislado, "
                     "cada uno de ellos se encuentra con un Hombre Pez.",
        "momento": "1850-03-03T23:00:00",
        "lugar": "el risco aislado",
        "testigos_iniciales": ["pescador_supersticioso", "el_que_no_muere"],
    }
]

ANTES = datetime.fromisoformat("1850-03-03T20:00:00")
LA_NOCHE = datetime.fromisoformat("1850-03-03T23:00:00")
DESPUES = datetime.fromisoformat("1850-03-04T09:00:00")


def _mundo(tmp_path, semilla=SEMILLA):
    carpeta = tmp_path / "mundo"
    carpeta.mkdir(exist_ok=True)
    (carpeta / "singularidades.json").write_text(
        json.dumps(semilla, ensure_ascii=False), encoding="utf-8"
    )
    return Persistencia(carpeta)


def test_antes_del_momento_no_dispara(tmp_path):
    p = _mundo(tmp_path)
    grafo = GrafoMundo(p)

    assert chequear_singularidades(p, grafo, ANTES) == []
    assert grafo.hechos() == []
    assert p.singularidades_disparadas() == {}


def test_al_alcanzar_el_momento_dispara_una_sola_vez(tmp_path):
    p = _mundo(tmp_path)
    grafo = GrafoMundo(p)

    disparadas = chequear_singularidades(p, grafo, LA_NOCHE)   # el momento exacto cuenta
    assert [s.id for s in disparadas] == ["el_hombre_pez"]

    # El hecho raíz quedó en el grafo con su contenido, lugar y momento agendado.
    hecho = grafo.hecho("el_hombre_pez")
    assert hecho.contenido == SEMILLA[0]["contenido"]
    assert hecho.lugar == "el risco aislado"
    assert hecho.momento == "1850-03-03T23:00:00"

    # Idempotencia: avanzar de nuevo no la vuelve a disparar ni duplica el hecho.
    assert chequear_singularidades(p, grafo, DESPUES) == []
    assert [h.id for h in grafo.hechos()] == ["el_hombre_pez"]
    assert list(p.singularidades_disparadas()) == ["el_hombre_pez"]


def test_los_testigos_iniciales_conocen_la_raiz(tmp_path):
    p = _mundo(tmp_path)
    grafo = GrafoMundo(p)
    chequear_singularidades(p, grafo, LA_NOCHE)

    raiz = grafo.version_raiz("el_hombre_pez")
    assert grafo.quienes_conocen(raiz.id) == ["el_que_no_muere", "pescador_supersticioso"]


def test_sin_testigos_el_hecho_existe_sin_que_nadie_lo_sepa(tmp_path):
    semilla = [{**SEMILLA[0], "testigos_iniciales": []}]
    p = _mundo(tmp_path, semilla)
    grafo = GrafoMundo(p)
    chequear_singularidades(p, grafo, LA_NOCHE)

    raiz = grafo.version_raiz("el_hombre_pez")
    assert grafo.quienes_conocen(raiz.id) == []


def test_el_reset_del_estado_vivo_la_vuelve_pendiente(tmp_path):
    p = _mundo(tmp_path)
    chequear_singularidades(p, GrafoMundo(p), LA_NOCHE)
    p.cerrar()

    # El reset del taller: borra estado.db y grafo.json, las semillas quedan.
    (tmp_path / "mundo" / "estado.db").unlink()
    (tmp_path / "mundo" / "grafo.json").unlink()

    p = Persistencia(tmp_path / "mundo")
    assert p.singularidades_disparadas() == {}
    assert [s.id for s in p.cargar_singularidades()] == ["el_hombre_pez"]
    # Y puede volver a ocurrir: el destino se resetea con el mundo.
    assert [s.id for s in chequear_singularidades(p, GrafoMundo(p), LA_NOCHE)] == ["el_hombre_pez"]


def test_la_hora_del_mundo_persiste_y_arranca_sin_fijar(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    assert p.leer_momento_mundo() is None

    p.guardar_momento_mundo("1850-03-01T07:00:00")
    p.guardar_momento_mundo("1850-03-02T07:00:00")   # la última pisa a la anterior
    p.cerrar()

    assert Persistencia(tmp_path / "mundo").leer_momento_mundo() == "1850-03-02T07:00:00"
