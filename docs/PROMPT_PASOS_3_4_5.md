# Codex Fragmentum — Prompts de arranque: pasos 3, 4 y 5 del MVP

*Estos tres prompts son deliberadamente más compactos que los de los pasos 1 y 2: se detallan al llegar a cada uno, con lo aprendido en los anteriores. Diseñarlos en detalle ahora sería especulación (el paso 2 puede cambiar cosas). Cada uno se pega a Claude Code al arrancar su fase, junto con una relectura de lo construido hasta ese momento. Presuponen: paso 1 completo, paso 2 validado (la mutación del rumor se siente reveladora; si no se validó, no seguir: repensar).*

---

## Paso 3: el mínimo de Blades para un Score jugable

**Objetivo.** Que exista la primera resolución dramática formal: el jugador (como Marcos u otro ser) declara una acción con riesgo, el sistema calcula posición y efecto cruzando su memetario con la situación, tira los dados, y el resultado (limpio, con costo, o mala consecuencia) queda narrado y con efectos reales en el estado.

**La decisión arquitectónica que manda (ADR-002).** Blades vive del lado del enchufe, nunca en el núcleo. Antes de programar, definir la interfaz mínima SistemaDeReglas que el núcleo ofrece y Blades consume: qué le pasa el núcleo (loadout del ser ante la situación, afinidad semántica, estado relevante) y qué devuelve el sistema de reglas (resultado tipado de la resolución más efectos a aplicar, que el motor aplica por la puerta única). La interfaz es la mínima que Blades necesita: nada de abstracción universal de sistemas de juego.

**Alcance.** Tiradas con tres resultados; posición y efecto calculados desde el memetario (los memes activos afines a la acción mejoran, las PF en conflicto empeoran); stress como recurso simple (empujar la tirada pagando stress); UN clock de amenaza que avanza con las malas consecuencias. Consultar el skill codex-fragmentum-blades (referencias de tiradas y clocks) para el detalle mecánico, recordando que su sección de estatus fue corregida: enchufable, no columna.

**Restricción del ADR-007.** La hoja mecánica del ser (stress, stats, lo que el sistema de reglas necesite persistir) se guarda en archivo separado del cuerpo cognitivo, dentro de la carpeta del ser: pertenece a la capa de reglas y no viajará con el alma cuando exista el enchufe de seres.

**No es del paso 3.** Trauma inyectado al memetario (fase posterior: requiere hitos), vicios, downtime completo, múltiples clocks, free play estructurado. Tests con dados sembrados (random con seed) y MockClient para la narración.

---

## Paso 4: el corpus liviano

**Objetivo.** Que los seres tengan fondo además de cristal: cada ser puede referenciar un corpus (texto destilado curado por James) con sus tres dimensiones (profundidad, fidelidad ya materializada en el contenido, postura), y ese fondo entra al prompt cuando el ser habla o recuenta, cambiando su voz.

**El documento que manda.** docs/CORPUS_DISENO.md tiene el diseño completo y las decisiones cerradas: entidad de primera clase referenciada (no poseída), acceso por interpretación del LLM (las dimensiones como contexto, no dosificación mecánica), el LLM no inventa contenido del corpus que no está escrito, implementación liviana (campos de texto), RAG explícitamente diferido, evolución explícitamente diferida.

**Restricción del ADR-007 (si no se hizo antes).** Migrar cada ser a su propia carpeta autocontenida dentro del mundo (seres/marcos/ser.json), con su corpus al lado (seres/marcos/corpus.md). El estado vivo sigue únicamente en el SQLite del mundo (regla 1): la carpeta del ser es semilla, no runtime.

**Alcance.** Modelo Pydantic de Corpus y de la referencia ser→corpus con dimensiones; carga desde JSON en la carpeta del mundo (mismo patrón semilla que los seres); integración al armado de prompts de transmisión y narración (el fondo del ser entra como contexto junto al cristal). La prueba: el mismo rumor recontado por el mismo cristal CON y SIN corpus debería sonar distinto; y dos seres con el mismo corpus pero distinta postura (venera / desconfía) deberían citarlo distinto.

**No es del paso 4.** RAG, embeddings sobre el corpus, evolución del corpus, derivación automática de PF desde corpus, corpus del mundo (empezar por corpus de seres; el del mundo se agrega si el MVP lo pide).

---

## Paso 5: la interfaz mínima y el cierre del MVP

**Objetivo.** Que "Una noche en la taberna" sea JUGABLE de punta a punta: James se sienta, juega treinta a sesenta minutos en la terminal, y sale con la sensación de haber estado en algún lado.

**Alcance.** El loop de juego en terminal: el jugador habita a Marcos, ve lo que su cristal le muestra, conversa con los NPCs (transmisiones con mutación), declara acciones (free play o Score según el peso), el mundo registra todo. El elenco completo del MVP: cinco NPCs con memetario y corpus liviano, el hecho semilla del kraken, tres clocks. Armar el mundo de la taberna es trabajo AUTORAL de James (escribir seres y corpus) tanto como trabajo de código; el código provee el loop.

**La decisión estructural del paso (registrada en la Fase 0).** El motor se expone también como servidor websocket, además del modo terminal: un módulo servidor.py fino que envuelve el mismo loop y lo sirve por mensajes JSON. No construir ningún cliente visual: solo dejar el enchufe probado (un test que conecta, juega un turno por websocket, y desconecta). El día que se quiera un cuerpo (Godot u otro), será un cliente más.

**Criterios de cierre del MVP (de la Fase 0 y la evaluación crítica).** Éxito: James juega y siente que estuvo en algún lado; una persona externa entiende sin explicación; la mutación del rumor del kraken entre dos NPCs es visible y satisface. Muerte o repensado profundo: narraciones genéricas, mutaciones sin diferencia significativa, jugable pero aburrido, o costo por sesión desproporcionado. Ser honesto con estos criterios: para eso se escribieron antes de empezar.

---

## Mejoras transversales pendientes (hacer en el paso donde toquen, no antes)

Anotadas en el análisis de arquitecto para no perderlas. Al llegar a los clusters (post-MVP): decidir si los co-movilizados se derivan por consulta sobre la tabla de activaciones o se agregan como columna. Al acercarse cualquier apertura del código: elegir LICENSE conscientemente. Al usar por primera vez cada skill especializado restante (memetario, grafo-mundo, cartografia, llm-prompts): parchearlo con los hallazgos de la verificación (interferencia productiva, llm_router real, temperatura emocional como construcción nueva) — regla just-in-time, no antes. La interferencia productiva (el meme no convocado que irrumpe) se incorpora al motor cuando haya juego real donde apreciarla, probablemente entre los pasos 4 y 5.
