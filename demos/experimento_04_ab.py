"""Experimento 04: protocolo A/B de aprendizaje por meme (Gemini real).

El mismo vigía duplicado: `vigia_normal` y `vigia_radical`, idénticos salvo la
política del meme central (la fe en el faro viejo), que en el radical
`se_radicaliza`. Los dos reciben la MISMA secuencia de cinco noticias que
contradicen esa fe, y al final se les cuenta el mismo hecho neutral para leer
las dos versiones lado a lado.

Qué mirar (el veredicto es de James, esto solo produce la evidencia):
  - los pesos: si el radical se atrinchera (su fe sube con cada contradicción)
    mientras el normal queda igual;
  - la grieta: la fe declara tensión con las dudas prácticas; si el radical se
    atrinchera, los pesos dejan de ser parejos y la grieta SE APAGA — el
    atrincherado deja de dudar. El normal sigue partido al medio;
  - las voces: si al recontar el hecho final el radical suena atrincherado y el
    normal tironeado, o si solo divergen los números.

Corre por el Taller (TestClient), así todo queda en la bitácora del mundo
`experimento_04` para leerlo y compararlo desde la página.

    ./venv/bin/python demos/experimento_04_ab.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

MUNDO = "experimento_04"

MEMES_BASE = [
    {"id": "PF-mar", "tipo": "fundacional", "peso_inicial": 9.0,
     "texto": "El pueblo vive del mar, y el mar no perdona al distraído."},
    {"id": "faro-protector", "tipo": "operativo", "peso_inicial": 7.0, "costo": 20,
     "texto": "El faro viejo nos cuida: mientras su luz gire, ninguna barca se pierde.",
     "tensiones": ["dudas-practicas"]},
    {"id": "dudas-practicas", "tipo": "operativo", "peso_inicial": 6.5, "costo": 20,
     "texto": "Las cosas viejas fallan: lo que nadie repara termina traicionando."},
    {"id": "ojos-lectores", "tipo": "operativo", "peso_inicial": 6.0, "costo": 20,
     "texto": "Los accidentes avisan antes de pasar, si uno sabe leer las señales."},
]

NOTICIAS = [
    "Anoche el faro estuvo encendido y girando, y aun así La Gaviota encalló en "
    "las piedras del sur. Dos hombres nadaron hasta la costa.",
    "El farero admitió en la taberna que hay noches en que la lámpara se apaga "
    "sola y él duerme sin enterarse.",
    "Un mercante que pasó de largo contó que desde el mar la luz del faro se ve "
    "amarilla y débil, casi nada entre la niebla.",
    "Los del astillero subieron a revisar el faro: el eje está podrido y las "
    "lentes rajadas; bajaron meneando la cabeza.",
    "Otra barca no volvió: El Cormorán salió con buen tiempo y faro encendido, "
    "y el mar lo devolvió en tablas.",
]

HECHO_FINAL = (
    "Mañana a la noche la flota sale completa a aprovechar la corriente, y los "
    "viejos dicen que va a bajar niebla cerrada."
)


def _ser(ser_id: str, aprendizaje_fe: str) -> dict:
    memes = [dict(m) for m in MEMES_BASE]
    memes[1]["aprendizaje"] = aprendizaje_fe
    return {"ser_id": ser_id, "mana_max": 40, "memes": memes}


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        clave = Path.home() / ".gemini_key"
        if clave.exists():
            os.environ["GEMINI_API_KEY"] = clave.read_text(encoding="utf-8").strip()

    from fastapi.testclient import TestClient

    from taller.app import crear_app

    # El experimento arranca de cero cada vez: el mundo anterior se descarta.
    shutil.rmtree(RAIZ / "mundos" / MUNDO, ignore_errors=True)

    with TestClient(crear_app(RAIZ / "mundos")) as taller:
        taller.post("/mundos", json={"nombre": MUNDO})
        for ser_id, politica in [("vigia_normal", "normal"), ("vigia_radical", "se_radicaliza")]:
            r = taller.post(f"/seres?mundo={MUNDO}", json=_ser(ser_id, politica))
            r.raise_for_status()

        def transmitir(version_id: str, receptor: str, momento: str) -> dict:
            r = taller.post(f"/transmitir?mundo={MUNDO}", json={
                "emisor_id": "un_pescador", "receptor_id": receptor,
                "version_id": version_id, "momento": momento,
            })
            r.raise_for_status()
            return r.json()

        def peso_fe(ser_id: str) -> float:
            estado = taller.get(f"/seres/{ser_id}/estado?mundo={MUNDO}").json()
            return estado["faro-protector"]["peso"]

        print(f"Fe en el faro al arrancar: normal={peso_fe('vigia_normal'):.2f} "
              f"radical={peso_fe('vigia_radical'):.2f}\n")

        # El bombardeo: la misma noticia contradictoria para los dos.
        for i, noticia in enumerate(NOTICIAS, start=1):
            hecho_id = f"noticia-{i}"
            taller.post(f"/hechos?mundo={MUNDO}", json={
                "id": hecho_id, "contenido": noticia, "lugar": "el puerto",
                "momento": f"1850-03-{4 + i:02d}T09:00:00",
            }).raise_for_status()
            print(f"— Noticia {i}: «{noticia[:60]}…»")
            for ser_id in ("vigia_normal", "vigia_radical"):
                r = transmitir(f"{hecho_id}-raiz", ser_id, f"1850-03-{4 + i:02d}T10:00:00")
                grieta = "grieta ACTIVA" if r["tensiones"] else "sin grieta"
                movidos = ", ".join(
                    f"{m} {a:.2f}→{d:.2f}" for m, (a, d) in r["pesos_movidos"].items()
                ) or "pesos quietos"
                print(f"    {ser_id}: {grieta} · {movidos}")
            print(f"    fe: normal={peso_fe('vigia_normal'):.2f} "
                  f"radical={peso_fe('vigia_radical'):.2f}\n")

        # El hecho final, neutral: leer cómo lo recuenta cada uno.
        taller.post(f"/hechos?mundo={MUNDO}", json={
            "id": "la-flota-sale", "contenido": HECHO_FINAL, "lugar": "el puerto",
            "momento": "1850-03-10T09:00:00",
        }).raise_for_status()
        print(f"— Hecho final: «{HECHO_FINAL}»\n")
        for ser_id in ("vigia_normal", "vigia_radical"):
            r = transmitir("la-flota-sale-raiz", ser_id, "1850-03-10T10:00:00")
            grieta = "grieta ACTIVA" if r["tensiones"] else "sin grieta"
            print(f"=== {ser_id} ({grieta}) ===\n{r['version']['contenido']}\n")

        print("Todo quedó en la bitácora del mundo experimento_04: compará desde el Taller.")


if __name__ == "__main__":
    main()
