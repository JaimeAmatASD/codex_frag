---
name: codex-fragmentum-grafo-mundo
description: Sistema de información del proyecto Codex Fragmentum, donde la información es física y muta como un virus al transmitirse entre personajes. Cubre los hechos del mundo como nodos raíz, los árboles de mutación que registran cómo cada versión derivada se desvió al pasar por el prisma de un receptor, la propagación entre agentes vía encuentros, el grafo NetworkX que estructura todo. Cargá cuando el trabajo toque cómo se modela un hecho del mundo, cómo se transmite información entre NPCs, cómo se produce una versión mutada (llamada al LLM tier 1 muy específica), cómo se registra el conocimiento de cada agente, cómo se busca en el grafo. Cargalo también cuando James tunee frecuencias de transmisión, chance de mutación, o decida qué versión recibe un agente cuando hay varias circulando. Triggers en inglés — fact graph, rumor mutation tree, information propagation, prism transformation, knowledge graph queries, fact node, version derivation. Presupone codex-fragmentum-arquitectura cargado.
---

# Codex Fragmentum — Grafo de información del mundo

Este skill se ocupa del sistema que modela cómo la información existe, se transmite y muta en el mundo del Codex. Si llegaste a este skill, James está trabajando en la pieza que vuelve concreta la promesa central del proyecto: la verdad muere con el testigo, los rumores se deforman en cada salto, lo que cada personaje sabe es función de su trayectoria personal de encuentros e información recibida. Para el contexto general, asumí que el skill maestro codex-fragmentum-arquitectura ya está cargado.

## Por qué este sistema importa estructuralmente

Vale la pena empezar por la motivación porque sin ella las decisiones técnicas pueden parecer arbitrarias. La promesa central de Codex Fragmentum, la frase que vive como subtítulo informal del proyecto, es "donde la verdad muere con el testigo". Esa frase tiene peso operativo, no solo poético. Significa que la información en el mundo es física: ocupa lugar (vive en personajes específicos), tiene velocidad (tarda en propagarse), se deforma al moverse (cada salto la muta), y puede perderse si su único portador muere antes de transmitirla.

Para hacer concreta esa promesa hace falta un sistema que modele información así, no como variables booleanas que indican si un personaje sabe o no algo, sino como un grafo vivo donde los hechos tienen versiones derivadas que circulan, mutan y a veces se extinguen. Ese sistema es lo que este skill cubre.

La diferencia con cómo otros proyectos manejan información es radical. AI Dungeon trata la información como contenido del LLM: el modelo recuerda lo que escribe, olvida cuando el contexto se llena, inventa cuando se le pregunta. Otros simuladores narrativos tratan la información como flags binarios por agente. Codex la trata como entidades estructurales con vida propia que pasan por filtros cognitivos al moverse.

## Los tres niveles de evento

Una distinción conceptual fundamental que conviene tener clara antes de tocar código: hay tres niveles de evento que no deben confundirse, aunque pueden derivar uno del otro.

Un hecho del mundo es lo que objetivamente ocurrió. El kraken existió, emergió esa noche, en esa cala. Es información objetiva con fecha, lugar, descripción, testigos directos. Existe independientemente de quién lo sepa. Es el nodo raíz de su árbol de mutaciones.

Una información transmitida es una versión derivada del hecho que circula por el grafo de personajes. Cuando Marcos le cuenta a Lía sobre el kraken, no se transmite el hecho original: se transmite una versión filtrada por el cristal de Marcos al narrarlo, que después se filtra otra vez por el cristal de Lía al recibirlo. Esa versión que ahora tiene Lía es un nodo nuevo en el árbol, derivado del nodo de Marcos, con sus propias mutaciones.

Un hito biográfico es algo distinto y vive en el skill de memetario, no acá. Si te encontrás trabajando con hitos, el skill correcto es codex-fragmentum-memetario. Acá nos ocupamos solamente de hechos del mundo y sus versiones transmitidas.

## La estructura de un hecho del mundo

Un hecho del mundo es un objeto Pydantic con varios campos. Identificador único. Título y descripción objetiva (la verdad tal como ocurrió). Fecha de ocurrencia (formato libre del mundo). Lugar donde ocurrió (referencia a la celda específica). Lista de testigos directos (agentes que lo vivieron y por lo tanto tienen la versión más cercana a la raíz). Y crucialmente, el árbol de mutaciones que registra todas las versiones que derivan de este hecho.

```python
class HechoMundo(BaseModel):
    id: str  # HECHO-kraken_avistamiento_1247_otono
    titulo: str
    descripcion_objetiva: str  # la verdad raíz
    fecha_ocurrencia: str  # formato libre del mundo
    lugar_id: str  # referencia a celda
    testigos_directos: list[str]  # IDs de agentes
    arbol_mutaciones: ArbolMutaciones
    embedding: Optional[list[float]] = None
```

La descripción objetiva es la versión raíz del árbol. Existe siempre, aunque ningún personaje la conozca exactamente. Sirve como referencia para calcular la distancia de cada versión derivada respecto al hecho original.

## El árbol de mutaciones

Cada hecho del mundo tiene un árbol asociado donde la raíz es la descripción objetiva y cada nodo derivado es una versión específica del hecho tal como llegó a algún personaje. El árbol es estrictamente direccional: las flechas van de versión origen a versión derivada, nunca al revés.

```python
class ArbolMutaciones(BaseModel):
    raiz: NodoVersion
    nodos: dict[str, NodoVersion]  # id -> nodo

class NodoVersion(BaseModel):
    id: str  # NODO-marcos_v1
    contenido: str  # cómo está formulada esta versión
    embedding: list[float]  # 384 floats
    parent_id: Optional[str] = None  # de qué versión deriva
    children_ids: list[str] = []  # versiones derivadas
    emisor_id: Optional[str] = None  # quién contó esta versión
    receptor_id: Optional[str] = None  # a quién
    fecha_transmision: Optional[str] = None
    prisma_aplicado: dict  # qué memes del receptor estaban activos
    distancia_a_raiz: float  # similitud coseno con la raíz
```

Un detalle importante: cada nodo registra el prisma aplicado, es decir, qué memes operativos del receptor estaban activos cuando recibió la versión. Esto permite reconstruir después por qué la mutación fue como fue, y eventualmente entrenar al sistema para predecir mutaciones más precisas. También permite operaciones de análisis: si un investigador (humano, no en juego) quiere entender por qué cierta versión del rumor se volvió dominante, puede mirar los prismas aplicados en su rama del árbol.

La distancia a la raíz se calcula como similitud coseno entre el embedding de esta versión y el embedding de la raíz. Una distancia cercana a cero significa que la versión está muy mutada (poco parecida a la raíz). Una distancia cercana a uno significa que está casi intacta. Esta métrica es útil para muchas operaciones: filtrar versiones todavía reconocibles, detectar cuándo un rumor se ha distorsionado tanto que se volvió otra cosa, decidir si dos versiones son "la misma información" para efectos de propagación.

## La operación fundamental: propagar un hecho

Esta es la función más distintiva del sistema y probablemente donde James va a iterar más al ver cómo se comportan los rumores. La función toma un emisor, un receptor, y la versión origen que el emisor le va a transmitir. Devuelve un nuevo nodo de versión que representa cómo el receptor entendió y va a transmitir esta información.

```python
def propagar_hecho(emisor: Agente, receptor: Agente, version_origen: NodoVersion) -> NodoVersion:
    # 1. Calcular el loadout activo del receptor en este contexto
    loadout = calcular_loadout(receptor, contexto={"input": version_origen.contenido})
    
    # 2. Armar prompt con el loadout, la versión origen, el lugar actual
    prompt = template_mutacion(version_origen, loadout, lugar_actual)
    
    # 3. LLM (tier 1) produce nueva versión + drift estimado
    propuesta = llm.structured(prompt, PropuestaMutacion, tier=1)
    
    # 4. Calcular embedding de la nueva versión
    nuevo_embedding = embed(propuesta.contenido_nuevo)
    
    # 5. Crear NodoVersion con todos los metadatos
    nuevo_nodo = NodoVersion(...)
    
    # 6. Agregarlo al grafo del mundo
    G.add_node(nuevo_nodo.id, tipo="version_hecho", data=nuevo_nodo)
    G.add_edge(version_origen.id, nuevo_nodo.id, relacion="muto_a")
    G.add_edge(receptor.id, nuevo_nodo.id, relacion="conoce_version")
    
    return nuevo_nodo
```

Lo crítico de esta función es que el LLM no decide qué pasa, decide cómo se filtra. El motor le pasa la versión origen y el loadout del receptor. El LLM produce una versión mutada que respeta el loadout (es decir, los memes activos del receptor influyen en cómo se reformula la información). El motor valida la respuesta, calcula el embedding, registra todo en el grafo.

Si el LLM devuelve una versión idéntica al origen (sin mutación significativa), el sistema puede detectarlo midiendo la distancia coseno entre origen y propuesta. Si es muy alta, hubo poca mutación. Si es muy baja, hubo demasiada mutación (la versión es irreconocible). Para el MVP conviene aceptar ambos extremos sin reintento, pero para iteraciones posteriores vale la pena agregar lógica de retry con feedback al LLM cuando la mutación es claramente nula o claramente excesiva.

## La lógica de propagación entre agentes

La propagación de información en el mundo no es continua: ocurre cuando agentes se encuentran y conversan. La lógica de cuándo se transmite qué a quién es donde se concentra el balance del sistema.

Cada tick del mundo (típicamente un día), el motor evalúa para cada agente si va a hablar de algún tema. Esto se modela como una probabilidad por agente y por hecho conocido. Si el agente conoce un hecho, hay una chance (provisional 30%) de que en ese tick lo mencione a alguien presente. Si la probabilidad sale, el motor selecciona a quién contárselo entre los otros agentes presentes en la misma celda.

```python
def procesar_propagacion(hecho: HechoMundo, tick_actual: int):
    for agente_id in agentes_que_conocen(hecho):
        if random.random() > 0.3:  # chance de hablar
            continue
        agente = cargar_agente(agente_id)
        otros = agentes_en_celda(agente.celda_actual_id)
        for receptor in otros:
            if receptor.conoce(hecho.id):
                continue  # ya sabe esta info
            if random.random() > 0.5:  # chance de contárselo a este
                continue
            # propagar
            version = agente.version_que_conoce(hecho.id)
            propagar_hecho(agente, receptor, version)
```

Las probabilidades exactas son provisionales. James va a tunearlas según se sienta el ritmo de propagación. Si los rumores se mueven demasiado rápido y el mundo se vuelve homogéneo, bajan las chances. Si se mueven demasiado lento y los hechos quedan en un solo agente para siempre, suben.

Hay una pieza de balance importante: la chance de transmisión debe depender de la naturaleza del hecho y de la relación entre agentes, no solo de probabilidades genéricas. Un hecho fascinante (avistamiento de monstruo, muerte súbita) se cuenta más que un hecho mundano (cosecha rutinaria). Un hecho que comparte categoría simbólica con los memes activos del emisor se cuenta más fácil. Una relación cercana entre emisor y receptor (compañeros, familiares) facilita la transmisión, una relación tensa la dificulta. Para el MVP estos refinamientos pueden quedar como TODO; para iteraciones posteriores conviene programarlos.

## Velocidad de propagación según geografía

Una pieza que conecta este skill con el de cartografía: la velocidad de propagación depende del nivel jerárquico de las celdas. Rumores cruzan rápido entre celdas internas de un mismo pueblo (chance alta por tick), lento entre provincias (chance media), casi nunca entre reinos (chance baja).

```python
VELOCIDAD_PROPAGACION = {
    4: 0.30,  # interiores (taberna a casa) → horas
    3: 0.10,  # pueblo a pueblo → días
    2: 0.03,  # provincia a provincia → semanas
    1: 0.005, # reino a reino → meses
    0: 0.001, # mundo (entre civilizaciones) → años
}
```

Estas probabilidades se aplican cuando un agente se mueve de una celda a otra y lleva información consigo. La idea es que la información tiende a quedarse local. Solo cuando alguien se mueve, la información salta entre regiones.

Esto produce sensación de mundo grande: lo que pasa en el norte tarda en llegar al sur, y para cuando llega ya está deformado. La latencia narrativa que el manifiesto original prometía se manifiesta exactamente acá, en estas probabilidades de propagación geográfica.

## Búsqueda de conocimiento

Una operación frecuente: dado un agente y un hecho, ¿qué versión del hecho conoce? Si conoce alguna, ¿cuándo la recibió y de quién? Esta operación se ejecuta cada vez que el LLM va a narrar algo en presencia de un agente, para saber qué información tiene disponible para refractar.

```python
def busqueda_conocimiento(agente: Agente, hecho_id: str) -> Optional[NodoVersion]:
    """¿Qué versión de este hecho conoce este agente?"""
    aristas = G.edges(agente.id, data=True)
    for _, target, data in aristas:
        if data.get("relacion") == "conoce_version":
            nodo = G.nodes[target]["data"]
            if pertenece_al_arbol(nodo, hecho_id):
                return nodo
    return None
```

La función recorre las aristas salientes del agente buscando relaciones de tipo "conoce_version" hacia nodos que pertenezcan al árbol del hecho buscado. Si encuentra alguna, devuelve esa versión. Si no, el agente no conoce nada del hecho.

Para que esto sea eficiente con grafos grandes, conviene mantener un índice secundario que mapea (agente_id, hecho_id) directamente al nodo de versión que conoce. Para el MVP con pocos agentes y pocos hechos, la búsqueda directa es suficiente. Si el sistema escala, el índice ahorra mucho tiempo.

Un caso particular: un agente puede conocer múltiples versiones de un mismo hecho (escuchó el rumor por dos fuentes distintas). En ese caso, la búsqueda devuelve una de las versiones (típicamente la más reciente o la de mayor confianza). Manejar versiones múltiples del mismo hecho en un solo agente es complejidad que conviene postergar para iteraciones posteriores.

## El uso de NetworkX

El grafo del mundo se modela con la librería NetworkX, específicamente con MultiDiGraph porque permite múltiples aristas entre el mismo par de nodos con relaciones distintas. Esto es importante porque entre dos agentes puede haber simultáneamente relaciones de tipo "es_pariente_de", "transmitió_información_a", "vive_cerca_de".

Los nodos del grafo son de varios tipos: agentes (PJ, NPCs, dioses), hechos del mundo, versiones del árbol de mutaciones, lugares (referenciados pero típicamente almacenados aparte). Las aristas registran las relaciones entre ellos.

```python
import networkx as nx

G = nx.MultiDiGraph()
G.add_node("PJ-marcos_pescador", tipo="agente", data=marcos_obj)
G.add_node("HECHO-kraken_avistamiento", tipo="hecho", data=hecho_obj)
G.add_node("NODO-marcos_v1", tipo="version_hecho", data=version_obj)

G.add_edge("PJ-marcos_pescador", "NODO-marcos_v1", relacion="vivio_directamente")
G.add_edge("NODO-marcos_v1", "NODO-lia_v2", relacion="transmitio_a", fecha="...")
```

NetworkX en memoria es perfecto para el MVP. Cuando el grafo crezca a más de diez mil nodos, conviene considerar persistencia en SQLite con tablas dedicadas (una de nodos, una de aristas, índices apropiados) o migrar a Neo4j si el caso lo justifica. Pero esto es decisión para fases posteriores.

La persistencia del grafo entre sesiones se hace con `nx.write_gpickle()` para snapshots completos y reconstrucción rápida, complementada con exportación a JSON Graph format para inspección humana cuando hace falta debuggear.

## La integración con el motor cognitivo

Una decisión importante de arquitectura: el grafo de información y el motor cognitivo (memetario) están acoplados pero son sistemas distintos. No deben colapsarse en uno solo aunque interactúen constantemente.

El grafo registra qué versiones discretas de qué hechos llegaron a qué agentes, cuándo, de quién. Es estructura discreta, auditable, rastreable. La pregunta "¿qué sabe Marcos sobre el kraken?" se responde mirando el grafo.

El memetario registra cómo cada agente refracta la información que tiene. Es estructura semántica continua via embeddings. La pregunta "¿cómo va a interpretar Marcos el rumor del kraken cuando alguien se lo cuente?" se responde mirando su memetario.

Cuando se propaga un hecho (función `propagar_hecho`), las dos capas trabajan juntas: el motor cognitivo aporta el loadout del receptor que actúa como prisma, el grafo registra el resultado de la mutación como nuevo nodo conectado al árbol. Cada llamada a propagar_hecho es un punto donde las dos capas se hablan.

Si te encontrás programando algo del grafo aislado del memetario, parate y revisá si efectivamente puede aislarse. La mayoría de las operaciones del grafo necesitan datos del memetario para producir resultados sensatos.

## Recordatorios operativos

Cuando James trabaje en este territorio, tres cosas conviene tener presentes.

Primera, la calidad de las mutaciones depende casi enteramente del template del prompt que se le pasa al LLM. Si las mutaciones se sienten cosméticas (cambian palabras pero no la sustancia), el problema está en el template, no en la lógica de propagación. El skill de codex-fragmentum-llm-prompts cubre cómo iterar sobre templates específicos como el de mutación.

Segunda, no todos los hechos merecen modelarse explícitamente como hechos del mundo. Solo aquellos que importan narrativamente: avistamientos significativos, muertes, traiciones, descubrimientos, eventos cosmológicos. Los hechos menores (qué desayunó un personaje, qué tiempo hace) no necesitan estructura de árbol; pueden ser información atmosférica que el LLM narra sin ser tracked. Si te encontrás creando muchísimos hechos del mundo para eventos triviales, estás invirtiendo esfuerzo donde no rinde.

Tercera, los rumores que circulan deben poder extinguirse. Si todos los hechos siguen circulando para siempre, el grafo crece sin límite y el rendimiento se degrada. Conviene tener una lógica de "envejecimiento": versiones de hechos muy antiguos pueden archivarse del grafo activo si no se han transmitido en N ticks. Para el MVP esto puede no ser crítico, pero para fases posteriores es importante. La extinción de información también es narrativamente significativa: representa los hechos que el mundo olvidó.
