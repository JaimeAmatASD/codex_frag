# Sistema de tiradas — resolución de acciones

Este archivo es referencia operativa para cuando estés programando o diseñando la resolución mecánica de acciones del PJ durante un Score. Asume que el SKILL.md principal del motor de Blades ya está cargado, así que no repite los conceptos generales de las tres fases ni la justificación filosófica del sistema.

## La estructura básica de una tirada

Cuando el PJ del jugador entra en un Score y declara una acción concreta, el sistema resuelve esa acción mecánicamente antes de que el LLM la narre. La resolución produce un resultado que es uno de tres valores discretos, y ese resultado se le pasa al LLM como contexto estructurado para que la narración tenga la forma correcta. Esto importa: el LLM no decide el resultado, el motor lo decide. El LLM solo narra el resultado que el motor produjo.

La tirada concreta usa dados de seis caras. La cantidad de dados depende del personaje y de la acción específica que está intentando, y se calcula sumando el rango del personaje en esa acción más cualquier modificador relevante. Una vez que se sabe cuántos dados tirar, se tiran todos y se mira el dado más alto. Ese dado más alto cae en una de tres categorías que producen los tres resultados narrativos.

Si el dado más alto sale seis, el resultado es éxito limpio. La acción se logra como el jugador quería, sin costo adicional. El LLM narra el éxito sin complicación. Esto no significa que no pasa nada interesante: el éxito es un evento del mundo, cambia algo, abre opciones nuevas, satisface al personaje. Pero no hay precio que pagar por el logro.

Si el dado más alto sale cuatro o cinco, el resultado es éxito con costo. La acción se logra pero pasa algo malo en el camino. Este resultado es probablemente el más interesante narrativamente porque produce consecuencia y avance simultáneamente. El LLM narra el éxito y la complicación juntos. La complicación puede ser un costo emocional (el PJ logra lo que quería pero se da cuenta de algo que prefería no saber), un costo de relación (consigue el secreto pero el NPC ya no confía en él), un costo de recurso (lo logra pero pierde un objeto importante), o un detalle que vuelve para morder más adelante (logra pasar inadvertido pero deja una huella sutil que el antagonista podrá seguir).

Si el dado más alto sale uno, dos o tres, el resultado es mala consecuencia. La acción no se logra y además hay daño. Este es el resultado que más empuja la ficción hacia adelante porque combina fallo con presión nueva. El LLM narra el fallo con su consecuencia: el PJ pierde algo (vida, recurso, posición, oportunidad), queda en peor situación que antes, sufre estrés, daña una relación, deja una pista que sus enemigos podrán seguir, o cualquier combinación de estas.

Lo que es estructuralmente importante de este sistema, y la razón principal por la que vale la pena adoptarlo en lugar de un sistema simple de éxito o fracaso, es que fuerza al LLM a generar consecuencias narrativas en cada acción. Un sistema dicotómico permite que el LLM produzca "no pasa nada interesante". El sistema de tres categorías no lo permite: incluso el éxito limpio es un evento, el éxito con costo es siempre material narrativo (la complicación se vuelve semilla de la siguiente escena), y la mala consecuencia produce drama por definición. El sistema vuelve estructuralmente imposible que una tirada se sienta vacía.

Cuando programes el template de prompt para narrar el resultado de una tirada, asegurate de que el LLM reciba la categoría del resultado como parámetro explícito en el prompt. No basta con decirle "el personaje intentó X": tiene que recibir "el personaje intentó X, el resultado es éxito con costo, narrá el éxito y la complicación que esto produce". Sin esa instrucción explícita, el LLM tiende a narrar éxitos limpios siempre porque es lo más cómodo de escribir.

## Cantidad de dados según atributos

En Blades canónico hay tres atributos generales (Insight, Prowess, Resolve) y cada uno agrupa cuatro acciones específicas. El personaje tiene un rango de cero a cuatro en cada acción, y cuando intenta una acción tira esa cantidad de dados.

Para Codex tenés dos opciones legítimas. Podés usar el esquema canónico tal cual, traduciendo nombres si querés (Astucia para Insight, Pericia para Prowess, Voluntad para Resolve, por ejemplo). O podés diseñar tu propio esquema de atributos que se ajuste mejor al mundo medieval-fantástico que estás construyendo. La segunda opción es más trabajo pero te permite tener atributos como "Fervor" o "Astucia Mundana" o "Tacto" que son específicos del mundo. Cuando llegues a este punto, James, te conviene decidir antes de armar la primera ficha de PJ porque cambiar atributos después es bastante invasivo.

Las acciones específicas dentro de cada atributo tampoco tienen que ser idénticas a las de Blades canónico. En Blades hay acciones como Sneak (moverse sin ser visto), Prowl (moverse con sigilo combativo), Attune (sentir lo sobrenatural), Command (ordenar con autoridad), Sway (convencer con palabras), Study (analizar). Para Codex algunas acciones de Blades hacen sentido directo (Sway, Study), otras necesitan adaptación (Prowl tiene menos sentido si el PJ no es un ladrón profesional), y otras nuevas pueden agregar valor (Pescar, Recordar Profecía, Resistir Visión).

Mi recomendación práctica es empezar con el esquema canónico de tres atributos y doce acciones, ajustar los nombres al castellano, y dejar refinamiento del esquema para la segunda iteración cuando ya hayas jugado el MVP y sepas qué acciones aparecen recurrentemente y cuáles nunca se usan.

Cuando el PJ tiene cero dados en una acción, el sistema usa la regla del cero: en lugar de tirar nada (que sería automáticamente fallo), se tiran dos dados pero se toma el menor. Esto da una pequeña chance de éxito incluso para acciones en las que el personaje no tiene entrenamiento, lo cual es importante para no bloquear líneas narrativas por falta de habilidad.

## Posición y efecto

Antes de tirar dados, cada acción se evalúa en dos ejes que modulan la interpretación del resultado. Estos dos ejes son la pieza más conceptualmente sutil del sistema de Blades y vale la pena entenderla bien antes de programarla, porque mal entendida produce mecánica plana.

La posición representa cuán riesgosa es la acción. Tiene tres niveles que se pueden codificar como un enum o un entero. Posición controlada significa que el personaje tiene ventaja, el riesgo es bajo, y las malas consecuencias serán leves o evitables. Posición arriesgada significa que la situación es pareja, las consecuencias serán significativas pero no catastróficas. Posición desesperada significa que el personaje está en desventaja clara, las consecuencias pueden ser graves o letales.

El efecto representa cuánto cambia el mundo si la acción tiene éxito. También tiene tres niveles. Efecto limitado significa que el éxito logra algo modesto, parcial, una versión reducida de lo que el personaje quería. Efecto estándar significa que el éxito hace exactamente lo que el personaje quería, ni más ni menos. Efecto grande significa que el éxito tiene impacto extra, abre opciones nuevas, daña al rival más allá de lo esperado, o produce ondas que afectan a otras situaciones.

En Blades canónico jugado en mesa, posición y efecto las decide el GM al juzgar la situación. Eso no es una opción en Codex porque no hay GM humano. La pregunta arquitectónica importante es: ¿quién decide posición y efecto en Codex? Hay tres respuestas legítimas y vale la pena entender por qué elegimos la que elegimos.

La primera opción sería que las decida el LLM. Le pasamos contexto, le pedimos que evalúe la situación, y el LLM responde con posición y efecto. Esta opción es atractiva porque es flexible, pero tiene un problema serio: el LLM tiende a normalizar resultados hacia "arriesgada/estándar" porque es lo cómodo de evaluar y narrar. Pierde sensibilidad al contexto específico del personaje. Además, mete una llamada extra al LLM antes de la tirada, lo que duplica el costo.

La segunda opción sería que las decida el jugador, eligiendo cuán riesgosa es su acción dentro de un menú. Esto es lo que hacen algunos juegos solitarios. Pero rompe el espíritu de Blades: el jugador no tiene visión privilegiada de la situación, debería estar sometido al juicio de la mecánica como en una mesa de rol con GM.

La tercera opción, que es la que elegimos para Codex, es que las decida el motor calculándolas determinísticamente del estado del mundo. La fórmula combina varios factores que el sistema ya conoce. El memetario del personaje cruzado con el del lugar produce un score base de favorabilidad: si los modificadores del lugar subsidian fuertemente los memes que el personaje necesita activar para esta acción, la posición sube hacia controlada. Si los penalizan fuerte, baja hacia desesperada. La afinidad o conflicto entre las PF del personaje y las del antagonista (si lo hay) suma o resta. El estado del personaje (estrés actual, vida, hitos relevantes que reaparecen como flashback en este contexto) modula. Las herramientas o recursos que lleva sumar o restan.

El cálculo concreto puede ser una combinación lineal de estos factores con umbrales. Por ejemplo: si la suma de modificadores positivos supera +5, posición controlada. Si está entre -2 y +5, posición arriesgada. Si está por debajo de -2, posición desesperada. Para el efecto, mirar cuántos memes activos del loadout son relevantes para esta acción específica (medido por similitud semántica con la acción declarada): muchos memes alineados producen efecto grande, pocos producen limitado. Los números exactos son provisionales y vas a tunearlos viendo cómo se comporta el sistema en juego real.

El cálculo es aritmética determinista, no llamadas al LLM. Sucede silenciosamente antes de la tirada. El LLM recibe el resultado como contexto estructurado: "posición arriesgada, efecto estándar, resultado 4-5". Eso le da una rúbrica precisa para narrar.

## La importancia de mostrar posición y efecto al jugador

Una decisión de UX que es importante no perder de vista: el jugador puede ver la posición y el efecto antes de decidir si tira o si retira la acción. Esto no es solo conveniencia, es estructural al diseño dramático.

El drama mecánico no es solo el resultado de la tirada sino la decisión informada de tirar sabiendo el riesgo. Un jugador que ve "posición desesperada, efecto limitado" y elige tirar igual está produciendo drama por elección consciente, no por azar. El sistema lo está haciendo cargo de una decisión, no sometiéndolo a una sorpresa.

Cuando programes la UI de Score, asegurate de que la posición y el efecto se muestran claramente antes de la tirada, junto con la cantidad de dados. El jugador debe poder leer "vas a tirar tres dados, en posición arriesgada, con efecto estándar" y decidir si acepta esos términos, modifica la acción para mejorar la posición, paga estrés para empujar, o se retira.

Si el jugador retira la acción antes de tirar, no hay consecuencia mecánica: simplemente no pasa esa acción en el mundo. El personaje pensó en hacer algo, lo evaluó, y prefirió no hacerlo. Esto es legítimo y no debe penalizarse mecánicamente, aunque puede haber narración del momento (el personaje duda y se queda quieto).

## Empuje del jugador para modificar la tirada

Antes de tirar, el jugador tiene la opción de pagar dos puntos de estrés para mejorar la tirada de tres maneras posibles, y solo puede elegir una de las tres por tirada. Puede agregar un dado extra, lo que aumenta la chance de sacar seis. Puede mejorar la posición en un nivel, de desesperada a arriesgada o de arriesgada a controlada. Puede mejorar el efecto en un nivel, de limitado a estándar o de estándar a grande.

Estas tres palancas le dan al jugador agencia mecánica real durante el Score. Puede arriesgarse a forzar resultados que de otro modo serían malos, sabiendo que cada empujón lo acerca al punto de quiebre del estrés (donde se gana un trauma).

El detalle de cómo funciona el sistema de estrés y los traumas vive en references/stress-y-trauma.md. Cargá ese archivo si vas a programar esa parte.

## Consecuencias de mala tirada y resistencia

Cuando la tirada produce mala consecuencia, el sistema (con apoyo del LLM tier 2 narrando) determina qué consecuencia concreta sufre el personaje. Las consecuencias pueden ser de varios tipos: daño físico (que reduce la barra de vida), daño emocional o reputacional (que se traduce a stress), pérdida de oportunidad (la acción no solo falla sino que cierra esa puerta), complicación del mundo (algo cambia en el contexto que ahora juega en contra), o detalle que persiste como problema futuro.

Una vez que el LLM narra la consecuencia, el jugador tiene la opción de resistir pagando estrés. La resistencia funciona así: el jugador declara que su personaje resiste la consecuencia, paga una cantidad de estrés que depende del atributo relevante (típicamente entre uno y cinco puntos), y el sistema permite atenuar, esquivar o transformar la consecuencia.

Atenuar significa que la consecuencia ocurre pero menos grave (en lugar de perder tres de vida, pierde uno). Esquivar significa que la consecuencia se evita por completo a costa del estrés. Transformar significa que la consecuencia cambia de naturaleza, típicamente de daño físico a estrés emocional (el personaje recibe el golpe pero su voluntad lo mantiene en pie, a costa de carga psíquica acumulada).

La cantidad de estrés que cuesta resistir se calcula tirando seis dados menos la calidad del personaje en el atributo relevante, y el resultado se compara con el dado más alto: el costo de resistencia es seis menos el dado más alto. Por ejemplo, si la resistencia tira tres dados y el más alto sale cuatro, el costo es 6 - 4 = 2 puntos de estrés. Esto significa que personajes con mejores atributos resisten más barato.

La regla operativa importante es que el jugador no tiene que resistir cada consecuencia. Puede aceptar el daño si prefiere reservar estrés para más adelante. Esa decisión de cuándo resistir y cuándo tragar es donde está mucho del drama del juego: el jugador elige qué peleas dar y cuáles dejar pasar.

## Cómo se acopla con el motor cognitivo

Recordá que cada elemento del sistema de tiradas se acopla con el motor cognitivo. Los modificadores que entran en el cálculo de posición y efecto vienen del cruce de memetarios. Los memes que se activan durante el Score acumulan refuerzo si la tirada sale bien (peso histórico crece). El estrés y los traumas alimentan el memetario inyectando memes experimentales. Los hitos biográficos, cuando se generan después de un Score climático, modifican la arquitectura del personaje.

Si te encontrás programando una mecánica de tirada que no tiene punto de contacto con el motor cognitivo, pará y revisá. La integración es lo que vuelve único al sistema. Una tirada que solo afecta números (vida, estrés) y no afecta memetario está dejando vacío el potencial narrativo.

## Recordatorios operativos

Cuando James trabaje en este territorio, dos cosas conviene tener presentes.

Primera: no estás programando un sistema de combate. Estás programando un sistema de resolución de acciones dramáticas, que pueden o no incluir violencia. Una conversación tensa donde el PJ intenta sonsacarle un secreto al tabernero es un Score válido, con sus tiradas y consecuencias. Si te encontrás pensando solo en combate, estás reduciendo el alcance del sistema.

Segunda: el resultado de una tirada nunca debe ser anticlimático. Si la mecánica produce un resultado que el LLM narra como "no pasa nada relevante", algo está mal en el prompt o en cómo se está interpretando el resultado. Cada tirada debe producir cambio narrativo concreto. Si James reporta que las tiradas se sienten vacías, el problema casi nunca está en la mecánica, está en la narración. Revisá los templates antes de tocar las reglas.
