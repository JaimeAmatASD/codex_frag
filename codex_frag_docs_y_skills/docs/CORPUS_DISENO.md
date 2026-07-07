# Codex Fragmentum — El sistema de corpus
## Cómo los seres beben de fuentes y por qué eso los hace quienes son
*Documento de diseño — Junio 2026*

---

## Para qué existe este documento

El corpus es la pieza del sistema que diseñamos enteramente en conversación y que hasta ahora no vivía en ningún documento, solo en los mensajes. Este documento lo fija antes de que se diluya. No introduce decisiones nuevas: recoge y ordena lo que ya acordamos.

El corpus responde a una pregunta que el memetario solo no resuelve. El memetario dice cómo un ser palpa el mundo (su postura, sus receptores, sus cicatrices). Pero no dice de dónde viene esa postura, en qué se nutre, qué textos o ideas la alimentan. Un anarquista y un comunista pueden tener posturas igualmente fuertes, pero beben de fuentes distintas: uno de Bakunin, otro de Marx. Fray Tomás bebe de la Regla de San Benito y de los Justos de Borges. El corpus es el sustrato de fuentes del que un ser extrae su forma de ver.

La metáfora útil es la de NotebookLM, la herramienta donde uno carga un conjunto de fuentes y después conversa con ellas. Cada ser de Codex, y el mundo mismo, tiene su corpus de fuentes. Pero con tres diferencias profundas respecto a NotebookLM, que son lo que vuelve al corpus de Codex una pieza de diseño rica y no una simple carga de documentos. Esas tres diferencias son las tres dimensiones del corpus, y son el corazón de este documento.

---

## El corpus como entidad de primera clase

Antes de las dimensiones, una decisión arquitectónica que las enmarca. El corpus es una entidad separada y agnóstica, igual que el mundo, los seres, los lugares. No está incrustado dentro de un ser. Es una entidad propia que los seres referencian.

Esto importa por varias razones. Permite que varios seres compartan corpus: tres monjes de la misma abadía pueden beber del mismo corpus benedictino, sin duplicarlo. Permite que el mundo tenga su propio corpus (su lore, sus leyes, su historia) del que todos los seres pueden beber en distinta medida. Permite editar un corpus independientemente de los seres que lo usan: corregir una fuente, agregar un texto, y todos los que beben de él se ven afectados. Y permite que el corpus evolucione como cosa propia, con su historia.

La relación entre un ser y un corpus no es de posesión sino de referencia, con parámetros. Un ser apunta a uno o más corpus, y para cada uno tiene una configuración de las tres dimensiones que vienen ahora. Dos seres pueden beber del mismo corpus de maneras radicalmente distintas según esa configuración.

---

## Primera dimensión: la profundidad de asimilación

La primera diferencia con NotebookLM es que no todos beben de su corpus con la misma hondura. Hay una dimensión de profundidad de asimilación, que va de superficial a entrañado.

Fray Tomás sabe sus textos de memoria. Los rumia, los tiene incorporados hasta el tuétano, puede citarlos sin pensar, los aplica a situaciones que los textos nunca contemplaron porque los entendió tan hondo que puede extrapolarlos. Ese es el extremo profundo de la dimensión. Un anarquista de café que leyó a Bakunin por encima, que tiene cuatro consignas y una actitud pero no asimiló el cuerpo del pensamiento, está en el extremo superficial. Los dos tienen el mismo corpus referenciado (digamos, el pensamiento anarquista), pero uno lo bebió hasta el fondo y el otro apenas lo mojó.

La profundidad se modela como un valor, digamos de 1 a 10, que dice cuán asimilado tiene el ser su corpus. Ese valor condiciona cuánto del corpus puede el ser efectivamente movilizar, con qué soltura, con qué capacidad de extrapolación. Un ser con profundidad alta puede sacar del corpus respuestas a situaciones nuevas; uno con profundidad baja solo puede repetir las consignas más superficiales.

Una sutileza importante que acordamos: la profundidad no es uniforme dentro de un corpus. Un ser puede haber asimilado profundamente una parte de su corpus y superficialmente otra. El cura que se sabe los evangelios de memoria pero apenas hojeó a los Padres de la Iglesia. Para el MVP esto puede simplificarse a una profundidad global por corpus, pero el diseño contempla que pueda afinarse a profundidad por sección o por fuente dentro del corpus.

---

## Segunda dimensión: la fidelidad de comprensión

La segunda diferencia con NotebookLM, y la más sutil, es que beber de un corpus no significa entenderlo bien. Hay una dimensión de fidelidad de comprensión: cuán fielmente el ser captó lo que el corpus realmente dice, versus cuánto lo deformó al asimilarlo.

El ejemplo que usamos es el del marxista soviético que entendió mal a Marx. Bebió profundamente de su corpus (profundidad alta), pero lo que asimiló es un Marx deformado por la maquinaria del Estado, por las lecturas oficiales, por su propia necesidad. Su corpus efectivo no es el Marx real sino un Marx-deformado. Tiene mucha profundidad sobre una comprensión infiel.

Acá está la decisión de diseño más importante y más contraintuitiva sobre el corpus, y conviene que quede muy clara porque es fácil de implementar mal. La deformación de comprensión no la genera el sistema automáticamente. La escribís vos, autoralmente, en el contenido del corpus.

Es decir: si querés un marxista soviético que entendió mal a Marx, no le das el corpus del Marx real con un parámetro de "fidelidad 30%" y dejás que el sistema deforme. Vos escribís directamente el Marx-deformado, el Marx tal como ese personaje lo entendió, y se lo das como su corpus. El sistema no deforma comprensiones; vos creás corpus ya deformados cuando un personaje los necesita.

Esto es coherente con la decisión raíz de todo el proyecto, la del ADR-001: el LLM y el sistema no son fuente de verdad ni de creatividad descontrolada. Vos, como autor, controlás qué cree cada personaje. Si querés un personaje que malentendió una doctrina, escribís el malentendido. El sistema no inventa malentendidos por su cuenta, porque un malentendido generado al azar sería ruido, mientras que un malentendido escrito por vos es caracterización.

Por qué entonces hablamos de "fidelidad" como dimensión, si no es un parámetro que el sistema aplica. Porque es una dimensión conceptual del diseño que te guía como autor. Cuando creás el corpus de un personaje, pensás explícitamente: ¿este personaje entendió bien o mal su fuente? Y si entendió mal, escribís el corpus deformado. La fidelidad vive en tu cabeza de autor y se materializa en el contenido que escribís, no en un número que el motor procesa. Es una dimensión de diseño, no un campo de datos calculado.

Esto tiene una consecuencia hermosa: dos personajes pueden referenciar "el mismo" pensador y tener corpus de contenido distinto, porque uno lo entendió fiel y el otro deformado. El sistema los trata como dos corpus distintos (porque su contenido es distinto), aunque conceptualmente ambos digan "yo sigo a Marx". La divergencia de comprensión se vuelve divergencia de contenido, que es algo que el sistema sí sabe manejar.

---

## Tercera dimensión: la postura hacia el conocimiento

La tercera diferencia con NotebookLM es la relación emocional y epistémica del ser con su propio corpus. No es lo mismo venerar un texto que desconfiar de él que haberlo recibido como dogma frío impuesto. Hay una dimensión de postura hacia el conocimiento.

Tres personajes pueden tener el mismo corpus, con la misma profundidad y la misma fidelidad, y aun así relacionarse con él de maneras opuestas. Uno lo venera: el texto es sagrado, indiscutible, fuente de consuelo. Otro desconfía: lo estudió a fondo pero lo tiene en cuarentena permanente, lo cita para discutirlo. Otro lo recibió como dogma frío: se lo inculcaron sin amor, lo repite por obligación o miedo, no lo eligió. El que venera, el que sospecha, y el que obedece sin fe.

Esta dimensión conecta directamente con la temperatura emocional que viene de Fray Tomás (siguiendo a Damasio), que mencionamos en el mapa de reuso. La postura hacia el corpus es una forma de temperatura emocional aplicada al conocimiento. El marxista que recibió a Marx como dogma frío tiene una temperatura distinta hacia su corpus que el que lo descubrió con pasión militante, aunque el contenido del corpus sea idéntico.

La postura se modela como un atributo de la relación entre el ser y el corpus (no del corpus mismo, porque el mismo corpus puede ser venerado por uno y sospechado por otro). Y condiciona cómo el ser moviliza el corpus en la narración: el que venera cita con reverencia, el que desconfía cita con reservas, el que obedece cita con la rigidez de lo impuesto. Para el LLM, conocer la postura del personaje hacia su corpus es información de caracterización valiosísima que cambia el tono de cómo el personaje habla de aquello en lo que cree.

---

## Cómo se accede al corpus: por interpretación, no por dosificación

Una decisión sobre el mecanismo de acceso. Cuando un ser moviliza su corpus (cuando va a hablar, decidir o percibir desde sus fuentes), ¿cómo se determina qué parte del corpus usa y cómo?

Descartamos la dosificación mecánica. No es que el sistema calcule "este personaje tiene profundidad 6, entonces accede al 60% del corpus, las primeras seis fuentes de diez". Eso sería tosco y produciría comportamientos artificiales. La profundidad, la fidelidad y la postura no son perillas que recortan mecánicamente el acceso.

En cambio, el acceso es por interpretación del LLM. Al LLM se le da el corpus relevante junto con las tres dimensiones expresadas como contexto (qué tan profundo lo tiene este personaje, con qué fidelidad, con qué postura), y el LLM interpreta cómo eso se traduce en lo que el personaje dice o piensa. Las dimensiones son matices finos que el LLM sabe manejar interpretativamente mucho mejor que cualquier regla mecánica.

Esto es coherente con la división de trabajo de todo el sistema: el motor mantiene el estado (qué corpus tiene el ser, con qué dimensiones) y el LLM hace el trabajo interpretativo fino (cómo eso se manifiesta en la prosa). Pedirle a una regla que decida cómo un personaje con veneración media y fidelidad baja cita su corpus sería pedirle a la aritmética algo que es esencialmente interpretativo. El LLM es la herramienta correcta para ese matiz.

Hay un límite a esto que conviene tener presente. Que el acceso sea interpretativo no significa que el LLM pueda inventar contenido del corpus que no está. El LLM interpreta cómo el personaje usa el corpus que tiene, pero no agrega fuentes ni doctrinas que vos no escribiste. La creatividad del LLM es sobre la forma de movilizar el corpus, no sobre su contenido. El contenido lo controlás vos.

---

## Implementación gradual: liviano primero, RAG después

Una decisión pragmática sobre cómo construir esto sin caer en sobreingeniería, que es coherente con la filosofía de capas y con tu riesgo dominante.

La implementación liviana va primero. En la primera versión, el corpus de un ser no es una base de datos vectorial sofisticada con recuperación semántica. Es, simplemente, campos de texto con material destilado que vos curás. Escribís un texto que captura la esencia del corpus de ese personaje (las ideas-fuerza, las citas clave, el tono), y eso se le pasa al LLM como contexto cuando el personaje habla. Profundidad, fidelidad y postura se expresan en cómo escribís ese texto destilado y en unos pocos parámetros que acompañan.

Esto es barato, controlable, y suficiente para el MVP y bastante más allá. Para un puñado de personajes con corpus de tamaño manejable, un texto destilado bien escrito le da al LLM todo lo que necesita. No hace falta maquinaria de recuperación para personajes cuyo corpus entra en unos párrafos.

El RAG (recuperación aumentada, con embeddings y búsqueda semántica sobre fuentes extensas) se difiere. Tiene sentido cuando un corpus sea demasiado grande para caber destilado en el contexto: un personaje que beba de una biblioteca entera, donde haga falta recuperar dinámicamente qué fragmento es relevante a cada situación. Eso es funcionalidad de fase avanzada. El diseño la contempla (el corpus como entidad separada con sus fuentes ya prevé que algún día esas fuentes se indexen), pero no se construye hasta que un corpus real lo justifique. La generalidad por destilación de casos reales, no por especulación.

Esta gradualidad conecta con la decisión de las dos velocidades de creación. El corpus liviano (texto destilado curado a mano) es el flujo del arquitecto aplicado al corpus: vos escribís directamente la esencia. Cuando llegue el RAG, podría conectarse con el flujo del jardinero: plantás fuentes completas y el sistema las indexa y recupera. Pero eso es después.

---

## La evolución del corpus en el tiempo

Una dimensión temporal que acordamos prever en el diseño pero diferir en la construcción.

Los corpus de los seres no son estáticos en la vida real. Una persona profundiza en sus fuentes con los años, o se desencanta de ellas, o las reinterpreta tras una crisis, o incorpora fuentes nuevas. El marxista puede volverse crítico de Marx. El creyente puede perder la fe en sus textos. El que despreciaba una doctrina puede convertirse. El corpus de un ser, y su relación con él (las tres dimensiones), evolucionan.

La decisión de diseño es que esta evolución está prevista pero diferida, y crucialmente, cuando se construya, se engancha a los disparadores que ya mueven al personaje, no a un motor de evolución separado. No hay un sistema aparte que haga evolucionar corpus. La evolución del corpus es una consecuencia de los mismos eventos que ya reconfiguran al ser: los hitos biográficos, las crisis, el paso del tiempo.

Es decir: cuando un personaje sufre un hito que cuestiona su fe, ese mismo hito (que ya modifica PF, inyecta memes, abre deudas morales según el diseño del memetario) puede también modificar su postura hacia el corpus, de veneración a desconfianza. Cuando una crisis biográfica se resuelve, puede cambiar la fidelidad con que entiende sus fuentes. Cuando pasa mucho tiempo de estudio, puede subir la profundidad. Los disparadores ya existen en el sistema; lo único que se agrega, cuando llegue el momento, es que esos disparadores también toquen el corpus.

Esto evita construir un subsistema de evolución de corpus separado, que sería sobreingeniería. La evolución del corpus es un efecto más de los mecanismos de cambio que el sistema ya tiene. Para el MVP, los corpus son estáticos (los personajes no cambian de fuentes en una noche en la taberna). La evolución se construye cuando se construyan los hitos y las crisis, colgándose de ellos.

---

## Cómo el corpus se relaciona con el memetario

Conviene dejar clara la relación entre el corpus y el memetario, porque son dos piezas distintas que se tocan.

El memetario es la estructura cognitiva activa: las piedras fundacionales, los memes operativos, los hitos. Es cómo el ser palpa el mundo aquí y ahora. El corpus es el sustrato de fuentes del que esa estructura se nutre. La relación natural entre ambos es que el corpus alimenta al memetario: las piedras fundacionales de un ser derivan, en buena parte, de su corpus.

Fray Tomás ya insinúa esto. Sus PF (la Regla de San Benito, los Justos de Borges) son ideas-fuerza derivadas de textos fuente. En ese sentido, las PF de Fray Tomás ya son un corpus rudimentario destilado en postura. Lo que Codex agrega es formalizar esa relación: el corpus es la fuente, las PF son la destilación de la fuente en postura cognitiva operativa.

Esto sugiere un flujo posible, aunque no obligatorio para el MVP: derivar PF desde el corpus. Dado el corpus de un personaje y sus tres dimensiones, se podrían derivar (vos a mano, o el LLM como propuesta que vos validás) las piedras fundacionales que ese corpus produce en ese personaje. El anarquista con corpus bakuninista profundo y venerado produce ciertas PF; el mismo corpus superficial y recibido como dogma produce PF más débiles o distintas. El corpus más las tres dimensiones determinan qué postura cognitiva emerge.

Para el MVP esto puede hacerse a mano: escribís el corpus liviano y escribís las PF directamente, sin derivación automática. La derivación corpus a PF es una comodidad futura, no una necesidad. Pero el diseño deja claro que conceptualmente el corpus es anterior al memetario: las fuentes producen la postura.

---

## El corpus del mundo

Todo lo anterior aplica a los seres, pero el mundo mismo también tiene corpus, y conviene tratarlo porque tu forma de crear (los fragmentos míticos que mostraste) lo hace especialmente relevante.

El corpus del mundo es su lore, su historia, sus leyes, su tono. Pero, como vimos con tus textos de la niña Pak y el tigre inmenso, ese corpus no tiene por qué ser una enciclopedia de worldbuilding escrita como manual. Puede ser una colección de fragmentos míticos, cuentos, estampas, de los cuales el LLM extrae el tono del mundo, sus leyes implícitas, sus personajes recurrentes. El corpus del mundo es jardín de cuentos, no manual de referencia.

Esto conecta el corpus con la decisión de las dos velocidades de creación. El flujo del jardinero, aplicado al corpus del mundo, es exactamente esto: plantás fragmentos narrativos y el sistema (y el LLM al narrar) bebe de ellos como corpus, extrayendo el tono y las leyes sin que vos las hayas enunciado como reglas. El flujo del arquitecto sería, en cambio, escribir el lore como documento estructurado de reglas del mundo. Los dos alimentan el mismo corpus del mundo, y un autor puede mezclarlos.

Las tres dimensiones aplican al corpus del mundo de forma análoga, aunque con menos peso que en los seres. La profundidad sería cuánto del lore está efectivamente disponible al narrar. La fidelidad es menos relevante (el mundo no malentiende su propio lore, aunque los seres dentro de él sí pueden tener versiones deformadas, que son sus corpus propios). La postura del mundo hacia su corpus es difusa; tiene más sentido hablar de postura en los seres.

---

## Resumen de las decisiones sobre el corpus

El corpus es una entidad de primera clase, separada y agnóstica, que los seres y el mundo referencian, no poseen. Varios seres pueden compartir corpus; un corpus se edita independientemente de quienes lo usan.

Tiene tres dimensiones de diseño. La profundidad de asimilación, cuán hondo bebió el ser de su corpus, modelada como valor, posiblemente afinable por sección. La fidelidad de comprensión, cuán fielmente lo entendió, que no es un parámetro que el sistema aplica sino una dimensión autoral: la deformación se escribe en el contenido del corpus, no la genera el motor. Y la postura hacia el conocimiento, la relación emocional y epistémica del ser con su corpus (venera, desconfía, obedece sin fe), modelada en la relación ser-corpus, conectada con la temperatura emocional de Damasio.

El acceso al corpus es por interpretación del LLM, no por dosificación mecánica: las tres dimensiones se le pasan como contexto y el LLM interpreta cómo se manifiestan, dentro del límite de que no inventa contenido que vos no escribiste.

La implementación es gradual: corpus liviano (texto destilado curado a mano) primero, suficiente para el MVP y más allá; RAG con recuperación semántica diferido hasta que un corpus grande lo justifique.

La evolución del corpus en el tiempo está prevista pero diferida, y cuando se construya se engancha a los disparadores que ya mueven al personaje (hitos, crisis, tiempo), no a un motor de evolución separado.

El corpus se relaciona con el memetario como fuente a destilación: las piedras fundacionales derivan del corpus. Para el MVP se escriben ambos a mano; la derivación automática es comodidad futura.

El mundo también tiene corpus, que puede ser un jardín de fragmentos míticos (flujo del jardinero) o lore estructurado (flujo del arquitecto), o ambos.

---

## Lo que esto significa para el MVP

Concretamente, para la noche en la taberna de Cala Norte, el corpus se implementa en su forma más liviana. Cada uno de los pocos personajes (Marcos, el tabernero, los NPCs) tiene un corpus liviano: un texto destilado breve que captura de qué fuentes bebe su forma de ver, con una indicación de profundidad, una comprensión ya escrita por vos con la fidelidad que quieras, y una postura. El mundo tiene un corpus liviano también: el tono de Cala Norte, sus creencias sobre el mar, quizás uno o dos fragmentos míticos que establezcan la voz.

Nada de RAG, nada de evolución, nada de derivación automática de PF. Solo textos destilados que le dan al LLM el sustrato de fuentes desde el cual cada personaje habla. Eso alcanza para probar si el corpus, sumado al memetario, hace que los personajes se sientan nutridos de algo, que tengan un fondo del cual sale su forma de ver. Si en la taberna el tabernero habla desde un fondo distinto al de Marcos, y se nota que beben de aguas distintas, el corpus liviano funciona y lo demás puede esperar.

---

*El corpus es de dónde viene la mirada. El memetario es la mirada. Lo que se ve es cosa del mundo.*
