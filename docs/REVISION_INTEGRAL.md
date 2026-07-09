# Codex Fragmentum — Revisión integral del proyecto
## Qué está desalineado, qué falta, qué está sólido
*Auditoría de toda la documentación, skills y decisiones — Junio 2026*

---

## Qué se revisó y el veredicto general

Se revisó el cuerpo completo del proyecto: los seis ADRs, el documento de corpus, el mapa de reuso, la verificación del código de Fray Tomás, el prompt de arranque, los skills instalados (arquitectura, blades, llm-prompts), y mediante el transcript, los tres documentos grandes de la primera sesión (conceptual, técnico, evaluación crítica) y los skills restantes.

El veredicto general: el diseño reciente (ADRs, corpus, verificación, prompt de arranque) es sólido y consistente entre sí. El problema está en la capa anterior: los documentos grandes y los skills fueron escritos ANTES de las decisiones más importantes de esta sesión (la Fase 0 que redefinió a Codex como engine, la verificación del código, el sistema de corpus completo), y no fueron actualizados. El proyecto tiene dos estratos de documentación que se contradicen en puntos importantes, y como los skills se cargan automáticamente en cada conversación futura, esas contradicciones van a confundir a los asistentes que trabajen en el proyecto.

Nada de esto es grave todavía porque no hay código construido sobre las contradicciones. Es exactamente el momento barato de arreglarlo.

---

## Hallazgos, priorizados

### CRÍTICO 1: El skill maestro define a Codex como lo que ya no es

El skill codex-fragmentum-arquitectura, incluida la versión con lecciones entregada hoy, define al proyecto en su frontmatter y en su sección "El proyecto en una frase" como "una novela interactiva solitaria con LLM como motor narrativo". La Fase 0 redefinió a Codex como un ENGINE para crear ficciones, donde la novela de Cala Norte es una ficción posible hecha con el engine, no el engine mismo. Esta es la decisión de identidad más importante del proyecto y el documento que se carga en cada conversación futura dice lo contrario.

Consecuencia si no se corrige: cada asistente futuro va a trabajar con la identidad vieja, tomando decisiones de "novela única" donde corresponde pensar "engine general". La corrección es una edición del skill (frontmatter y dos secciones).

### CRÍTICO 2: El skill de Blades contradice el ADR-002

El skill codex-fragmentum-blades declara que "sin el motor de drama, el proyecto no funciona" y llama a Blades "una de las dos columnas que sostienen el proyecto entero". El ADR-002 y la Fase 0 decidieron lo contrario: el sistema de reglas es una capa ENCHUFABLE e intercambiable, Blades es una opción que cada autor puede reemplazar, y está explícitamente en la categoría "intercambiable", no en el núcleo irrenunciable.

Consecuencia si no se corrige: un asistente cargando el skill de Blades va a tratar a Blades como intocable e incrustarlo en el núcleo, exactamente lo que el ADR-002 prohíbe. La corrección es ajustar dos o tres párrafos del skill (el detalle mecánico del skill sigue siendo válido; lo desalineado es el estatus que se atribuye).

### CRÍTICO 3: El flujo del jardinero no tiene diseño en ningún lado

La Fase 0 estableció las dos velocidades de creación como requisito de primera clase: el flujo del arquitecto (definir estructura directamente) y el flujo del jardinero (plantar fragmentos narrativos y que el sistema derive estructura), ambos editando el mismo sustrato. El grep al transcript confirma que este concepto no existe en ningún documento de la primera sesión, y en esta sesión solo el documento de corpus lo roza (el corpus del mundo como jardín de cuentos). No hay diseño de cómo el sistema ingiere un fragmento y deriva entidades, ni siquiera a nivel conceptual de una página.

Consecuencia: el requisito más distintivo de la visión de engine no tiene ni un esbozo de diseño. No es urgente construirlo (no es del MVP), pero un requisito de primera clase sin una página de diseño es un hueco que se olvida. Mínimo necesario: registrarlo formalmente (en la Fase 0 consolidada y una mención en el skill maestro), no diseñarlo en detalle todavía.

### ALTO 4: La Fase 0 sigue sin consolidarse y es la fuente de todo lo demás

Las correcciones de los hallazgos 1, 2 y 3 derivan todas de la Fase 0, que sigue viviendo solo en la conversación. Si esta conversación se pierde antes de consolidarla, la fuente de la identidad del proyecto se pierde con ella. Es el documento pendiente más importante: la visión (engine, problema perenne de Pigmalión, dos velocidades), el núcleo irrenunciable (alma de Fray Tomás: memetario, autoobservación, plasticidad, más autonomía del mundo), y las cuatro categorías (irrenunciable, graduable, intercambiable, prescindible).

### ALTO 5: Los hallazgos de la verificación no se propagaron a los skills especializados

La verificación del código encontró piezas que cambian el contenido de los skills especializados y ninguno fue actualizado: la interferencia productiva (que decidiste incorporar como mecanismo de primera clase) no está en el skill de memetario; el llm_router real de Fray Tomás (el embrión del sistema de tiers, ya funcionando) no está en el skill de llm-prompts; la temperatura emocional como construcción nueva tampoco. Además, los documentos grandes de la primera sesión siguen diciendo sentence-transformers donde el código real usa fastembed.

Recomendación deliberadamente anti-sobreingeniería: NO actualizar los seis skills ahora. Actualizar solo el maestro (hallazgo 1) porque se carga siempre, y parchear cada skill especializado la primera vez que se use en trabajo real. Actualizarlos todos hoy es trabajo especulativo; parchearlos al usarlos es trabajo just-in-time.

### ALTO 6: El SPECULUM sigue siendo núcleo irrenunciable sin diseño propio en Codex

Ya estaba registrado como deuda y sigue abierto, pero la verificación cambió su naturaleza: ahora existe speculum.py (427 líneas funcionando) como prototipo. La deuda ya no es "diseñar la autoobservación desde cero" sino "decidir cómo se adapta el SPECULUM de Fray Tomás a seres de Codex" (frecuencia por nivel de ser, qué hace un ser con lo que ve de sí, cómo alimenta el cambio de pesos). Sigue sin ser del MVP, pero conviene que la Fase 0 consolidada lo nombre como deuda explícita del núcleo.

### MEDIO 7: Tres skills posiblemente no instalados

En el entorno actual solo aparecen instalados tres de los seis skills de Codex: arquitectura, blades y llm-prompts. Los de memetario, grafo-mundo y cartografía existen como archivos .skill pero no figuran entre los skills activos. Puede ser un artefacto de qué se montó en esta conversación, pero conviene que verifiques en claude.ai (Configuración, Skills) que los seis están efectivamente subidos y habilitados. Si faltan tres, las conversaciones futuras sobre el grafo o la cartografía van a trabajar sin su contexto especializado.

### MEDIO 8: No existe un índice maestro de la documentación

El proyecto acumula unas catorce piezas de documentación (tres documentos grandes, seis ADRs, corpus, mapa de reuso, verificación, prompt de arranque, y la Fase 0 por venir) sin ningún documento que las liste, diga qué contiene cada una, y establezca cuál manda cuando se contradicen. Dado el hallazgo de los dos estratos contradictorios, falta sobre todo una REGLA DE PRECEDENCIA escrita. La propuesta natural: los ADRs y la Fase 0 consolidada mandan sobre los skills, y los skills mandan sobre los documentos grandes de la primera sesión, que quedan como referencia histórica y de profundidad conceptual, con una nota al inicio que lo diga. Esto es un README de una página y evita reescribir los documentos grandes (que sería trabajo grande de bajo retorno: su filosofía sigue siendo válida, lo desactualizado son detalles técnicos puntuales).

### MEDIO 9: Decisiones de esta conversación sin registrar en ningún documento

Dos decisiones conversadas hoy no viven en ningún lado: el modo servidor (dejar previsto desde el día uno que el motor pueda exponerse por websocket, para el futuro cuerpo en Godot u otro), y la recomendación sobre cuerpos (texto primero, Godot 2D o vista mapa-grafo como candidatos, Luanti si vóxeles, Minecraft descartado). La primera merece una línea en el prompt de arranque (afecta la estructura inicial del código); la segunda merece un párrafo en la Fase 0 consolidada como nota de futuro.

### MENORES

Vocabulario inconsistente: los documentos recientes dicen "seres" (ADR-006), los skills y documentos viejos dicen "agentes" y "personajes". Conviene elegir uno (sugerencia: "seres" para las entidades del mundo, reservando "agentes" para el sentido técnico de Fray Tomás) y usarlo en adelante, corrigiendo lo viejo solo cuando se toque por otra razón. El skill maestro menciona "pickle de NetworkX" para snapshots; pickle es frágil y el ADR-003 habla de serialización de grafo en general; al construir, preferir formatos no-pickle (GraphML o JSON de nodos/aristas) y corregir la mención cuando se edite el skill. Y el skill maestro dice que el MVP depende de "cuánto reuso se logre", incertidumbre que la verificación ya resolvió; se actualiza junto con el hallazgo 1.

---

## Lo que está sólido y no hay que tocar

Para que la revisión no distorsione: la mayor parte del trabajo reciente pasó la auditoría sin observaciones. Los seis ADRs son consistentes entre sí y con la Fase 0, se referencian mutuamente correctamente, y sus consecuencias negativas anticiparon (y en un caso, predijeron literalmente) los problemas reales encontrados en el código de Fray Tomás. El documento de corpus está alineado con los ADRs y con la filosofía de capas. El prompt de arranque es coherente con la verificación, las lecciones y los ADRs. La verificación del código es el documento mejor anclado del proyecto porque está atado a evidencia. Y la cadena decisión-a-documento de esta sesión (Fase 0 conversada, ADRs, corpus, verificación, prompt) muestra el proceso funcionando bien: el problema es solo que la capa anterior no se enteró de las decisiones posteriores, que es el costo natural de diseñar en capas sucesivas.

---

## Plan de corrección propuesto (barato, priorizado)

Primero, regenerar el skill maestro en versión definitiva única que corrija todo junto: identidad de engine (frontmatter y cuerpo), las dos velocidades mencionadas como requisito, el corpus mencionado entre las decisiones tomadas, vocabulario de seres, la nota de precedencia documental, más las lecciones y el reuso verificado que ya tenía. Un solo archivo para subir una sola vez, en lugar del que quedó pendiente de subir.

Segundo, ajustar los dos o tres párrafos del skill de Blades que le atribuyen estatus de columna irrenunciable, alineándolo con el ADR-002.

Tercero, consolidar la Fase 0 en su documento formal, incluyendo el SPECULUM como deuda nombrada del núcleo, el flujo del jardinero como requisito registrado, y la nota de futuro sobre cuerpos.

Cuarto, escribir el README índice de una página con la regla de precedencia.

Quinto, agregar la línea del modo servidor al prompt de arranque.

Y explícitamente NO hacer ahora: actualizar los skills especializados restantes (se parchean al usarse), reescribir los documentos grandes (quedan como históricos bajo la regla de precedencia), y diseñar el flujo del jardinero en detalle (se registra, no se diseña).

Todo el plan es trabajo de horas, no de días, y después de él la documentación queda coherente para empezar a programar sin que ningún asistente futuro herede contradicciones.
