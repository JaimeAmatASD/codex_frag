# Lecciones

Una línea por error: fecha, categoría, y qué hacer distinto. Se agrega cuando algo
sale mal, no cuando sale bien — para eso está `docs/adr/`.

Esto es lo que escribís vos (o Claude con tu acuerdo). Distinto de la auto memory
de Claude, que él mantiene solo con hallazgos operativos. Acá van los errores que
no querés recometer.

Si un bug volvió a pasar, es porque su lección no estaba acá, o estaba escrita
como consejo en vez de como prohibición.

---

## Transversales

- **verificación** — Un test que nunca se vio fallar no prueba nada. Rojo antes que verde.
- **verificación** — Un agente que ablanda un test para que pase destruye el harness entero, y James no puede detectarlo leyendo el diff. Si falla: se arregla el código, o se pregunta.
- **verificación** — Gate verde no significa bueno en un sistema generativo. Protege la estructura, no el texto.
- **verificación** — Nunca declarar terminada una salida generada que nadie leyó. Si no se leyó, se dice "sin revisar".
- **agentes** — Código enredado frena a los propios agentes: se traban desenredando lo suyo y queman tokens. Los límites de complejidad son plata, no estética.
- **agentes** — Lo que tiene que cumplirse sí o sí va en config o en un hook. Una instrucción en prosa se cumple casi siempre, que no es lo mismo.
- **proceso** — Un boceto que nunca se declaró boceto termina en producción sin que nadie lo haya decidido. Declarar el nivel al empezar.
- **proceso** — Dos intentos y se frena. Un agente dando vueltas en un fix quema tokens y no se puede destrabar desde afuera.
- **contexto** — Lo que debe valer siempre va en CLAUDE.md; lo condicional en un rule o un skill. Si la voz vive en un skill, se prende y apaga sola.
- **contexto** — Un skill vive en un solo lugar. Duplicado en personal y en el repo, uno pisa al otro y editás el que no se carga.
- **contexto** — Los skills del proyecto van en `.claude/skills/`. Una carpeta `skills/` en la raíz no la escanea nadie.
- **estructura** — Sin espacios en nombres de carpeta: rompen cualquier script que los toque.

## De este proyecto

- **2026-07 · datos** — Los contadores medían la atención de James, no la vida del ser: `registrar_activaciones` tenía UN solo llamador (la transmisión); Score y Diálogo no dejaban huella. Antes de leer una métrica, verificar quién la alimenta.
- **2026-07 · verificación** — `aplicar_decaimiento` y `reforzar_movilizados` existían, testeados y en verde, pero nadie los llamaba en producción. Construido no es integrado: buscar los llamadores reales antes de dar algo por vivo.
- **2026-07-30 · datos** — Un umbral de similitud absoluto no se muda entre textos de largos distintos: 0.75 servía en Blades (meme contra escena corta) y en el diálogo era inalcanzable (meme contra charla de 8.000 caracteres, máximo real 0.606), así que quince charlas no dejaron huella. Cuando el criterio es "lo más relevante", usar orden relativo (top-N), no piso absoluto.
- **2026-07-30 · verificación** — El test del diálogo usaba un encoder donde todo era afín a todo (similitud 1.0), así que pasaba en verde sobre un umbral que en producción nunca se cruzaba. Un test con datos degenerados no prueba la calibración: si el número importa, el test tiene que variar afinidades de verdad.
- **2026-07-30 · agentes** — Si al LLM se le pide un identificador, el prompt tiene que mostrárselo: el SPECULUM listaba los memes solo por su texto y pedía el `meme_id`, así que devolvía el texto (una vez con las comillas angulares incluidas) y la mirada entera se descartaba. No pedir lo que no se muestra; y aceptar el texto como alias, porque el modelo responde con lo que ve.
- **2026-07-30 · verificación** — La corrida real del SPECULUM con Gemini pasó por la rama `proponer_experimental` (id nuevo, valida que NO exista) y nunca por `ajustar_peso` (id existente), que estaba roto. Una verificación con LLM real cubre el camino que el LLM eligió, no todos: enumerar las ramas y forzar la que no salió.
- **2026-07-30 · datos** — Un id que contiene el separador de su propio campo se parte solo: `'conosco esta tierra, es mi cuerpo'` en el campo "tensiones (ids, coma)" quedó como dos referencias inexistentes, y `el_que_no_muere` corrió sin ninguna tensión. Los ids no llevan el separador, y una referencia que no resuelve es error visible, nunca warning.
- **2026-07-31 · verificación** — Un test que lee el mundo vivo de James (`mundos/prueba/seres/*.json`) se rompe cuando él juega: aprobar dos experimentales del SPECULUM en el comerciante tiró `test_dos_seres` con un `KeyError` del encoder de prueba. Si un test carga contenido que el autor edita en su mesa de trabajo, el codificador tolera lo desconocido (vector neutro) y solo asegura lo que el test nombra.
- **2026-08-04 · datos** — El criterio manda sobre el número, y el test tiene que escribir el criterio: el diseño decía "un mes tranquilo vacía una barra llena" y la tasa que puse (0.25/día) descargaba 7.5 de 9. Un test que asertaba el criterio -no la tasa- lo cazó en el primer intento. Cuando una constante sale de una intención, testear la intención.
- **2026-08-03 · verificación** — Tener UN llamador no es estar integrado: `codex/bias.py` estaba construido, testeado y llamado (por el latido y los demos), y aun así las tres puertas que James usa —transmitir, diálogo y Score— pedían el loadout sin bias, así que la hora del mundo no inclinaba nada. El barrido de "quién me llama" da falso verde si una sola ruta alcanza: la pregunta es si me llaman TODOS los caminos que deberían.
- **2026-07-30 · proceso** — El Taller abierto conserva en memoria el código con el que arrancó: un fix en `codex/` no tiene efecto hasta reiniciar `taller/servidor.py`. Si un cambio "no hizo nada" en el Taller, descartar esto primero.

<!-- completar: James, los errores que ya te comiste acá.
     Los que más rinden son los que te hicieron perder una tarde. -->

---

## Categorías en uso

`verificación` · `agentes` · `proceso` · `contexto` · `estructura` · `datos`
