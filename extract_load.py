import json
import os
import requests
import os
import json
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

import os
DB_CONFIG = {
    "host": "localhost",
    "port": int(os.environ.get("POSTGRES_PORT_HOST", 5433)),
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
}
API_KEY = os.environ.get("DATADOCKED_API_KEY")

# --- Configuración ---
USE_LIVE_API = False  # cámbialo a True solo cuando quieras gastar créditos reales
API_KEY = os.environ.get("DATADOCKED_API_KEY", "TU_API_KEY_AQUI")
SAMPLE_FILE = "sample_vessels_panama.json"

DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": 5433,  
    "dbname": "ais_panama",
    "user": "ais_user",
    "password": "ais_pass",
}


def extract():
    """Obtiene los datos crudos, ya sea de la API real o del archivo de muestra."""
    if USE_LIVE_API:
        headers = {"accept": "application/json", "x-api-key": API_KEY}
        params = {"latitude": 9.08, "longitude": -79.68, "circle_radius": 50}
        resp = requests.get(
            "https://datadocked.com/api/vessels_operations/get-vessels-by-area",
            headers=headers, params=params, timeout=15
        )
        resp.raise_for_status()
        return resp.json()["vessels"]
    else:
        with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["vessels"]


def transform(raw_vessels):
    """Limpia y estandariza los datos, descartando registros sin coordenadas válidas."""
    clean = []
    for v in raw_vessels:
        try:
            lat = float(v["latitude"])
            lon = float(v["longitude"])
        except (TypeError, ValueError):
            continue  # descarta buques sin posición válida

        clean.append({
            "mmsi": int(v["mmsi"]),
            "name": (v.get("name") or "UNKNOWN").strip(),
            "ship_type": v.get("typeSpecific") or "Unknown",
            "lat": lat,
            "lon": lon,
            "speed": float(v["speed"]) if v.get("speed") not in (None, "") else None,
            "course": float(v["course"]) if v.get("course") not in (None, "") else None,
            "heading": float(v["heading"]) if v.get("heading") not in (None, "") else None,
        })
    return clean


import pg8000.dbapi as pg8000

def load(vessels):
    """Carga a PostgreSQL/PostGIS: upsert en ships + current, insert en history."""
    conn = pg8000.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    cur = conn.cursor()

    for v in vessels:
        cur.execute("""
            INSERT INTO ships (mmsi, name, ship_type, first_seen, last_seen)
            VALUES (%s, %s, %s, now(), now())
            ON CONFLICT (mmsi) DO UPDATE SET
                name = EXCLUDED.name,
                ship_type = EXCLUDED.ship_type,
                last_seen = now();
        """, (v["mmsi"], v["name"], v["ship_type"]))

        cur.execute("""
            INSERT INTO vessel_positions_current (mmsi, geom, speed, course, heading, updated_at)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, now())
            ON CONFLICT (mmsi) DO UPDATE SET
                geom = EXCLUDED.geom, speed = EXCLUDED.speed,
                course = EXCLUDED.course, heading = EXCLUDED.heading,
                updated_at = EXCLUDED.updated_at;
        """, (v["mmsi"], v["lon"], v["lat"], v["speed"], v["course"], v["heading"]))

        cur.execute("""
            INSERT INTO vessel_positions_history (mmsi, geom, speed, course, heading, recorded_at)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, now());
        """, (v["mmsi"], v["lon"], v["lat"], v["speed"], v["course"], v["heading"]))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Cargados {len(vessels)} buques en la base de datos.")


if __name__ == "__main__":
    raw = extract()
    clean = transform(raw)
    load(clean)