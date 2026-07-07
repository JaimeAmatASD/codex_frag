"""Tests del grafo de información: hechos, versiones derivadas, conocimiento y linaje.

Deterministas y sin LLM: el grafo es código puro (ADR-005). También cubren que la
persistencia pasa por la puerta única y sobrevive a recargar el mundo (regla 1).
"""

import pytest

from codex.grafo_mundo import GrafoMundo
from codex.hechos import Hecho, Version
from codex.persistencia import Persistencia

HECHO = Hecho(
    id="avistamiento-bahia",
    contenido="Se vio una forma enorme y oscura moviéndose bajo el agua de la bahía.",
    momento="1850-03-01T07:00:00",
    lugar="la bahía",
)


def _version_derivada(raiz: Version, **cambios) -> Version:
    base = dict(
        id="v-pescador-1",
        hecho_id=raiz.hecho_id,
        contenido="El mar mostró una señal: algo enorme vino a avisarnos una desgracia.",
        version_padre=raiz.id,
        emisor="un_testigo",
        receptor="pescador_supersticioso",
        momento="1850-03-01T08:00:00",
        distancia_raiz=0.3,
    )
    base.update(cambios)
    return Version(**base)


def test_registrar_hecho_crea_la_raiz(tmp_path):
    grafo = GrafoMundo(Persistencia(tmp_path / "mundo"))
    raiz = grafo.registrar_hecho(HECHO)

    assert raiz.hecho_id == HECHO.id
    assert raiz.contenido == HECHO.contenido
    assert raiz.version_padre is None and raiz.emisor is None and raiz.receptor is None
    assert raiz.distancia_raiz == 0.0
    assert grafo.linaje(raiz.id) == [raiz]
    assert grafo.version_raiz(HECHO.id) == raiz


def test_version_derivada_conocimiento_y_linaje(tmp_path):
    grafo = GrafoMundo(Persistencia(tmp_path / "mundo"))
    raiz = grafo.registrar_hecho(HECHO)
    v1 = _version_derivada(raiz)
    grafo.registrar_version(v1)

    # El receptor conoce la versión que recibió; el linaje va raíz → versión.
    assert grafo.versiones_conocidas("pescador_supersticioso") == [v1]
    assert grafo.versiones_conocidas("pescador_supersticioso", hecho_id=HECHO.id) == [v1]
    assert grafo.versiones_conocidas("pescador_supersticioso", hecho_id="otro") == []
    assert grafo.linaje(v1.id) == [raiz, v1]


def test_un_ser_puede_conocer_varias_versiones_del_mismo_hecho(tmp_path):
    grafo = GrafoMundo(Persistencia(tmp_path / "mundo"))
    raiz = grafo.registrar_hecho(HECHO)
    v1 = _version_derivada(raiz)
    v2 = _version_derivada(raiz, id="v-pescador-2", emisor="otra_boca",
                           contenido="Dicen que algo grande se movió en la bahía.")
    grafo.registrar_version(v1)
    grafo.registrar_version(v2)

    conocidas = grafo.versiones_conocidas("pescador_supersticioso", hecho_id=HECHO.id)
    assert {v.id for v in conocidas} == {"v-pescador-1", "v-pescador-2"}


def test_el_testigo_conoce_la_raiz(tmp_path):
    grafo = GrafoMundo(Persistencia(tmp_path / "mundo"))
    raiz = grafo.registrar_hecho(HECHO)
    grafo.registrar_conocimiento("un_testigo", raiz.id)

    assert grafo.versiones_conocidas("un_testigo") == [raiz]


def test_el_grafo_sobrevive_a_recargar_el_mundo(tmp_path):
    persistencia = Persistencia(tmp_path / "mundo")
    grafo = GrafoMundo(persistencia)
    raiz = grafo.registrar_hecho(HECHO)
    v1 = _version_derivada(raiz)
    grafo.registrar_version(v1)

    recargado = GrafoMundo(Persistencia(tmp_path / "mundo"))
    assert recargado.linaje(v1.id) == [raiz, v1]
    assert recargado.versiones_conocidas("pescador_supersticioso") == [v1]


def test_registros_invalidos_se_rechazan(tmp_path):
    grafo = GrafoMundo(Persistencia(tmp_path / "mundo"))
    raiz = grafo.registrar_hecho(HECHO)

    with pytest.raises(ValueError):        # hecho duplicado
        grafo.registrar_hecho(HECHO)
    with pytest.raises(ValueError):        # versión sin padre
        grafo.registrar_version(_version_derivada(raiz, version_padre=None))
    with pytest.raises(ValueError):        # padre inexistente
        grafo.registrar_version(_version_derivada(raiz, version_padre="no-existe"))
    with pytest.raises(ValueError):        # hecho inexistente
        grafo.registrar_version(_version_derivada(raiz, hecho_id="no-existe"))
    with pytest.raises(ValueError):        # conocimiento de una versión inexistente
        grafo.registrar_conocimiento("alguien", "no-existe")

    grafo.registrar_version(_version_derivada(raiz))
    with pytest.raises(ValueError):        # versión duplicada
        grafo.registrar_version(_version_derivada(raiz))
