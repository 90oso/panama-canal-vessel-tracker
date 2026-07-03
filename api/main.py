import os
from fastapi import FastAPI
import pg8000.dbapi as pg8000
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AIS Panama API")


def get_connection():
    return pg8000.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "AIS Panama API"}


@app.get("/locations")
def get_locations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.mmsi, s.name, s.ship_type,
               ST_X(c.geom) AS lon, ST_Y(c.geom) AS lat,
               c.speed, c.course, c.heading, c.updated_at
        FROM vessel_positions_current c
        JOIN ships s ON s.mmsi = c.mmsi;
    """)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

from fastapi import Query

@app.get("/locations/radius")
def get_locations_by_radius(
    lat: float = Query(..., description="Latitud del punto central"),
    lon: float = Query(..., description="Longitud del punto central"),
    dist: float = Query(..., description="Radio de búsqueda en kilómetros"),
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.mmsi, s.name, s.ship_type,
               ST_X(c.geom) AS lon, ST_Y(c.geom) AS lat,
               c.speed, c.course, c.heading,
               ST_Distance(
                   c.geom::geography,
                   ST_SetSRID(ST_MakePoint(%s::float8, %s::float8), 4326)::geography
               ) / 1000 AS distance_km
        FROM vessel_positions_current c
        JOIN ships s ON s.mmsi = c.mmsi
        WHERE ST_DWithin(
            c.geom::geography,
            ST_SetSRID(ST_MakePoint(%s::float8, %s::float8), 4326)::geography,
            %s::float8 * 1000
        )
        ORDER BY distance_km;
    """, (lon, lat, lon, lat, dist))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]