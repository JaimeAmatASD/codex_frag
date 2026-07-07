---
name: codex-fragmentum-cartografia
description: Sistema espacial del proyecto Codex Fragmentum. Cubre la grilla jerárquica que organiza el mundo en niveles anidados (de mundo a interior), los lugares como cuerpos cognitivos distribuidos con memetario simbólico propio que modula a quienes los habitan, los secretos sembrados en celdas que se activan por condiciones específicas, los objetos del mundo con sus reinos (mineral, vegetal, divino, conceptual e híbridos) y ciclos de vida. Cargá cuando el trabajo toque la modelación del espacio, el diseño de un nuevo lugar, los modificadores de costo que aplica al memetario de los agentes, los secretos descubribles al entrar a una celda, los objetos cargados narrativamente, los ciclos cosmológicos vinculados a dioses, la carga lazy de celdas. Triggers en inglés — spatial grid, hierarchical world map, place memetary, location modifiers, seeded secrets, world objects, kingdom hybridization, lazy loading. Presupone codex-fragmentum-arquitectura cargado.
---

# Codex Fragmentum — Sistema espacial y de objetos del mundo

Este skill se ocupa del sistema que modela el espacio del Codex y todo lo que vive en él más allá de los agentes vivos. Si llegaste a este skill, James está trabajando en cómo se estructura geográficamente el mundo, en cómo los lugares afectan a quienes los habitan, en qué cosas hay sembradas para descubrir, en los objetos cargados de significado que pueblan el mundo. Para el contexto general, asumí que el skill maestro codex-fragmentum-arquitectura ya está cargado.

Una nota importante de entrada. Este skill tiene estructura modular con archivos de referencia separados, porque cubre cuatro subdominios que tocan código distinto y conviene poder cargarlos por separado. El SKILL.md principal cubre los conceptos transversales y sirve como índice. Cuando estés trabajando en un subdominio específico, cargá su archivo de referencia correspondiente.

## Por qué los lugares no son escenografía

Vale la pena empezar por la idea más distintiva del proyecto en este territorio. En la mayoría de los simuladores narrativos, los lugares son fondos donde pasan cosas. Tienen descripción, tienen nombre, eventualmente tienen efectos especiales, pero son pasivos respecto a quienes los habitan. Los personajes actúan, los lugares observan.

En Codex Fragmentum los lugares son cuerpos cognitivos distribuidos. Tienen memetario simbólico propio, tienen modificadores de costo que afectan a los memes de los agentes que los habitan. Una abadía vuelve más caro activar memes violentos y más barato activar memes contemplativos. Una tribu vikinga hace lo opuesto. Una taberna donde durante años se activó cantar borracho termina, lentamente, subsidiando cantar borracho a quienes entran nuevos.

Esto no es decoración filosófica, es mecánica concreta. Cuando un personaje entra a un lugar y el motor calcula su loadout, los modificadores del lugar entran en el cálculo y cambian qué memes son baratos para él en ese contexto. El mismo personaje en dos lugares distintos produce loadouts distintos. Esa es la pieza que produce arcos de personaje emergentes cuando un agente cambia de entorno por mucho tiempo.

La consecuencia conceptual más importante es la que se llama coproducción agente-mundo. Los personajes no son separables del lugar donde están. Los lugares no son separables de quienes los habitan. Cambiar uno cambia al otro, gradualmente, a lo largo de meses de juego. Esta circularidad es lo que vuelve vivos a los entornos.

## Cómo está organizado este skill

Los aspectos detallados del sistema espacial viven en archivos de referencia separados. La razón es que cuatro subdominios distintos tocan código distinto y conviene poder cargarlos por separado.

El archivo references/grilla-jerarquica.md cubre la estructura espacial misma: cómo se modelan las celdas en niveles jerárquicos, cómo se cargan lazy en memoria, cómo se calculan vecinas y descendientes, cómo se decide qué celdas simular con detalle versus solo estadísticamente. Cargalo cuando el trabajo sea sobre la arquitectura del espacio, no sobre los lugares específicos que viven en él.

El archivo references/memetario-de-lugares.md cubre la mecánica de cómo los lugares afectan cognitivamente a sus habitantes: el memetario simbólico, los modificadores de costo, el bucle de retroalimentación donde los lugares cambian con quienes los habitan. Cargalo cuando estés diseñando un nuevo lugar significativo o tuneando los modificadores que aplica.

El archivo references/secretos-y-objetos.md cubre los dos sistemas que pueblan los lugares con contenido descubrible: los secretos sembrados que se activan al entrar bajo ciertas condiciones, y los objetos del mundo con sus reinos, ciclos de vida, e interacciones. Cargalo cuando estés sembrando contenido narrativo en el mapa o diseñando un objeto cargado.

Si vas a trabajar en una pieza específica, cargá este SKILL.md principal más el archivo de referencia correspondiente. Si el trabajo cruza varios subdominios (por ejemplo, diseñar una nueva celda con su memetario y sus secretos sembrados), cargá los archivos relevantes simultáneamente.

## Las decisiones arquitectónicas que están tomadas

Para que un asistente colaborador no las reabra sin razón, vale la pena listar acá las decisiones del dominio que ya están cerradas.

El espacio se modela como grilla jerárquica con cinco niveles posibles, no como mapa visual. Mundo, región, pueblo, lugar específico, interior. Cada celda es un objeto con su propio estado. La razón es que una grilla jerárquica permite carga lazy (solo cargar en memoria lo cercano al jugador) y velocidad de propagación variable según nivel (rumores cruzan rápido entre interiores del mismo pueblo, lento entre regiones).

Cada lugar tiene memetario simbólico y modificadores de costo. No es opcional. Un lugar sin memetario simbólico es escenografía pasiva, lo cual rompe la promesa del proyecto sobre coproducción agente-mundo. Cuando se diseña un lugar nuevo, el primer paso es definir su memetario simbólico, no su descripción visual.

Los secretos sembrados son contenido narrativo que James como autor pone en celdas específicas, no contenido generado por el LLM en tiempo real. La razón es que el contenido sembrado tiene calidad estética garantizada (vos lo escribiste), mientras que el generado en tiempo real tiene varianza alta. El LLM se invoca para narrar el descubrimiento, pero el contenido del secreto es preescrito.

Los objetos del mundo se clasifican por reino (mineral, vegetal, animal, humanoide, divino, espectral, conceptual) y pueden ser híbridos (mineral-vegetal para una flor de cristal). Los reinos compuestos son donde se concentra lo numinoso del mundo: cosas que violan la lógica natural y por lo tanto cargan significado divino o cósmico. Esta clasificación no es decoración taxonómica, es información que el motor usa para decidir cómo se comportan los objetos.

## El bucle de retroalimentación

Una pieza conceptual que conviene tener clara antes de tocar código en cualquier subdominio. El sistema espacial está acoplado en bucles de retroalimentación que producen sensación de mundo vivo. Los agentes son moldeados por los lugares (a través de los modificadores). Los lugares son moldeados por los agentes (a través de la activación repetida que afecta lentamente sus memetarios simbólicos). Los dioses inyectan en agentes y a veces en lugares (memes con activación contextual). Los agentes mueren y se llevan piel cognitiva consigo. Los lugares quedan cargados con la sombra de quienes los habitaron.

Cuando programes algo del sistema espacial, fijate dónde toca este bucle. Una celda no es solo un punto en un grid, es un nodo del bucle. Un objeto no es solo un item con propiedades, puede ser un nodo del bucle si está cargado simbólicamente. Los puntos donde las cosas se entrelazan son donde el sistema cobra vida.

## La integración con el resto del sistema

Para no perder de vista cómo este territorio se conecta con los demás, vale la pena explicitar los puntos de contacto principales.

Con el memetario, la integración más fuerte: los modificadores de costo de los lugares entran en el cálculo de loadout de los agentes que los habitan. Cada vez que se calcula un loadout, se consulta el memetario simbólico del lugar actual del agente. Esto significa que la operación cargar_lugar es frecuente.

Con el grafo de información, la integración pasa por la propagación: la velocidad de propagación de rumores depende del nivel jerárquico de las celdas. Un rumor en una celda nivel 4 (interior) se mueve rápido a otras celdas nivel 4 dentro del mismo lugar. Cruzar a un nivel superior es más lento.

Con el motor de drama (Blades), la integración pasa por las consecuencias narrativas: una mala consecuencia en un Score puede modificar el estado de la celda donde ocurrió, dejar huellas que otros descubren después, o avanzar clocks asociados al lugar.

Con la integración con LLM, la integración pasa por los prompts: cuando el LLM narra una escena en un lugar, el contexto que recibe incluye la descripción del lugar y su memetario simbólico, lo que tiñe el tono de la narración aunque no se modifique el comportamiento del personaje.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera, no diseñes lugares sin memetario simbólico. La tentación natural cuando se modela un nuevo lugar es escribir su descripción visual primero. Pero la descripción visual es lo menos importante para el sistema. Lo crítico es el memetario simbólico y los modificadores. Si esos están bien definidos, el LLM puede generar la descripción visual desde ellos. Si solo está la descripción visual, el lugar es escenografía pasiva.

Segunda, el alcance del MVP no incluye múltiples lugares interconectados. La taberna de Cala Norte es UNA celda. Para el MVP no hay grilla jerárquica activa porque solo hay un lugar. Esto significa que si te encontrás programando lógica de carga lazy o navegación entre celdas para el MVP, estás haciendo trabajo que no se va a usar todavía. La arquitectura debe ser extensible (los modelos Pydantic deben soportar la jerarquía completa) pero la implementación de la lógica de movimiento puede esperar.

Tercera, los lugares son artefactos curados, no generados procedurally. La tentación de proyecto de "generar lugares automáticamente con LLM cuando el jugador llega a una zona nueva" produce mundos genéricos. James escribe los lugares importantes. El LLM puede ayudar a redactar descripciones, pero los memetarios simbólicos y los modificadores los decide James como autor del mundo. Esto es trabajo manual de worldbuilding, no procedural generation.
