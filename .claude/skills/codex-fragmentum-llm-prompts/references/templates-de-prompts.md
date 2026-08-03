# Templates de prompts — la cara concreta de la integración con LLM

Este archivo es referencia operativa para cuando estés escribiendo, iterando o debuggeando los prompts que el sistema le pasa al LLM. Es probablemente el archivo más práctico de toda la serie de prompts: las decisiones acá impactan directamente en la calidad del texto que el jugador efectivamente lee. Asume que el SKILL.md principal de prompts ya está cargado.

Una nota importante de entrada: este archivo cubre la mecánica y estructura de los prompts, no su dirección estética. Cuándo el LLM debería sonar borgeano versus le-guiniano, qué referencias literarias guían la prosa, qué prosa rechazamos como genérica, todo eso es territorio del skill de estética que James decidió postergar. Este archivo se enfoca en cómo armar prompts que efectivamente le den al LLM el contexto necesario para hacer su trabajo, asumiendo que la pregunta estética se resuelve aparte.

## Por qué los templates merecen iteración constante

Antes de meternos en estructura concreta, vale la pena entender por qué los templates son donde se juega tanto del proyecto. La razón tiene tres partes.

Primero, el LLM no sabe nada de Codex Fragmentum cuando recibe un prompt. No tiene contexto del proyecto, no conoce a tus personajes, no entiende tu mundo. Cada llamada parte de cero en términos de contexto del mundo. Lo único que sabe el LLM es lo que vos le pasás en el prompt mismo. Si el prompt no le da contexto suficiente, el output va a ser genérico. Si el prompt lo sobrecarga con información irrelevante, el output va a ser confuso.

Segundo, el LLM tiende a producir el output cómodo. Sin instrucciones específicas y orientadoras, va a producir prosa promedio en tono promedio con estructura predecible. Lo que diferencia un output mediocre de uno notable no es el modelo (los modelos modernos son capaces de prosa excelente) sino la calidad del prompt que los guía. Un buen prompt es como una buena dirección de cine: el LLM hace el trabajo pero la dirección le dice qué hacer y cómo.

Tercero, los templates son lo único que vas a iterar literalmente cientos de veces a lo largo del proyecto. El motor del Codex se programa una vez y se ajusta ocasionalmente. Los templates se afinan permanentemente porque cada vez que James note que algo del output no se siente bien, la primera intervención es ajustar el template, no tocar la mecánica. Por eso conviene programarlos para iteración fácil desde el día uno: archivos de texto separados, sistema de sustitución claro, versionado en git para poder comparar versiones.

## La estructura común de todos los templates en Codex

Todos los templates del proyecto comparten un esqueleto común con tres bloques. Tener esta estructura clara te ahorra reinventar el formato cada vez y le da consistencia al sistema.

El primer bloque es la voz narrativa raíz. Es un texto que vive en una variable global o en un archivo dedicado y se inyecta al inicio de todo prompt narrativo. Define quién es el narrador del Codex, qué tono mantiene, qué cosas nunca hace (no rompe la cuarta pared, no se disculpa por nada, no menciona que es una IA), qué referencias estéticas guían su prosa. El contenido específico de la voz narrativa raíz es decisión estética y por eso pertenece al skill de estética. Acá lo que importa es que existe, que es un solo texto unificado, y que se usa en todo prompt narrativo.

El segundo bloque es el contexto del momento. Este bloque es específico de cada llamada y contiene los datos estructurados que el motor pasa al LLM. Acá vive la información del personaje habitado (sus PF activas, sus MO en el loadout actual, sus hitos biográficos), del lugar donde está (su memetario simbólico, sus modificadores), de los hechos relevantes que el personaje conoce, de las últimas escenas para continuidad. La forma del contexto es siempre estructurada y consistente: nunca prosa libre del motor, siempre datos en formato claro.

El tercer bloque es la instrucción específica de la tarea. Esta parte cambia según qué template sea: narrar una escena de free play, refractar una pieza de información, generar la propuesta de un trauma, narrar el resultado de una tirada. La instrucción debe ser clara, concreta, con cualquier estructura de output requerida explicitada al final.

Esta estructura tripartita debería ser consistente en todos los templates. Cuando un asistente futuro lea un template de Codex, debería reconocer inmediatamente la estructura aunque no haya visto ese template específico antes. La consistencia ayuda a la mantenibilidad del sistema en el tiempo.

## Los templates fundamentales del MVP

Para el MVP necesitás tener funcionando un puñado de templates. No te conviene escribir todos antes de probar ninguno: empezá con los críticos, jugá una sesión, ajustá según lo que veas, después agregá los siguientes. Te listo los más importantes en orden de prioridad para construirlos.

El template de free play es el primero porque es el que más se va a usar. Recibe la acción declarada por el jugador, el contexto del personaje refractante, el lugar actual, los últimos turnos para continuidad, y le pide al LLM que narre la escena resultante. La instrucción específica es algo así como: "narrá lo que sucede como respuesta a esta acción, refractado por el cristal del personaje habitado. Mantenete en el momento presente. No avances el tiempo más de lo necesario para que la acción se complete. Si la acción tiene consecuencias inmediatas que requieren decisión del jugador, mostralas pero detenete antes de que el jugador decida". El tier para este template es típicamente 1, salvo que la escena sea claramente dramática (en cuyo caso el motor decide subir a 2).

El template de mutación de información es el segundo en prioridad porque es donde la promesa del proyecto se manifiesta con más claridad. Recibe una versión origen del hecho (cómo lo sabe el emisor), el memetario del receptor que va a recibirla, el contexto del momento de la transmisión, y le pide al LLM que produzca la versión mutada del hecho tal como llegó al receptor. La instrucción es algo así como: "producí una nueva versión de la información tal como esta persona la entiende y la cuenta, dadas sus piedras fundacionales y sus memes activos. La nueva versión puede mantener algunos detalles del origen pero debe reflejar el filtro específico del receptor. No es la misma información, es lo que esta persona específicamente entendió y va a transmitir cuando la cuente". El output de este template debe ser estructurado (Pydantic schema), no texto libre, porque entra al grafo como nodo. El tier es 1.

El template de score es el tercero. Recibe la acción del jugador, el contexto del PJ, el lugar, el antagonista si lo hay, la posición y el efecto ya calculados, el resultado de la tirada (limpio, con costo, mala consecuencia), y le pide al LLM que narre el resultado de la acción con su consecuencia narrativa. La instrucción explicita el resultado y le pide la consecuencia: "el resultado de la acción es éxito con costo. Narrá el éxito y la complicación que esto produce. La complicación no debe ser cosmética, debe cambiar algo del mundo o del personaje que el jugador va a tener que considerar después". El tier es 2 típicamente, 3 para Scores climáticos.

El template de propuesta de hito biográfico es el cuarto. Se invoca después de un Score particularmente intenso o después de eventos que el motor identifica como potencialmente reconfiguradores. Recibe el contexto del evento (qué pasó, dónde, qué memes estaban activos, qué consecuencias hubo), y le pide al LLM que evalúe si el evento amerita un hito y, si sí, que proponga su estructura. El output es estructurado: o devuelve "no amerita hito" o devuelve un objeto hito completo con título, descripción objetiva, experiencia subjetiva, categorías simbólicas, y efectos estructurales propuestos (qué memes inyectar, qué PF modificar, qué deudas morales abrir). El motor valida la propuesta y aplica los efectos. El tier es 2.

El template de resumen de downtime es el quinto. Se invoca cuando el jugador hace un time-jump grande. Recibe las instrucciones del jugador sobre cómo vivió su personaje durante el período, los eventos del mundo que efectivamente le llegaron al personaje según su grafo de conocimiento, las consecuencias diferidas de Scores anteriores, y le pide al LLM que produzca una crónica narrada del período. La instrucción es probablemente la más larga de todos los templates porque tiene que orientar al LLM a tejer múltiples hilos en una sola narración coherente: "produciendo una crónica del tiempo pasado, integrá la rutina del personaje con los eventos relevantes que llegaron a él, con los flashbacks o sueños recurrentes que se activaron, con las consecuencias diferidas. La crónica debe sentirse como un capítulo de novela que cubre semanas, no como un changelog de eventos sueltos". El tier es 2.

El template de descripción de NPC tibio es de menor prioridad pero útil. Se invoca cuando un NPC tibio se enciende por interacción con el jugador y necesita memetario inferido desde sus tags. Recibe los tags del NPC, el contexto de cómo se está encendiendo, y le pide al LLM que proponga la estructura básica del memetario que ese NPC tendría dado sus tags y el mundo. El output es estructurado: un memetario simplificado con dos o tres PF y cuatro o cinco MOs. El tier es 0 o 1 (estos NPCs no son centrales).

## La estructura concreta de un template

Para que sea operativo, te muestro cómo se ve un template en archivo concreto. Esto es ilustrativo, podés tunearlo según prefieras.

```
templates/freeplay.txt
========================
{{voz_narrativa_raiz}}

Estás narrando una escena de Codex Fragmentum. El personaje habitado es {{personaje.nombre}}.

Sus piedras fundacionales activas:
{{#each personaje.pf}}
- {{this.contenido}}
{{/each}}

Sus memes operativos activos en este momento (loadout):
{{#each loadout}}
- {{this.contenido}} (peso: {{this.peso_actual}})
{{/each}}

Sus hitos biográficos relevantes a este contexto:
{{#each hitos_relevantes}}
- {{this.titulo}}: {{this.experiencia_subjetiva}}
{{/each}}

Está actualmente en: {{lugar.nombre}}
{{lugar.descripcion_base}}

Las últimas escenas que vivió:
{{historial_reciente}}

Acaba de hacer la siguiente acción:
{{accion_jugador}}

Narrá lo que sucede como consecuencia inmediata, refractado por el cristal del personaje. Mantenete en el momento presente, no avances el tiempo más de lo necesario para completar esta acción específica. Si la respuesta del mundo abre una nueva decisión para el jugador, mostrala pero detenete antes de que él decida. Tu narración debe sentirse desde adentro del personaje, no desde un narrador omnisciente externo.
```

El sistema de sustitución usado en el ejemplo (con doble llave y bloques each) es similar a Handlebars o Jinja2. Cualquier sistema funciona; lo importante es que sea legible. La sustitución de las variables la hace el motor antes de pasar el prompt al LLM: el motor toma el template como string, lo procesa con los datos del contexto actual, y produce el prompt final.

Para datos estructurados que son listas o diccionarios, conviene formatearlos como bloques claros con encabezados, no como JSON crudo. El LLM lee mejor "estos son sus memes activos: ..." que un JSON serializado. La excepción son los esquemas de output esperado, que sí conviene mostrar como JSON cuando le pedís al LLM que devuelva estructura.

## La iteración sobre templates como práctica

Una vez que tengas templates funcionando, viene la parte que más vas a hacer: iterar sobre ellos. Esta práctica tiene su propia lógica que vale la pena nombrar.

La iteración empieza cuando algo del output no se siente bien. James va a notarlo porque es sensible literariamente. La intervención correcta no es tocar el motor, no es cambiar el modelo, no es ajustar parámetros numéricos: es revisar el template. La pregunta a hacerse es: ¿qué información le falta al LLM en este prompt para hacer mejor su trabajo? O alternativamente: ¿qué información sobra y lo está confundiendo?

Las respuestas típicas son tres. Una, falta contexto: el prompt no le da al LLM datos que necesitaba para entender la situación. Solución: agregar el bloque de contexto faltante (puede ser tan específico como "agregá la lista de hitos del PJ que tienen palabras gatillo presentes en el contexto actual"). Dos, sobra contexto: el prompt lo abruma con datos irrelevantes que diluyen los importantes. Solución: filtrar el contexto para incluir solo lo relevante (puede requerir trabajo en el motor para decidir qué es relevante). Tres, la instrucción está mal calibrada: el LLM está produciendo algo distinto a lo que se quería porque la instrucción es ambigua o incompleta. Solución: reescribir la instrucción específica con más precisión.

La iteración debe quedar registrada. Cuando cambies un template, hacé commit con un mensaje claro de qué problema estabas resolviendo y qué cambiaste. Esto te permite revisar el historial cuando algo se rompe ("desde que cambié el template de mutación, los rumores se sienten más planos") y rollback si hace falta.

Una herramienta que vale la pena programar para el MVP, aunque sea básica: un test runner para templates que toma un input fijo y produce su output, comparando con outputs anteriores. Esto te permite cambiar un template y ver inmediatamente cómo cambia el output sin tener que jugar una sesión entera. Es la diferencia entre iterar en minutos versus iterar en horas.

## Los antipatrones a evitar

Hay un puñado de errores recurrentes que conviene nombrar para que un asistente colaborador los reconozca.

El antipatrón de la voz omnisciente: cuando el template no le dice al LLM que narre desde adentro del personaje y el output sale como narrador externo describiendo lo que el personaje hace. Esto rompe el cristal-piel: la prosa no está refractada, está observando. Solución: la instrucción debe enfatizar "narrá desde adentro del personaje" o "refractado por su cristal".

El antipatrón de la lista de hechos: cuando el output del LLM se siente como recuento de eventos en lugar de prosa narrativa. Esto suele pasar en resúmenes de downtime mal armados. Solución: la instrucción debe pedir explícitamente "narrá como capítulo de novela" o "tejé los hilos en una sola crónica fluida".

El antipatrón de las consecuencias cosméticas: cuando una mala tirada produce narración donde "algo sale mal" pero ese algo no afecta al estado del mundo o del personaje. Solución: la instrucción debe pedir que la consecuencia sea concreta y verificable, mencionando algo que el jugador va a tener que considerar después.

El antipatrón de la disculpa fantasma: cuando el LLM produce frases que rompen la cuarta pared, pidiendo perdón por algo, o haciendo meta-comentarios sobre la narración. Esto suele venir de modelos sobre-entrenados a ser servíciles. Solución: la voz narrativa raíz debe explicitar "nunca rompés la cuarta pared, nunca te disculpás, nunca mencionás que sos una IA". Esto se repite en cada prompt.

El antipatrón de la prosa genérica: cuando el output podría ser de cualquier libro de fantasía promedio, sin la voz específica de Codex. Esto es típicamente el síntoma más común y más difícil de resolver. La solución es múltiple: voz narrativa raíz fuerte, contexto rico que dé al LLM material específico, instrucción que prohíba clichés concretos. Pero la solución profunda viene del skill de estética cuando exista.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera: los templates no son código que escribís una vez y dejás. Son artefactos vivos que se afinan permanentemente. Conviene programar el sistema de modo que cambiar un template sea trivial (archivo separado, hot reload si es posible, sin recompilación).

Segunda: cuando James reporta que el output no se siente bien, la primera hipótesis a investigar siempre es el template, no el motor. La gran mayoría de los problemas de calidad del output se resuelven en el prompt, no en la mecánica. Si después de iterar el template el problema persiste, ahí sí se mira el modelo, el motor, o la arquitectura.

Tercera: cada template es una decisión sobre cuánto contexto darle al LLM. Más contexto generalmente mejora la calidad pero aumenta el costo en tokens y la latencia. Hay un punto de retornos decrecientes donde agregar más contexto no mejora más el output. Encontrarlo requiere iteración y observación. La regla práctica: empezar con contexto generoso, luego ir podando lo que no aporta. Es más fácil quitar que agregar.
