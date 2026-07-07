# Memetario simbólico de los lugares — los lugares como cuerpos cognitivos

Este archivo es referencia operativa para cuando estés diseñando o programando cómo los lugares afectan cognitivamente a los agentes que los habitan. Cubre el memetario simbólico de los lugares, los modificadores de costo que aplican, el bucle de retroalimentación donde los lugares cambian con quienes los habitan. Asume que el SKILL.md principal de cartografía ya está cargado.

## Por qué esto es la pieza más distintiva del sistema espacial

Vale la pena empezar por la motivación porque es lo que diferencia profundamente a Codex de cualquier simulador narrativo convencional. En la mayoría de los sistemas, los lugares son contenedores pasivos donde pasan cosas. Tienen propiedades estáticas (clima, atmósfera, descripción) pero no afectan la cognición de los personajes. Un personaje pacífico puesto en un campo de batalla sigue actuando pacíficamente, solo está pacíficamente en un lugar violento.

En Codex Fragmentum los lugares son cuerpos cognitivos distribuidos. Tienen memetario simbólico propio: un conjunto de tags que representan la carga simbólica del lugar. Tienen modificadores de costo que afectan a los memes de los agentes según cuán alineado está cada meme con esa carga simbólica. El campo de batalla vuelve más barato activar memes violentos y más caro activar memes contemplativos. La abadía hace lo opuesto. El personaje pacífico en el campo de batalla literalmente piensa distinto: sus memes operativos cambian de loadout porque los costos cambiaron.

Esto produce una consecuencia narrativa enorme. Los arcos de personaje grandes, donde un personaje cambia profundamente a lo largo de meses de juego, no están programados explícitamente. Emergen del cruce entre el personaje y los lugares que habitó durante mucho tiempo. El monje benedictino llevado a una tribu vikinga cambia no porque el código lo haga cambiar sino porque los modificadores del nuevo entorno cambian qué memes le son baratos, sus activaciones se acumulan, sus pesos se ajustan, y eventualmente sus PF se cuestionan.

Esta es una de las piezas más bonitas del proyecto y conviene programarla con cuidado.

## La estructura del memetario simbólico

Cada lugar tiene una lista de etiquetas simbólicas. No son frases largas, son tags concisos que representan qué carga el lugar. Una abadía podría tener tags como contemplación, humildad, orden_horario, sospecha_de_la_novedad, dignidad_del_trabajo_manual, latín_como_vehículo_de_verdad. Una taberna podría tener bebida, conversación, indulgencia, secretos_susurrados, relajación_de_la_etiqueta. Un campo de batalla podría tener violencia_legítima, honor_marcial, cercanía_de_la_muerte, fraternidad_de_supervivientes.

```python
class Lugar(BaseModel):
    # ... otros campos ...
    memetario_simbolico: list[str]
    modificadores_categoria: dict[str, int] = {}
```

El memetario simbólico no es solo decoración: cada tag se asocia con uno o más modificadores de costo que afectan a los memes operativos de los agentes según las categorías de esos memes.

## Los modificadores de costo

Los modificadores son donde la carga simbólica se vuelve mecánica concreta. Cada lugar tiene un diccionario que mapea categorías de memes a modificadores numéricos. Un modificador positivo encarece los memes de esa categoría (más caros de activar). Un modificador negativo los abarata (más baratos). Un modificador de cero los deja igual.

```python
modificadores_categoria = {
    "accion_violenta": +3,
    "elocuencia_latina": -1,
    "trabajo_manual": -1,
    "soberbia": +5,
    "novedad_intelectual": +2,
    "contemplacion": -2,
}
```

Cuando un agente entra a este lugar y el motor calcula su loadout, el costo de cada uno de sus memes se ajusta sumando los modificadores de las categorías a las que el meme pertenece. Un meme que tenga categoría accion_violenta y costo base 2 pasa a costar 5 en este lugar. Si el agente tiene mana máximo 20 y este meme costaba antes 2 puntos, ahora cuesta 5, lo cual lo deja con 15 para repartir entre los otros memes. Si el meme cuesta más de 20, queda excluido del loadout (no puede activarse en este lugar).

La pregunta práctica es cómo definir las categorías de los memes y los modificadores de los lugares. Mi recomendación es trabajar inductivamente: empezar con un set chico de categorías (cinco a diez) que cubran los temas principales del mundo, asignar memes a categorías según su contenido obvio, y agregar nuevas categorías solo cuando aparece la necesidad. Las categorías pueden ser modificadas en cualquier momento, así que no hace falta acertar perfecto desde el principio.

Para la magnitud de los modificadores, una regla práctica útil es esta: los modificadores típicos van de -3 a +3, los modificadores fuertes (raros, para situaciones donde el lugar está fuertemente alineado o opuesto a una categoría) van de -5 a +5, y los modificadores extremos (muy raros, casi prohibitivos) van más allá. Si te encontrás poniendo modificadores de +10 a muchas categorías de muchos lugares, la inflación lo vuelve sin sentido.

## El cálculo concreto en el loadout

Para que la integración con el memetario sea concreta, el cálculo del costo efectivo de un meme en un lugar específico se ve así.

```python
def costo_efectivo(meme: MemeOperativo, lugar: Lugar) -> int:
    costo = meme.costo_mana_base
    for categoria in meme.categorias:
        modificador = lugar.modificadores_categoria.get(categoria, 0)
        costo += modificador
    return max(1, costo)  # piso de 1, nunca gratis
```

El piso de 1 es importante. Sin él, modificadores muy negativos podrían llevar el costo a cero o negativo, lo cual rompería el sistema económico. Un meme siempre cuesta al menos 1 mana, aunque el lugar lo subsidie fuerte.

No hay techo explícito porque a veces conviene que un meme sea efectivamente imposible de activar en cierto lugar. Si un meme cuesta 99 (porque el lugar lo penaliza mucho), simplemente nunca entra al loadout de un agente con mana máximo 20. Eso es correcto narrativamente: hay cosas que ciertos lugares no permiten pensar.

## El bucle de retroalimentación

Una pieza más sutil del sistema que vale la pena programar bien para iteraciones futuras: los lugares también cambian con quienes los habitan. Esto cierra el bucle agente-mundo y produce sensación de que los lugares tienen historia.

La mecánica funciona así. Cada vez que un agente activa un meme en un lugar, el sistema registra esa activación contra el lugar. Si un meme se activa repetidamente en el mismo lugar a lo largo de muchos días de juego, su categoría empieza a infiltrarse en el memetario simbólico del lugar. Lentamente, durante meses de tiempo del mundo, una taberna donde mucha gente activa cantar_borracho gana ese tag en su memetario simbólico, y empieza a subsidiar cantar_borracho a recién llegados.

```python
def registrar_activacion_en_lugar(meme: MemeOperativo, lugar: Lugar, peso: float):
    for categoria in meme.categorias:
        lugar.activaciones_acumuladas[categoria] = (
            lugar.activaciones_acumuladas.get(categoria, 0) + peso
        )
        # Después de un umbral, la categoría se incorpora al memetario simbólico
        if lugar.activaciones_acumuladas[categoria] > UMBRAL_INCORPORACION:
            if categoria not in lugar.memetario_simbolico:
                lugar.memetario_simbolico.append(categoria)
                lugar.modificadores_categoria[categoria] = -1
                # Subsidio leve, gana fuerza con más activaciones
```

Este sistema produce evolución lenta de los lugares. La taberna que durante años fue lugar genérico se va volviendo lugar de cantar borracho específicamente, lo cual la diferencia de otras tabernas y le da identidad. Los lugares ganan personalidad como ganan personalidad las personas: por uso repetido.

Esta mecánica es fase 2 o posterior, no MVP. Para el MVP el memetario simbólico de la taberna está fijado por James y no cambia. Pero programar la estructura para que pueda cambiar es trabajo barato y deja la puerta abierta a iteraciones posteriores.

## Cómo diseñar un lugar nuevo

Para que sea operativo, te dejo el procedimiento práctico que conviene seguir cuando James diseña un lugar nuevo en el mapa.

Primero, definir el rol narrativo del lugar. ¿Qué función cumple en el mundo? ¿Por qué es importante que el jugador pueda visitarlo? Si la respuesta es "para tener variedad geográfica" sin más, probablemente no merece ser modelado individualmente, puede ser celda de fondo sin memetario.

Segundo, listar los tres a cinco tags simbólicos más importantes del lugar. Estos son los que más fuerte afectan a quienes lo habitan. Para una taberna podrían ser bebida, secretos, indulgencia. Para una abadía podrían ser contemplación, orden, humildad.

Tercero, decidir los modificadores de costo asociados. Para cada tag simbólico, qué categorías de memes refuerza (modificadores negativos, los abarata) y qué categorías de memes choca (modificadores positivos, los encarece). Una taberna con tag bebida abarata indulgencia y conversación, encarece sigilo y disciplina_corporal.

Cuarto, escribir la descripción base del lugar y el prompt de narración. La descripción es lo que el motor pasa al LLM como contexto. El prompt de narración es la dirección estética sobre cómo el LLM debe tratar este lugar específicamente cuando narra escenas en él.

Quinto, sembrar secretos y objetos si el lugar amerita contenido descubrible. Esto vive en el archivo references/secretos-y-objetos.md.

## Recordatorios operativos

Cuando James trabaje en este territorio, dos cosas conviene tener presentes.

Primera, la fuerza del sistema viene de la consistencia. Si todos los lugares tienen modificadores genéricos y débiles, el sistema no produce efecto. Los lugares que producen arcos de personaje son los que tienen modificadores fuertes en categorías específicas. La abadía debe penalizar fuerte la violencia y subsidiar fuerte la contemplación. Si penaliza un poco y subsidia un poco, el efecto se diluye.

Segunda, no todos los lugares necesitan memetario simbólico complejo. Lugares de paso (un camino, una orilla) pueden tener memetario vacío o casi vacío. Solo los lugares narrativamente importantes (donde el jugador va a pasar tiempo significativo) necesitan modificadores robustos. Si te encontrás programando memetario simbólico para cada cuadrado del mapa, estás haciendo trabajo desperdiciado. Concentralo en los lugares que importan.
