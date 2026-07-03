import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Tráfico de Buques - Canal de Panamá", layout="wide")
st.title("Tráfico de Buques en el Canal de Panamá")

# --- Sidebar: controles ---
st.sidebar.header("Filtros")
use_radius = st.sidebar.checkbox("Filtrar por radio desde un punto")

if use_radius:
    lat = st.sidebar.number_input("Latitud central", value=9.08, format="%.4f")
    lon = st.sidebar.number_input("Longitud central", value=-79.68, format="%.4f")
    dist = st.sidebar.slider("Radio (km)", min_value=1, max_value=50, value=15)
else:
    lat = lon = dist = None

# --- Obtener datos de la API ---
@st.cache_data(ttl=60)
def fetch_locations(lat=None, lon=None, dist=None):
    if lat is not None:
        resp = requests.get(f"{API_URL}/locations/radius", params={"lat": lat, "lon": lon, "dist": dist})
    else:
        resp = requests.get(f"{API_URL}/locations")
    resp.raise_for_status()
    return resp.json()

try:
    vessels = fetch_locations(lat, lon, dist)
except requests.exceptions.RequestException as e:
    st.error(f"No se pudo conectar a la API: {e}")
    st.stop()

st.sidebar.markdown(f"**Buques encontrados:** {len(vessels)}")

# --- Mapa ---
center = [lat, lon] if lat else [9.0, -79.6]
m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

if use_radius:
    folium.Circle(
        location=[lat, lon], radius=dist * 1000,
        color="#378ADD", fill=True, fill_opacity=0.08
    ).add_to(m)
    folium.Marker(
        location=[lat, lon], icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa")
    ).add_to(m)

for v in vessels:
    popup_text = f"<b>{v['name']}</b><br>Tipo: {v['ship_type']}<br>MMSI: {v['mmsi']}<br>Velocidad: {v['speed']} nudos"
    folium.CircleMarker(
        location=[v["lat"], v["lon"]],
        radius=4,
        color="#D85A30",
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=200),
    ).add_to(m)

st_folium(m, width=None, height=600)

# --- Tabla de datos ---
st.subheader("Detalle de buques")
import pandas as pd
df = pd.DataFrame(vessels)
st.dataframe(df, use_container_width=True)