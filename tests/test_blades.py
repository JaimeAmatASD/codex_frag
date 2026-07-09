"""Tests del enchufe Blades: posición/efecto desde el cristal, tiradas con tres
resultados, regla del cero, empuje pagando stress, la mala consecuencia que
avanza el clock de amenaza, y la narración del resultado (el LLM narra lo que el
motor decidió). Deterministas: afinidades dadas, dados guionados, MockClient."""

import logging

import pytest

from codex.blades import HojaMecanica, SistemaBlades, narrar_resolucion
from codex.llm import ErrorLLM, MockClient
from codex.loadout import Loadout
from codex.modelos import MemeVivo, TipoMeme
from codex.reglas import (
    AccionDeclarada,
    AvanzarClock,
    CategoriaResultado,
    ContextoAccion,
    Empuje,
    NivelEfecto,
    PagarStress,
    Posicion,
)

HOJA = HojaMecanica(ser_id="pescador", acciones={"faenar": 2, "pelear": 0})
ACCION = AccionDeclarada(ser_id="pescador", accion="faenar",
                         descripcion="Salir a faenar con el mar picado.")


class DadosGuionados:
    """RNG falso: entrega los dados del guion, en orden (regla 5)."""

    def __init__(self, dados):
        self._dados = list(dados)

    def randint(self, a, b):
        return self._dados.pop(0)


def _contexto(memes_y_afinidades, stress=0.0):
    """Arma un ContextoAccion a mano: (id, tipo, afinidad) por meme del loadout."""
    seleccionados = [
        MemeVivo(id=mid, tipo=tipo, texto=mid, costo=0, peso=5.0)
        for mid, tipo, _ in memes_y_afinidades
    ]
    return ContextoAccion(
        loadout=Loadout(ser_id="pescador", seleccionados=seleccionados, mana_usado=0),
        afinidades={mid: af for mid, _, af in memes_y_afinidades},
        estado_reglas={"stress": stress},
    )


def _blades(dados=(6,)):
    return SistemaBlades(
        hojas={"pescador": HOJA}, clock_amenaza_id="amenaza", rng=DadosGuionados(dados)
    )


CRISTAL_A_FAVOR = [
    ("PF-mar", TipoMeme.FUNDACIONAL, 0.9),
    ("leer-aguas", TipoMeme.OPERATIVO, 0.95),
    ("faena-dura", TipoMeme.OPERATIVO, 0.95),
]
CRISTAL_EN_CONTRA = [
    ("PF-mar", TipoMeme.FUNDACIONAL, 0.1),      # la PF choca con la acción
    ("leer-aguas", TipoMeme.OPERATIVO, 0.1),
    ("faena-dura", TipoMeme.OPERATIVO, 0.1),
]
CRISTAL_NEUTRO = [
    ("PF-mar", TipoMeme.FUNDACIONAL, 0.6),
    ("leer-aguas", TipoMeme.OPERATIVO, 0.8),
]


def test_blades_cumple_la_interfaz_del_nucleo():
    from codex.reglas import SistemaDeReglas

    assert isinstance(_blades(), SistemaDeReglas)


def test_cristal_a_favor_da_posicion_controlada_y_efecto_grande():
    ev = _blades().evaluar(ACCION, _contexto(CRISTAL_A_FAVOR))
    assert ev.posicion == Posicion.CONTROLADA
    assert ev.efecto == NivelEfecto.GRANDE          # tres memes relevantes
    assert ev.dados == 2                            # el rango de "faenar" en la hoja


def test_cristal_en_contra_da_posicion_desesperada_y_efecto_limitado():
    ev = _blades().evaluar(ACCION, _contexto(CRISTAL_EN_CONTRA))
    assert ev.posicion == Posicion.DESESPERADA
    assert ev.efecto == NivelEfecto.LIMITADO        # ningún meme relevante


def test_cristal_neutro_da_posicion_arriesgada_y_efecto_estandar():
    ev = _blades().evaluar(ACCION, _contexto(CRISTAL_NEUTRO))
    assert ev.posicion == Posicion.ARRIESGADA
    assert ev.efecto == NivelEfecto.ESTANDAR        # un solo meme relevante


def test_ser_sin_hoja_no_participa_de_scores():
    accion = AccionDeclarada(ser_id="forastero", accion="faenar", descripcion="...")
    with pytest.raises(ValueError):
        _blades().evaluar(accion, _contexto(CRISTAL_NEUTRO))


def test_tirada_limpia_no_deja_efectos():
    blades = _blades(dados=(3, 6))
    ctx = _contexto(CRISTAL_A_FAVOR)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    assert r.dados_tirados == [3, 6]                # dos dados: el rango de "faenar"
    assert r.categoria == CategoriaResultado.LIMPIO # manda el más alto
    assert r.efectos == []


def test_exito_con_costo_con_dado_mas_alto_4_o_5():
    blades = _blades(dados=(4, 2))
    ctx = _contexto(CRISTAL_NEUTRO)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)
    assert r.categoria == CategoriaResultado.CON_COSTO
    assert r.efectos == []


def test_mala_consecuencia_avanza_el_clock_de_amenaza():
    blades = _blades(dados=(2, 3))
    ctx = _contexto(CRISTAL_NEUTRO)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    assert r.categoria == CategoriaResultado.MALA_CONSECUENCIA
    assert r.efectos == [AvanzarClock(clock_id="amenaza", segmentos=1)]


def test_en_posicion_desesperada_la_mala_consecuencia_pega_doble():
    blades = _blades(dados=(1, 1))
    ctx = _contexto(CRISTAL_EN_CONTRA)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)
    assert r.efectos == [AvanzarClock(clock_id="amenaza", segmentos=2)]


def test_regla_del_cero_tira_dos_y_toma_el_menor():
    blades = _blades(dados=(6, 2))
    ctx = _contexto(CRISTAL_NEUTRO)
    accion = AccionDeclarada(ser_id="pescador", accion="pelear", descripcion="...")
    ev = blades.evaluar(accion, ctx)
    assert ev.dados == 0

    r = blades.tirar(ev, ctx)
    assert r.dados_tirados == [6, 2]
    assert r.categoria == CategoriaResultado.MALA_CONSECUENCIA   # manda el MENOR: 2


def test_empuje_dado_extra_paga_stress():
    blades = _blades(dados=(1, 1, 6))
    ctx = _contexto(CRISTAL_NEUTRO, stress=3.0)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx, empuje=Empuje.DADO_EXTRA)

    assert len(r.dados_tirados) == 3                # 2 del rango + 1 comprado
    assert r.categoria == CategoriaResultado.LIMPIO
    assert PagarStress(ser_id="pescador", cantidad=2) in r.efectos


def test_empuje_mejora_posicion_un_nivel():
    blades = _blades(dados=(1, 1))
    ctx = _contexto(CRISTAL_EN_CONTRA, stress=0.0)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx, empuje=Empuje.MEJORAR_POSICION)

    assert r.evaluacion.posicion == Posicion.ARRIESGADA     # subió desde desesperada
    assert AvanzarClock(clock_id="amenaza", segmentos=1) in r.efectos  # ya no pega doble
    assert PagarStress(ser_id="pescador", cantidad=2) in r.efectos


def test_empuje_mejora_efecto_un_nivel():
    blades = _blades(dados=(6, 6))
    ctx = _contexto(CRISTAL_NEUTRO, stress=0.0)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx, empuje=Empuje.MEJORAR_EFECTO)
    assert r.evaluacion.efecto == NivelEfecto.GRANDE        # subió desde estándar


def test_no_se_puede_empujar_sin_stress_disponible():
    blades = _blades(dados=(6, 6))
    ctx = _contexto(CRISTAL_NEUTRO, stress=8.0)             # 8 + 2 > 9 de tope
    ev = blades.evaluar(ACCION, ctx)
    with pytest.raises(ValueError):
        blades.tirar(ev, ctx, empuje=Empuje.DADO_EXTRA)


def test_la_narracion_recibe_la_categoria_explicita():
    """El LLM no decide el resultado: lo recibe como rúbrica explícita (sin eso,
    tiende a narrar éxitos limpios siempre). La narración es prosa, sin validar
    contra esquema: el motor ya dispuso todo lo que importa."""
    blades = _blades(dados=(4, 2))
    ctx = _contexto(CRISTAL_NEUTRO)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)
    cliente = MockClient(respuestas=["Logra zarpar, pero el patrón ya no lo mira igual."])

    narracion = narrar_resolucion(cliente, r, ctx)

    assert narracion == "Logra zarpar, pero el patrón ya no lo mira igual."
    prompt = cliente.llamadas[0]
    assert "éxito con costo" in prompt          # la categoría, explícita
    assert "arriesgada" in prompt               # los términos de la tirada
    assert ACCION.descripcion in prompt         # lo que el jugador declaró
    assert "PF-mar" in prompt                   # el cristal del ser tiñe la narración


def test_sin_llm_el_resultado_queda_dicho_igual(caplog):
    """ADR-005: si el LLM falla, el Score no se pierde — queda la crónica mecánica
    del resultado, con log. La tirada ya ocurrió y sus efectos son reales."""
    blades = _blades(dados=(2, 1))
    ctx = _contexto(CRISTAL_NEUTRO)
    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    class ClienteCaido:
        def responder(self, prompt):
            raise ErrorLLM("429")

    with caplog.at_level(logging.WARNING):
        narracion = narrar_resolucion(ClienteCaido(), r, ctx)

    assert "mala consecuencia" in narracion     # la crónica mínima dice qué pasó
    assert any("narración" in m.message.lower() for m in caplog.records)
