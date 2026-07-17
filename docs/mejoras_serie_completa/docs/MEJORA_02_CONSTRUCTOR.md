# Codex Fragmentum — Prompt de mejora: el constructor de seres por descripción
## Relatás un personaje en lenguaje natural, el sistema deriva el ser completo, vos curás

*Segunda mejora del plan de docs/ANALISIS_BRAINSTORMING_JUL2026.md (parte 2, mejoras 2 y 3). Presupone hecha la mejora de tensión (tensiones y funcion ya existen en el modelo). Leé el análisis, el código del Taller (taller/app.py, taller/index.html) y codex/transmision.py (el patrón de validar-reintentar-degradar que acá se reusa).*

---

## La idea en tres líneas

Hoy crear un ser es llenar formularios. Con esta mejora, el autor RELATA al personaje ("es un veterinario de 62 años, ayuda a cualquiera, nunca perdonó a su hijo, tiene miedo a quedarse solo"), tipeado o dictado (el dictado ya existe en el Taller), y el sistema deriva la propuesta completa del ser: piedras, memes con función y tensiones, pesos, hoja mecánica. La propuesta cae en el formulario de edición existente, NUNCA se guarda sola: el autor la revisa, la retoca y la guarda con el flujo normal. Es el flujo del jardinero de la Fase 0 aplicado a seres: plantás una descripción, crece una estructura, podás.

## Decisiones ya tomadas (no re-debatir)

**El LLM propone, el motor valida, el autor cura.** La respuesta del modelo se valida con Pydantic contra los modelos existentes del ser (con los campos de la mejora anterior incluidos). Si no valida, UN reintento con feedback del error (mismo patrón e INTENTOS que transmision.py); si vuelve a fallar, se degrada con mensaje claro al autor ("no pude derivar un ser válido, probá reformular la descripción") y se loguea. Jamás se guarda nada sin pasar por el formulario y el botón de guardar del autor.

**El template de derivación usa la esencia operativa como esqueleto.** Archivo nuevo templates/derivar_ser.txt, editable desde la zona Templates del Taller como los otros. El prompt instruye que el ser derivado tenga: dos o tres piedras fundacionales (las leyes de conservación del personaje, lo que casi nunca cambia), y entre los memes operativos al menos un deseo, un miedo o tabú, un sesgo perceptivo (qué interpreta siempre mal), y una forma característica de mentir o callar. Cada meme con su funcion (perceptivo, estrategico, moral, identitario, emocional). Si la descripción sugiere una contradicción (el veterinario que ayuda a cualquiera pero nunca perdonó a su hijo), el template pide declararla como par en tensiones con pesos parejos: la grieta detectada por la mejora anterior nace acá. Los ids de memes: cortos, en minúsculas, con guiones bajos, sin espacios. Escalas de pesos, costos y mana: instruir al modelo con los rangos reales tomando los seres existentes del mundo como referencia (leerlos antes de escribir el template). La hoja mecánica: acciones con rangos 0 a 4, coherentes con la descripción.

**Dónde vive en el Taller.** En la zona Personajes, arriba del formulario: un campo de texto libre grande ("Relatá al personaje") con el dictado ya disponible, y un botón "Derivar ser". Al responder, la propuesta PUEBLA el formulario de crear/editar existente (no una vista nueva): el autor ve el ser como si lo hubiera tipeado, lo ajusta, y guarda con el botón de siempre. Mínimo cambio de interfaz; nada de rediseñar la página. La llamada al LLM usa el cliente real ya configurado, por la vía única existente.

**La bitácora registra la derivación** (descripción de entrada, propuesta de salida, si hubo reintento), para poder comparar cómo distintas redacciones producen distintos seres: es material de calibración del template.

## Tests (deterministas, sin red, sin tokens)

Con MockClient guionado: respuesta válida puebla la estructura esperada (piedras presentes, memes con funcion, ids sin espacios); respuesta inválida más reintento inválido termina en degradación limpia con mensaje, sin guardar nada; una respuesta con id de meme con espacios o funcion desconocida es rechazada por la validación. Del endpoint del Taller: la ruta responde la propuesta sin tocar disco. Seguir los patrones de tests existentes.

## Criterio de éxito (lo juzga James en el Taller)

Relatar al veterinario del ejemplo, tal cual, y mirar la propuesta: éxito si al primer vistazo el ser SE SIENTE él (las piedras suenan a leyes suyas, el miedo a quedarse solo está, la tensión entre ayudar a cualquiera y no perdonar al hijo quedó declarada con pesos parejos) y lo único que dan ganas de hacer es retocar palabras, no rearmar la estructura. Después, la prueba completa del ciclo: guardarlo, contarle un hecho, y leer si su versión lo delata. Si las propuestas salen genéricas tras iterar el template un par de veces, reportar honesto antes de dar la mejora por buena.

## Lo que NO es de esta mejora

No construir: derivación de corpus (es el paso 4), derivación de lugares o mundos, refinamiento conversacional iterativo ("hacelo más oscuro" — la versión uno es una pasada más edición manual), derivación en lote de varios seres, ni guardado automático de nada. Si aparece la tentación de que la propuesta se guarde sola "para agilizar", parate: la curaduría del autor es el punto, no la fricción.

## Cómo proceder

Primero el template derivar_ser.txt en texto plano y el esquema Pydantic de la respuesta esperada, mostralos y esperá el visto bueno de James. Después el endpoint con validar-reintentar-degradar y sus tests con mock, luego el retoque de la zona Personajes, y al final la bitácora. Commits chicos en castellano.
