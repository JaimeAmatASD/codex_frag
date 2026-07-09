"""Tests del clock mínimo del paso 3: avance, completación y persistencia."""

import pytest
from pydantic import ValidationError

from codex.clocks import Clock, avanzar
from codex.persistencia import Persistencia

AMENAZA = Clock(id="mar-enturbiado", nombre="El mar se enturbia", segmentos_total=6)


def test_el_clock_nace_vacio_y_activo():
    assert AMENAZA.segmentos_actuales == 0
    assert AMENAZA.estado == "activo"


def test_avanzar_suma_y_completa_saturando():
    a1 = avanzar(AMENAZA, 2)
    assert a1.segmentos_actuales == 2 and a1.estado == "activo"

    # Avanzar de más satura en el total y completa: el clock disparó su evento.
    a2 = avanzar(a1, 10)
    assert a2.segmentos_actuales == 6
    assert a2.estado == "completado"

    # Un clock completado no sigue avanzando (se conserva como memoria del mundo).
    assert avanzar(a2, 1) == a2


def test_segmentos_totales_solo_los_de_blades():
    with pytest.raises(ValidationError):
        Clock(id="x", nombre="x", segmentos_total=5)


def test_el_clock_persiste_por_la_puerta_unica(tmp_path):
    p = Persistencia(tmp_path / "mundo")
    assert p.cargar_clock("mar-enturbiado") is None

    p.guardar_clock(AMENAZA)
    p.guardar_clock(avanzar(AMENAZA, 3))   # guardar de nuevo actualiza, no duplica

    recargada = Persistencia(tmp_path / "mundo")
    clock = recargada.cargar_clock("mar-enturbiado")
    assert clock is not None
    assert clock.segmentos_actuales == 3
    assert clock.estado == "activo"
