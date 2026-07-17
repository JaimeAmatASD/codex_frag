# Codex Fragmentum — Mejora 04 (EXPERIMENTO): mecanismos de aprendizaje por meme
## No todos los memes cambian igual — hipótesis a validar antes de adoptar

*Cuarta pieza de la serie, y es distinta: es un EXPERIMENTO con veredicto, no una adopción. Sale de docs/ANALISIS_BRAINSTORMING_JUL2026.md, parte 3. Presupone hechas las mejoras 01 a 03. Leé codex/decaimiento.py y el registro de activaciones en codex/persistencia.py.*

## La hipótesis

Algunos memes se refuerzan con evidencia; otros se radicalizan cuando son contradichos (como las creencias conspirativas); otros solo cambian por trauma; otros se erosionan lento. Si cada meme lleva su propio mecanismo de aprendizaje, los personajes desarrollan trayectorias psicológicas distinguibles. La pregunta del experimento: ¿esa diferencia SE NOTA jugando, o es complejidad sin retorno?

## Diseño del experimento (esto sí se construye, acotado)

**El campo y las políticas.** La definición del meme gana aprendizaje, opcional, con cuatro valores: normal (default, lo de hoy), se_radicaliza (cuando una transmisión recibida lo CONTRADICE — baja afinidad semántica con su texto pero mismo tema — en vez de debilitarse gana peso), solo_trauma (ni refuerzos ni contradicciones lo mueven; solo un hito/evento marcado como traumático lo cambia), se_erosiona (decae más rápido de lo normal ante contradicciones repetidas). La detección de "contradicción" es la más delicada: versión mínima con embeddings existentes (mismo tema por similitud con el contenido recibido, señal de oposición por el prompt de mutación que ya reporta memes resonantes — si un meme resonó pero la versión entendida lo desafía, el LLM lo marca en un campo nuevo opcional del esquema de respuesta). Mantenerlo simple; si la detección no da, simplificar el experimento antes que sofisticarla.

**El protocolo A/B en el Taller.** Mismo ser duplicado (copiar la carpeta semilla con otro id), uno con se_radicaliza en un meme central y otro con normal. Bombardearlos con la MISMA secuencia de cinco o seis noticias contradictorias desde la zona Probar. Al final, contarles el mismo hecho y leer las dos versiones lado a lado, más comparar los pesos en la vista de estado vivo.

## El veredicto (James decide, y queda registrado)

Éxito: las trayectorias divergen Y la diferencia se nota al leer cómo recuentan (el radicalizado suena más atrincherado, no solo tiene otro número). Fracaso: los pesos divergen pero las voces no, o nada diverge. Si fracasa, se descarta CON EVIDENCIA (se anota en el análisis y se borra el campo o queda inerte), y eso también es un buen resultado: complejidad evitada con datos. Nada de esto se declara adoptado hasta el veredicto.

## Lo que NO es de este experimento

Ni fusión de memes, ni memes que generan memes, ni emociones como sistema, ni tocar las PF (las piedras no aprenden: se conservan; su cambio es territorio de la mejora 05 y de las crisis). Ni calibración fina de umbrales: números gruesos, leer, decidir.

## Cómo proceder

Primero el campo con las políticas y el ajuste mínimo del esquema de respuesta de mutación, visto bueno de James, después la aplicación en decaimiento/refuerzo con tests puros (políticas aplicadas a secuencias sintéticas de eventos), y al final el protocolo A/B corrido de verdad en el Taller con Gemini. Cerrar con el veredicto escrito.
