"""
Módulo 2: Transformación de coordenadas
Soporta: PSAD56 UTM 19S / WGS84 UTM 19S / Latitud-Longitud
"""
from pyproj import Transformer
import streamlit as st

# Códigos EPSG
EPSG_PSAD56  = "EPSG:24879"   # PSAD56 / UTM zone 19S
EPSG_WGS84U  = "EPSG:32719"   # WGS84 / UTM zone 19S
EPSG_WGS84G  = "EPSG:4326"    # WGS84 geográfico (lat/lon)

SISTEMAS = {
    "UTM PSAD56 — Huso 19S (EPSG:24879)": "psad56",
    "UTM WGS84  — Huso 19S (EPSG:32719)": "wgs84utm",
    "Latitud / Longitud — WGS84 (EPSG:4326)": "latlon",
}


def utm_psad56_a_wgs84(norte: float, este: float) -> tuple:
    """PSAD56 UTM 19S → WGS84 (lat, lon)."""
    t = Transformer.from_crs(EPSG_PSAD56, EPSG_WGS84G, always_xy=True)
    lon, lat = t.transform(este, norte)
    return lat, lon


def utm_wgs84_a_wgs84(norte: float, este: float) -> tuple:
    """WGS84 UTM 19S → WGS84 (lat, lon)."""
    t = Transformer.from_crs(EPSG_WGS84U, EPSG_WGS84G, always_xy=True)
    lon, lat = t.transform(este, norte)
    return lat, lon


def wgs84_a_psad56(lat: float, lon: float) -> tuple:
    """WGS84 (lat, lon) → PSAD56 UTM 19S (norte, este)."""
    t = Transformer.from_crs(EPSG_WGS84G, EPSG_PSAD56, always_xy=True)
    este, norte = t.transform(lon, lat)
    return norte, este


def normalizar_coordenadas(sistema: str, v1: float, v2: float) -> dict:
    """
    Recibe (sistema, v1, v2) y devuelve dict con todas las representaciones.
    Para PSAD56/WGS84 UTM: v1=Norte, v2=Este
    Para LatLon: v1=Lat, v2=Lon
    """
    if sistema == "psad56":
        norte_psad56, este_psad56 = v1, v2
        lat, lon = utm_psad56_a_wgs84(norte_psad56, este_psad56)
        t = Transformer.from_crs(EPSG_WGS84G, EPSG_WGS84U, always_xy=True)
        este_wgs84, norte_wgs84 = t.transform(lon, lat)
    elif sistema == "wgs84utm":
        norte_wgs84, este_wgs84 = v1, v2
        lat, lon = utm_wgs84_a_wgs84(norte_wgs84, este_wgs84)
        norte_psad56, este_psad56 = wgs84_a_psad56(lat, lon)
    else:  # latlon
        lat, lon = v1, v2
        norte_psad56, este_psad56 = wgs84_a_psad56(lat, lon)
        t = Transformer.from_crs(EPSG_WGS84G, EPSG_WGS84U, always_xy=True)
        este_wgs84, norte_wgs84 = t.transform(lon, lat)

    return {
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "norte_psad56": round(norte_psad56, 3),
        "este_psad56":  round(este_psad56, 3),
        "norte_wgs84":  round(norte_wgs84, 3),
        "este_wgs84":   round(este_wgs84, 3),
    }


def render_coordenadas() -> dict | None:
    """
    Widget de ingreso de coordenadas. Retorna dict normalizado o None.
    """
    st.subheader("📍 Coordenadas de la Faena")

    # Opción GPS móvil
    try:
        from streamlit_js_eval import get_geolocation
        if st.button("📱 Usar GPS del dispositivo", use_container_width=True):
            loc = get_geolocation()
            if loc:
                st.session_state["gps_lat"] = loc["coords"]["latitude"]
                st.session_state["gps_lon"] = loc["coords"]["longitude"]
                st.success(f"GPS: {st.session_state['gps_lat']:.6f}, {st.session_state['gps_lon']:.6f}")
    except ImportError:
        pass

    sistema_label = st.radio(
        "Sistema de coordenadas",
        list(SISTEMAS.keys()),
        index=0,
        horizontal=False,
    )
    sistema = SISTEMAS[sistema_label]

    col1, col2 = st.columns(2)

    # Si hay GPS preloaded, usarlo como default
    gps_lat = st.session_state.get("gps_lat")
    gps_lon = st.session_state.get("gps_lon")

    # Coordenadas de ejemplo (Las Loas, Andacollo — datos reales)
    # JC (Jeovana Coronado): N 6.656.248,244 / E 298.134,557
    # JS (Jorge Salfate):    N 6.656.557,818 / E 297.724,236
    # FP (Francisco Pérez):  N 6.656.075,940 / E 298.389,145
    if sistema == "latlon":
        with col1:
            v1 = st.number_input("Latitud (°)", value=gps_lat if gps_lat else -30.21148,
                                  format="%.6f", step=0.000001)
        with col2:
            v2 = st.number_input("Longitud (°)", value=gps_lon if gps_lon else -71.09935,
                                  format="%.6f", step=0.000001)
    else:
        # Prefill desde GPS si está disponible; por defecto JC — Las Loas Andacollo
        if gps_lat and sistema == "psad56":
            norte_def, este_def = wgs84_a_psad56(gps_lat, gps_lon)
        else:
            norte_def, este_def = 6656248.244, 298134.557  # JC — Las Loas Andacollo (PSAD56)
        with col1:
            v1 = st.number_input("Norte (m)", value=norte_def, format="%.3f", step=1.0)
        with col2:
            v2 = st.number_input("Este (m)",  value=este_def,  format="%.3f", step=1.0)

    if st.button("✅ Confirmar coordenadas", use_container_width=True):
        try:
            coords = normalizar_coordenadas(sistema, v1, v2)
            st.session_state["coordenadas"] = coords
            st.success(f"Coordenadas confirmadas: {coords['lat']:.6f}°, {coords['lon']:.6f}°")
            return coords
        except Exception as e:
            st.error(f"Error en conversión: {e}")

    return st.session_state.get("coordenadas")
