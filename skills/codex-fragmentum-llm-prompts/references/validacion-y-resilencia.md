# Validación y resilencia — la capa que vuelve sostenible al sistema

Este archivo es referencia operativa para cuando estés programando o debuggeando la capa que maneja respuestas del LLM y errores asociados. Cubre cómo se valida que las respuestas sean utilizables, qué hacer cuando no lo son, cómo testear sin gastar tokens, y cómo cachear lo que se puede reusar. Asume que el SKILL.md principal de prompts ya está cargado.

Una nota de tono. Este archivo es probablemente menos filosófico que los anteriores. Mientras los archivos de tiers y de templates tocan decisiones arquitectónicas grandes con implicaciones conceptuales, este se ocupa de la plomería: validar, reintentar, cachear, mockear. Esa plomería no es glamorosa pero es lo que vuelve al sistema sostenible cuando se enfrenta al uso real, donde los LLMs fallan en formas inesperadas, las APIs tienen latencia, los modelos cambian de comportamiento entre versiones, y los costos se acumulan.

## Por qué la resilencia importa más de lo que parece

Cuando un programador imagina integrar un LLM, la imagen natural es del caso feliz: prompt va, respuesta vuelve, todo funciona. Esa imagen es correcta para la gran mayoría de las llamadas. Pero el sistema vive o muere por cómo maneja las que no entran en ese caso feliz.

El LLM puede devolver JSON malformado cuando le pediste estructura. Puede inventar campos que no estaban en el schema. Puede ignorar parte del prompt y responder a otra cosa. Puede tardar mucho y producir timeout. La API puede estar momentáneamente caída. El modelo puede haber sido actualizado sin aviso y haber cambiado su comportamiento sutil. Cualquiera de estos casos, mal manejado, deja al sistema en estado inconsistente o lo cuelga.

Para James trabajando solo en sesiones largas, un sistema que se rompe ocasionalmente no es solo molestia: es desincentivo a usarlo. Si cada vez que James se sienta a jugar tiene una probabilidad de que el sistema se rompa, va a evitar sentarse a jugar. La resilencia frente a fallas es lo que mantiene al proyecto usable a través del tiempo.

Y hay otra dimensión. La resilencia bien implementada vuelve auditables los problemas. Cuando algo falla, el sistema debería capturar suficiente información para diagnosticar después. Sin esa captura, los problemas se vuelven misteriosos: "a veces la mutación de rumores se pone rara, no sé por qué". Con captura, el problema se vuelve diagnosticable: "en estos siete casos donde la mutación falló, el LLM devolvió texto en lugar de JSON estructurado, y en seis de ellos el prompt tenía la misma característica X". Esa diferencia entre opaco y diagnosticable es lo que permite mejorar el sistema en lugar de pelearse con él.

## Validación con Pydantic como contrato

La pieza fundamental de la resilencia es la validación de respuestas estructuradas con Pydantic. La consigna es: cualquier respuesta del LLM que no sea texto libre debe pasar por validación antes de ser usada por el motor. Si la validación falla, el sistema decide qué hacer (retry, fallback, propagación del error), pero nunca se pasa al motor una respuesta no validada.

La razón es estructural. El motor del Codex asume que los datos que recibe son consistentes. Si el LLM devuelve un objeto con un campo faltante o un tipo incorrecto, y ese objeto se inserta en el grafo del mundo, el grafo queda inconsistente. Después, cuando otra parte del motor intenta usar ese nodo del grafo, falla en un lugar lejano del origen del problema, y diagnosticarlo se vuelve mucho más difícil. La validación temprana evita ese escenario.

Pydantic hace este trabajo de manera elegante. Definís un schema con las clases ya existentes en el proyecto (NodoVersion, PropuestaHito, MemeOperativo, etc.) y le pedís a Pydantic que valide la respuesta del LLM contra ese schema. Si la respuesta cumple el schema, Pydantic devuelve un objeto del tipo correcto, listo para usar. Si no cumple, levanta una ValidationError con detalle de qué está mal.

La parte más fina es cómo se le pide al LLM que devuelva en formato. Hay tres approaches que vale la pena conocer.

El approach más simple es pedirle al LLM en el prompt que devuelva JSON con cierto formato, y después parsear esa respuesta. Esto funciona bien con modelos modernos pero requiere instrucciones explícitas en el prompt: "devolvé tu respuesta como JSON con esta estructura". El problema es que el LLM puede agregar texto antes o después del JSON, lo que confunde al parser. Solución típica: usar regex o extraer el primer bloque JSON encontrado, ser tolerante con prefijos y sufijos.

El segundo approach usa la modalidad de tool use o function calling que algunos proveedores ofrecen. Le pasás al LLM un schema de la función que querés que llame y el LLM responde con argumentos validados contra el schema. Esto es más confiable que el approach simple pero requiere que el proveedor lo soporte y agrega complejidad al cliente.

El tercer approach usa la modalidad de structured output que algunos proveedores ofrecen explícitamente. Le pasás un schema y el modelo está garantizado por el proveedor de devolver algo que cumpla el schema. Es el más robusto pero también el menos universal.

Para Codex, mi recomendación práctica es empezar con el approach simple (instrucción de JSON en el prompt + parsing tolerante) porque funciona en todos los proveedores y tiene buena confiabilidad con los modelos modernos. Si se descubre que cierto tipo de llamada falla la validación con frecuencia, escalar a tool use o structured output para esa llamada específica. La uniformidad inicial vale más que la robustez óptima.

## Estrategia de retries

Cuando una respuesta del LLM falla la validación o produce error de API, la pregunta es: ¿reintentar, fallback, o propagar el error? La respuesta depende del tipo de fallo.

Para fallos de validación (la respuesta no cumple el schema esperado), el retry tiene sentido pero con una particularidad. No basta con hacer la misma llamada de nuevo, porque el LLM probablemente repita el mismo error. Lo que conviene es agregarle al prompt información sobre qué falló: "tu respuesta anterior no fue válida porque el campo X estaba faltante. Por favor, asegurate de incluir todos los campos requeridos en este formato: ...". Este retry con feedback tiene chance significativa de éxito porque le da al modelo información que no tenía.

Para fallos de API (timeout, error 5xx, rate limit), el retry es estándar con backoff exponencial. Esperás un poco, reintentás. Si después de dos o tres reintentos sigue fallando, hay un problema más profundo y conviene propagar el error.

Para fallos de contenido (la respuesta cumple el schema pero el contenido es claramente equivocado), la situación es más sutil. Detectar este tipo de fallo requiere lógica de validación adicional más allá del schema. Por ejemplo, si pediste una mutación de un rumor y el LLM devuelve un texto idéntico al original (cero mutación), el schema podría pasar pero el contenido es inútil. Esa validación de contenido se puede hacer programáticamente para casos obvios (similitud coseno entre origen y resultado mayor a 0.95 indica que no hubo mutación real) y en esos casos hacer retry.

La regla operativa para retries es máximo tres intentos en total. Después del tercer fallo, el sistema debería propagar el error y dejar que el motor decida qué hacer. Para algunas operaciones (como la mutación de un rumor en propagación pasiva durante downtime), el motor puede decidir simplemente no propagar ese rumor en ese tick y reintentar más tarde. Para otras (como la narración de un Score crítico), el motor puede decidir mostrarle al jugador un mensaje de "el sistema tuvo un problema, ¿querés reintentar la acción?".

## Manejo de errores en código

Para que la resilencia sea concreta, te muestro patrones de código que vale la pena seguir.

```python
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar
import time

T = TypeVar('T', bound=BaseModel)

class LLMResponseError(Exception):
    """Error genérico de respuesta del LLM."""
    pass

class LLMValidationError(LLMResponseError):
    """La respuesta no cumplió el schema esperado."""
    pass

class LLMContentError(LLMResponseError):
    """La respuesta cumple schema pero el contenido es inválido."""
    pass


def call_with_retries(
    client: LLMClient,
    prompt: str,
    schema: Type[T],
    tier: int,
    content_validator: Optional[Callable[[T], bool]] = None,
    max_attempts: int = 3
) -> T:
    """
    Llama al LLM con validación y retries automáticos.
    Si content_validator se pasa, además de validar el schema valida el contenido.
    """
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            # Si es retry de validación, agregamos el feedback al prompt
            actual_prompt = prompt
            if attempt > 0 and isinstance(last_error, ValidationError):
                actual_prompt = prompt + f"\n\nTu respuesta anterior no fue válida porque: {last_error}\n" \
                                         f"Por favor, devolvé una respuesta que cumpla este formato exactamente."
            
            response = client.structured(actual_prompt, schema, tier)
            
            # Validación de contenido si aplica
            if content_validator and not content_validator(response):
                raise LLMContentError(f"Contenido inválido en intento {attempt+1}")
            
            return response
            
        except ValidationError as e:
            last_error = e
            log_validation_failure(prompt, schema, str(e), attempt)
            
        except LLMContentError as e:
            last_error = e
            log_content_failure(prompt, schema, response, attempt)
            
        except Exception as e:
            # Error de API u otro
            last_error = e
            log_api_failure(prompt, str(e), attempt)
            time.sleep(2 ** attempt)  # backoff exponencial
    
    # Si llegamos acá, todos los intentos fallaron
    raise LLMResponseError(f"Falló después de {max_attempts} intentos. Último error: {last_error}")
```

La estructura es ilustrativa, podés tunearla. Lo importante son los principios: retry con feedback en validación, backoff en errores de API, validación de contenido como capa adicional, propagación del error después del límite, logging estructurado de cada fallo para diagnóstico posterior.

## El sistema de logging para diagnóstico

Una pieza de infraestructura que vale la pena programar desde el día uno: logging estructurado de cada llamada al LLM, sus inputs, sus outputs, sus errores, su latencia, su costo estimado.

La razón es práctica. Cuando algo va mal en el sistema, tenés que poder responder preguntas concretas. ¿Cuántas veces falló la validación esta semana? ¿En qué templates se concentran las fallas? ¿Hay algún modelo que está fallando más que los otros? ¿La latencia subió últimamente? Sin logging, todas estas preguntas son misterios. Con logging, son consultas a una base de datos.

El logging debería capturar al menos los siguientes campos por cada llamada: timestamp, template usado (identificador), tier asignado, modelo concreto que se usó, prompt completo que se envió, respuesta cruda recibida, si la validación pasó o falló (y por qué), si se hizo retry y cuántos, latencia en milisegundos, tokens de input y output, costo estimado en dólares. Todo eso se almacena, idealmente en un archivo JSONL local que se puede analizar con scripts simples.

El volumen de data puede crecer rápido. Una sesión de una hora puede generar megabytes de logs. Esto está bien para diagnóstico durante desarrollo. Para producción a largo plazo, conviene rotar los logs (mantener solo los últimos N días o tamaño M, archivar el resto).

Una optimización importante es no loggear el prompt completo en cada llamada si los prompts son largos y repetitivos. Se puede loggear un hash del prompt y mantener una tabla de hashes a prompts que se actualiza cuando aparece un hash nuevo. Eso reduce el volumen de logs sin perder la capacidad de diagnóstico.

## El cliente mock para tests

La sostenibilidad del proyecto requiere que se puedan correr tests automáticos sin gastar tokens. La pieza que hace esto posible es el cliente mock.

El cliente mock es una implementación de la interfaz LLMClient que no llama a ninguna API. En lugar de eso, devuelve respuestas pre-grabadas según una lógica predefinida. Hay varias estrategias para programar esa lógica.

La estrategia más simple es un dict que mapea hashes de prompts a respuestas. Cuando llega una llamada, se calcula el hash del prompt y se busca en el dict. Si está, se devuelve la respuesta. Si no está, se levanta error indicando que el test debe pre-grabar la respuesta para ese caso.

La estrategia más flexible es una lista de "matchers" donde cada matcher es una función que evalúa si el prompt coincide con cierto patrón y, si coincide, devuelve cierta respuesta. Esto te permite, por ejemplo, tener un matcher que dice "para cualquier prompt que contenga 'mutación de rumor', devolvé esta respuesta de mutación genérica". Es más laxo pero más útil para cubrir muchos tests con pocas respuestas pre-grabadas.

La estrategia más rica es grabar respuestas reales del LLM durante una sesión de "captura" y reusarlas en tests. El sistema intercepta las llamadas reales y las guarda en un archivo. En tests, el mock client carga ese archivo y devuelve las respuestas correspondientes. Esta estrategia produce tests más realistas porque las respuestas son lo que el LLM realmente devolvería, no lo que el programador imagina.

Para el MVP, mi recomendación es empezar con la estrategia simple (dict de hashes a respuestas) y evolucionar a la rica si aparece la necesidad. Lo importante es que los tests sean rápidos (sin latencia de red) y baratos (sin tokens).

Cuando programes tests, conviene que cubran al menos estos casos: caso feliz donde el LLM devuelve respuesta válida, caso de fallo de validación que requiere retry con feedback, caso de fallo de API que requiere retry con backoff, caso de fallo persistente que debe propagar error. Cubrir estos cuatro casos te da confianza de que la capa de resilencia funciona, sin tener que descubrirlo en producción.

## El sistema de caché para respuestas reusables

Algunas respuestas del LLM se pueden reusar entre llamadas porque su input es idéntico. Por ejemplo, la descripción de un objeto que el personaje ve por primera vez puede generarse una vez y reusarse cada vez que ese personaje vuelva a ver el objeto. La narración de un lugar visto desde un memetario específico puede tener componentes cacheables.

El caché se programa con una clave derivada del input. La clave debería incluir el template usado, el modelo (porque distintos modelos producen distintos outputs), y un hash del contexto relevante. Si la misma combinación de template + modelo + contexto aparece de nuevo, se devuelve la respuesta cacheada en lugar de llamar al LLM.

La pregunta importante es qué llamadas son cacheables y cuáles no. La regla general: si el output depende del estado actual del mundo (que cambia constantemente), no es cacheable. Si depende solo de información estática (descripciones de cosas que no cambian, mutaciones que no dependen del momento), es cacheable.

En la práctica, la mayoría de las llamadas en Codex no son cacheables porque dependen del estado dinámico. Pero hay algunas excepciones que vale la pena identificar y cachear: descripciones iniciales de NPCs tibios cuando se encienden, descripciones base de lugares vistos por primera vez, traducciones de tags simbólicos a memetarios inferidos.

Para el MVP, el caché es opcional. Para fases posteriores donde los costos importan más, vale la pena agregarlo selectivamente para las operaciones que más se benefician.

## El monitoreo de salud del sistema

Una práctica que vale la pena adoptar a partir de fase 2 (cuando James empiece a usar el sistema regularmente): un dashboard simple de salud del sistema que James pueda consultar para ver si todo está funcionando bien.

El dashboard puede ser un script simple que lee los logs y reporta métricas: tasa de éxito de llamadas (porcentaje que pasaron validación al primer intento), tasa de retry (porcentaje que requirieron retry), latencia promedio por tier, costo por hora de juego, distribución de fallos por template, modelos usados con frecuencia. Estas métricas, vistas a lo largo del tiempo, revelan problemas antes de que se vuelvan crisis.

Por ejemplo, si la tasa de retry de cierto template empieza a subir consistentemente a lo largo de varias sesiones, eso es señal de que algo cambió: puede ser que el modelo se actualizó y cambió comportamiento, puede ser que el template empezó a recibir contexto más complejo del esperado, puede ser que un proveedor está degradando la calidad. Sin monitoreo, James se entera de estos problemas cuando el sistema se rompe. Con monitoreo, puede actuar antes.

El dashboard no tiene que ser sofisticado. Un script Python que genera un reporte HTML estático con gráficos simples es suficiente. Lo importante es que James pueda mirarlo periódicamente y tener una imagen de la salud del sistema.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera: la resilencia es invisible cuando funciona. James no va a notar que la capa de resilencia existe cuando todo va bien. Solo la nota cuando algo falla y el sistema sigue funcionando en lugar de romperse. Esto significa que invertir en resilencia se siente como invertir en algo que no se ve, lo cual puede frustrar. La realidad es que es la pieza que vuelve sostenible al proyecto a largo plazo, especialmente cuando James no está mirando.

Segunda: cada error que se loggea es información valiosa. La tentación natural cuando aparece un error inesperado es resolverlo y olvidarlo. La práctica correcta es registrarlo, entender por qué pasó, y considerar si es síntoma de un problema más profundo. A veces sí lo es. A veces no. Pero la información acumulada de los errores te muestra patrones que ningún error individual revelaría.

Tercera: cuando el sistema se rompe en producción, los primeros lugares a mirar son los logs y las métricas, no el código. El código probablemente esté bien (si los tests pasan). Lo que cambió suele estar en los datos: el LLM cambió, el prompt está siendo invocado con contexto que no se anticipó, el modelo de un proveedor degradó. Los logs y las métricas te llevan al problema concreto. Sin ellos, todo es adivinanza.
