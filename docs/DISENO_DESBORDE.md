# Diseño — el desborde: cuando un ser se rompe y le queda una cicatriz

Fecha: 2026-08-04. Decidido con James en sesión, sobre el hallazgo 2 del
`MAPA_INTEGRACION_2026-08.md`: el stress sube y nunca baja, y al llegar al techo no
pasa nada — solo se apaga la posibilidad de empujar.

El arco completo ya estaba diseñado en
`.claude/skills/codex-fragmentum-blades/references/stress-y-trauma.md` y
`vicios-y-downtime.md`. Este documento no lo reinventa: elige **el corte mínimo que se
puede construir hoy** y nombra lo que queda afuera.

## El problema, en una frase

El stress hoy mide cuántas veces el autor apretó el acelerador, no lo que le pasó al
ser. Es el mismo bug que en julio hacía que los pesos midieran la atención de James en
vez de la vida del personaje.

**La evidencia:** de los 35 Scores jugados en el mundo `prueba`, 14 terminaron con costo
y 4 en mala consecuencia. Ninguno de esos 18 golpes le cargó nada a nadie. Lo único que
llenó la barra fueron los empujes voluntarios, y así los cuatro seres llegaron a 6, 6, 8
y 2 después de 35 escenas. A ese ritmo el desborde sería un evento cada cuarenta y pico
de Scores; el diseño apunta a uno cada cinco o diez.

## Las tres decisiones de James

1. **El trauma se propone, no se impone.** Cae como tarjeta en la ficha, se aprueba o se
   rechaza — el mismo ritual del SPECULUM. El autor dispone (ADR-001).
2. **Las malas consecuencias cargan la barra.** El ser paga por lo que vivió, no por lo
   que el autor decidió gastar. (Descartado por ahora: el "resistir" de Blades canónico,
   donde el autor paga stress para atenuar un golpe.)
3. **El tiempo del mundo la descarga.** No hay vicio: su mitad distintiva —visitar la
   taberna y llevarse un rumor de esa celda— depende de la cartografía, que no tiene una
   línea de código.

---

## Las cuatro piezas

### 1. La barra se llena con lo vivido

En `codex/blades.py`, junto a `COSTO_EMPUJE`, entran dos constantes nuevas: el stress
que cobra cada categoría de resultado.

| Resultado | Carga |
|---|---|
| `limpio` | 0 |
| `con_costo` | 1 |
| `mala_consecuencia` | 2 |

La resolución las emite como `PagarStress` igual que el empuje, así que viajan por la
maquinaria de efectos que ya existe y se aplican por la puerta única. Se acumulan con el
empuje: una mala consecuencia en una tirada empujada cobra 2 + 2.

Contra los 35 Scores ya jugados, esto habría repartido 22 puntos además de los empujes.

### 2. El tiempo la descarga

`POST /reloj/avanzar` ya enfría los memes de todos los seres en el mismo tick
(`_enfriar_seres`). Ahí mismo se descarga stress, con una tasa por día calibrada para
que **un mes tranquilo vacíe una barra llena**: 30 días × 0.3 = 9, el techo. Con piso
en 0 — a diferencia del peso de un meme, el stress sí llega a cero.

Dos decisiones tomadas, vetables:

- **Fijar** la hora NO descarga. Es teletransporte autoral, no tiempo vivido — la misma
  regla que ya rige para el decaimiento de memes desde el paso 1.
- Los días del **latido** (`POST /vida`) SÍ descargan, a la misma tasa. Son tiempo que el
  ser vivió de verdad.

### 3. Al llenarse, el ser propone su cicatriz

Cuando aplicar los efectos de una tirada deja el stress en el techo de la hoja
(`stress_max`, hoy 9), el motor congela la situación y pide una propuesta.

**Lo que se congela y entra al prompt:** la acción declarada, su descripción, la posición
y el efecto, la categoría del resultado, la narración de la escena, los memes que se
movilizaron, y la grieta que estuviera abierta.

**Lo que el LLM devuelve, en una sola llamada:**

- **La escena de la cicatriz**: un párrafo breve donde el ser absorbe el golpe. Es lo
  único de todo el sistema que se lee, y es lo que James va a juzgar.
- **La cicatriz**: un meme experimental con id, texto, peso inicial bajo, costo y
  justificación.

**Validación, antes de mostrar nada:**

- El esquema reusa `PropuestaExperimental` de `codex/speculum.py`, que ya impone peso
  ≤ 3.0, ids en minúsculas y justificación no vacía.
- Ciclo validar-reintentar-degradar, el mismo patrón de la derivación y el espejo.
- **Chequeo de duplicado por similitud semántica**: si la cicatriz propuesta se parece a
  un meme que el ser ya tiene, la propuesta cambia a *reforzar ese* en vez de inyectar
  uno nuevo. Lo pide el diseño original y evita que el ser junte cinco variantes de la
  misma herida.

**Nada se aplica solo.** La propuesta queda en la bitácora (tipo `trauma`) y viaja a la
ficha del Taller como tarjeta Aprobar / Rechazar, igual que el espejo.

### 4. Aprobar y rechazar

- **Aprobar**: el meme entra a la semilla y se siembra (el camino que
  `POST /speculum/aplicar` ya recorre para un experimental), y **la barra vuelve a cero**.
- **Rechazar**: el ser aguantó. La barra baja **a la mitad del techo** (con techo 9,
  queda en 4.5). Así no queda trabado pidiendo lo mismo en cada escena, pero aguantar
  tampoco sale gratis.

**Si la tarjeta se pierde** (recargaste la página, cerraste sin decidir), no se pierde el
desborde: el ser sigue con la barra en el techo, y eso mismo es la marca. La ficha lo
muestra desbordado y ofrece pedir la cicatriz de nuevo, como el botón «que se mire» del
espejo. Cuesta una llamada al LLM cada vez y devuelve una propuesta nueva — no hay estado
pendiente que administrar ni tarjeta que rescatar.

---

## Lo que queda explícitamente afuera

Nombrado para que se sepa que se decidió, no que se olvidó:

- **El ascenso** de la cicatriz a meme operativo permanente tras N activaciones.
- **La crisis biográfica**: que una cicatriz dominante llegue a cambiar una piedra
  fundacional. Necesita meses de juego acumulado; hoy el ser más vivido del mundo tiene
  16 movilizaciones.
- **Las reapariciones**: palabras gatillo, lugares gatillo, sueños recurrentes.
- **El vicio y el downtime**: la mitad que los hace distintos necesita la cartografía.

---

## Qué se toca

- `codex/blades.py` — las dos constantes de carga y los `PagarStress` por categoría.
- `codex/trauma.py` (nuevo) — congelar la situación, armar el prompt, validar la
  propuesta, chequear el duplicado por similitud. Vive pegado al memetario, no aislado.
- `templates/trauma.txt` (nuevo) — editable desde el Taller, como los demás.
- `codex/decaimiento.py` — la descarga de stress por día.
- `taller/app.py` — la propuesta viaja en la respuesta de `/score/tirar`; una puerta para
  aprobarla o rechazarla; la descarga en `/reloj/avanzar` y en `/vida`.
- `taller/index.html` — la tarjeta de la cicatriz en la ficha.

## Cómo se verifica

Con TDD, un test por comportamiento, todos sin red ni tokens (LLM mock con guion):

1. Una tirada limpia no carga stress; una con costo carga 1; una mala carga 2.
2. Una mala consecuencia en tirada empujada carga las dos cosas.
3. Avanzar el reloj N días descarga stress y nunca baja de 0.
4. Fijar la hora no descarga.
5. Llegar al techo produce una propuesta de cicatriz y **no la aplica**.
6. La propuesta que duplica un meme existente llega como refuerzo, no como inyección.
7. Aprobar siembra el meme y deja la barra en cero.
8. Rechazar no siembra nada y deja la barra a la mitad.
9. Si el LLM cae, el desborde degrada con aviso visible (regla 3) y la barra queda como
   estaba: el trauma no ocurrió, y se puede volver a pedir.
10. Un ser desbordado que perdió su tarjeta puede volver a pedir la cicatriz, y la barra
    sigue en el techo hasta que resuelva.
11. Un ser sin hoja mecánica no juega Scores y por lo tanto nunca se desborda: la
    descarga por tiempo no le rompe nada.

## Las perillas provisionales

Todas al tope de su módulo, para calibrar jugando:

- Carga por categoría: 1 y 2.
- Descarga por día: 0.3 (sale del criterio "un mes vacía la barra", no al revés).
- Techo de stress: 9 (ya existente, en la hoja de cada ser).
- Rechazo: la barra baja a la mitad.

## Veredicto de James

- Fecha:
- Notas:
