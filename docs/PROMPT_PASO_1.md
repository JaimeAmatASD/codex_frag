# Codex Fragmentum — Prompt de arranque para Claude Code
## Paso 1 del MVP: el motor cognitivo multi-agente

*Pegá este documento al inicio de tu sesión de Claude Code. Está escrito para que Claude Code entienda qué construir, con qué criterio, y qué errores no cometer.*

---

## Contexto del proyecto (leé esto primero)

Codex Fragmentum es un engine para crear ficciones interactivas vivas, donde el motor mantiene el estado del mundo y el LLM solo narra lo que el motor decide. Estás construyendo el paso 1 del MVP: el motor cognitivo que da a cada ser de la ficción una forma propia de percibir el mundo.

Hay dos repositorios en juego. Uno se llama fray_tomas (o la carpeta donde esté el código de Fray Tomás): es REFERENCIA DE SOLO LECTURA. No lo modifiques. Es el prototipo probado del motor cognitivo, del cual aprendés cómo se resuelve cada pieza. El otro es codex (el repo nuevo, vacío o casi): es DONDE SE ESCRIBE. Todo el código nuevo va acá, naciendo limpio.

No copies módulos de fray_tomas a codex. Reimplementá cada pieza en codex mirando cómo la resolvió fray_tomas, pero corrigiendo desde el nacimiento los defectos conocidos (listados abajo en "Las cinco reglas"). Reimplementar con el plano a la vista es más sólido y a menudo más rápido que heredar código atado a otro contexto.

Antes de escribir código, si están disponibles, leé los documentos de diseño del proyecto: los seis ADRs, el documento de corpus, el mapa de reuso, y la verificación del código de Fray Tomás. Si no están en el repo, pedímelos. El skill codex-fragmentum-arquitectura y sus hermanos también tienen el contexto.

---

## Qué construir en el paso 1

El objetivo del paso 1 es tener el motor cognitivo de un ser, instanciable muchas veces, funcionando con dos o tres seres simultáneos que perciben de forma distinta. Concretamente:

La clase que representa el memetario de un ser: el grafo de memes (piedras fundacionales, operativos, experimentales) con sus atributos, persistido de forma unificada. En fray_tomas esto está en motor/memetario.py y ya es parametrizable por path, que es justo lo que necesitás para instanciarlo por ser.

El cálculo de loadout: dado un ser y una situación, seleccionar qué memes se activan. PF siempre gratis, luego score combinando peso histórico (60%) y similitud semántica (40%) multiplicado por bias circadiano, ordenando y llenando hasta el límite de mana. En fray_tomas está dentro de memetario.py. Dejá previsto (pero no implementado aún) que el costo de un meme podrá modificarse según el lugar donde está el ser; en el paso 1 no hay lugares todavía.

Los embeddings para la similitud semántica: en fray_tomas, motor/embeddings.py usa fastembed con ONNX y el modelo all-MiniLM-L6-v2, local en CPU. Heredá ese enfoque (es liviano y gratis). Incluí el caché de vectores.

El decaimiento de los pesos: la fórmula asintótica que nunca llega a cero, refuerzo por activaciones, PF que no decaen. En fray_tomas, motor/decaimiento.py más lógica en memetario.py.

El registro de activaciones: cada vez que un meme se usa, queda registrado. ATENCIÓN a la regla 4 de abajo sobre esto.

El bias circadiano: multiplicadores por tipo de meme según la hora. Pero NO uses la hora del sistema. Introducí un "reloj del mundo" (una abstracción que devuelve la hora del mundo ficcional) que todos los módulos consulten. En el paso 1 puede ser un reloj simple configurable; lo importante es que ningún módulo llame a datetime.now() directamente.

La prueba del paso: instanciar dos o tres seres con memetarios distintos, darles la misma situación, y verificar que cada uno selecciona un loadout distinto coherente con su memetario. Si un pescador supersticioso y un comerciante escéptico, ante la misma noticia de un avistamiento extraño, activan memes distintos y se nota quiénes son, el paso 1 funciona.

---

## Las cinco reglas (no las violes, vienen de bugs reales de Fray Tomás)

Estas reglas salen de auditar el código de Fray Tomás, que sufrió cada uno de estos problemas. Son obligatorias.

Regla 1, persistencia unificada. No tengas dos almacenes de la misma verdad. Fray Tomás quedó a mitad de una migración (memes en JSON, activaciones en SQLite) y eso le aplanó la identidad en silencio: los memes usados a diario figuraban como nunca usados y el decaimiento los castigaba. Decidí UNA estructura de persistencia desde el primer commit. Recomendación alineada con el ADR-003: dentro de la carpeta de cada mundo, SQLite para lo que se consulta intensamente (activaciones, logs, índices) y JSON para lo que conviene leer a mano (definición de memes, entidades), con un único punto que los mantenga coherentes.

Regla 2, una sola puerta de escritura del estado. Ningún módulo escribe memes, pesos o activaciones por su cuenta. Todas las escrituras pasan por una capa única que mantiene la coherencia. Esto previene exactamente el desfase de la regla 1.

Regla 3, logging en lugar de except-pass silencioso. Fray Tomás traga excepciones por todos lados: si fastembed falta, el loadout pierde la similitud semántica y nadie se entera. Acá, toda degradación se registra con logging, aunque no rompa la ejecución. Si algo falla y se sigue con un fallback, que quede en el log.

Regla 4, distinguir "estuvo en el loadout" de "fue efectivamente usado". Fray Tomás registra todo el loadout como activado en cada pensamiento, lo que infla los datos de co-activación y contamina el decaimiento y los futuros clusters. Separá dos conceptos: que un meme haya sido seleccionado en el loadout, y que haya sido efectivamente movilizado en la respuesta. Registralos distinto. Esto importa para que el refuerzo y los clusters midan algo real.

Regla 5, MockClient y tests desde el primer módulo. Fray Tomás tiene cero tests. Acá, creá un MockClient para el LLM (que devuelva respuestas predecibles sin llamar a ninguna API) desde el principio, y escribí tests para cada pieza del motor cognitivo a medida que la construís. El loadout, el decaimiento y la persistencia son deterministas y se testean sin LLM.

---

## Criterio de calidad del código

Python 3.11 o superior. networkx para el grafo, fastembed con ONNX para embeddings, pydantic para validar cualquier estructura, sqlite3 para persistencia. Mantené el código legible y documentado, porque uno de los futuros posibles del proyecto es abrir el código. No sobreingenierices: construí solo lo que el paso 1 necesita, dejando previstos (con comentarios o interfaces mínimas) los puntos de extensión que los pasos siguientes van a usar (lugares que modifican costos, niveles de complejidad de seres, el grafo de información), pero sin implementarlos todavía.

Recordá la filosofía de capas de costo: lo determinista (loadout, decaimiento, similitud) es código puro y local, sin LLM. El LLM recién entra en pasos posteriores para narrar. El paso 1 casi no necesita LLM, salvo el MockClient para dejar el enchufe listo.

---

## Lo que NO es del paso 1 (no lo construyas todavía)

No construyas: el grafo de información con mutación de rumores (eso es el paso 2, el corazón del riesgo), el motor de Blades, los lugares y su geografía, el corpus, la interfaz de usuario, el SPECULUM (autoobservación), las crisis biográficas, los clusters, la inyección divina. Todo eso viene después. Si te encontrás construyendo algo de esta lista, parate: te saliste del paso 1.

---

## Cómo proceder

Empezá proponiendo la estructura de carpetas del repo codex y el esquema de persistencia unificada (regla 1), y esperá mi visto bueno antes de escribir el motor. Esa es la decisión de la que cuelga todo lo demás, así que conviene acordarla primero. Después construí pieza por pieza, con tests, en este orden sugerido: persistencia y modelos, embeddings, memetario y carga de memes, loadout, decaimiento, reloj del mundo y bias, y por último la prueba con dos o tres seres. Mostrame cada pieza antes de seguir con la próxima.
