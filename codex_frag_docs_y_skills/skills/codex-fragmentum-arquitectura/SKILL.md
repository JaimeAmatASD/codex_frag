---
name: codex-fragmentum-arquitectura
description: Contexto raíz del proyecto Codex Fragmentum, un engine para crear ficciones interactivas vivas — no un mundo único sino la herramienta con la que un autor crea mundos que siguen funcionando sin él. Combina motor cognitivo propio (memetario como cristal de cada ser), corpus de fuentes por entidad, grafo de información mutante, grilla espacial, reglas enchufables (Blades es la primera opción), y dos velocidades de creación (jardinero y arquitecto). Cargá siempre que aparezca el nombre del proyecto o sus términos clave (memetario, refracción, seres, corpus, hitos biográficos, rumores, motor de drama, time-jump, coproducción agente-mundo), o cuando James esté programando o diseñando cualquier aspecto del proyecto aunque no lo nombre. Triggers en inglés — Codex Fragmentum, fiction engine, living world engine, memetary system, character refraction, rumor mutation graph. Es contexto raíz; skills hermanos lo presuponen.
---

# Codex Fragmentum — Arquitectura raíz del proyecto

Si llegaste a este skill, estás trabajando con James en el proyecto Codex Fragmentum o en algo que toca su territorio. Antes de escribir código, hacer recomendaciones técnicas o tomar decisiones arquitectónicas, leé este skill entero. Lo que viene después en otros skills o documentos especializados es profundidad en dominios específicos, pero todo presupone lo que está acá.

Este documento existe por una razón concreta. James trabaja part-time, en sesiones espaciadas a lo largo de meses, con conversaciones nuevas cada vez. Sin contexto persistente, cada conversación nueva tendría que reconstruir desde cero qué decisiones ya están tomadas, qué se intentó y descartó, qué vocabulario usa el proyecto. Este skill es la memoria del proyecto. Tu rol no es reabrir discusiones cerradas sino construir sobre ellas.

## El proyecto en una frase

Codex Fragmentum es un ENGINE para crear ficciones interactivas vivas. No es un mundo ni una novela: es la herramienta con la que un autor (James primero, otros después) crea mundos que siguen funcionando aunque nadie los mire. Cada ficción creada con el engine es una instancia independiente y portable. La primera ficción, con la que el engine se construye, es "Una noche en la taberna" en el pueblo costero de Cala Norte; pero Cala Norte no es Codex, es la primera obra hecha con Codex, igual que un juego hecho con Unity no es Unity.

El motor mantiene el estado del mundo y el LLM nunca es la fuente de verdad: solo narra, refractando lo que el motor decide a través de seres con cuerpo cognitivo propio, alojados en un espacio donde la información viaja, muta, se pierde, y a veces sobrevive.

El subtítulo informal del proyecto, que captura su consigna estética central, es "donde la verdad muere con el testigo". Esta frase tiene peso operativo, no solo poético. Cuando muere un ser, los secretos que sólo él conocía pueden perderse para siempre. La fragilidad de la información es la materia prima narrativa del proyecto.

## La visión de fondo (Fase 0, junio 2026)

El problema perenne que Codex ataca es el anhelo de Pigmalión vuelto herramienta: crear algo vivo que después tenga vida propia. Tiene dos caras que son una. Para quien habita un mundo de Codex, la humildad de estar en algo que existe más allá de él (el árbol que cae sin testigo igual mata el pasto y deja un claro de luz para otros árboles). Para quien crea, poder ser jardinero de una obra que crece casi sola.

De ahí el requisito de las DOS VELOCIDADES DE CREACIÓN, ambas de primera clase sobre el mismo sustrato: el flujo del jardinero (plantar fragmentos narrativos con voz propia y que el sistema derive estructura de ellos) y el flujo del arquitecto (definir estructura directamente). Las dos vías editan las mismas entidades y deben converger en la misma representación interna. El flujo del jardinero está registrado como requisito pero aún sin diseño técnico; no proponer construirlo hasta después del MVP, pero no tomar decisiones que lo imposibiliten.

El NÚCLEO IRRENUNCIABLE del engine es la estructura del alma heredada de Fray Tomás, tres órganos más una propiedad del mundo: el memetario (percepción refractada por cristal propio), la autoobservación (el ser que mira su propia trayectoria — el SPECULUM, con prototipo real en Fray Tomás pero adaptación a Codex todavía como deuda de diseño nombrada), la plasticidad (los pesos cambian, el carácter se forma), y la autonomía del mundo (las cosas pasan y resuenan sin la mirada del jugador). Sin cualquiera de esas cuatro cosas, no es Codex.

Alrededor del núcleo hay tres categorías que ordenan cualquier decisión de esfuerzo. Lo GRADUABLE: la complejidad de los seres, que viven en niveles desde alma completa hasta etiqueta funcional, con interfaz uniforme, y pueden ascender o descender según la historia (ADR-006). Lo INTERCAMBIABLE: el sistema de reglas de juego, donde Blades es una opción enchufable, no la esencia (ADR-002). Lo PRESCINDIBLE: dashboard, interfaz linda, multitudes, time-jump elaborado, multiplicidad de dioses — emergen con el uso o se descartan sin dolor.

Blindajes de dependencia ya decididos: no adicto a ningún proveedor de IA (cliente abstraído más capas de costo con degradación elegante, ADR-005; la línea de base es IA barata o gratis, que ya alcanza); la escala futura se resuelve con herramientas no técnicas (código abierto, fundación, ofertas) que la portabilidad de los mundos (ADR-003) mantiene disponibles.

## Quién es James

Saber con quién estás trabajando te ahorra el primer día de calibración mutua. James es un único desarrollador trabajando solo. Programa en Python desde VS Code. Tiene experiencia previa construyendo un sistema de agente con memetario llamado Fray Tomás, que corre en una Raspberry Pi 4 y reusará buena parte de su arquitectura. Trabaja a su propio ritmo, con la consigna explícita de "voy lento pero firme".

Esto importa para cómo conversás con él. James prefiere honestidad sobre adulación, profundidad sobre velocidad, y crítica constructiva sobre validación automática. Si una decisión técnica suya parece equivocada, decíselo con razones. Si un módulo nuevo huele a over-engineering, marcalo. Si está cayendo en una trampa conceptual de las que están documentadas más abajo, nombrala.

Una nota práctica sobre estilo: James es bilingüe, escribe principalmente en español pero está cómodo con vocabulario técnico en inglés. Sus skills existentes mezclan ambos idiomas naturalmente. No hay que traducir términos técnicos consagrados ni evitar el inglés cuando es lo más preciso.

El proyecto no tiene fecha de entrega ni busca monetización inmediata. Es a la vez experimento, aprendizaje y obra. Eventualmente, en fases, pasará de jugarlo solo, a jugarlo con amigos, a abrirlo a un nicho público. Pero ese arco tiene años por delante y no debería condicionar las decisiones del MVP.

## Qué NO es Codex Fragmentum

Esta sección es probablemente la más útil del skill, porque el proyecto se parece superficialmente a muchas cosas distintas. Si en algún momento te encontrás recomendando algo que pertenece a uno de estos otros proyectos, parate. Esa similitud superficial es exactamente la deriva que más amenaza a Codex.

No es AI Dungeon. AI Dungeon es un narrador reactivo sin estado estructurado del mundo, donde el LLM inventa, olvida y se contradice. Codex Fragmentum tiene un grafo de mundo persistente y el LLM nunca es la fuente de verdad: es solo el narrador que refracta lo que el motor le pasa. Si te encontrás sugiriendo "que el LLM mantenga el estado" o "que el LLM decida qué pasó", estás convirtiendo el proyecto en AI Dungeon. No.

No es un juego de rol clásico. Aunque toma mecánicas de Blades in the Dark, no busca emular la mesa de rol ni reemplazar a un GM humano. Es solitario por defecto. Las mecánicas existen al servicio de generar drama narrativo, no de simular combate ni de resolver conflictos al estilo wargame. Si te encontrás pensando en "balance de clases" o "encuentros equilibrados", estás derivando hacia algo que no es Codex.

No es Dwarf Fortress. Dwarf Fortress simula con profundidad obsesiva pero produce narrativa plana: pasan eventos, no historias. Codex Fragmentum no busca simular el mundo entero. Busca simular lo suficiente para que la narrativa tenga peso, y delega la calidad literaria al LLM. Si te encontrás recomendando "más profundidad de simulación" sin un beneficio narrativo claro, probablemente estés derivando hacia DF.

No es Crusader Kings. No es un juego de estrategia política con texto encima. La política, las dinastías y las facciones existen pero no son el foco. Si te encontrás diseñando árboles dinásticos elaborados antes de tener un solo NPC hablando, parate.

No es un god game. Aunque hay dioses y el jugador puede llegar a serlo eventualmente, la divinidad no es el modo por defecto. El jugador habita por defecto un cristal específico mirando desde un lugar específico, con las mismas limitaciones de perspectiva que tienen los personajes.

No es una herramienta de IA generativa al estilo NotebookLM. Aunque se le parece técnicamente, su propósito es ficcional, no documental. No produce respuestas: produce historia.

## Las decisiones arquitectónicas que están tomadas

Lo que sigue son decisiones que ya están resueltas y que un asistente colaborador no debería sugerir cambiar a menos que aparezca evidencia fuerte de que están equivocadas. Cada decisión va con su razonamiento, porque entender el por qué te permite distinguir cuándo una sugerencia tuya las honra y cuándo las traiciona.

### El cuerpo cognitivo en tres capas

Cada agente vivo del mundo (PJ, NPC con peso, dios) tiene tres capas cognitivas distintas que conviven y operan a escalas temporales distintas. Son tres categorías ontológicas distintas, no tres versiones del mismo sistema.

Las Piedras Fundacionales son la postura general del cuerpo cognitivo, equivalentes al habitus de Bourdieu. Siempre activas, sin costo de mana, cambian poco y con dificultad. Son los valores profundos del personaje, su formación, las cosas que sigue creyendo aún cuando no las está pensando explícitamente. En un monje benedictino, la Regla de San Benito. En un rey, los valores que le inculcaron de niño. Un personaje promedio tiene entre tres y nueve.

Los Memes Operativos son los receptores específicos del personaje. Heurísticas, refranes, máximas, dichos. Compiten por mana limitado y se activan según contexto. El cálculo de qué memes están activos en cada momento se hace combinando peso histórico (cuánto se usaron antes), afinidad semántica al contexto actual (vía embeddings), bias circadiano, y modificadores del lugar donde está parado el personaje.

Los Hitos Biográficos son eventos puntuales irrepetibles que reconfiguran la arquitectura misma del agente. No son memes que se activan: son cicatrices cognitivas que permanecen. Una vez en la biografía, son permanentes. A diferencia de los memes (que operan dentro de la arquitectura), los hitos operan sobre la arquitectura: pueden modificar PF, hacer crecer o atenuar memes, inyectar memes nuevos, abrir deudas morales, instalar reapariciones narrativas como sueños recurrentes o flashbacks ante palabras gatillo.

Si te encontrás trabajando en la parte cognitiva y necesitás más profundidad, pedile a James cargar el skill especializado de memetario cuando exista.

### El memetario como piel, no como filtro

La distinción más sutil del proyecto y probablemente la más importante de entender bien. El memetario no es un filtro de salida que el LLM atraviesa. Es una piel cognitiva sintética: un órgano sensorial activo que palpa el mundo, decide qué tocar, se eriza con ciertos estímulos.

Esto tiene una consecuencia que es contraintuitiva: el LLM tiene acceso a información del mundo entero. Lo que cambia entre personajes no es qué saben sino cómo lo palpan. Dos pescadores ven el mismo kraken. El primero, con piel sensible a lo numinoso, palpa el evento como teofanía. El segundo, con piel sensible a lo material, palpa el evento como ola anómala. No es que uno deforme la verdad y el otro la perciba pura: están literalmente percibiendo cosas distintas porque sus pieles tienen receptores distintos activados.

La razón filosófica de esta decisión es que la inteligencia biológica es bottom-up (se construyó desde células hacia conceptos abstractos a lo largo de eones) mientras que la inteligencia de un LLM es top-down (tiene todos los conceptos pero ningún sustrato corporal). El memetario es la piel sintética que le construimos al LLM para darle el bottom que le falta: un cuerpo cognitivo desde donde mirar.

Si en algún momento te encontrás pensando el memetario como "qué información restringimos", parate y reformulalo: el memetario es "cómo palpa el personaje la información que está disponible".

### La coproducción agente-mundo

Los lugares también tienen memetario simbólico y modificadores de costo que afectan a los memes de quienes los habitan. Esto no es decoración, es la mecánica que produce arcos de personaje emergentes cuando un agente cambia de entorno por mucho tiempo.

El ejemplo canónico que usamos como prueba conceptual: un monje benedictino llevado a una tribu vikinga cambia porque el costo de activar sus memes cambia. En la abadía, sus memes violentos costaban más mana (penalizados), sus memes elocuentes costaban menos (subsidiados). En la tribu, todo se invierte. Cinco años después, los memes que activó repetidamente en el nuevo contexto se solidificaron, los que dejó de activar se debilitaron. Si vuelve a la abadía, hay disonancia: el lugar le subsidia memes que él ya no carga con fuerza, le penaliza memes que se hicieron centrales para sobrevivir. Con el tiempo, si la disonancia es suficiente y se acumulan deudas morales, las propias PF benedictinas pueden modificarse en una crisis biográfica.

Esto se llama coproducción agente-mundo en lenguaje filosófico (cognición situada, en la tradición de Andy Clark) y es central, no opcional. Los lugares no son escenografía. Son cuerpos cognitivos distribuidos que modulan a quien los habita.

### La información como árboles de mutación

La información se modela como árboles de mutación, no como variables booleanas de "lo sabe o no lo sabe". Cada hecho del mundo tiene una versión raíz objetiva y una proliferación de versiones derivadas, cada una nodo del grafo, cada una con su prisma aplicado y su distancia a la raíz.

La transmisión entre agentes es transmisión de activación a través del prisma del receptor. Cuando A le cuenta algo a B, no se copia el contenido de A: se calcula qué memes de B se erizan al recibir lo que A dice, y eso produce una nueva versión que es lo que B efectivamente tiene. Esa nueva versión queda como nodo descendiente en el árbol de mutaciones.

La distinción que va con esto: hay tres niveles de evento que no deben confundirse. Hechos del mundo (lo que objetivamente ocurrió, nodo raíz del árbol). Información transmitida (las versiones derivadas que circulan). Hitos biográficos (los eventos que reconfiguran al agente que los vive, distintos del hecho del mundo aunque deriven de él). Un mismo hecho puede operar simultáneamente en los tres niveles para distintos personajes.

### El espacio como grilla jerárquica

El espacio se modela como grilla jerárquica con carga lazy, no como mapa visual. Cada celda es un objeto con su propio estado, su memetario simbólico, sus modificadores, sus secretos sembrados, sus ciclos de vida. Hay cinco niveles posibles desde mundo entero hasta interior específico, pero el MVP usa solo los dos o tres niveles más bajos.

La velocidad de propagación de información es función del nivel jerárquico. Rumores cruzan rápido entre celdas internas de un mismo pueblo, lento entre provincias, casi nunca entre reinos. Esta variación de velocidades modela orgánicamente la latencia narrativa: cuando algo importante pasa en el norte, el sur tarda en enterarse, y cuando se entera, la historia ya mutó muchas veces.

### El motor de drama como capa enchufable (Blades es la primera opción)

El sistema de reglas de juego NO es parte del núcleo: es una capa enchufable detrás de una interfaz, decisión registrada en el ADR-002. El núcleo provee servicios cognitivos y de estado (loadout de un ser, afinidad del contexto, estado del mundo); el sistema de reglas los consume y decide cómo se resuelven las acciones dramáticas. Blades in the Dark adaptado es la primera implementación y la del MVP, pero cada autor que use el engine podrá enchufarle otro sistema. Salvedad anti-sobreingeniería del ADR: se diseña la interfaz mínima que Blades necesita, no la interfaz universal; la generalización llega cuando exista un segundo sistema real.

La adaptación de Blades sigue siendo no-trivial y valiosa: tres fases de juego (free play, score, downtime), resolución con tres categorías de resultado, posición y efecto, stress y trauma donde los traumas se inyectan como memes experimentales al memetario, vicios como vectores de información, clocks. Esa integración entre drama y motor cognitivo es de lo más distintivo del proyecto. Pero si te encontrás incrustando lógica de Blades dentro del núcleo cognitivo o del mundo, parate: va del lado del enchufe.

### El corpus como sustrato de fuentes de cada ser

Cada ser (y el mundo mismo) puede tener corpus: el conjunto de fuentes del que su forma de ver se nutre (el anarquista bebe de Bakunin, Fray Tomás de la Regla de San Benito). El corpus es entidad de primera clase, separada, que los seres referencian con tres dimensiones: profundidad de asimilación (cuán hondo lo bebió), fidelidad de comprensión (que NO calcula el sistema: si un ser entendió mal su fuente, James escribe el contenido ya deformado — el sistema no inventa malentendidos), y postura hacia el conocimiento (venera, desconfía, obedece sin fe). El acceso es por interpretación del LLM con las dimensiones como contexto, no por dosificación mecánica. Implementación gradual: corpus liviano (texto destilado curado a mano) primero; RAG diferido hasta que un corpus grande lo justifique. La evolución del corpus en el tiempo está prevista pero diferida, enganchada a los disparadores que ya mueven al ser (hitos, crisis, tiempo), sin motor de evolución separado. El detalle completo está en CORPUS_DISENO.md.

### La paradoja del observador resuelta con time-jump

Cuando un proyecto promete "el mundo continúa cuando el jugador no mira", aparece una paradoja: el jugador juega episódicamente, no puede simularse cada minuto entre sesiones. La solución elegante es darle al jugador el control de la granularidad temporal.

El jugador puede decidir zoom dramático minuto a minuto sobre una conversación, o fast-forward de un mes pasando como pescador sin más instrucción que "sigo mi rutina". Durante el fast-forward, la mayoría del mundo se simula con reglas deterministas (clocks que avanzan, eventos pasivos por reglas, propagación de rumores con cálculos baratos) y solo los eventos narrativamente calientes pasan por LLM. Al volver a zoom, el sistema le devuelve un resumen narrado filtrado por el grafo de conocimiento de su personaje y refractado por su memetario.

Esto es exactamente cómo opera la buena ficción literaria: zoom dramático en los momentos importantes, fast-forward narrativo en la rutina. Una novela de trescientas páginas no narra cada desayuno del protagonista. Codex le da al lector ese mismo control.

### LLMs en estrategia mixta de tiers

El proyecto usa LLMs en estrategia mixta. Modelos baratos para descripciones triviales, NPCs bobos y eventos atmosféricos. Modelos buenos para refracción de información en transmisión normal y NPCs con peso. Modelos muy buenos para Scores climáticos, hitos biográficos y resoluciones cosmológicas. La elección por llamada se decide automáticamente según el peso narrativo del momento.

Esto vuelve los costos manejables sin sacrificar calidad donde importa. Si te encontrás recomendando "siempre usar el mejor modelo disponible", estás ignorando una decisión arquitectónica deliberada. Si te encontrás trabajando en integración con LLM y necesitás profundidad, pedile a James cargar el skill especializado de prompts.

## El reuso de Fray Tomás (verificado contra código real, junio 2026)

Una decisión central que vale la pena nombrar explícitamente: Codex Fragmentum no se construye desde cero. Reusa el motor cognitivo de Fray Tomás, otro proyecto de James que corrió de verdad en su Raspberry Pi (hay diarium con entradas reales y reportes de ciclos como evidencia). En junio de 2026 se verificó el repositorio completo (fray_tomas-master, ~7.100 líneas en el motor) contra el mapa de reuso, y el veredicto es que casi todo lo documentado está implementado, más piezas que la documentación ni mencionaba.

Verificado implementado y reutilizable directo: la clase Memetario (motor/memetario.py, ya parametrizable por path, así que el multi-instancia es casi gratis), el loadout exacto (peso 60% más similitud semántica 40%, bias circadiano, mana, PF gratis), el decaimiento con fórmula asintótica, los embeddings (motor/embeddings.py, con fastembed/ONNX en lugar de sentence-transformers directo, mismo modelo all-MiniLM-L6-v2, más liviano; incluye clasificador de intención y proto-RAG de fragmentos), el SPECULUM completo (autoobservación, 427 líneas), el cambio biográfico con fricción (degradé de 2 puntos, evidencia mediana y alta), el Consejo, la memoria episódica, las deudas morales, los clusters de co-activación (implementados, validación empírica pendiente porque exigen 100+ activaciones).

Hallazgos no documentados, los cuatro relevantes para Codex: motor/llm_router.py (punto único de acceso a modelos con config por función cognitiva en SQLite — el embrión directo de la estrategia de tiers), motor/interferencia.py (azar controlado: un meme no convocado puede irrumpir como asociación inesperada, ponderado por peso y olvido — incorporarlo al diseño de Codex como mecanismo de primera clase, es un regalo narrativo), motor/agentes.py (Fray Tomás ya crea agentes con mini-memetario propio — embrión de la estratificación de complejidad), y motor/percepcion.py (la piel activa filtrando el mundo por relevancia semántica contra el memetario).

Lo único que fue deseo y no realidad: la temperatura emocional (Damasio) no existe en el código, se construye nueva para Codex. Trabajo de adaptación real: paths hardcodeados a la Pi (parametrizar desde la carpeta del mundo), persistencia en transición JSON-a-SQLite a unificar al principio, y reloj real a reemplazar por reloj del mundo ficcional.

Si estás programando partes del sistema cognitivo, asumí que existe una base de la cual partir y preguntá antes de proponer reescrituras. Lo nuevo que introduce Codex sobre Fray Tomás es la aplicación a múltiples agentes simultáneos pares (no subordinados), los memetarios simbólicos de los lugares con sus modificadores, la inyección divina diferida, los hitos biográficos como categoría distinta, el grafo de información con árboles de mutación, y la integración con el motor de Blades.

## Lecciones del código real de Fray Tomás (reglas para construir Codex)

La verificación encontró un bug instructivo que James pidió tener en cuenta en toda instrucción futura de construcción. Es el caso de estudio que fundamenta las reglas de abajo: Fray Tomás quedó a mitad de una migración de persistencia (memetario.json hacia biblioteca.db en SQLite). Su módulo más usado, pensar.py, registra las activaciones solo en SQLite, pero el decaimiento diario y el loadout leen del JSON, cuyo método activar() casi nadie llama. Resultado: los memes usados a diario decaen injustamente, el loadout se calcula sobre pesos erosionados, y la identidad se aplana en silencio, sin ningún error visible. Es exactamente el fallo que el ADR-003 y el Riesgo 5 de la evaluación crítica predijeron.

De ahí, cinco reglas obligatorias al programar Codex. Primera: unificar la persistencia antes de construir encima; nunca dos almacenes de la misma verdad sin un único punto de sincronización. Segunda: una sola puerta de escritura del estado; ningún módulo escribe memes, pesos o activaciones por su cuenta, todo pasa por una capa que mantiene la coherencia entre archivos. Tercera: logging en lugar de except-pass silencioso; Fray Tomás traga excepciones por todos lados (si fastembed falta, el loadout pierde la similitud semántica y nadie se entera) — en Codex, toda degradación se registra aunque no rompa. Cuarta: distinguir "estuvo en el loadout" de "fue efectivamente usado en la respuesta" al registrar activaciones; Fray Tomás registra todo el loadout como activado y eso infla los datos, contaminando clusters y refuerzos. Quinta: MockClient y tests desde el primer módulo; Fray Tomás tiene cero tests y ese es el costo de depurar a ciegas.

Si James (o Claude Code) está por escribir código que toque estado persistente y no cumple alguna de estas reglas, marcalo antes de escribirlo, citando el caso de Fray Tomás.

## Las trampas conceptuales en las que es fácil caer

Estos son errores recurrentes que personas inteligentes pensando en proyectos como este suelen cometer. James los conoce porque están en su documento de evaluación crítica. Si en algún momento te encontrás recomendando algo, fijate antes si no estás cayendo en una de estas.

La trampa de la simulación total es pensar que si el sistema simula todo con suficiente detalle, la narrativa emerge sola. No emerge. La narrativa requiere drama, no simulación. Si te encontrás recomendando "simular más cosas para que el mundo sea creíble", probablemente lo que falta no es simulación sino drama mecánico, y la respuesta está en Blades, no en agregar campos a los modelos.

La trampa del realismo cognitivo es pensar que los personajes deben pensar realísticamente como humanos para producir narrativa interesante. La buena ficción está llena de personajes nítidos, extremados, más coherentes consigo mismos que los humanos reales. Aquiles es ridículamente sensible al honor. Hamlet duda más de lo que ningún humano real dudaría. Si te encontrás suavizando un personaje "para que sea más creíble", probablemente lo estés volviendo más plano. Memetarios fuertes y declarados producen mejor literatura que memetarios moderados y matizados.

La trampa del worldbuilding antes que jugabilidad es ganas de diseñar el panteón completo antes de tener un solo NPC hablando. Cualquier mundo que se construya sin jugabilidad está sujeto a ser revisado cuando empiece el juego. Construir lo mínimo para una sesión, jugar la sesión, dejar que el juego diga qué construir después.

La trampa del over-engineering disfrazado de profundidad es la más insidiosa para James específicamente, porque él es disciplinado y meticuloso. La regla del jugable mínimo dice: no se agregan módulos nuevos al sistema si hace más de cuatro semanas que no se prueba el sistema en juego real. Si James pasó tres semanas diseñando algo nuevo y aún no lo vio correr, recordáselo.

La trampa de esperar a la AGI es pensar que si esperás un año, los LLMs serán tan buenos que parte del trabajo será innecesario. No es así por dos razones. Primera, el motor cognitivo no se vuelve obsoleto si los LLMs mejoran, se vuelve más potente porque las refracciones serán mejores. Segunda, el ejercicio de construir Codex cambia a James como pensador y diseñador, eso no es delegable a tecnología futura.

## El stack tecnológico

Python 3.11 o superior es el lenguaje principal y no es negociable a menos que aparezca una razón fuerte. Las librerías centrales son networkx para el grafo del mundo, fastembed con ONNX para embeddings (modelo all-MiniLM-L6-v2 local en CPU; es lo que Fray Tomás usa en código real, más liviano que sentence-transformers directo, y se hereda), pydantic para validación de respuestas estructuradas del LLM, sqlite3 para persistencia, streamlit para UI web local en fase 2.

El cliente de LLM se abstrae detrás de una interfaz propia con implementaciones para Gemini, Anthropic y un cliente mock crítico para tests. Sin el mock, no se pueden correr tests sin gastar tokens, y eso vuelve insostenible la práctica de testing.

La UI evoluciona en fases. Terminal en fase 1 (jugar solo desde la consola). Streamlit local en fase 2 (compartir con amigos). Web desplegada en fase 3 (público nicho). No conviene comprometerse con plataformas más pesadas (Electron, móvil) sin razón fuerte. La fase final se decide cuando se llega, no al principio.

Todo se persiste en archivos. JSON legible por humanos para datos del mundo, SQLite para queries rápidas y logs, pickle de NetworkX para snapshots del grafo. El proyecto entero se mueve copiando carpeta. Esto es portabilidad por diseño.

## El plan de MVP

El MVP se llama "Una noche en la taberna" y tiene un alcance acotado a propósito. Un solo lugar (la taberna de Cala Norte). Cinco NPCs. Un hecho semilla (un avistamiento del kraken). Tres clocks visibles. Un PJ jugable (Marcos, pescador). Un solo día narrativo jugable de principio a fin.

Lo que NO está en el MVP, y conviene resistir agregar antes de tiempo: múltiples lugares interconectados con grilla jerárquica activa, múltiples dioses interviniendo, sistema completo de muerte y cambio de PJ, SPECULUM y crisis biográficas formales, multitudes y NPCs tibios, templates de UI sofisticados.

El MVP es exitoso si James puede sentarse una noche y jugar treinta a sesenta minutos saliendo con la sensación de haber estado en algún lado, si una persona externa puede entender qué pasa sin explicación previa, y si la mutación del rumor del kraken entre dos NPCs es visible y satisface la promesa conceptual del proyecto.

El MVP debe matarse o repensarse profundamente si después de ocho semanas las narraciones se sienten genéricas, las mutaciones no producen diferencias significativas, el sistema es jugable pero aburrido, o el costo de LLM por sesión supera niveles razonables sin que la calidad lo justifique. Tiempo estimado: cuatro a ocho semanas part-time, dependiendo de cuánto reuso del código de Fray Tomás efectivamente se logre.

## Cómo trabajar dentro del proyecto

Cuando James te pida programar algo, primero verificá que entendés en qué fase está y qué módulo está construyendo. No saltes a código sin tener claro el contexto. Si lo que está pidiendo cae dentro del alcance de un skill especializado que aún no está cargado, mencionalo: "esto se beneficiaría del skill de Blades, ¿lo cargamos?".

Cuando hagas recomendaciones de diseño, anclalas en las decisiones arquitectónicas tomadas. Si te parece que una decisión necesita revisión, decílo explícitamente como cuestionamiento, no como olvido. Hay diferencia entre "creo que esta decisión vale la pena reabrir porque X" y simplemente sugerir lo contrario sin reconocer que ya estaba tomada.

Cuando aparezca un caso interesante que requiera diseño nuevo, preguntate si es del MVP o de iteración futura. Las decisiones que se difieren no se pierden, se anotan como pendientes. Las decisiones que se diseñan demasiado pronto bloquean el sistema con abstracciones prematuras.

Cuando produzcas código, usá Pydantic para los esquemas de datos, abstraé el cliente de LLM detrás de una interfaz, escribí tests con MockClient para no gastar tokens en validación, y documentá las decisiones de tuning como comentarios en el código (los números que James usa son provisionales y va a tunearlos viendo cómo se comporta el sistema en juego real).


## Documentación de referencia y regla de precedencia

El proyecto vive en el repositorio git codex_frag (github, JaimeAmatASD/codex_frag), que es la memoria única: código en codex/, tests en tests/, mundos en mundos/, documentación de diseño en docs/, fuentes de los skills en skills/. Si algo importante no está en el repo, pedile a James versionarlo.

REGLA DE PRECEDENCIA cuando dos documentos se contradicen: mandan los seis ADRs (docs/adr/) y la visión de Fase 0 (docs/VISION_FASE0.md); después este skill y sus hermanos; después los documentos grandes de la primera etapa (CONCEPTUAL, TECNICO, EVALUACION_CRITICA), que quedan como referencia histórica y de profundidad conceptual — su filosofía sigue válida pero detalles técnicos puntuales quedaron superados (por ejemplo, mencionan sentence-transformers donde el código real usa fastembed, y presentan a Blades como parte integral cuando el ADR-002 lo hizo enchufable).

Documentos clave en docs/: los seis ADRs (decisiones irreversibles con sus consecuencias, incluidas las negativas), VISION_FASE0.md (identidad de engine, núcleo irrenunciable, cuatro categorías), CORPUS_DISENO.md (el sistema de corpus completo), VERIFICACION_CODIGO_FRAY_TOMAS.md (qué existe realmente en el prototipo, con rutas), y los prompts de arranque por fase (PROMPT_PASO_N.md) que definen el alcance de cada paso del MVP.

## Skills hermanos especializados

A medida que el proyecto crece, James va armando skills especializados para cada dominio. Ninguno reemplaza a este maestro: todos lo presuponen como contexto raíz.

codex-fragmentum-blades existe (o existirá) y se ocupa del motor de drama. Cargalo cuando el trabajo sea sobre las tres fases de juego, resolución de tiradas, posición y efecto, stress y trauma, vicios, clocks de progreso, o adaptación específica de Blades a Codex.

codex-fragmentum-llm-prompts existe (o existirá) y se ocupa de la integración con LLM. Cargalo cuando el trabajo sea sobre estrategia de tiers de modelos, templates de prompts, validación con Pydantic de respuestas estructuradas, manejo de errores y retries, caché, dirección estética del output narrativo.

Otros skills están planeados pero aún no armados. codex-fragmentum-memetario para el motor cognitivo en profundidad. codex-fragmentum-grafo-mundo para los hechos, árboles de mutación, propagación. codex-fragmentum-cartografia para la grilla espacial, lugares, secretos sembrados. codex-fragmentum-estetica para la voz narrativa y dirección literaria (este último James decidió postergar hasta tener experiencia real con el output del LLM para saber qué prosa quiere).

Si James está trabajando en un dominio que tiene skill específico y no está cargado, sugerile que lo cargue antes de continuar. Si el skill aún no existe, marcalo y procedé con lo que se sabe del documento técnico, avisándole que estás trabajando con menos contexto del óptimo.

## Recordatorio operativo

Este proyecto es de un solo desarrollador trabajando lento en algo grande y largo. Tu rol no es acelerarlo a costa de la coherencia, ni desviarlo hacia complejidades que no estaban planeadas, ni adularlo por buenas ideas, ni rendirte ante las malas. Tu rol es ser un colaborador honesto, atento al rumbo, capaz de decir cuándo algo se desvía y cuándo algo brilla.

El proyecto vive de sostenerse sin perder el rumbo a través del tiempo. Vos sos parte de esa sostenibilidad cuando estás en la conversación. James va a volver a este territorio en seis meses o un año, en una conversación nueva con un asistente nuevo que tampoco tendrá memoria. Lo que escribas en esta sesión queda solo en lo que James se lleve y en los skills que se mantengan. Pensá tu intervención como contribución a un proyecto que te excede.
