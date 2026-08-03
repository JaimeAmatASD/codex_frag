# Sistema de vicios y downtime — la fase entre Scores

Este archivo es referencia operativa para cuando estés programando o diseñando el funcionamiento del personaje entre acciones focales: cómo descarga estrés visitando su vicio, qué actividades realiza durante períodos de calma, cómo el sistema simula el paso del tiempo de forma lazy. Los dos temas (vicios y downtime) viven juntos en este archivo porque están funcionalmente acoplados: los vicios son la actividad central del downtime, y separar la información en dos archivos forzaría saltar entre ellos constantemente. Asume que el SKILL.md principal del motor de Blades ya está cargado.

## La función dramática del downtime

Antes de entrar en mecánicas concretas, vale la pena entender por qué el downtime existe como fase distinta y qué función dramática cumple en el ritmo del juego.

Una sesión de Codex que fuera puramente acción focal sería agotadora y plana. El drama necesita contraste. Si todos los momentos son tensos, ningún momento se siente tenso. Si el personaje siempre está actuando, nunca tiene espacio para procesar lo que actuó. La fase de downtime existe para producir ese contraste: es el espacio donde la tensión se asienta, donde las consecuencias de los Scores anteriores se hacen sentir, donde el personaje se prepara para los Scores próximos.

Hay otra función igual de importante. El downtime es donde el mundo cambia mientras el personaje no actúa. Los rumores se propagan, los clocks avanzan, los NPCs viven sus vidas, los dioses meditan sus intervenciones. Sin esta fase, el mundo se sentiría congelado entre acciones del jugador, lo que rompería la promesa del proyecto de "el mundo continúa cuando dejás de mirar".

Y hay una tercera función que es la más práctica de todas: el downtime es donde el sistema gasta menos LLM. Toda la propagación pasiva, la avance de clocks por reglas deterministas, la simulación lazy de eventos del mundo, suceden con cálculos baratos. Solo cuando algo narrativamente caliente sucede (un clock se completa, un dios decide actuar, un personaje cercano muere) se invoca al LLM para narrar. Esto vuelve económicamente viable que el jugador pueda saltar semanas o meses sin que cada decisión consulte al modelo.

Cuando programes el sistema de downtime, tené presente que estas tres funciones están conviviendo. Una decisión de diseño que mejore la economía de LLM puede empeorar la sensación dramática, o viceversa. El equilibrio se logra distinguiendo qué eventos merecen narración rica (los calientes) y qué eventos pueden simularse silenciosamente (la mayoría).

## Downtime corto versus downtime largo

Conviene distinguir dos tipos de downtime que tienen mecánicas ligeramente distintas. El downtime corto sucede entre dos Scores de la misma sesión de juego, típicamente representa horas o un día del mundo. El downtime largo sucede cuando el jugador decide hacer un time-jump grande, saltando semanas o meses.

El downtime corto es más simple. El jugador declara una o dos actividades concretas (visitar el vicio, hablar con un NPC específico, descansar en su casa) y el sistema resuelve cada una con una llamada al LLM o un cálculo de reglas según corresponda. Los clocks pueden avanzar uno o dos segmentos según los triggers que se cumplan. La narración es focalizada en el personaje.

El downtime largo es donde la simulación lazy se vuelve crítica. El jugador da una instrucción general ("vivo como pescador, sigo mi rutina, paso un mes") y el sistema tiene que hacer dos cosas en paralelo. Por un lado, generar una crónica del personaje durante ese mes (qué hizo en general, a quién vio, qué oyó, qué actividades de su vicio realizó). Por el otro, avanzar el mundo entero treinta ticks, lo que implica propagar rumores, avanzar clocks pasivos, simular eventos por reglas, y solamente narrar con LLM aquellos eventos que cumplen criterio de "narrativamente caliente para este personaje".

Cuando el time-jump termina y el jugador retoma el control, el sistema le devuelve un resumen narrado que combina la crónica del personaje con los eventos relevantes que llegaron a él durante ese tiempo. Crucialmente, el resumen está filtrado por el grafo de conocimiento del personaje (solo se entera de cosas que efectivamente le llegaron como información) y refractado por su memetario (los hechos se interpretan desde su cristal). El resumen es donde la promesa del proyecto se manifiesta más claramente: el jugador siente que algo pasó mientras no miraba, y siente que su personaje vivió ese tiempo.

## Los vicios como sistema dual

Los vicios son simultáneamente una mecánica de descarga de estrés y un vector de propagación de información. Esta dualidad es el aspecto más elegante del diseño y vale la pena entenderla bien antes de programarla, porque mal entendida produce dos sistemas separados en lugar de uno integrado.

La dimensión de descarga funciona así. El personaje tiene un vicio principal (y opcionalmente un vicio secundario que descarga la mitad). Cada vicio está asociado a un tipo de lugar específico del mundo: la bebida con la taberna, el juego con la casa de apuestas, la fe extrema con el templo, la lujuria con el burdel, la contemplación con el claustro o la cala solitaria, el opio con el fumadero, la violencia con el callejón. La asociación entre vicio y lugar no es arbitraria: es la materialización geográfica del vicio.

Cuando el personaje visita su lugar de vicio durante downtime, se hace una tirada de dados igual que en un Score pero con una mecánica de resolución distinta. El jugador tira una cantidad de dados igual a algún atributo relevante (típicamente dos dados base más modificadores), mira el resultado más alto, y el sistema interpreta así. Si saca alto, descarga mucho estrés (el vicio fue exitoso, el personaje vuelve fresco). Si saca bajo, descarga poco (el vicio no funcionó del todo, el personaje sigue cargado). Si saca exactamente la cantidad de estrés que tenía, descarga perfecto. Si saca por encima de lo que tenía, sobreindulge: descarga todo el estrés pero pasa algo malo (pierde tiempo, queda en peor posición, gasta dinero, daña una relación, deja una huella).

La sobreindulgencia es el momento mecánicamente más interesante porque produce drama por el éxito. El personaje quería descargar y descargó, pero el descontrol lo llevó más allá de lo necesario. Esta es la mecánica que evita que el vicio sea simplemente "botón de cura": tiene su propio costo cuando se usa demasiado.

La dimensión de información funciona en paralelo y es la pieza más distintiva. Cada visita al vicio, además de descargar estrés, genera un evento de mundo apropiado al lugar. En la taberna se oyen rumores: el sistema selecciona uno o dos hechos del mundo cuya versión esté circulando en esa celda y se los presenta al personaje. En la casa de juego se cruzan apuestas que arrastran información: el personaje conoce a otros jugadores y puede oír cosas. En el burdel se escucha un secreto: alguien le confidencia algo a la persona que pagó por su tiempo. En el templo se conoce un fanático: aparece un NPC con piedras fundacionales fuertes que puede convertirse en aliado o adversario. En el fumadero se tienen visiones: memes inyectados por dioses se activan más barato bajo el opio, lo que puede producir flashforwards proféticos o reapariciones de traumas dormidos.

Esta dimensión de información es el motor que evita que la simulación se sienta separada de la experiencia del jugador. Sin los vicios como vector, los rumores podrían propagarse en el grafo sin que el personaje del jugador los reciba nunca, y el sistema se sentiría hermético. Con los vicios, el sistema empuja mecánicamente al jugador a hacer la cosa que más alimenta el flujo narrativo: visitar lugares de información disfrazados de necesidad psíquica.

Cuando programes el sistema de vicios, asegurate de no separar las dos dimensiones en módulos diferentes. La descarga de estrés y la generación de eventos de información son la misma operación: una visita al vicio. Si las separás arquitectónicamente, podés terminar con un caso donde el sistema descarga estrés sin generar info, o donde genera info sin que el jugador lo experimente como vicio. Tienen que estar pegadas en el código.

## Cómo se eligen los rumores que el vicio entrega

Una decisión de diseño que vale la pena cerrar antes de programar: cuando el personaje visita su vicio y el sistema debe entregarle información, ¿cómo se elige qué información específicamente?

Hay tres criterios que combinar. Primero, la celda donde está el vicio debe tener rumores activos en su grafo local. El sistema consulta qué versiones de qué hechos están circulando en esa celda y filtra solo las que el personaje todavía no conoce (no tiene sentido entregar un rumor que el personaje ya sabe). Segundo, entre los candidatos disponibles, se prefieren los rumores cuyo contenido tiene afinidad semántica con los memes activos en el loadout del personaje en ese momento. Esto produce un efecto sutil: el personaje "oye" más nítidamente lo que su cristal estaba dispuesto a oír. Un personaje con loadout activo de memes religiosos en la taberna probablemente reciba el rumor de la herejía en lugar del rumor de la cosecha. Tercero, hay un componente aleatorio para evitar que el sistema sea predecible: aunque haya un rumor con afinidad alta, hay chance de que se le entregue otro distinto.

El cálculo concreto puede ser una distribución de probabilidades sobre los rumores candidatos, donde la probabilidad de cada uno es proporcional a la afinidad semántica más un piso de aleatoriedad. La cantidad de rumores entregados por visita es típicamente uno o dos, no más, para no saturar al jugador.

Una vez seleccionado el rumor, se aplica una mutación adicional al pasarlo al personaje (porque viene a través del filtro del vicio, no de un encuentro directo con quien sabe). Esto significa que hasta los rumores que llegan por taberna se mutan ligeramente al pasar por la atmósfera de la taberna y la disposición del personaje para oírlos en ese contexto. Pequeñas mutaciones acumuladas son lo que vuelve viva a la red de información.

## Las actividades de downtime más allá del vicio

El vicio no es la única actividad posible durante downtime, aunque es la más mecánicamente codificada. El jugador puede declarar otras actividades que se resuelven con sus propias mecánicas.

Reducir heat es una actividad donde el personaje intenta hacerse menos visible para alguien que lo está buscando o sospechando. Mecánicamente, hace tirada para reducir uno o más segmentos de un clock de "te están buscando" o equivalente. La narración es el personaje cubriendo huellas, mintiendo sobre dónde estuvo, evitando los lugares donde podrían reconocerlo.

Trabajar en proyecto largo es actividad donde el personaje avanza algo que tiene su propio clock. Construir una barca, escribir cartas a un mentor lejano, cultivar un huerto, traducir un libro prohibido. La actividad avanza segmentos del clock del proyecto, que cuando se completa produce un evento narrativo grande (la barca está lista, el mentor responde, la cosecha llega, el libro está traducido).

Investigar algo concreto es actividad donde el personaje intenta saber más sobre un hecho específico que ya conoce parcialmente. Hace tirada para acceder a información, y si tiene éxito, el grafo de conocimiento del personaje se actualiza con una versión más cercana a la raíz del hecho (menos mutada). Mala consecuencia puede significar que su investigación llamó la atención de alguien que no quería ser investigado.

Hacer indulgencia adicional es actividad donde el personaje gasta dinero o recurso para descargar más estrés que lo que el vicio normal le daría. Es esencialmente una versión cara y arriesgada de visitar el vicio, con más chance de sobreindulgencia.

Cada una de estas actividades cuesta tiempo del downtime. En un downtime corto típicamente caben una o dos actividades, en un downtime largo pueden caber cuatro o cinco. La economía exacta es algo a tunear viendo cómo se siente el ritmo, pero la regla general es que el jugador no debería poder hacer todas las actividades que quiere en cada downtime: tiene que elegir, y esa elección es donde está el drama de gestión del personaje.

## La simulación lazy del mundo durante downtime

Esta es la parte computacionalmente más densa del sistema y vale la pena entenderla bien para programarla eficientemente.

Cuando el jugador declara un time-jump (digamos, treinta días), el sistema no puede simular cada agente y cada celda en cada uno de los treinta días. Eso sería computacionalmente prohibitivo y económicamente inviable en términos de costo de LLM. La simulación lazy es la solución.

El principio es: simular solo lo que tiene chance de afectar al personaje del jugador, y simular el resto solo cuando el personaje se acerque a ello. Para implementar esto, el sistema clasifica las celdas y agentes según su distancia (geográfica y narrativa) al personaje del jugador.

Las celdas y agentes cercanos (mismo pueblo, NPCs con relación significativa) se simulan con detalle moderado. Cada tick del downtime, los rumores se propagan localmente, los clocks que afectan a estos agentes avanzan, los eventos de relación se evalúan. Si algo significativo pasa (un NPC cercano muere, un clock se completa), se invoca al LLM para narrar.

Las celdas y agentes intermedios (mismo reino, NPCs con relación lejana) se simulan estadísticamente. No se modela cada acción de cada NPC, sino que se calculan probabilidades agregadas: en treinta días, ¿se propagó el rumor del kraken a la siguiente provincia? Tirada simple. ¿Murió alguien importante? Probabilidad por edad y condición. ¿Cambió el dios principal del reino? Solo si los clocks divinos relevantes se completaron.

Las celdas y agentes lejanos (otros reinos, civilizaciones distantes) no se simulan en absoluto durante downtime corto o medio. Solo se actualiza su estado cuando el jugador finalmente se acerca a ellos, momento en que el sistema "recupera el tiempo perdido" simulando rápidamente lo que debió haber pasado en esa zona durante todo el tiempo que el jugador no estuvo cerca.

Esta es la pieza arquitectónica más sutil del proyecto y conviene programarla con tests cuidadosos. Si la simulación lejana no se "recupera" correctamente cuando el jugador llega, el mundo se siente quieto. Si la simulación cercana es demasiado activa, el costo computacional explota. El equilibrio es delicado y vale la pena tunearlo iterativamente.

## El resumen narrado al final del time-jump

Cuando el downtime largo termina, el sistema debe entregar al jugador un resumen narrado de lo que vivió su personaje y de lo que pasó alrededor. Este resumen es la pieza de UX más importante del sistema de downtime y conviene programarla con cuidado.

El resumen tiene tres componentes que el LLM tiene que tejer en una sola narración coherente. La crónica del personaje: qué hizo durante ese tiempo según las instrucciones que dio el jugador, salpicada de detalles emergentes que el sistema le agrega (un día de tormenta, un encuentro casual, un sueño recurrente que reapareció). Los eventos del mundo que llegaron al personaje: rumores que oyó, noticias que leyó, gente que pasó por su pueblo. Las consecuencias diferidas de Scores anteriores: si en un Score anterior el personaje dejó una huella, durante el downtime esa huella puede haberse manifestado.

La regla crítica es que el resumen está filtrado por el grafo de conocimiento del personaje. Si durante el downtime murió alguien importante en otra provincia, pero la noticia no llegó al pueblo del personaje, el resumen no lo menciona. El personaje genuinamente no se enteró. Esto puede crear momentos narrativos potentes: el jugador recibe el resumen, parece que pasó un mes tranquilo, y luego varias sesiones después se entera de algo grande que pasó durante ese tiempo y que su personaje desconocía. Esa demora informacional es exactamente la promesa del proyecto.

El LLM que genera este resumen debe ser tier 2 (modelo bueno, no básico), porque la calidad de este texto es lo que el jugador más recuerda al volver a jugar. Un resumen bien escrito hace que el jugador sienta que pasó tiempo. Un resumen mecánico se siente como un changelog.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera: no programes el sistema de vicios separado del sistema de información. La integración es la pieza más distintiva del diseño y separar las dos cosas la rompe. Cuando el personaje visita un vicio, en una sola operación se descarga estrés, se obtienen rumores, se avanza un clock, se mutan algunas versiones del grafo. Todo eso pasa junto.

Segunda: la simulación lazy se siente fácil cuando funciona y horrible cuando falla. Los bugs en este territorio son sutiles porque el jugador no ve el mundo lejano simulado, solo ve sus consecuencias cuando se acerca. Si algo está mal en cómo se "recupera" el tiempo lejano, el jugador llega a un lugar donde nada cambió en seis meses y eso destruye la inmersión. Vale la pena programar tests específicos que verifiquen que cuando el jugador llega a una zona después de un time-jump, el estado de esa zona refleja lo que debería haber pasado.

Tercera: la economía del downtime está calibrada para que cada elección del jugador pese. Si el jugador siente que puede hacer todas las actividades que quiere en cada downtime, los costos están bajos. Si siente que nunca llega a hacer lo que necesita, los costos están altos. El punto correcto es donde el jugador siempre tiene que decidir qué dejar para el próximo downtime, lo que produce drama de gestión del tiempo del personaje.
