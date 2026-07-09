# Codex Fragmentum — Análisis de arquitecto: qué tenemos y hacia dónde vamos
## Auditoría del repositorio codex_frag y roadmap
*Julio 2026 — basado en clonado, lectura completa del código, y ejecución de la suite*

---

## Veredicto ejecutivo

El paso 1 del MVP está construido, y está construido bien. El repositorio contiene el motor cognitivo multi-ser completo (1.386 líneas incluyendo tests), con las cinco reglas derivadas de los bugs de Fray Tomás cumplidas por construcción y documentadas en el propio código, los seis ADRs respetados, las fórmulas correctas, 31 tests que pasan todos, y la prueba conceptual del paso funcionando: dos seres con memetarios distintos, ante la misma noticia, arman loadouts distintos y coherentes con quiénes son.

La conclusión operativa: el proyecto está listo para el paso 2, que es el corazón del riesgo y de la promesa (la mutación de un rumor entre dos seres). Es trabajo de VS Code con Claude Code. Los detalles y el plan, abajo.

---

## Lo que tenemos, verificado pieza por pieza

### La arquitectura cumple las cinco reglas por construcción, no por disciplina

Esta es la diferencia de calidad más importante respecto de Fray Tomás, y vale la pena explicarla. Fray Tomás violaba las reglas porque nada se lo impedía: cualquier módulo podía escribir estado, la misma verdad vivía en dos lugares. El código nuevo hace las violaciones estructuralmente difíciles.

La regla 1 (persistencia unificada) está resuelta con una separación conceptual limpia: la DEFINICIÓN de un meme (estática, legible, curada a mano) vive en el JSON del ser; el ESTADO VIVO (peso actual, activaciones) vive solo en SQLite. El peso nunca se duplica en el JSON. La clase MemeVivo une ambas caras en una vista coherente, que es exactamente lo que a Fray Tomás le faltaba. Verificado además en el gitignore: el estado.db se excluye del versionado porque es runtime, la semilla JSON se versiona porque es autoral. Esa distinción semilla/estado es pensamiento arquitectónico correcto.

La regla 2 (puerta única de escritura) está resuelta con la clase Persistencia como único módulo que toca disco. Lo verifiqué con grep: no hay ninguna llamada a sqlite o escritura de archivos fuera de persistencia.py. Imposible por construcción el desfase que aplanó a Fray Tomás.

La regla 3 (logging en lugar de silencio) está en todos los casos degradados: meme sin estado, conexión a meme inexistente, movilización fuera del loadout, embeddings caídos. Y tuve la suerte de validarla empíricamente: en mi entorno el modelo de fastembed no pudo descargarse, y el sistema logueó el error, degradó el loadout a peso histórico con warning visible, y completó la corrida igual. La degradación elegante del ADR-005 funcionando en vivo ante una falla real de red, en su primera corrida. Exactamente el escenario que Fray Tomás escondía.

La regla 4 (loadout versus movilizado) está en el esquema mismo: columnas separadas veces_en_loadout y veces_movilizado, la ultima_activacion y el refuerzo de peso cuentan solo movilizados. El test test_registrar_distingue_loadout_de_movilizado lo cubre.

La regla 5 (MockClient y tests desde el día uno) está cumplida con 31 tests que cubren cada módulo, incluidos los caminos de degradación, y un MockClient determinista con guion que además define la interfaz ClienteLLM (Protocol) dejando el enchufe del LLM listo para el paso 2. Los tests no dependen de red: el codificador de embeddings es inyectable y los tests usan vectores 2D diseñados a mano (un eje para presagio/agua, otro para comercio/razón), que es una técnica de testing elegante.

### Las decisiones de diseño respetan los ADRs y agregan mejoras propias

El reloj del mundo existe como Protocol más implementación simple, y el grep confirma que ningún módulo llama a datetime.now(). El bias circadiano lee la hora del mundo y es un invocable que se pasa directo al loadout. La fórmula del loadout es la heredada (60 por ciento peso, 40 por ciento similitud, por bias, PF gratis, llenado por mana) con una mejora sobre Fray Tomás que está bien razonada: el peso se normaliza a 0..1 sobre los candidatos para que sea conmensurable con la similitud, y la decisión está comentada. El decaimiento es asintótico con piso mayor que cero y techo de refuerzo, con funciones puras separadas de la aplicación con persistencia (testeables sin disco). El punto de extensión para los modificadores de lugar está previsto donde corresponde (costo_efectivo en el loadout) sin implementarse, tal como pedía el prompt de arranque. Los números de calibración están nombrados como constantes y documentados como provisionales.

### El elenco de prueba ya tiene voz

Los dos seres de prueba (pescador supersticioso, comerciante escéptico) están bien construidos: PF que definen postura ("El mar guarda señales que hay que saber leer" contra "Todo tiene una explicación natural y un precio"), operativos que compiten, un experimental cada uno, conexiones declaradas (cargadas al grafo, listas para los clusters futuros). Ante la noticia del avistamiento, el pescador activa el presagio y el comerciante activa el rumor de mercado. La refracción diferencial, que es el alma del proyecto, ya se ve en miniatura.

---

## Hallazgos: lo que falta o conviene ajustar (nada grave)

Primero, el README está vacío. Para un proyecto cuyo futuro posible es abrirse, y cuya documentación de diseño es su mayor activo, el README es la puerta de entrada. Debería contar qué es Codex en tres párrafos, cómo correr el demo y los tests, y apuntar a la documentación.

Segundo, y es el hallazgo más importante: la documentación de diseño no está en el repositorio. Los seis ADRs, el corpus, la verificación de Fray Tomás, el prompt de arranque, la revisión integral: nada de eso está versionado en codex_frag. Hoy viven dispersos en descargas de nuestras conversaciones. El repo debería tener una carpeta docs/ con todo, y una carpeta skills/ con las fuentes de los seis skills, para que el git sea la memoria única del proyecto (esto además resuelve tu pedido de "sumar sin perder": cada versión queda en la historia).

Tercero, un detalle técnico menor para anotar, no para corregir ya: el registro de activaciones guarda como co_activados a los compañeros de loadout. Para los clusters futuros (memes que trabajan juntos) lo que importa son los co-MOVILIZADOS, que hoy no se guardan directo pero se pueden derivar por consulta (filas con mismo ser y momento, filtradas por movilizado). Cuando llegue el análisis de clusters, decidir si derivar por query o agregar la columna. Lo dejo anotado para que no se olvide; no bloquea nada.

Cuarto, falta LICENSE. Sin licencia, el código es propietario por defecto, lo cual está bien hoy, pero conviene decidirlo conscientemente cuando se acerque cualquier apertura.

Quinto, quedaron abiertos los pendientes de la revisión integral previa al repo: el skill maestro sigue diciendo "novela interactiva" (yo estaba a mitad de la corrección definitiva cuando llegó el repo; la retomo), el skill de Blades sigue contradiciendo al ADR-002, y la Fase 0 sigue sin consolidar. Con la carpeta docs/ en el repo, la Fase 0 consolidada tiene ahora un lugar natural donde vivir.

---

## Hacia dónde vamos: el roadmap

### El paso 2 es el corazón de todo: la mutación del rumor

Todo lo construido hasta acá es la base probada. Lo que no existe en ningún lado, y es la apuesta conceptual del proyecto entero, es esto: que cuando un ser le cuenta algo a otro, la versión que el receptor guarda esté deformada por su cristal, y que esa deformación se sienta reveladora y no aleatoria. Si eso funciona, Codex cumple su promesa ("la verdad muere con el testigo"). Si no funciona ni con buenos prompts, hay que repensar antes de construir nada más. Por eso va segundo y no quinto.

El esbozo arquitectónico del paso 2, para discutir en VS Code antes de programar. Tres módulos nuevos sobre lo existente. Un módulo de hechos: el modelo Pydantic de Hecho del mundo (la verdad raíz) y de Version (cada forma en que circula), con su linaje (de qué versión deriva, quién la emitió, quién la recibió) y su distancia semántica a la raíz (embeddings ya existentes). Un módulo de grafo del mundo: el MultiDiGraph de NetworkX que sostiene hechos, versiones y quién conoce qué, persistido a través de la puerta única (la Persistencia crece para serializar el grafo, en formato no-pickle). Y un módulo de transmisión: la operación central, donde A le cuenta una versión a B, el sistema calcula el loadout de B ante ese contenido (ya existe), arma el prompt de mutación con el cristal activo de B, llama al LLM, valida la respuesta con Pydantic, y si pasa, registra la versión nueva como nodo hijo en el grafo. El LLM propone, el motor dispone (ADR-001): ninguna versión entra al grafo sin validar.

La estrategia de prueba en dos niveles, gracias al MockClient: primero el flujo completo con mock (barato, determinista, valida toda la maquinaria sin gastar un token), después la calidad de la mutación con LLM real barato (la línea de base del ADR-005), jugando el rumor del kraken entre el pescador y el comerciante y leyendo si las dos versiones divergen de forma reveladora. El criterio de éxito es cualitativo y tuyo: leés las dos versiones y sentís que cada una delata a su portador. El criterio de fracaso también: si tras iterar los prompts las mutaciones son genéricas o arbitrarias, paramos y repensamos antes del paso 3.

### Después del paso 2, en orden

Paso 3, el mínimo de Blades para un Score jugable, construido contra la interfaz enchufable del ADR-002, del lado del enchufe y no del núcleo. Paso 4, el corpus liviano (textos destilados por ser, las tres dimensiones como contexto del prompt) para que los seres tengan fondo además de cristal. Paso 5, la interfaz mínima de juego en terminal, y acá entra la decisión que tomamos sobre el futuro cuerpo: el motor se estructura desde ya para poder exponerse como servidor (websocket) además de correr en terminal, de modo que el día que quieras enchufarle Godot u otra cara, sea agregar un cliente y no reestructurar. Con el paso 5 completo, tenés "Una noche en la taberna" jugable, que era la definición del MVP.

En paralelo y barato: el saneamiento documental (README, docs/ y skills/ en el repo, skill maestro corregido, Fase 0 consolidada), que es una sesión corta y deja el proyecto coherente para cualquier colaborador futuro, humano o IA.

---

## La lectura honesta del momento

Hace unas semanas este proyecto era cincuenta mil palabras de diseño y cero código, y el riesgo dominante era diseñar para siempre. Hoy es un motor que corre, con tests, que cumple sus propias reglas, y cuya primera prueba conceptual (dos cristales, una noticia, dos percepciones) funciona. El diseño demostró valer: las reglas nacidas de los bugs de Fray Tomás están impresas en la estructura del código nuevo, y la degradación elegante ya sobrevivió a su primera falla real.

Lo que viene es la apuesta grande. El paso 2 no es un paso más: es el experimento que valida o refuta la idea central. Conviene entrar a él con esa conciencia, sin ansiedad pero sin dispersión: nada de lugares, dioses, clusters ni interfaces hasta que la mutación del rumor demuestre ser mágica. Una cosa increíble por vez, y esta es la que toca.
