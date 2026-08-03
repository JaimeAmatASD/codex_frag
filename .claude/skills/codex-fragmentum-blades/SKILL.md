---
name: codex-fragmentum-blades
description: Motor de drama de Codex Fragmentum, basado en Blades in the Dark adaptado a contexto narrativo solitario con LLM como narrador. Cargá cuando el trabajo toque las mecánicas que producen drama — tres fases de juego (free play, score, downtime), resolución de tiradas con tres resultados, posición y efecto, sistema de stress y trauma con acoplamiento al memetario, vicios como vectores de información, clocks de progreso. Cargalo también cuando James decida si una situación es Score formal o free play, cuando tunee umbrales mecánicos, escriba prompts que reciben categorías de tirada, o aparezcan dudas sobre cómo Codex difiere de Blades canónico. Triggers en inglés — Blades adaptation, drama engine, score resolution, position and effect, stress system, trauma as injected meme, progress clocks, three-tier dice resolution, vice as information vector. Presupone codex-fragmentum-arquitectura cargado.
---

# Codex Fragmentum — Motor de drama (Blades adaptado)

Este skill se ocupa exclusivamente del motor de drama mecánico del proyecto. Si llegaste a este skill, James está trabajando en alguna de las mecánicas que producen drama narrativo confiable: tiradas, stress, vicios, clocks. Para el contexto general del proyecto, asumí que el skill maestro codex-fragmentum-arquitectura ya está cargado. Si no lo está y necesitás contexto general, pedile a James cargarlo.

## Por qué Blades y por qué adaptado

El motor cognitivo del Codex (memetario, refracción, propagación de información) puede producir un mundo que se siente vivo pero no necesariamente un mundo que se siente dramático. La simulación pura tiende a producir eventos sin tensión: pasan cosas, pero no se sienten como historia. La buena ficción requiere drama: decisiones que importan, consecuencias que duelen, resoluciones que cambian algo.

Blades in the Dark, el juego de rol diseñado por John Harper, es probablemente el mejor sistema mecánico jamás escrito para producir drama narrativo de forma confiable. Cada uno de sus subsistemas existe para empujar la ficción hacia adelante: las tiradas no admiten "no pasa nada", el stress fuerza decisiones que pesan, los clocks vuelven visible el progreso de las amenazas. Codex Fragmentum toma esos subsistemas y los adapta a un contexto narrativo solitario con LLM como narrador.

La adaptación implica algunos cambios importantes que conviene tener presentes desde el principio para no caer en la trampa de aplicar Blades canónico literal. Codex no usa playbooks fijos como Cutter, Hound, Lurk: los arquetipos son fluidos, definidos por el memetario del personaje, no por hojas de personaje cerradas. Codex no tiene crews de ladrones cooperativos: el jugador habita un personaje a la vez, en sesiones solitarias. La consecuencia más profunda de la adaptación es que en Codex los traumas no son etiquetas que se acumulan hasta el retiro del personaje, sino que se inyectan como memes experimentales en el memetario y pueden ascender a operativos o incluso modificar piedras fundacionales. Esa integración entre el motor de drama y el motor cognitivo es lo más distintivo del proyecto.

Si en algún momento te encontrás recomendando algo que pertenece a Blades canónico pero no a Codex (un Heist con planning fase, un Crew con upgrade tracks, un Faction game completo), parate y verificá si tiene sentido en este contexto. La mayoría de las veces no.

## Las tres fases de juego

Esta es la única mecánica de Blades que aplica transversalmente a todo el sistema y por eso vive en el SKILL.md principal y no en un archivo de referencia separado. Si James está trabajando en cualquier mecánica de drama, va a necesitar saber en qué fase está.

El juego no es un flujo continuo de acciones idénticas. Está estructurado en tres fases que se alternan, y cada una tiene su propio ritmo, su propia función dramática y su propio costo de LLM.

La fase de free play es donde el jugador conversa, explora, toma decisiones cotidianas. El personaje camina por el pueblo, habla con NPCs, observa, oye rumores. El LLM narra refractado por el cristal del personaje pero las llamadas son de tier bajo (modelos rápidos y baratos como Gemini Flash). No hay tiradas formales. Es donde el mundo se respira, donde los personajes construyen relación, donde las pistas se siembran.

La fase de score es la acción focal. El jugador identifica algo concreto que quiere lograr (sonsacarle un secreto al tabernero, infiltrarse en el monasterio, ejecutar un ritual prohibido, sobrevivir a un encuentro con algo que el mar trajo). Esa acción se resuelve con la mecánica formal: cálculo de posición y efecto, tirada de dados con tres resultados posibles, narración del resultado con LLM tier alto. Es la fase donde el drama es explícito y donde se gasta más en LLM.

La fase de downtime es la recuperación, la rutina, el paso del tiempo. El jugador descansa, visita su vicio, trabaja en proyectos largos, deja pasar días o semanas. El LLM produce resúmenes (tier medio) y el motor avanza clocks, simula eventos pasivos, propaga rumores con cálculos baratos.

El ritmo natural de una sesión es alternar fases. No hay regla rígida sobre cuándo cambiar: lo decide el jugador implícitamente cuando declara una acción focal o cuando dice "dejo pasar tiempo". Una sesión típica podría ser: free play, free play, score, downtime corto, free play, free play, score grande, downtime largo. El sistema detecta el cambio de fase y aplica la mecánica correspondiente.

Cuando James esté programando, tener claras las fases le ayuda a decidir qué módulos están involucrados en cada momento. En free play, el motor cognitivo refracta y el LLM narra. En score, además entran las mecánicas de tiradas, posición/efecto, stress. En downtime, además entran los vicios, los clocks pasivos, la simulación lazy del mundo.

## Cómo está organizado este skill

Los subsistemas detallados del motor de drama viven en archivos de referencia separados, no en este SKILL.md principal. La razón es que James trabaja modularmente: cuando programa el sistema de tiradas, no necesita simultáneamente el detalle completo del sistema de stress en el contexto. Cargar todo siempre sería desperdicio y ruido.

El archivo references/tiradas.md cubre la resolución de acciones con sus tres categorías de resultado, el cálculo de posición y efecto cruzando memetarios, los atributos del personaje y la cantidad de dados que se tira en cada acción. Cargalo cuando el trabajo sea sobre cómo se resuelven mecánicamente las acciones del PJ.

El archivo references/stress-y-trauma.md cubre la barra de stress, los empujones que el jugador puede hacer pagando estrés, el sistema de trauma extendido que inyecta memes experimentales en el memetario, y la posibilidad de modificación de piedras fundacionales por traumas solidificados. Cargalo cuando el trabajo toque cómo el personaje acumula carga psíquica y cómo eso lo modifica con el tiempo.

El archivo references/vicios-y-downtime.md cubre el sistema de vicios como mecanismo de descarga de stress y simultáneamente como vector de propagación de información, las actividades de downtime, el funcionamiento de la fase de downtime corta versus larga. Cargalo cuando el trabajo sea sobre las mecánicas que pasan entre Scores.

El archivo references/clocks.md cubre los clocks de progreso, sus tipos (propagación, divinos, políticos, personales, ambientales), la lógica de triggers que los avanzan, qué pasa cuando se completan, y la decisión de visibilidad para el jugador. Cargalo cuando el trabajo sea sobre cómo se modela el avance del tiempo y de las amenazas en el mundo.

Si vas a trabajar en una pieza específica, lo correcto es cargar este SKILL.md principal más el archivo de referencia correspondiente. Si vas a hacer trabajo transversal que toca varios subsistemas a la vez, cargá los que sean relevantes. Si tenés dudas sobre cuál cargar, mejor cargar de más que de menos: la información extra no daña, la información faltante sí.

## El estatus de este sistema: enchufable, no núcleo (ADR-002)

Una precisión importante que corrige versiones anteriores de este skill: el sistema de reglas NO es parte del núcleo de Codex. Por decisión registrada en el ADR-002, es una capa enchufable detrás de una interfaz: el núcleo (memetario, mundo, información) provee servicios cognitivos y de estado, y el sistema de reglas los consume para resolver acciones dramáticas. Blades es la PRIMERA implementación de esa interfaz y la del MVP, pero cada autor que use el engine podrá reemplazarla por otro sistema. Codex sin Blades sigue siendo Codex; Blades es una opción excelente, no la esencia.

Esto tiene una consecuencia práctica al programar: la lógica de Blades vive del lado del enchufe, nunca incrustada en el núcleo cognitivo ni en el mundo. Si te encontrás metiendo conceptos de Blades (stress, posición, clocks) dentro del memetario o del grafo del mundo, parate: va en el módulo de reglas, comunicándose por la interfaz. La salvedad anti-sobreingeniería del ADR también aplica: la interfaz es la mínima que Blades necesita, no una abstracción universal de sistemas de juego; se generaliza recién cuando exista un segundo sistema real.

Dicho el estatus, el valor sigue intacto: dentro del MVP, el drama que Blades aporta es lo que convierte un mundo vivo en una historia vivible. La simulación pura produce eventos; el drama produce historia. Por eso Blades es la primera opción y se construye con cuidado.

## Cómo se acopla con el motor cognitivo

La pregunta que conviene hacerse cuando diseñes cualquier mecánica de drama es: ¿cómo alimenta esto al memetario, y cómo es alimentado por él? Las dos columnas no operan en paralelo: están entretejidas.

El memetario alimenta al drama proveyendo los modificadores que entran en el cálculo de posición y efecto. Un personaje cuyas piedras fundacionales chocan con la situación está en peor posición. Un personaje cuyos memes operativos se subsidian en este lugar tiene mejor efecto.

El drama alimenta al memetario inyectando memes experimentales cuando los traumas se acumulan, reforzando memes que se activaron durante Scores exitosos, modificando piedras fundacionales cuando los traumas se solidifican lo suficiente como para producir crisis biográfica.

Esta circularidad es la que produce arcos de personaje emergentes. El personaje que arranca como pescador tranquilo, después de varios Scores violentos en los que su stress se llenó, termina con memes experimentales de violencia que se solidificaron, y eventualmente con piedras fundacionales modificadas. No hay pantalla de creación de personaje donde se elija "ahora soy guerrero": el personaje se va construyendo solo a través del juego.

Cuando programes cualquier subsistema de drama, asegurate de no romper este acoplamiento. Si el sistema de stress no produce traumas que afectan al memetario, perdés el camino emergente. Si los Scores no usan modificadores del memetario para calcular posición/efecto, perdés la singularidad del personaje. Cada pieza del drama tiene su correspondencia con el motor cognitivo y conviene tenerlas a la vista.

## Recordatorios operativos

Cuando James trabaje en este territorio, dos cosas te conviene tener presentes constantemente.

Primera: la regla de las tres categorías de resultado no es opcional. Cualquier acción que se resuelve con tirada produce uno de tres resultados (limpio, con costo, mala consecuencia). Si te encontrás diseñando algo donde una acción puede "no producir nada", estás violando la columna vertebral del sistema. Reformulá hasta que cada resolución produzca consecuencia narrativa.

Segunda: los clocks no son temporizadores genéricos, son el mecanismo principal de avance del mundo. Si te encontrás pensando "habría que simular X durante el time-jump", probablemente la respuesta correcta es "armemos un clock para X". Los clocks son baratos, son verificables, son visibles cuando conviene, son la herramienta nativa de Codex para todo lo que cambia en el mundo gradualmente.

Si James te pide algo que no encaja en ningún archivo de referencia (por ejemplo, una mecánica nueva que no es ni tirada, ni stress, ni vicio, ni clock), eso es probablemente señal de que está derivando hacia mecánica que no es de Blades adaptado. Decíselo: "esto no parece encajar en los subsistemas de Blades, ¿estás seguro de que pertenece al motor de drama o quizá pertenece a otro skill?".
