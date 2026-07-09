"""Tests de la capa de persistencia. Son deterministas: no usan LLM ni red."""

import json

from codex.modelos import Ser
from codex.persistencia import Persistencia

SER_EJEMPLO = {
    "ser_id": "pescador",
    "mana_max": 100,
    "memes": [
        {"id": "PF-mar", "tipo": "fundacional", "texto": "El mar cobra lo que se le debe.", "peso_inicial": 9.0},
        {"id": "presagio", "tipo": "operativo", "texto": "Un avistaje anuncia tormenta.", "peso_inicial": 5.0, "costo": 20},
    ],
}


def _mundo(tmp_path) -> Persistencia:
    return Persistencia(tmp_path / "mundo")


def test_cargar_ser_desde_json(tmp_path):
    p = _mundo(tmp_path)
    p.carpeta_seres.mkdir(parents=True, exist_ok=True)
    (p.carpeta_seres / "pescador.json").write_text(json.dumps(SER_EJEMPLO), encoding="utf-8")

    ser = p.cargar_ser("pescador")

    assert ser.ser_id == "pescador"
    assert len(ser.memes) == 2
    assert ser.memes[0].id == "PF-mar"


def test_origen_de_un_ser_cargado(tmp_path):
    """ADR-007: todo ser lleva `origen`. Si su JSON no lo trae, la puerta de carga
    lo completa con el id del mundo que lo contiene; si lo trae (un ser enchufado
    desde otro mundo), se respeta."""
    p = _mundo(tmp_path)
    p.carpeta_seres.mkdir(parents=True, exist_ok=True)
    (p.carpeta_seres / "pescador.json").write_text(json.dumps(SER_EJEMPLO), encoding="utf-8")
    viajero = {**SER_EJEMPLO, "ser_id": "viajero", "origen": "cala_norte"}
    (p.carpeta_seres / "viajero.json").write_text(json.dumps(viajero), encoding="utf-8")

    assert p.cargar_ser("pescador").origen == "mundo"
    assert p.cargar_ser("viajero").origen == "cala_norte"


def test_sembrar_es_idempotente(tmp_path):
    p = _mundo(tmp_path)
    ser = Ser(**SER_EJEMPLO)

    p.sembrar_ser(ser)
    p.actualizar_pesos("pescador", {"PF-mar": 7.5})  # el peso evoluciona...
    p.sembrar_ser(ser)                               # ...y re-sembrar NO lo pisa.

    estado = p.leer_estado("pescador")
    assert set(estado) == {"PF-mar", "presagio"}
    assert estado["PF-mar"].peso == 7.5


def test_registrar_distingue_loadout_de_movilizado(tmp_path):
    """Regla 4: estar en el loadout no es lo mismo que haberse usado."""
    p = _mundo(tmp_path)
    p.sembrar_ser(Ser(**SER_EJEMPLO))

    # Ambos memes entran al loadout, pero solo 'presagio' se moviliza de verdad.
    p.registrar_activaciones(
        "pescador", "2026-06-13T20:00:00", "avistaje raro",
        loadout_ids=["PF-mar", "presagio"], movilizados_ids=["presagio"],
    )

    estado = p.leer_estado("pescador")
    assert estado["PF-mar"].veces_en_loadout == 1
    assert estado["PF-mar"].veces_movilizado == 0       # no se usó
    assert estado["PF-mar"].ultima_activacion is None    # así que no cuenta como activación
    assert estado["presagio"].veces_en_loadout == 1
    assert estado["presagio"].veces_movilizado == 1
    assert estado["presagio"].ultima_activacion == "2026-06-13T20:00:00"


def test_actualizar_pesos(tmp_path):
    p = _mundo(tmp_path)
    p.sembrar_ser(Ser(**SER_EJEMPLO))

    p.actualizar_pesos("pescador", {"presagio": 4.2})

    assert p.leer_estado("pescador")["presagio"].peso == 4.2


def test_cache_embeddings(tmp_path):
    p = _mundo(tmp_path)

    assert p.leer_vector("abc") is None
    p.guardar_vector("abc", b"\x01\x02\x03")
    assert p.leer_vector("abc") == b"\x01\x02\x03"
