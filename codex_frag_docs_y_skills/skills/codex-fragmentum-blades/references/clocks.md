# Sistema de clocks — la columna vertebral de la presión narrativa

Este archivo es referencia operativa para cuando estés programando o diseñando los clocks de progreso del proyecto. Los clocks son el mecanismo más transversal del sistema: aparecen durante Scores, durante downtime, durante propagación de información, durante intervenciones divinas, durante simulación lazy del mundo lejano. Por eso merecen su archivo propio que se carga junto con cualquier otro subsistema en el que estés trabajando. Asume que el SKILL.md principal del motor de Blades ya está cargado.

## Qué es un clock y por qué importa

Un clock en Blades, y por extensión en Codex, es un círculo dividido en segmentos que se va llenando a lo largo del juego. Cuando se completa, dispara un evento del mundo. Tiene cuatro variantes principales según la cantidad de segmentos: cuatro, seis, ocho o doce. La cantidad de segmentos comunica narrativamente la magnitud o lentitud del proceso que el clock está modelando.

Esta es la descripción superficial que cualquier persona que haya visto Blades puede repetir. Pero la pregunta importante es por qué esta mecánica tan simple es tan poderosa, y la respuesta tiene tres capas que vale la pena entender bien.

La primera capa es que los clocks vuelven visible el progreso de las amenazas. En la mayoría de los juegos, las amenazas son binarias: están latentes hasta que se activan, momento en que aparecen de golpe. Un clock convierte la amenaza en proceso: el jugador ve que algo se está acercando, ve cuánto le falta, puede tomar decisiones para retrasarlo o acelerarlo. Esto produce tensión sostenida en lugar de sorpresas puntuales. El drama no está en si la amenaza ocurre sino en cuándo y qué tan preparado está el personaje cuando ocurre.

La segunda capa es que los clocks dan agencia mecánica al jugador. Si una amenaza es binaria, el jugador no puede "hacer algo al respecto" hasta que aparece. Si es un clock, el jugador puede dedicar acciones específicas a retrasarla, puede priorizar diferentes amenazas según cuánto les falta, puede decidir aceptar el costo de ignorar una para enfocarse en otra. La gestión de clocks es donde se juega buena parte de la estrategia narrativa del jugador.

La tercera capa, y la más importante para Codex específicamente, es que los clocks son el mecanismo nativo para modelar el avance del mundo durante el time-jump. Cuando el jugador deja pasar un mes, no se simula cada acción de cada NPC. Se avanzan los clocks según reglas, y los que se completan disparan eventos. Esta es la implementación concreta de la simulación lazy. Sin clocks, el time-jump tendría que ser narrativamente arbitrario o computacionalmente caro. Con clocks, es ambas cosas: barato y narrativamente verificable.

## Los tipos de clocks que existen en Codex

Conviene categorizar los clocks por su función narrativa porque eso te ayuda a saber cuándo crearlos, cómo nombrarlos, qué triggers darles. Identifico cinco tipos principales que cubren la mayoría de los casos.

Los clocks de propagación modelan cómo viaja la información por el mundo. Por ejemplo, "el rumor del kraken llega al obispado" puede ser un clock de seis segmentos que avanza un segmento cada vez que el rumor cruza una celda hacia esa dirección. Cuando se completa, dispara el evento "el obispo se entera" que tiene sus propias consecuencias narrativas (puede generar un nuevo clock "el obispo envía un inquisidor"). Estos clocks son típicamente ocultos para el jugador, porque el drama está en que de pronto descubre que la información ya viajó.

Los clocks divinos modelan procesos cosmológicos lentos. "El Dios del Fuego pierde fe" puede ser un clock de ocho o doce segmentos que avanza cada vez que un creyente importante muere, cada vez que un templo se profana, cada vez que un milagro deja de ocurrir cuando debería. Cuando se completa, dispara descalibración del aspecto que sostenía: las llamas dejan de ser lógicas, el calor de hogar se invierte, los ritos no funcionan. Estos clocks son típicamente ocultos hasta que el desbalance empieza a manifestarse, momento en que se hacen parcialmente visibles a personajes con sensibilidad teológica.

Los clocks políticos modelan procesos sociales medios. "El reino se entera de la herejía" o "el gremio de pescadores se rebela" o "la corte sospecha de la reina" son clocks típicos de doce segmentos que avanzan con eventos sociales acumulados. Estos clocks pueden ser parcialmente visibles si el personaje tiene acceso a información política, ocultos si no.

Los clocks personales modelan presiones específicas sobre el personaje. "Tu reputación de loco se consolida en el pueblo" es un clock típico de cuatro segmentos que avanza cuando el personaje hace algo extraño en público. "Tu mujer descubre tu secreto" puede ser de seis segmentos. "Tu salud cede a la edad" puede ser de ocho. Estos clocks son los más intensos dramáticamente y conviene tener varios activos simultáneamente para cada PJ jugado, porque crean la sensación de que el personaje vive en un mundo que aprieta desde múltiples direcciones a la vez.

Los clocks ambientales modelan procesos del mundo natural. "La cosecha falla", "el invierno llega temprano", "el mar se enturbia", "la peste avanza desde el sur". Estos clocks son típicamente parcialmente visibles a través de signos ambientales que el LLM puede narrar (las nubes inusuales, el frío que llega antes, los peces que escasean). Avanzan según reglas de simulación natural más que por acciones de personajes.

Cuando vayas a crear un clock nuevo, fijate primero en qué tipo es. Eso te orienta para decidir cuántos segmentos darle (más segmentos para procesos lentos, menos para procesos rápidos), qué triggers asignarle (eventos específicos del mundo que avanzan ese tipo de proceso), y qué visibilidad tiene para el jugador.

## Los triggers que avanzan un clock

Cada clock define explícitamente qué condiciones lo avanzan. Un trigger es una condición que cuando se cumple, suma uno o más segmentos al clock. La definición de los triggers es donde se concentra la artesanía narrativa del clock: triggers bien diseñados producen sensación de mundo coherente, triggers genéricos producen sensación de mecánica vacía.

Los triggers pueden ser de varios tipos. Triggers de evento específico: cuando ocurre exactamente esta cosa en el mundo, el clock avanza. "Cuando un rumor del kraken cruza a la celda 03_02, avanza el clock 'rumor llega al obispado' en un segmento". Triggers de acción del jugador: cuando el PJ realiza cierto tipo de acción, el clock avanza. "Cuando Marcos hace algo extraño en público, avanza 'reputación de loco' en un segmento". Triggers de paso del tiempo: con cierta probabilidad por tick, el clock avanza pasivamente. "Cada día tiene 10% de chance de avanzar 'salud cede a la edad' en un segmento". Triggers condicionales compuestos: combinaciones de varios eventos que tienen que ocurrir juntos. "Cuando Marcos visita la taberna y bebe demasiado y hay un forastero presente, avanza 'sospechan de Marcos' en dos segmentos".

Cuando programes la estructura de datos de un clock, conviene que cada trigger sea un objeto con tres campos: la condición (que puede ser una expresión booleana o una función), el incremento (cuántos segmentos suma cuando se cumple), y opcionalmente una probabilidad (si el trigger no es determinista). Esto te permite tener clocks con triggers complejos y al mismo tiempo verificarlos eficientemente cada tick: el sistema solo evalúa los triggers cuyas condiciones tienen chance de haberse cumplido.

Una decisión de diseño que vale la pena cerrar antes de programar: los triggers se evalúan una vez por tick (es decir, una vez por día del mundo), o se evalúan en respuesta a eventos específicos (cuando ocurre el evento que un trigger está esperando)? La respuesta correcta es híbrida. Los triggers de paso del tiempo se evalúan en cada tick. Los triggers de evento específico se evalúan cuando ocurre el evento al que están suscriptos. Los triggers de acción del jugador se evalúan inmediatamente después de la acción. Esto evita evaluación innecesaria y mantiene latencia baja.

## Qué pasa cuando un clock se completa

Cuando un clock alcanza su segmento final, dispara su evento de completación. Este evento puede ser de varios tipos.

Puede disparar un evento narrativo, que es típicamente lo que pasa con clocks personales y políticos. "El inquisidor llega al pueblo" es un evento narrativo: aparece un nuevo NPC con piedras fundacionales fuertes, hay una escena de su entrada en el pueblo, los demás NPCs reaccionan, el mundo cambia su tono. Este evento típicamente requiere narración por LLM (tier 2 o 3 según importancia), porque su calidad literaria es lo que el jugador va a recordar.

Puede disparar una transformación de estado, que es típicamente lo que pasa con clocks de propagación. "El obispo se entera" cambia el estado de un NPC: el obispo ahora tiene cierto rumor en su grafo de conocimiento, lo que hace que ciertos comportamientos suyos cambien. Esto puede no requerir narración inmediata: el cambio sucede silenciosamente y se manifestará narrativamente cuando el obispo aparezca en escena.

Puede disparar la creación de un nuevo clock derivado. "El reino se entera de la herejía" puede generar como consecuencia un nuevo clock "los inquisidores convergen sobre el pueblo del herje", que ahora empieza a llenarse desde cero. Esto modela cómo los procesos sociales producen procesos derivados: cada gran evento abre nuevos frentes.

Puede disparar un cambio en el mundo natural o cosmológico. "La cosecha falla" cambia el estado de las celdas agrícolas y dispara consecuencias económicas (clocks de "el hambre se siente en el pueblo"). "El Dios del Fuego pierde fe" descalibra el aspecto del fuego en el mundo, lo que afecta a todos los lugares y objetos vinculados a ese aspecto.

Cuando programes la lógica de completación de clocks, conviene que cada clock tenga un campo "al_completar" que sea una función o una secuencia de operaciones a ejecutar. Esa función puede crear nuevos clocks, modificar estado de NPCs o lugares, invocar al LLM para narrar, marcar otros clocks como afectados, y registrar el evento en el log del mundo para futuras referencias.

## La decisión de visibilidad

Cada clock tiene una propiedad de visibilidad para el jugador. Esta decisión no es trivial y vale la pena pensarla por cada clock que crees.

Visible total significa que el jugador ve el clock con su nombre, sus segmentos totales, y sus segmentos llenos actualmente. La UI lo muestra como un círculo gráfico con label. Esto es apropiado para clocks donde el drama está en verlos llenarse: "el inquisidor llega" debería ser visible al menos parcialmente porque la presión narrativa viene de saber que se acerca.

Visible parcial significa que el jugador ve que el clock existe y conoce su nombre, pero no ve cuántos segmentos están llenos. Solo recibe pistas narrativas que el LLM va sembrando. Esto es apropiado para clocks donde la información parcial produce ansiedad: "tu mujer sospecha de tu secreto" puede ser visible como categoría sin que el jugador sepa exactamente cuán lejos está.

Oculto significa que el jugador no sabe que el clock existe. Solo descubre las consecuencias cuando se completa. Esto es apropiado para clocks de propagación de información que el personaje no debería saber, y para clocks divinos que operan por debajo del radar humano.

Una regla práctica: por cada clock visible que tenés activo en una sesión, conviene tener tres o cuatro clocks ocultos corriendo en paralelo. Los visibles producen tensión consciente, los ocultos producen sensación de que pasan cosas que el jugador no controla. La combinación es lo que hace que el mundo se sienta más grande que el personaje.

## Cómo se acoplan los clocks con el resto del sistema

Para que el sistema de clocks no sea una capa aislada, vale la pena pensar explícitamente en sus puntos de contacto con cada subsistema.

Con el sistema de tiradas: ciertos resultados de tirada avanzan clocks. Una mala consecuencia en un Score puede avanzar el clock "te están buscando" en uno o dos segmentos. Un éxito con costo puede avanzar un clock distinto. El template de prompt que narra el resultado de tirada debería tener acceso a la lista de clocks relevantes y poder decidir cuáles avanzar como parte de la consecuencia narrada.

Con el sistema de stress y trauma: los traumas inyectados en el memetario pueden tener clocks asociados. "El trauma del kraken solidifica" puede ser un clock de seis segmentos que avanza cada vez que el meme experimental se activa exitosamente. Cuando se completa, el meme experimental asciende a operativo permanente. La progresión de los traumas hacia crisis biográfica es esencialmente una cadena de clocks.

Con el sistema de vicios y downtime: las visitas al vicio pueden avanzar clocks de "indulgencia se vuelve hábito" o "los del pueblo notan tus visitas". El downtime largo es donde la mayoría de los clocks pasivos avanzan según sus probabilidades por tick.

Con el sistema de propagación de información: los rumores que cruzan ciertas celdas avanzan clocks de propagación. Cada salto en el árbol de mutación puede avanzar el clock que ese salto representa.

Con el sistema cognitivo: las modificaciones de PF (crisis biográficas) tienen clocks asociados que miden cuánta evidencia se ha acumulado. Cuando el clock de "PF X está siendo cuestionada" se completa, se habilita la modificación.

Cuando programes cualquier subsistema, fijate si toca clocks. Si los toca, programá la integración explícitamente: no asumas que el sistema de clocks va a "darse cuenta solo". Los puntos de contacto deben ser explícitos en el código.

## Cómo se modelan los clocks en datos

Para que la sección sea útil al programar, vale la pena cerrar la estructura de datos concreta. Un clock como objeto Pydantic podría verse así.

```python
class Clock(BaseModel):
    id: str
    nombre: str
    descripcion: str
    tipo: Literal["propagacion", "divino", "politico", "personal", "ambiental"]
    segmentos_total: Literal[4, 6, 8, 12]
    segmentos_actuales: int = 0
    visibilidad: Literal["total", "parcial", "oculto"]
    triggers: list[Trigger]
    al_completar: AccionCompletion
    lugares_relacionados: list[str] = []
    agentes_relacionados: list[str] = []
    creado_en_tick: int
    completado_en_tick: Optional[int] = None
    estado: Literal["activo", "completado", "cancelado"] = "activo"
```

Los triggers y la acción de completación son tipos compuestos que vale la pena modelar con su propio detalle. Pero esta estructura básica te permite empezar a trabajar.

Cuando un clock se completa, conviene marcar `estado = completado` y `completado_en_tick` con el tick actual, en lugar de borrar el clock. Mantener los clocks completados en el sistema te permite reconstruir la historia del mundo más adelante: si en el SPECULUM querés analizar qué presiones vivió un personaje, los clocks completados son la materia prima.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera: los clocks no son temporizadores. Son representación de presión narrativa con triggers específicos. Si te encontrás creando clocks que avanzan automáticamente cada N ticks sin más, estás reduciendo el potencial del mecanismo. Cada clock debería tener triggers específicos del mundo que produzcan sensación de causalidad: el clock avanza porque algo concreto pasó, no porque pasó tiempo abstracto.

Segunda: la regla práctica de balance es tener entre cinco y ocho clocks activos en cualquier momento del juego, distribuidos entre visibles y ocultos. Menos de cinco produce sensación de mundo congelado. Más de ocho produce ansiedad excesiva sobre demasiadas amenazas simultáneas. Cuando James reporte que "el mundo se siente quieto" o "siento que pasan cosas que no entiendo", revisá la cantidad y distribución de clocks antes de tocar otra cosa.

Tercera: cada vez que un clock se completa, es un momento narrativo. Aunque el evento de completación sea silencioso (transformación de estado sin narración inmediata), el sistema debería registrarlo de modo que pueda recuperarse después como material narrativo. El log de clocks completados es parte de la memoria del mundo.
