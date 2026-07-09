# Sistema de stress y trauma — la moneda del drama y su acoplamiento con el memetario

Este archivo es referencia operativa para cuando estés programando o diseñando el sistema de carga psíquica del personaje. Es el subsistema donde más fuerte se acopla el motor de drama con el motor cognitivo, y por eso requiere especial cuidado para no separar las dos cosas en silos. Asume que el SKILL.md principal del motor de Blades ya está cargado.

## Por qué este sistema es la diferencia entre Codex y Blades canónico

Vale la pena empezar con esto porque es donde Codex se separa más claramente de Blades, y entender la razón te ayuda a programar bien las decisiones que vienen.

En Blades canónico, el stress es una barra que se llena y los traumas son etiquetas predefinidas que el personaje acumula al desbordarse. La lista canónica incluye cold (frío emocional), haunted (acechado por algo del pasado), obsessed (fijado en algo), paranoid (siempre viendo amenazas), reckless (sin medir consecuencias), soft (perdió el filo violento), unstable (impredecible), vicious (cruel sin razón). Cuatro traumas y el personaje se retira del juego porque ya no es jugable como protagonista, queda como NPC dañado.

Esta mecánica funciona muy bien para Blades porque encaja con su estética (ladrones de Doskvol que se queman a sí mismos en el oficio) y con su loop de juego (los traumas son el costo del trabajo y eventualmente fuerzan al jugador a crear un nuevo personaje cuando el actual se rompe).

Para Codex, una estética distinta pide una mecánica distinta. Codex es novela interactiva donde el personaje no es un especialista que se quema, sino un cristal que se va modificando por lo que vive. Los traumas no son etiquetas que se acumulan hacia el retiro, son cicatrices cognitivas que cambian quién es el personaje a través del tiempo. La mecánica tiene que reflejar eso.

La adaptación de Codex es: cuando la barra de stress se llena, en lugar de aplicar una etiqueta predefinida, el sistema genera un meme experimental nuevo que se inyecta en el memetario del personaje, con contenido específico relacionado con la situación que llenó la barra. Ese meme empieza con peso bajo y costo de mana medio. Si las situaciones futuras lo activan repetidamente, gana peso histórico y eventualmente puede ascender a meme operativo permanente. Si se vuelve dominante en el comportamiento del personaje a lo largo de muchas sesiones, puede modificar una piedra fundacional, lo que constituye una crisis biográfica.

Esta es la pieza que vuelve emergente la construcción del personaje. El jugador no elige qué tipo de personaje quiere, el personaje se va construyendo solo a partir de las decisiones que tomó, los Scores que jugó, los traumas que acumuló, los memes que esos traumas dejaron en su piel. Después de cincuenta horas de juego, el personaje del jugador tiene una huella cognitiva única que ningún otro jugador podría replicar exactamente, porque emergió de su trayectoria específica de tiradas y consecuencias.

## La barra de estrés y sus reglas básicas

El personaje tiene una barra de estrés con una capacidad máxima (típicamente nueve segmentos, aunque podés tunear este número viendo cómo se comporta el sistema). La barra empieza vacía al inicio de cada arco narrativo grande y se va llenando a lo largo del juego.

Hay tres maneras principales de que el estrés suba. La primera es el empuje voluntario del jugador para modificar tiradas (descripto en references/tiradas.md): el jugador paga dos puntos de estrés para agregar un dado, mejorar posición o mejorar efecto. La segunda es la resistencia a consecuencias de mala tirada (también descripta en tiradas): el jugador paga una cantidad variable de estrés para atenuar, esquivar o transformar una consecuencia. La tercera es el estrés que se acumula directamente como consecuencia narrativa: situaciones particularmente angustiantes, traiciones, pérdidas, miedos enfrentados, pueden agregar puntos de estrés sin que el jugador haya pagado nada, porque la situación misma es lo suficientemente intensa.

Hay también maneras de bajar el estrés. La principal es visitar el vicio durante downtime (descripto en references/vicios-y-downtime.md). Otras maneras incluyen rituales específicos asociados a ciertos lugares o personajes (un sacerdote puede absolver, una madre puede consolar, una taberna puede emborrachar), o el simple paso del tiempo en estado de paz (un mes tranquilo descarga lentamente).

La barra es visible para el jugador siempre. No hay drama oculto en cuánto estrés tiene su personaje: el drama está en las decisiones que el jugador toma sabiendo cuán cerca está del desbordamiento. Cuando programes la UI, el indicador de estrés debe estar siempre a la vista, idealmente con representación visual (segmentos llenándose, no solo número).

## Qué pasa cuando la barra se llena

Cuando el estrés alcanza el máximo, el sistema entra en el flujo de generación de trauma. Este flujo es donde el motor de drama hace su llamada al LLM más interesante de toda la mecánica, y por eso vale la pena programarlo con cuidado.

El paso uno es congelar la situación que produjo el desbordamiento. El sistema captura contexto: qué Score se estaba jugando, qué acción intentó el personaje, qué consecuencia recibió, qué memes estaban activos en su loadout en ese momento, qué piedras fundacionales se cuestionaron, qué relaciones estaban en juego. Todo este contexto se serializa para el prompt.

El paso dos es la llamada al LLM tier 2 con el template de generación de trauma. El prompt le pide al LLM que proponga un meme experimental que represente la cicatriz cognitiva que esta situación dejó. El LLM debe devolver un meme estructurado con su contenido (frase corta tipo refrán o máxima), su categoría simbólica (qué tipo de cicatriz es: traición sufrida, miedo descubierto, certeza perdida, etcétera), una intensidad inicial baja (el meme arranca con peso bajo), y opcionalmente reapariciones narrativas (palabras gatillo que pueden activar flashback en futuras situaciones).

El paso tres es la validación del meme propuesto. Pydantic valida que la respuesta tenga el formato correcto. Pero además, el sistema debe verificar que el meme propuesto no duplica un meme que el personaje ya tiene activo. Si el LLM propone "no se puede confiar en sacerdotes" pero el personaje ya tiene ese meme operativo con peso alto, lo que tiene sentido es no inyectar uno nuevo sino reforzar el existente. Esta verificación se hace por similitud semántica: si el embedding del meme propuesto está cerca de uno existente, se trata como refuerzo, no como inyección.

El paso cuatro es la inyección del meme en el memetario del personaje. Se agrega al catálogo con estado experimental y origen marcado como "trauma". El sistema lo registra en el log de eventos del personaje.

El paso cinco es que la barra de estrés se vacía. El personaje sale del Score con la barra a cero y un trauma nuevo en su memetario. Al jugador se le narra esto explícitamente: el LLM produce una escena breve donde el personaje "absorbe" la cicatriz, donde el lector siente que algo cambió en él. No es un cambio de stats numéricos: es un cambio de quién es.

## La progresión de los traumas en el tiempo

Una vez inyectado, el meme experimental sigue las reglas normales de los MO: puede activarse en futuros Scores si su embedding es relevante al contexto, puede ganar peso histórico con cada activación exitosa, puede decaer si nunca se activa (aunque más lento que un MO normal porque arrancó con origen "trauma" que tiene resistencia al decaimiento).

Si el meme se activa varias veces y siempre ayuda al personaje (por ejemplo, le da posición controlada en situaciones donde antes habría tenido posición arriesgada), va ascendiendo. Después de un umbral de activaciones exitosas (provisional: cinco o seis) y un período mínimo de tiempo (provisional: cuatro semanas de juego), el meme experimental asciende automáticamente a meme operativo permanente. Sale del estado "trauma" y pasa a ser parte estable del catálogo del personaje.

Si el meme operativo derivado de trauma sigue siendo dominante por mucho tiempo más (provisional: ocho semanas adicionales) y se vuelve uno de los memes con mayor peso histórico del personaje, el sistema marca al personaje como candidato a crisis biográfica. La crisis se dispara cuando ocurra el próximo Score climático. En esa crisis, el personaje tiene la posibilidad de modificar una de sus piedras fundacionales para incorporar el aprendizaje del trauma, o resistir el cambio y mantener su PF original a costa de mayor estrés futuro cada vez que el meme operativo del trauma choque con la PF resistida.

Esta progresión no debe sentirse mecánica para el jugador. Cuando programes la UI, no muestres barras de progreso explícitas hacia "ascenso de meme" o "crisis biográfica". Esos son cambios cualitativos del personaje, no logros desbloqueables. El sistema los detecta y los aplica silenciosamente, y solo se le narra al jugador cuando suceden, como momentos significativos de la vida del personaje.

## La resistencia al estrés y el ritmo del juego

Una decisión de balance importante: cuán rápido debe llenarse la barra de estrés. Si se llena demasiado rápido, los traumas se acumulan sin que tengan tiempo de procesarse narrativamente, y el personaje se siente caótico. Si se llena demasiado lento, los traumas no aparecen lo suficiente como para producir progresión emergente, y el personaje se siente estático.

El equilibrio que conviene apuntar es aproximadamente un trauma cada cinco a diez Scores jugados. Esto significa que en una sesión de juego donde el jugador ejecuta dos o tres Scores, no debería desbordarse el stress. En cambio, a lo largo de cinco o seis sesiones, debería haber al menos un trauma generado.

Para conseguir este ritmo, los costos de empuje y resistencia deben estar tuneados de modo que el jugador pueda permitirse algunos pero no todos. Provisionalmente, dos puntos por empuje y entre uno y cinco por resistencia. La cantidad de descarga por vicio debe estar tuneada para que vacíe parcialmente la barra pero no completamente. Provisionalmente, una visita exitosa de vicio descarga entre cuatro y seis puntos.

Estos números son provisionales y vas a tunearlos. La regla de oro para el tuneo es: el jugador debe sentir que el estrés es un recurso significativo (cada empuje pesa), pero no debe sentirse atrapado (siempre debe haber salida posible). Si el jugador empieza a evitar empujes por miedo al trauma, los costos están altos. Si el jugador empuja sin pensar porque "siempre puedo descargar después", los costos están bajos.

## La reaparición de traumas como dispositivo narrativo

Una pieza específica del sistema que vale la pena programar bien: las reapariciones narrativas asociadas a los traumas inyectados. Cada meme con origen "trauma" tiene en su definición un campo de reapariciones, que son condiciones bajo las cuales el trauma vuelve a manifestarse activamente en la narración aunque el meme no esté en el loadout activo.

Las reapariciones más útiles son tres tipos. Las palabras gatillo: ciertas palabras o conceptos en el contexto narrativo activan automáticamente la reaparición (el personaje que tuvo trauma con un kraken puede tener "tinta", "profundidad", "ojos antiguos" como palabras gatillo). Los lugares gatillo: estar en cierto tipo de lugar reactiva el trauma (mar de noche, tabernas con olor a aceite, cualquier lugar similar al original del trauma). Los sueños recurrentes: con cierta probabilidad por noche, el personaje sueña con la situación del trauma, y eso se narra como escena.

Cuando se dispara una reaparición, no se modifica el loadout activo: el meme entra en una activación de un solo turno con efecto narrativo. El LLM recibe el contexto del trauma original y narra la reaparición como flashback, sueño, o resurgimiento momentáneo. Después de narrar la reaparición, el sistema agrega un punto de estrés al personaje porque las reapariciones cargan psíquicamente.

Las reapariciones son una de las partes más bonitas del sistema porque producen continuidad emocional en el personaje a lo largo de meses de juego. El jugador puede no acordarse de un trauma viejo, pero el sistema sí, y lo trae de vuelta cuando las condiciones se alinean. Es lo que hace que el personaje se sienta habitado por su propia historia.

## Recordatorios operativos

Cuando programes este sistema, dos cosas vale la pena tener siempre presentes.

Primera: no programes el sistema de stress y trauma sin acceso al sistema de memetario. Son dos sistemas que se hablan constantemente. Si los programás aislados como módulos separados con interfaz limpia entre ellos, vas a tener fricción permanente. Mejor programarlos en conversación: stress y trauma viven en el mismo módulo de Python, comparten estructuras de datos, pueden modificarse mutuamente. La separación es conceptual (en este archivo de referencia), no necesariamente arquitectónica en el código.

Segunda: cuando un jugador reporte que "el sistema de stress se siente arbitrario" o "los traumas no parecen tener sentido", el problema casi siempre está en la calidad del prompt de generación de trauma, no en la mecánica de stress. Revisá los templates antes de revisar los umbrales numéricos. Un trauma bien generado se siente como cicatriz. Un trauma mal generado se siente como debuff aleatorio. La diferencia la hace el LLM teniendo el contexto correcto.
