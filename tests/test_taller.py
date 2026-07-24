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
    app = crear_app(raiz_mundos=raiz, cliente_llm=cliente, encoder=_encoder, rng=rng)
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

def test_dialogo_responde_y_no_toca_pesos_ni_activaciones(taller):
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

    # Exploración, no transmisión: el peso vivo no se mueve.
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["oido-fino"]["peso"] == 6.0
    assert estado["oido-fino"]["veces_movilizado"] == 0

    # Pero sí queda en la bitácora, para comparar intentos.
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
    assert res["stress"] == 2.0                            # pagó el empuje
    assert res["clock"]["segmentos_actuales"] == 1         # la amenaza avanzó

    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "score"


def test_los_clocks_se_listan(taller):
    taller.post("/mundos", json={"nombre": "taberna"})
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6,
    })
    clocks = taller.get("/clocks?mundo=taberna").json()
    assert clocks[0]["id"] == "amenaza" and clocks[0]["estado"] == "activo"


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


# ----- La página -----

def test_la_pagina_se_sirve_en_la_raiz(taller):
    r = taller.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Taller" in r.text
