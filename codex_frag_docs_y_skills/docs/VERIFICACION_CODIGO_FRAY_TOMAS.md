# Codex Fragmentum — Verificación del código real de Fray Tomás
## Qué es código funcionando, qué fue más deseo que realidad
*Actualización del mapa de reuso tras leer el repositorio — Junio 2026*

---

## El veredicto general

La pregunta era cuánto de lo que la documentación de Fray Tomás describía está efectivamente implementado. La respuesta, tras leer el repositorio completo (159 archivos, ~7.100 líneas solo en el motor), es mejor de lo que el mapa de reuso estimaba con cautela: casi todo lo documentado está implementado, y además hay piezas implementadas que la documentación ni mencionaba.

El documento de mejoras técnicas que habías subido presentaba los embeddings, el ritmo circadiano y la memoria episódica como mejoras a futuro. Ese documento quedó desactualizado por tu propio trabajo: las tres cosas están construidas y funcionando. La advertencia que dejé en el mapa de reuso ("verificar contra código real, algunas piezas podrían ser propuestas") resultó casi innecesaria, salvo por una excepción que detallo abajo.

Lo que sí encontré son limitaciones de empaquetado (paths atados a la Pi, una migración de persistencia a mitad de camino) que no son deseo versus realidad sino trabajo de adaptación concreto y acotado. Y una sola pieza que efectivamente fue más deseo que realidad: la temperatura emocional.

---

## Verificado componente por componente

### El motor cognitivo central — todo implementado, reuso directo confirmado

**Memetario (motor/memetario.py, 328 líneas).** La clase Memetario existe, completa: grafo NetworkX, persistencia JSON, los tres tipos de meme (piedra_fundacional, operativo, experimental), el esquema con contra_meme, pregunta_control y cuando_no_usar tal como la documentación decía. Y una sorpresa buena para Codex: ya es una clase con el path parametrizado en el constructor (`Memetario(path=...)`). La transformación de instancia única a clase instanciable, que el mapa estimaba como el trabajo de adaptación principal, está casi regalada: instanciar `Memetario(path_del_agente_X)` por cada ser ya funciona estructuralmente. El trabajo real es organizar dónde vive cada memetario y quitar el path global por defecto.

**Cálculo de loadout (en memetario.py, seleccionar_loadout).** Implementado exactamente como se documentó: PF gratis siempre, score combinando peso histórico (60%) y similitud semántica (40%), multiplicado por bias circadiano, orden descendente, llenado hasta el límite de mana. Reuso directo. La única adaptación para Codex sigue siendo agregar los modificadores de costo del lugar, que es sumar un parámetro y unas líneas.

**Decaimiento (motor/decaimiento.py + lógica en memetario.py).** Implementado con la fórmula exacta documentada (factor asintótico que nunca llega a cero, factor de éxito por activaciones, PF que no decaen). Corre como cron diario. Reuso directo.

**Embeddings (motor/embeddings.py, 267 líneas).** Completamente implementado, con un detalle técnico que conviene conocer: usa fastembed con ONNX en lugar de sentence-transformers directo, porque es más liviano para la Pi. Mismo modelo (all-MiniLM-L6-v2, 384 dimensiones, 100% local). Incluye similitud coseno, batch, caché de vectores, y dos piezas extra valiosas: el clasificador de intención por similitud (que el mapa quería verificar: existe) y seleccionar_fragmentos_relevantes, que es un proto-RAG de selección de fragmentos por relevancia semántica, directamente útil para el corpus de Codex cuando llegue la fase RAG. Reuso directo, y la elección de fastembed es heredable porque Codex también se beneficia de lo liviano.

**Bias circadiano (motor/foco.py).** Implementado. Usa datetime.now(), la hora real, como anticipé: la adaptación para Codex es cambiar la fuente de la hora a la hora del mundo ficcional. Trivial.

**Registro de activaciones (motor/activaciones.py).** Implementado sobre SQLite. Es la materia prima del SPECULUM y de los clusters. Reuso directo del patrón.

### El alma completa — implementada, incluida la autoobservación

**SPECULUM (motor/speculum.py, 427 líneas).** Implementado y es de los módulos más grandes. Lee el DIARIUM acumulado, busca patrones, silencios y evolución, construye un prompt de autoobservación, y parsea propuestas de cambio que devuelve el LLM. Corre cada 20 días con mínimo de 5 entradas (la reflexión necesita acumulación para ser genuina, decisión sabia). Esto importa mucho para Codex: la autoobservación, que en la Fase 0 definiste como parte del núcleo irrenunciable y que yo había marcado como deuda de diseño, ya tiene prototipo funcionando. El SPECULUM de Codex no se diseña desde cero: se adapta este.

**Cambio biográfico (motor/cambio_biografico.py, 458 líneas, el módulo más grande del motor).** Implementado, y no estaba con este detalle en la documentación. Es el sistema de fricción del cambio de identidad: regla del degradé (máximo 2 puntos de cambio por movimiento), evidencia mediana (cambios de 3-5 puntos requieren 3 reflexiones del SPECULUM que lo mencionen), evidencia alta (6+ puntos requieren aprobación del fundador), PF intocables sin aprobación, todo cambio auditado en historial. Esto es el sistema de crisis biográficas de Codex ya prototipado, con la plasticidad protegida por fricción deliberada, que es exactamente la tercera pata del núcleo irrenunciable. Para Codex, "aprobación del fundador" se traduce según el ser: para el PJ, pregunta al jugador; para NPCs, reglas automáticas según nivel.

**Consejo (motor/consejo.py).** Implementado: 4 roles que debaten, umbral de PF, decisión, acta registrada. Confirma el costo (una llamada LLM por voz). La recomendación del mapa se sostiene: no para personajes comunes de Codex, adaptable para la deliberación de dioses.

**Memoria episódica (motor/memoria_episodica.py).** Implementada: consolidación nocturna agrupando entradas del DIARIUM por similitud semántica y sintetizando memorias abstractas, más búsqueda semántica sin costo de API. El mapa la marcaba como diferible para Codex y eso se sostiene, pero el código existe para cuando llegue el momento.

**Deudas morales (motor/deudas_morales.py).** Implementadas, con umbral de alarma (3+ deudas sin compensar disparan Capítulo Extraordinario). Diferible para Codex como decía el mapa, pero existe.

### Los hallazgos que la documentación no mencionaba

Acá está el oro inesperado. Cuatro módulos implementados que no figuraban en los documentos que me habías pasado, y los cuatro son directamente relevantes para Codex.

**El router de LLM (motor/llm_router.py, 219 líneas).** Un punto único de acceso a modelos donde ningún módulo llama directamente a una API: todo pasa por el Router, y una tabla en SQLite (llm_config) define qué modelo usar para cada función cognitiva, con temperatura y tokens por función, recargable sin tocar código. Esto es el embrión exacto de la estrategia de tiers del ADR-005 y del skill de prompts. La diferencia es de vocabulario: Fray Tomás rutea por función ("reflexion", "operativo"), Codex rutea por tier según peso narrativo. La arquitectura es la misma. El cliente abstraído que el documento técnico de Codex pedía construir ya existe en versión funcional; falta agregarle la interfaz de MockClient para tests y el mapeo a tiers.

**La interferencia productiva (motor/interferencia.py).** Azar controlado en el pensamiento: un meme no convocado puede irrumpir como asociación inesperada, con probabilidad según el nivel de apertura del contexto (crítico 0.1, normal 0.3, exploración 0.7), ponderado por peso del meme y bonus para los olvidados hace mucho. Esto no estaba en ningún documento de Codex y es un regalo para la calidad narrativa: es el mecanismo de la ocurrencia, lo que hace que un personaje tenga asociaciones inesperadas pero coherentes con quién es. Un pescador al que, en medio de una conversación sobre redes, le irrumpe el meme del kraken. Recomendación nueva: incorporar la interferencia al diseño del memetario de Codex como mecanismo de primera clase. Es barata (ya está escrita) y produce exactamente el tipo de vida interior impredecible-pero-fiel que el proyecto busca.

**Los agentes con mini-memetario (motor/agentes.py, 420 líneas).** Fray Tomás crea agentes que trabajan para él: temporales (descartables) o permanentes (frailes), y los permanentes tienen mini-memetario propio y autonomía acotada. Esto significa que la transformación de instancia única a multi-agente, que el mapa describía como el cambio estructural grande entre Fray Tomás y Codex, ya empezó dentro del propio Fray Tomás. Ya hay seres de complejidad menor con memetarios livianos instanciados junto al ser principal. Es el embrión de la estratificación de complejidad del ADR-006, funcionando. La diferencia conceptual persiste (los agentes de Fray Tomás son sus subordinados; los seres de Codex son pares en un mundo), pero el patrón técnico de instanciar memetarios de distinto peso ya existe.

**La percepción semántica (motor/percepcion.py).** Fray Tomás lee feeds RSS del mundo real y filtra por relevancia semántica contra su memetario, con costo cero de tokens para el filtrado. Esto es la piel activa (el memetario que palpa y decide qué mirar) implementada sobre el mundo real. Para Codex, el patrón se traslada: un ser filtra los eventos del mundo ficcional por relevancia semántica con su memetario, y solo lo que su piel detecta entra a su atención. El mecanismo de "a qué es sensible cada ser" ya tiene prototipo.

Además: un sistema formal de migraciones de base de datos (db_migrations.py con versionado de esquema), señal de madurez de ingeniería que facilita heredar la persistencia.

### Lo que fue más deseo que realidad

La lista es corta, que es la mejor noticia del análisis.

**La temperatura emocional (Damasio).** No está en el código. Busqué el campo en los memes y el mecanismo: no existen. Lo único "emocional" es una categoría del clasificador de intención, y "temperatura" solo aparece como parámetro de sampling del LLM. La temperatura emocional como atributo del memetario era diseño documentado, no implementación. Para Codex sigue siendo la recomendación del mapa (agregarla como campo del meme, bajo esfuerzo, alto retorno narrativo, conecta con la postura hacia el corpus), pero ahora sabiendo que se construye desde cero, no se hereda.

**Los clusters emergentes (motor/analisis_clusters.py).** Caso intermedio interesante: el código está implementado (co-activación por sesión, matriz de co-ocurrencias, alimenta al SPECULUM), corrigiendo mi estimación de que era "probablemente diseño no implementado". Pero tiene un umbral mínimo de 100 activaciones para producir algo que no sea ruido, y es plausible que nunca haya corrido con datos suficientes (el estado vivo no está en el repo, así que no puedo confirmarlo; lo sabés vos). Veredicto: código real, validación empírica pendiente. Para Codex se hereda el código sabiendo que la mecánica está por probarse con datos reales.

**El umbral de PF.** Implementado pero rudimentario: una lista de palabras clave de conflicto ético. Funciona para Fray Tomás; para Codex el mapa ya recomendaba repensar su rol, y viendo la implementación lo confirmo: es lo bastante simple como para que reescribirlo no duela.

### Las limitaciones de empaquetado (trabajo de adaptación real)

Esto no es deseo versus realidad sino el costo concreto de trasladar el código, y conviene tenerlo listado porque es el trabajo de la primera fase del MVP.

**Paths atados a la Pi.** Todo el código referencia rutas absolutas de tu Raspberry (/var/lib/picoclaw/...). Para Codex hay que parametrizar las rutas, lo cual encaja naturalmente con el ADR-003 (cada mundo es una carpeta portable): las rutas pasan a derivarse de la carpeta del mundo. Trabajo mecánico, un día.

**La doble persistencia en transición.** Fray Tomás está a mitad de una migración de JSON (memetario.json con NetworkX) a SQLite (biblioteca.db con tablas memes, relaciones_memes, activaciones, diarium, actas). El módulo memetario.py todavía opera sobre JSON; activaciones, speculum, clusters y cambio biográfico ya operan sobre SQLite; existe migrar_memetario.py como puente. Para Codex hay que decidir y unificar. Mi recomendación, alineada con el ADR-003: dentro de la carpeta de cada mundo, SQLite para lo que se consulta intensamente (activaciones, logs, índices) y JSON para lo que conviene leer a mano (definición de memes, entidades), que es de hecho hacia donde tu transición ya iba. Trabajo de unificación: unos días, y conviene hacerlo al principio para no heredar la ambigüedad.

**La hora real versus la hora del mundo.** El bias circadiano y todos los timestamps usan datetime.now(). Codex necesita el reloj del mundo ficcional. Adaptación pequeña pero transversal: conviene introducir desde el día uno un "reloj del mundo" que todos los módulos consulten en lugar del reloj del sistema.

---

## El mapa de reuso, corregido en una tabla

| Componente | Mapa estimaba | Verificado | Veredicto para Codex |
|---|---|---|---|
| Estructura del memetario | Reutilizable directo | Implementado, ya es clase parametrizable | Reuso directo, multi-instancia casi gratis |
| Cálculo de loadout | Reutilizable con salvedad | Implementado exacto (60/40, bias, mana) | Reuso directo + agregar modificadores de lugar |
| Decaimiento | Reutilizable directo | Implementado con fórmula exacta | Reuso directo |
| Embeddings | "Verificar si implementado" | Implementado (fastembed/ONNX) + clasificador + proto-RAG | Reuso directo, mejor de lo esperado |
| Bias circadiano | Reutilizable, cambiar reloj | Implementado con hora real | Reuso + reloj del mundo |
| SPECULUM / autoobservación | Deuda de diseño, diferible | Implementado (427 líneas) | Adaptar, no diseñar desde cero |
| Crisis biográficas / fricción | Adaptable | Implementado completo (degradé, evidencias) | Adaptar reglas de aprobación por nivel de ser |
| Consejo 4 voces | Adaptable a dioses | Implementado | Se sostiene: solo para dioses |
| Memoria episódica | "Verificar", diferible | Implementada | Diferible, pero existe |
| Clusters emergentes | "Probablemente solo diseño" | Implementado, validación empírica pendiente | Heredar código, probar con datos |
| Clasificador de intención | "Si está implementado" | Implementado | Reuso directo |
| Temperatura emocional | Adaptable, alto retorno | NO implementada (era deseo) | Construir nueva (sigue siendo barata) |
| Router LLM / tiers | No estaba en el mapa | Implementado (hallazgo) | Base directa del ADR-005, agregar tiers y mock |
| Interferencia productiva | No estaba en el mapa | Implementada (hallazgo) | Incorporar al diseño de Codex, regalo narrativo |
| Agentes con mini-memetario | No estaba en el mapa | Implementado (hallazgo) | Embrión del ADR-006 ya funcionando |
| Percepción semántica | No estaba en el mapa | Implementada (hallazgo) | Patrón de la piel activa, trasladable |
| Persistencia | Filosofía heredable | En transición JSON→SQLite | Unificar al principio según ADR-003 |

---

## Impacto en la secuencia del MVP

La secuencia recomendada se mantiene pero ahora con nombres de archivos reales y estimaciones más firmes.

**Paso 1 (antes: "traer el motor cognitivo, envolverlo en clase instanciable").** Ahora es más concreto y más corto: tomar memetario.py, embeddings.py, foco.py, activaciones.py e interferencia.py; parametrizar rutas para que deriven de la carpeta del mundo; introducir el reloj del mundo; unificar la persistencia; instanciar dos o tres memetarios simultáneos y verificar loadouts independientes. Como la clase ya es parametrizable y los módulos están desacoplados, esto baja de "semanas" a "días".

**Paso 2 (sin cambios, sigue siendo el corazón del riesgo).** Construir la mutación de un rumor entre dos agentes a través de sus memetarios. Esto sigue siendo lo nuevo, lo no probado, y lo que valida la promesa del proyecto. Con el llm_router como base para las llamadas y el proto-RAG de embeddings para las similitudes, las piezas de apoyo ya existen; lo que se construye es el grafo de hechos y el template de mutación.

**Pasos 3 a 5 (Blades mínimo, corpus liviano, interfaz).** Sin cambios.

Y una incorporación nueva que recomiendo para el diseño, no necesariamente para el MVP: la interferencia productiva como mecanismo del memetario de Codex. Está escrita, es barata, y produce la clase de imprevisibilidad fiel al personaje que distingue a un ser vivo de un autómata coherente.

---

## La frase para llevarte

Tu "lento pero firme" quedó verificado contra evidencia: lo que documentaste, lo construiste, y construiste más de lo que documentaste. El riesgo grande del proyecto (que el corazón cognitivo fuera humo) está descartado con código a la vista. Lo que queda por delante es exactamente lo que el diseño dice que queda: lo nuevo de Codex (el grafo de información mutante, el mundo, las reglas), apoyado sobre un motor que ya late.

---

*Verificado contra el repositorio fray_tomas-master (159 archivos). El estado vivo del memetario (memorias, pesos actuales, activaciones acumuladas) no está en el repo y queda en tu Pi; nada del veredicto depende de él, porque lo que Codex reusa es el código, no la biografía de Fray Tomás.*
