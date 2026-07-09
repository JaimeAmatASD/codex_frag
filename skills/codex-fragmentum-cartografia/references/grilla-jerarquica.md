# Grilla espacial jerárquica — la arquitectura del espacio

Este archivo es referencia operativa para cuando estés programando o diseñando la arquitectura espacial del proyecto. Cubre cómo se modelan las celdas, cómo se organizan jerárquicamente, cómo se cargan en memoria de manera lazy, cómo se calcula la propagación según el nivel. Asume que el SKILL.md principal de cartografía ya está cargado.

## Por qué jerárquica y no plana

Vale la pena empezar por la motivación porque es la decisión de diseño más fundamental del territorio. Una grilla plana de millones de celdas es inmanejable computacionalmente. Si el mundo entero estuviera modelado como una grilla bidimensional uniforme, cargar el estado del mundo en memoria sería imposible y simular su evolución sería inviable.

La grilla jerárquica resuelve este problema con una estructura recursiva. El mundo tiene celdas de nivel cero que son enormes (continentes, océanos). Cada celda de nivel cero contiene celdas de nivel uno (regiones, reinos). Cada celda de nivel uno contiene celdas de nivel dos (provincias, comarcas). Y así hasta nivel cuatro, que son interiores específicos como una taberna o una habitación.

Esto permite carga lazy: solo se carga en memoria lo cercano al jugador y a un nivel apropiado de detalle. Cuando el jugador está en la taberna, se carga la taberna con todos sus interiores y se carga al nivel del pueblo el contexto inmediato, pero la región solo se carga como resumen y los reinos lejanos no se cargan en absoluto. Cuando el jugador se mueve, lo que dejó atrás se descarga (después de simularse rápidamente) y lo nuevo se carga.

La jerarquía también es la jerarquía de perspectivas. Un dios que mira el mundo entero ve celdas de nivel cero como resúmenes estadísticos. Un campesino que vive en un pueblo ve solo su nivel tres y sus vecinos. La granularidad espacial es la granularidad de atención.

## La estructura de datos

Cada celda es un objeto Pydantic con una estructura específica que conviene tener presente.

```python
class Lugar(BaseModel):
    id: str  # LUGAR-cala_norte_pueblo
    tipo: Literal["mundo", "reino", "provincia", "pueblo", "interior", "natural"]
    nombre: str
    nivel_jerarquico: int  # 0 a 4
    parent_id: Optional[str] = None  # nivel superior
    children_ids: list[str] = []  # niveles inferiores
    coords_locales: tuple[int, int]  # (x, y) dentro del parent
    descripcion_base: str
    prompt_narracion: str  # dirección estética para el LLM
    memetario_simbolico: list[str]
    modificadores_categoria: dict[str, int] = {}
    agentes_presentes: list[str] = []
    eventos_recientes: list[str] = []
    secretos: list[SecretoSembrado] = []
    objetos: list[str] = []  # IDs de objetos
    ciclos: list[CicloVida] = []
```

Algunos campos merecen comentario. El campo coords_locales es un par (x, y) relativo al parent, no coordenadas globales. Esto significa que para identificar una celda únicamente necesitás el parent más las coords. Los IDs incluyen parent y coords concatenados, lo que los vuelve estables: LUGAR-reino_sur_03_02 es la celda en posición (3, 2) dentro del reino del sur.

El campo prompt_narracion es dirección estética que el motor pasa al LLM cuando narra escenas en este lugar. No es la descripción del lugar (eso es descripcion_base), es instrucción al LLM sobre cómo tratar narrativamente este lugar específico. Algo como "cuando narres esta cala, evocá la paradoja del lugar que vibra cuando lo demás muere. Hay algo antiguo en él. Prosa corta, pocos adjetivos."

Los campos memetario_simbolico y modificadores_categoria son lo que vuelve al lugar cuerpo cognitivo. Estos campos viven en el archivo de referencia memetario-de-lugares.md.

## La clase Grilla

El sistema de grilla está implementado por una clase Grilla que mantiene índices y permite operaciones espaciales eficientes.

```python
class Grilla:
    def __init__(self, dimension_top: tuple[int, int]):
        self.celdas: dict[str, Lugar] = {}
        self.indice_espacial: dict[tuple, str] = {}
        # (parent_id, x, y) -> celda_id
        self.indice_agentes: dict[str, str] = {}
        # agente_id -> celda_actual_id
    
    def vecinas(self, celda_id: str) -> list[str]:
        """Las 8 celdas vecinas (Moore neighborhood) en el mismo nivel."""
        celda = self.celdas[celda_id]
        x, y = celda.coords_locales
        parent = celda.parent_id
        vecinas = []
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            key = (parent, x+dx, y+dy)
            if key in self.indice_espacial:
                vecinas.append(self.indice_espacial[key])
        return vecinas
    
    def descendientes(self, celda_id: str) -> list[str]:
        """Todas las celdas anidadas dentro de esta."""
        celda = self.celdas[celda_id]
        result = list(celda.children_ids)
        for hijo in celda.children_ids:
            result.extend(self.descendientes(hijo))
        return result
    
    def ancestros(self, celda_id: str) -> list[str]:
        """Cadena hasta la raíz."""
        result = []
        current = self.celdas[celda_id].parent_id
        while current:
            result.append(current)
            current = self.celdas[current].parent_id
        return result
```

Las tres operaciones principales son vecinas, descendientes, ancestros. Cada una es útil para operaciones distintas: vecinas para propagación horizontal de información, descendientes para zoom in (entrar a un nivel inferior), ancestros para zoom out (consultar contexto del nivel superior).

El uso de Moore neighborhood (las 8 celdas adyacentes incluyendo diagonales) en vez de Von Neumann (solo las 4 ortogonales) es decisión deliberada. Permite movimiento más natural de información y agentes. Pero si en algún momento descubris que la propagación se siente demasiado rápida, podés cambiar a Von Neumann reduciendo a 4 vecinos.

## La carga lazy

Esta es la pieza que vuelve manejable un mundo grande. El sistema mantiene un cache de celdas cargadas en memoria con tamaño máximo configurable.

```python
class GestorCeldas:
    CACHE_MAX = 50
    
    def __init__(self):
        self.cache: dict[str, Lugar] = {}
        self.acceso_reciente: list[str] = []
    
    def get(self, celda_id: str) -> Lugar:
        if celda_id in self.cache:
            self.acceso_reciente.remove(celda_id)
            self.acceso_reciente.append(celda_id)
            return self.cache[celda_id]
        
        # Cargar de disco
        celda = cargar_celda_disco(celda_id)
        self.cache[celda_id] = celda
        self.acceso_reciente.append(celda_id)
        
        # Si excede cache_max, descargar la menos reciente
        # PERO antes simular sus eventos pendientes (lazy simulation)
        if len(self.cache) > self.CACHE_MAX:
            descartar_id = self.acceso_reciente.pop(0)
            simular_eventos_pendientes(self.cache[descartar_id])
            persistir_celda(self.cache[descartar_id])
            del self.cache[descartar_id]
        
        return celda
```

Lo importante de este mecanismo es la simulación lazy al descargar. Cuando una celda sale del cache (porque hace tiempo que no se usa y otras la desplazaron), el sistema simula rápidamente los eventos pendientes que debieron haber ocurrido en ella desde la última vez que estuvo cargada, los persiste, y entonces la descarga. Esto significa que cuando el jugador vuelve a una celda después de mucho tiempo, el estado de esa celda refleja correctamente el tiempo transcurrido aunque no se haya estado simulando activamente.

Para el MVP, donde solo hay una celda (la taberna de Cala Norte), nada de esto es necesario. La carga lazy es infraestructura para fases posteriores cuando el mundo se expanda. Programar la lógica completa antes de necesitarla es trabajo desperdiciado.

## Velocidades de propagación según nivel

Una pieza importante que conecta este archivo con el skill de codex-fragmentum-grafo-mundo: la velocidad de propagación de información depende del nivel jerárquico de las celdas involucradas.

```python
VELOCIDAD_PROPAGACION = {
    4: 0.30,  # interiores → interiores: rumor cruza taberna en horas
    3: 0.10,  # pueblo → pueblo: días
    2: 0.03,  # provincia → provincia: semanas
    1: 0.005, # reino → reino: meses
    0: 0.001, # mundo: años
}

def chance_propagacion(celda_origen_id: str, celda_destino_id: str) -> float:
    """¿Cuán probable es que un rumor salte de un lugar a otro?"""
    nivel_origen = celdas[celda_origen_id].nivel_jerarquico
    nivel_destino = celdas[celda_destino_id].nivel_jerarquico
    nivel_efectivo = min(nivel_origen, nivel_destino)
    return VELOCIDAD_PROPAGACION[nivel_efectivo]
```

Estas probabilidades son por tick (típicamente un día del mundo). Es decir, en cada día del mundo, cada rumor que existe en un nivel 3 tiene 10% de chance de saltar a una celda vecina del mismo nivel. Esto suena bajo pero acumulado en treinta días de time-jump produce propagación sustancial.

Las velocidades exactas son provisionales. Si James reporta que la información se mueve demasiado rápido (los rumores llegan al obispado al día siguiente del avistamiento), bajan los números. Si se mueve demasiado lento (los rumores se quedan estancados en una celda para siempre), suben.

## El movimiento de agentes entre celdas

El sistema mantiene un índice de qué agentes están en qué celdas (indice_agentes en la clase Grilla). Cada vez que un agente se mueve, el índice se actualiza y la celda origen y la destino reciben actualizaciones de su lista agentes_presentes.

El movimiento de un agente puede disparar varios efectos: propagación de información que ese agente conoce hacia otros agentes en la nueva celda, recálculo del loadout cognitivo del agente bajo los modificadores de la nueva celda, evaluación de secretos sembrados en la nueva celda que se activan por presencia, eventos de relación con otros agentes ya presentes.

Cuando programes el movimiento, asegurate de que estos efectos se procesen en el orden correcto. Primero actualizar el índice. Después recalcular el loadout. Después evaluar secretos. Por último procesar propagación e interacciones. Si el orden está mal, podés tener bugs sutiles donde la propagación usa datos obsoletos.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera, la grilla del MVP no es jerárquica activa, es una sola celda. No programes lógica de movimiento entre celdas para el MVP. La estructura de datos puede soportar la jerarquía completa, pero las operaciones de movimiento, vecinas, propagación entre celdas, son trabajo de iteración 1, no de MVP.

Segunda, los IDs de las celdas son estables y se construyen desde el parent y las coordenadas. Esto significa que si James reorganiza el mapa moviendo una celda, los IDs cambian, lo cual rompe todas las referencias en otras partes del sistema. Para evitar esto, una vez que un mapa está construido, los IDs no deberían cambiar. Si hace falta reorganizar, conviene crear celdas nuevas y migrar el contenido en lugar de renombrar.

Tercera, la carga lazy es feature de fase 2 o posterior, no de MVP. No programes el GestorCeldas completo hasta que tengas suficientes lugares como para que la memoria importe. Para el MVP con una sola celda, simplemente cargá todo al inicio y mantenelo en memoria.
