# ADR-003: El estado del mundo vive en archivos portables, cada mundo es una instancia independiente

*Estado: aceptada — Junio 2026*

---

## Contexto

Dado que el motor mantiene el estado del mundo (ADR-001), hay que decidir cómo se representa y persiste ese estado. Las opciones de persistencia condicionan la portabilidad, la facilidad de respaldo, la capacidad de inspección, y las puertas que se abren o cierran para el futuro (compartir mundos, escalar a muchos usuarios, abrir el código).

El proyecto es, según la Fase 0, para el autor primero, de evolución lenta, y con un futuro abierto donde podría crecer a muchos usuarios o abrirse como código libre. La decisión de persistencia debería servir al presente simple sin cerrar el futuro.

## Opciones consideradas

### Opción A: Base de datos relacional central

Todo el estado en una base de datos relacional (PostgreSQL o similar). Mundos, entidades, hechos, todo en tablas.

Ventajas: queries potentes, integridad referencial, maduro y conocido, escala bien a muchos datos.

Desventajas: pesado para un proyecto que empieza siendo de un usuario, requiere un servidor de base de datos corriendo, dificulta la portabilidad (no podés copiar un mundo con un cp), mezcla todos los mundos en una sola base.

### Opción B: Todo en archivos, cada mundo una carpeta portable

El estado de cada mundo vive en archivos dentro de una carpeta. JSON para datos legibles, SQLite para queries rápidas e índices dentro de ese mundo, formatos de grafo para el grafo. Un mundo es una carpeta que se copia, se respalda, se mueve.

Ventajas: portabilidad total (un mundo es una carpeta), respaldo trivial (copiar la carpeta), inspección humana (los JSON se leen), independencia entre mundos (cada uno aislado), sin servidor que mantener, alineado con la visión de mundos como instancias independientes.

Desventajas: queries entre mundos imposibles o costosas (pero no se necesitan), menos eficiente para volúmenes muy grandes de datos, hay que gestionar la consistencia entre los distintos archivos de un mundo a mano.

### Opción C: Híbrido, base central para metadatos y archivos para contenido

Una base liviana para índices globales y archivos para el contenido pesado.

Ventajas: combina queries globales con portabilidad parcial.

Desventajas: complejidad de mantener dos sistemas sincronizados, rompe la portabilidad total, prematuro para las necesidades actuales.

## Decisión

Se adopta la Opción B: todo en archivos, cada mundo es una carpeta independiente y portable.

Dentro de la carpeta de un mundo se usan los formatos apropiados a cada tipo de dato: JSON legible para los datos que conviene poder leer e inspeccionar a mano (entidades, lugares, hechos, configuración), SQLite para los datos que se consultan con frecuencia y se benefician de índices (logs, historial de turnos, índices de búsqueda), y formatos de serialización de grafo para el grafo de información y propagación.

Un mundo es autocontenido: copiando su carpeta se copia el mundo entero, con todo su estado, su historia, sus entidades. Mover un mundo de una máquina a otra es copiar una carpeta. Respaldar es copiar. No hay servidor de base de datos que mantener ni estado global compartido entre mundos.

## Consecuencias

### Positivas

Portabilidad total, que es la propiedad que mantiene abiertas las puertas del futuro identificadas en la Fase 0. Un mundo que es una carpeta puede correr en la máquina del autor hoy y en un servidor mañana sin cambiar su naturaleza. Si el proyecto se abre como código, los mundos son compartibles como carpetas. Esta decisión es el seguro de escalabilidad y de apertura, sin costo presente.

Respaldo e inspección triviales. El autor puede leer los JSON para entender qué tiene su mundo, puede versionar un mundo con git, puede respaldarlo copiándolo.

Independencia entre mundos, coherente con la visión de engine donde cada ficción es su propia instancia. Un bug o corrupción en un mundo no afecta a otros.

Sin infraestructura que mantener. No hay servidor de base de datos, lo que simplifica el desarrollo y la operación, apropiado para un proyecto personal.

### Negativas

Las consultas que cruzan muchos mundos son costosas o imposibles. Pero el proyecto no las necesita: cada mundo se juega por separado. Si en un futuro de muchos usuarios hicieran falta queries globales (por ejemplo, estadísticas sobre todos los mundos), habría que agregar una capa de índices, que es trabajo de ese futuro, no de ahora.

Menos eficiente para volúmenes de datos muy grandes dentro de un mundo. Un mundo con cientos de miles de entidades y hechos podría empezar a sufrir con archivos. Mitigación: el SQLite dentro del mundo absorbe las necesidades de query intensivo, y la mayoría de los mundos no llegarán a esos volúmenes. Si alguno lo hace, ese mundo específico puede migrarse a una persistencia más pesada sin afectar a los demás.

La consistencia entre los distintos archivos de un mundo (JSON, SQLite, grafo) hay que gestionarla en código, porque no hay una base de datos única que garantice integridad referencial. Esto es trabajo real y una fuente potencial de bugs: si se actualiza el grafo pero no el JSON correspondiente, el mundo queda inconsistente. Mitigación: centralizar las operaciones de escritura de estado en una capa que mantenga los archivos sincronizados, y tener operaciones de verificación de consistencia.

## Notas de implementación

La estructura de directorios de un mundo está esbozada en el documento técnico de Codex. Esta decisión hereda directamente la filosofía de persistencia de Fray Tomás, que ya usa archivos (SQLite, JSON, grafo) y es portable. El mapa de reuso de Fray Tomás clasifica esta filosofía de persistencia como reutilizable directo.

La capa que centraliza las escrituras de estado y mantiene la consistencia entre archivos es un componente a diseñar con cuidado, porque es donde se origina el riesgo de inconsistencia mencionado en las consecuencias negativas.
