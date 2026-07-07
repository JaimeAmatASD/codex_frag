# Codex Fragmentum — Prompt de arranque para Claude Code
## Paso 2 del MVP: la mutación del rumor (el corazón del proyecto)

*Pegá este documento al inicio de la sesión de Claude Code, con el repo codex_frag como directorio de trabajo. Presupone el paso 1 completo (lo está: motor cognitivo multi-ser, 31 tests).*

---

## Qué es este paso y por qué es el más importante

Este paso construye la apuesta conceptual central de Codex: cuando un ser le cuenta algo a otro, la versión que el receptor guarda queda DEFORMADA por su cristal cognitivo, y esa deformación tiene linaje rastreable. "La verdad muere con el testigo" deja de ser un lema y se vuelve mecánica.

Es también el experimento que valida o refuta el proyecto. Si la mutación de un rumor entre el pescador y el comerciante se siente reveladora (leés las dos versiones y cada una delata a su portador), Codex cumple su promesa y seguimos. Si tras iterar los prompts las mutaciones son genéricas o arbitrarias, PARAMOS y repensamos antes de construir nada más. Entrá al paso con esa conciencia: no es un paso más.

Antes de escribir código, leé: docs/adr/ADR-001 (el motor manda, el LLM ilustra), ADR-004 (grafo con árboles de mutación), ADR-005 (capas de costo), docs/VERIFICACION_CODIGO_FRAY_TOMAS.md (qué hay en el prototipo), y el código existente en codex/ (especialmente modelos.py, persistencia.py, loadout.py: el paso 2 se apoya en ellos y sigue sus patrones).

## Qué construir

Tres módulos nuevos, siguiendo los patrones ya establecidos (Pydantic, puerta única, logging, tests por módulo).

**codex/hechos.py — los modelos.** Un Hecho es algo que objetivamente ocurrió en el mundo (la verdad raíz, exista o no quien la conozca completa): id, contenido, momento del mundo, lugar (string simple por ahora; no hay sistema de lugares todavía). Una Version es cada forma en que ese hecho circula: id, hecho_id, contenido, version_padre (None si es la raíz), emisor (None en la raíz), receptor, momento, y distancia_raiz (similitud coseno entre su contenido y el de la raíz, con los embeddings existentes). Validados con Pydantic como todo en el proyecto.

**codex/grafo_mundo.py — el grafo de información.** Un MultiDiGraph de NetworkX por mundo que sostiene hechos, versiones y la relación "quién conoce qué versión". Operaciones mínimas: registrar un hecho (crea la raíz), registrar una versión derivada, consultar qué versión(es) de un hecho conoce un ser, y reconstruir el linaje de una versión (la cadena de deformación hasta la raíz). La persistencia del grafo pasa por la puerta única: la clase Persistencia crece con guardar_grafo/cargar_grafo, serializando en formato NO-pickle (node-link JSON de networkx está bien) dentro de la carpeta del mundo. Cada dato en un solo lugar: el grafo es la única fuente de quién sabe qué.

**codex/transmision.py — la operación central.** La función transmitir(emisor, receptor, version, ...) que hace el ciclo completo: (1) toma el contenido que el emisor cuenta; (2) calcula el loadout del RECEPTOR ante ese contenido (ya existe: calcular_loadout con la situación siendo el contenido transmitido) — ese loadout es el cristal activo con el que el receptor escucha; (3) arma el prompt de mutación con el contenido recibido más los memes activos del receptor (PF y seleccionados, con sus textos); (4) llama al LLM por la interfaz ClienteLLM existente; (5) valida la respuesta (estructura Pydantic: contenido_entendido, y opcionalmente qué memes resonaron) — si no valida, reintenta una vez y si falla degrada con log a "transmisión sin deformación" (el receptor guarda lo que oyó tal cual, anotado); (6) registra la versión nueva en el grafo con su linaje y distancia, vía la puerta única; (7) registra las activaciones del receptor (loadout y movilizados: los memes que el LLM reportó como resonantes son los movilizados — regla 4).

El prompt de mutación es la pieza artesanal del paso. Principio (ADR-001): el LLM no decide qué pasó; recibe el contenido oído y el cristal del receptor, y devuelve CÓMO ese receptor lo entendió y lo recontaría. La deformación sale de que el cristal tiñe la comprensión: el pescador supersticioso oye "avistamiento extraño" y entiende presagio; el comerciante oye lo mismo y entiende oportunidad o fraude. Instrucción clave al modelo: conservar el núcleo del hecho pero teñir interpretación, énfasis, causa atribuida y color emocional según los memes activos; prohibido inventar hechos nuevos no derivables del contenido oído. Empezá con un template simple y iterá contra casos reales; el skill codex-fragmentum-llm-prompts tiene los principios de templates y validación.

**Cliente LLM real mínimo.** Para probar calidad hace falta un cliente real además del mock: implementá UNO solo, el más simple posible, contra la interfaz ClienteLLM existente (una clase, un método responder), para el proveedor barato que James elija (línea de base del ADR-005). Sin router de tiers todavía: un solo modelo barato configurable por variable de entorno. El router llega en pasos posteriores.

## La prueba del paso (dos niveles)

Nivel 1, flujo con MockClient (sin tokens, determinista, en tests/): sembrar el hecho raíz del avistamiento; transmitir del pescador al comerciante con el mock devolviendo una respuesta guionada válida; verificar que la versión queda en el grafo con linaje correcto, distancia calculada, activaciones registradas distinguiendo loadout de movilizados, y que el linaje se reconstruye raíz→versión. También el camino degradado: respuesta inválida dos veces → transmisión sin deformación, logueada.

Nivel 2, calidad con LLM real (demos/prueba_paso2.py): el hecho raíz llega al pescador y al comerciante; cada uno recuenta; imprimir las dos versiones lado a lado con su distancia a la raíz y los memes que resonaron. Después una cadena de dos saltos (raíz → pescador → comerciante) mostrando la deriva acumulada. El criterio de éxito lo juzga James leyendo: ¿cada versión delata a su portador? ¿La cadena de dos saltos cuenta una historia de deformación creíble?

## Reglas (las mismas cinco, más dos del paso)

Las cinco reglas del paso 1 siguen vigentes y el código nuevo las sigue (mirá cómo las cumple el existente). Dos adicionales de este paso: (a) el LLM propone, el motor dispone — ninguna versión entra al grafo sin validación Pydantic, y toda degradación de validación se loguea; (b) no sobre-modelar — UN hecho semilla, DOS seres, transmisiones directas; nada de propagación automática, velocidades, ni poda del grafo todavía.

## Lo que NO es del paso 2

No construyas: lugares ni grilla espacial, propagación automática entre muchos seres, velocidades de propagación, poda o archivado del grafo, el router de tiers, Blades, corpus, interfaz de juego, modo servidor. Si te encontrás en cualquiera de esas cosas, te saliste del paso.

## Cómo proceder

Empezá proponiendo los modelos Pydantic (Hecho, Version, y el esquema de respuesta del LLM) y el template del prompt de mutación en texto plano, y esperá el visto bueno de James sobre ambos antes de escribir el resto: son las dos decisiones de las que cuelga el paso. Después: grafo_mundo con tests, transmision con tests sobre mock, cliente real mínimo, y el demo de calidad al final. Mostrale a James las dos versiones del rumor apenas existan: su lectura es el instrumento de medición del paso.
