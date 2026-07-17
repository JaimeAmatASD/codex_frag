# Análisis del brainstorming — julio 2026
## Qué ya existe, qué adoptar, qué investigar, qué es humo
*Análisis de arquitecto sobre ideas_cod_frag.odt (tres conversaciones: crítica narrativa/UX de Copilot, manifiesto de dioses y ecosistema, motor de identidad). Conceptos repetidos unificados. Cruzado contra el código real del repo y los ADRs.*

---

## El veredicto en una frase

La mayor parte del brainstorming no propone cosas nuevas: REDESCUBRE el proyecto por caminos independientes, lo cual es la mejor validación posible del diseño. De lo genuinamente nuevo, hay cinco ideas de oro implementables pronto, una hipótesis de investigación excelente, un bloque entero (los dioses) que es diseño futuro valioso a consolidar sin construir, y tres cosas que son humo o van contra el núcleo del proyecto y conviene descartar con nombre y apellido.

---

## Parte 1 — Lo que el brainstorming redescubrió (ya existe, construido o diseñado)

Unifico acá todo lo que las tres conversaciones proponen y que ya es realidad del proyecto, porque reconocerlo evita el peligro de refundar lo fundado.

**El sistema de secretos que se deforman con la distancia, el tiempo y el intérprete** (manifiesto, ideas 8 y sección 1 de "Crónicas") es el paso 2, construido y validado: grafo de hechos y versiones, prisma del receptor, distancia a la raíz. El ejemplo del monje racionalista que convierte el kraken en terremoto es literalmente lo que el template de mutación ya hace. La "localidad del conocimiento" (el secreto muere con su portador) es el ADR-004 y el lema del proyecto.

**"El motor decide, el LLM narra"** (secciones 8 y 9 de la charla de identidad, repetidas dos veces) es el ADR-001 palabra por palabra. Que otra IA, sin conocer los ADRs, haya concluido que "esto reduce muchísimo la arbitrariedad del modelo" es validación independiente de la decisión fundacional.

**Las Piedras Fundacionales como otra clase de objeto, no memes pesados** (sección 10 de identidad): ya es así en el diseño y el código (tipo propio, no decaen, protegidas por el sistema de fricción biográfica que exige aprobación para tocarlas). Lo que la charla agrega y vale la pena adoptar es la METÁFORA: "leyes de conservación del personaje", como en física. Es la mejor formulación que ha tenido el concepto y merece entrar a la documentación y a los skills tal cual.

**Las capas de estabilidad con velocidades distintas de cambio** (acciones, hábitos, memes, relaciones, historia, piedras): ya existe implícito. Las PF no decaen, los operativos decaen lento, los experimentales rápido; los hábitos son los clusters de co-activación (diseñados, heredados de Fray Tomás); relaciones e historia viven en el grafo y los hitos. La charla no inventa la estructura: la nombra bien. Adoptar el nombre "capas de estabilidad" como vocabulario.

**El iterador temporal y el time skip narrativo** (secciones 11 y 12): es el time-jump del diseño original, categorizado en la Fase 0 como diferido. Los clocks ya construidos son su primera pieza.

**La malla narrativa donde cada celda tiene prompts, secretos, clocks y atmósfera, y los lugares como entidades con memoria y personalidad** (secciones 15 y 16): es exactamente el skill de cartografía ya diseñado (grilla jerárquica más memetario de lugares). "Un bosque que cambia a quienes viven allí" es la coproducción agente-mundo, decidida hace meses. Post-MVP como estaba.

**Toda la sección de Blades** (17): construida en el paso 3 (clocks, posición y efecto, éxito parcial, stress) o prevista en el skill (trauma que se vuelve meme, vicios como nodos de información, downtime).

**El mapa abstracto que sirve a la narrativa y no al wargame** (manifiesto, 10), **la perspectiva única del jugador** (Crónicas, 4), **el mundo que sigue sin que lo miren** (manifiesto, 2), **el cambio de perspectiva tras la muerte** (manifiesto, 18), y **"no hay victoria absoluta, sino historias memorables"** (manifiesto, 12): todo es diseño original del proyecto, Fase 0 incluida.

**Sobre el "cambio de paradigma" a motor de identidad** (conclusión de la charla y del documento entero): mi lectura de arquitecto es que NO es un pivote, es el redescubrimiento del núcleo irrenunciable de la Fase 0. "¿Qué hace que Juan siga siendo Juan tras cuarenta años?" es la identidad narrativa de Ricoeur que ya está en el diseño del SPECULUM; el alma (memetario, autoobservación, plasticidad) siempre fue el centro, y "las dos líneas se necesitan mutuamente" (mundo y persona) es la arquitectura actual descrita desde afuera. No hay nada que refundar. Hay UNA consecuencia práctica real: esta convergencia sube la prioridad del SPECULUM, la deuda de diseño nombrada del núcleo, por encima de expansiones de mundo como la cartografía. Cuando toque elegir el próximo frente grande, la autoobservación va primero.

---

## Parte 2 — Las ideas nuevas de oro (implementables, adoptar pronto)

Estas cinco son aportes genuinos del brainstorming, baratas sobre lo ya construido y de alto retorno. En orden de recomendación.

**1. Incompatibilidades entre memes y el conflicto interno emergente** (identidad, secciones 7 y B; el ejemplo repetido tres veces en el documento: "nunca abandones a tu familia" contra "el deber está por encima de todo"). Hoy el modelo ya tiene conexiones entre memes, pero sin signo: no distingue refuerzo de tensión. Agregar tipo a la arista (refuerza / tensiona) es un cambio chico de modelo, y sobre él un detector barato en el loadout: cuando dos memes incompatibles de peso similar entran juntos al cristal, el sistema lo reporta como tensión interna, y esa tensión entra al prompt (de mutación o de narración) como material dramático explícito. El drama no se escribe: emerge de la contradicción, que es exactamente lo que la crítica de Copilot pedía ("la ficción buena vive de tensión, no solo de coherencia; el personaje memorable deja ver una grieta"). Las dos conversaciones convergen acá y las unifico en una sola mejora. Implementable ya, en el ciclo actual del Taller.

**2. El constructor de seres por descripción natural** (identidad, 18: "es un veterinario de 62 años, ayuda a cualquiera, nunca perdonó a su hijo, tiene miedo a quedarse solo" y la IA propone memes, piedras, contradicciones y hoja). Esto ES el flujo del jardinero de la Fase 0 aplicado a seres, el requisito de primera clase que estaba registrado sin diseño. Y tiene hogar natural: una zona del Taller donde escribís (o dictás, ya que el dictado existe) la descripción, el LLM propone el ser.json completo, y vos editás y aprobás antes de guardar. El LLM propone, el motor dispone, el autor cura: mismo patrón que la transmisión. Es además el ataque directo al cuello de botella real del proyecto ahora, que es la fricción de crear seres a mano. Recomendación fuerte: próxima mejora del Taller.

**3. La esencia operativa como guía autoral** (Copilot: deseo, miedo, sesgo, tabú, forma de mentir; qué no puede admitir, qué mentira se cuenta, qué interpreta siempre mal). No es mecánica nueva: es una plantilla de calidad para escribir seres. Se implementa como el esqueleto del prompt del constructor anterior: un ser bien formado sale con al menos un meme de deseo, uno de miedo o tabú, un sesgo perceptivo, y una forma característica de mentir o callar. Costo casi nulo, retorno directo en voz y en drama. Unifico las dos listas (la de Copilot y la de "qué quiere, qué teme, qué no puede admitir") en una sola guía.

**4. La clasificación funcional de memes** (identidad, 6: perceptivos, estratégicos, morales, identitarios, emocionales). Importante unificación de criterio: NO reemplaza al tipo actual (fundacional, operativo, experimental), que mide estabilidad; es una dimensión ortogonal que mide función. Se adopta como campo opcional nuevo (funcion), y su valor inmediato es en los prompts: el template puede decirle al modelo qué clase de lente es cada meme activo ("esto tiñe cómo interpreta", "esto tiñe qué haría", "esto tiñe qué siente"), afinando la refracción. Barato; adoptar cuando se toque el modelo por la mejora 1.

**5. Las Singularidades Narrativas** (identidad, 13: eventos inevitables que determinan el contexto, no el resultado; "no importa quién llegue: algo importante ocurre allí"). Idea nueva, buena, y casi gratis sobre lo construido: es un hecho futuro agendado en el reloj del mundo, opcionalmente con clock propio, que ocurre esté quien esté cuando el reloj llega. Le da al mundo el "destino" que la crítica de Copilot echaba en falta, sin quitarle libertad a nadie: el evento es fijo, las historias que produce dependen de quiénes estén. Recomendación: el mundo de la taberna del paso 5 debería tener exactamente UNA (el kraken llega la noche señalada, pase lo que pase antes).

**Mención sobre UX** (Copilot: menos jerga de motor, consecuencias narrativas visibles, "quién cambió, qué rumor se deformó, qué vínculo se tensó"). Unificación de criterio necesaria: hay dos caras y la crítica aplica distinto a cada una. El Taller es herramienta de AUTOR, y para vos la jerga (loadout, pesos, distancias) es información, no ruido: ahí la mejora es incremental (la bitácora ya registra; una vista de "qué cambió desde ayer" en términos de seres y rumores sería el siguiente paso natural, no urgente). La cara de JUGADOR (paso 5) es donde la regla de Copilot manda entera: cero jerga, todo diegético, el jugador ve hambre, miedo y sospecha, nunca embeddings. Registrado como principio del paso 5.

---

## Parte 3 — La hipótesis de investigación (excelente, no escribir código todavía)

**El mecanismo de aprendizaje propio de cada meme** (identidad, sección final y 20.A): no todos los memes cambian igual; algunos se refuerzan con evidencia, otros se radicalizan al ser contradichos (como las creencias conspirativas), otros solo cambian por trauma. El propio documento lo dice con lucidez: hipótesis de investigación, no especificación. Coincido y agrego el cómo: es un campo aprendizaje con tres o cuatro políticas discretas (normal, se_radicaliza, solo_trauma, se_erosiona) que modifican la función de refuerzo y decaimiento existente. El experimento que lo valida antes de adoptarlo: un mismo ser en el Taller, mismo bombardeo de noticias contradictorias, con y sin política de radicalización, y leer si la diferencia de trayectoria se NOTA en cómo recuenta después. Si no se nota jugando, es complejidad sin retorno y se descarta con evidencia. Es, dicho técnicamente, la física fina de la plasticidad, o sea del núcleo irrenunciable: por eso merece el experimento y también por eso no merece código especulativo.

---

## Parte 4 — El bloque de los dioses: diseño futuro valioso, consolidar sin construir

El manifiesto entero de dioses y ecosistema (capas de existencia, dioses caprichosos a la griega, gasto de esencia y favor, omnipresencia contra omnipotencia como trade-off de diseño, conflicto divino solo indirecto a través de campeones, cultos, milagros y rumores, templos como nodos de poder, ascensión de mortales, el dios que quiere volverse mortal, muerte divina por olvido, muerte funcional con corrupción de la realidad, la nigromancia de información, el Pulso de tres fases) es material de diseño RICO y coherente con el proyecto: los dioses con deliberación de Consejo e inyección diferida estaban en el diseño original, y la Fase 0 los categorizó como prescindibles del MVP. Nada de esto es humo conceptual. El peligro es de alcance: es un juego entero montado sobre el engine, y construir cualquier parte ahora violaría la regla del jugable mínimo.

Veredicto: consolidarlo como documento de diseño futuro (este análisis cumple esa función por ahora; si el material crece, merece docs propio) y robarle desde ya dos imágenes que son demasiado buenas para esperar sin registro. La muerte funcional de un dios que corrompe lo que sostenía ("si muere el dios del fuego, las llamas queman en frío y no dan luz") es de las ideas más potentes del documento y define cómo deberían diseñarse los dioses cuando toque: no como personajes poderosos sino como pilares de la física del mundo. Y la nigromancia de información (recuperar el secreto de un muerto: carísima, ritual, cuerpo íntegro, dato fragmentario) es la excepción perfecta que confirma el lema del proyecto, porque hasta la resurrección de la verdad devuelve una verdad rota.

---

## Parte 5 — El humo y lo que va contra el núcleo (descartar con nombre)

**El multijugador implícito.** El manifiesto desliza varias veces "un jugador puede ser un pescador, otro un campeón, otro un noble, otro un dios". Unificación de criterio necesaria: el proyecto tiene múltiples PERSPECTIVAS habitables (diseño original: el jugador cambia de personaje, incluso al morir), no múltiples JUGADORES simultáneos. El multijugador multiplica todo (sincronización, servidores, diseño social, moderación) y la Fase 0 definió ficción solitaria con la escala como problema futuro no-técnico. Si algún día se quisiera, la arquitectura de mundos portables no lo impide; hoy y para el MVP entero, es humo. Descartado explícitamente para que ninguna conversación futura lo cuele como supuesto.

**Los tags permanentes y la "memoria fija sin puntos de guardado"** (Crónicas, 2: "si un personaje adquiere el tag Traicionado, su filtro se vuelve cínico para siempre"). Esto va CONTRA el núcleo: la plasticidad es irrenunciable, y un tag eterno es una estatua parcial. Lo que el proyecto ya tiene es mejor y cubre la intención: la traición se inyecta como meme de peso alto y persistencia alta (quizás con política solo_trauma cuando exista), y queda como HITO biográfico, la cicatriz que no se borra. El pasado es permanente en los hitos; el carácter, nunca. Se descarta la formulación, se conserva la intención por las vías existentes.

**El juez de actuación** (manifiesto, 9 y Crónicas, 4: bonificar la buena interpretación con Favor). Riesgo de diseño: el sistema no puede juzgar "buena actuación" sin delegar arbitrariedad al LLM, contra el ADR-001. El matiz rescatable ya existe orgánicamente: la descripción detallada y en personaje mejora la afinidad semántica entre lo declarado y los memes del ser, lo que ya mejora posición y efecto sin ningún juez. La especificidad se premia sola por la mecánica. Descartar el bono explícito, documentar que el incentivo ya es emergente.

**Las repeticiones.** El documento repite tres veces el ejemplo de "la autoridad siempre miente" contra "la magia existe", dos veces las capas de estabilidad, dos veces el flujo de resolución, y contiene dos resúmenes de la misma charla. Sin drama: es la naturaleza del brainstorming pegado de varias fuentes. Este análisis las unificó; el ejemplo de la autoridad y la magia, dicho sea de paso, es muy bueno y merece volverse el ejemplo canónico de la documentación del memetario cuando se actualice ese skill.

**Un matiz técnico sobre "cada meme propone una acción y el motor obtiene la decisión"** (identidad, 8). Es MÁS determinista que lo construido: hoy el motor selecciona el cristal y el LLM narra comprensión o resultado; nadie calcula decisiones de acción de los NPCs porque los NPCs todavía no actúan solos. La idea no es humo: es el germen del futuro motor de decisión autónoma de NPCs (el tick del mundo), y está bien anotada para entonces. Pero conviene no confundirla con una corrección de lo actual: lo actual es correcto para lo que existe.

---

## Plan de adopción, en orden

Ahora, dentro del ciclo del Taller: las aristas con signo y el detector de tensión interna (mejora 1), con la clasificación funcional de memes de paso (mejora 4), porque tocan el mismo modelo. Después, el constructor de seres por descripción en el Taller (mejora 2) con la esencia operativa como esqueleto de su prompt (mejora 3): es la mejora de mayor palanca autoral. En el diseño del mundo del paso 5: una Singularidad Narrativa (mejora 5) y el principio de cero jerga en la cara del jugador. Como experimento cuando haya juego sostenido: los mecanismos de aprendizaje por meme (parte 3), con el protocolo descrito. Consolidado sin construir: todo el bloque de dioses (parte 4). Descartado con registro: multijugador simultáneo, tags permanentes, juez de actuación (parte 5). Y una re-priorización de fondo que el brainstorming justifica: el SPECULUM antes que la cartografía cuando toque el próximo frente grande, porque si Codex es un motor de identidad, la autoobservación es su órgano pendiente.
