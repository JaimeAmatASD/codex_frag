# Codex Fragmentum

Engine para ficciones interactivas vivas: mundos que siguen funcionando aunque
nadie los mire, seres que perciben desde su propio cristal, información que se
deforma de boca en boca. **El motor manda, el LLM ilustra.** No es un juego
terminado ni un producto: es la mesa de trabajo autoral de James.

Qué es y cómo se corre: `README.md`. Por qué es así: `docs/` (visión, ADRs).

---

## Con quién estás trabajando

James dirige el proyecto. No es programador profesional pero sus docs definen
el proceso; tiene sensibilidad literaria fina y el criterio final es suyo.

- No le muestres diffs: contale qué hace el cambio en idioma del dominio,
  qué quedó verificado y qué tiene que mirar él.
- Términos técnicos: cinco palabras entre paréntesis y seguir.
- Las decisiones técnicas se deciden y se informan. Lo que solo él sabe
  (el criterio literario, qué sería un desastre) se le pregunta.
- Nada construido se commitea sin su veredicto escrito — las guías viven en
  `test manuales/`, con espacio para su firma.

## Comandos

```bash
./venv/bin/pytest                       # la suite completa: sin red, sin tokens
./venv/bin/python taller/servidor.py    # el Taller (puerto 8765, abre el navegador)
./venv/bin/python demos/vivir.py --mundo prueba --ser el_que_no_muere --dias 30
```

La key de Gemini sale de `GEMINI_API_KEY` o de `~/.gemini_key`.

## Stack

Python ≥3.11 · pydantic v2 · networkx · fastembed (embeddings locales, CPU) ·
FastAPI + uvicorn (solo el Taller) · pytest + httpx. Estado vivo por mundo en
SQLite (`mundos/<mundo>/estado.db`, no se versiona); semillas en JSON legible.

## Reglas duras

Las cinco nacen de bugs reales del prototipo Fray Tomás (`docs/PROMPT_PASO_1.md`);
cada módulo de `codex/` documenta en su docstring cuál encarna. Mantené eso.

- **El motor manda, el LLM ilustra.** El LLM nunca es fuente de verdad (ADR-001).
- **Una sola puerta de escritura del estado**: todo pasa por `codex/persistencia.py`
  (reglas 1 y 2). Ningún módulo escribe pesos o activaciones por su cuenta.
- **Nada de except-pass**: toda degradación se loguea, aunque no rompa (regla 3).
- **"Estuvo en el loadout" ≠ "fue movilizado"**: se registran distinto (regla 4).
- **Los tests no tocan la red ni gastan tokens**: LLM mock con guion, codificador
  de embeddings inyectable (regla 5).
- **El contenido es enchufable**: vive en la carpeta del mundo o del ser; el motor
  en `codex/` no conoce contenido concreto (ADR-007).

## Cómo trabajar acá

- **Cambios chicos y verificables.** Uno por vez, suite en verde entre uno y otro.
- **No sobre-ingeniería.** Si una función alcanza, no armes una jerarquía de clases.
- **No toques lo que no te pidieron.** Si ves algo mal al lado, avisá; no lo
  arregles de prepo.
- **"Listo" significa suite corrida en verde**, no "debería pasar".
- Antes de agregar una dependencia, preguntá.
- Todo bug arreglado deja un test que lo reproduce y una línea en `lessons.md`.

## Estructura

- `codex/` — el motor (lo único instalable)
- `taller/` — el dashboard autoral (FastAPI, fuera del motor)
- `mundos/` — cada mundo una carpeta portable: semilla JSON versionada, estado runtime
- `tests/` — un archivo por módulo; deterministas
- `demos/` — corridas de mesa por terminal
- `docs/` — la memoria de diseño: visión, ADRs, corpus, prompts de cada fase
- `test manuales/` — guías de veredicto paso a paso para James

## Glosario

Solo lo transversal; el detalle vive en `docs/CORPUS_DISENO.md` y los ADRs.

- **meme** — unidad de creencia o idea de un ser, con peso que sube y baja
- **memetario** — todos los memes de un ser
- **loadout / el cristal** — los memes que despiertan ante una situación
- **PF / piedra fundacional** — meme identitario; no se toca por vías normales
- **movilizado** — meme efectivamente usado, no solo convocado al loadout
- **transmisión** — un ser le cuenta algo a otro; el rumor muta por su cristal
- **Score** — escena jugada con posición, efecto y dados (estilo Blades)
- **SPECULUM** — el ser se lee a sí mismo y propone ajustes; el autor dispone
- **el latido** — la vida ociosa: ticks de rutina sin LLM entre visitas
- **bitácora** — JSONL por mundo donde el Taller registra cada corrida
