# Tráfico de Buques en el Canal de Panamá (AIS)

Proyecto semestral — Arquitectura y Exposición de Datos Geoespaciales.

Pipeline end-to-end que integra una fuente de datos AIS en tiempo real con un motor de almacenamiento espacial (PostGIS), expuesto vía API REST y visualizado en un dashboard interactivo, para monitorear el tráfico de buques en el Canal de Panamá.

## Arquitectura

```
DataDocked API (REST, AIS)
        |
        v
   Mage AI (orquestación)
        |
        v
  Script Python (Extract, Transform, Load)
        |
        v
  PostgreSQL + PostGIS (ships, current, history)
        |
        v
      FastAPI (endpoints REST)
        |
        v
   Streamlit (dashboard interactivo)
```
<img width="578" height="552" alt="Captura de pantalla 2026-07-22 183703" src="https://github.com/user-attachments/assets/bb85daeb-dd51-4f67-b523-056f752009bc" />



Todo el stack corre en contenedores Docker orquestados con Docker Compose.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Orquestación | Mage AI |
| Almacenamiento | PostgreSQL + PostGIS |
| Procesamiento | Python (pg8000, requests) |
| Backend / API | FastAPI + Uvicorn |
| Visualización | Streamlit + Folium |
| Infraestructura | Docker + Docker Compose |
| Fuente de datos | [DataDocked](https://datadocked.com) — endpoint `get-vessels-by-area` |

## Estructura del proyecto

```
proyecto-ais-panama/
├── docker-compose.yml
├── .env                        # credenciales locales (no versionado)
├── .env.example                # plantilla de referencia
├── .gitignore
├── init-db/
│   └── 001_schema.sql          # DDL: extensión PostGIS, tablas, índices espaciales
├── mage-project/
│   ├── requirements.txt        # dependencias extra del pipeline (pg8000)
│   ├── sample_vessels_panama.json  # datos de muestra para desarrollo sin gastar créditos
│   └── ais_pipelines/          # pipeline generado por Mage (bloques de extracción, transformación y carga)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                 # endpoints /locations y /locations/radius
└── dashboard/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py                  # dashboard Streamlit con mapa Folium
```

## Modelo de datos

Tres tablas normalizadas en PostgreSQL/PostGIS:

- **`ships`** — catálogo de buques (MMSI, nombre, tipo). No cambia con cada consulta.
- **`vessel_positions_current`** — última posición conocida de cada buque (una fila por MMSI, se actualiza con `UPSERT`). Es la que alimenta el mapa en vivo.
- **`vessel_positions_history`** — histórico completo de posiciones, nunca se sobrescribe. Base para trayectorias o análisis temporal futuro.

El campo `geom` usa el tipo espacial `GEOMETRY(Point, 4326)` de PostGIS, con índices `GIST` para consultas espaciales eficientes.

## Cómo levantar el proyecto

### Requisitos previos

- Docker y Docker Compose instalados.
- Una API key de [DataDocked](https://datadocked.com/dashboard/my_keys) (tier gratuito disponible).

### Pasos

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd proyecto-ais-panama
   ```

2. Copia la plantilla de variables de entorno y complétala con tus credenciales:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` y define `POSTGRES_PASSWORD` y `DATADOCKED_API_KEY`.

3. Levanta todo el stack:
   ```bash
   docker compose up -d --build
   ```

4. Verifica que los 4 contenedores estén corriendo:
   ```bash
   docker compose ps
   ```
   Deberías ver: `ais_postgres`, `ais_mage`, `ais_api`, `ais_dashboard`.

### Accesos

| Servicio | URL |
|---|---|
| Mage AI (orquestador) | http://localhost:6789 |
| API — documentación Swagger | http://localhost:8000/docs |
| API — endpoint de buques | http://localhost:8000/locations |
| API — búsqueda por radio | http://localhost:8000/locations/radius?lat=9.08&lon=-79.68&dist=15 |
| Dashboard | http://localhost:8501 |

## Pipeline de datos

El pipeline `ais_panama_ingesta` en Mage AI consta de tres bloques:

1. **`extract_vessels`** — obtiene los datos crudos, ya sea de la API en vivo de DataDocked o del archivo de muestra local (controlado por el flag `USE_LIVE_API`).
2. **`clean_vessels`** — limpia y estandariza los registros, descartando aquellos sin coordenadas válidas.
3. **`load_to_postgis`** — carga los datos a las tres tablas, usando `ST_MakePoint(lon, lat)` para construir la geometría espacial.

<img width="578" height="552" alt="image" src="https://github.com/user-attachments/assets/47ffa16e-6e08-4fbf-b1e4-6f2df6bb00c9" />


Un trigger programado ejecuta el pipeline automáticamente en intervalos definidos.

### Nota sobre el uso de la API en vivo

El tier gratuito de DataDocked tiene un número limitado de créditos. Por defecto, el pipeline usa datos de muestra (`USE_LIVE_API = False`) para permitir desarrollo y pruebas sin consumir créditos. Antes de una demostración con datos reales, cambia el flag a `True` en el bloque `extract_vessels`.

## Endpoints de la API

### `GET /locations`
Devuelve la última posición conocida de todos los buques registrados.

### `GET /locations/radius`
Devuelve los buques dentro de un radio (en km) alrededor de un punto dado, ordenados por distancia.

**Parámetros:**
- `lat` (float) — latitud del punto central
- `lon` (float) — longitud del punto central
- `dist` (float) — radio de búsqueda en kilómetros

**Ejemplo:**
```
GET /locations/radius?lat=9.08&lon=-79.68&dist=15
```

Implementado con `ST_DWithin` y `ST_Distance` de PostGIS, usando el tipo `geography` para cálculos de distancia reales sobre la superficie terrestre.

## Dashboard

El dashboard en Streamlit permite:
- Visualizar todos los buques activos en un mapa interactivo (Folium).
- Filtrar por radio desde un punto central definido por el usuario, consumiendo el endpoint espacial de la API.
- Consultar el detalle tabular de cada buque (MMSI, nombre, tipo, velocidad, rumbo, distancia).

## Autores
Rafael Batista

Daniel Salinas

Proyecto semestral — Tópicos Especiales II.
