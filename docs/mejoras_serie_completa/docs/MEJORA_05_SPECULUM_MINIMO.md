# Codex Fragmentum — Mejora 05: el SPECULUM mínimo
## La autoobservación: el ser que mira su propia trayectoria

*Quinta y última de la serie, la más grande: es la deuda de diseño del NÚCLEO (Fase 0) que el brainstorming re-priorizó ("motor de identidad"). Hacerla recién con las mejoras 01 a 04 cerradas. Leé docs/VISION_FASE0.md (núcleo irrenunciable), docs/VERIFICACION_CODIGO_FRAY_TOMAS.md (el SPECULUM de Fray Tomás, speculum.py, y el sistema de fricción de cambio_biografico.py: son el prototipo de esto) y la bitácora del Taller.*

## La idea en tres líneas

Un ser de Codex no solo percibe y cambia: SE MIRA. El SPECULUM mínimo lee la trayectoria registrada del ser (qué memes movilizó y cuánto, qué tensiones se le repiten, qué hechos recibió y cómo los deformó) y produce dos cosas: una reflexión breve en primera persona (quién estoy siendo) y PROPUESTAS tipadas de cambio (subir o bajar peso de memes operativos, proponer un meme experimental nuevo). El autor aprueba o rechaza cada propuesta. Es identidad narrativa operativa: hacerse cargo del propio cambio.

## Decisiones ya tomadas (no re-debatir)

**El LLM propone, el motor valida, el autor dispone (fricción heredada de Fray Tomás).** Las propuestas llegan en esquema Pydantic estricto: tipo de cambio (ajustar_peso o proponer_experimental), meme, delta acotado (máximo 2 puntos por propuesta, la regla del degradé de Fray Tomás), y justificación citando la evidencia de la trayectoria. Las PF son INTOCABLES por esta vía: si la reflexión sugiere que una piedra tambalea, solo puede DECIRLO en la reflexión (material para futuras crisis biográficas), jamás proponer cambiarla. Nada se aplica sin aprobación explícita del autor en el Taller; lo aprobado se aplica por la puerta única y queda en la bitácora con su justificación.

**La materia prima es lo ya registrado.** Nada de registrar cosas nuevas: el SPECULUM consulta activaciones (loadout vs movilizado), tensiones detectadas, y las transmisiones de la bitácora del ser. Umbral mínimo de material (por ejemplo, diez movilizaciones registradas) para que la reflexión no sea humo: sin material suficiente, el Taller lo dice y no llama al LLM.

**Manual, por ser, desde el Taller.** Un botón "que se mire" en la ficha del personaje. Nada de frecuencia automática ni schedulers: la cadencia la decide el autor. Template nuevo templates/speculum.txt, editable como los demás.

## Tests (deterministas, sin red)

Con MockClient: propuestas válidas se listan sin aplicarse; delta mayor al degradé es rechazado por validación; propuesta sobre una PF es rechazada; aprobar aplica por la puerta única y registra; rechazar no toca nada; sin material suficiente no se llama al cliente.

## Criterio de éxito (James en el Taller)

Después de una sesión de juego real (transmisiones y Scores acumulados), pedirle a un ser que se mire. Éxito si la reflexión te cuenta algo del personaje que vos no habías formulado pero reconocés al leerlo (el espejo muestra, no inventa), y si al menos una propuesta te da ganas de aprobarla. Si las reflexiones son horóscopo genérico tras iterar el template, reportar honesto: el SPECULUM sin espejo real es peor que no tenerlo.

## Lo que NO es de esta mejora

Ni crisis biográficas completas, ni cambios de PF, ni hitos automáticos, ni SPECULUM para todos los seres a la vez, ni frecuencia automática, ni memoria episódica consolidada. Es el órgano mínimo: mirar la evidencia, decir quién se está siendo, proponer ajustes chicos con fricción.

## Cómo proceder

Primero el esquema Pydantic de la reflexión y propuestas más el template en texto plano, visto bueno de James, después la consulta de trayectoria con tests, el flujo aprobar/rechazar por la puerta única, y al final el botón en el Taller. Commits chicos en castellano.
