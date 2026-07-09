# Secretos sembrados y objetos del mundo

Este archivo es referencia operativa para cuando estés diseñando o programando los dos sistemas que pueblan los lugares con contenido descubrible: los secretos sembrados que se activan por condiciones, y los objetos cargados narrativamente con sus reinos, ciclos de vida e interacciones. Asume que el SKILL.md principal de cartografía ya está cargado.

## Por qué los dos sistemas viven juntos en este archivo

Una decisión de organización: secretos y objetos se podrían haber separado en dos archivos pero los junté porque comparten una premisa común. Ambos son contenido autoral preescrito que James planta en el mundo y que el jugador descubre durante el juego. Ambos pueden tener prompts narrativos asociados que guían al LLM cuando los narra. Ambos son la materialización de la idea de que el mundo es algo que se descubre, no algo que se genera procedurally al llegar.

Cuando estés trabajando en diseñar contenido del mundo (no en programar el motor), probablemente vas a tocar los dos sistemas a la vez. Por eso conviene tenerlos juntos.

## Por qué el contenido se siembra y no se genera

Vale la pena hacer explícita una decisión que aparece en muchos puntos del proyecto: el contenido importante del mundo lo escribe James como autor, no lo genera el LLM en tiempo real cuando el jugador llega.

La razón es de calidad. Un LLM que genera contenido al vuelo produce material de calidad variable: a veces brillante, a veces genérico, a veces erróneo. Para escenografía de paso (la descripción de un árbol cualquiera, el aspecto de un camino) eso está bien. Para contenido que carga peso narrativo (los secretos importantes, los objetos significativos), la varianza es inaceptable.

La estrategia de Codex es híbrida. James escribe el contenido importante: define los secretos sembrados, escribe los objetos cargados, redacta los prompts narrativos asociados. El LLM se invoca para dos cosas distintas: para narrar el descubrimiento del contenido cuando ocurre (refractado por el cristal del personaje que descubre), y para generar contenido atmosférico de paso que no merece ser preescrito.

Esto implica que James va a hacer trabajo de worldbuilding manual significativo. Pero ese trabajo es lo que vuelve singular al mundo. Un mundo enteramente generado se siente genérico. Un mundo con piezas curadas, conectadas por generación atmosférica, se siente habitado.

## La estructura de un secreto sembrado

Un secreto es información que existe latente en una celda específica y que se revela cuando un agente entra y se cumplen ciertas condiciones. Es el mecanismo principal por el cual el mundo tiene cosas para descubrir.

```python
class SecretoSembrado(BaseModel):
    id: str
    descripcion: str  # contenido del secreto
    condiciones_activacion: dict
    chance_descubrimiento: float = Field(ge=0, le=1)
    prompt_narracion: str
    descubierto_por: list[str] = []
    estado: Literal["dormido", "descubierto", "agotado"] = "dormido"
```

Las condiciones de activación son un diccionario flexible que el motor evalúa. Pueden incluir tiempo (solo de noche, solo en ciertas estaciones), estado del agente (debe llevar cierto objeto, debe tener cierta marca, debe haber visitado el lugar antes), eventos del mundo (solo después de cierto evento histórico). El motor evalúa todas las condiciones y, si todas se cumplen, hace una tirada con la chance de descubrimiento. Si sale, el secreto pasa de dormido a descubierto.

```python
condiciones_activacion = {
    "tiempo": "noche",
    "marca_requerida": None,
    "objeto_requerido": None,
    "evento_previo": None
}
```

El campo prompt_narracion es la instrucción al LLM sobre cómo narrar el descubrimiento del secreto cuando ocurre. James lo escribe como autor del mundo. Por ejemplo, para un secreto de cueva con pinturas rupestres: "Cueva con pinturas rupestres. Símbolos de un dios olvidado. La narración debe sentir asombro y antigüedad. Que el personaje no entienda completamente lo que ve, que haya algo que se le escapa."

El campo estado tiene tres valores. Dormido es el default antes de descubrirse. Descubierto es cuando ya se descubrió pero podría volver a ser relevante (un secreto compartible, donde el primer descubridor lo difunde). Agotado es cuando el secreto ya cumplió su función narrativa y no debe reactivarse (un evento único que solo ocurre una vez).

## Cómo se evalúan las condiciones

Cuando un agente entra a una celda, el motor evalúa cada secreto sembrado en esa celda contra el contexto actual. Para cada secreto, primero se chequea que su estado sea dormido (los descubiertos y agotados se saltean). Después se evalúan las condiciones una por una.

```python
def evaluar_secretos_al_entrar(agente: Agente, lugar: Lugar):
    for secreto in lugar.secretos:
        if secreto.estado != "dormido":
            continue
        if not condiciones_cumplidas(secreto.condiciones_activacion, agente, lugar):
            continue
        if random.random() > secreto.chance_descubrimiento:
            continue
        # Descubierto
        revelar_secreto(secreto, agente, lugar)
        secreto.estado = "descubierto"
        secreto.descubierto_por.append(agente.id)
```

La función condiciones_cumplidas evalúa cada condición contra el estado actual del agente, del lugar, del mundo. La chance_descubrimiento agrega un componente probabilístico: incluso si todas las condiciones se cumplen, no siempre el secreto se revela. Esto modela el azar real del descubrimiento (estás en el lugar correcto en el momento correcto, pero no necesariamente prestás atención al detalle correcto).

Una vez descubierto, revelar_secreto invoca al LLM con el prompt narrativo del secreto, refractado por el cristal del personaje que descubre. El secreto se convierte en información en el grafo del mundo (un hecho del mundo nuevo o una versión nueva de uno existente), lo cual lo hace transmisible: el personaje puede ahora contárselo a otros.

## La estructura de un objeto del mundo

Los objetos del mundo son entidades que existen en celdas específicas o son portadas por agentes. La estructura básica es:

```python
class Objeto(BaseModel):
    id: str
    nombre: str
    reino: list[str]  # uno o varios
    descripcion_base: str
    prompt_narracion: str
    lugar_actual_id: Optional[str] = None
    portado_por: Optional[str] = None
    categoria: Literal["empty", "mundano", "ritual", "magico", "divino"] = "empty"
    memetario_simbolico: list[str] = []
    interacciones: list[InteraccionObjeto] = []
    ciclo_vida: Optional[CicloVida] = None
    atributos: dict = {}
```

El campo categoria indica el peso narrativo del objeto. Empty es el default para objetos que casi no interesan (una piedra cualquiera). Mundano es para objetos cotidianos pero con alguna utilidad (una jarra de vino, un cuchillo). Ritual es para objetos con función ceremonial pero sin propiedades intrínsecas (un cáliz, un incensario). Mágico es para objetos con propiedades sobrenaturales pero acotadas (un amuleto que protege, una piedra que ilumina). Divino es para objetos vinculados directamente a un dios (la corona de la diosa del invierno, una reliquia santa).

Para el MVP, la mayoría de los objetos son empty o mundano. Los objetos cargados (ritual, mágico, divino) son raros y deben diseñarse con cuidado.

## Los reinos y la hibridación

El campo reino clasifica al objeto según la categoría ontológica a la que pertenece. Esta clasificación no es decoración taxonómica, es información que el motor usa para decidir cómo se comportan los objetos.

Los reinos primarios son mineral, vegetal, animal, humanoide, divino, espectral, conceptual. Cada uno representa una categoría distinta de existencia. Una piedra es mineral. Un árbol es vegetal. Un fantasma es espectral. Un rumor reificado puede ser conceptual.

Lo más interesante son los reinos compuestos. Una flor de cristal es mineral-vegetal. Una criatura mitológica como un grifo es animal-divino. Un poseso es humanoide-espectral. Un dogma es conceptual-divino. La hibridación es donde se concentra lo numinoso del mundo: cosas que violan la lógica natural y por eso cargan significado divino o cósmico.

Mecánicamente, las reglas de cada reino se heredan parcialmente al objeto. Una flor de cristal puede ser destruida por golpes (regla mineral) pero también marchitarse si se separa de la luz (regla vegetal). Un grifo puede ser herido como animal pero también requiere ofrendas para mantener su benevolencia (regla divina). El motor consulta los reinos del objeto para decidir cómo aplicar las reglas en cada interacción.

Esto te abre una mecánica narrativa potente: los hechos imposibles del mundo se explican por hibridación de reinos. Tu mundo entero puede tener una "tabla periódica" de hibridaciones que sugiere dónde está lo extraordinario.

## Las interacciones de objeto

Algunos objetos tienen interacciones predefinidas con ciertos tipos de actores. Estas interacciones son la materialización de la idea de "química de significados" entre el memetario del objeto y el del agente.

```python
class InteraccionObjeto(BaseModel):
    actor_categoria: str  # "bendecido_diosa_invierno", "hereje", "pj"
    trigger: str  # "pisa", "toma", "ofrece", "rompe"
    efecto_descripcion: str
    efecto_mecanico: dict
    frecuencia: Literal["siempre", "una_vez", "una_vez_por_persona", "diaria"]
```

El ejemplo canónico que James propuso es la flor de cristal que solo florece para los bendecidos por la diosa del invierno. La interacción se ve así: actor_categoria es "bendecido_diosa_invierno", trigger es "pisa_el_pasto", efecto_descripcion es "el pasto le regala una flor de cristal", efecto_mecanico es agregar el objeto flor_cristal al inventario del personaje, frecuencia es "una_vez_por_persona".

Cuando un agente activa un trigger sobre el objeto, el motor evalúa todas las interacciones del objeto. Para cada una, chequea si el agente cumple la categoría del actor (mediante tags simbólicos del agente o memes activos). Si cumple, aplica el efecto. Si no, esa interacción se saltea.

Esto produce una mecánica de "química de significados". Los objetos cargados reaccionan diferencialmente según con qué memetario se cruzan. Un mismo pasto produce flor de cristal para un bendecido pero se marchita al paso de un hereje.

## Los ciclos de vida

Algunos objetos (especialmente vegetales y aspectos de lugares) tienen ciclos de vida que avanzan con el tiempo. Esto modela los cambios cosmológicos y estacionales del mundo.

```python
class CicloVida(BaseModel):
    objeto_id: str
    estados_por_estacion: dict[str, str]
    estado_actual: str
    vinculo_divino: Optional[str] = None
```

El ejemplo canónico es el pasto de la llanura que florece en invierno y se marchita en las otras estaciones. Los estados_por_estacion serían algo como:

```python
{
    "primavera": "marchito_dorado",
    "verano": "marchito_dorado",
    "otono": "marchito_dorado",
    "invierno": "florece_anomalo_verde_brillante"
}
```

El campo vinculo_divino es lo más interesante: si está presente, el ciclo del objeto depende del estado del dios al que está vinculado. Si la diosa del invierno pierde fe (su clock divino avanza), el florecimiento anómalo del pasto se desestabiliza. Si la diosa muere, el ciclo entero se rompe: el pasto puede quedar en estado permanente o desaparecer.

Esto materializa la consigna del manifiesto sobre descalibración de la realidad cuando muere un dios. La cosmología del mundo está físicamente presente en sus objetos a través de los ciclos vinculados.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera, no satures el mundo de objetos cargados. La regla práctica: la mayoría de los objetos son categoría empty o mundano (escenografía y utilería). Los objetos ritual, mágico, divino son raros (uno o dos por celda significativa). Si te encontrás diseñando muchos objetos cargados, estás invirtiendo esfuerzo donde no rinde y diluyendo el peso narrativo de los pocos objetos verdaderamente importantes.

Segunda, los secretos sembrados deben estar bien distribuidos por dificultad. Si todos los secretos son fáciles de descubrir (chance alta, condiciones laxas), el jugador los descubre todos rápido y el mundo pierde misterio. Si todos son difíciles (chance baja, condiciones específicas), el jugador puede no descubrir ninguno y el mundo se siente vacío. Mi recomendación es una distribución piramidal: muchos secretos fáciles de superficie, algunos secretos medios que requieren cierto esfuerzo, pocos secretos profundos que requieren convergencia rara de condiciones.

Tercera, los prompts narrativos asociados a secretos y objetos importantes son donde James pone su voz como autor. Un mismo secreto narrado con prompt genérico se siente como wikipedia. Narrado con prompt específico que da dirección estética se siente como literatura. Tomate tiempo para escribir esos prompts, son donde se distingue Codex de cualquier otro proyecto procedurally generated.
