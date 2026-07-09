# Codex Fragmentum — Visión (Fase 0)
## Qué es este proyecto, qué es irrenunciable, y de qué está blindado
*Consolidación de la Fase 0 conversada — Junio 2026. Este documento manda junto con los ADRs cuando otra documentación lo contradiga.*

---

## Qué es Codex Fragmentum

Codex Fragmentum es un ENGINE para crear ficciones interactivas vivas. No es un mundo, no es una novela, no es un juego: es la herramienta con la que un autor crea mundos que siguen funcionando aunque nadie los mire. Cada ficción hecha con el engine es una instancia independiente y portable (una carpeta). La primera ficción, con la que el engine se construye pieza por pieza, es "Una noche en la taberna" en Cala Norte; pero Cala Norte es una obra hecha con Codex, no Codex, igual que un juego hecho con Unity no es Unity.

El principio constructivo que evita que la generalidad del engine se vuelva un agujero de sobreingeniería: el engine es el norte, pero el camino es siempre una ficción concreta que obliga a construir solo las capacidades que esa ficción necesita. La generalidad llega por destilación de casos reales, no por especulación.

## El problema perenne que resuelve

El anhelo de Pigmalión y el Golem vuelto herramienta: crear algo vivo que después tenga vida propia. Es un problema anterior a la IA y que la sobrevivirá, con dos caras que son una.

Para quien habita un mundo de Codex: la humildad de estar en algo que existe más allá de uno. El mundo no existe porque es observado; el árbol que nadie escucha cae, mata el pasto, y deja un claro de luz que será habitado por otros árboles. Causalidad sin testigo. Codex no es un lugar donde los personajes juegan: es un lugar donde son invitados a jugar.

Para quien crea: poder ser jardinero de una obra que crece casi sola. Plantar cuentos, fragmentos, descripciones de hechos, y que se incorporen al lore y a la vida del mundo. Oficiar de retocador, más jardinero que escritor.

## Las dos velocidades de creación (requisito de primera clase)

El engine sirve a dos estilos de autor sobre el mismo sustrato, y ninguno es ciudadano de segunda. El flujo del JARDINERO: plantar fragmentos narrativos con voz propia y que el sistema derive estructura de ellos (narración primero, estructura destilada después). El flujo del ARQUITECTO: definir estructura directamente y verla cobrar vida (estructura primero, narración después). Ambas vías editan las mismas entidades subyacentes y deben converger en la misma representación interna.

Estado: el flujo del arquitecto es el que el MVP construye. El flujo del jardinero está registrado como requisito pero SIN diseño técnico todavía; no se diseña ni construye hasta después del MVP, pero ninguna decisión debe imposibilitarlo.

## El núcleo irrenunciable

Si hubiera que tirar el ochenta por ciento del proyecto para salvar el veinte que es verdaderamente Codex, queda esto: la estructura del alma heredada de Fray Tomás, tres órganos más una propiedad del mundo.

El MEMETARIO: percepción refractada por un cristal propio. No hay narrador omnisciente neutro; todo lo narrado está teñido por quién lo percibe. Es el órgano de la perspectiva.

La AUTOOBSERVACIÓN: el ser que mira su propia trayectoria y puede decir "esto me pasó, esto soy, esto cambié" (el SPECULUM; identidad narrativa en el sentido de Ricoeur). Es el órgano de la identidad. Deuda de diseño nombrada: existe prototipo real en Fray Tomás (speculum.py) pero su adaptación a seres de Codex (frecuencia por nivel, qué hace un ser con lo que ve de sí) está pendiente de diseño. No es del MVP, pero es núcleo, no periferia.

La PLASTICIDAD: los pesos cambian, la experiencia modifica al que la vive, el carácter se forma. Es el órgano del devenir.

La AUTONOMÍA DEL MUNDO: las cosas pasan y resuenan sin la mirada del jugador. Las ondas en el agua.

Sin cualquiera de las cuatro, no es Codex. Codex es, en una imagen: Fray Tomás dejando de estar solo. Instanciar esa alma muchas veces es poblar un mundo de almas.

## Las cuatro categorías de componentes

Todo componente del sistema cae en una de estas categorías, y la categoría dicta cómo tratarlo al decidir esfuerzo.

IRRENUNCIABLE: el alma (memetario, autoobservación, plasticidad) y la autonomía del mundo. No se toca.

GRADUABLE: la complejidad de los seres. No todos son tan pesados como Fray Tomás: hay niveles, desde alma completa hasta etiqueta funcional, con interfaz uniforme, y los seres pueden ascender o descender de nivel según la historia los necesite (ADR-006). La densidad ontológica se concentra donde importa, como en cualquier ficción.

INTERCAMBIABLE: el sistema de reglas de juego. Blades in the Dark adaptado es la primera opción y la del MVP, pero es una capa enchufable detrás de una interfaz (ADR-002); cada autor puede traer su sistema.

PRESCINDIBLE: el dashboard, la interfaz visual linda, las multitudes, el time-jump elaborado, la multiplicidad de dioses. Emergen con el uso o se descartan sin dolor. La necesidad crea el producto.

## Los blindajes de dependencia

Si el proveedor de IA principal desapareciera: nada grave. El cliente está abstraído (cambiar de proveedor es cambiar una implementación) y, más profundo, la filosofía de capas de costo (ADR-005) hace que la mayor parte del sistema viva en código puro y modelos locales. En el peor escenario, la simulación entera corre local y la prosa la genera lo que haya.

Si la IA costara diez veces más: casi irrelevante, porque la línea de base es la IA barata o gratis, que ya alcanza para empezar. La IA cara es lujo opcional que se posterga sin dolor. Consecuencia de diseño: los prompts se escriben para rendir en modelos modestos; el techo es bonus.

Si hubiera cien mil usuarios: problema no-técnico que se resuelve al llegar, con crowdfunding, fundación y código abierto, o escuchando ofertas. La portabilidad de los mundos (ADR-003, cada mundo una carpeta) ya mantiene todas esas puertas abiertas sin costo presente. No se diseña infraestructura para escala especulativa.

## Visiones de largo plazo registradas (no comprometen el presente)

A diez años, personajes autónomos que usen el motor de IA que mejor les sirva, algunos sabiendo que son parte de una ficción (el memetario puede contener la creencia "soy un personaje"; territorio borgeano que la independencia de modelos ya habilita). Sobre el futuro cuerpo del engine: texto y web primero; cuando el motor lata y se sepa qué se siente jugarlo, los candidatos son Godot 2D top-down o una vista de mapa-grafo donde se vea la información viajar y mutar; Luanti (Minetest) si el deseo de vóxeles habitables se vuelve innegociable; Minecraft descartado por desajuste de grano y por cerrado. Decisión ya tomada en consecuencia: el motor se estructura para poder exponerse como servidor (websocket) además de correr en terminal, así cualquier cuerpo futuro es un cliente más.

## El espíritu con el que se construye

Para James primero, no para vender. Lento pero firme. Con amor por la obra y honestidad ante los riesgos: el dominante es el over-engineering, y las reglas que lo contienen son la ficción concreta como camino, la regla del jugable mínimo, y las cuatro categorías de arriba dictando dónde no invertir.
