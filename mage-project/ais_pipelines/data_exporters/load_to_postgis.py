if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def load_to_postgis(vessels, *args, **kwargs):
    import pg8000.dbapi as pg8000

    conn = pg8000.connect(
        host="postgres",
        port=5432,
        database="ais_panama",
        user="ais_user",
        password="ais_pass",
    )
    cur = conn.cursor()

    for v in vessels:
        cur.execute("""
            INSERT INTO ships (mmsi, name, ship_type, first_seen, last_seen)
            VALUES (%s, %s, %s, now(), now())
            ON CONFLICT (mmsi) DO UPDATE SET
                name = EXCLUDED.name, ship_type = EXCLUDED.ship_type, last_seen = now();
        """, (v["mmsi"], v["name"], v["ship_type"]))

        cur.execute("""
            INSERT INTO vessel_positions_current (mmsi, geom, speed, course, heading, updated_at)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, now())
            ON CONFLICT (mmsi) DO UPDATE SET
                geom = EXCLUDED.geom, speed = EXCLUDED.speed,
                course = EXCLUDED.course, heading = EXCLUDED.heading, updated_at = EXCLUDED.updated_at;
        """, (v["mmsi"], v["lon"], v["lat"], v["speed"], v["course"], v["heading"]))

        cur.execute("""
            INSERT INTO vessel_positions_history (mmsi, geom, speed, course, heading, recorded_at)
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, now());
        """, (v["mmsi"], v["lon"], v["lat"], v["speed"], v["course"], v["heading"]))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Cargados {len(vessels)} buques desde Mage.")