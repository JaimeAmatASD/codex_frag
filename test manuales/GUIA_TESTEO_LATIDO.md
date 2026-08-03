# Guía de testeo — El latido (vida ociosa, paso 2)

Esta guía es para vos, James. El latido está construido, con 191 tests en verde,
pero **sin commit todavía**: falta tu veredicto. Esta guía es el recorrido para
dártelo con las manos en la masa, no leyendo código.

Lo que el latido promete, en una frase: que el ser viva entre tus visitas —
rutina barata y sin LLM que mueve los pesos — para que los pesos midan al
personaje y no tu atención. El criterio de éxito es tuyo, pero el honesto sería:

> Éxito si después de un mes de vida los pesos se movieron de una forma en la
> que reconocés al personaje (la vida lo talló, no lo desfiguró), y si la cola
> de momentos calientes te trae escenas que te dan ganas de jugar. Si la rutina
> empuja los pesos a cualquier lado, o los momentos calientes son ruido,
> reportar honesto: un latido que desfigura es peor que un ser apagado.

**Todo este recorrido cuesta cero tokens.** El latido no llama a ningún LLM por
construcción (hay un test que revisa el código fuente para garantizarlo). Solo
el paso 6, opcional, gasta una llamada.

---

## Antes de empezar

```
./venv/bin/python taller/servidor.py
```

Mundo **`prueba`**, zona **Probar**: ahí está el panel nuevo
**«Vivir N días — la vida ociosa (cero tokens)»**, y debajo la cola de
**Momentos calientes pendientes**.

Tres cosas para saber antes de apretar nada:

- **La vida vivida es vivida.** Vivir N días mueve los pesos del ser de verdad
  (micro-refuerzos y decaimiento diario). Es tu mesa de trabajo, está bien —
  pero no es un simulacro que se descarta.
- **El reloj del mundo NO se toca.** Los días vividos son del ser, no del
  mundo. Si querés que el tiempo pase para todos, avanzás el reloj como
  siempre. (Decisión mía, la podés vetar.)
- El mundo necesita **hora fijada** para vivir; si no la tiene, el Taller te lo
  dice y no pasa nada.

---

## Paso 0 — Leer la rutina antes de vivirla

El único ser con rutina hoy es **el_que_no_muere**. Su rutina vive en
`mundos/prueba/seres/el_que_no_muere/rutina.json`: 8 plantillas (despertar,
huerta, mercado, repaso junto al fuego…) repartidas en mañana/tarde/noche, y
dos **anomalías** con peso 0.5 — el hueco donde ayer había un recuerdo, las
anotaciones con su letra que le resultan ajenas.

Leela y preguntate: **¿esta es la vida de tu personaje?** La rutina es
contenido, no motor: si una plantilla no te suena, editá el JSON y listo. La
escribí yo como ejemplo; es tuya.

---

## Paso 1 — El ser sin rutina no late

1. En el panel, elegí a **hombre_loco** (o cualquier otro) y apretá «Vivir».
2. Tiene que salir el aviso: sin `rutina.json` no late. Nada cambió.

Chequeo de diseño: un ser sin rutina no vive a medias ni inventa una — se salta
con aviso. Si el mensaje te parece claro, listo.

---

## Paso 2 — Un día, reproducible

1. Elegí a **el_que_no_muere**, días = **1**, semilla = **42**. «Vivir».
2. Mirá el resultado: los pesos inicio → fin con su delta (verde sube, rojo
   baja). Con un solo día los movimientos son chicos — así debe ser: la vida
   ordinaria talla despacio (refuerzo 0.02 por uso, no el 0.20 de una escena).
   **Aviso: con semilla 42 van a salir todos en rojo, incluso los memes que el
   día movilizó.** No es una falla, es el balance de las constantes, y conviene
   que lo entiendas antes del paso 3 — está explicado abajo, en «El equilibrio
   real». Un día es demasiado poco para que la rutina levante nada.
3. Andá a la **Bitácora**: hay una entrada tipo `vida` por día vivido, con los
   3 ticks (mañana 9h, tarde 15h, noche 22h): qué situación tocó y qué memes
   movilizó cada una. Si un meme de afuera del cristal irrumpió, dice
   `[irrupción]`; si un tick escaló, dice `[caliente]`.
4. Preguntas para este paso:
   - ¿Las situaciones caen en la franja que les corresponde?
   - ¿Los memes que se movilizan tienen que ver con la situación? (El repaso
     nocturno debería convocar otra cosa que el mercado.)

Con la misma semilla, la corrida se repite idéntica — útil si querés mirar dos
veces lo mismo. Sin semilla, la vida es la que salga.

---

## Paso 3 — Un mes: el equilibrio

Este es el paso del veredicto. Antes de correrlo, abrí la ficha del ser y mirá
**«el cristal, viviendo»**: anotá (mentalmente) los pesos de ahora.

1. Días = **30**, sin semilla. «Vivir». Tarda unos segundos: son 90 ticks y 30
   ciclos de decaimiento.
2. Leé los deltas con estas preguntas:
   - ¿Lo que subió es lo que ese hombre usaría viviendo esa vida? ¿Lo que bajó
     es lo que esa vida no toca?
   - ¿Las dos anomalías de la rutina empujaron lo que tenían que empujar
     (vigilancia, sospecha de la propia memoria)? *Dato de la verificación
     nuestra: en 60 días de test, la vigilancia subió de 2.0 a ~3.0–3.9
     mientras el control sin anomalías quedó en ~2.0.*
   - ¿Algún peso se fue a un extremo que desfigura al personaje? Eso sería
     falla del equilibrio rutina/decaimiento, y es exactamente lo que hay que
     reportar.
   - **La pregunta nueva, con lo medido en «El equilibrio real»:** ¿te parece
     bien que un mes de vida ordinaria erosione sus convicciones más fuertes
     (las de peso alto) mientras levanta las débiles? Mirá si el ser que sale de
     los 30 días sigue siendo el mismo hombre, o si quedó aplanado hacia el
     medio.
3. Volvé a la ficha: `veces_movilizado` creció **sin que vos hicieras nada**.
   Ese era el problema de fondo — los números del expediente ya no miden solo
   tu atención. (En la tabla de activaciones cada registro lleva ahora su
   régimen: `vivencia` para lo autorado, `rutina` e `interferencia` para lo del
   latido — el fondo y la escena no se mezclan.)

---

## El equilibrio real (medido el 2026-07-30, para tu criterio)

Esto no lo sabíamos cuando se construyó el latido; salió de ensayar el paso 2. Los
dos movimientos son asintóticos: el decaimiento tira hacia el piso (0.1), el
refuerzo hacia el techo (10). Eso hace que **el mismo día de vida pese distinto
según cuán fuerte sea el meme**:

| peso del meme | pierde en un día | gana por movilización | movilizaciones/día para empatar |
|---|---|---|---|
| 2.0 (débil) | −0.095 | +0.160 | **1** |
| 5.0 (medio) | −0.245 | +0.100 | **3** |
| 8.0 (fuerte) | −0.395 | +0.040 | **9** |

Hay **3 ticks por día**, y cada tick moviliza 1 o 2 memes de todo el memetario. O
sea: un meme débil que la rutina roza una vez ya sube; uno medio necesita salir en
casi todos los ticks para no bajar; **uno fuerte no puede sostenerse por rutina, es
aritméticamente imposible**.

La consecuencia: la vida ordinaria **comprime** la personalidad. Levanta lo débil y
erosiona lo fuerte. El drift test que pasó en verde (la vigilancia de 2.0 a ~3.0-3.9)
probó justamente el caso favorable: un meme que arrancaba débil.

**La pregunta es tuya y es literaria, no técnica.** Hay dos lecturas legítimas:

- *Está bien así.* Una vida sin acontecimientos aplana a cualquiera; lo que no se
  ejercita se pierde; que las convicciones fuertes se erosionen entre visitas es
  exactamente lo que le pasaba a Fray Tomás sintiéndose encerrado. Los picos
  autorados (Score, transmisión, diálogo, con refuerzo 0.20) son los que sostienen
  lo fuerte, y así debe ser: el carácter se sostiene con acontecimientos.
- *Está mal así.* Si el latido arrastra todo hacia el medio, los pesos vuelven a no
  medir al ser — solo miden cuánto tiempo pasó sin que lo visites, que es el problema
  original con otro disfraz.

Si tras el paso 3 te parece que desfigura, hay perillas para tocar (subir el refuerzo
de rutina, bajar el decaimiento diario, más ticks por día, o que el decaimiento
también se ablande con el peso). No toqué ninguna: elegir acá es tu veredicto.

---

## Paso 4 — La cola de momentos calientes

Más o menos 1 de cada 20 ticks escala: en 30 días (90 ticks) esperá unos 4–5
momentos calientes. (En 7 días puede salir cero — es azar, no falla.)

Cada momento pendiente trae la situación y el cristal que estaba despierto, y
cuatro botones:

- **Jugarlo como Score** — te lleva al Score con la situación ya cargada.
- **Contarle algo en ese momento** — te lleva a la transmisión.
- **Marcar jugado** / **Descartar** — curaduría pura.

1. Jugá **uno** que te llame, por la puerta que pida la escena.
2. Descartá alguno que no.
3. Las preguntas del criterio acá:
   - ¿Los momentos que trae la vida **dan ganas** de jugarlos? No "son
     razonables": ganas.
   - ¿Con la situación y el cristal alcanza para jugar la escena, o llegás con
     las manos vacías?

Este es el cambio de workflow que promete el latido: vos dejás de inventar
situaciones y pasás a **curar** las que la vida trajo. Si eso no te alivia el
trabajo autoral, hay que repensarlo — la restricción dura sigue siendo que no
te pida más clicks de los que das hoy.

---

## Paso 5 — La corrida de mesa (opcional, terminal)

Lo mismo sin Taller, para cuando quieras mirar de cerca:

```
./venv/bin/python demos/vivir.py --mundo prueba --ser el_que_no_muere --dias 30 --semilla 42
```

Imprime deltas y pendientes. Ojo: también mueve los pesos de verdad; lo que no
hace es persistir la cola (esa vive en el Taller).

---

## Paso 6 (opcional, gasta una llamada) — El espejo después de la vida

Si viviste un mes o más, apretá **«Que se mire (LLM real)»** en la ficha. La
pregunta original de todo este problema: ¿el espejo ahora distingue mejor el
silencio por carácter del silencio por falta de ocasión? ¿La reflexión suena
más al personaje que la de la corrida de julio?

---

## Decisiones mías que podés vetar

- `/vida` **no** avanza el reloj del mundo (los días son del ser).
- Las **piedras fundacionales no laten**: la rutina no las refuerza ni las
  moviliza (su presencia en el cristal ya queda registrada).
- 3 ticks por día, a las **9, 15 y 22**.
- Interferencia **5%** (el pensamiento de ducha), escalada **5%** (1 de cada 20
  ticks se marca caliente).
- Las anomalías de la rutina de ejemplo pesan **0.5** (la mitad de frecuentes
  que lo cotidiano).
- Una rutina lleva entre **3 y 20** plantillas.

---

## Veredicto

*(Completá acá, con fecha. Con tu firma, el paso 2 se commitea; sin ella, no.)*

### Vida ociosa, paso 2 — el latido
- ¿Tras un mes de vida reconocés al personaje en sus pesos? (sí / no / a medias):
- ¿La cola te trajo momentos con ganas de jugarlos? ¿Cuál jugaste?:
- ¿Alguna decisión vetada de la lista de arriba?:
- Veredicto (éxito / fracaso honesto / ajustar y repetir):
- Fecha:
- Notas:

---

Con este veredicto escrito se commitea el paso 2, y **recién entonces** tiene
sentido sentarnos a diseñar la fase 2 (el modo auto que consume la cola): para
ese diseño va a valer más una semana tuya usando la cola manual que cualquier
brainstorming en seco.
