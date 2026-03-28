import os
import requests
import simplekml
import pandas as pd
import geopandas as gpd
import streamlit as st
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point, shape, box
from config import SERNAGEOMIN_LAYER_CONCESION, SERNAGEOMIN_LAYER_VERTICE, TEMP_DIR

def sanitize_filename(name: str) -> str:
    """Evita errores de FileNotFoundError en Linux al crear archivos"""
    if not name:
        return "Concesion"
    for char in r"<>:/\|?*":
        name = name.replace(char, "_")
    return name.strip()


def query_arcgis_features(url: str, params: dict) -> list:
    """Consulta genérica a la API REST de ArcGIS"""
    try:
        response = requests.get(url, params=params, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("features", [])
    except Exception as e:
        print(f"Error consultando ArcGIS: {e}")
        return []


@st.cache_data(show_spinner=False)
def buscar_concesiones(norte: float, este: float, radio_km: float = 5.0) -> list:
    """Busca concesiones en un radio usando un bounding box en WGS84"""
    # Aproximación simple: 1 grado ~ 111 km
    radio_deg = radio_km / 111.0
    
    # Asumimos que los norte/este ingresados ya son Lat/Lon en la sesión 
    # (Lo transformamos en coordenadas.py y lo pasamos acá)
    # Pero si entran en UTM, toca transformar. Sernageomin usa PSAD56 UTM 19S (EPSG:24879) 
    # y los features devuelven geometría en EPSG:24879 por defecto o WGS84 según pedimos.
    
    # Para la API de Sernageomin, pedimos WGS84 outSR=4326
    params = {
        "where": "1=1",
        "geometry": f"{este-radio_deg},{norte-radio_deg},{este+radio_deg},{norte+radio_deg}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json"
    }
    
    features = query_arcgis_features(SERNAGEOMIN_LAYER_CONCESION, params)
    return features


def generar_catastro_minero(coord_dict: dict, radio_km: float) -> tuple:
    """
    Busca concesiones alrededor de coord_dict['lat'], coord_dict['lon']
    Retorna (figura_matplotlib, dataframe_concesiones, features_raw)
    """
    lat = coord_dict["lat"]
    lon = coord_dict["lon"]
    
    features = buscar_concesiones(lat, lon, radio_km)
    
    if not features:
        return None, pd.DataFrame(), []
        
    # Crear DataFrame
    data_list = []
    for f in features:
        attr = f.get("attributes", {})
        data_list.append({
            "NOMBRE": attr.get("NOMBRE", "S/N"),
            "TITULAR": attr.get("TITULAR", "Desconocido"),
            "TIPO": attr.get("TIPO_CONC", "—"),
            "ESTADO": attr.get("ESTADO", "—"),
            "ROL_NACIONAL": attr.get("ROL_NAC", "—"),
        })
        
    df = pd.DataFrame(data_list).drop_duplicates(subset=["NOMBRE"])
    
    # Crear GeoDataFrame para plotear
    gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    if gdf.empty:
        return None, df, features
        
    # Transformar a Web Mercator para usar contextily
    gdf_wm = gdf.to_crs(epsg=3857)
    pto_wm = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_wm.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2)
    pto_wm.plot(ax=ax, color="blue", marker="*", markersize=200, zorder=5)
    
    try:
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    except Exception:
        pass
        
    ax.set_axis_off()
    plt.tight_layout()
    
    return fig, df, features


def exportar_kmz(features: list, filename: str) -> str:
    """Crea un KMZ con los polígonos de las concesiones (API Sernageomin)"""
    kml = simplekml.Kml()
    for f in features:
        attr = f.get("attributes", {})
        geom = f.get("geometry", {})
        nombre = attr.get("NOMBRE", "Polígono")
        
        # Sernageomin polígonos vienen en anillos
        rings = geom.get("rings", [])
        if rings:
            pol = kml.newpolygon(name=nombre)
            # Asegurar longitud, latitud 
            coords = [(pt[0], pt[1]) for pt in rings[0]]
            pol.outerboundaryis = coords
            pol.style.linestyle.color = simplekml.Color.red
            pol.style.linestyle.width = 3
            pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.red)
            
    os.makedirs(TEMP_DIR, exist_ok=True)
    safe_name = sanitize_filename(filename)
    path = os.path.join(TEMP_DIR, f"{safe_name}.kmz")
    kml.savekmz(path)
    return path


def render_catastro():
    """UI interactiva en Streamlit para el catastro minero"""
    st.subheader("🏛️ Catastro Minero (Sernageomin)")
    if "coordenadas" not in st.session_state:
        st.info("Primero define las coordenadas en la pestaña 'Datos Iniciales'.")
        return
        
    coords = st.session_state["coordenadas"]
    radio = st.slider("Radio de Búsqueda (km)", min_value=1.0, max_value=50.0, value=5.0, step=1.0)
    
    if st.button("🔍 Buscar Catastro Minero", use_container_width=True, type="primary"):
        with st.spinner(f"Buscando concesiones a {radio} km..."):
            fig, df_concesiones, features = generar_catastro_minero(coords, radio)
            
            if df_concesiones.empty:
                st.warning("No se encontraron concesiones en ese radio.")
            else:
                st.session_state["catastro_df"] = df_concesiones
                st.session_state["catastro_features"] = features
                if fig:
                    img_path = os.path.join(TEMP_DIR, "catastro_tmp.png")
                    fig.savefig(img_path, bbox_inches="tight")
                    plt.close(fig)
                    st.session_state["catastro_img"] = img_path
                    
    if "catastro_df" in st.session_state:
        st.success(f"Se encontraron **{len(st.session_state['catastro_df'])}** concesiones.")
        st.dataframe(st.session_state["catastro_df"], use_container_width=True)
        
        if "catastro_img" in st.session_state:
            st.image(st.session_state["catastro_img"], caption="Catastro Minero Oficial")
            
        st.markdown("### Seleccionar Faena para Análisis Geológico")
        nombres = st.session_state["catastro_df"]["NOMBRE"].tolist()
        seleccionada = st.selectbox("Elige la concesión principal", options=nombres)
        
        if st.button("Fijar Concesión"):
            # Encontrar el feature
            feat = next((f for f in st.session_state["catastro_features"] 
                         if f.get("attributes", {}).get("NOMBRE") == seleccionada), None)
            if feat:
                st.session_state["concesion"] = feat
                st.session_state["datos_faena"] = {"nombre_faena": seleccionada}
                st.success(f"✅ Concesión **'{seleccionada}'** fijada como oficial para geología.")
                
        # KMZ
        if st.button("Descargar Catastro KMZ"):
            path_kmz = exportar_kmz(st.session_state["catastro_features"], f"Catastro_{radio}km")
            with open(path_kmz, "rb") as f:
                st.download_button("⬇️ Descargar Archivo KMZ", data=f, file_name=os.path.basename(path_kmz))
