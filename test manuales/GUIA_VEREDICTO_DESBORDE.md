# Guía de veredicto — el desborde

Esta guía es para vos, James. El desborde está construido, con **231 tests en verde** y
verificado de punta a punta con LLM simulado, pero **sin commit**: falta tu veredicto.

Lo que promete, en una frase: que cuando un ser aguanta todo lo que puede aguantar, le
quede una cicatriz que vos reconozcas como herida y no como un número que cambió.

El criterio de éxito es tuyo, pero el honesto sería:

> Éxito si la escena de la cicatriz se lee como una herida —algo que le pasó a alguien—
> y la idea que le queda te da ganas de aprobarla porque suena a él. Fracaso si suena a
> horóscopo, a lección sana, o a debuff con prosa. **Reportar que no funciona también es
> un buen veredicto.**

Casi todo el recorrido cuesta cero tokens. Solo el paso 4 gasta llamadas, y son las que
deciden el veredicto.

---

## Antes de empezar

```
./venv/bin/python taller/servidor.py
```

Mundo **`prueba`**. Tres cosas para saber antes de apretar nada:

- **Tus seres ya tienen barra cargada** de lo que jugaste: el comerciante está en 8 de 9,
  el pescador en 6 de 9, el que no muere en 6 de 25.
- **El que no muere aguanta 25**, casi tres veces más que los demás. No lo toqué: es una
  decisión tuya y le queda bien al personaje.
- **Lo que hagas acá es real.** Aprobar una cicatriz siembra un meme de verdad. Si querés
  probar sin consecuencias, hacelo en un mundo nuevo.

---

## Paso 1 — La barra ahora mide lo que le pasa (cero tokens)

Antes, la barra solo subía cuando **vos** elegías empujar una tirada: medía tu acelerador,
no la vida del ser. Ahora un mal resultado le cobra al ser aunque vos no pagues nada.

1. Zona **Personajes**: mirá la barra de cada ser, al lado de su hoja. Es el chip nuevo
   con los bloquecitos.
2. Zona **Probar**, jugá un Score con el **pescador** (está en 6 de 9). Elegí una acción
   donde le pueda ir mal.
3. Mirá el resultado: si salió **con costo** le sumó 1, si salió **mala consecuencia** le
   sumó 2. Si además empujaste, se suman las dos cosas.
4. Volvé a Personajes y mirá cómo quedó su barra.

**Lo que tenés que juzgar acá:** si el ritmo se siente bien. Con estos números, un ser de
techo 9 se desborda más o menos cada ocho o diez escenas malas. Si te parece que se rompe
demasiado seguido o demasiado poco, se toca una perilla (`CARGA_CON_COSTO` y
`CARGA_MALA_CONSECUENCIA`, al tope de `codex/blades.py`).

---

## Paso 2 — El tiempo calma (cero tokens)

1. Zona **Mundo**: avanzá el reloj unos días.
2. Volvé a Personajes: las barras de **todos** bajaron. Es el mismo tick que ya enfriaba
   los memes.
3. Probá también el latido: **Vivir N días** en la zona Probar baja la barra del ser que
   vivió, sin mover el reloj del mundo.
4. Comprobá lo contrario: **fijar** la hora (en vez de avanzarla) NO baja nada. Fijar es
   teletransporte autoral, no tiempo vivido.

**Lo que tenés que juzgar acá:** la velocidad. Está calibrado para que **un mes tranquilo
vacíe una barra llena de 9**. Ojo con el que no muere: como su techo es 25, un mes solo le
baja 9 puntos — necesita casi tres meses de paz para calmarse del todo. Puede que eso te
guste (aguanta más y también tarda más en soltar) o puede que no; decidilo vos.

---

## Paso 3 — Desbordar a un ser (cero tokens)

El comerciante está a **una mala consecuencia** del techo. Podés esperar a que pase
jugando, o forzarlo: en la ficha, modo **editar**, subile el stress al tope.

Cuando la barra llegue al techo vas a ver dos cosas: el chip de la barra se marca con ⚠,
y aparece el botón **«Se desbordó — que aparezca la cicatriz»**. Si el desborde pasó
jugando un Score, el aviso sale ahí mismo, sin que tengas que ir a la ficha.

---

## Paso 4 — La cicatriz (acá se gastan tokens, y acá está el veredicto)

1. Apretá **«Se desbordó — que aparezca la cicatriz»**.
2. Va a aparecer, en este orden: **la escena** (un párrafo de lo que le quedó al ser
   después del golpe) y debajo **la idea nueva** con su justificación.
3. **Leé la escena primero y sola.** Es lo único de todo el sistema que se lee, y es lo
   que decide si esto sirve.

**Las preguntas del veredicto:**

- ¿La escena se siente como algo que le pasó a **ese** ser, o podría ser de cualquiera?
- ¿Es concreta —un gesto, un silencio, algo que hace distinto— o explica la herida?
- ¿La idea que le queda suena a **lo que aprendió mal**, o a una lección sana de manual?
- ¿Te dan ganas de aprobarla?

4. Decidí: **Aprobar la cicatriz** (le queda el meme y la barra vuelve a cero) o
   **Aguantó** (no le queda nada, y la barra baja a la mitad del techo).
5. Si aprobaste, mirá su cristal: el meme nuevo está ahí, con peso humilde. Nace débil a
   propósito — es una sospecha recién grabada, no una certeza.

*Si la tarjeta se te pierde (recargaste la página), no perdiste nada: mientras la barra
siga llena el ser sigue desbordado y podés pedirla de nuevo. Sale una cicatriz distinta
cada vez, así que también podés pedir dos y comparar.*

**Si sale a horóscopo:** lo primero a tocar es el prompt, no los números — está en
`templates/trauma.txt`, editable desde la zona **Templates** del Taller. Según tu propio
doc de diseño, cuando un trauma se siente arbitrario el problema casi siempre está ahí.

---

## Paso 5 — La herida que ya tenía (opcional, un token)

Hay un caso que vale la pena ver: si lo que el desborde le deja es algo que el ser **ya
creía**, el motor no le agrega una idea nueva — refuerza la que ya tiene, y te lo dice
así en la tarjeta. Un ser no junta cinco versiones de la misma cicatriz.

Es difícil de forzar a propósito. Si te aparece jugando, mirá si te parece la decisión
correcta.

---

## Lo que quedó explícitamente afuera

Para que sepas que se decidió, no que se olvidó:

- Que la cicatriz **ascienda** a meme permanente después de usarse muchas veces.
- La **crisis biográfica**: que una cicatriz dominante llegue a cambiar una piedra
  fundacional. Necesita meses de juego acumulado.
- Las **reapariciones**: palabras gatillo, lugares, sueños recurrentes.
- El **vicio y el downtime**: su mitad distintiva necesita la cartografía, que todavía
  no existe.

---

## Veredicto

*(Completá acá, con fecha. Sin tu firma, nada se da por cerrado.)*

### La escena de la cicatriz — ¿herida o debuff con prosa?
- Veredicto:
- Fecha:
- Notas:

### El ritmo — ¿se rompen demasiado seguido, demasiado poco?
- Veredicto:
- Notas:

### La velocidad de la calma — ¿un mes está bien?
- Veredicto:
- Notas:

### ¿Algo que quieras cambiar antes de commitear?
-
