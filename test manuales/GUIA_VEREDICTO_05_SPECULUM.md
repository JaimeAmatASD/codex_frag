# Guía de veredicto — Mejora 05: el SPECULUM mínimo

Esta guía es para vos, James. El espejo está construido, con 169 tests en verde y
verificado fin a fin con Gemini real (sobre una copia; tu mundo `prueba` está
intacto y todavía no se miró nadie en él). Lo que falta es tu lectura, con el
criterio de éxito que definiste en el doc de la mejora:

> Éxito si la reflexión te cuenta algo del personaje que vos no habías formulado
> pero reconocés al leerlo (el espejo muestra, no inventa), y si al menos una
> propuesta te da ganas de aprobarla. Si las reflexiones son horóscopo genérico
> tras iterar el template, reportar honesto: el SPECULUM sin espejo real es peor
> que no tenerlo.

**Reportar que sale horóscopo también es un buen veredicto**: complejidad evitada
con datos.

---

## Antes de empezar: levantar el Taller

```
./venv/bin/python taller/servidor.py
```

Se abre el navegador solo (puerto 8765). La key de Gemini se lee de `~/.gemini_key`.
Todo pasa en el mundo **`prueba`**, zona **Personajes**: cada ficha tiene ahora el
botón **«Que se mire (LLM real)»**.

Tres cosas para saber antes de apretar nada:

- **Nada se aplica solo.** La mirada devuelve una reflexión y propuestas en
  tarjetas; el mundo no cambia hasta que VOS aprobás una. Rechazar no toca nada.
- **Las piedras fundacionales son intocables** por esta vía. Si al ser le tambalea
  una, el espejo solo puede DECIRLO en la reflexión — es material para futuras
  crisis biográficas, no una propuesta.
- Cada mirada es una llamada real a Gemini, y queda en la **Bitácora** (tipo
  `speculum`), así podés comparar intentos si después tocás el template.

---

## Paso 1 — El espejo que se niega (material insuficiente)

El espejo solo funciona con vida acumulada: **10 movilizaciones** como mínimo
(usos reales de memes, no solo llevados en el loadout). Sin eso, el Taller lo dice
y el LLM ni se llama.

1. Buscá a **comerciante_esceptico** (hoy lleva 8 movilizaciones) y apretá
   «Que se mire».
2. Tiene que aparecer el aviso: cuántas lleva, cuántas pide el mínimo. Sin
   demora, sin gasto: no hubo llamada.

Esto es una decisión de diseño tuya de chequear: la reflexión sin acumulación es
humo. Si el aviso te parece claro, listo el paso.

---

## Paso 2 — La mirada de verdad

**el_que_no_muere** ya supera el umbral (16 movilizaciones de las sesiones que
jugaste). Mejor todavía si antes le das un rato más de vida — el doc pide "después
de una sesión de juego real": contale un hecho en **Probar**, charlá algo en
**Diálogo**, tirá un Score. Cuanto más registro, más espejo.

1. En su ficha, abrí antes «el cristal, viviendo» y mirá los pesos un momento:
   eso es lo que el espejo va a leer. Fijate especialmente qué memes tienen
   movilizado 0 — los silencios.
2. Apretá **«Que se mire (LLM real)»**. Tarda unos segundos.
3. Leé la reflexión despacio, con estas preguntas:
   - ¿Te cuenta algo que vos NO habías formulado pero reconocés al leerlo?
   - ¿Cita la evidencia (la idea que lleva siempre y nunca usa, la que usa más
     de lo que admitiría, la grieta que se le repite), o podría ser la reflexión
     de cualquier personaje?
   - Si nombra una piedra que tambalea: ¿lo dice sin proponer tocarla?

*Dato de la verificación nuestra, para que lo peses vos:* en la corrida de prueba
su reflexión nombró las tres piedras que carga y jamás usó, el meme de la
vigilancia usado el 100% de las veces, su grieta repetida 5 veces, y cerró con que
sus piedras amenazan con volverse «peso muerto en mi espalda» — sin proponer
tocarlas. La captura está en `screenshoots/speculum_mirada.png`. Salió anclada,
no horóscopo; pero fue UNA corrida, y el criterio es tuyo.

---

## Paso 3 — Disponer (aprobar y rechazar)

Debajo de la reflexión salen las propuestas (de cero a tres), cada una con su
justificación citando la evidencia. Solo dos formas posibles: mover el peso de un
meme no fundacional (máximo 2 puntos — nadie se refunda en una noche) o probarse
un meme experimental nuevo (nace humilde, peso hasta 3).

1. Si alguna te da ganas, **Aprobá** — de a una. El peso se mueve por la puerta
   única (o el experimental entra a la semilla y se siembra) y lo ves al instante
   en la tabla del cristal. Queda en la Bitácora (`speculum_aplicada`) con la
   justificación.
2. Las que no te convencen, **Rechazá**: la tarjeta desaparece y nada pasó.
3. Ojo: aprobar modifica tu mundo `prueba` de verdad. Está bien — es tu mesa de
   trabajo — pero si querés dejar todo como estaba, rechazá todo.

La pregunta del criterio acá: **¿al menos una propuesta te dio ganas de
aprobarla?** No "es razonable", sino ganas: que el ajuste le venga bien al
personaje que vos conocés.

---

## Paso 4 (opcional) — El ciclo completo

Si aprobaste algo, la prueba de fuego es que el cambio se note viviendo:

1. Hablale en **Diálogo** o contale un hecho en **Probar** que roce el meme
   ajustado (o el experimental nuevo).
2. ¿La voz acusa el cambio? Un experimental recién sembrado pesa poco (es una
   sospecha, no una certeza), así que puede tardar en asomar — eso también es
   diseño, no falla.

---

## Si sale horóscopo: iterar antes de sentenciar

El template vive en la zona **Templates → «el espejo (speculum)»**. Como con la
mutación y el Score, la primera respuesta floja no es el veredicto: tocá el
template (por ejemplo, endurecé el "el espejo MUESTRA, no inventa", o pedile que
cite números), guardá y pedile otra mirada. La Bitácora te deja comparar las dos
lado a lado. Si tras un par de vueltas sigue genérico, veredicto honesto.

---

## Veredicto

*(Completá acá, con fecha. Sin tu firma acá abajo, la serie no se cierra.)*

### Mejora 05 — SPECULUM mínimo
- ¿La reflexión te contó algo que reconociste sin haberlo formulado? (sí / no / a medias):
- ¿Alguna propuesta te dio ganas de aprobarla? ¿Cuál?:
- Veredicto (éxito / fracaso honesto / iterar template y repetir):
- Fecha:
- Notas:

---

Con este veredicto escrito, la serie de 5 mejoras queda cerrada del todo.
