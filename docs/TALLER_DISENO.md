# El Taller — diseño del dashboard autoral

*Estado: diseño aprobado por James — Julio 2026. Es una herramienta de autor, no
parte del motor ni del juego: la categoría de `demos/`, con interfaz.*

## Qué es y para qué

Un dashboard súper simple en el navegador para que James pueda **pulir el mundo de
forma intuitiva**: crear y editar personajes y lore, tirarles noticias y Scores,
leer (o escuchar) lo que sale, ajustar los templates, y comparar resultados entre
iteraciones. También corre la suite de tests con un click.

El ciclo que habilita es el del proyecto entero: **ajustar → probar → comparar →
volver a ajustar**, sin tocar JSON ni terminal.

## Decisiones

- **Carpeta `taller/`, fuera del motor.** El servidor importa `codex` igual que los
  demos. Nada del motor sabe que el taller existe.
- **FastAPI + uvicorn, una sola página HTML sin build.** Dos dependencias nuevas
  (grupo opcional `taller` en pyproject). Vanilla JS; sin frameworks ni npm. El
  paso 5 prevé exponer el motor como servidor websocket: este servidor HTTP fino
  es un ensayo en esa dirección, no un compromiso.
- **El audio vive entero en el navegador.** Dictado con Web Speech API (Chrome) en
  todo campo de texto; lectura con `speechSynthesis` (castellano si hay) en toda
  narración o versión. Cero dependencias de audio; el motor ni se entera.
- **Arranque sin fricción.** `./venv/bin/python taller/servidor.py` abre el
  navegador solo. Si `GEMINI_API_KEY` no está en el entorno, se busca en
  `~/.gemini_key`.
- **Semillas versionables.** Lo que el taller crea/edita (ser.json, hoja_reglas.json,
  templates) son archivos del repo, diffeables en git. El estado vivo sigue solo en
  el SQLite del mundo (regla 1); el taller lo toca únicamente por la puerta única,
  salvo el reset (borrar los archivos de runtime es operación de herramienta).

## Las siete zonas de la página

1. **Mundo.** Selector de carpetas de `mundos/` + crear mundo nuevo + botón
   "resetear estado vivo" (borra `estado.db` y `grafo.json`; las semillas quedan).
2. **Personajes.** Lista de seres del mundo elegido. Formulario de crear/editar:
   `ser_id`, `origen`, `mana_max`, piedras fundacionales y memes (tipo, texto,
   peso, costo, conexiones), y la hoja mecánica (`stress_max`, acciones → rango
   0-4). Guarda `seres/<id>/ser.json` y `hoja_reglas.json`. Al lado de la semilla,
   **el estado vivo en solo lectura**: pesos actuales, veces en loadout, veces
   movilizado — en quién se está convirtiendo el personaje.
3. **Diálogo.** Hablarle directo a un ser, sin secreto ni emisor: escribís una
   escena, una pregunta o una línea de otro personaje, y responde en su voz con
   el cristal ACTUAL (calculado sobre la charla acumulada, turno a turno). Es
   exploración, no transmisión: no registra activaciones ni mueve pesos — pero
   sí queda en la bitácora para comparar intentos. Incluye un **modo editar**:
   un panel al lado de la charla para tocar el peso vivo de un meme a mano
   (por `POST /seres/<id>/pesos`, la puerta única de siempre) y ver el efecto
   en el próximo turno, sin salir de la pantalla. (La otra mitad de "modo
   editar" que se pensó —que la charla misma proponga cambios y el autor los
   apruebe— se pospuso a propósito: es el mismo motor de propuestas que va a
   traer el SPECULUM, mejora 05; construirlo una sola vez.)
4. **Lore.** Registrar hechos (id, contenido, momento, lugar) por la puerta única
   del grafo, y ver el árbol de versiones de cada hecho: quién conoce qué, con qué
   distancia a la verdad.
5. **Probar.** Tres acciones:
   - *Contale algo a un ser*: emisor (testigo u otro ser), receptor, hecho o
     versión → `transmitir` con Gemini real → versión nueva, memes resonantes,
     distancia.
   - *Score*: ser, acción de su hoja, descripción libre (tipeada o dictada) →
     se muestran posición/efecto/dados ANTES de tirar → tirar, o empujar pagando
     stress → categoría, narración, stress y clock actualizados. Si el mundo no
     tiene clock de amenaza, el taller ofrece crearlo.
   - *Correr tests*: `pytest -q` en subproceso, salida con verde/rojo.
6. **Templates.** Editor de texto plano para `templates/mutacion.txt`,
   `templates/narracion_score.txt` y `templates/dialogo.txt` — el lugar donde
   los docs mandan iterar cuando las voces no revelan. Guardar y re-probar sin
   salir de la página.
7. **Bitácora.** Toda transmisión, todo Score y todo diálogo quedan registrados
   (entrada, salida, personaje, términos, fecha) en un JSONL por mundo dentro
   de `taller/bitacora/`. La zona lista las entradas y permite poner dos lado
   a lado: pulir es comparar.

## La API del servidor (fina, envuelve el motor)

JSON simple: `GET/POST /mundos`, `GET/POST /seres`, `GET /seres/<id>/estado`,
`POST /seres/<id>/pesos`, `GET/POST /hechos`, `POST /transmitir`, `POST /dialogo`,
`POST /score/evaluar`, `POST /score/tirar`, `POST /tests`, `GET/PUT /templates/<nombre>`,
`GET /bitacora`, `POST /reset`.
Cada endpoint hace lo que los demos ya hacen (Persistencia, Memetario, GrafoMundo,
transmitir, SistemaBlades, narrar_resolucion) — sin lógica nueva de motor, con una
excepción a propósito: `/dialogo` trae `codex/dialogo.py`, un primitivo chico y
nuevo (hablarle a un ser a partir de texto libre, sin Hecho ni emisor) que el
motor todavía no tenía.

## Errores

Si Gemini falla (HTTP, timeout, red), el motor ya degrada (`ErrorLLM`): el taller
muestra el resultado degradado con un aviso visible. Nunca cuelga (espera acotada
por `TIMEOUT_SEGUNDOS`) y nunca crashea la página. Las validaciones de pydantic
(un ser mal formado, un hecho duplicado) vuelven como mensaje legible en el
formulario.

## Tests

La API se testea sin red ni navegador, con `MockClient` y mundos en tmp_path:
crear ser → los JSON quedan en disco y validan; transmitir → la versión queda en
el grafo con linaje; score → los efectos se aplican (stress/clock); diálogo →
responde en su voz sin tocar activaciones ni pesos, y el peso vivo solo se mueve
por `/seres/<id>/pesos` (el modo editar); bitácora → las corridas quedan
registradas; templates → guardar y releer. La página HTML no se testea (es una
vista fina); dictado y lectura son features del navegador.

## Lo que NO es (límites explícitos)

- No es el juego: el loop jugable de la taberna es el paso 5.
- No hay corpus: eso es el paso 4 y manda `CORPUS_DISENO.md`.
- No hay import/export de cartuchos: prohibido por ADR-007 hasta que existan dos
  mundos reales que quieran intercambiar algo.
- No hay usuarios, ni auth, ni deploy: corre local, para una persona.
