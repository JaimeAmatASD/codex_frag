# Tiers de modelos LLM — estrategia de routing y abstracción del cliente

Este archivo es referencia operativa para cuando estés programando o diseñando la arquitectura de cómo Codex Fragmentum invoca a los modelos de lenguaje. Cubre tres temas conectados: la clasificación de llamadas en tiers según su peso narrativo, la abstracción del cliente que permite cambiar de proveedor, y la economía concreta de cuánto cuesta operar el sistema. Asume que el SKILL.md principal de prompts ya está cargado.

## Por qué la estrategia de tiers existe

Vale la pena empezar con la motivación, porque sin entenderla bien la implementación se vuelve arbitraria.

Una sesión de juego de una hora en Codex puede fácilmente disparar entre treinta y cien llamadas al LLM. Free play tiene una llamada por turno (digamos veinte por hora). Cada Score puede tener tres a cinco llamadas (la narración del intento, el cálculo de consecuencias, eventualmente la propuesta de hito biográfico). Cada propagación de rumor entre NPCs en el grafo es una llamada. Los downtimes generan crónicas que pueden ser una llamada larga o varias cortas. Las intervenciones divinas, las narraciones de hitos, los resúmenes de time-jump son llamadas pesadas. Todo eso se suma rápidamente.

Si todas esas llamadas usaran un modelo de tier alto (digamos Sonnet 4.6 o Gemini 2.5 Pro), una sesión de una hora podría costar varios dólares. Multiplicado por las horas de juego que James espera tener (decenas o cientos a lo largo de meses), el proyecto se vuelve insostenible económicamente. No es solo cuestión de presupuesto: es cuestión de viabilidad. Un proyecto que cuesta cinco dólares la hora de uso es un proyecto que sus usuarios van a abandonar por costo, no por calidad.

La alternativa opuesta también falla. Si todas las llamadas usaran el modelo más barato disponible (Gemini Flash gratuito o equivalente), los momentos que requieren prosa cuidada, refracción sutil, narración climática, se sentirían planos. El jugador termina la sesión sin haber tenido un solo momento memorable porque ningún momento tuvo el modelo capaz de producirlo.

La estrategia de tiers es el camino del medio: clasificar cada llamada según su peso narrativo y rutearla al modelo apropiado. La mayoría de las llamadas son de bajo peso (descripciones de paso, NPCs incidentales, mutaciones menores) y pueden usar modelos baratos sin perder calidad perceptible. Las pocas llamadas que son de alto peso (narraciones de momentos climáticos, refracciones complejas en hitos biográficos, resúmenes de períodos largos) usan modelos buenos y producen los momentos que el jugador recuerda.

Esto no es optimización prematura: es la única forma de que el proyecto funcione. Cuando James programe cualquier nueva llamada al LLM, la pregunta arquitectónica primaria es "¿qué tier?", no "¿qué modelo?". El tier se mantiene estable aunque cambien los modelos disponibles.

## Los cuatro tiers y sus criterios

Para Codex propongo cuatro tiers que cubren el rango necesario sin proliferación innecesaria. Los nombres son arbitrarios pero los criterios deberían quedar claros.

Tier 0 es para llamadas triviales donde el output mínimo es suficiente. Descripción de un árbol, una piedra, un objeto inanimado que el personaje pasa al lado. Generación de un NPC tibio cuando se enciende. Eventos atmosféricos sin peso narrativo (el ruido del mar, el frío del amanecer, la luz que entra por la ventana). El criterio para asignar tier 0 es: si esta llamada saliera vacía o defectuosa, ¿lo notaría el jugador? Si la respuesta es probablemente no, es tier 0. Modelos apropiados: Gemini Flash gratuito, Haiku 4.5, o cualquier modelo local que tengas disponible. Costo objetivo: cero o casi cero.

Tier 1 es para llamadas operativas con peso narrativo moderado. Refracción de información cuando un rumor pasa entre NPCs secundarios. NPCs con personalidad pero sin peso dramático actual respondiendo en free play. Mutaciones de rumor en el grafo. Decisiones autónomas de NPCs principales en momentos no críticos. El criterio es: ¿esta llamada va a aparecer directamente en lo que el jugador lee, o es operación interna del sistema con poco impacto experiencial? Si es interna pero importa para coherencia, tier 1. Modelos apropiados: Gemini 2.0 Flash, Haiku 4.5, o equivalentes. Costo objetivo: un orden de magnitud menos que tier 2.

Tier 2 es para llamadas dramáticas con peso narrativo alto. Narración de Scores incluyendo sus consecuencias. Diálogos del PJ del jugador con NPCs principales. Resúmenes de downtime largos. Refracción de información cuando el receptor es el PJ. Generación de propuestas de hitos biográficos. El criterio es: ¿el jugador va a leer esto y va a importarle cómo está escrito? Si la respuesta es sí, es tier 2. Modelos apropiados: Sonnet 4.6 o 4.7, Gemini 2.5 Pro. Es el tier de trabajo más común en momentos donde el jugador está enganchado.

Tier 3 es para llamadas climáticas donde la calidad literaria define el momento. Resoluciones cosmológicas (un dios muere, la realidad se descalibra). Hitos biográficos profundos del PJ del jugador. Narraciones de muertes de personajes con peso emocional. Crisis biográficas (modificación de PF). Aperturas y cierres de arcos narrativos grandes. Estos momentos son los que el jugador va a recordar y contar a otros. El criterio es: ¿este momento tiene que valer por sí solo como pieza literaria? Si sí, tier 3. Modelos apropiados: Opus 4.7, Gemini 2.5 Pro deep reasoning, o lo mejor que esté disponible al momento. Costo alto pero infrecuente.

Una regla de proporción aproximada que vale la pena tener en mente. En una hora típica de juego, esperarías ver algo así como cuarenta llamadas tier 0, treinta llamadas tier 1, ocho a doce llamadas tier 2, y cero o una llamada tier 3. Esa distribución es lo que hace que el costo total sea manejable: el tier 0 es prácticamente gratis, el tier 1 es barato, el tier 2 es donde se concentra el grueso del costo pero está acotado, el tier 3 aparece raramente. Si te encontrás con una distribución muy distinta (digamos, muchas llamadas tier 2 por hora), revisá si efectivamente cada una merece ese tier o si algunas pueden bajarse.

## La asignación de tier no es responsabilidad del template

Una decisión de diseño que vale la pena explicitar: el tier no se decide en el template del prompt, se decide en el código que invoca al LLM. Esto importa porque significa que el mismo template puede llamarse en distintos tiers según el contexto.

Por ejemplo, el template de refracción de información se usa siempre que un personaje recibe información de otro. Si los dos personajes son NPCs secundarios sin peso dramático actual, la llamada se rutea a tier 1. Si uno de los dos es el PJ del jugador, la misma operación con el mismo template se rutea a tier 2 porque ahora va a aparecer directamente en lo que el jugador lee. Si la información que se transmite es un hito biográfico mayor que el PJ está recibiendo, podría ser tier 3.

La función que decide el tier vive en el código del motor, no en el template. Recibe el contexto de la llamada (qué tipo de operación es, qué personajes están involucrados, qué peso narrativo tiene el momento) y devuelve el tier apropiado. Esa función puede ser un conjunto de reglas explícitas, una tabla de decisión, o algo más sofisticado en el futuro. Para el MVP basta con reglas simples y conviene mantenerlas simples para poder auditarlas.

Cuando programes esta función, conviene loggear cada decisión de tier. Esto te permite después analizar la distribución de tiers en sesiones reales y verificar si se ajusta a las expectativas. Si descubrís que el sistema está rutando demasiadas llamadas a tier 2, podés ajustar las reglas para bajar algunas a tier 1.

## La abstracción del cliente

Ahora que tenés claro el qué (cuatro tiers) y el cuándo (decisión por contexto), viene el cómo arquitectónico. La pieza clave es la abstracción del cliente de LLM detrás de una interfaz propia.

La razón es práctica. Si cada parte del código que invoca al LLM lo hace directamente con la SDK de Anthropic o de Google, cambiar de proveedor o usar varios simultáneamente requiere reescribir todas esas invocaciones. Si en cambio toda invocación pasa por una interfaz tuya, cambiar de proveedor afecta solo la implementación de la interfaz, no el código del motor.

La interfaz tiene una forma simple. Es una clase abstracta de Python con un puñado de métodos: uno para narración libre (devuelve texto), uno para respuesta estructurada (devuelve un objeto Pydantic validado), opcionalmente uno para estimar costo antes de llamar. Las implementaciones concretas heredan de esta clase: GeminiClient, AnthropicClient, MockClient. Cada implementación maneja los detalles del proveedor (autenticación, formato de mensaje, parsing de respuesta) pero expone la misma interfaz al motor.

El cliente abstracto recibe el tier como parámetro en cada llamada. Internamente, mapea el tier a un modelo concreto disponible. Ese mapeo puede vivir en configuración (un archivo YAML o un dict en código) y se puede cambiar sin tocar el motor. Esto es importante porque los modelos disponibles cambian con el tiempo: hoy Sonnet 4.6 es la opción para tier 2, en seis meses puede ser Sonnet 4.8 o algo equivalente. El mapeo se actualiza, el motor sigue funcionando.

Una decisión arquitectónica importante: el cliente abstracto puede usar implementaciones diferentes para tiers diferentes. Por ejemplo, podés mapear tier 0 y tier 1 a Gemini (porque Google ofrece tier gratuito generoso para Flash) y tier 2 y tier 3 a Anthropic (porque Sonnet y Opus son superiores en calidad narrativa). El cliente abstracto tiene que ser capaz de orquestar esa heterogeneidad sin que el motor lo sepa.

El cliente mock es probablemente el componente más subestimado de toda esta arquitectura. Sirve para testing: en lugar de llamar a APIs reales en cada test, el mock devuelve respuestas pre-grabadas. Esto permite testear el flujo del motor sin gastar tokens, sin depender de conectividad, sin sufrir flakiness por variaciones del modelo. Cuando programes la abstracción, programá el mock primero y los clientes reales después. El mock guía el diseño de la interfaz porque te fuerza a pensar qué mínimo necesitás.

## La estructura concreta del cliente

Para que sea operativo, te dejo la estructura concreta que conviene seguir. Es Python con type hints y Pydantic.

```python
from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMClient(ABC):
    """Interfaz abstracta para invocar modelos de lenguaje."""
    
    @abstractmethod
    def narrate(self, prompt: str, tier: int) -> str:
        """Llamada para narración libre, devuelve texto."""
        pass
    
    @abstractmethod
    def structured(self, prompt: str, schema: Type[T], tier: int) -> T:
        """Llamada para respuesta estructurada, devuelve objeto Pydantic validado."""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt: str, tier: int) -> float:
        """Estimación de costo en dólares para esta llamada."""
        pass


class GeminiClient(LLMClient):
    """Implementación que usa Gemini para tiers 0 y 1."""
    
    TIER_TO_MODEL = {
        0: "gemini-1.5-flash",  # gratuito o casi
        1: "gemini-2.0-flash",
        2: "gemini-2.5-pro",
        3: "gemini-2.5-pro",  # podría ser deep reasoning
    }
    
    def narrate(self, prompt: str, tier: int) -> str:
        # Llamada concreta a la API de Gemini
        ...


class AnthropicClient(LLMClient):
    """Implementación que usa Anthropic para tiers 2 y 3."""
    
    TIER_TO_MODEL = {
        0: "claude-haiku-4-5",
        1: "claude-haiku-4-5",
        2: "claude-sonnet-4-6",
        3: "claude-opus-4-7",
    }
    
    def narrate(self, prompt: str, tier: int) -> str:
        ...


class HybridClient(LLMClient):
    """Cliente que rutea cada tier al proveedor apropiado."""
    
    def __init__(self, gemini: GeminiClient, anthropic: AnthropicClient):
        self.gemini = gemini
        self.anthropic = anthropic
    
    def narrate(self, prompt: str, tier: int) -> str:
        if tier <= 1:
            return self.gemini.narrate(prompt, tier)
        else:
            return self.anthropic.narrate(prompt, tier)


class MockClient(LLMClient):
    """Cliente para tests, devuelve respuestas pre-grabadas."""
    
    def __init__(self, responses: dict):
        self.responses = responses
    
    def narrate(self, prompt: str, tier: int) -> str:
        # Busca respuesta pre-grabada por hash del prompt o regla
        ...
```

Esta estructura es mínima pero suficiente para empezar. Lo importante es la separación de responsabilidades: el motor habla con la interfaz abstracta, las implementaciones concretas manejan los detalles de cada proveedor, el cliente híbrido orquesta entre ellas, el mock permite tests.

## La economía concreta

Para que las decisiones de tier no sean abstractas, vale la pena tener números concretos en mente. Los costos son aproximados (varían según proveedor y cambian con el tiempo) pero el orden de magnitud es estable.

Una llamada tier 0 cuesta entre cero y un décimo de centavo. Asumiendo cuarenta por hora, eso son tres a cuatro centavos por hora. Insignificante.

Una llamada tier 1 cuesta entre uno y tres centavos. Asumiendo treinta por hora, eso son sesenta a noventa centavos por hora. Manejable.

Una llamada tier 2 cuesta entre cinco y veinte centavos según longitud y modelo. Asumiendo diez por hora, eso son cincuenta centavos a dos dólares por hora. Acá es donde se concentra el costo.

Una llamada tier 3 cuesta entre veinte y cincuenta centavos. Asumiendo media a una por hora, eso son diez a cincuenta centavos por hora.

Sumando estimación realista: una hora de juego puede costar entre uno y tres dólares. Para un proyecto que James va a usar quizá cien horas en un año, eso son cien a trescientos dólares anuales en LLM. Es un costo manejable para un proyecto personal serio, especialmente si se considera el valor que James está obteniendo del proceso de construcción más allá del juego en sí.

Lo importante de tener estos números es que te dan un benchmark contra el cual evaluar el sistema en producción. Si James reporta que una sesión de una hora costó diez dólares, hay un problema: alguna llamada está siendo ruteada al tier equivocado, o se están haciendo más llamadas de las necesarias, o algo en el sistema se descontroló. El número total de costo por hora es un indicador de salud del sistema.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera: la decisión de qué tier usar es decisión arquitectónica recurrente. Cada vez que aparezca una nueva operación que invoca al LLM, la pregunta "¿qué tier?" es la primera que conviene responder, antes de escribir el template o decidir el modelo. Si no podés justificar el tier, probablemente no entendés todavía el peso narrativo de la operación.

Segunda: el costo del LLM se mide en sesiones reales, no en estimaciones. Conviene loggear cada llamada con su tier, su modelo concreto, su input/output token count y su costo estimado. Después de las primeras sesiones de juego, James va a tener data real sobre la distribución de tiers y podrá ajustar las reglas. Sin logging, todo es especulación.

Tercera: cambiar de modelo dentro de un tier no debería requerir cambios en el motor. Si Anthropic saca Sonnet 4.8 que es mejor que 4.6, James actualiza el mapeo TIER_TO_MODEL en el AnthropicClient y todo el motor se beneficia automáticamente. Esa flexibilidad arquitectónica es lo que hace que el proyecto sea sostenible en el tiempo, mientras los modelos siguen evolucionando.
