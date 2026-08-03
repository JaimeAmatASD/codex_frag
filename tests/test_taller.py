"""Tests del Taller (el dashboard autoral, docs/TALLER_DISENO.md).

Sin red ni navegador (regla 5): TestClient de FastAPI, MockClient para el LLM,
encoder de vectores falso, mundos en tmp_path. La página HTML no se testea acá
(es una vista fina); el dictado y la lectura son features del navegador.
"""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from codex.llm import MockClient
from codex.persistencia import Persistencia
from taller.app import crear_app

VECTORES = {}  # los tests que midan afinidades reales cargan acá sus vectores


def _encoder(textos):
    return [np.asarray(VECTORES.get(t, [0.5, 0.5]), dtype=np.float32) for t in textos]


class DadosCargables:
    """RNG guionable desde cada test (regla 5): se le cargan los dados que saldrán."""

    def __init__(self):
        self._dados = []

    def cargar(self, dados):
        self._dados.extend(dados)

    def randint(self, a, b):
        assert self._dados, "el test no cargó dados suficientes"
        return self._dados.pop(0)


@pytest.fixture()
def taller(tmp_path):
    """Un taller limpio sobre una carpeta de mundos vacía, con LLM y dados guionables."""
    cliente = MockClient(respuesta_por_defecto="")
    rng = DadosCargables()
    raiz = tmp_path / "mundos"
    app = crear_app(raiz_mundos=raiz, cliente_llm=cliente, encoder=_encoder, rng=rng,
                    carpeta_pendientes=tmp_path / "pendientes")
    with TestClient(app) as tc:
        tc.cliente_llm = cliente
        tc.rng = rng
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


def test_ser_id_con_ruta_da_400_y_no_escribe_fuera(taller):
    # El ser_id se vuelve carpeta: "../fuera" escribiría fuera del mundo.
    taller.post("/mundos", json={"nombre": "taberna"})
    ser = _ser_tabernero(ser_id="../fuera")
    r = taller.post("/seres?mundo=taberna", json=ser)
    assert r.status_code == 400
    assert not (taller.raiz_mundos / "fuera").exists()


# ----- Zona Mundo: el reloj y las singularidades -----

def _singularidad(**extra):
    base = {
        "id": "el_hombre_pez",
        "contenido": "La noche de la primera luna de sangre, en el risco aislado, "
                     "cada uno de ellos se encuentra con un Hombre Pez.",
        "momento": "1850-03-03T23:00:00",
        "lugar": "el risco aislado",
        "testigos_iniciales": ["pescador_supersticioso"],
    }
    base.update(extra)
    return base


def test_reloj_y_singularidad_de_punta_a_punta(taller):
    taller.post("/mundos", json={"nombre": "costa"})
    assert taller.get("/reloj?mundo=costa").json() == {"momento": None}
    assert taller.post("/singularidades?mundo=costa", json=_singularidad()).status_code == 200
    assert taller.get("/singularidades?mundo=costa").json()[0]["estado"] == "pendiente"

    # Fijar la hora antes del momento: nada dispara.
    r = taller.post("/reloj?mundo=costa", json={"momento": "1850-03-03T20:00:00"})
    assert r.json()["disparadas"] == []

    # Avanzar hasta la noche: dispara y aparece en Lore con su testigo.
    r = taller.post("/reloj/avanzar?mundo=costa", json={"horas": 3})
    assert r.json()["momento"] == "1850-03-03T23:00:00"
    assert [s["id"] for s in r.json()["disparadas"]] == ["el_hombre_pez"]
    assert taller.get("/singularidades?mundo=costa").json()[0]["estado"] == "disparada"
    hechos = taller.get("/hechos?mundo=costa").json()
    assert hechos[0]["hecho"]["id"] == "el_hombre_pez"
    assert hechos[0]["versiones"][0]["conocida_por"] == ["pescador_supersticioso"]

    # Avanzar de nuevo no la re-dispara (idempotencia, también vía la API).
    r = taller.post("/reloj/avanzar?mundo=costa", json={"dias": 1})
    assert r.json()["disparadas"] == []


def test_editar_una_singularidad_reemplaza_por_id(taller):
    taller.post("/mundos", json={"nombre": "costa"})
    taller.post("/singularidades?mundo=costa", json=_singularidad())
    taller.post("/singularidades?mundo=costa", json=_singularidad(lugar="la escollera"))

    lista = taller.get("/singularidades?mundo=costa").json()
    assert len(lista) == 1
    assert lista[0]["lugar"] == "la escollera"


def test_avanzar_sin_hora_fijada_da_409_y_avances_invalidos_400(taller):
    taller.post("/mundos", json={"nombre": "costa"})
    assert taller.post("/reloj/avanzar?mundo=costa", json={"horas": 1}).status_code == 409

    taller.post("/reloj?mundo=costa", json={"momento": "1850-03-01T07:00:00"})
    assert taller.post("/reloj/avanzar?mundo=costa", json={}).status_code == 400
    assert taller.post("/reloj/avanzar?mundo=costa", json={"horas": -2}).status_code == 400


def test_singularidad_con_momento_invalido_da_400(taller):
    taller.post("/mundos", json={"nombre": "costa"})
    r = taller.post("/singularidades?mundo=costa",
                    json=_singularidad(momento="la primera luna de sangre"))
    assert r.status_code == 400


def test_reset_vuelve_pendiente_la_singularidad_y_borra_la_hora(taller):
    taller.post("/mundos", json={"nombre": "costa"})
    taller.post("/singularidades?mundo=costa", json=_singularidad())
    # Fijar la hora MÁS ALLÁ del momento también dispara: el destino no se saltea.
    r = taller.post("/reloj?mundo=costa", json={"momento": "1850-03-04T00:00:00"})
    assert [s["id"] for s in r.json()["disparadas"]] == ["el_hombre_pez"]

    taller.post("/reset?mundo=costa")
    assert taller.get("/reloj?mundo=costa").json() == {"momento": None}
    assert taller.get("/singularidades?mundo=costa").json()[0]["estado"] == "pendiente"


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


def test_una_tension_a_un_meme_inexistente_no_se_guarda_en_silencio(taller):
    """Bug del 2026-07-30: el campo de tensiones del Taller parte por comas, así
    que un id CON coma se guardaba partido en dos referencias inexistentes. El
    motor las ignoraba con un warning que nadie leía y el ser corría sin
    tensiones. Guardar una referencia que no existe ahora es un 400."""
    taller.post("/mundos", json={"nombre": "taberna"})
    roto = _ser_tabernero()
    roto["memes"][1]["tensiones"] = ["PF-casa", "meme que no existe"]

    r = taller.post("/seres?mundo=taberna", json=roto)

    assert r.status_code == 400
    assert "meme que no existe" in r.json()["detail"]


def test_una_tension_a_un_meme_del_ser_se_guarda_bien(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    bien = _ser_tabernero()
    bien["memes"][1]["tensiones"] = ["PF-casa"]

    assert taller.post("/seres?mundo=taberna", json=bien).status_code == 200


def test_derivar_propone_sin_tocar_disco(taller):
    import json as _json
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.cliente_llm.respuesta_por_defecto = _json.dumps({
        "ser_id": "veterinario",
        "mana_max": 40,
        "memes": [
            {"id": "pf_ayudar", "tipo": "fundacional", "texto": "Ningún ser que sufre me es ajeno.",
             "peso_inicial": 9.0, "costo": 0, "funcion": "moral", "tensiones": ["no_perdono"]},
            {"id": "no_perdono", "tipo": "operativo", "texto": "Lo que mi hijo hizo no tiene perdón.",
             "peso_inicial": 8.5, "costo": 20, "funcion": "emocional"},
        ],
        "hoja": {"stress_max": 9, "acciones": {"curar": 4}},
    }, ensure_ascii=False)

    r = taller.post("/seres/derivar?mundo=taberna", json={"descripcion": "un veterinario de 62 años"})

    assert r.status_code == 200
    propuesta = r.json()["propuesta"]
    assert propuesta["ser_id"] == "veterinario"
    assert propuesta["memes"][0]["tensiones"] == ["no_perdono"]
    # NADA en disco: la propuesta se cura en el formulario, no se guarda sola.
    assert not (taller.raiz_mundos / "taberna" / "seres" / "veterinario").exists()
    # La bitácora registró la derivación (material de calibración del template).
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "derivacion"
    assert entradas[0]["terminos"]["reintento"] is False


def test_derivar_degrada_con_mensaje_claro_y_sin_guardar(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.cliente_llm.respuesta_por_defecto = "esto nunca va a ser un JSON"

    r = taller.post("/seres/derivar?mundo=taberna", json={"descripcion": "alguien"})

    assert r.status_code == 422
    assert "reformular" in r.json()["detail"]
    assert taller.get("/bitacora?mundo=taberna").json() == []


# ----- Zona Diálogo -----

def test_dialogo_responde_y_la_charla_deja_huella(taller):
    """La charla es vida (regla 4): moviliza los memes afines y el uso refuerza.
    Con el encoder por defecto todo es afín a todo: ambos memes resuenan."""
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    taller.cliente_llm.respuesta_por_defecto = "Acá se escucha todo, forastero."

    r = taller.post("/dialogo?mundo=taberna", json={
        "ser_id": "tabernero", "historial": [],
        "mensaje": "Un forastero te pregunta hace cuánto que existe esta taberna.",
    })

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["respuesta"] == "Acá se escucha todo, forastero."
    assert {m["id"] for m in cuerpo["memes_activos"]} == {"PF-casa", "oido-fino"}
    # El endpoint reporta el peso que se movió, como /transmitir y /score/tirar.
    antes, despues = cuerpo["pesos_movidos"]["oido-fino"]
    assert despues > antes

    # La charla dejó huella: movilizaciones y refuerzo (la PF no cambia de peso).
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] > 6.0
    assert estado["oido-fino"]["veces_movilizado"] == 1
    assert estado["PF-casa"]["veces_movilizado"] == 1
    assert estado["PF-casa"]["peso"] == 9.0

    # Y queda en la bitácora, para comparar intentos.
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "dialogo"
    assert entradas[0]["ser"] == "tabernero"
    assert entradas[0]["salida"] == "Acá se escucha todo, forastero."


def test_dialogo_manda_el_historial_completo_al_prompt(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    taller.cliente_llm.respuesta_por_defecto = "..."

    taller.post("/dialogo?mundo=taberna", json={
        "ser_id": "tabernero",
        "historial": [
            {"quien": "vos", "texto": "hace cuánto que existe esta taberna?"},
            {"quien": "tabernero", "texto": "más de lo que quiero acordarme."},
        ],
        "mensaje": "y quién la construyó?",
    })

    prompt = taller.cliente_llm.llamadas[-1]
    assert "hace cuánto que existe esta taberna?" in prompt
    assert "más de lo que quiero acordarme." in prompt
    assert "y quién la construyó?" in prompt


def test_dialogo_ser_inexistente_da_404(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    r = taller.post("/dialogo?mundo=taberna", json={
        "ser_id": "fantasma", "historial": [], "mensaje": "hola?",
    })
    assert r.status_code == 404


def test_modo_editar_mueve_el_peso_vivo_y_el_dialogo_siguiente_lo_ve(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    r = taller.post("/seres/tabernero/pesos?mundo=taberna", json={"pesos": {"oido-fino": 1.0}})
    assert r.status_code == 200

    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] == 1.0
    # La semilla no se tocó: el modo editar es sobre el estado vivo, no ser.json.
    ser = taller.get("/seres?mundo=taberna").json()[0]
    assert ser["memes"][1]["peso_inicial"] == 6.0


# ----- El espejo (SPECULUM) -----

MIRADA_JSON = json.dumps({
    "reflexion": "Escucho todo y no cuento casi nada: estoy siendo el que acumula.",
    "propuestas": [
        {"tipo": "ajustar_peso", "meme_id": "oido-fino", "delta": 1.5,
         "justificacion": "usada en casi todas las situaciones registradas"},
        {"tipo": "proponer_experimental", "meme_id": "sospecha_del_silencio",
         "texto": "Callar también es una forma de mentir.", "peso_inicial": 2.0,
         "costo": 10, "justificacion": "las grietas repetidas giran en lo que callo"},
    ],
})


def _acumular_movilizaciones(taller, veces=12):
    """Arma trayectoria real por la puerta única: N usos efectivos de oido-fino."""
    p = Persistencia(taller.raiz_mundos / "taberna")
    for i in range(veces):
        p.registrar_activaciones(
            "tabernero", f"1850-03-01T{10 + i % 12}:00:00", "charla en la barra",
            ["PF-casa", "oido-fino"], ["oido-fino"],
        )
    p.cerrar()


def test_speculum_sin_material_avisa_claro_y_no_llama_al_llm(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    r = taller.post("/speculum/mirar?mundo=taberna", json={"ser_id": "tabernero"})

    assert r.status_code == 200
    assert r.json() == {"suficiente": False, "movilizaciones": 0, "minimo": 10}
    assert taller.cliente_llm.llamadas == []   # el espejo calla: ni una llamada


def test_speculum_mirar_lista_propuestas_sin_aplicar_nada(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    _acumular_movilizaciones(taller)
    taller.cliente_llm.respuesta_por_defecto = MIRADA_JSON

    r = taller.post("/speculum/mirar?mundo=taberna", json={"ser_id": "tabernero"})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["suficiente"] is True
    assert "acumula" in cuerpo["reflexion"]
    assert [p["tipo"] for p in cuerpo["propuestas"]] == ["ajustar_peso", "proponer_experimental"]

    # NADA se aplicó: ni el peso vivo ni la semilla.
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] == 6.0
    assert "sospecha_del_silencio" not in estado
    ser = taller.get("/seres?mundo=taberna").json()[0]
    assert len(ser["memes"]) == 2

    # Pero la mirada queda en la bitácora, propuestas incluidas.
    entrada = taller.get("/bitacora?mundo=taberna").json()[0]
    assert entrada["tipo"] == "speculum"
    assert len(entrada["terminos"]["propuestas"]) == 2


def test_aprobar_un_ajuste_mueve_el_peso_vivo_y_registra_la_justificacion(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    r = taller.post("/speculum/aplicar?mundo=taberna", json={
        "ser_id": "tabernero",
        "propuesta": {"tipo": "ajustar_peso", "meme_id": "oido-fino", "delta": 1.5,
                      "justificacion": "usada en casi todas las situaciones"},
    })

    assert r.status_code == 200
    assert r.json()["efecto"] == {"meme": "oido-fino", "antes": 6.0, "despues": 7.5}
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] == 7.5
    # La semilla no se tocó (regla 1): el ajuste es sobre el estado vivo.
    ser = taller.get("/seres?mundo=taberna").json()[0]
    assert ser["memes"][1]["peso_inicial"] == 6.0

    entrada = taller.get("/bitacora?mundo=taberna").json()[0]
    assert entrada["tipo"] == "speculum_aplicada"
    assert entrada["terminos"]["justificacion"] == "usada en casi todas las situaciones"


def test_aprobar_un_experimental_entra_a_la_semilla_y_se_siembra(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    r = taller.post("/speculum/aplicar?mundo=taberna", json={
        "ser_id": "tabernero",
        "propuesta": {"tipo": "proponer_experimental", "meme_id": "sospecha_del_silencio",
                      "texto": "Callar también es una forma de mentir.",
                      "peso_inicial": 2.0, "costo": 10,
                      "justificacion": "las grietas repetidas giran en lo que callo"},
    })

    assert r.status_code == 200
    ser = taller.get("/seres?mundo=taberna").json()[0]
    nuevo = next(m for m in ser["memes"] if m["id"] == "sospecha_del_silencio")
    assert nuevo["tipo"] == "experimental"
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["sospecha_del_silencio"]["peso"] == 2.0   # sembrado, vivo


def test_aplicar_sobre_una_piedra_fundacional_se_rechaza(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())

    r = taller.post("/speculum/aplicar?mundo=taberna", json={
        "ser_id": "tabernero",
        "propuesta": {"tipo": "ajustar_peso", "meme_id": "PF-casa", "delta": -2.0,
                      "justificacion": "ya no siento que sea mi reino"},
    })

    assert r.status_code == 400
    assert "piedra fundacional" in r.json()["detail"]
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["PF-casa"]["peso"] == 9.0   # intocable, intocada


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


# ----- Zona Probar -----

def _mundo_armado(taller):
    """Taberna con el tabernero (semilla + hoja) y el hecho del kraken con testigo."""
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    taller.post("/hechos?mundo=taberna", json={**HECHO, "testigo": "el_viejo_tomas"})


def test_transmitir_muta_y_queda_en_grafo_y_bitacora(taller):
    import json as _json
    _mundo_armado(taller)
    taller.cliente_llm.respuesta_por_defecto = _json.dumps({
        "contenido_entendido": "Al viejo Tomás algo le rompió las redes; acá se termina sabiendo todo.",
        "memes_resonantes": ["oido-fino"],
    }, ensure_ascii=False)

    r = taller.post("/transmitir?mundo=taberna", json={
        "emisor_id": "el_viejo_tomas",
        "receptor_id": "tabernero",
        "version_id": "kraken-bahia-raiz",
        "momento": "1850-03-01T09:00:00",
    })

    assert r.status_code == 200
    version = r.json()["version"]
    assert "se termina sabiendo todo" in version["contenido"]
    assert version["emisor"] == "el_viejo_tomas"

    # Quedó en el árbol del hecho, y el tabernero la conoce.
    arbol = taller.get("/hechos?mundo=taberna").json()[0]
    assert len(arbol["versiones"]) == 2
    assert arbol["versiones"][1]["conocida_por"] == ["tabernero"]

    # Y en la bitácora, para comparar iteraciones después.
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "transmision"
    assert entradas[0]["ser"] == "tabernero"
    assert "sabiendo todo" in entradas[0]["salida"]


def test_transmitir_muestra_los_pesos_que_movio_la_contradiccion(taller):
    """Experimento 04: el meme radicalizable contradicho gana peso, y la
    respuesta y la bitácora lo muestran para el protocolo A/B."""
    import json as _json
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero(memes=[
        {"id": "PF-casa", "tipo": "fundacional", "texto": "Mi taberna es mi reino.",
         "peso_inicial": 9.0},
        {"id": "oido-fino", "tipo": "operativo", "texto": "Acá se escucha todo.",
         "peso_inicial": 6.0, "costo": 20, "aprendizaje": "se_radicaliza"},
    ]))
    taller.post("/hechos?mundo=taberna", json={**HECHO, "testigo": "el_viejo_tomas"})
    taller.cliente_llm.respuesta_por_defecto = _json.dumps({
        "contenido_entendido": "Dicen que en mi propia taberna nadie se enteró de nada.",
        "memes_resonantes": [],
        "memes_desafiados": ["oido-fino"],
    }, ensure_ascii=False)

    r = taller.post("/transmitir?mundo=taberna", json={
        "emisor_id": "el_viejo_tomas",
        "receptor_id": "tabernero",
        "version_id": "kraken-bahia-raiz",
        "momento": "1850-03-01T09:00:00",
    })

    assert r.status_code == 200
    movidos = r.json()["pesos_movidos"]
    assert list(movidos) == ["oido-fino"]
    antes, despues = movidos["oido-fino"]
    assert antes == 6.0 and despues > 6.0    # contradicho → se atrinchera

    # La semilla guardó la política y la bitácora registró el movimiento.
    ser = taller.get("/seres?mundo=taberna").json()[0]
    assert ser["memes"][1]["aprendizaje"] == "se_radicaliza"
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["terminos"]["pesos_movidos"] == {"oido-fino": [antes, despues]}


def test_transmitir_muestra_y_registra_la_grieta(taller):
    import json as _json
    taller.post("/mundos", json={"nombre": "taberna"})
    # PF y operativo en tensión declarada, de peso parejo (9.0 y 8.0: diferencia
    # normalizada 0.11, bajo el umbral): la grieta debe activarse al escuchar.
    taller.post("/seres?mundo=taberna", json=_ser_tabernero(memes=[
        {"id": "PF-casa", "tipo": "fundacional", "texto": "Mi taberna es mi reino.",
         "peso_inicial": 9.0, "tensiones": ["oido-fino"]},
        {"id": "oido-fino", "tipo": "operativo", "texto": "Acá se escucha todo.",
         "peso_inicial": 8.0, "costo": 20},
    ]))
    taller.post("/hechos?mundo=taberna", json={**HECHO, "testigo": "el_viejo_tomas"})
    taller.cliente_llm.respuesta_por_defecto = _json.dumps({
        "contenido_entendido": "Algo pasó en la bahía, y en mi taberna ya se sabe.",
        "memes_resonantes": ["oido-fino"],
    }, ensure_ascii=False)

    r = taller.post("/transmitir?mundo=taberna", json={
        "emisor_id": "el_viejo_tomas",
        "receptor_id": "tabernero",
        "version_id": "kraken-bahia-raiz",
        "momento": "1850-03-01T09:00:00",
    })

    assert r.status_code == 200
    tensiones = r.json()["tensiones"]
    assert len(tensiones) == 1
    assert {tensiones[0]["meme_a"], tensiones[0]["meme_b"]} == {"PF-casa", "oido-fino"}

    # El prompt que viajó al LLM lleva la grieta, y la bitácora la registra.
    assert "grieta" in taller.cliente_llm.llamadas[-1]
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert len(entradas[0]["terminos"]["tensiones"]) == 1


def test_score_sin_clock_da_409(taller):
    _mundo_armado(taller)
    r = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores.",
    })
    assert r.status_code == 409
    assert "clock" in r.json()["detail"].lower()


def test_score_completo_evaluar_tirar_y_efectos(taller):
    _mundo_armado(taller)
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6,
    })
    taller.cliente_llm.respuesta_por_defecto = "El tabernero escucha más de lo que quisiera."
    taller.rng.cargar([1, 2, 3, 1])   # 3 del rango + 1 del empuje → manda el 3: mala

    ev = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores.",
    })
    assert ev.status_code == 200
    terminos = ev.json()
    assert terminos["evaluacion"]["dados"] == 3            # el rango de "escuchar"

    r = taller.post("/score/tirar?mundo=taberna", json={**terminos, "empuje": "dado_extra"})
    assert r.status_code == 200
    res = r.json()
    assert res["resolucion"]["categoria"] == "mala_consecuencia"
    assert res["narracion"] == "El tabernero escucha más de lo que quisiera."
    assert res["stress"] == 4.0        # 2 por el empuje (lo que gastó el autor)
                                       # + 2 por la mala consecuencia (lo que vivió el ser)
    assert res["clock"]["segmentos_actuales"] == 1         # la amenaza avanzó

    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "score"


def test_score_deja_huella_en_el_ser(taller):
    """El Score escribe en la libreta del ser (regla 4), como la transmisión:
    todo el loadout estuvo en consideración, pero solo los memes que actuaron
    en la tirada cuentan como movilizados, y el uso refuerza su peso."""
    _mundo_armado(taller)
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6,
    })
    # Afinidades guionadas: "oido-fino" resuena con la acción (1.0, relevante);
    # la PF queda en el medio (~0.71): ni en conflicto ni relevante — solo mira.
    VECTORES["Quedarse detrás de la barra oyendo a los pescadores."] = [1.0, 0.0]
    VECTORES["Acá se escucha todo."] = [1.0, 0.0]
    VECTORES["Mi taberna es mi reino."] = [0.7071, 0.7071]
    taller.rng.cargar([4, 4, 4])   # manda el 4: con costo, sin efectos que apliquen

    ev = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores.",
    })
    assert ev.status_code == 200

    r = taller.post("/score/tirar?mundo=taberna", json=ev.json())
    assert r.status_code == 200
    # El endpoint reporta los pesos que se movieron, como /transmitir.
    antes, despues = r.json()["pesos_movidos"]["oido-fino"]
    assert despues > antes

    p = Persistencia(taller.raiz_mundos / "taberna")
    try:
        estado = p.leer_estado("tabernero")
    finally:
        p.cerrar()
    # Todo el loadout estuvo en consideración...
    assert estado["PF-casa"].veces_en_loadout == 1
    assert estado["oido-fino"].veces_en_loadout == 1
    # ...pero solo el que actuó en la tirada se usó de verdad (regla 4).
    assert estado["oido-fino"].veces_movilizado == 1
    assert estado["PF-casa"].veces_movilizado == 0
    # Y el uso refuerza: la semilla era 6.0.
    assert estado["oido-fino"].peso > 6.0

    # La bitácora anota qué memes se movilizaron: el espejo leerá esto.
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["terminos"]["movilizados"] == ["oido-fino"]


def test_avanzar_el_reloj_enfria_los_memes(taller):
    """Paso 1 de la vida ociosa: el tiempo del mundo enfría lo que no se usa.
    Un ciclo de decaimiento = un día del mundo; las PF no se mueven. Avanzar
    12h dos veces da lo mismo que avanzar un día entero."""
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T00:00:00"})

    r = taller.post("/reloj/avanzar?mundo=taberna", json={"dias": 1})
    assert r.status_code == 200

    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    esperado = 0.1 + (6.0 - 0.1) * 0.95          # piso + (peso-piso)*(1-tasa)^1
    assert estado["oido-fino"]["peso"] == pytest.approx(esperado)
    assert estado["PF-casa"]["peso"] == 9.0      # la PF no decae

    taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 12})
    taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 12})
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    esperado = 0.1 + (esperado - 0.1) * 0.95     # otro día entero, en dos tramos
    assert estado["oido-fino"]["peso"] == pytest.approx(esperado)


def test_los_clocks_se_listan(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6,
    })
    clocks = taller.get("/clocks?mundo=taberna").json()
    assert clocks[0]["id"] == "amenaza" and clocks[0]["estado"] == "activo"


# ----- La vida ociosa (el latido): POST /vida y su cola -----

RUTINA_TABERNA = {
    "plantillas": [
        {"id": "abrir", "texto": "Abre la taberna y baldea el piso.", "franja": "mañana"},
        {"id": "mediodia", "texto": "Sirve el guiso del mediodía.", "franja": "tarde"},
        {"id": "cierre", "texto": "Cuenta la caja a la luz de una vela.", "franja": "noche"},
    ]
}


def _preparar_taberna_viva(taller, con_rutina=True, con_reloj=True):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/seres?mundo=taberna", json=_ser_tabernero())
    if con_reloj:
        taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T00:00:00"})
    if con_rutina:
        (taller.raiz_mundos / "taberna/seres/tabernero/rutina.json").write_text(
            json.dumps(RUTINA_TABERNA), encoding="utf-8"
        )


def test_vivir_dias_llena_la_cola_y_la_bitacora(taller, monkeypatch):
    from codex import vida

    monkeypatch.setattr(vida, "PROB_ESCALADA", 1.0)   # todo tick sale caliente
    _preparar_taberna_viva(taller)

    r = taller.post("/vida?mundo=taberna", json={"ser_id": "tabernero", "dias": 2, "semilla": 5})
    assert r.status_code == 200
    datos = r.json()
    assert datos["dias_vividos"] == 2
    assert len(datos["pendientes"]) == 6            # 3 ticks × 2 días, todos escalados
    assert set(datos["deltas"]) == {"PF-casa", "oido-fino"}

    # Bitácora: UNA entrada por día vivido, no por tick.
    de_vida = [e for e in taller.get("/bitacora?mundo=taberna").json() if e["tipo"] == "vida"]
    assert len(de_vida) == 2

    # La cola: todos pendientes; marcar uno jugado queda registrado.
    cola = taller.get("/vida/pendientes?mundo=taberna").json()
    assert len(cola) == 6
    assert all(m["estado"] == "pendiente" for m in cola)
    r = taller.post("/vida/pendientes/marcar?mundo=taberna",
                    json={"id": cola[0]["id"], "estado": "jugado"})
    assert r.status_code == 200
    estados = {m["id"]: m["estado"] for m in taller.get("/vida/pendientes?mundo=taberna").json()}
    assert estados[cola[0]["id"]] == "jugado"

    # Marcas inválidas: id inexistente o estado que no es jugado/descartado.
    assert taller.post("/vida/pendientes/marcar?mundo=taberna",
                       json={"id": "no-existe", "estado": "jugado"}).status_code == 400
    assert taller.post("/vida/pendientes/marcar?mundo=taberna",
                       json={"id": cola[1]["id"], "estado": "quemado"}).status_code == 400


def test_los_dias_del_latido_tambien_calman(taller):
    """Los días vividos son del ser: si vivió en paz se calma, aunque el reloj
    del mundo no se haya movido (el latido no lo toca)."""
    _preparar_taberna_viva(taller)
    _con_stress(taller, "tabernero", 6.0)

    r = taller.post("/vida?mundo=taberna",
                    json={"ser_id": "tabernero", "dias": 4, "semilla": 5})

    assert r.json()["stress"] == pytest.approx(4.8)          # 6.0 - 4×0.3
    assert _stress_de(taller, "tabernero") == pytest.approx(4.8)
    # El reloj del mundo NO se movió: los días fueron del ser.
    assert taller.get("/reloj?mundo=taberna").json()["momento"] == "1850-03-01T00:00:00"


def test_vida_valida_mundo_ser_rutina_y_reloj(taller):
    # Mundo inexistente.
    r = taller.post("/vida?mundo=no-existe", json={"ser_id": "tabernero", "dias": 1})
    assert r.status_code == 404

    _preparar_taberna_viva(taller, con_rutina=False, con_reloj=False)

    # El ser_id con ruta se corta antes de tocar disco (mismo criterio que /seres).
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "../fuera", "dias": 1})
    assert r.status_code == 400
    # Ser inexistente.
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "fantasma", "dias": 1})
    assert r.status_code == 404
    # Días para atrás no hay.
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "tabernero", "dias": 0})
    assert r.status_code == 400
    # Sin rutina no late.
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "tabernero", "dias": 1})
    assert r.status_code == 409
    assert "rutina" in r.json()["detail"]
    # Con rutina pero sin hora del mundo, tampoco.
    (taller.raiz_mundos / "taberna/seres/tabernero/rutina.json").write_text(
        json.dumps(RUTINA_TABERNA), encoding="utf-8"
    )
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "tabernero", "dias": 1})
    assert r.status_code == 409
    assert "hora" in r.json()["detail"]
    # Una rutina malformada da 400 legible, no un stacktrace.
    (taller.raiz_mundos / "taberna/seres/tabernero/rutina.json").write_text(
        json.dumps({"plantillas": [{"id": "solo-una", "texto": "poca vida"}]}),
        encoding="utf-8",
    )
    taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T00:00:00"})
    r = taller.post("/vida?mundo=taberna", json={"ser_id": "tabernero", "dias": 1})
    assert r.status_code == 400
    assert "3 y 20" in r.json()["detail"]


# ----- Zona Templates y tests -----

def test_editar_un_template_permitido(taller, tmp_path, monkeypatch):
    import taller.app as modulo_app
    carpeta = tmp_path / "templates"
    carpeta.mkdir()
    (carpeta / "mutacion.txt").write_text("versión vieja $receptor_id", encoding="utf-8")
    monkeypatch.setattr(modulo_app, "CARPETA_TEMPLATES", carpeta)

    assert "vieja" in taller.get("/templates/mutacion").json()["texto"]

    r = taller.put("/templates/mutacion", json={"texto": "versión nueva $receptor_id"})
    assert r.status_code == 200
    assert (carpeta / "mutacion.txt").read_text(encoding="utf-8") == "versión nueva $receptor_id"


def test_solo_los_dos_templates_del_motor(taller):
    assert taller.get("/templates/otro").status_code == 404
    assert taller.put("/templates/passwd", json={"texto": "x"}).status_code == 404


def test_correr_una_suite_de_pytest(taller, tmp_path, monkeypatch):
    import taller.app as modulo_app
    monkeypatch.setattr(modulo_app, "CARPETA_TESTS", tmp_path)
    (tmp_path / "test_trivial.py").write_text(
        "def test_pasa():\n    assert True\n", encoding="utf-8"
    )

    r = taller.post("/tests", json={"ruta": "test_trivial.py"})

    assert r.status_code == 200
    assert r.json()["exito"] is True
    assert "1 passed" in r.json()["salida"]


def test_el_runner_de_tests_no_acepta_flags_ni_rutas_ajenas(taller):
    """pytest EJECUTA el conftest de lo que se le apunte: la ruta va relativa a la
    carpeta de tests del repo y sin flags, o no va."""
    assert taller.post("/tests", json={"ruta": "-p malicioso"}).status_code == 400
    assert taller.post("/tests", json={"ruta": "../../otro/lado"}).status_code == 400
    assert taller.post("/tests", json={"ruta": "/tmp/lo-que-sea"}).status_code == 400


def test_requests_de_otro_origen_se_rechazan(taller):
    """El taller es local y de una persona: una página web ajena no puede operarlo
    (drive-by contra localhost)."""
    r = taller.post("/mundos", json={"nombre": "intruso"},
                    headers={"Origin": "https://malicioso.example"})
    assert r.status_code == 403
    assert taller.get("/mundos").json() == []


# ----- La descarga de stress: el tiempo en paz calma -----

def _con_stress(taller, ser_id, cuanto, mundo="taberna"):
    """Deja al ser con esa barra, por la puerta única."""
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / mundo)
    p.guardar_estado_reglas(ser_id, {"stress": cuanto})
    p.cerrar()


def _stress_de(taller, ser_id, mundo="taberna"):
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / mundo)
    valor = p.leer_estado_reglas(ser_id).get("stress", 0.0)
    p.cerrar()
    return valor


def test_avanzar_el_reloj_descarga_el_stress(taller):
    """El mismo tick que enfría los memes calma a los seres."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 6.0)
    taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T09:00"})

    taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 0, "dias": 4})

    assert _stress_de(taller, "tabernero") == pytest.approx(4.8)   # 6.0 - 4×0.3


def test_fijar_la_hora_no_descarga_el_stress(taller):
    """Fijar es teletransporte autoral, no tiempo vivido: no calma a nadie
    (la misma regla que ya rige para el decaimiento de los memes)."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 6.0)

    taller.post("/reloj?mundo=taberna", json={"momento": "1850-04-01T09:00"})

    assert _stress_de(taller, "tabernero") == 6.0


def test_un_ser_que_nunca_jugo_un_score_no_se_rompe_al_calmarse(taller):
    """El stress vive en la capa de reglas; un ser sin Scores jugados no tiene
    nada registrado, y el paso del tiempo tiene que ser inofensivo para él."""
    _mundo_armado(taller)
    taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T09:00"})

    r = taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 0, "dias": 3})

    assert r.status_code == 200
    assert _stress_de(taller, "tabernero") == 0.0


# ----- El desborde: la cicatriz se propone, no se impone -----

CICATRIZ = json.dumps({
    "escena": "Se quedó callado mucho después de que lo soltaran.",
    "cicatriz": {"meme_id": "lo_que_no_se_grita", "texto": "Gritar no sirve de nada.",
                 "peso_inicial": 2.0, "costo": 10,
                 "justificacion": "no gritó cuando lo arrastraron"},
}, ensure_ascii=False)

# La cicatriz tiene que ser una idea NUEVA para estos tests. Con el encoder por
# defecto todo se parece a todo (similitud 1.0) y el chequeo de duplicado la
# convertiría en un refuerzo del meme que el ser ya tiene: un dato degenerado no
# prueba nada de la calibración (lessons.md, 2026-07-30). Este vector queda por
# debajo del umbral contra cualquiera de los del tabernero, sin importar el orden
# en que corran los tests. Que la cicatriz YA creída llegue como refuerzo lo
# prueba tests/test_trauma.py, con similitudes guionadas.
VECTORES["Gritar no sirve de nada."] = [0.0, 1.0]


def _pedir_cicatriz(taller):
    return taller.post("/trauma/pedir?mundo=taberna", json={"ser_id": "tabernero"})


def test_pedir_la_cicatriz_no_aplica_nada(taller):
    """El corazón del asunto: el ser propone, el autor dispone. Pedir no toca
    ni el memetario ni la barra."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 9.0)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ

    r = _pedir_cicatriz(taller)

    assert r.status_code == 200
    assert "callado" in r.json()["escena"]
    assert r.json()["propuesta"]["meme_id"] == "lo_que_no_se_grita"
    # Nada se aplicó: el meme no existe ni en el estado vivo ni en la semilla.
    assert "lo_que_no_se_grita" not in taller.get(
        "/seres/tabernero/estado?mundo=taberna").json()
    seres = taller.get("/seres?mundo=taberna").json()
    assert all(m["id"] != "lo_que_no_se_grita" for m in seres[0]["memes"])
    assert _stress_de(taller, "tabernero") == 9.0          # la barra sigue llena


def test_pedir_la_cicatriz_sin_estar_desbordado_da_409(taller):
    _mundo_armado(taller)

    r = _pedir_cicatriz(taller)

    assert r.status_code == 409
    assert "desbord" in r.json()["detail"].lower()


def test_la_cicatriz_se_puede_volver_a_pedir(taller):
    """Si se perdió la tarjeta (recargaste la página), el ser sigue desbordado:
    la barra llena ES la marca, no hay estado pendiente que rescatar."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 9.0)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ

    assert _pedir_cicatriz(taller).status_code == 200
    assert _pedir_cicatriz(taller).status_code == 200


def test_si_el_llm_no_da_cicatriz_valida_avisa_y_la_barra_no_se_toca(taller):
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 9.0)
    taller.cliente_llm.respuesta_por_defecto = "no hay json acá"

    r = _pedir_cicatriz(taller)

    assert r.status_code == 422
    assert _stress_de(taller, "tabernero") == 9.0


def test_aprobar_la_cicatriz_la_siembra_y_vacia_la_barra(taller):
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 9.0)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ
    propuesta = _pedir_cicatriz(taller).json()["propuesta"]

    r = taller.post("/trauma/resolver?mundo=taberna", json={
        "ser_id": "tabernero", "decision": "aprobar", "propuesta": propuesta})

    assert r.status_code == 200
    assert r.json()["stress"] == 0.0
    assert _stress_de(taller, "tabernero") == 0.0
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["lo_que_no_se_grita"]["peso"] == 2.0      # sembrado con su peso humilde
    seres = taller.get("/seres?mundo=taberna").json()       # y entró a la SEMILLA
    assert any(m["id"] == "lo_que_no_se_grita" for m in seres[0]["memes"])
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "trauma_aplicada"


def test_rechazar_la_cicatriz_no_siembra_nada_y_deja_la_barra_a_la_mitad(taller):
    """El ser aguantó: no queda cicatriz, pero aguantar tampoco es gratis —
    si no bajara, el desborde volvería a pedir lo mismo en cada escena."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 9.0)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ
    propuesta = _pedir_cicatriz(taller).json()["propuesta"]

    r = taller.post("/trauma/resolver?mundo=taberna", json={
        "ser_id": "tabernero", "decision": "rechazar", "propuesta": propuesta})

    assert r.status_code == 200
    assert r.json()["stress"] == 4.5                       # la mitad del techo (9)
    assert _stress_de(taller, "tabernero") == 4.5
    assert "lo_que_no_se_grita" not in taller.get(
        "/seres/tabernero/estado?mundo=taberna").json()
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "trauma_rechazada"


def test_el_score_avisa_cuando_el_ser_quedo_desbordado(taller):
    """La página tiene que poder mostrar la tarjeta sin ir a buscar nada."""
    _mundo_armado(taller)
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6})
    _con_stress(taller, "tabernero", 7.0)
    taller.cliente_llm.respuesta_por_defecto = "Lo agarran del brazo."
    taller.rng.cargar([2, 2, 2])          # mala consecuencia: carga 2 → 7 + 2 = 9 (techo)

    ev = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores."}).json()
    r = taller.post("/score/tirar?mundo=taberna", json={**ev, "empuje": None}).json()

    assert r["stress"] == 9.0
    assert r["desbordado"] is True


def test_un_score_que_no_llena_la_barra_no_avisa_desborde(taller):
    _mundo_armado(taller)
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6})
    taller.cliente_llm.respuesta_por_defecto = "Escucha y calla."
    taller.rng.cargar([6, 6, 6])                            # limpio: no carga nada

    ev = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores."}).json()
    r = taller.post("/score/tirar?mundo=taberna", json={**ev, "empuje": None}).json()

    assert r["desbordado"] is False


def test_el_template_del_trauma_se_edita_desde_el_taller(taller):
    assert taller.get("/templates/trauma").status_code == 200


def test_la_lista_de_seres_trae_la_barra_para_mostrarla(taller):
    """El diseño pide que la barra esté siempre a la vista: la ficha necesita el
    stress actual y su techo sin pedir nada aparte."""
    _mundo_armado(taller)
    _con_stress(taller, "tabernero", 7.0)

    ser = taller.get("/seres?mundo=taberna").json()[0]

    assert ser["stress"] == 7.0
    assert ser["hoja"]["stress_max"] == 9


# ----- El bias circadiano en las puertas del Taller -----

def _ser_noctambulo(**extra):
    """Dos memes que empatan en todo -mismo peso, misma afinidad- salvo el tipo,
    y mana para UNO solo. Así lo único que puede desempatar es la hora del mundo:
    si el bias no está enchufado, la franja horaria no cambia nada."""
    base = {
        "ser_id": "noctambulo",
        "mana_max": 10,
        "memes": [
            {"id": "PF-guardia", "tipo": "fundacional",
             "texto": "El puerto no se cuida solo.", "peso_inicial": 9.0},
            {"id": "rutina-del-muelle", "tipo": "operativo",
             "texto": "Barrer el muelle antes de que abran.", "peso_inicial": 5.0, "costo": 10},
            {"id": "corazonada-del-agua", "tipo": "experimental",
             "texto": "Algo respira debajo del agua.", "peso_inicial": 5.0, "costo": 10},
        ],
        "hoja": {"stress_max": 9, "acciones": {"acechar": 2}},
    }
    base.update(extra)
    return base


def _puerto(taller):
    taller.post("/mundos", json={"nombre": "puerto"})
    taller.post("/seres?mundo=puerto", json=_ser_noctambulo())


DIA = "1850-03-01T10:00"
NOCHE = "1850-03-01T23:00"


def _memes_del_dialogo(taller, momento):
    taller.post("/reloj?mundo=puerto", json={"momento": momento})
    r = taller.post("/dialogo?mundo=puerto", json={
        "ser_id": "noctambulo", "historial": [], "mensaje": "¿Qué estás mirando?",
    })
    assert r.status_code == 200
    return {m["id"] for m in r.json()["memes_activos"]}


def test_la_hora_del_mundo_inclina_el_cristal_en_el_dialogo(taller):
    """De día pesa lo práctico; de noche, lo exploratorio (codex/bias.py)."""
    _puerto(taller)
    taller.cliente_llm.respuesta_por_defecto = "Nada. El agua."

    assert _memes_del_dialogo(taller, DIA) == {"PF-guardia", "rutina-del-muelle"}
    assert _memes_del_dialogo(taller, NOCHE) == {"PF-guardia", "corazonada-del-agua"}


def test_la_hora_del_mundo_inclina_el_cristal_en_el_score(taller):
    _puerto(taller)
    taller.post("/clocks?mundo=puerto", json={
        "id": "amenaza", "nombre": "La marea sube", "segmentos_total": 6,
    })
    accion = {"ser_id": "noctambulo", "accion": "acechar",
              "descripcion": "Se queda quieto en la punta del muelle, mirando el agua."}

    taller.post("/reloj?mundo=puerto", json={"momento": DIA})
    de_dia = taller.post("/score/evaluar?mundo=puerto", json=accion).json()
    taller.post("/reloj?mundo=puerto", json={"momento": NOCHE})
    de_noche = taller.post("/score/evaluar?mundo=puerto", json=accion).json()

    def ids(evaluado):
        return {m["id"] for m in evaluado["contexto"]["loadout"]["seleccionados"]}

    assert ids(de_dia) == {"PF-guardia", "rutina-del-muelle"}
    assert ids(de_noche) == {"PF-guardia", "corazonada-del-agua"}


def test_la_hora_del_mundo_inclina_el_cristal_al_escuchar(taller):
    """En la transmisión la hora la trae el pedido (el momento de la escena),
    no el reloj guardado: se escucha a la hora en que el emisor habla."""
    import json as _json
    _puerto(taller)
    taller.post("/hechos?mundo=puerto", json={
        "id": "luz-en-la-bahia", "contenido": "Hubo una luz bajo el agua, frente al faro.",
        "momento": "1850-03-01T04:00", "lugar": "la bahía", "testigo": "el_farero",
    })
    taller.cliente_llm.respuesta_por_defecto = _json.dumps({
        "contenido_entendido": "Una luz, debajo del agua.", "memes_resonantes": [],
    }, ensure_ascii=False)

    taller.post("/transmitir?mundo=puerto", json={
        "emisor_id": "el_farero", "receptor_id": "noctambulo",
        "version_id": "luz-en-la-bahia-raiz", "momento": NOCHE,
    })

    estado = taller.get("/seres/noctambulo/estado?mundo=puerto").json()
    assert estado["corazonada-del-agua"]["veces_en_loadout"] == 1
    assert estado["rutina-del-muelle"]["veces_en_loadout"] == 0


# ----- La página -----

def test_la_pagina_se_sirve_en_la_raiz(taller):
    r = taller.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Taller" in r.text
