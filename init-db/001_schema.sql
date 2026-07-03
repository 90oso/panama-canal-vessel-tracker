-- Habilitar la extensión espacial
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla maestra de buques
CREATE TABLE ships (
    mmsi        BIGINT PRIMARY KEY,
    name        VARCHAR(100),
    ship_type   VARCHAR(100),
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Última posición conocida (para el mapa en vivo)
CREATE TABLE vessel_positions_current (
    mmsi        BIGINT PRIMARY KEY REFERENCES ships(mmsi),
    geom        GEOMETRY(Point, 4326) NOT NULL,
    speed       NUMERIC(6,2),
    course      NUMERIC(6,2),
    heading     NUMERIC(6,2),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice espacial (clave para que las consultas geográficas sean rápidas)
CREATE INDEX idx_current_geom ON vessel_positions_current USING GIST (geom);

-- Histórico de posiciones (para trayectorias futuras)
CREATE TABLE vessel_positions_history (
    id          SERIAL PRIMARY KEY,
    mmsi        BIGINT NOT NULL REFERENCES ships(mmsi),
    geom        GEOMETRY(Point, 4326) NOT NULL,
    speed       NUMERIC(6,2),
    course      NUMERIC(6,2),
    heading     NUMERIC(6,2),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_history_geom ON vessel_positions_history USING GIST (geom);
CREATE INDEX idx_history_mmsi_time ON vessel_positions_history (mmsi, recorded_at);