# ADR-007: El contenido es enchufable — mundos, lore y seres como cartuchos

*Estado: aceptada — Julio 2026. Origen: directiva de James, adaptada al template de ADRs del proyecto. Cuestiones abiertas listadas al final; no bloquean.*

---

## Contexto

Codex Fragmentum es un engine, no un mundo (VISION_FASE0). Dos decisiones previas ya establecieron enchufabilidad parcial: el ADR-002 hizo intercambiable el sistema de reglas (Blades como opción, no esencia) y el ADR-003 hizo de cada mundo una instancia independiente y portable. Esta decisión extiende el principio al contenido mismo: mundos, paquetes de lore, y seres individuales deben poder enchufarse y desenchufarse de la máquina. Sacar un ser de un mundo y ponerlo en otro. Importar un paquete de lore. Retirar contenido sin romper el resto.

La metáfora rectora: el contenido es cartucho, la máquina es Codex.

Hay base técnica heredada (la clase Memetario ya es parametrizable por path, así que un ser es potencialmente un paquete autocontenido a nivel de archivos) y hay precedente diegético en el material semilla del proyecto: seres que atraviesan mundos, que vivieron el final de otros mundos, que fueron otras cosas antes de ser lo que son. La ficción que este engine quiere albergar ya contiene la idea; esta decisión la vuelve arquitectura.

## Opciones consideradas

### Opción A: Sin portabilidad de contenido

Cada mundo es una isla total: sus seres y su lore nacen y mueren con él. Nada se comparte entre mundos.

Ventajas: cero costo de diseño, cero namespacing, cero preguntas de canon.

Desventajas: contradice la identidad de engine (un engine cuyo contenido no se reutiliza empuja al autor a la deriva de mundo único); desperdicia el material semilla como biblioteca; cierra la puerta a una futura comunidad de cartuchos; y pierde la resonancia temática de seres que migran entre mundos.

### Opción B: Contenido linkeado y sincronizado entre mundos

Un personaje puede existir "vivo" en varios mundos a la vez, con su estado sincronizado: lo que le pasa en uno repercute en los demás.

Ventajas: la fantasía del personaje único y continuo a través de mundos.

Desventajas: es sincronización distribuida, uno de los problemas más infernales de la ingeniería de software, con conflictos de estado, relojes de mundos distintos, y dependencias entre instancias que destruyen la independencia del ADR-003. Además exige un árbitro de canon (¿cuál versión del personaje es "la verdadera"?). Costo desproporcionado y filosofía contraria al proyecto.

### Opción C: Enchufar es copiar (fork), nunca linkear

El contenido se empaqueta y se copia. Un ser o un lore enchufado en un mundo nuevo es un fork: diverge de su origen y no se sincroniza jamás. No existe "el mismo" personaje vivo en dos mundos; existen dos descendientes de un mismo paquete.

Ventajas: preserva por diseño la independencia y portabilidad de las instancias (ADR-003); evita la sincronización distribuida por construcción; no necesita árbitro de canon; y es temáticamente coherente con el proyecto entero: en un mundo donde la información muta al viajar, que los seres diverjan al viajar es la misma ley aplicada a las almas. Dos Niñas Pak divergentes son ambas legítimas, como dos versiones de un rumor.

Desventajas: renuncia definitiva a la continuidad inter-mundos de un personaje (aceptada conscientemente); las preguntas de canon entre forks quedan sin árbitro por diseño.

## Decisión

Se adopta la Opción C, con la siguiente estructura.

**Tres granularidades de enchufe.** Mundo (la instancia completa, ya cubierta por ADR-003). Paquete de lore (un subgrafo de hechos más lugares, seres menores y fuentes). Ser (cuerpo cognitivo más corpus más biografía).

**El paquete de un ser separa cuatro capas.** Lo que viaja: piedras fundacionales, memes operativos con sus pesos congelados al momento de exportar, hitos biográficos, corpus de fuentes, voz. Lo que se recalcula al importar: los embeddings, según el modelo de embeddings configurado en el mundo destino. Lo que pertenece al mundo y no viaja: posición en la grilla, aristas del grafo de relaciones, nodos de información que el ser posee en los árboles de mutación. Lo que pertenece a las reglas y no viaja: la hoja mecánica (stress, trauma, stats), que se regenera con el sistema de reglas del mundo destino (ADR-002).

Nota de coherencia con la regla 1 (persistencia): el estado vivo de un ser (pesos actuales, activaciones) sigue viviendo únicamente en el SQLite del mundo mientras el ser está enchufado; el paquete se ARMA al exportar, extrayendo y congelando ese estado. Exportar es fotografiar, no mudar la fuente de verdad.

**Gradiente de enchufe, apoyado en ADR-006.** Un ser puede entrar a un mundo en cualquier nivel de complejidad: primero como leyenda (solo sus hechos y rumores circulando por el grafo de información, sin cuerpo cognitivo), luego como ser de nivel bajo, eventualmente como alma completa, con posibilidad de ascender dentro del mundo destino según la historia lo pida. El enchufe más barato de un personaje es enchufar su fama.

**Identificación: ID local estable más campo de origen (decisión de arquitectura delegada y tomada).** Toda entidad (ser, lugar, hecho) tiene un ID local estable y limpio (marcos, nina_pak) más un campo origen que registra de qué mundo o paquete proviene (cala_norte, vc). El identificador compuesto (cala_norte:marcos) se materializa solo al exportar, importar, o cuando dos mundos se tocan; dentro de un mundo no se usa, porque la carpeta del mundo ya es el namespace. Razonamiento: lo caro de retrofitear no es el prefijo en cada string sino la estabilidad de los IDs y la trazabilidad del origen, y ambas se obtienen sin pagar la verbosidad del prefijo literal en todo el código y los datos. Si al importar hay colisión de ID local, la política de importación renombra o prefija en ese momento (regla de la herramienta futura, no del dato presente).

## Alcance para el MVP (lo único que se hace ahora)

No se construye tooling de importación/exportación ni formato de paquete. Solo tres restricciones de diseño, baratas hoy y caras de retrofitear, para no bloquear el futuro.

Primera: IDs locales estables más campo origen en toda entidad nueva, desde los primeros hechos del paso 2 y aplicándolo a los seres existentes (un campo más en su JSON, con default igual al mundo que los contiene).

Segunda: cada ser vive en su propia carpeta autocontenida dentro de la carpeta del mundo (ser.json y, cuando llegue el paso 4, su corpus al lado). El estado vivo NO se muda ahí: sigue en el SQLite del mundo (regla 1).

Tercera: cuando exista la hoja mecánica del sistema de reglas (paso 3), se persiste en archivo separado del cuerpo cognitivo, para que la separación de capas del paquete sea un hecho de disco y no una promesa.

## Consecuencias

### Positivas

El contenido se vuelve reutilizable entre mundos, y el material semilla del proyecto pasa de ser lore de un mundo futuro a biblioteca de componentes enchufables. Se refuerza la identidad de engine frente a la deriva de mundo único. Queda habilitada, sin diseñarla hoy, una futura comunidad de cartuchos (coherente con los futuros de apertura de la Fase 0). Y la coproducción agente-mundo ya define qué le pasa a un ser trasplantado: el caso del benedictino en la tribu vikinga es, sin cambios, la mecánica de aterrizaje de un personaje enchufado — el mundo destino modifica los costos de sus memes y el arco emerge solo.

### Negativas y costos aceptados

El campo origen agrega un dato más a toda entidad desde el día uno (mucho más barato que el prefijo literal, pero no gratis). El principio invita a un scope creep nuevo, construir import/export antes de tener juego, que queda explícitamente prohibido por la regla del jugable mínimo: el tooling se construye cuando haya dos mundos reales que quieran intercambiar algo. Las preguntas de canon entre forks quedan sin árbitro por diseño: dos versiones divergentes de un mismo ser son ambas legítimas, y quien quiera una verdad única no la va a encontrar en el sistema. Los embeddings deben recomputarse en cada importación, con su costo en tiempo (no en dinero: son locales).

## Cuestiones abiertas (diferidas, no bloquean)

La política de equipaje de saber al enchufar un ser queda deliberadamente ABIERTA, sin default (decisión de James): (a) el ser viaja con el subgrafo de información que poseía, importado como hechos de origen externo cuyo único testigo es el recién llegado, máximamente compatible con "donde la verdad muere con el testigo"; o (b) viaja solo con su alma y llega sin saber. Será una opción elegible por enchufe cuando la herramienta exista, y la experiencia de juego real informará si conviene un default.

El formato concreto del paquete (manifiesto, versión de esquema, versión del modelo de embeddings). Las reglas de merge de un paquete de lore en el grafo destino (colisiones, integridad referencial). Y los hitos biográficos que referencian hechos inexistentes en el mundo destino, con propuesta preliminar registrada: los hitos son cicatrices autocontenidas y viajan siempre; la narración los trata como pasado no verificable del personaje.

## Notas

Esta decisión generaliza ADR-002 (reglas enchufables) y ADR-003 (mundos independientes y portables) hacia el contenido, y se apoya en ADR-006 (niveles de complejidad con interfaz uniforme) para el gradiente de enchufe. Hereda de la verificación del código de Fray Tomás la viabilidad técnica del ser como paquete (Memetario parametrizable por path). Las tres restricciones del alcance MVP están integradas en los prompts de arranque de las fases 2, 3 y 4. La referencia al material semilla queda pendiente de precisión hasta que el semillero esté versionado en el repositorio.
