# ADR-005: La inteligencia del sistema se escalona en capas de costo con degradación elegante

*Estado: aceptada — Junio 2026*

---

## Contexto

Codex se construye sobre IA generativa, que cuesta dinero y depende de proveedores externos. La Fase 0 estableció que el proyecto no debe ser adicto a ningún proveedor, debe funcionar con IA barata o gratis como línea de base, y debe poder degradar a historias más simples si los recursos faltan, en lugar de romperse.

Hace falta una decisión arquitectónica que materialice esa filosofía: cómo se distribuye el trabajo de "pensar" del sistema entre recursos de distinto costo, y cómo se garantiza que la falta de los recursos caros no rompa el sistema.

## Opciones consideradas

### Opción A: Todo al mejor LLM disponible

Cada tarea que requiere inteligencia se resuelve con el mejor modelo. Máxima calidad.

Ventajas: calidad uniforme alta, simplicidad de no tener que decidir qué va dónde.

Desventajas: costo insostenible para uso prolongado, dependencia total de que exista y sea accesible un modelo caro, punto único de falla (si el proveedor cae o encarece, el sistema se vuelve inviable), desperdicio (tareas triviales resueltas con un modelo caro).

### Opción B: Todo a un modelo barato o local

Todo se resuelve con lo más barato disponible. Mínimo costo, máxima independencia.

Ventajas: costo mínimo, independencia máxima.

Desventajas: los momentos que merecen brillo literario no lo tienen, la experiencia se aplana en los picos narrativos que más importan.

### Opción C: Capas de costo creciente, eligiendo la más barata que sirva

La inteligencia se escalona en capas: código puro, modelos locales o gratuitos, IA barata, IA cara. Cada tarea se resuelve en la capa más barata que la resuelva aceptablemente. Si una capa superior no está disponible, el sistema degrada a las inferiores con pérdida de calidad controlada, no con ruptura.

Ventajas: costo optimizado (cada tarea en su capa apropiada), independencia (la línea de base son las capas baratas), sin punto único de falla (la caída de la capa cara degrada, no rompe), aprovecha recursos caros cuando los hay sin depender de ellos.

Desventajas: requiere decidir, por cada tarea, en qué capa vive, lo que es trabajo de diseño continuo; requiere que los prompts funcionen razonablemente en modelos modestos; agrega la complejidad de tener varias capas y la lógica de ruteo entre ellas.

## Decisión

Se adopta la Opción C: escalonamiento por capas de costo con degradación elegante.

Las capas, de más barata a más cara, son cuatro. Código puro para todo lo determinista o casi determinista (reglas de juego, cálculos, mapa, decaimiento, propagación, clocks, aritmética de la mecánica). Modelos locales o gratuitos para embeddings, clasificaciones por similitud, y prosa de baja exigencia (el modelo all-MiniLM-L6-v2 de Fray Tomás corre local). IA barata para narración que aparece pero no es culminante y para seres de complejidad media. IA cara solo para los momentos donde la calidad literaria define la experiencia y se recuerda.

La regla de decisión, aplicable a cada funcionalidad nueva, es preguntar en orden: ¿se puede con código? Si sí, código, aunque cueste más programarlo. ¿Con modelo local o embeddings? Entonces ahí. ¿Necesita lenguaje sin brillo? IA barata. ¿Es un momento que se nota y se recuerda? Recién ahí IA cara. El sesgo es siempre hacia la capa más barata que haga el trabajo aceptablemente.

La degradación elegante es requisito: la línea de base son las capas baratas, que ya alcanzan para que el sistema funcione. La IA cara es lujo opcional. Si la IA cara desaparece o encarece, el sistema desplaza trabajo hacia abajo y las historias se hacen más simples, pero sigue funcionando. No hay un piso de potencia de IA por debajo del cual Codex no corre; hay un gradiente donde la riqueza de la ficción se adapta a los recursos.

Para que la degradación funcione, la complejidad de la ficción es parametrizable: cuántos seres de alma completa, con qué frecuencia se invoca la capa cara, cuán elaborada es la simulación. Esos parámetros se ajustan según los recursos, y se relacionan con los niveles de complejidad de los seres (ver ADR sobre estratificación).

## Consecuencias

### Positivas

Independencia de proveedores, materializada. La línea de base barata o local significa que ningún proveedor caro es indispensable. Conecta con ADR-001 (el sistema no depende del modelo porque el estado vive en el motor) para blindar al proyecto contra la volatilidad de proveedores, precios y disponibilidad.

Sin punto único de falla por costo o disponibilidad. La caída de la capa cara degrada la calidad, no rompe el sistema. Esta es la propiedad de degradación elegante, una de las más valiosas en sistemas construidos sobre IA en un contexto de proveedores volátiles.

Costo optimizado. La mayor parte del trabajo vive en código y capas baratas, así que el costo operativo se mantiene bajo. La capa cara, acotada a los picos, no domina el gasto.

Robustez del código. Cuanto más trabajo vive en la capa de código puro, más del sistema es determinista, auditable, gratis, y sin alucinaciones. Esto mejora la confiabilidad general.

### Negativas

Trabajo de diseño continuo. Cada funcionalidad nueva exige decidir en qué capa vive, lo que es una decisión recurrente que no se puede automatizar del todo. Es carga cognitiva permanente sobre el desarrollo.

Más trabajo de programación al preferir código. Resolver algo en código cuesta más esfuerzo inicial que tirárselo a un LLM. Se acepta este costo a cambio de robustez e independencia: el código, una vez escrito, es gratis y confiable para siempre.

Los prompts deben funcionar en modelos modestos. Esto es una restricción de diseño sobre los templates: no pueden depender del mejor modelo para producir resultados aceptables. Diseñar para el piso y que el techo sea bonus. Es disciplina extra al escribir prompts.

Complejidad de ruteo. Tener varias capas y la lógica que decide y dirige cada llamada a su capa es maquinaria que hay que construir y mantener. El cliente LLM abstraído y la estrategia de tiers del skill de prompts absorben parte de esto, pero es complejidad real originada en esta decisión.

## Notas de implementación

Esta decisión generaliza la filosofía de Fray Tomás (hacer todo lo posible localmente, llamar al LLM solo para lo profundo) agregando sub-niveles dentro del trabajo de IA y la capa de código puro por debajo. La estrategia de tiers del skill de prompts es la implementación de las capas de IA; esta decisión la enmarca en una filosofía más amplia que incluye el código y los modelos locales. Se relaciona estrechamente con el ADR sobre estratificación de complejidad de los seres, que es la perilla narrativa con la que se ajusta el consumo de las capas.
