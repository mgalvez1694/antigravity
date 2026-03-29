import streamlit as st
from pyproj import Transformer
import pydeck as pdk

# PSAD56 UTM 19S (Geología Sernageomin)
epsg_psad56 = "EPSG:24879"
# WGS84 UTM 19S (Google Earth, dispositivos modernos)
epsg_wgs84_utm = "EPSG:32719"
# WGS84 Geográficas (Lat/Lon)
epsg_wgs84_latlon = "EPSG:4326"

transformer_wgs84_to_psad56 = Transformer.from_crs(epsg_wgs84_latlon, epsg_psad56, always_xy=True)
transformer_utm_to_psad56   = Transformer.from_crs(epsg_wgs84_utm, epsg_psad56, always_xy=True)
transformer_psad56_to_latlon = Transformer.from_crs(epsg_psad56, epsg_wgs84_latlon, always_xy=True)


def get_map_pydeck(lon: float, lat: float) -> pdk.Deck:
    """Genera un mapa simple centrado en Lat/Lon usando Pydeck"""
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=14,
        pitch=0
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [lon, lat]}],
        get_position="position",
        get_color=[200, 30, 0, 160],
        get_radius=200,
    )
    return pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/satellite-v9")


def render_coordenadas() -> dict | None:
    """
    Formulario de Coordenadas
    Permite ingreso en PSAD56, WGS84 o Lat/Lon. Retorna dict con `norte_psad56` y `este_psad56`
    """
    st.subheader("📍 Datos de Ubicación")
    
    sistema = st.radio("Sistema de Entrada", ["PSAD56 UTM 19S", "WGS84 UTM 19S", "WGS84 Grados decimales"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        val1 = st.number_input("Norte / Latitud", format="%.6f", value=0.0)
    with col2:
        val2 = st.number_input("Este / Longitud", format="%.6f", value=0.0)

    coords_dict = None

    if st.button("✅ Confirmar coordenadas", use_container_width=True):
        if val1 == 0 and val2 == 0:
            st.warning("Introduce coordenadas distintas a cero.")
            return None
        
        norte_psad = 0
        este_psad = 0
        lon_wgs = 0
        lat_wgs = 0

        try:
            if "PSAD56" in sistema:
                norte_psad = val1
                este_psad = val2
                lon_wgs, lat_wgs = transformer_psad56_to_latlon.transform(este_psad, norte_psad)
            elif "UTM 19S" in sistema:
                este_psad, norte_psad = transformer_utm_to_psad56.transform(val2, val1)
                lon_wgs, lat_wgs = transformer_psad56_to_latlon.transform(este_psad, norte_psad)
            else:
                lat_wgs = val1
                lon_wgs = val2
                este_psad, norte_psad = transformer_wgs84_to_psad56.transform(lon_wgs, lat_wgs)

            coords_dict = {
                "norte_psad56": norte_psad,
                "este_psad56": este_psad,
                "lat": lat_wgs,
                "lon": lon_wgs
            }
            st.session_state["coordenadas"] = coords_dict
            st.success("Coordenadas guardadas en PSAD56 y WGS84.")
        except Exception as e:
            st.error(f"Error procesando coordenadas: {str(e)}")
            return None

    coords_actual = st.session_state.get("coordenadas")
    if coords_actual:
        st.pydeck_chart(get_map_pydeck(coords_actual["lon"], coords_actual["lat"]))
        return coords_actual
    
    return None
