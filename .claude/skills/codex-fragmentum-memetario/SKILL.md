---
name: codex-fragmentum-memetario
description: Motor cognitivo de los agentes vivos del proyecto Codex Fragmentum. El memetario funciona como piel sintética activa (no filtro pasivo) con tres capas distintas — Piedras Fundacionales como postura general, Memes Operativos como receptores específicos en competencia por mana limitado, Hitos Biográficos como cicatrices que reconfiguran la arquitectura. Cargá cuando el trabajo toque cómo los agentes piensan, palpan información, refractan estímulos, deciden sus acciones; cuando estés programando o tuneando el cálculo de loadout, el sistema de decaimiento, la activación de PF por umbral; cuando aparezcan dudas sobre cómo se acopla el cristal con el resto del sistema; cuando James diseñe un personaje nuevo o esté afinando los parámetros de mana, costos, pesos. Triggers en inglés — character cognitive engine, memetary system, cristal-piel architecture, loadout calculation, mana economy, cognitive layers, foundational stones, operational memes, biographical hits. Presupone codex-fragmentum-arquitectura cargado.
---

# Codex Fragmentum — Motor cognitivo de los agentes vivos

Este skill se ocupa específicamente del motor cognitivo del proyecto: cómo están construidos los cuerpos cognitivos de los agentes vivos (PJ, NPCs principales, dioses), cómo se calcula qué piensan en cada momento, cómo cambian a lo largo del tiempo. Si llegaste a este skill, James está trabajando en el corazón del proyecto, en lo que vuelve singular a cada personaje. Para el contexto general, asumí que el skill maestro codex-fragmentum-arquitectura ya está cargado.

## Por qué esto es la pieza más distintiva del proyecto

Vale la pena empezar por ahí porque condiciona todas las decisiones de diseño que vienen después. Codex Fragmentum se distingue de otros proyectos similares (AI Dungeon, simuladores narrativos, novelas interactivas) en que sus personajes no son chatbots con personalidad ni perfiles temáticos pasados al LLM. Son cuerpos cognitivos sintéticos con arquitectura propia, donde el LLM solamente ilustra desde lo que el cuerpo ya determinó.

La metáfora central que conviene tener internalizada es la del cristal sintético, no la de la lente. Una lente es pasiva, la luz pasa, sale deformada. Un cristal-piel es activo, palpa la realidad, decide qué tocar, se eriza con ciertos estímulos, ignora otros. Esta diferencia parece sutil pero cambia profundamente cómo se modelan los personajes. No estamos restringiendo qué información reciben, estamos dándoles un órgano sensorial con el que palparla.

Hay una razón filosófica que vale la pena nombrar porque a veces resurge cuando se discute alguna decisión técnica. La inteligencia biológica humana se construyó bottom-up a lo largo de eones, desde células hasta corteza cerebral, y por eso está encarnada. Cada concepto abstracto que pensamos descansa sobre estructuras sensoriales concretas. Un LLM funciona al revés, top-down, tiene todos los conceptos pero ningún sustrato corporal. El memetario es el cuerpo cognitivo sintético que le construimos al LLM para que pueda ser alguien específico mirando desde algún lugar específico, no narrador omnisciente sin alma.

Cuando programes algo del memetario, mantené esta imagen activa. Si te encontrás pensándolo como filtro, parate y reformulá como piel.

## Las tres capas

Cada agente vivo tiene tres capas cognitivas distintas. Son tres categorías ontológicas distintas, no tres versiones del mismo sistema. Operan a escalas temporales distintas y se afectan mutuamente sin colapsar en una sola cosa.

### Piedras Fundacionales

Son la postura general del cuerpo cognitivo, equivalentes al concepto de habitus en Bourdieu. Siempre activas, sin costo de mana, cambian poco y con dificultad. Son los valores profundos del personaje, su formación, lo que sigue creyendo aunque no esté pensándolo explícitamente.

Para Fray Tomás, las PF incluyen la Regla de San Benito, el poema de Borges sobre los justos, las parábolas de Lucas. Para un rey podrían ser los valores que le inculcaron de niño. Para un pescador del pueblo de Cala Norte podrían incluir la fe en el patrón de la barca, la lealtad al pueblo, el respeto al mar como cosa con dueños.

Las PF se modifican solamente mediante crisis biográfica documentada o mediante hitos biográficos suficientemente grandes. Esto las vuelve lentas pero estables, lo cual es deseable: la identidad del personaje a través del tiempo descansa principalmente en sus PF. Si las PF cambiaran fácilmente, los personajes serían inconsistentes.

Un personaje promedio tiene entre tres y nueve PF. Un dios puede tener menos pero más fuertes. Un personaje recién creado puede tener apenas una o dos, las que el motor más necesita establecer para que pueda actuar coherentemente desde el primer turno.

### Memes Operativos

Son los receptores específicos del personaje. Heurísticas, refranes, máximas, dichos. "Pega primero, pega por dos". "Más vale pájaro en mano". "Quien madruga, Dios lo ayuda". "Nunca confíes en un sacerdote que no come". "El mar tiene dueños y no los conoces".

A diferencia de las PF, los MO compiten por mana limitado. Hay un sistema económico interno donde el personaje tiene N puntos de mana disponibles (típicamente veinte) y cada meme cuesta entre uno y tres puntos según su peso. Si tiene treinta MOs en su catálogo y solo veinte puntos de mana, el sistema está obligado a elegir cuáles enciende en cada momento.

Esa elección no la hace el personaje conscientemente. La hace el motor calculando para cada MO disponible un score combinado de varios factores: su peso histórico (cuánto se usó antes con éxito), su afinidad semántica al contexto actual (medida vía embeddings), el bias circadiano del momento, los modificadores del lugar donde está parado. Los MOs que ganan el cálculo entran en el loadout activo y son los que efectivamente palpan la situación. Los que pierden quedan dormidos para esa situación.

El sistema de mana limitado no es restricción accidental, es feature crítico. Si el personaje pudiera tener todos sus memes activos siempre, sería el Funes de Borges: vería todo, recordaría todo, no podría decidir nada. La limitación lo fuerza a tener foco atencional en cada momento, lo cual produce humanidad cognitiva. Y como el foco cambia según contexto, cada situación produce un personaje levemente distinto del mismo personaje, lo cual es exactamente lo que vuelve vivos a los humanos reales.

### Hitos Biográficos

Son la categoría más distintiva del proyecto y la que requiere más cuidado al programarse. Un hito es un evento puntual irrepetible que reconfigura la arquitectura misma del agente. No es un meme que se activa en ciertas situaciones: es algo que le pasó al personaje y permanece como cicatriz cognitiva que cambia quién es.

La distinción entre meme e hito es categórica. Un meme es una regla generalizable que se aplica a múltiples situaciones (pega primero se aplica a infinitas peleas potenciales). Un hito es lo que pasó esa noche, en esa cala, a esa edad, con ese olor a mar (el avistamiento del kraken por Marcos solo pasó una vez). Los memes operan dentro de la arquitectura. Los hitos operan sobre la arquitectura.

Los efectos estructurales de un hito pueden incluir varias cosas. Modificar PF (atenuar la fe en el patrón de la barca, despertar una nueva PF de búsqueda profética). Inyectar memes nuevos (un meme experimental "el mar es boca de un dios" que se activa más barato cerca del mar). Archivar memes viejos (dejar dormido el meme "la pesca es solo oficio" que ya no representa al personaje post-hito). Abrir deudas morales (no le conté a mi mujer lo que vi). Instalar reapariciones narrativas (sueños recurrentes con palabras gatillo, flashbacks ante ciertos lugares).

Los hitos son raros. Un personaje promedio acumula entre cero y diez a lo largo de toda su vida de juego. Pero su impacto es desproporcionado: tres hitos bien escritos producen más densidad biográfica que cien memes. Cuando el LLM narra a un personaje y recibe en el contexto su listado de hitos, eso le da material biográfico denso de manera muy compacta.

## El cálculo de loadout

Esta es la operación más importante del motor cognitivo y la que más se ejecuta. Cada vez que un agente piensa o recibe input, el sistema calcula qué memes operativos están activos en ese momento. La función debe ser eficiente porque corre constantemente.

La fórmula combina cuatro factores para producir un score por cada MO candidato. El peso histórico del meme (peso_actual, que es el peso_base modulado por uso pasado y decaimiento). La afinidad semántica del meme con el input actual (distancia coseno entre el embedding del meme y el embedding del input). El bias circadiano según hora del día (los memes operativos pesan más a la mañana, los reflexivos pesan más a la noche). Los modificadores del lugar donde está el personaje (la abadía vuelve más caro activar memes violentos, la tribu vikinga los abarata).

```python
score = (peso_actual * 0.6 + similitud_semantica * 0.4) * bias_circadiano
costo_efectivo = costo_mana_base + suma_modificadores_lugar(meme.categorias, lugar)
```

Los memes se ordenan por score descendente y se van metiendo en el loadout activo hasta llenar el mana disponible. Los que no caben quedan dormidos para esa situación. El sistema registra qué memes se activaron y refuerza su peso histórico cuando el resultado del turno fue favorable.

Una decisión de tuning que vale la pena explicitar. Los pesos exactos del peso histórico versus la similitud semántica son provisionales. Lo que James va a tunear empíricamente. Si descubre que los personajes se sienten demasiado anclados en lo que ya conocen, sube el peso de la similitud semántica. Si se sienten demasiado reactivos al input inmediato, sube el peso del histórico. La regla práctica para tunear: el ratio 60-40 es punto de partida razonable, ajustar según se sienta el personaje en juego real.

## El sistema de decaimiento

Los memes operativos no son inmutables. Su peso cambia con el tiempo según uso. Esta es la pieza que produce evolución de los personajes a lo largo de meses de juego.

La fórmula es simple. Cada N días sin uso, el peso del meme se reduce. Cada activación exitosa lo refuerza. La función matemática es asintótica: el peso nunca cae a cero (los memes nunca se borran, siempre son recuperables si se reactivan), pero puede caer significativamente para memes que el personaje deja de usar.

```python
factor_decaimiento = max(0.05, 1.0 / (1.0 + 0.02 * dias_sin_uso))
factor_exito = min(2.0, 1.0 + (total_activaciones * 0.01))
peso_actual = peso_base * factor_decaimiento * factor_exito
```

Las PF no decaen. Esto es decisión arquitectónica deliberada. Si las PF decayeran como los MO, la identidad del personaje sería volátil. Las PF cambian solamente por crisis biográfica explícita, que requiere acumulación documentada de evidencia que las cuestione.

La aplicación del decaimiento corre como tarea programada, típicamente una vez por día del mundo (a las 6:00 del juego). Es operación barata, no requiere LLM, solo aritmética sobre los catálogos de memes de los agentes activos. Para el MVP donde hay pocos agentes activos, esto es trivial. Cuando el sistema escale a cientos de agentes principales, vale la pena considerar paralelizarlo o aplicarlo lazy (solo cuando un meme se va a usar, recalcular su peso).

## La inyección divina diferida

Una operación particular del memetario que merece su sección: cómo los dioses plantan memes en personajes para activarse después.

Un dios puede inyectar un meme experimental en el memetario de un personaje, con una particularidad: el meme tiene costo de mana extremadamente alto (típicamente 99) en condiciones normales, pero modificadores fuertísimos que lo abaratan en condiciones específicas. Por ejemplo, un meme "el mar es boca de un dios y vos estás en su lengua" inyectado por el Dios del Mar puede tener costo 99 default pero modificador -97 cuando el personaje está cerca del mar de noche.

En condiciones normales el meme nunca entra al loadout porque costaría 99 de mana, imposible. Pero cuando el personaje está cerca del mar de noche, el costo cae a 2 y el meme se activa como visión, profecía, sueño. El dios actúa diferido sobre el personaje sin necesidad de presencia activa. Es como un campo magnético que solo se hace sentir cuando hay un metal cerca.

Esta mecánica es elegante porque permite a los dioses ejercer influencia sin gastar esencia constantemente. Plantan la semilla una vez, la activación es ambiental. Cuando programes esto, asegurate de que el sistema de modificadores sea aditivo correctamente y que costos negativos no produzcan números absurdos. Un piso de costo (mínimo 1) y un techo (máximo 99) son protecciones útiles.

## Crisis biográficas y modificación de PF

Las PF cambian solamente bajo condiciones específicas. Esta operación es rara pero importante porque es donde los arcos de personaje grandes se manifiestan mecánicamente.

El proceso es el siguiente. El motor monitorea evidencia que cuestiona cada PF a lo largo del tiempo. Cuando un meme operativo derivado de un trauma se vuelve dominante por mucho tiempo (típicamente ocho semanas de juego con activaciones frecuentes y peso histórico alto), el sistema marca al personaje como candidato a crisis biográfica. La crisis se dispara en el siguiente Score climático.

En la crisis, el personaje tiene posibilidad de modificar una PF para incorporar el aprendizaje del trauma, o resistir el cambio y mantener su PF original. Si modifica, la PF se atenúa o se invierte en lugar de borrarse, y queda registrado el evento como hito biográfico mayor. Si resiste, se acumula deuda moral por seguir manteniendo una PF que la evidencia cuestiona.

La modificación de una PF nunca es operación silenciosa. Siempre se le narra al jugador como momento significativo de la vida del personaje. El LLM tier 3 narra la crisis y su resolución, porque es uno de los momentos más densos narrativamente del juego.

## Estratificación por profundidad

No todos los agentes del mundo tienen memetario completo. Esto es decisión arquitectónica importante porque permite escalar el mundo sin que el costo computacional explote.

Hay cuatro niveles de profundidad. El PJ del jugador tiene memetario completo: todas las capas, sistema completo de mana, registro detallado de activaciones, posibilidad de crisis biográfica. Los NPCs principales (entre cinco y quince en el MVP) tienen memetario completo simplificado: las tres capas pero con menos memes, sin SPECULUM, decisiones autónomas más rápidas. Los NPCs secundarios tienen memetario reducido: dos o tres PF, cuatro o cinco MOs, sin sistema de mana (todos activos con pesos), sin hitos. Los NPCs tibios (cientos en el mundo) no tienen memetario instanciado; solo tienen tags simbólicos que se infieren a memetario bajo demanda cuando se encienden por interacción.

Reglas de ascenso y descenso entre niveles. Un NPC tibio que interactúa significativamente con el PJ varias veces puede ascender a secundario. Un secundario que entra en Score importante puede ascender a principal. Un principal que sale del foco narrativo por mucho tiempo puede descender a secundario. Esta dinámica de ascenso permite que el mundo se desarrolle orgánicamente: los personajes que importan ganan profundidad, los que dejan de importar la pierden.

Cuando programes algo del memetario, asegurate de que la operación funcione para los cuatro niveles de profundidad. Una función de cálculo de loadout debe poder operar tanto sobre un PJ con memetario completo como sobre un NPC secundario con memetario simplificado. La interfaz debe ser uniforme aunque la profundidad de los datos varíe.

## El reuso de Fray Tomás

Una decisión central que conviene tener presente cuando programes este territorio: el motor cognitivo no se construye desde cero. Reusa el motor de Fray Tomás, otro proyecto de James que ya está corriendo en una Raspberry Pi 4. Específicamente, todo lo relativo a la estructura de datos del memetario, los embeddings con sentence-transformers all-MiniLM-L6-v2, el cálculo de loadout, el bias circadiano, el decaimiento, la evaluación de umbral de PF ya está implementado y probado en el código de Fray Tomás.

Antes de proponer reescritura de cualquier pieza cognitiva, conviene preguntarle a James si esa pieza ya existe en Fray Tomás. La respuesta probable es que sí, y entonces la tarea es adaptarla a múltiples agentes en lugar de uno solo, no programarla desde cero.

Lo nuevo que introduce Codex sobre Fray Tomás es la aplicación a múltiples agentes simultáneos con estratificación de profundidad, los memetarios simbólicos de los lugares con sus modificadores que afectan los costos de los agentes que los habitan, la inyección divina diferida de memes, los hitos biográficos como categoría distinta, y la integración con el motor de Blades para que los traumas alimenten el memetario.

## Recordatorios operativos

Cuando James trabaje en este territorio, cuatro cosas conviene tener presentes.

Primera, si te encontrás programando algo cognitivo aislado del resto del sistema, parate. El motor cognitivo se acopla constantemente con la propagación de información (los memes determinan cómo se mutan los rumores), con el motor de drama (los costos de los memes determinan posición y efecto en Scores, los traumas inyectan memes), con la cartografía (los memetarios simbólicos de los lugares modifican costos). Si lo programás aislado, la integración después es difícil.

Segunda, los números (mana máximo 20, costos 1 a 3, factores 0.6 y 0.4 en el score) son provisionales y vas a tunearlos viendo cómo se siente el sistema en juego. Documentá cada número como provisional con un comentario en el código para que en seis meses sepas qué tunear y qué no.

Tercera, cuando James reporte que un personaje "no se siente vivo" o "todos los personajes se sienten iguales", la primera hipótesis a investigar es si los memetarios están bien diferenciados. Si dos personajes tienen catálogos de memes muy similares con pesos similares, van a refractar parecido y el LLM va a producir narraciones parecidas. Memetarios fuertes y declarados, distintos entre personajes, producen voces distintas.

Cuarta, no tengas miedo de hacer personajes radicalmente distintos. La trampa del realismo cognitivo dice que los personajes deben pensar como humanos reales, lo cual lleva a memetarios moderados y matizados. Pero la buena ficción está llena de personajes nítidos, extremados. Aquiles es ridículamente sensible al honor. Hamlet duda más que ningún humano real. Memetarios fuertes producen mejor literatura que memetarios moderados.
