# Guía de veredictos — Mejoras 01 a 04

Esta guía es para vos, James. Las cuatro mejoras están construidas, con tests en verde
y verificadas con Gemini real. Lo único que falta es tu lectura: cada una tiene un
criterio de éxito que definiste en su doc, y acá está convertido en pasos concretos.

Se hace en una tarde, en orden (01 → 04). Al final de esta guía hay un espacio para
escribir cada veredicto. **Reportar que algo no funciona también es un buen veredicto**:
complejidad evitada con datos.

---

## Antes de empezar: levantar el Taller

En una terminal, parado en la carpeta del proyecto:

```
./venv/bin/python taller/servidor.py
```

Se abre el navegador solo (puerto 8765). La key de Gemini se lee de `~/.gemini_key`.
Para las mejoras 01, 02 y 03 usá el mundo **`prueba`**. Para la 04, el mundo
**`experimento_04`** (la corrida ya está hecha; solo vas a leer).

---

## Mejora 01 — La grieta (tensión interna)

**La pregunta:** ¿la versión con tensión delata que el ser está tironeado, sin que el
texto lo resuelva ni lo explique didácticamente?

El ser de prueba es **el_que_no_muere**, con la tensión que elegiste:
«el olvido» ⇄ «conosco esta tierra». Los pesos están parejos, así que la grieta
está activa.

1. En la zona **Probar**, contale un hecho a el_que_no_muere. Uno que toque la
   tensión rinde más (algo sobre recordar, sobre la tierra, sobre perder algo).
2. Mirá la respuesta: abajo de los memes resonantes tienen que aparecer las
   **tensiones activas**. Guardá o copiá el texto de su versión.
3. Ahora desactivá la grieta: en **Personajes**, editá el_que_no_muere y bajale
   bastante el peso a uno de los dos memes (por ejemplo «el olvido» a la mitad).
   Guardá.
4. Contale **el mismo hecho** de nuevo y leé las dos versiones lado a lado.
5. **Restaurá el peso original** cuando termines.

Éxito si en la primera versión se nota el tironeo y en la segunda no. Si la
diferencia no se siente, el doc de la 01 ya prevé el camino: iterar la plantilla
(`templates/tension.txt`, editable desde la zona Templates) o recalibrar el umbral —
anotalo así en el veredicto.

---

## Mejora 02 — El constructor (relatar un ser)

**La pregunta:** ¿el ser propuesto SE SIENTE él al primer vistazo, y lo único que dan
ganas de hacer es retocar palabras, no rearmar la estructura?

1. En **Personajes**, arriba del formulario está el campo «Relatá al personaje»
   (podés dictar 🎙). Usá el ejemplo del doc, tal cual:
   *«Es un veterinario de 62 años, ayuda a cualquiera, nunca perdonó a su hijo,
   tiene miedo a quedarse solo.»*
2. Botón **Derivar ser**. La propuesta cae en el formulario — nada se guarda solo.
3. Revisá con tu ojo: ¿las piedras suenan a leyes suyas? ¿está el miedo a quedarse
   solo? ¿la contradicción (ayuda a cualquiera / nunca perdonó al hijo) quedó
   declarada como tensión con pesos parejos?
4. La prueba completa del ciclo: guardalo, contale un hecho en Probar, y leé si su
   versión lo delata a él.
5. Si no lo querés en el mundo, borralo después.

Si las propuestas salen genéricas, probá reformular el relato o tocar
`templates/derivar_ser.txt`, y si tras un par de vueltas sigue genérico, veredicto
honesto.

---

## Mejora 03 — El Hombre Pez (singularidad)

**La pregunta:** ¿se siente como destino y no como script?

La singularidad sembrada está **pendiente**: la noche de la primera luna de sangre
(1850-03-03, 23:00), los cuatro se encuentran con el Hombre Pez en el risco aislado.

1. En la zona **Mundo**, mirá la lista de singularidades: «el_hombre_pez» tiene que
   figurar como pendiente, con el reloj del mundo antes de esa noche.
2. **Avanzá el reloj** hasta pasada la medianoche del 3 de marzo de 1850.
3. Al cruzar el momento, la singularidad dispara: andá a **Lore** y encontrá el
   encuentro como hecho nuevo. Los cuatro seres quedaron como testigos de la
   versión raíz.
4. Ahora las historias: pedile a dos de los testigos (por ejemplo el pescador y el
   comerciante) que lo recuenten, y leé las dos versiones. El evento era inevitable;
   lo que cada uno vio, no.

Éxito si al leerlo sentís que el mundo tenía una cita marcada y cada ser salió de
ella con su propia herida. Si se siente mecánico, script, anotalo.

*Nota: si necesitás repetirla, el reset del mundo la vuelve pendiente — pero el
reset borra todo el estado vivo (pesos, activaciones, reloj), así que dejala para
el final si vas a resetear.*

---

## Mejora 04 — El experimento de aprendizaje (veredicto ESCRITO)

**La pregunta única:** ¿el radicalizado SUENA más atrincherado, o solo tiene otro
número?

Esta no requiere correr nada: el A/B ya se corrió con Gemini real
(`demos/experimento_04_ab.py`). Dos vigías idénticos salvo un meme central:
`vigia_normal` (política normal) y `vigia_radical` (se_radicaliza), bombardeados
con la misma secuencia de noticias contradictorias sobre el faro.

1. En el Taller, elegí el mundo **`experimento_04`**.
2. En el estado vivo, compará los pesos del meme central: el normal quedó en
   **7.00** (no se movió), el radical subió **7.00 → 8.77**. Además la grieta del
   radical se apagó al final: se atrincheró tanto que la tensión cruzó el umbral.
3. En la **Bitácora** están las 12 transmisiones de la corrida. Las últimas dos son
   el mismo hecho final contado a cada vigía: leelas lado a lado. Ahí está el
   corazón del veredicto.

**El dato honesto que ya vimos nosotros** (para que lo peses vos): los números
divergen con claridad, pero las dos voces del hecho final suenan parecidas — ambas
dudan del faro. La contradicción hoy mueve pesos y estructura interna, no (todavía)
la voz, porque el prompt de mutación no ve los pesos.

Tu veredicto tiene tres salidas posibles, y las tres son buenas si son honestas:

- **Éxito**: la diferencia se nota al leer, no solo en el número. Se adopta.
- **Fracaso**: los pesos divergen pero las voces no. Se borra el campo o queda
  inerte, con la evidencia anotada. Complejidad evitada con datos.
- **Una iteración antes de decidir**: que el prompt de mutación vea los pesos
  (el atrincheramiento entraría a la voz) y repetir el A/B. Es un cambio chico;
  lo pedís y lo hacemos.

---

## Veredictos

*(Completá acá, con fecha. Sin tu firma acá abajo, nada se da por cerrado.)*

### Mejora 01 — tensión interna
- Veredicto:
- Fecha:
- Notas:

### Mejora 02 — constructor de seres
- Veredicto:
- Fecha:
- Notas:

### Mejora 03 — singularidades
- Veredicto:
- Fecha:
- Notas:

### Mejora 04 — aprendizaje por meme (experimento)
- Veredicto (éxito / fracaso / una iteración):
- Fecha:
- Notas:

---

Con los cuatro veredictos escritos, recién ahí arranca la **05 (SPECULUM mínimo)**.
