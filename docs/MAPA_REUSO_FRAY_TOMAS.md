# Codex Fragmentum — Mapa de reuso desde Fray Tomás
## Qué se reutiliza, qué se adapta, qué se construye nuevo
*Documento de arquitectura — Junio 2026*

---

## Para qué existe este documento

Una de las decisiones que más condiciona el esfuerzo real de Codex Fragmentum es cuánto del motor cognitivo de Fray Tomás es efectivamente reutilizable. Si gran parte se reusa, el MVP es cuestión de semanas. Si hay que reescribir casi todo, es cuestión de meses. Este documento responde esa pregunta componente por componente, basado en la lectura de los tres documentos técnicos de Fray Tomás (resumen del alma, resumen técnico, mejoras técnicas).

El documento clasifica cada pieza en una de tres categorías. Reutilizable directo significa que el código de Fray Tomás se puede importar o copiar con cambios mínimos. Adaptable significa que la lógica sirve pero hay que modificarla porque Codex tiene requisitos que Fray Tomás no tiene. Nuevo significa que Codex necesita algo que Fray Tomás no tiene en absoluto y hay que construir desde cero.

Una advertencia honesta sobre la confiabilidad de este mapa. Está hecho leyendo documentación de Fray Tomás, no su código real. La documentación describe la arquitectura pero el código puede diferir en detalles. Antes de tomar decisiones de esfuerzo basadas en este mapa, conviene que James verifique contra el código real de Fray Tomás cuáles piezas están efectivamente implementadas y cuáles eran diseño o mejora planeada. El propio documento de mejoras técnicas sugiere que algunas cosas (embeddings, ritmo circadiano, memoria episódica) podrían ser propuestas todavía no implementadas al momento de escribir esos documentos en marzo 2026.

---

## Diferencia estructural de fondo entre los dos proyectos

Antes de ir componente por componente, conviene entender la diferencia arquitectónica grande, porque explica por qué algunas cosas se reusan tal cual y otras necesitan adaptación profunda.

Fray Tomás es un agente único. Hay un solo memetario, un solo cuerpo cognitivo, una sola identidad que evoluciona. Todo el sistema está construido alrededor de servir a ese agente: el DIARIUM es su diario, el Consejo son sus voces internas, el SPECULUM es su autorreflexión. La arquitectura es monolítica en el sentido de que asume un solo sujeto.

Codex Fragmentum es multi-agente. Hay muchos cuerpos cognitivos simultáneos, con estratificación de profundidad (PJ completo, NPCs principales, secundarios, tibios, multitudes). El mismo motor cognitivo tiene que servir a decenas o cientos de agentes a la vez, cada uno con su memetario, su corpus, su estado. La arquitectura tiene que ser multiplicable.

Esta diferencia es la lente principal para leer todo el mapa. Lo que en Fray Tomás es una instancia única, en Codex tiene que volverse una clase instanciable muchas veces. La buena noticia es que esa transformación (de instancia única a clase instanciable) es de las más limpias en programación: si el código de Fray Tomás está razonablemente modularizado, envolver su memetario en una clase que se puede instanciar por agente es trabajo mecánico, no rediseño.

---

## El motor cognitivo central

### El memetario como estructura de datos — REUTILIZABLE DIRECTO

La estructura del memetario de Fray Tomás (nodos con sus atributos, aristas con sus relaciones, las tres capas de PF, MO y experimentales) es exactamente lo que Codex necesita para cada agente. El esquema JSON de un meme (id, tipo, contenido, peso_base, peso_actual, costo_mana, decae, estado, embedding, contra_meme, pregunta_control, cuando_no_usar) se traslada casi sin cambios.

La única adaptación necesaria es de empaquetado, no de contenido: en Fray Tomás el memetario es un archivo global (memetario.json). En Codex cada agente tiene su propio memetario, así que la estructura pasa de ser un singleton a ser un campo de cada agente. Esto es el cambio de instancia única a clase instanciable mencionado arriba. El contenido de cada meme no cambia, cambia dónde vive.

Recomendación: tomar el esquema de meme de Fray Tomás tal cual, envolverlo en el modelo Pydantic de Memetario que ya está esbozado en el documento técnico de Codex, e instanciarlo por agente. Esfuerzo bajo.

### El cálculo de loadout — REUTILIZABLE DIRECTO con una salvedad

La fórmula de selección de loadout de Fray Tomás (score combinando peso histórico al 60%, similitud semántica al 40%, multiplicado por bias circadiano, ordenando descendente y llenando hasta el límite de mana) es exactamente la que Codex necesita. El documento técnico de Codex de hecho ya la incorporó porque venía de Fray Tomás.

La salvedad es la que ya discutimos largamente en la conversación: Codex agrega los modificadores de costo del lugar (la coproducción agente-mundo). En Fray Tomás el costo de un meme es fijo. En Codex el costo efectivo depende del lugar donde está el agente, sumando los modificadores que el memetario simbólico del lugar aplica a las categorías del meme. Esto es una adaptación acotada: la función de cálculo de loadout recibe un parámetro nuevo (el lugar) y suma los modificadores antes de comparar contra el mana disponible.

Recomendación: reusar la función de loadout de Fray Tomás, agregarle el parámetro de lugar y la suma de modificadores. Esfuerzo bajo a medio.

### El decaimiento — REUTILIZABLE DIRECTO

La fórmula de decaimiento de Fray Tomás (factor_decaimiento asintótico que nunca llega a cero, factor_exito que refuerza con activaciones, PF que no decaen) se traslada sin cambios. La única diferencia operativa es de escala: Fray Tomás aplica decaimiento a un memetario, Codex tiene que aplicarlo a muchos. Eso es un bucle sobre agentes, no un cambio de lógica.

Hay una consideración de rendimiento que aparece solo en Codex por la escala. Aplicar decaimiento diario a un solo agente es trivial. Aplicarlo a cientos de agentes principales cada día del mundo puede empezar a pesar. La solución es aplicar decaimiento lazy (recalcular el peso de un meme solo cuando se va a usar, en lugar de barrer todos los memes de todos los agentes cada día). Pero esto es optimización para cuando el mundo escale, no para el MVP. Para el MVP con pocos agentes, el barrido directo de Fray Tomás funciona igual.

Recomendación: reusar la fórmula tal cual. Diferir la optimización lazy hasta que la escala la justifique. Esfuerzo bajo.

### Los embeddings — REUTILIZABLE DIRECTO (si están implementados)

El sistema de embeddings (modelo all-MiniLM-L6-v2 local, vectorización de textos, similitud coseno, caché de vectores) es idéntico a lo que Codex necesita. Codex usa embeddings para lo mismo (selección de loadout por similitud semántica) más usos nuevos (distancia de versiones en el árbol de mutación de hechos, selección de qué rumores entrega un vicio).

Acá es donde la advertencia sobre verificar contra el código real importa más. El documento de mejoras técnicas de Fray Tomás presenta los embeddings como Mejora 1, prioridad alta, descrita como trabajo a hacer. Si al momento de leer esto los embeddings ya están implementados en Fray Tomás, se reusan directo. Si todavía eran propuesta, hay que implementarlos, pero el documento de mejoras ya tiene el plan completo (módulo embeddings.py, flujo técnico, instalación). En cualquier caso el esfuerzo es bajo porque sentence-transformers hace el trabajo pesado.

Recomendación: verificar si están implementados en Fray Tomás. Si sí, reusar. Si no, implementar siguiendo el plan del documento de mejoras. Esfuerzo bajo en ambos casos.

### El bias circadiano — REUTILIZABLE DIRECTO con reinterpretación conceptual

La función de bias circadiano de Fray Tomás (multiplicadores por tipo de meme según la hora del día) es código trivial de reusar. Pero conviene pensar qué significa en Codex, porque el contexto es distinto.

En Fray Tomás el bias circadiano usa la hora real del mundo (la Pi sabe qué hora es en Mallorca). Tiene sentido: Fray Tomás vive en tiempo real, de noche está contemplativo. En Codex el tiempo es del mundo ficcional, no del reloj real. Un personaje puede estar viviendo su mediodía mientras James juega a medianoche. Entonces el bias circadiano de Codex debe usar la hora del mundo del juego, no la hora real.

Esto es adaptación menor (cambiar de qué reloj lee la hora) pero conceptualmente importante. Y abre una posibilidad interesante: distintos personajes en distintas zonas horarias del mundo podrían tener biases distintos simultáneamente. Para el MVP esto es innecesario (un solo pueblo, una sola hora), pero el diseño debería contemplar que el bias lee la hora del mundo del agente, no una hora global.

Recomendación: reusar la función, cambiar la fuente de la hora de real a hora-del-mundo. Esfuerzo bajo.

### El umbral de Piedras Fundacionales — ADAPTABLE

El mecanismo de Fray Tomás para activar las PF por umbral (detección de palabras de conflicto ético o incertidumbre en el contexto) sirve conceptualmente pero necesita repensarse para Codex.

En Fray Tomás las PF se activan cuando hay un dilema ético real, porque Fray Tomás es un agente moral que decide acciones con consecuencias. El umbral por palabras clave de conflicto tiene sentido para él.

En Codex las PF cumplen un rol distinto. No son principalmente un tribunal moral que se convoca ante dilemas, son la postura cognitiva de fondo desde la cual el personaje palpa todo. Un personaje no necesita un dilema ético para que sus PF operen: sus PF están siempre tiñendo cómo ve el mundo. Esto significa que el mecanismo de umbral por palabras clave es menos central en Codex, o cumple una función más acotada (quizás para disparar momentos de deliberación consciente del personaje, pero no para la operación normal).

Recomendación: revisar conceptualmente qué rol juega el umbral de PF en Codex antes de reusar el mecanismo. Posiblemente se simplifique o se reserve para casos específicos. Esfuerzo de diseño medio, de código bajo.

---

## Los sistemas de identidad y memoria

### El Consejo Interno (4 voces) — ADAPTABLE, con potencial inesperado

El Consejo de Fray Tomás (Operativo, Pastor, Custodio, Escribano debatiendo antes de decisiones, cada uno una llamada al LLM) es uno de los sistemas más interesantes para Codex, pero no de la forma obvia.

En Fray Tomás el Consejo sirve para que un agente moral tome decisiones deliberadas con múltiples perspectivas. En Codex, la mayoría de los personajes no necesitan un consejo de cuatro voces para cada acción: sería carísimo en LLM (cuatro llamadas por decisión por personaje) e innecesario para un pescador decidiendo si va a la taberna.

Pero el patrón del Consejo tiene un uso natural en Codex que el documento de arquitectura ya insinuó: los dioses. Un dios decidiendo cómo intervenir en el mundo es exactamente el tipo de decisión que se beneficia de múltiples voces internas debatiendo. Y los dioses son pocos, así que el costo de cuatro llamadas por decisión divina es aceptable. El Consejo de Fray Tomás podría reaparecer en Codex como el mecanismo de deliberación de los dioses, posiblemente con roles distintos apropiados a cada dios.

Recomendación: no usar el Consejo para personajes comunes. Considerar adaptarlo como mecanismo de deliberación divina. Esfuerzo de adaptación medio, pero diferible a la fase donde los dioses entren en juego (no es del MVP).

### El DIARIUM — ADAPTABLE parcialmente

El DIARIUM de Fray Tomás (registro de qué hizo, cómo lo vivió, en tres niveles: operativo, personal, SPECULUM) es un sistema de memoria autobiográfica de un agente único. En Codex la situación es distinta y conviene separar.

El PJ del jugador podría beneficiarse de algo como el DIARIUM: un registro de su trayectoria que sirve para que el sistema entienda quién se fue volviendo el personaje. Esto conecta con el sistema de hitos biográficos de Codex, que es esencialmente una versión más estructurada del DIARIUM personal. Los hitos de Codex y el DIARIUM de Fray Tomás resuelven el mismo problema (memoria de los eventos que marcan al personaje) con vocabulario distinto.

Los NPCs no necesitan DIARIUM completo. Sería carísimo y narrativamente innecesario que cada NPC mantenga un diario reflexivo. Para los NPCs alcanza con su lista de hitos (más compacta) y su registro de qué información conocen (el grafo).

Recomendación: no reusar el DIARIUM como sistema general. Tomar su concepto de memoria autobiográfica y materializarlo en el sistema de hitos biográficos para el PJ y los NPCs principales. El SPECULUM (autorreflexión que propone cambios) es claramente diferible: es funcionalidad de fase avanzada, no de MVP. Esfuerzo: el concepto ya está absorbido en el diseño de hitos de Codex.

### La memoria episódica con consolidación nocturna — ADAPTABLE, diferible

El sistema de Fray Tomás de consolidar entradas del DIARIUM por similitud semántica cada noche (agrupar lo parecido, sintetizar en memorias más abstractas, como el sueño) es elegante y tiene análogo en Codex, pero es claramente de fase avanzada.

En Codex la consolidación de memoria tendría sentido para personajes que acumulan mucha historia a lo largo de muchas sesiones. El PJ del jugador después de cincuenta horas de juego podría beneficiarse de que sus recuerdos viejos se consoliden en memorias más abstractas, liberando detalle pero conservando esencia. Pero esto es un problema que solo aparece después de mucho juego, no en el MVP.

Recomendación: diferir completamente. Es funcionalidad para cuando el sistema tenga personajes con historia larga. El mecanismo de Fray Tomás (agrupar por similitud, sintetizar con LLM) se reusa cuando llegue el momento. No es del MVP ni de las primeras iteraciones.

---

## Los mecanismos emergentes (hallazgos del resumen del alma)

Dos mecanismos del documento del alma de Fray Tomás merecen sección propia porque son directamente relevantes para Codex y de los más valiosos para reusar. No estaban en los otros documentos técnicos con el mismo detalle.

### La arquitectura de demons con clusters emergentes — REUTILIZABLE como concepto, ALTO VALOR

Esta es probablemente la pieza conceptual más valiosa que Fray Tomás le aporta a Codex después del motor cognitivo básico. Fray Tomás modela la formación de carácter mediante clusters de memes que se coactivan repetidamente y se solidifican con el tiempo, siguiendo la regla de Hebb (lo que se activa junto permanece junto). Demons son esos clusters que se forman alrededor de tipos de situación.

Esto es exactamente el mecanismo que Codex necesita para que sus personajes desarrollen carácter emergente y no solo cambien por hitos puntuales. En la conversación habíamos hablado de bloques de memes que se coactivan (el ejemplo de amaos los unos a los otros más siempre fui buen panadero produciendo hacer pan como acto de amor). Eso es exactamente la arquitectura de demons de Fray Tomás. Resulta que el mecanismo ya está diseñado en Fray Tomás, no hay que inventarlo.

Para Codex esto significa que la formación de carácter de un personaje a lo largo del juego no es solo la acumulación de hitos y el ajuste de pesos, sino también la solidificación de clusters de memes que se activan juntos. Un personaje que repetidamente coactiva ciertos memes en ciertas situaciones va formando demons que lo definen, igual que Fray Tomás. Esto enriquece muchísimo la evolución de personajes y conecta con la idea de carácter emergente que es central al proyecto.

El documento de mejoras técnicas, sin embargo, no lista los clusters entre las mejoras implementadas, y el resumen del alma los presenta como diseño. Así que probablemente sea diseño no implementado todavía en Fray Tomás. Eso significa que para Codex es construcción nueva, pero con el diseño conceptual ya hecho.

Recomendación: incorporar la arquitectura de demons al diseño del memetario de Codex como mecanismo de formación de carácter, complementario a los hitos. Verificar si está implementado en Fray Tomás. Probablemente sea construcción nueva guiada por diseño existente. Es funcionalidad de fase intermedia, no de MVP (requiere acumulación de juego para que los clusters se formen), pero el diseño debe contemplarla desde el principio. Esfuerzo de diseño bajo (ya está pensado), de construcción medio, diferible.

### La temperatura emocional — ADAPTABLE, valiosa para la narración

Fray Tomás incorpora, siguiendo a Damasio, la idea de que el memetario tiene temperatura emocional: lo que el agente reporta sentir es dato válido del razonamiento, no decoración. Se toma en serio (heterofenomenología de Dennett) y se registra.

Para Codex esto es directamente relevante a la calidad narrativa. Un personaje cuyo estado emocional es dato del sistema (no solo del LLM improvisando) produce narración más coherente. Si el sistema sabe que un personaje está cargado emocionalmente respecto a cierto tema (porque sus memes asociados tienen temperatura alta), el LLM puede narrarlo con esa carga. Esto conecta con el sistema de stress de Blades pero es distinto: el stress es un recurso mecánico, la temperatura emocional es coloración del memetario.

Hay una conexión interesante con el corpus que diseñamos. La postura de un personaje hacia su corpus (venera, desconfía, recibió como dogma) es una forma de temperatura emocional aplicada al conocimiento. El marxista que recibió a Marx como dogma frío tiene temperatura distinta hacia su corpus que el que lo descubrió con pasión. La temperatura emocional de Fray Tomás generaliza esto a todo el memetario.

Recomendación: incorporar la temperatura emocional como atributo de los memes en Codex (un meme no solo tiene peso, tiene carga emocional). Usarla para colorear la narración. Es adaptación de bajo esfuerzo (un campo más en el meme) con alto retorno narrativo. Diferible del MVP pero barata de contemplar en el diseño.

### El juicio trágico y las deudas morales — ADAPTABLE, principalmente para PJ y dioses

Fray Tomás modela (siguiendo a Berlin) que a veces dos valores buenos son incompatibles y hay que elegir con pérdida real, registrando la deuda moral. Esto es rico para Codex pero acotado a ciertos agentes.

Para el PJ del jugador, las deudas morales son material narrativo potente: decisiones donde el personaje sacrificó algo valioso y eso queda como peso. Conecta con los hitos biográficos (una deuda moral grande puede ser un hito) y con el sistema de stress (las deudas no resueltas pueden cargar). Para los dioses, el juicio trágico es apropiado a su escala de decisiones. Para NPCs comunes es probablemente demasiado.

Recomendación: adaptar las deudas morales para el PJ y los dioses, integradas con hitos y stress. No para NPCs comunes. Diferible del MVP. Esfuerzo medio.

---

## La integración con LLM

### La arquitectura de llamadas — ADAPTABLE hacia algo más sofisticado

Fray Tomás llama a un solo modelo (Gemini 2.5 Flash) para todo el razonamiento profundo, con la filosofía de minimizar llamadas y hacer todo lo posible localmente. Codex necesita algo más sofisticado: la estrategia de tiers de modelos (tier 0 a 3 según peso narrativo) que ya está diseñada en el skill de prompts.

El principio de fondo de Fray Tomás (hacer localmente todo lo posible, llamar al LLM solo para lo que lo necesita) es exactamente correcto y Codex lo hereda. Pero Codex lo extiende: en lugar de un solo modelo para todo lo que pasa el filtro local, Codex rutea a distintos modelos según la importancia narrativa del momento.

Recomendación: heredar la filosofía de minimización de llamadas. Construir nueva la capa de routing por tiers, que Fray Tomás no tiene porque no la necesita. Esfuerzo: la filosofía se reusa, la implementación de tiers es nueva pero está diseñada.

### El clasificador de intención local — REUTILIZABLE DIRECTO (si está implementado)

El clasificador de intención de Fray Tomás (usar embeddings para clasificar si una situación es ética, operativa, técnica, emocional, por similitud con ejemplos, sin entrenar nada) es una técnica que Codex puede reusar en varios lugares. Por ejemplo, para clasificar si una acción del jugador es free play o amerita un Score, o para decidir el tier de modelo apropiado a una situación.

Recomendación: reusar la técnica de clasificación por similitud. Aplicarla a las decisiones de clasificación que Codex necesita. Esfuerzo bajo.

---

## La persistencia

### El modelo de archivos — REUTILIZABLE DIRECTO como filosofía

La estrategia de persistencia de Fray Tomás (SQLite para datos duros y actas, NetworkX más JSON para el grafo de memes, JSON para memoria de trabajo, todo en archivos portables) es exactamente la filosofía que Codex adopta. El documento técnico de Codex ya la heredó.

La diferencia es de organización: Fray Tomás persiste un solo agente, Codex persiste un mundo entero con muchos agentes, lugares, hechos, partidas. La estructura de directorios es más compleja en Codex (la del documento técnico, con mundos, lugares, agentes, hechos, dioses, partidas separados). Pero el principio (todo en archivos, portable copiando carpeta, SQLite para queries rápidas, JSON para legibilidad) es idéntico.

Recomendación: heredar la filosofía de persistencia tal cual. Expandir la organización de directorios a la estructura multi-entidad de Codex. Esfuerzo bajo a medio.

---

## Lo que Codex necesita y Fray Tomás no tiene en absoluto

Estas son las piezas nuevas, las que hay que construir desde cero porque no existen en Fray Tomás. Es importante tenerlas claras porque son donde está el grueso del esfuerzo real del proyecto.

### El grafo de información con árboles de mutación — NUEVO

Fray Tomás no tiene nada parecido a la propagación de información mutante entre agentes, porque es un agente único: no hay a quién transmitirle información deformada. Todo el sistema de hechos del mundo, árboles de mutación, propagación entre agentes vía encuentros, búsqueda de qué versión conoce cada agente, es completamente nuevo. Es probablemente el componente más distintivo de Codex y el que más trabajo nuevo requiere.

### La grilla espacial jerárquica — NUEVO

Fray Tomás no tiene espacio. Vive en una Pi, no en un mundo con geografía. Toda la grilla jerárquica, la carga lazy de celdas, las velocidades de propagación por nivel, es nueva.

### El memetario simbólico de lugares — NUEVO

La idea de que los lugares tienen memetario propio y modifican los costos de los memes de quienes los habitan no existe en Fray Tomás. Es la coproducción agente-mundo, completamente nueva.

### El motor de drama (Blades) — NUEVO

Fray Tomás no tiene mecánicas de juego. No hay tiradas, posición, efecto, stress, vicios, clocks. Todo el motor de Blades adaptado es nuevo.

### El sistema de corpus por entidad — NUEVO (aunque con raíces en Fray Tomás)

El corpus con sus tres dimensiones (profundidad, fidelidad, postura) que discutimos en la conversación es nuevo, pero tiene una raíz conceptual en Fray Tomás. Fray Tomás ya tiene PF que beben de textos concretos (la Regla de San Benito, las parábolas de Lucas, los poemas de Borges). En cierto sentido, las PF de Fray Tomás ya son un corpus rudimentario: ideas-fuerza derivadas de fuentes. Lo que Codex agrega es formalizar esa relación con las tres dimensiones y hacerla una entidad separada y agnóstica. Así que el corpus no se reusa de Fray Tomás, pero el patrón de derivar memes de textos fuente sí está presente y puede informar el diseño.

### La estratificación de agentes — NUEVO

Fray Tomás es un agente de máxima profundidad. No tiene el concepto de agentes tibios, multitudes, o niveles de profundidad. Toda la estratificación (PJ completo, principales, secundarios, tibios, multitudes) con sus reglas de ascenso y descenso es nueva.

### El time-jump y la simulación lazy del mundo — NUEVO

Fray Tomás vive en tiempo real continuo. No tiene el concepto de saltar tiempo y simular lazy lo que pasó. Todo el sistema de time-jump es nuevo.

---

## Síntesis del esfuerzo

Poniendo todo junto, el panorama del esfuerzo es el siguiente.

El motor cognitivo central (memetario, loadout, decaimiento, embeddings, bias circadiano) es mayormente reutilizable de Fray Tomás con adaptaciones acotadas, principalmente la transformación de instancia única a clase instanciable y el agregado de los modificadores de lugar. Esto es la mejor noticia del proyecto: el corazón cognitivo ya existe y está probado. Quizás un cuarto del esfuerzo total y es el cuarto que ya está casi hecho.

Los sistemas de identidad y memoria de Fray Tomás (Consejo, DIARIUM, memoria episódica, SPECULUM) son parcialmente adaptables pero en su mayoría diferibles. Su concepto informa el diseño de Codex (los hitos biográficos absorben el DIARIUM, el Consejo puede reaparecer en los dioses) pero poco se reusa tal cual para el MVP.

La persistencia y la filosofía de integración con LLM se heredan como principios pero se expanden en implementación.

Y los componentes verdaderamente nuevos (grafo de información, grilla espacial, memetario de lugares, motor de Blades, corpus formalizado, estratificación, time-jump) son el grueso del trabajo real de Codex. Tres cuartos del esfuerzo total están acá, y es trabajo nuevo aunque diseñado.

La conclusión arquitectónica es alentadora pero realista. Fray Tomás te regala el motor cognitivo, que es la pieza más difícil de hacer bien y la que más tiempo habría llevado desde cero. Pero Codex es mucho más que un motor cognitivo: es ese motor multiplicado por muchos agentes, situado en un espacio, conectado por un grafo de información mutante, animado por un motor de drama. Eso es trabajo nuevo sustancial. El reuso de Fray Tomás no convierte a Codex en un proyecto chico, pero sí elimina el riesgo más grande (que el motor cognitivo no funcione) porque ya funciona en otro proyecto.

---

## La recomendación de secuencia

Dado este mapa, la secuencia de construcción del MVP que minimiza riesgo es la siguiente.

Primero, traer el motor cognitivo de Fray Tomás y envolverlo en la clase instanciable de Codex. Verificar que funciona con dos o tres agentes instanciados simultáneamente. Esto es bajo esfuerzo y alto valor: confirma que la pieza reutilizable efectivamente se reusa.

Segundo, construir la pieza nueva más distintiva y más riesgosa: el grafo de información con la mutación de un rumor entre dos agentes. Esto es lo que valida la promesa conceptual del proyecto. Si la mutación de información a través de los memetarios se siente mágica, el proyecto tiene futuro. Si no, hay que repensar antes de invertir más.

Tercero, agregar lo mínimo del motor de Blades para tener un Score jugable. Cuarto, agregar el corpus liviano a los personajes para darles voz. Quinto, envolver todo en la interfaz mínima.

Esta secuencia ataca temprano el mayor riesgo (que la mutación de información no funcione) reusando primero lo seguro (el motor cognitivo). Es la secuencia que más rápido te dice si el proyecto es viable.

---

*Documento basado en lectura de documentación de Fray Tomás, no de su código. Verificar contra código real antes de decisiones de esfuerzo definitivas.*
