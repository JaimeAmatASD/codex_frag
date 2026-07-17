# Codex Fragmentum — Prompt de mejora: tensión interna entre memes
## Aristas con signo, detector de tensión, y clasificación funcional de memes

*Pegá este documento (o pedile a Claude Code que lo lea de docs/) al inicio de la sesión, con el repo codex_frag como directorio de trabajo. Es una mejora acotada sobre lo construido, primera adopción del plan de docs/ANALISIS_BRAINSTORMING_JUL2026.md (parte 2, mejoras 1 y 4). Leé ese análisis y el código de codex/modelos.py, codex/loadout.py y codex/transmision.py antes de empezar.*

---

## La idea en tres líneas

Hoy las conexiones entre memes no tienen signo: no distinguen refuerzo de contradicción. Esta mejora agrega tensiones (memes incompatibles), un detector que avisa cuando dos memes en tensión de peso similar entran juntos al cristal, y esa tensión entra a los prompts como material dramático. El drama no se escribe: emerge de la grieta. "Nunca abandones a tu familia" contra "el deber está por encima de todo", pesando parecido, activados juntos: eso es un personaje partido al medio, y el sistema ahora lo ve y lo narra.

## Decisiones ya tomadas (no re-debatir)

**Retrocompatibilidad total, sin migración.** El campo conexiones existente queda como está y significa refuerzo. Se agrega un campo nuevo tensiones (lista de ids de memes, default lista vacía) en la definición del meme. Los ser.json existentes cargan sin tocar. La tensión es simétrica: si A declara tensión con B, vale en ambos sentidos aunque B no la declare; el detector normaliza.

**Clasificación funcional de paso, como campo opcional.** La definición del meme gana funcion, opcional, con valores perceptivo, estrategico, moral, identitario o emocional (Literal de Pydantic, default None). NO reemplaza al tipo (fundacional/operativo/experimental), que mide estabilidad; la función mide qué clase de lente es. Su único uso en esta mejora: anotar cada meme activo en los prompts para afinar la refracción.

**El detector vive en el loadout y es código puro.** Tras seleccionar el loadout, detectar los pares del loadout que están en tensión y cuyos pesos normalizados son similares (umbral inicial 0.25 de diferencia, constante nombrada y calibrable). Cada par detectado produce una TensionInterna (modelo Pydantic: los dos ids, sus textos, una intensidad simple, por ejemplo el menor de los dos pesos normalizados). El resultado del loadout gana el campo tensiones (lista, puede ser vacía). Las PF participan del detector igual que los operativos: una PF en tensión con un operativo fuerte es de las grietas más dramáticas que existen.

**La tensión entra a los prompts, con plantilla condicional.** templates/mutacion.txt y templates/narracion_score.txt ganan una sección que solo aparece si hay tensiones: algo como "Ahora mismo hay una grieta en él: cree a la vez que $texto_a y que $texto_b, y las dos cosas tiran para lados distintos. Esa tensión debe notarse en cómo entiende/actúa, sin resolverse mágicamente." El armado del prompt (en transmision.py y en el camino del Score) inyecta la sección si corresponde, string vacío si no. La función de cada meme, si la tiene, se anota junto al meme en la lista de memes activos ("(lente moral)", "(lente perceptiva)").

**El grafo y la bitácora se enteran.** La carga del memetario al grafo (persistencia) suma las aristas de tensión con atributo de tipo, igual que hoy carga las conexiones. Las tensiones detectadas en cada transmisión o Score quedan en la bitácora del Taller (que ya registra entrada y salida), para que el autor VEA la grieta. Toda escritura, por la puerta única, como siempre.

**El Taller muestra y edita.** En la zona Probar, la respuesta muestra las tensiones activas junto a los memes resonantes (texto simple, sin rediseño). En el editor de personajes, el formulario de meme gana los campos tensiones (ids separados por coma, como las conexiones) y funcion (selector con las cinco opciones más vacío). Mínimo cambio en taller/app.py e index.html; nada de rediseñar la página.

## El material de prueba

Agregarle una tensión real a un ser existente para poder probar. Propuesta (James la cura o la cambia desde el Taller): al pescador supersticioso, un meme nuevo "el mar da de comer a mi familia" (funcion estrategico) en tensión con su meme del presagio o con "el mar se cobra lo que se le debe" si existe algo así; ajustar pesos para que queden parejos. Alternativa igual de buena: la tensión natural de el_que_no_muere entre "el olvido" y "conozco esta tierra, es mi cuerpo" (recordar es su tierra, olvidar es su condición). Elegir UNA, no poblar todo de tensiones: la grieta vale porque es rara.

## Tests (deterministas, sin red, sin tokens)

Del detector: par en tensión con pesos similares se detecta; con pesos muy dispares no; la simetría funciona aunque solo un lado la declare; loadout sin tensiones devuelve lista vacía. De los modelos: un ser.json viejo sin los campos nuevos carga igual (retrocompatibilidad); funcion inválida es rechazada por Pydantic. Del prompt: con tensiones, la sección aparece en el texto armado; sin tensiones, no aparece ni deja residuo. Seguir el patrón existente de encoder inyectable y MockClient.

## Criterio de éxito (lo juzga James en el Taller)

Contarle el mismo hecho al mismo ser dos veces: una con la tensión activa (pesos parejos) y otra con la tensión desactivada (bajarle el peso a uno de los dos memes desde el editor). Leer las dos versiones lado a lado. Éxito si la versión con tensión delata la grieta: se nota que el ser está tironeado, sin que el texto lo resuelva ni lo explique didácticamente. Si la diferencia no se siente tras iterar la plantilla un par de veces, se reporta honesto y se recalibra el umbral o la redacción de la sección antes de dar la mejora por buena.

## Lo que NO es de esta mejora

No construir: mecanismos de aprendizaje por meme (es el experimento futuro del análisis, parte 3), resolución automática de la tensión (la grieta no se resuelve: se narra), decisiones autónomas de NPCs, fusión o mutación de memes, el constructor de seres por descripción (es la mejora siguiente), singularidades narrativas, ni migración del formato de conexiones existente. Si aparece la tentación de que el motor decida cuál meme "gana" la tensión, parate: en esta mejora nadie gana, y ahí está la gracia.

## Cómo proceder

Primero los modelos (TensionInterna, campos nuevos en la definición del meme) y la sección de plantilla en texto plano, mostralos y esperá el visto bueno de James. Después el detector con sus tests, la integración a los dos caminos de prompt, el grafo y la bitácora, y al final los retoques del Taller y el material de prueba. Commits chicos con mensajes en castellano como los que ya tiene el repo.
