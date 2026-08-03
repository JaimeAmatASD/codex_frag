---
name: codex-fragmentum-llm-prompts
description: Integración con LLMs del proyecto Codex Fragmentum. Cargá cuando el trabajo toque cómo el sistema invoca modelos de lenguaje, qué modelo usar para qué tarea, cómo se estructuran prompts, validación de respuestas, manejo de errores y reintentos, costos. Cargalo también cuando James escriba o itere templates (refracción de información, narración de score, mutación de rumor, propuesta de trauma, cronicón de downtime), decida tier de modelo para una tarea nueva, programe la abstracción del cliente, o aparezcan dudas sobre APIs de modelos generativos. No cubre dirección estética del output (eso es del skill de estética futuro), sino aspectos técnicos. Triggers en inglés — LLM integration, prompt engineering, model tier strategy, structured output validation, Pydantic schemas, prompt templates, API client abstraction, token optimization, model routing. Presupone codex-fragmentum-arquitectura cargado.
---

# Codex Fragmentum — Integración con LLM y prompts

Este skill se ocupa de cómo Codex Fragmentum invoca a los modelos de lenguaje y cómo trabaja con sus respuestas. Si llegaste a este skill, James está trabajando en algún aspecto de la integración técnica con LLMs: el cliente abstraído, los templates de prompts, la validación de respuestas, el manejo de errores, la economía de tokens. Para el contexto general del proyecto, asumí que el skill maestro codex-fragmentum-arquitectura ya está cargado.

Una distinción importante de entrada: este skill cubre la dimensión técnica de la integración con LLMs, no la dirección estética del output narrativo. Cuán literario debe ser un texto, qué referencias estilísticas guían la prosa, cómo se siente una buena refracción versus una plana, todo eso es territorio del skill de estética que James decidió postergar hasta tener experiencia real con el output del sistema. Si la conversación deriva hacia decisiones estéticas, decíselo y proponé que esa parte se trabaje separada (idealmente armando el skill de estética cuando llegue el momento, no improvisando ahora).

## Por qué la integración con LLM es uno de los dos pilares del proyecto

El motor cognitivo del Codex (memetario, refracción, propagación) determina qué información tiene cada personaje y cómo la palpa. El motor de drama (Blades adaptado) determina cómo se resuelven las acciones y se producen consecuencias. Pero ninguno de los dos produce texto. Lo que el jugador efectivamente lee, el output que constituye su experiencia, lo escribe el LLM.

Esto significa que la calidad final del proyecto depende críticamente de tres cosas: que el motor produzca buen contexto para pasarle al LLM, que el LLM tenga capacidad suficiente para producir buen texto desde ese contexto, y que la integración entre ambos sea robusta y económica. Las tres cosas tienen que funcionar. Si el motor produce buen contexto pero el prompt está mal armado, el output es malo. Si el prompt está bien armado pero el modelo es demasiado básico para la tarea, el output es plano. Si el modelo es excelente pero la integración no valida sus respuestas y ocasionalmente falla, el sistema entero se vuelve frágil.

Por eso este skill existe como dominio especializado: la integración con LLM no es trivial, requiere decisiones arquitectónicas específicas, y vale la pena pensarla con cuidado.

## La consigna central: el LLM nunca es la fuente de verdad

Si tuviera que destilar el approach de Codex en una sola frase, sería esta. El motor del Codex tiene el estado del mundo. El motor decide qué pasó, quién sabe qué, cómo se calcula la posición y el efecto, cuándo se completa un clock. El LLM solo narra lo que el motor ya decidió.

Esta consigna es lo que distingue a Codex de proyectos como AI Dungeon donde el LLM efectivamente "es" el motor y "es" el estado. Esa arquitectura tiene problemas serios de coherencia (el LLM olvida cosas, se contradice, inventa cosas que no pasaron) que se vuelven catastróficos en proyectos largos. Codex evita esos problemas por diseño: el LLM puede inventar cómo se siente algo, qué olor tiene, qué metáfora describe el momento, pero no puede inventar que algo pasó. Lo que pasó lo determina el motor.

En la práctica, esto se traduce a una regla operativa clara: cada llamada al LLM recibe contexto estructurado de qué pasó (datos del motor) y le pide que produzca narración. Si el LLM devuelve algo que se sale de los hechos pasados (por ejemplo, narra que el personaje hizo X cuando en realidad hizo Y), el sistema lo detecta y rechaza la respuesta o la corrige. Esta validación es parte del flujo normal, no caso excepcional.

Cuando programes integraciones con LLM, mantené siempre esta jerarquía: motor manda, LLM ilustra. Si te encontrás permitiendo que el LLM tome decisiones sobre el estado del mundo, parate y revisá si eso pertenece al motor.

## Cómo está organizado este skill

Los aspectos detallados de la integración con LLM viven en archivos de referencia separados. La razón es que las distintas dimensiones del problema tocan código distinto y conviene cargarlas según el dominio específico en el que estés trabajando.

El archivo references/tiers-de-modelos.md cubre la estrategia de qué modelo usar para qué tarea, cómo se categorizan las llamadas por peso narrativo, cómo se abstrae el cliente del LLM detrás de una interfaz propia para poder cambiar de proveedor, cómo se manejan los costos. Cargalo cuando el trabajo sea sobre la arquitectura del cliente, decisiones de routing entre modelos, optimización de costos, o cuando aparezca un caso nuevo que necesite asignación de tier.

El archivo references/templates-de-prompts.md cubre cómo se estructura un prompt en Codex, qué bloques debe contener, cómo se hace prompt engineering específico para cada tipo de tarea (refracción, narración de score, mutación de rumor, generación de trauma, resumen de downtime). Cargalo cuando estés escribiendo o iterando templates concretos, o cuando James esté ajustando la calidad del output narrativo.

El archivo references/validacion-y-resilencia.md cubre cómo se usa Pydantic para forzar respuestas estructuradas del LLM, cómo se manejan los casos donde la respuesta no cumple el schema, qué estrategia de retries usar, cómo cachear respuestas que pueden reusarse, cómo testear sin gastar tokens. Cargalo cuando estés programando la lógica de validación, debuggeando errores de respuesta, o tratando de bajar el costo de tokens.

Si vas a trabajar en una pieza específica, lo correcto es cargar este SKILL.md principal más el archivo de referencia correspondiente. Si el trabajo cruza varias dimensiones (por ejemplo, escribir un template nuevo y al mismo tiempo decidir su tier de modelo y su validación), cargá los archivos relevantes simultáneamente.

## Las decisiones arquitectónicas que están tomadas

Conviene listar acá las decisiones del dominio que ya están cerradas, para que un asistente colaborador no las reabra sin razón fuerte.

El cliente de LLM está abstraído detrás de una interfaz propia (Python ABC), con implementaciones concretas para cada proveedor (Gemini, Anthropic, posiblemente OpenAI). Esto es no negociable porque sin esa abstracción, cambiar de proveedor o usar varios simultáneamente requiere reescribir todo el código que llama al LLM. La abstracción incluye también un cliente mock que devuelve respuestas pre-grabadas, esencial para tests sin gastar tokens.

Las llamadas al LLM se categorizan en tiers según el peso narrativo de la tarea, no según el subsistema. Una tarea de refracción de información puede ser tier 1 si es entre NPCs secundarios o tier 2 si es entre el PJ y un NPC principal. La decisión de tier es función del momento, no del módulo de código. Esta política mantiene los costos bajo control sin sacrificar calidad donde importa.

Las respuestas del LLM que requieren formato estructurado se validan con Pydantic. No se confía en que el LLM devuelva JSON bien formado: se valida explícitamente y se reintenta con feedback del error si falla. La estrategia de retries es máximo dos intentos antes de fallar al motor, con la lógica que si el LLM no produce respuesta utilizable después de dos intentos, hay un problema más profundo que reintentar más veces no va a resolver.

Los templates de prompts viven como archivos de texto separados (típicamente en una carpeta prompts/) y no hardcodeados en el código Python. Esto permite editarlos sin tocar código, lo cual es crítico porque vas a iterar mucho sobre ellos. Los templates usan algún sistema de sustitución (puede ser f-strings de Python o Jinja2) que permita inyectar el contexto estructurado en posiciones específicas del prompt.

El sistema de caché es opcional para el MVP pero conviene programar las llamadas al LLM de modo que sean cacheables (claves derivables del input + modelo + tier). Algunas respuestas son cacheables (descripciones de objetos que no cambian, narraciones de lugares vistos por primera vez por un personaje específico), otras no (cualquier cosa que dependa del estado actual del mundo o del personaje).

## Recordatorios operativos transversales

Cuando James trabaje en este territorio, cuatro cosas conviene tener siempre presentes.

Primera: la calidad del output del LLM es el techo de la calidad del proyecto. Si el motor es brillante pero el LLM produce texto mediocre, el jugador experimenta mediocridad. Esto significa que cuando James reporte "algo no se siente bien", la primera hipótesis a investigar suele ser "¿el prompt está bien armado y el modelo es apropiado?", antes de tocar el motor. Muchas veces el problema es de prompt, no de mecánica.

Segunda: los costos de LLM se acumulan más rápido de lo que la intuición sugiere. Una sesión de juego de una hora puede fácilmente hacer cincuenta o más llamadas al modelo. Si todas son tier 3, los costos se vuelven impagables. La estrategia de tiers no es decoración, es lo que vuelve económicamente viable el proyecto. Cuando aparezca la tentación de subir todas las llamadas a tier alto "para que la calidad sea consistente", recordar que la calidad consistente al máximo no es alcanzable económicamente.

Tercera: testear con el cliente mock es no opcional. Los tests automáticos del proyecto no pueden depender de llamadas reales al LLM porque cada corrida de tests gastaría dinero y sería lenta. El mock client devuelve respuestas pre-grabadas que permiten testear el flujo del motor sin tocar APIs externas. Cualquier código que llame al LLM debe poder ser testeado con el mock.

Cuarta: el comportamiento del LLM puede cambiar entre versiones del modelo. Anthropic, Google y otros proveedores actualizan sus modelos periódicamente, y los outputs pueden cambiar de formato, calidad o tono. Esto significa que los templates y las validaciones tienen que ser robustos a pequeñas variaciones, y que conviene loggear las respuestas del LLM en producción para detectar regresiones cuando una actualización del modelo cambia el comportamiento. Si algo dejó de funcionar y nada cambió en el código, lo primero a verificar es si el modelo subyacente cambió.
