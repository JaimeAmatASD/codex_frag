# ADR-004: La información se modela como grafo dirigido con árboles de mutación

*Estado: aceptada — Junio 2026*

---

## Contexto

La promesa central de Codex Fragmentum, según la Fase 0, incluye que la información es física: vive en personajes, viaja, se deforma al moverse, se pierde si su portador muere. Hace falta decidir cómo se modela la información para que esa promesa sea concreta y no solo retórica.

La decisión condiciona cómo se representa qué sabe cada personaje, cómo se transmite información entre ellos, cómo se registra la deformación de los rumores, y cómo se consulta el conocimiento de un personaje.

## Opciones consideradas

### Opción A: Flags booleanos por personaje

Cada personaje tiene un conjunto de hechos que conoce o no conoce. Saber es binario: conocés el hecho o no.

Ventajas: simplísimo de implementar, consultas triviales.

Desventajas: no modela la deformación (un rumor o se sabe o no, no se sabe deformado), no modela versiones distintas del mismo hecho circulando, no captura la promesa de información que muta. Es exactamente el modelo que el proyecto quiere superar.

### Opción B: Grafo dirigido con árboles de mutación

Cada hecho del mundo es la raíz de un árbol. Cada vez que el hecho se transmite de un personaje a otro, se crea un nodo nuevo: la versión que el receptor entendió, derivada de la versión que el emisor le contó, filtrada por el cristal cognitivo del receptor. El árbol registra todas las versiones que circulan, con su linaje (de qué versión deriva cada una), su contenido, y su distancia respecto a la verdad original.

Ventajas: modela la deformación con precisión (cada salto es un nodo con su mutación), permite versiones múltiples del mismo hecho circulando simultáneamente, captura el linaje de cada rumor (se puede rastrear cómo se deformó), realiza la promesa central del proyecto.

Desventajas: mucho más complejo de implementar, el grafo crece con cada transmisión, requiere decisiones sobre cuándo podar o archivar versiones viejas, las consultas son más costosas que con flags.

### Opción C: Versiones por personaje sin linaje

Cada personaje tiene su propia versión de cada hecho que conoce, pero sin registrar de quién la recibió ni de qué versión deriva.

Ventajas: modela la deformación, más simple que el grafo completo.

Desventajas: pierde el linaje (no se puede rastrear la cadena de deformación), pierde la capacidad de analizar cómo se propagó un rumor, pierde la estructura de árbol que permite entender la divergencia de versiones.

## Decisión

Se adopta la Opción B: grafo dirigido con árboles de mutación, implementado sobre NetworkX MultiDiGraph.

Cada hecho del mundo tiene una versión raíz que representa la verdad objetiva (exista o no alguien que la conozca exactamente). Cada transmisión genera un nodo de versión derivado, con su contenido, su embedding semántico, su nodo padre (de qué versión deriva), su emisor y receptor, y su distancia a la raíz medida por similitud coseno. El grafo registra también las relaciones entre entidades (quién conoce qué versión, quién transmitió a quién, quién está dónde).

El detalle completo de la estructura, las operaciones de propagación, y las consultas de conocimiento está en el skill de grafo de mundo. Esta decisión establece la elección estructural de fondo: grafo con linaje, no flags ni versiones sin linaje.

## Consecuencias

### Positivas

Realiza la promesa central del proyecto. La información efectivamente muta, viaja, se deforma con linaje rastreable. La frase "la verdad muere con el testigo" se vuelve mecánica concreta: si el portador de la versión más fiel muere, esa versión deja de propagarse y solo sobreviven las más deformadas.

Permite análisis ricos. Se puede rastrear cómo un rumor se deformó a lo largo de su cadena de transmisión, qué prismas cognitivos lo modificaron, cuánto se alejó de la verdad. Esto es material narrativo y también herramienta de depuración.

Permite versiones múltiples coexistiendo. Un personaje puede haber oído el rumor por dos fuentes con dos deformaciones distintas, y el sistema lo representa.

### Negativas

Complejidad de implementación alta. Es uno de los componentes nuevos más grandes del proyecto (el mapa de reuso de Fray Tomás lo clasifica como nuevo, no reutilizable, porque Fray Tomás es agente único y no propaga información). Esta complejidad es trabajo real y sustancial.

El grafo crece con cada transmisión. Sin gestión, podría crecer sin límite y degradar el rendimiento. Requiere una estrategia de envejecimiento y archivado de versiones viejas que no se transmiten hace mucho. Esta estrategia es trabajo adicional, mencionado como diferible al MVP pero necesario después.

Las consultas son más costosas que con flags. Saber qué versión de un hecho conoce un personaje requiere recorrer el grafo, no leer un booleano. Mitigación: índices secundarios que mapean directamente entidad y hecho a la versión conocida, a costa de mantener esos índices.

Riesgo de sobre-modelar. No todos los hechos del mundo merecen un árbol de mutación. Los hechos triviales (qué desayunó alguien) no necesitan esta maquinaria. Hay que tener disciplina sobre qué hechos se modelan como hechos del mundo con su árbol, y cuáles son solo atmósfera narrada sin tracking. Modelar todo con grafo sería desperdicio.

## Notas de implementación

Esta decisión depende de ADR-001 (el motor mantiene el estado) y de ADR-003 (el estado vive en archivos, el grafo se persiste con serialización de grafo dentro de la carpeta del mundo). Es uno de los componentes que más se acopla con el motor cognitivo, porque la mutación de cada versión usa el loadout del receptor como prisma. El skill de grafo de mundo desarrolla esta interdependencia.
