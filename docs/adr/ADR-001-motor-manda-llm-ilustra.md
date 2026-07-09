# ADR-001: El motor mantiene el estado, el LLM solo ilustra

*Estado: aceptada — Junio 2026*

---

## Contexto

Codex Fragmentum es una ficción interactiva construida sobre modelos de lenguaje. La pregunta más fundamental de su arquitectura es quién tiene la autoridad sobre la verdad del mundo: ¿el LLM, que genera el texto que el jugador lee, o un motor determinista separado que mantiene el estado?

Esta decisión condiciona todo lo demás. Define qué puede y qué no puede hacer el LLM, cómo se garantiza la coherencia del mundo a lo largo de sesiones largas, cómo se persiste el estado, y qué tan dependiente es el sistema de las particularidades de cualquier modelo concreto.

El problema de fondo es conocido en los sistemas narrativos basados en IA. Un LLM es excelente generando prosa pero es estructuralmente incapaz de mantener estado consistente a lo largo del tiempo. Olvida lo que dijo hace muchas interacciones cuando su ventana de contexto se llena. Se contradice. Inventa hechos que no ocurrieron cuando se le pregunta por algo que no recuerda. Para una conversación corta esto es tolerable. Para un mundo persistente que el jugador habita durante decenas de horas y que debe recordar quién sabe qué, quién murió, qué pasó hace tres meses de tiempo del juego, es catastrófico.

## Opciones consideradas

### Opción A: El LLM es el motor

El LLM mantiene el estado del mundo en su contexto y en su capacidad generativa. Se le pasa la historia hasta el momento y se le pide que continúe, confiando en que recuerde y mantenga coherencia. Es el modelo de AI Dungeon y de la mayoría de los experimentos tempranos de narrativa con IA.

Ventajas: simplicidad de implementación inicial, flexibilidad máxima (el LLM puede hacer cualquier cosa sin que haya que programarla), arranque rápido.

Desventajas: incoherencia inevitable en sesiones largas, imposibilidad de garantizar que el mundo recuerde su propio estado, dependencia total de la ventana de contexto del modelo, imposibilidad de auditar o consultar el estado del mundo de forma estructurada, costo creciente porque hay que reenviar toda la historia en cada llamada.

### Opción B: El motor mantiene el estado, el LLM solo narra

Un motor determinista, escrito en código, mantiene el estado del mundo: qué entidades existen, qué saben, dónde están, qué pasó. El LLM se invoca para generar la prosa que ilustra lo que el motor ya determinó, recibiendo como entrada un contexto estructurado del estado relevante, y devolviendo narración. El LLM nunca decide qué pasó; decide cómo se cuenta lo que el motor dice que pasó.

Ventajas: coherencia garantizada porque el estado vive en estructuras de datos auditables, independencia de la ventana de contexto del modelo, posibilidad de consultar y persistir el estado, capacidad de cambiar de modelo sin perder el mundo, costo controlado porque solo se envía el contexto relevante a cada llamada.

Desventajas: mucho más trabajo de implementación porque hay que programar el motor que mantiene el estado, menos flexibilidad espontánea (lo que el motor no modela, no existe), riesgo de rigidez si el motor es demasiado restrictivo sobre lo que el LLM puede narrar.

### Opción C: Híbrido con estado parcial en el LLM

Un motor mantiene el estado duro (entidades, relaciones, hechos) pero se le permite al LLM cierta autonomía para generar detalles menores que después se incorporan al estado. Un punto intermedio donde el LLM puede proponer pequeñas verdades nuevas que el motor valida e incorpora.

Ventajas: combina coherencia en lo importante con flexibilidad en lo menor.

Desventajas: complejidad de decidir qué es "menor" y qué es "importante", riesgo de que las pequeñas verdades generadas por el LLM se acumulen en inconsistencias, frontera difusa difícil de mantener.

## Decisión

Se adopta la Opción B: el motor mantiene el estado, el LLM solo ilustra.

La regla operativa es: el motor del Codex tiene el estado del mundo y decide qué pasó. El LLM recibe contexto estructurado de qué pasó y produce narración. El LLM puede inventar cómo se siente algo, qué olor tiene, qué metáfora lo describe, pero no puede inventar que algo pasó. Lo que pasó lo determina el motor.

Cuando el LLM devuelve una narración que se sale de los hechos que el motor estableció (por ejemplo, narra que un personaje hizo algo distinto de lo que el motor determinó), el sistema lo detecta y rechaza o corrige la respuesta. Esta validación es parte del flujo normal, no un caso excepcional.

Se incorpora un matiz controlado de la Opción C, pero acotado y siempre bajo validación: cuando el LLM genera contenido que debe incorporarse al estado (por ejemplo, la versión mutada de un rumor, o la propuesta de un hito biográfico), ese contenido pasa por validación estructurada (Pydantic) y por reglas de coherencia antes de incorporarse. El LLM propone, el motor dispone. Nunca se incorpora al estado contenido del LLM sin validar.

## Consecuencias

### Positivas

El mundo es coherente a lo largo de sesiones arbitrariamente largas, porque su estado no vive en la memoria volátil del LLM sino en estructuras de datos persistentes. Un mundo de Codex puede recordar lo que pasó hace cien horas de juego porque ese recuerdo es un dato, no una esperanza de que el modelo no haya olvidado.

El sistema es independiente del modelo. Cambiar de Gemini a Claude, o a un modelo local, o a lo que exista en cinco años, no destruye el mundo, porque el mundo no vive en el modelo. Esto conecta directamente con la filosofía de no ser adicto a ningún proveedor (ver ADR sobre capas de costo).

El estado es auditable y consultable. Se puede preguntar al sistema, de forma estructurada y sin invocar al LLM, qué sabe un personaje, dónde está, qué pasó. Esto es esencial para depurar, para la simulación lazy, y para que el motor tome decisiones deterministas baratas.

El costo se controla. No hay que reenviar toda la historia en cada llamada; solo el contexto relevante al momento. Esto hace viable económicamente el uso prolongado.

### Negativas

El costo de implementación es mucho mayor que dejar que el LLM haga todo. Hay que programar el motor que mantiene el estado del mundo, que es la mayor parte del trabajo del proyecto. Esta es una desventaja real y aceptada: estamos eligiendo más trabajo a cambio de coherencia y robustez.

Lo que el motor no modela, no existe. Si el motor no tiene un concepto de, digamos, el clima, entonces el clima no puede afectar la historia de forma persistente, aunque el LLM pueda mencionarlo en una narración aislada. Esto significa que la riqueza del mundo está limitada por lo que el motor modela, y ampliar esa riqueza requiere programar, no solo prompts. Es el precio de la coherencia.

Existe un riesgo de rigidez. Si el motor es demasiado restrictivo sobre lo que el LLM puede narrar, la prosa puede sentirse encorsetada, perdiendo la espontaneidad que hace atractivos a los sistemas donde el LLM tiene rienda suelta. Mitigación: el motor debe controlar el qué (qué pasó) pero darle al LLM libertad amplia sobre el cómo (cómo se cuenta, qué se siente, qué se describe). La frontera entre qué y cómo hay que cuidarla en cada template de prompt.

La validación de las respuestas del LLM agrega complejidad al flujo. Cada respuesta que se incorpora al estado tiene que validarse, lo que significa más código, más casos de error que manejar, más posibilidad de que una validación falle y haya que reintentar. Esto está cubierto en el skill de validación y resilencia, pero es trabajo real que se origina en esta decisión.

## Notas de implementación

Esta decisión ya está reflejada en los skills de arquitectura, memetario, grafo de mundo, y prompts. El skill de prompts en particular desarrolla la consigna "el LLM nunca es la fuente de verdad" y los mecanismos de validación. Esta decisión es el fundamento del que esos desarrollos dependen.

La frontera entre lo que el motor controla y lo que el LLM decide se desarrolla con más detalle en el ADR sobre la frontera núcleo-reglas y en el ADR sobre capas de costo, que son refinamientos de esta decisión fundamental.
