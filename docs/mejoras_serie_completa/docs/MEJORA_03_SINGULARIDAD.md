# Codex Fragmentum — Mejora 03: Singularidades Narrativas
## El evento inevitable: fija el contexto, no el resultado

*Tercera mejora de la serie (ver docs/ANALISIS_BRAINSTORMING_JUL2026.md, parte 2, mejora 5). Presupone hechas las mejoras 01 y 02. Leé codex/reloj.py, codex/hechos.py, codex/grafo_mundo.py y codex/persistencia.py antes de empezar.*

## La idea en tres líneas

Una Singularidad es un evento agendado en el reloj del mundo que ocurre pase lo que pase: "la noche del día N, el kraken emerge frente a la costa". No determina qué historias produce (eso depende de quiénes estén y qué sepan); determina que ALGO ocurre. Le da destino al mundo sin quitarle libertad a nadie.

## Decisiones ya tomadas (no re-debatir)

**Semilla versionable, estado vivo aparte (regla 1).** Las singularidades del mundo viven en mundos/<m>/singularidades.json (lista de objetos: id, momento del mundo en que ocurre, contenido del hecho, lugar, origen, y opcionalmente testigos_iniciales con ids de seres que la presencian). Es semilla: se versiona y se edita. La marca de "ya disparada" vive SOLO en el SQLite del mundo, por la puerta única. El reset del mundo las vuelve pendientes.

**Disparo al avanzar el reloj, idempotente.** Una función chequear_singularidades que, al avanzar el tiempo del mundo, detecta las pendientes cuyo momento quedó alcanzado y las registra como HECHO RAÍZ en el grafo (vía la puerta única, como cualquier hecho), marcándolas disparadas. Nunca dispara dos veces. Si hay testigos_iniciales, esos seres quedan conociendo la versión raíz; si no hay, el hecho existe sin testigos (el mundo sabe cosas que nadie sabe todavía).

**El Taller la muestra y la dispara.** En la zona Mundo: la lista de singularidades con su estado (pendiente/disparada) y un control para avanzar el reloj del mundo (horas o días). Al avanzar, si algo dispara, aparece en Lore como hecho nuevo. Crear/editar singularidades desde el Taller: formulario mínimo que escribe la semilla.

**Una sola en el mundo de prueba.** Sembrar exactamente UNA (el kraken, o lo que James prefiera). La singularidad vale porque es rara.

## Tests (deterministas, sin red)

Avanzar el reloj más allá del momento dispara una sola vez (idempotencia probada avanzando dos veces); antes del momento no dispara; el hecho raíz queda en el grafo con su contenido y lugar; los testigos_iniciales conocen la raíz; el reset del estado vivo la vuelve pendiente sin tocar la semilla.

## Criterio de éxito (James en el Taller)

Avanzar el reloj hasta la noche señalada, ver el kraken aparecer en Lore, y después contárselo a dos seres y leer las versiones: el evento era inevitable, las historias que produce no. Si se siente como destino y no como script, funciona.

## Lo que NO es de esta mejora

Ni cadenas de singularidades, ni condiciones más allá del momento (nada de "si X entonces"), ni consecuencias mecánicas automáticas (clocks que arrancan solos), ni propagación automática a más seres. Momento, hecho, testigos opcionales: eso es todo.

## Cómo proceder

Primero el modelo Pydantic y el formato de la semilla, visto bueno de James, después la función de chequeo con tests, la integración al avance del reloj, y al final el Taller. Commits chicos en castellano.
