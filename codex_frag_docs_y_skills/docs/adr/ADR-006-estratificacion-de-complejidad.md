# ADR-006: Los seres tienen complejidad graduable en niveles, con interfaz uniforme

*Estado: aceptada — Junio 2026*

---

## Contexto

El núcleo irrenunciable de Codex, según la Fase 0, es la estructura del alma de Fray Tomás: memetario, autoobservación, plasticidad. Pero no todos los seres de un mundo necesitan esa alma completa. Un mundo bien hecho tiene protagonistas con vida interior profunda y también figuras de fondo que cumplen su función sin necesitar autoobservación ni crisis biográficas. La densidad ontológica se concentra donde importa, como en cualquier ficción.

Hace falta decidir cómo se modela esa variación de complejidad. La decisión tiene dos motivaciones que conviene no confundir: una narrativa (los mundos necesitan seres de distinta densidad, es buen diseño de ficción) y una de recursos (instanciar alma completa para cientos de seres sería caro, conecta con ADR-005). Ambas empujan hacia lo mismo.

## Opciones consideradas

### Opción A: Todos los seres con alma completa

Cada ser, del protagonista al tabernero, tiene memetario completo, autoobservación, plasticidad.

Ventajas: uniformidad de implementación, cualquier ser puede volverse protagonista sin conversión.

Desventajas: costo computacional y de IA prohibitivo para muchos seres, desperdicio (el tabernero no necesita crisis biográficas), no refleja cómo son las ficciones (densidad uniforme es antinatural).

### Opción B: Dos clases separadas, seres completos y seres simples

Una clase para seres profundos y otra distinta para figuras de fondo, con código separado.

Ventajas: cada clase optimizada para su rol.

Desventajas: el resto del sistema tiene que saber con qué clase habla, llenándose de condicionales; convertir un ser simple en uno profundo (cuando la historia lo requiere) significa cambiar de clase, operación invasiva; dos caminos de código que mantener.

### Opción C: Complejidad graduable en niveles, con interfaz uniforme

Un solo tipo de ser que puede tener más o menos profundidad según su nivel. Los niveles van desde alma completa hasta etiqueta funcional. Todos los niveles comparten la misma interfaz: el resto del sistema interactúa con cualquier ser de la misma manera, y la profundidad es un parámetro interno del ser, no un tipo distinto. Los niveles pueden cambiar: un ser puede ascender o descender según la historia lo necesite.

Ventajas: el sistema trata a todos los seres uniformemente (sin condicionales por tipo), la profundidad se ajusta sin cambiar de tipo, el ascenso y descenso de nivel es natural, la complejidad escala con los recursos (perilla de ADR-005).

Desventajas: la interfaz uniforme tiene que estar bien diseñada para servir a todos los niveles, lo que requiere cuidado; un ser de nivel bajo que devuelve "menos riqueza" tiene que hacerlo de forma que el resto del sistema lo maneje sin sorprenderse.

## Decisión

Se adopta la Opción C: complejidad graduable en niveles con interfaz uniforme.

Los niveles, de más a menos profundo, son aproximadamente cuatro. Un ser de complejidad máxima tiene las tres capas del memetario, autoobservación activa, plasticidad completa (cambian pesos, se forman clusters de carácter, hay crisis biográficas), corpus con sus dimensiones, hitos. Es un Fray Tomás; hay pocos por mundo. Un ser de complejidad media tiene memetario simplificado, plasticidad básica (los pesos cambian pero sin autoobservación profunda ni crisis elaboradas), corpus liviano; piensa pero no se autoobserva hondo. Un ser de complejidad baja tiene unos pocos rasgos definidos, sin memetario real ni plasticidad; es funcional y consistente pero sin vida interior; el tabernero. Un ser mínimo es casi una etiqueta que se enciende solo si el jugador insiste en interactuar, infiriendo algo de memetario sobre la marcha.

La interfaz es uniforme: el motor que calcula cómo percibe un ser funciona igual para el alma completa y para el tabernero, devolviendo más o menos riqueza según el nivel, sin que el resto del sistema necesite saber con qué nivel habla. La profundidad es un atributo interno del ser, no un tipo distinto.

Los niveles pueden cambiar. Un ser de nivel bajo que la historia vuelve importante puede ascender, ganar memetario, desarrollar vida interior. Uno que sale del foco puede descender. El ascenso y descenso tiene sentido narrativo (los personajes ganan alma cuando la historia los necesita) además de técnico (gestión de recursos).

## Consecuencias

### Positivas

El sistema queda limpio: una sola interfaz para todos los seres, sin condicionales por tipo desperdigados por el código. La profundidad se maneja internamente.

Refleja cómo son las ficciones reales, con densidad concentrada donde importa. Es buen diseño narrativo, no solo optimización.

Es la perilla de recursos de ADR-005. Ajustar cuántos seres de cada nivel hay es ajustar el consumo de las capas caras de IA. En modo austero, pocos seres de alma completa; en modo rico, muchos. El mismo mundo se estira y encoge según recursos.

El ascenso y descenso de nivel da vida al mundo: personajes secundarios que se vuelven protagonistas, protagonistas que se desvanecen en figuras de fondo, como en la escritura real.

### Negativas

La interfaz uniforme tiene que estar muy bien diseñada para servir a todos los niveles sin filtrarse. Si un ser de nivel bajo devuelve datos en una forma que el resto del sistema no espera, aparecen bugs sutiles. Diseñar esa interfaz con cuidado es trabajo real.

El ascenso de nivel implica "rellenar" la profundidad que faltaba (un tabernero que asciende necesita que se le genere memetario). Ese proceso de enriquecimiento sobre la marcha hay que diseñarlo, y puede invocar IA (inferir el memetario desde los rasgos previos), con su costo.

Riesgo de que los niveles se multipliquen. Cuatro niveles es manejable; si la tentación de matizar lleva a ocho o diez niveles, la complejidad de manejarlos crece. Disciplina: mantener pocos niveles claros.

## Notas de implementación

Esta decisión se relaciona estrechamente con ADR-005 (las capas de costo): los niveles de complejidad son la perilla narrativa con la que se ajusta el consumo de recursos. También con ADR-001 (el motor mantiene el estado): el estado de un ser incluye su nivel de complejidad. La estratificación está esbozada en el skill de memetario (estratificación por profundidad) y en el de arquitectura. El mecanismo de ascenso y descenso de nivel, y el proceso de enriquecimiento al ascender, son piezas a desarrollar; no son del MVP (que tiene un elenco fijo y pequeño) pero el diseño los contempla desde el principio para no cerrarse la puerta.
