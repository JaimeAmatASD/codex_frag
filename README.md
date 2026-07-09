# Codex Fragmentum

Un engine para crear ficciones interactivas vivas: mundos que siguen funcionando aunque nadie los mire, habitados por seres que perciben cada uno desde su propio cristal cognitivo, donde la información viaja de boca en boca y se deforma en cada salto. El lema operativo del proyecto: **donde la verdad muere con el testigo**.

El motor mantiene el estado del mundo; el LLM nunca es fuente de verdad, solo narra lo que el motor decide, refractado por el cristal de quien percibe. Cada mundo es una carpeta portable e independiente.

## Estado actual

**Paso 1 del MVP: completo.** Motor cognitivo multi-ser funcionando: memetario instanciable por ser, loadout (qué memes se activan ante una situación), decaimiento y refuerzo asintóticos, bias circadiano sobre reloj del mundo ficcional, embeddings locales (fastembed), persistencia unificada con puerta única de escritura, MockClient para el enchufe del LLM. 31 tests.

**Paso 2 (en curso): la mutación del rumor.** La apuesta central del proyecto: que cuando un ser le cuenta algo a otro, la versión que el receptor guarda quede deformada por su cristal, con linaje rastreable en un grafo.

## Correr

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest                          # la suite completa, sin red ni tokens
python demos/prueba_paso1.py    # demo con embeddings reales (baja ~90 MB la primera vez)
```

El demo carga dos seres (un pescador supersticioso y un comerciante escéptico), les da la misma noticia, y muestra que cada uno activa memes distintos, coherentes con quién es.

## Estructura

- `codex/` — el motor. Cada módulo documenta en su docstring qué regla de diseño encarna y de qué bug real (del prototipo Fray Tomás) nace.
- `tests/` — un archivo por módulo; deterministas, sin red, sin tokens (codificador de embeddings inyectable, cliente LLM mock).
- `mundos/` — cada mundo es una carpeta: definiciones de seres en JSON legible (la semilla, versionada), estado vivo en SQLite (runtime, no se versiona).
- `docs/` — la memoria de diseño del proyecto: visión (Fase 0), los seis ADRs, el sistema de corpus, la verificación del prototipo, y los prompts de arranque de cada fase.
- `skills/` — fuentes de los skills de Claude que acompañan el desarrollo.

## Las cinco reglas

Nacen de bugs reales del prototipo anterior (Fray Tomás) y el código las cumple por construcción: (1) cada dato vive en un solo lugar; (2) ningún módulo escribe estado salvo la puerta única (`persistencia.py`); (3) toda degradación se loguea, nunca `except: pass`; (4) "estuvo en el loadout" y "fue efectivamente usado" son cosas distintas y se registran distinto; (5) tests y cliente LLM mock desde el primer módulo.

## Documentación

Empezar por `docs/VISION_FASE0.md` (qué es esto y qué es irrenunciable) y `docs/adr/` (las decisiones difíciles de revertir, con sus costos aceptados). Regla de precedencia: ADRs y Fase 0 mandan sobre el resto de la documentación cuando se contradicen.

---

*Proyecto personal de James, en construcción lenta y firme. Python 3.11+, pydantic, networkx, fastembed.*
