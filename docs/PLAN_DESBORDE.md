# Plan de implementación — el desborde

> **Para agentes:** usar `superpowers:subagent-driven-development` o
> `superpowers:executing-plans` para ejecutar tarea por tarea. Los pasos usan
> casillas (`- [ ]`) para seguimiento.

**Objetivo:** que la barra de stress mida lo que le pasa al ser, que el tiempo la
descargue, y que al llenarse el ser proponga la cicatriz que le quedó — para que el
autor la apruebe o la rechace.

**Diseño aprobado:** `docs/DISENO_DESBORDE.md`. Este plan no decide nada nuevo; lo
ejecuta.

**Arquitectura:** tres piezas independientes que se pueden verificar por separado. La
carga vive en `codex/blades.py` (donde ya vive el empuje), la descarga en
`codex/decaimiento.py` (donde ya vive el enfriado por tiempo), y la propuesta de cicatriz
en un módulo nuevo `codex/trauma.py` que reusa el esquema y el ciclo de validación del
SPECULUM. El Taller solo abre puertas: no agrega lógica de motor.

**Stack:** Python ≥3.11 · pydantic v2 · FastAPI · pytest. Sin dependencias nuevas.

## Restricciones globales

Valen para TODAS las tareas:

- **El motor manda, el LLM ilustra** (ADR-001). El LLM propone la cicatriz; el motor
  valida y el autor dispone. Nada que venga del modelo entra sin validar.
- **Una sola puerta de escritura**: todo pasa por `codex/persistencia.py`. Ningún módulo
  escribe stress ni pesos por su cuenta.
- **Nada de except-pass**: toda degradación se loguea aunque no rompa (regla 3).
- **Los tests no tocan la red ni gastan tokens** (regla 5): `MockClient` con guion,
  encoder de embeddings inyectable.
- **NO SE COMMITEA NADA.** En este proyecto nada construido se commitea sin el veredicto
  escrito de James. Cada tarea termina con la suite completa en verde, no con un commit.
  El comando es `./venv/bin/pytest`.
- **"Listo" significa suite corrida en verde**, no "debería pasar".
- Si aparece un bug al pasar, deja un test que lo reproduce y una línea en `lessons.md`.

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `codex/blades.py` (modificar) | La carga de stress por categoría de resultado |
| `codex/decaimiento.py` (modificar) | La descarga de stress por día vivido |
| `codex/trauma.py` (crear) | Congelar el desborde, pedir la cicatriz, validarla |
| `templates/trauma.txt` (crear) | El prompt de la cicatriz, editable desde el Taller |
| `taller/app.py` (modificar) | Las puertas: pedir, aprobar, rechazar; y la descarga |
| `taller/index.html` (modificar) | La tarjeta de la cicatriz en la ficha |
| `tests/test_blades.py` (modificar) | Tarea 1 |
| `tests/test_decaimiento.py` (modificar) | Tarea 2 |
| `tests/test_trauma.py` (crear) | Tarea 3 |
| `tests/test_taller.py` (modificar) | Tareas 2 y 4 |

---

## Tarea 1: La barra se llena con lo vivido

**Archivos:**
- Modificar: `codex/blades.py` (constantes al tope, junto a `COSTO_EMPUJE` en la línea 79;
  emisión de efectos en `SistemaBlades.tirar`, alrededor de la línea 195)
- Test: `tests/test_blades.py`

**Interfaces:**
- Consume: `PagarStress(ser_id: str, cantidad: float)` de `codex/reglas.py`, ya existente.
- Produce: la constante `CARGA_POR_CATEGORIA: dict[CategoriaResultado, int]`, que la
  tarea 3 lee para nada — es interna. Lo que sí produce para el resto: `tirar()` ahora
  devuelve `Resolucion.efectos` con un `PagarStress` extra cuando el resultado no es
  limpio.

- [ ] **Paso 1: Escribir los tests que fallan**

En `tests/test_blades.py`, al final. Usan los helpers `_blades(dados=...)`,
`_contexto(...)` y las constantes `CRISTAL_*` que **ya existen** en ese archivo (líneas
30-72): no hay que crear fixtures nuevas.

```python
def test_una_tirada_limpia_no_carga_stress():
    """La barra mide lo que le PASA al ser: un éxito limpio no deja marca."""
    blades = _blades(dados=(6, 6))
    ctx = _contexto(CRISTAL_NEUTRO)

    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    assert r.categoria == CategoriaResultado.LIMPIO
    assert [e for e in r.efectos if isinstance(e, PagarStress)] == []


def test_una_tirada_con_costo_carga_un_punto():
    blades = _blades(dados=(4, 4))
    ctx = _contexto(CRISTAL_NEUTRO)

    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    assert r.categoria == CategoriaResultado.CON_COSTO
    assert PagarStress(ser_id="pescador", cantidad=1) in r.efectos


def test_una_mala_consecuencia_carga_dos_puntos():
    blades = _blades(dados=(2, 3))
    ctx = _contexto(CRISTAL_NEUTRO)

    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx)

    assert r.categoria == CategoriaResultado.MALA_CONSECUENCIA
    assert PagarStress(ser_id="pescador", cantidad=2) in r.efectos


def test_el_empuje_y_el_golpe_se_suman():
    """Empujar cuesta 2 (lo que el autor gasta) y el golpe cuesta 2 (lo que el ser
    vive): una mala consecuencia en tirada empujada cobra las dos cosas."""
    blades = _blades(dados=(2, 3, 1))
    ctx = _contexto(CRISTAL_NEUTRO, stress=0.0)

    r = blades.tirar(blades.evaluar(ACCION, ctx), ctx, empuje=Empuje.DADO_EXTRA)

    total = sum(e.cantidad for e in r.efectos if isinstance(e, PagarStress))
    assert total == 4
```

`ACCION` usa la acción `faenar`, que la hoja del pescador tira con 2 dados; por eso cada
guion de dados trae dos valores (y tres cuando hay dado extra). Manda el más alto.

- [ ] **Paso 2: Correr los tests y verlos fallar**

```
./venv/bin/pytest tests/test_blades.py -k "carga or golpe" -v
```

Esperado: los tres que esperan carga FALLAN (la lista de `PagarStress` viene vacía, o
solo trae el empuje). El de la tirada limpia PASA ya — es el control, y tiene que seguir
verde después.

- [ ] **Paso 3: Escribir el código mínimo**

En `codex/blades.py`, junto a `COSTO_EMPUJE` (línea 79):

```python
COSTO_EMPUJE = 2               # stress que paga cada empuje (uno solo por tirada)
# Lo que le cuesta al SER lo que le pasó, sin que el autor elija pagarlo. Antes la
# barra solo subía por empuje, así que medía cuántas veces el autor apretó el
# acelerador y no lo que el personaje vivió (mismo bug que los pesos en julio).
# Provisionales: se calibran jugando.
CARGA_CON_COSTO = 1
CARGA_MALA_CONSECUENCIA = 2
```

En `SistemaBlades.tirar`, después de decidir la categoría y antes del `return`:

```python
        if categoria == CategoriaResultado.CON_COSTO:
            efectos.append(PagarStress(
                ser_id=evaluacion.accion.ser_id, cantidad=CARGA_CON_COSTO))
        elif categoria == CategoriaResultado.MALA_CONSECUENCIA:
            efectos.append(PagarStress(
                ser_id=evaluacion.accion.ser_id, cantidad=CARGA_MALA_CONSECUENCIA))
```

Ojo: el bloque de `MALA_CONSECUENCIA` que ya existe agrega el `AvanzarClock`. Poné la
carga donde no dupliques la rama; lo más limpio es agregar la carga en un bloque aparte
después de que la categoría ya está decidida.

- [ ] **Paso 4: Correr los tests y verlos pasar**

```
./venv/bin/pytest tests/test_blades.py -v
```

Esperado: PASS, y ningún test viejo de blades roto.

- [ ] **Paso 5: Suite completa**

```
./venv/bin/pytest
```

Esperado: todo verde, **pero van a romper tests viejos, y eso está previsto**. Son dos
familias, y ninguna es un bug:

1. **Tests que asertan la lista de efectos completa.** `test_mala_consecuencia_avanza_el_clock_de_amenaza`
   y `test_en_posicion_desesperada_la_mala_consecuencia_pega_doble` (líneas 124 y 133)
   hacen `assert r.efectos == [AvanzarClock(...)]`. Ahora la lista trae también el
   `PagarStress`. Cambialos a `assert AvanzarClock(...) in r.efectos`, que es lo que
   cada test quiere decir de verdad.
2. **Tests del Taller que asertan el stress resultante.** `test_score_completo_evaluar_tirar_y_efectos`
   espera `stress == 2.0` tras un empuje con mala consecuencia; ahora son 4.0.
   Actualizá el número y dejá un comentario de una línea: el golpe ahora también carga.

Si rompe algún otro test que NO sea de estas dos familias, pará: eso sí sería un
efecto no previsto.

---

## Tarea 2: El tiempo descarga la barra

**Archivos:**
- Modificar: `codex/decaimiento.py` (constante al tope; función nueva al final)
- Modificar: `taller/app.py` (`_enfriar_seres`, línea ~354; y el endpoint `/vida`, ~765)
- Test: `tests/test_decaimiento.py` y `tests/test_taller.py`

**Interfaces:**
- Consume: `Persistencia.leer_estado_reglas(ser_id) -> dict` y
  `Persistencia.guardar_estado_reglas(ser_id, dict)`, ya existentes.
- Produce: `descargar_stress(persistencia: Persistencia, ser_id: str, dias: float) -> float`
  en `codex/decaimiento.py`. Devuelve el stress nuevo. La tarea 4 no la usa; el Taller sí.

- [ ] **Paso 1: Escribir los tests que fallan**

En `tests/test_decaimiento.py`:

```python
def test_el_tiempo_descarga_el_stress(persistencia):
    """Un ser al que dejan en paz se calma: la barra baja con los días vividos."""
    persistencia.guardar_estado_reglas("ermitano", {"stress": 6.0})

    nuevo = descargar_stress(persistencia, "ermitano", dias=8)

    assert nuevo == 4.0                                    # 8 días × 0.25
    assert persistencia.leer_estado_reglas("ermitano")["stress"] == 4.0


def test_la_descarga_nunca_baja_de_cero(persistencia):
    persistencia.guardar_estado_reglas("ermitano", {"stress": 1.0})

    nuevo = descargar_stress(persistencia, "ermitano", dias=90)

    assert nuevo == 0.0


def test_un_mes_tranquilo_vacia_una_barra_llena(persistencia):
    """El criterio de calibración del diseño, escrito como test: si alguien
    cambia la tasa y rompe esto, se entera acá."""
    persistencia.guardar_estado_reglas("ermitano", {"stress": 9.0})

    assert descargar_stress(persistencia, "ermitano", dias=30) == 0.0


def test_un_ser_sin_stress_registrado_no_se_rompe(persistencia):
    assert descargar_stress(persistencia, "nunca_jugo", dias=5) == 0.0
```

Usá la fixture de persistencia que ya usan los tests de ese archivo.

- [ ] **Paso 2: Correr y ver fallar**

```
./venv/bin/pytest tests/test_decaimiento.py -k descarga -v
```

Esperado: FAIL con `NameError: name 'descargar_stress' is not defined` (o error de
importación). Agregá el import al principio del archivo de test.

- [ ] **Paso 3: Escribir el código mínimo**

En `codex/decaimiento.py`, junto a las otras tasas:

```python
TASA_DESCARGA_STRESS = 0.25  # stress que se descarga por día vivido en paz: un mes
                             # tranquilo vacía una barra llena (9). Provisional.
```

Y al final del módulo:

```python
def descargar_stress(persistencia: Persistencia, ser_id: str, dias: float) -> float:
    """El tiempo vivido en paz descarga la barra, con piso en 0.

    A diferencia del peso de los memes (que decae asintóticamente y nunca llega
    al piso), el stress SÍ llega a cero: un ser puede quedar en paz del todo.
    Escribe por la puerta única. Sin vicio todavía, esta es la única válvula."""
    if dias <= 0:
        return persistencia.leer_estado_reglas(ser_id).get("stress", 0.0)
    actual = persistencia.leer_estado_reglas(ser_id).get("stress", 0.0)
    nuevo = max(0.0, actual - TASA_DESCARGA_STRESS * dias)
    if nuevo != actual:
        persistencia.guardar_estado_reglas(ser_id, {"stress": nuevo})
    return nuevo
```

- [ ] **Paso 4: Correr y ver pasar**

```
./venv/bin/pytest tests/test_decaimiento.py -v
```

- [ ] **Paso 5: Enchufarlo en las dos puertas del tiempo — test primero**

En `tests/test_taller.py`, al final de la sección de la zona Probar:

```python
def test_avanzar_el_reloj_descarga_el_stress(taller):
    """El mismo tick que enfría los memes calma a los seres."""
    _mundo_armado(taller)
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.guardar_estado_reglas("tabernero", {"stress": 6.0})
    p.cerrar()
    taller.post("/reloj?mundo=taberna", json={"momento": "1850-03-01T09:00"})

    taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 0, "dias": 4})

    p = Persistencia(taller.raiz_mundos / "taberna")
    assert p.leer_estado_reglas("tabernero")["stress"] == 5.0
    p.cerrar()


def test_fijar_la_hora_no_descarga_el_stress(taller):
    """Fijar es teletransporte autoral, no tiempo vivido: no calma a nadie
    (misma regla que ya rige para el decaimiento de los memes)."""
    _mundo_armado(taller)
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.guardar_estado_reglas("tabernero", {"stress": 6.0})
    p.cerrar()

    taller.post("/reloj?mundo=taberna", json={"momento": "1850-04-01T09:00"})

    p = Persistencia(taller.raiz_mundos / "taberna")
    assert p.leer_estado_reglas("tabernero")["stress"] == 6.0
    p.cerrar()
```

Correr y ver fallar el primero (el segundo pasa ya: es el control).

- [ ] **Paso 6: Enchufarlo**

En `taller/app.py`, dentro de `_enfriar_seres`, junto al `aplicar_decaimiento`:

```python
            aplicar_decaimiento(memetario, p, ciclos=dias)
            descargar_stress(p, carpeta.name, dias)
```

Agregá `descargar_stress` al import de `codex.decaimiento` (línea 29).

En el endpoint `/vida`, después de que `vivir()` termina, descargá los días vividos por
el ser: son tiempo que vivió de verdad. Buscá dónde el endpoint ya tiene
`cuerpo.dias` y agregá `descargar_stress(p, cuerpo.ser_id, cuerpo.dias)`.

- [ ] **Paso 7: Test del latido y suite completa**

Agregá en `tests/test_taller.py`, junto a los otros tests del latido. Usa el helper
`_preparar_taberna_viva`, que **ya existe** en ese archivo (línea 785) y siembra mundo,
ser, reloj y rutina:

```python
def test_los_dias_del_latido_tambien_calman(taller):
    """Los días vividos son del ser: si vivió en paz se calma, aunque el reloj
    del mundo no se haya movido (el latido no lo toca)."""
    _preparar_taberna_viva(taller)
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.guardar_estado_reglas("tabernero", {"stress": 6.0})
    p.cerrar()

    taller.post("/vida?mundo=taberna",
                json={"ser_id": "tabernero", "dias": 4, "semilla": 5})

    p = Persistencia(taller.raiz_mundos / "taberna")
    assert p.leer_estado_reglas("tabernero")["stress"] == 5.0      # 4 días × 0.25
    assert p.leer_momento_mundo() == "1850-03-01T00:00:00"         # el reloj no se movió
    p.cerrar()


def test_un_ser_que_nunca_jugo_un_score_no_se_rompe_al_calmarse(taller):
    """El stress vive en la hoja mecánica; un ser sin Scores jugados no tiene
    nada registrado, y el paso del tiempo tiene que ser inofensivo para él."""
    _preparar_taberna_viva(taller)

    r = taller.post("/reloj/avanzar?mundo=taberna", json={"horas": 0, "dias": 3})

    assert r.status_code == 200
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    assert p.leer_estado_reglas("tabernero").get("stress", 0.0) == 0.0
    p.cerrar()
```

```
./venv/bin/pytest
```

Esperado: todo verde.

---

## Tarea 3: El motor congela el desborde y pide la cicatriz

**Archivos:**
- Crear: `codex/trauma.py`
- Crear: `templates/trauma.txt`
- Crear: `tests/test_trauma.py`

**Interfaces:**
- Consume: `PropuestaExperimental`, `PropuestaAjuste`, `Propuesta`,
  `PESO_MAX_EXPERIMENTAL`, `INTENTOS` de `codex/speculum.py`; `ClienteLLM`, `ErrorLLM`
  de `codex/llm`; `Embeddings.similitud(a, b) -> float`; `Ser` de `codex/modelos.py`.
- Produce, para la tarea 4:
  - `class Cicatriz(BaseModel)` con `escena: str` y `propuesta: Propuesta`.
  - `desbordado(estado_reglas: dict, stress_max: float) -> bool`
  - `pedir_cicatriz(ser: Ser, situacion: SituacionDesborde, cliente: ClienteLLM, embeddings: Embeddings) -> tuple[Cicatriz | None, bool]`
    — devuelve la cicatriz y si hubo reintento; `None` si el LLM no dio nada válido.
  - `class SituacionDesborde(BaseModel)` con `accion: str`, `descripcion: str`,
    `categoria: str`, `posicion: str`, `narracion: str`, `memes_movilizados: list[str]`,
    `tensiones: list[str]`.
- `UMBRAL_DUPLICADO = 0.80` — por encima de eso, la cicatriz propuesta se considera
  "ya la tiene" y la propuesta se convierte en refuerzo.

- [ ] **Paso 1: Escribir el template**

Creá `templates/trauma.txt` con placeholders de `string.Template`. Mirá
`templates/speculum.txt` para el tono y el formato de salida JSON antes de escribirlo.
Requisitos duros del template:

- Le habla al ser en segunda persona, como el speculum.
- Muestra los memes del ser **con su id**, porque le vamos a pedir un id (esto ya nos
  costó un bug: ver `lessons.md`, 2026-07-30).
- Pide un único bloque JSON con dos claves: `escena` (un párrafo breve, en tercera
  persona, donde el ser absorbe el golpe — sin explicar la mecánica, sin nombrar el
  stress) y `cicatriz` (un objeto con `meme_id`, `texto`, `peso_inicial`, `costo`,
  `justificacion`).
- Dice el tope: `peso_inicial` no puede pasar de `$peso_max_experimental`.
- Placeholders: `$ser_id`, `$pf`, `$memes`, `$situacion`, `$peso_max_experimental`.

- [ ] **Paso 2: Escribir los tests que fallan**

Creá `tests/test_trauma.py`:

```python
"""Tests del desborde (docs/DISENO_DESBORDE.md). Sin red ni tokens (regla 5)."""

import json

import numpy as np
import pytest

from codex.llm import ErrorLLM, MockClient
from codex.trauma import (
    Cicatriz,
    SituacionDesborde,
    desbordado,
    pedir_cicatriz,
)

SITUACION = SituacionDesborde(
    accion="acechar",
    descripcion="Se queda quieto mirando el agua mientras los otros huyen.",
    categoria="mala_consecuencia",
    posicion="desesperada",
    narracion="Lo agarran del brazo y lo arrastran. No grita.",
    memes_movilizados=["la_vigilancia_como_escudo"],
    tensiones=["«el olvido» ⇄ «conozco esta tierra»"],
)


def _respuesta(meme_id="lo_que_no_se_grita", texto="Gritar no sirve de nada.", peso=2.0):
    return json.dumps({
        "escena": "Se quedó callado mucho después de que lo soltaran.",
        "cicatriz": {"meme_id": meme_id, "texto": texto, "peso_inicial": peso,
                     "costo": 10, "justificacion": "no gritó cuando lo arrastraron"},
    }, ensure_ascii=False)


def test_la_barra_llena_es_desborde():
    assert desbordado({"stress": 9.0}, stress_max=9) is True
    assert desbordado({"stress": 8.5}, stress_max=9) is False
    assert desbordado({}, stress_max=9) is False


def test_la_cicatriz_llega_con_su_escena(ser_de_prueba, embeddings_falsos):
    cliente = MockClient(respuestas=[_respuesta()])

    cicatriz, reintento = pedir_cicatriz(ser_de_prueba, SITUACION, cliente, embeddings_falsos)

    assert reintento is False
    assert "callado" in cicatriz.escena
    assert cicatriz.propuesta.tipo == "proponer_experimental"
    assert cicatriz.propuesta.meme_id == "lo_que_no_se_grita"
    assert cicatriz.propuesta.peso_inicial == 2.0


def test_una_cicatriz_que_el_ser_ya_tiene_llega_como_refuerzo(ser_de_prueba, embeddings_falsos):
    """Si la herida propuesta se parece a un meme que ya tiene, no se inyecta una
    variante nueva: se refuerza la que ya está (el ser no junta cinco versiones
    de la misma cicatriz)."""
    cliente = MockClient(respuestas=[_respuesta(texto="La vigilancia me protege.")])

    cicatriz, _ = pedir_cicatriz(ser_de_prueba, SITUACION, cliente, embeddings_falsos)

    assert cicatriz.propuesta.tipo == "ajustar_peso"
    assert cicatriz.propuesta.meme_id == "la_vigilancia_como_escudo"
    assert cicatriz.propuesta.delta > 0


def test_una_propuesta_invalida_se_reintenta_una_vez(ser_de_prueba, embeddings_falsos):
    cliente = MockClient(respuestas=["no hay json acá", _respuesta()])

    cicatriz, reintento = pedir_cicatriz(ser_de_prueba, SITUACION, cliente, embeddings_falsos)

    assert reintento is True
    assert cicatriz is not None


def test_si_el_llm_no_da_nada_valido_no_hay_cicatriz(ser_de_prueba, embeddings_falsos):
    cliente = MockClient(respuesta_por_defecto="nunca json")

    cicatriz, _ = pedir_cicatriz(ser_de_prueba, SITUACION, cliente, embeddings_falsos)

    assert cicatriz is None


def test_si_el_llm_se_cae_degrada_con_aviso(ser_de_prueba, embeddings_falsos, caplog):
    """Regla 3: se loguea, no se traga en silencio."""
    class Caido:
        def responder(self, prompt):
            raise ErrorLLM("sin red")

    cicatriz, _ = pedir_cicatriz(ser_de_prueba, SITUACION, Caido(), embeddings_falsos)

    assert cicatriz is None
    assert "desborde" in caplog.text.lower()


def test_el_prompt_muestra_los_ids_de_los_memes(ser_de_prueba, embeddings_falsos):
    """Si le pedimos un id, se lo mostramos (lessons.md, 2026-07-30)."""
    cliente = MockClient(respuestas=[_respuesta()])

    pedir_cicatriz(ser_de_prueba, SITUACION, cliente, embeddings_falsos)

    assert "la_vigilancia_como_escudo" in cliente.llamadas[0]
    assert "Se queda quieto mirando el agua" in cliente.llamadas[0]
```

Y las dos fixtures, en el mismo archivo:

```python
@pytest.fixture()
def ser_de_prueba():
    from codex.modelos import Meme, Ser
    return Ser(
        ser_id="el_vigilante",
        mana_max=40,
        memes=[
            Meme(id="PF-nadie-mira", tipo="fundacional",
                 texto="Nadie mira de verdad.", peso_inicial=9.0),
            Meme(id="la_vigilancia_como_escudo", tipo="operativo",
                 texto="Si miro bien, no me agarran.", peso_inicial=6.0, costo=20),
        ],
    )


@pytest.fixture()
def embeddings_falsos():
    """Encoder guionado (regla 5): 'La vigilancia me protege.' es casi idéntico al
    meme que el ser ya tiene; cualquier otro texto es ortogonal a todo."""
    class Falsos:
        disponible = True
        def similitud(self, a, b):
            pareja = {"La vigilancia me protege.", "Si miro bien, no me agarran."}
            return 0.95 if {a, b} == pareja else 0.1
    return Falsos()
```

- [ ] **Paso 3: Correr y ver fallar**

```
./venv/bin/pytest tests/test_trauma.py -v
```

Esperado: FAIL en la importación (`No module named 'codex.trauma'`). Ese es el fallo
correcto para arrancar.

- [ ] **Paso 4: Escribir `codex/trauma.py`**

El módulo, con docstring que diga qué regla dura encarna (la 1: el LLM propone, el motor
valida y el autor dispone). Estructura:

```python
"""El desborde: cuando la barra de stress se llena, el ser propone la cicatriz.

Encarna la regla 1 (el motor manda, el LLM ilustra): el modelo escribe la escena
y sugiere el meme, y el motor valida el esquema, recorta el peso y chequea que no
sea una herida que el ser ya tiene. Nada se aplica acá — el autor dispone, como en
el SPECULUM (docs/DISENO_DESBORDE.md).
"""
```

Piezas, en orden:

1. `SituacionDesborde(BaseModel)` con los campos declarados arriba, y un método
   `texto()` que la convierte en el bloque legible que entra al prompt.
2. `Cicatriz(BaseModel)` con `escena: str = Field(min_length=1)` y `propuesta: Propuesta`.
3. `desbordado(estado_reglas, stress_max)` — una línea: `estado_reglas.get("stress", 0.0) >= stress_max`.
4. `armar_prompt(ser, situacion)` — `Template(...).substitute(...)`, con los memes
   listados como `- «texto» [id: xxx]` (copiá el formato de `consultar_trayectoria` en
   `codex/speculum.py`, que ya lo hace bien).
5. `_parsear(cruda, ser, embeddings)` — extrae el primer bloque JSON (`cruda.find("{")` /
   `cruda.rfind("}")`, igual que `_parsear_mirada`), valida `escena`, construye la
   `PropuestaExperimental`, y **antes de devolverla** corre el chequeo de duplicado:

```python
def _duplicado(texto: str, ser: Ser, embeddings) -> str | None:
    """El id del meme que ya dice casi lo mismo, o None."""
    for m in ser.memes:
        if embeddings.similitud(texto, m.texto) >= UMBRAL_DUPLICADO:
            return m.id
    return None
```

Si hay duplicado, en vez de la experimental se devuelve
`PropuestaAjuste(tipo="ajustar_peso", meme_id=<el duplicado>, delta=DELTA_CICATRIZ, justificacion=...)`
con `DELTA_CICATRIZ = 1.0` como constante del módulo. Ojo: si el duplicado es una PF,
`validar_contra_ser` del speculum la rechaza (las PF son intocables) — en ese caso
devolvé la experimental original, y logueá que la cicatriz rozaba una piedra.

6. `pedir_cicatriz(...)` — el ciclo validar-reintentar-degradar, calcado de `mirarse` en
   `codex/speculum.py` (líneas ~270 en adelante): `INTENTOS` vueltas, la segunda con el
   error anterior agregado al prompt, `except ErrorLLM` que loguea con
   `logger.warning("El desborde de %s no pudo pedir cicatriz: %s", ...)` y devuelve
   `(None, reintento)`. Leé `mirarse` antes de escribir esto y seguí su forma.

- [ ] **Paso 5: Correr y ver pasar**

```
./venv/bin/pytest tests/test_trauma.py -v
```

- [ ] **Paso 6: Suite completa**

```
./venv/bin/pytest
```

---

## Tarea 4: Las puertas del Taller

**Archivos:**
- Modificar: `taller/app.py` (cuerpos de request cerca de la línea 200; `/score/tirar`
  ~703; endpoints nuevos después de los del speculum; `TEMPLATES_EDITABLES` línea 70)
- Test: `tests/test_taller.py`

**Interfaces:**
- Consume: todo lo que produjo la tarea 3.
- Produce:
  - `POST /score/tirar` agrega `"desbordado": bool` a su respuesta.
  - `POST /trauma/pedir` `{ser_id}` → `{"escena": str, "propuesta": {...}}` o 409 si el
    ser no está desbordado, o 422 si el LLM no dio nada válido.
  - `POST /trauma/resolver` `{ser_id, decision: "aprobar"|"rechazar", propuesta}` →
    `{"ok": True, "stress": float, "efecto": {...}}`.

- [ ] **Paso 1: Escribir los tests que fallan**

En `tests/test_taller.py`, sección nueva `# ----- El desborde -----`:

```python
def _desbordar(taller, ser_id="tabernero"):
    """Deja al ser con la barra en el techo, por la puerta única."""
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.guardar_estado_reglas(ser_id, {"stress": 9.0})
    p.cerrar()


CICATRIZ = json.dumps({
    "escena": "Se quedó callado mucho después de que lo soltaran.",
    "cicatriz": {"meme_id": "lo_que_no_se_grita", "texto": "Gritar no sirve de nada.",
                 "peso_inicial": 2.0, "costo": 10,
                 "justificacion": "no gritó cuando lo arrastraron"},
}, ensure_ascii=False)


def test_pedir_la_cicatriz_no_aplica_nada(taller):
    _mundo_armado(taller)
    _desbordar(taller)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ

    r = taller.post("/trauma/pedir?mundo=taberna", json={"ser_id": "tabernero"})

    assert r.status_code == 200
    assert "callado" in r.json()["escena"]
    assert r.json()["propuesta"]["meme_id"] == "lo_que_no_se_grita"
    # Nada se aplicó: el meme no existe todavía y la barra sigue llena.
    assert "lo_que_no_se_grita" not in taller.get(
        "/seres/tabernero/estado?mundo=taberna").json()
    seres = taller.get("/seres?mundo=taberna").json()
    assert all(m["id"] != "lo_que_no_se_grita" for m in seres[0]["memes"])


def test_pedir_la_cicatriz_sin_estar_desbordado_da_409(taller):
    _mundo_armado(taller)

    r = taller.post("/trauma/pedir?mundo=taberna", json={"ser_id": "tabernero"})

    assert r.status_code == 409
    assert "desbord" in r.json()["detail"].lower()


def test_aprobar_la_cicatriz_la_siembra_y_vacia_la_barra(taller):
    _mundo_armado(taller)
    _desbordar(taller)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ
    propuesta = taller.post("/trauma/pedir?mundo=taberna",
                            json={"ser_id": "tabernero"}).json()["propuesta"]

    r = taller.post("/trauma/resolver?mundo=taberna", json={
        "ser_id": "tabernero", "decision": "aprobar", "propuesta": propuesta})

    assert r.status_code == 200
    assert r.json()["stress"] == 0.0
    estado = taller.get("/seres/tabernero/estado?mundo=taberna").json()
    assert estado["lo_que_no_se_grita"]["peso"] == 2.0
    entradas = taller.get("/bitacora?mundo=taberna").json()
    assert entradas[0]["tipo"] == "trauma_aplicada"


def test_rechazar_la_cicatriz_no_siembra_nada_y_deja_la_barra_a_la_mitad(taller):
    """El ser aguantó: no queda cicatriz, pero aguantar tampoco es gratis."""
    _mundo_armado(taller)
    _desbordar(taller)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ
    propuesta = taller.post("/trauma/pedir?mundo=taberna",
                            json={"ser_id": "tabernero"}).json()["propuesta"]

    r = taller.post("/trauma/resolver?mundo=taberna", json={
        "ser_id": "tabernero", "decision": "rechazar", "propuesta": propuesta})

    assert r.status_code == 200
    assert r.json()["stress"] == 4.5
    assert "lo_que_no_se_grita" not in taller.get(
        "/seres/tabernero/estado?mundo=taberna").json()


def test_la_cicatriz_se_puede_volver_a_pedir(taller):
    """Si se perdió la tarjeta, el ser sigue desbordado y se pide de nuevo."""
    _mundo_armado(taller)
    _desbordar(taller)
    taller.cliente_llm.respuesta_por_defecto = CICATRIZ

    assert taller.post("/trauma/pedir?mundo=taberna",
                       json={"ser_id": "tabernero"}).status_code == 200
    assert taller.post("/trauma/pedir?mundo=taberna",
                       json={"ser_id": "tabernero"}).status_code == 200


def test_si_el_llm_no_da_cicatriz_valida_avisa_y_la_barra_no_se_toca(taller):
    _mundo_armado(taller)
    _desbordar(taller)
    taller.cliente_llm.respuesta_por_defecto = "no hay json acá"

    r = taller.post("/trauma/pedir?mundo=taberna", json={"ser_id": "tabernero"})

    assert r.status_code == 422
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    assert p.leer_estado_reglas("tabernero")["stress"] == 9.0
    p.cerrar()


def test_el_score_avisa_cuando_el_ser_quedo_desbordado(taller):
    """La página tiene que poder mostrar la tarjeta sin ir a buscar nada."""
    _mundo_armado(taller)
    taller.post("/clocks?mundo=taberna", json={
        "id": "amenaza", "nombre": "El mar se enturbia", "segmentos_total": 6})
    from codex.persistencia import Persistencia
    p = Persistencia(taller.raiz_mundos / "taberna")
    p.guardar_estado_reglas("tabernero", {"stress": 8.0})
    p.cerrar()
    taller.cliente_llm.respuesta_por_defecto = "Lo agarran del brazo."
    taller.rng.cargar([2, 2, 2, 2])       # mala consecuencia: carga 2 → llega a 9 (techo)

    ev = taller.post("/score/evaluar?mundo=taberna", json={
        "ser_id": "tabernero", "accion": "escuchar",
        "descripcion": "Quedarse detrás de la barra oyendo a los pescadores."}).json()
    r = taller.post("/score/tirar?mundo=taberna", json={**ev, "empuje": None})

    assert r.json()["desbordado"] is True
    assert r.json()["stress"] == 9.0
```

Nota sobre el último test: cargá los dados mirando cómo lo hacen los tests de Score que
ya existen (`test_score_completo_evaluar_tirar_y_efectos`), y ajustá la cantidad de dados
a la acción elegida. Si `stress_max` del tabernero no es 9, ajustá los números.

- [ ] **Paso 2: Correr y ver fallar**

```
./venv/bin/pytest tests/test_taller.py -k "cicatriz or desbord" -v
```

Esperado: 404 en los endpoints que no existen, y `KeyError: 'desbordado'` en el último.

- [ ] **Paso 3: Escribir los cuerpos de request**

En `taller/app.py`, junto a los otros `Cuerpo*`:

```python
class CuerpoTrauma(BaseModel):
    """Pedirle la cicatriz a un ser desbordado."""

    ser_id: str


class CuerpoResolverTrauma(BaseModel):
    """El autor dispone: aprueba la cicatriz o el ser aguanta."""

    ser_id: str
    decision: Literal["aprobar", "rechazar"]
    propuesta: Propuesta
```

`Literal` ya se importa en el proyecto (`codex/modelos.py` lo usa); agregá
`from typing import Literal` si no está en `taller/app.py`.

- [ ] **Paso 4: Escribir los endpoints**

Después de los del speculum. `POST /trauma/pedir`:

1. Cargar el ser (404 si no existe) y su hoja mecánica (`p.cargar_hoja_reglas`).
2. `if not desbordado(p.leer_estado_reglas(ser_id), hoja.stress_max): raise HTTPException(409, "Ese ser no está desbordado: la barra no llegó al techo.")`
3. Armar la `SituacionDesborde` desde la última entrada de Score del ser en la bitácora
   (`bitacora.leer(p.carpeta)`, filtrando `tipo == "score"` y `ser == ser_id`). Si no hay
   ninguna, armala con la descripción vacía y logueá el hueco: un ser puede haber
   quedado desbordado por un stress puesto a mano.
4. `cicatriz, reintento = pedir_cicatriz(ser, situacion, _cliente(), _embeddings(p))`
5. `if cicatriz is None: raise HTTPException(422, "El desborde no devolvió una cicatriz válida: probá de nuevo o ajustá el template.")` (mismo mensaje y forma que `/speculum/mirar`).
6. Bitácora tipo `trauma`, con la escena en `salida` y la propuesta en `terminos`.
7. Devolver `{"escena": ..., "propuesta": ...}`.

`POST /trauma/resolver`:

1. Cargar ser y hoja; 404 si no existe.
2. Si `decision == "rechazar"`: `nuevo = hoja.stress_max / 2`, guardar por la puerta
   única, bitácora tipo `trauma_rechazada`, devolver `{"ok": True, "stress": nuevo, "efecto": {}}`.
   No se toca ningún meme.
3. Si `decision == "aprobar"`: aplicar la propuesta **exactamente como
   `/speculum/aplicar`** (revalidar con `validar_contra_ser`, y las dos ramas
   `ajustar_peso` / `proponer_experimental` con su escritura de `ser.json` y su
   `Memetario(ser, p)`), después `p.guardar_estado_reglas(ser_id, {"stress": 0.0})`,
   bitácora tipo `trauma_aplicada`, y devolver `{"ok": True, "stress": 0.0, "efecto": ...}`.

**Antes de escribir el punto 3, leé `/speculum/aplicar` (línea ~598) entero.** Las dos
ramas son idénticas a las que necesitás. Si al escribirlo ves que estás copiando quince
líneas, extraé la aplicación de una propuesta a una función en `taller/app.py` que ambos
endpoints usen — pero solo si sale limpio; duplicar quince líneas legibles es mejor que
una abstracción forzada.

- [ ] **Paso 5: El aviso en `/score/tirar`**

En el `return` de `/score/tirar`, agregá:

```python
            "desbordado": desbordado(p.leer_estado_reglas(ser_id), blades.hojas[ser_id].stress_max),
```

Verificá cómo se accede a la hoja del ser desde el endpoint (`_blades(p)` arma el
sistema); si `hojas` no es accesible así, usá `p.cargar_hoja_reglas(ser_id).stress_max`.

- [ ] **Paso 6: El template a la lista de editables**

En `TEMPLATES_EDITABLES` (línea 70): `"trauma": "trauma.txt",`. Agregá un test:

```python
def test_el_template_del_trauma_se_edita_desde_el_taller(taller):
    assert taller.get("/templates/trauma").status_code == 200
```

- [ ] **Paso 7: Correr y ver pasar, después suite completa**

```
./venv/bin/pytest tests/test_taller.py -v
./venv/bin/pytest
```

---

## Tarea 5: La tarjeta en la ficha

**Archivos:**
- Modificar: `taller/index.html`

**Interfaces:**
- Consume: `POST /trauma/pedir`, `POST /trauma/resolver`, y el campo `desbordado` de
  `/score/tirar`.

No hay tests automáticos: la página es una vista fina y el proyecto no la testea
(está dicho en el docstring de `tests/test_taller.py`). Se verifica a mano.

- [ ] **Paso 1: Mirar cómo lo hace el espejo**

Buscá en `taller/index.html` el botón «Que se mire» y las tarjetas Aprobar/Rechazar del
SPECULUM. La tarjeta de la cicatriz es la misma forma con otro disparador y otro texto.
Copiá el patrón; no inventes uno nuevo.

- [ ] **Paso 2: La barra de stress visible en la ficha**

Si la ficha ya muestra el stress, marcá visualmente cuando llegó al techo. Si no lo
muestra, agregalo: el diseño dice que la barra tiene que estar siempre a la vista.

- [ ] **Paso 3: El botón y la tarjeta**

- En la ficha de un ser desbordado, un botón: **«Se desbordó — que aparezca la cicatriz»**.
- Al responder, mostrar **primero la escena** (es lo que se lee) y debajo la cicatriz
  propuesta con su justificación.
- Dos botones: **Aprobar** (llama a `/trauma/resolver` con `aprobar`) y **Aguantó**
  (llama con `rechazar`). Después de cualquiera de los dos, refrescar el estado del ser.
- Si `/score/tirar` devolvió `desbordado: true`, mostrar el aviso ahí mismo, sin obligar
  a ir a la ficha.

- [ ] **Paso 4: Verificación a mano**

```
./venv/bin/python taller/servidor.py
```

Sobre una COPIA del mundo `prueba` (no sobre el mundo de James), con Gemini real:
desbordar un ser a mano desde el modo editar, pedir la cicatriz, leer la escena, aprobar,
verificar que el meme quedó sembrado y la barra en cero.

- [ ] **Paso 5: Suite completa**

```
./venv/bin/pytest
```

---

## Al terminar

1. Correr `./venv/bin/pytest` una última vez y anotar el número de tests en verde.
2. Escribir la guía de veredicto para James en `test manuales/`, con el formato de las
   que ya existen (pasos concretos, criterio de éxito, espacio de firma). El criterio de
   éxito de esta mejora es literario y es suyo: **¿la escena de la cicatriz se lee como
   una herida, o como un debuff con prosa?**
3. **No commitear.** Todo queda esperando su veredicto escrito.
