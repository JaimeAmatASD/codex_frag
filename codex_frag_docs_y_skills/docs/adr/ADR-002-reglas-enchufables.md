# ADR-002: El sistema de reglas de juego es una capa enchufable, separada del núcleo

*Estado: aceptada — Junio 2026*

---

## Contexto

Codex Fragmentum incorpora mecánicas de juego adaptadas de Blades in the Dark: tiradas con tres resultados, posición y efecto, stress y trauma, vicios, clocks. Estas mecánicas producen el drama estructurado del juego.

La pregunta arquitectónica es si esas mecánicas son parte del núcleo de Codex o son una capa separable. La respuesta condiciona si Codex es un juego concreto (el juego de Blades-en-un-mundo-vivo) o un engine de ficciones que puede usar distintos sistemas de juego.

La visión del proyecto, establecida en la Fase 0, es que Codex es un engine para crear ficciones, no una ficción ni un juego concreto. Distintos autores que usen el engine querrán distintos sistemas de resolución: uno querrá Blades, otro algo tipo D&D, otro un sistema sin dados donde la resolución es puramente narrativa, otro un sistema propio. Si Blades estuviera incrustado en el núcleo, Codex sería el-engine-de-Blades, no un engine general.

## Opciones consideradas

### Opción A: Blades incrustado en el núcleo

Las mecánicas de Blades son parte integral del motor. El núcleo sabe de tiradas, posición, efecto, stress.

Ventajas: implementación más simple y directa, no hay que diseñar una interfaz de abstracción, todo está integrado.

Desventajas: imposible cambiar de sistema de reglas sin reescribir el núcleo, contradice la visión de engine general, ata a Codex a un sistema de juego concreto para siempre.

### Opción B: Sistema de reglas como capa enchufable detrás de una interfaz

El núcleo no sabe de Blades. Define una interfaz abstracta de "sistema de reglas" que cualquier sistema concreto implementa. Blades es una implementación de esa interfaz. Para usar otro sistema, se implementa la interfaz de otra manera, sin tocar el núcleo.

Ventajas: coherente con la visión de engine, permite múltiples sistemas de juego, protege el núcleo de cambios en las reglas, permite que distintos mundos usen distintos sistemas.

Desventajas: requiere diseñar la interfaz de abstracción, lo cual es trabajo extra y riesgo de sobreingeniería, agrega una capa de indirección que puede complicar la depuración.

## Decisión

Se adopta la Opción B con una salvedad anti-sobreingeniería importante.

El núcleo (memetario, autoobservación, plasticidad, propagación de información, mundo, espacio) no depende del sistema de reglas. El sistema de reglas se conecta al núcleo a través de una interfaz definida. Blades es una implementación concreta de esa interfaz, no parte del núcleo.

La frontera entre núcleo y sistema de reglas es la siguiente. El núcleo provee servicios cognitivos y de estado: dado un ser y una situación, sabe calcular su loadout, sabe cuán afín o adverso le es el contexto, sabe qué memes se le activan, sabe el estado del mundo. El sistema de reglas consume esos servicios y decide cómo se resuelven las acciones dramáticas: Blades los traduce a posición, efecto y tiradas; otro sistema los traduciría a otra mecánica. La frontera es que el núcleo provee el estado cognitivo y del mundo, y el sistema de reglas decide cómo ese estado se convierte en resolución de acciones.

La salvedad anti-sobreingeniería: no se diseña la interfaz universal de sistemas de reglas perfecta y general desde el principio. Se diseña la interfaz mínima que Blades necesita, con la disciplina de no incrustar Blades en el núcleo. La generalización de la interfaz se hace cuando exista un segundo sistema de reglas y se vea qué tienen en común, no por especulación previa. Un solo sistema de reglas bien separado del núcleo es suficiente para el MVP; la intercambiabilidad real se valida recién con el segundo.

## Consecuencias

### Positivas

Codex sigue siendo un engine general y no se ata a Blades. La visión de la Fase 0 se preserva en la arquitectura.

El sistema de reglas se puede cambiar, reemplazar o tener en variantes sin tocar el núcleo. Un autor puede traer su propio sistema de juego.

El núcleo queda más limpio conceptualmente, porque no mezcla la lógica cognitiva y de mundo con la lógica de mecánica de juego. Son dos preocupaciones separadas.

### Negativas

Hay trabajo extra de diseñar la interfaz, aunque sea mínima. Incrustar Blades habría sido más rápido.

La indirección puede complicar la depuración: cuando algo sale mal en una resolución de acción, hay que mirar tanto el núcleo (que proveyó el estado) como el sistema de reglas (que lo interpretó), en lugar de un solo lugar.

Existe el riesgo, que la salvedad busca mitigar, de que diseñar la interfaz se convierta en un agujero de sobreingeniería. Hay que vigilar activamente que la interfaz se mantenga mínima y crezca solo por destilación de casos reales.

## Notas de implementación

Esta decisión es un refinamiento de ADR-001. El núcleo que mantiene el estado (ADR-001) provee ese estado al sistema de reglas a través de la interfaz definida acá.

El skill de Blades documenta la implementación concreta del sistema de reglas, pero conviene tener presente que es una implementación de la interfaz, no el núcleo mismo. Si en el futuro se construye un segundo sistema de reglas, merecerá su propio skill, y la interfaz común se documentará entonces.
