# Mapa de integración — qué anda, qué anda a medias, qué es humo

Fecha: 2026-08-03. Pedido de James: *"necesito ver qué está realmente andando y qué
es más humo, y establecer qué cosas están conectadas y cuáles no, antes de empezar a
pulir lo narrativo y el engine."*

**Método.** No se leyó código para decidir esto. Se corrió. Una pieza no está viva
porque exista y tenga tests en verde — está viva si alguien la llama en producción y
si deja huella en el estado. Ese es el bug que ya nos comimos dos veces (`lessons.md`:
los contadores que medían la atención del autor; el decaimiento que nadie llamaba).

Tres barridos:

1. **Llamadores reales** — para cada función del motor, quién la usa fuera de los tests.
2. **Puertas de la UI** — para cada endpoint, si hay un botón que lo alcance.
3. **Corrida de verdad** — las 23 puertas del Taller, una por una, sobre una COPIA del
   mundo `prueba` real, con el encoder de embeddings de verdad y un LLM simulado que
   responde bien formado. Se midió el estado antes y después de cada una.

---

## Lo que anda, verificado corriendo

**Estructura, sin agujeros:**

- **Cero funciones huérfanas.** Ninguna función del motor existe sin que alguien la
  llame en producción. El bug de julio no se repitió.
- **Los 31 endpoints tienen puerta en la UI.** No hay API sin botón.
- **Toda escritura pasa por `persistencia.py`.** La puerta única se respeta: ningún
  módulo escribe pesos por su cuenta.
- **196 tests en verde.**

**Las puertas, con la huella que dejó cada una en la corrida:**

| Puerta | Huella medida |
|---|---|
| Transmitir | 2 pesos movidos, 2 movilizaciones, 1 bitácora |
| Diálogo | 1 peso movido, 2 movilizaciones, 1 bitácora |
| Score (evaluar → tirar) | 1 movilización, 1 bitácora, efectos aplicados |
| El latido (30 días) | 5 pesos movidos, 5 movilizaciones, 30 bitácora, 1 momento caliente |
| Reloj / avanzar | enfría los 5 memes de todos los seres |
| Espejo (mirar → aplicar) | 2 bitácora, 1 peso movido por la puerta única |
| Pesos a mano | mueve el peso vivo sin pisar la semilla |
| Hechos | entra al grafo con su versión raíz |

**Dos cosas que se creían pendientes y ya ocurrieron en tu mundo:**

- **La singularidad del Hombre Pez disparó de verdad** (marcada el 1850-03-03T23:55).
  Los cuatro seres quedaron conectados a la versión raíz, y una versión ya se derivó
  del pescador al becario. El encuentro pasó.
- **La derivación de seres corrió dos veces con Gemini real** (hay dos entradas
  `derivacion` en tu bitácora). En la auditoría dio 422 porque mi LLM simulado no
  habla ese formato — no es la pieza, es el simulador.

Tu bitácora acumula **121 entradas reales**: 45 diálogos, 35 Scores, 27 transmisiones,
7 propuestas del espejo aplicadas, 5 miradas, 2 derivaciones. Del 10 al 31 de julio.

---

## Lo que está conectado a medias

### 1. El bias circadiano está desenchufado en el Taller — **ARREGLADO el 2026-08-03**

`codex/bias.py` existía, testeado y funcionando, y lo usaba **solo el latido**.
Transmitir, Diálogo y Score pedían el loadout **sin bias**: el multiplicador quedaba en
1.0 y la hora del mundo no inclinaba nada en las tres puertas que James usa.

Enchufado con TDD (tres tests que fallaron primero, uno por puerta: el mismo ser, la
misma situación, y de noche elegía exactamente lo mismo que de día). Ahora:

- **Diálogo y Score** toman la hora del reloj del mundo.
- **Transmitir** toma la hora de la escena que manda el pedido: se escucha a la hora en
  que el emisor habla.
- Sin hora fijada, el cristal queda neutral como antes.

Suite: 199 en verde. **Pendiente de calibración de James:** los multiplicadores
(1.2 / 0.8, día de 6 a 18) son un punto de partida escrito en julio y nunca probado en
la mesa; viven al tope de `codex/bias.py`.

### 2. El stress sube, nunca baja, y al llegar arriba no pasa nada

No hay **vicio** ni **downtime** — cero código, aunque el diseño los tenga escritos. El
techo (9) solo apaga la posibilidad de empujar la tirada; no hay trauma, no hay meme
inyectado, no hay escena. El "trauma" solo existe como nombre de una política de
aprendizaje, que es otra cosa.

Tus seres hoy: comerciante 8, el que no muere 6, pescador 6, loco 2. **El comerciante
está a una tirada del tope**, y cuando lo cruce se le va a apagar una mecánica sin que
la ficción registre nada.

### 3. El latido nunca corrió sobre tu mundo real

De 202 activaciones registradas, **las 202 son de régimen `vivencia`. Cero de `rutina`.**
Y la cola de momentos calientes no existía como archivo hasta que la creó esta
auditoría. Tu mundo `prueba` no tiene un solo día de vida ociosa vivida.

Esto importa doble, porque es lo que mantiene vivo el problema de más abajo.

### 4. Los momentos calientes viven fuera del mundo

La cola va a `taller/pendientes/<mundo>.jsonl`, no a la carpeta del mundo, y no está en
`.gitignore`. Rompe "cada mundo una carpeta portable": si te llevás `mundos/prueba` a
otra máquina, la cola se queda atrás.

### 5. El espejo solo puede mirarse a dos de tus seis seres

Pide 10 movilizaciones. Hoy: comerciante 33, el que no muere 16, pescador 6, becario 4,
doctor 3, **loco 0**. Es exactamente el problema de la vida ociosa que planteaste en
julio, y sigue abierto porque el latido (punto 3) no está corriendo.

### 6. El reloj de amenaza casi no se mueve

1 de 6 segmentos después de 35 Scores. No es un bug, pero vale revisar si los umbrales
están tan altos que la presión nunca escala.

---

## Lo que es humo: documentado, sin una línea de código

- **La cartografía entera.** Grilla jerárquica, celdas, lugares con memetario propio,
  secretos sembrados, objetos y sus reinos. Hay un skill completo describiéndola y cero
  código. El mundo hoy no tiene espacio: `lugar` es un texto suelto en el hecho.
- **Vicios y downtime.** La otra mitad del motor de drama (ver punto 2).
- **El router de tiers de modelos.** Un solo modelo para todo; el propio docstring de
  `codex/llm` lo dice.
- **El corpus de fuentes por entidad.**
- **La fase 2 del latido**: el modo auto que consume la cola de momentos calientes.

---

## Lo que esto sugiere para la fase de pulido

El engine **está andando y está bien cableado**. La sorpresa no es que algo esté roto:
es que las piezas construidas están conectadas y dejan huella. Lo que falta es de otro
orden — pedazos que nunca se escribieron, y tres cables sueltos concretos (bias, stress
sin salida, latido sin correr).

Ninguna de las cinco reglas duras está violada.

---

## Huella de esta auditoría

Se corrió sobre una copia temporal. **El mundo real no se tocó** (sin modificaciones
desde el 2026-07-31 00:43). Pero por el punto 4, la corrida escribió un momento caliente
en `taller/pendientes/prueba.jsonl`, carpeta que antes no existía en el repo. Está
pendiente de borrado, a criterio de James.

---

## Veredicto de James

- Fecha:
- ¿Coincide el mapa con lo que ves en la mesa?:
- Por dónde arrancamos a pulir:
