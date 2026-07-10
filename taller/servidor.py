"""El Taller: arranque sin fricción.

    ./venv/bin/python taller/servidor.py

Busca la API key de Gemini en el entorno y, si no está, en ~/.gemini_key. Levanta
el servidor local y abre el navegador solo. Para cerrarlo: Ctrl+C.
"""

from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

DIRECCION = "127.0.0.1"
PUERTO = 8765


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        clave = Path.home() / ".gemini_key"
        if clave.exists():
            os.environ["GEMINI_API_KEY"] = clave.read_text(encoding="utf-8").strip()
        else:
            print(
                "Aviso: sin GEMINI_API_KEY (ni ~/.gemini_key). El taller abre igual,\n"
                "pero transmitir y narrar Scores va a fallar hasta que haya key."
            )

    import uvicorn

    from taller.app import crear_app

    app = crear_app(RAIZ / "mundos")
    url = f"http://{DIRECCION}:{PUERTO}"
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    print(f"El Taller: {url}  (Ctrl+C para cerrar)")
    uvicorn.run(app, host=DIRECCION, port=PUERTO, log_level="warning")


if __name__ == "__main__":
    main()
