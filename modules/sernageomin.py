"""
Módulo 3: Integración con Catastro Sernageomin (ArcGIS FeatureServer)
+ Exportación KMZ para Google Earth
"""
import requests
import simplekml
import os
import subprocess
import streamlit as st
from config import (
    SERNAGEOMIN_LAYER_CONCESION,
    SERNAGEOMIN_LAYER_VERTICE,
    GOOGLE_EARTH_EXE,
    TEMP_DIR,
)


# ── Consultas al API ────────────────────────────────────────────────────────

def buscar_por_punto(lon: float, lat: float) -> dict | None:
    """Busca la concesión que contiene el punto (WGS84 lon/lat)."""
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join([
            "NUMERO_ROL","DV_ROL","NOMBRE","TITULAR_NOMBRE","TITULAR_RUT",
            "TITULAR_DV","HECTAREAS","SITUACION_CONCESION","TIPO_CONCESION",
            "ORIGEN","COMUNA","DATUM","HUSO","FECHA_VENCIMIENTO",
            "NRO_INSCRIPCION","FOJAS","ANO_INSCRIPCION","ID_CONCESION"
        ]),
        "returnGeometry": "true",
        "f": "geojson",
    }
    r = requests.get(SERNAGEOMIN_LAYER_CONCESION, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("features"):
        feat = data["features"][0]
        if "properties" in feat:
            feat["attributes"] = feat["properties"]
        return feat
    return None


def buscar_por_nombre(nombre: str) -> list:
    """Busca concesiones por nombre (LIKE)."""
    params = {
        "where": f"NOMBRE LIKE '%{nombre.upper()}%'",
        "outFields": "NUMERO_ROL,DV_ROL,NOMBRE,TITULAR_NOMBRE,HECTAREAS,SITUACION_CONCESION,TIPO_CONCESION,COMUNA,ID_CONCESION",
        "returnGeometry": "false",
        "f": "json",
    }
    r = requests.get(SERNAGEOMIN_LAYER_CONCESION, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("features", [])


def buscar_por_rol(rol_str: str) -> dict | None:
    """
    Busca por rol nacional. Acepta formatos: '04201038-6', '04102-2122-5'
    El API guarda NUMERO_ROL sin guión y prescindiendo del dígito verificador.
    """
    rol_str = rol_str.strip().replace(" ", "").replace(".", "")
    partes = rol_str.split("-")
    if len(partes) > 1:
        # Con guiones: unir todo menos el último bloque (que es el DV)
        numero_9 = "".join(partes[:-1])
    else:
        # Sin guiones: si tiene más de 9 caracteres, asumir que el último es DV
        if len(rol_str) > 9:
            numero_9 = rol_str[:-1]
        else:
            numero_9 = rol_str

    params = {
        "where": f"NUMERO_ROL='{numero_9}'",
        "outFields": ",".join([
            "NUMERO_ROL","DV_ROL","NOMBRE","TITULAR_NOMBRE","TITULAR_RUT",
            "HECTAREAS","SITUACION_CONCESION","TIPO_CONCESION","ORIGEN",
            "COMUNA","DATUM","HUSO","NRO_INSCRIPCION","FOJAS",
            "ANO_INSCRIPCION","ID_CONCESION"
        ]),
        "returnGeometry": "true",
        "f": "geojson",
    }
    r = requests.get(SERNAGEOMIN_LAYER_CONCESION, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("features"):
        feat = data["features"][0]
        if "properties" in feat:
            feat["attributes"] = feat["properties"]
        return feat
    return None


def obtener_vertices(id_concesion: str) -> list:
    """Retorna lista de vértices de la concesión."""
    params = {
        "where": f"ID_CONCESION='{id_concesion}'",
        "outFields": "NORTE,ESTE,NOMBRE,ID_CONCESION",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json",
    }
    r = requests.get(SERNAGEOMIN_LAYER_VERTICE, params=params, timeout=15)
    r.raise_for_status()
    features = r.json().get("features", [])
    vertices = []
    for f in features:
        attr = f["attributes"]
        geom = f.get("geometry", {})
        vertices.append({
            "nombre": attr.get("NOMBRE", ""),
            "norte":  attr.get("NORTE"),
            "este":   attr.get("ESTE"),
            "lon":    geom.get("x"),
            "lat":    geom.get("y"),
        })
    return vertices


# ── Generación de mapa propiedad minera ────────────────────────────────────

def generar_mapa_propiedad(feature_geojson: dict, lon_faena: float,
                            lat_faena: float, nombre: str) -> tuple[str, str, str, str]:
    """Genera 4 PNGs satelitales (20, 5, 2 y 0.25 km2) con polígono 50% y estrella."""
    import geopandas as gpd
    import contextily as ctx
    import matplotlib.pyplot as plt
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame.from_features([feature_geojson], crs="EPSG:4326")
    gdf_mercator = gdf.to_crs(epsg=3857)

    punto_gdf = gpd.GeoDataFrame(
        geometry=[Point(lon_faena, lat_faena)], crs="EPSG:4326"
    ).to_crs(epsg=3857)

    if not punto_gdf.empty:
        cx, cy = punto_gdf.geometry.x.iloc[0], punto_gdf.geometry.y.iloc[0]
    else:
        centroide = gdf_mercator.geometry.centroid.iloc[0]
        cx, cy = centroide.x, centroide.y

    def _generar(area_km: int, filename: str, zoom_lvl: int) -> str:
        radio = (area_km ** 0.5) * 1000 / 2.0
        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1e1e1e")

        gdf_mercator.plot(
            ax=ax, facecolor=(1, 0, 0, 0.4), edgecolor="red", linewidth=2.5, zorder=2
        )
        punto_gdf.plot(
            ax=ax, color="yellow", edgecolor="black", markersize=350,
            marker="*", alpha=1.0, zorder=5
        )

        ax.set_xlim(cx - radio, cx + radio)
        ax.set_ylim(cy - radio, cy + radio)

        # Descarga los tiles satelitales en alta resolución (Google Earth Satellite)
        google_sat = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        ctx.add_basemap(ax, source=google_sat, zoom=zoom_lvl, zorder=1)
        ax.set_title(f"Propiedad Minera — {nombre} ({area_km} km²)", color="white",
                     fontsize=14, pad=10, fontweight="bold")
        ax.set_axis_off()
        plt.tight_layout()

        out_path = os.path.join(TEMP_DIR, filename)
        plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="#1e1e1e")
        plt.close(fig)
        return out_path

    p20 = _generar(20, "mapa_prop_20km.png", 14)
    p5 = _generar(5, "mapa_prop_5km.png", 15)
    p2 = _generar(2, "mapa_prop_2km.png", 16)
    p025 = _generar(0.25, "mapa_prop_025km.png", 17)
    return p20, p5, p2, p025


# ── Exportación KMZ ────────────────────────────────────────────────────────

def exportar_kmz(feature_geojson: dict, vertices: list,
                  lon_faena: float, lat_faena: float, nombre_faena: str,
                  nombre_cliente: str) -> str:
    """Genera KMZ con polígono concesión + vértices + punto de faena."""
    kml = simplekml.Kml()
    folder = kml.newfolder(name=nombre_faena)

    # Polígono de la concesión
    coords_geom = feature_geojson.get("geometry", {}).get("coordinates", [[]])
    coords_ring = coords_geom[0] if coords_geom else []
    if coords_ring:
        pol = folder.newpolygon(name=f"Concesión {nombre_faena}")
        pol.outerboundaryis = [(c[0], c[1]) for c in coords_ring]
        pol.style.linestyle.color = simplekml.Color.red
        pol.style.linestyle.width = 2
        pol.style.polystyle.color = simplekml.Color.changealpha("80", simplekml.Color.red)

    # Vértices nombrados
    for v in vertices:
        pt = folder.newpoint(name=v["nombre"])
        pt.coords = [(v["lon"], v["lat"])]
        pt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/ltblu-diamond.png"
        pt.description = f"Norte PSAD56: {v['norte']}\nEste PSAD56: {v['este']}"

    # Punto de faena (estrella)
    faena_pt = folder.newpoint(name=f"Faena — {nombre_cliente}")
    faena_pt.coords = [(lon_faena, lat_faena)]
    faena_pt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/shapes/star.png"
    faena_pt.style.iconstyle.color = simplekml.Color.yellow
    faena_pt.style.iconstyle.scale = 1.5

    kmz_path = os.path.join(TEMP_DIR, f"{nombre_faena.replace(' ', '_')}.kmz")
    os.makedirs(os.path.dirname(kmz_path), exist_ok=True)
    kml.savekmz(kmz_path)
    return kmz_path


def abrir_google_earth(kmz_path: str):
    """Abre el KMZ directamente en Google Earth Pro."""
    if os.path.exists(GOOGLE_EARTH_EXE):
        subprocess.Popen([GOOGLE_EARTH_EXE, kmz_path])
    else:
        os.startfile(kmz_path)


# ── Catastro Minero a 20km2 ────────────────────────────────────────────────
def generar_catastro_minero(lon: float, lat: float, rol_objetivo: str = None, radio_km: float = 2.5) -> tuple:
    """Genera mapa + DataFrame de concesiones vecinas en radio configurable. Retorna (img_path, df)."""
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import contextily as ctx
    
    import pandas as pd
    
    delta_lat = radio_km / 111.0
    delta_lon = radio_km / 96.0
    params = {
        "geometry": f"{lon-delta_lon},{lat-delta_lat},{lon+delta_lon},{lat+delta_lat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "NOMBRE,NUMERO_ROL,DV_ROL,TIPO_CONCESION,TITULAR_NOMBRE,HECTAREAS,SITUACION_CONCESION,COMUNA",
        "returnGeometry": "true",
        "f": "geojson"
    }
    
    try:
        r = requests.get(SERNAGEOMIN_LAYER_CONCESION, params=params, timeout=20)
        data = r.json()
        if not data.get("features"):
            return None, None

        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326").to_crs(epsg=3857)
        
        # Construir tabla resumen
        cols_tabla = ["NOMBRE", "TITULAR_NOMBRE", "TIPO_CONCESION", "HECTAREAS", "NUMERO_ROL", "DV_ROL", "SITUACION_CONCESION", "COMUNA"]
        df_result = pd.DataFrame([{c: feat.get("properties", {}).get(c, "") for c in cols_tabla} for feat in data["features"]])
        df_result.rename(columns={
            "NOMBRE": "Concesión", "TITULAR_NOMBRE": "Titular", "TIPO_CONCESION": "Tipo",
            "HECTAREAS": "Há", "NUMERO_ROL": "N° Rol", "DV_ROL": "DV",
            "SITUACION_CONCESION": "Situación", "COMUNA": "Comuna"
        }, inplace=True)
        fig, ax = plt.subplots(figsize=(12, 10), facecolor="#1e1e1e")
        
        # Dibujar polígonos iterando
        for idx, row in gdf.iterrows():
            rol_actual = row.get("NUMERO_ROL", "")
            geom = row.geometry
            if not geom: continue
            
            # Subrayar objetivo en rojo y el resto en cyan
            if rol_objetivo and str(rol_actual) in str(rol_objetivo):
                facecolor = (1, 0, 0, 0.4)
                edgecolor = "red"
                lw = 2.5
            else:
                facecolor = (0, 0.5, 1, 0.2)
                edgecolor = "cyan"
                lw = 1.0
                
            gpd.GeoSeries([geom]).plot(ax=ax, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, zorder=2)
            
            # Etiqueta en el centroide (Rol Nacional)
            c = geom.centroid
            ax.annotate(str(rol_actual), xy=(c.x, c.y), ha='center', va='center',
                        color='white', fontsize=7, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.2", fc="black", ec="none", alpha=0.6), zorder=4)
                        
        cx, cy = gdf.geometry.centroid.x.mean(), gdf.geometry.centroid.y.mean()
        radio_m = radio_km * 1000
        ax.set_xlim(cx - radio_m, cx + radio_m)
        ax.set_ylim(cy - radio_m, cy + radio_m)
        
        google_sat = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        ctx.add_basemap(ax, source=google_sat, zorder=1)
        
        ax.set_title(f"Catastro Minero Vecinal (Radio {radio_km} km | área ≈ {int(radio_km*radio_km*3.14):.0f} km²)",
                     color="white", fontsize=15, pad=15, fontweight="bold")
        ax.set_axis_off()
        
        out_path = os.path.join(TEMP_DIR, "mapa_catastro.png")
        plt.tight_layout()
        plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="#1e1e1e")
        plt.close(fig)
        return out_path, df_result
    except Exception as e:
        print(f"Error generando catastro: {e}")
        return None, None

# ── Widget Streamlit ────────────────────────────────────────────────────────

def render_sernageomin(coords: dict | None) -> dict | None:
    """
    Panel de búsqueda de concesión minera. Retorna dict con datos o None.
    """
    st.subheader("⚖️ Propiedad Minera — Catastro Sernageomin")

    metodo = st.radio(
        "Buscar por",
        ["Rol Nacional", "Nombre Concesión", "Punto de faena (automático)"],
        horizontal=True,
    )

    feature = None

    if metodo == "Rol Nacional":
        rol = st.text_input("Rol Nacional", placeholder="ej: 04201038-6")
        if st.button("🔍 Buscar por Rol") and rol:
            with st.spinner("Consultando catastro..."):
                feature = buscar_por_rol(rol)

    elif metodo == "Nombre Concesión":
        nombre_busq = st.text_input("Nombre Concesión", placeholder="ej: ADRIANITA")
        if st.button("🔍 Buscar por Nombre") and nombre_busq:
            with st.spinner("Consultando catastro..."):
                resultados = buscar_por_nombre(nombre_busq)
            if resultados:
                opciones = {
                    f"{f['attributes']['NOMBRE']} — {f['attributes']['TITULAR_NOMBRE']} ({f['attributes']['HECTAREAS']} há)": f
                    for f in resultados
                }
                seleccion = st.selectbox("Selecciona la concesión", list(opciones.keys()))
                # Obtener con geometría
                id_sel = opciones[seleccion]["attributes"]["ID_CONCESION"]
                params = {"where": f"ID_CONCESION='{id_sel}'",
                          "outFields": "*", "returnGeometry": "true", "f": "geojson"}
                r = requests.get(SERNAGEOMIN_LAYER_CONCESION, params=params, timeout=15)
                data = r.json()
                if data.get("features"):
                    feature = data["features"][0]
            else:
                st.warning("No se encontraron concesiones.")

    else:  # Por punto
        if coords:
            with st.spinner("Buscando concesión en el punto..."):
                feature = buscar_por_punto(coords["lon"], coords["lat"])
            if not feature:
                st.info("No se encontró concesión en ese punto. Prueba buscar por rol o nombre.")
        else:
            st.info("Ingresa primero las coordenadas de la faena.")

    # Guardar en sesión si encontramos algo
    if feature:
        st.session_state["concesion"] = feature

    feature = feature or st.session_state.get("concesion")

    if feature:
        attr = feature["attributes"]
        id_c = attr.get("ID_CONCESION", "")

        st.success(f"✅ Concesión encontrada: **{attr.get('NOMBRE')}**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Titular", attr.get("TITULAR_NOMBRE", "—"))
            st.metric("Hectáreas", attr.get("HECTAREAS", "—"))
            st.metric("Tipo", attr.get("TIPO_CONCESION", "—"))
        with col2:
            st.metric("Situación", attr.get("SITUACION_CONCESION", "—"))
            st.metric("Comuna", attr.get("COMUNA", "—"))
            st.metric("Origen", attr.get("ORIGEN", "—").replace("_", " "))

        with st.expander("📋 Datos completos"):
            st.json({k: v for k, v in attr.items() if v is not None})

        # Vértices
        if id_c:
            with st.spinner("Obteniendo vértices..."):
                vertices = obtener_vertices(id_c)
            if vertices:
                import pandas as pd
                st.dataframe(pd.DataFrame(vertices), use_container_width=True)
                st.session_state["vertices"] = vertices
            else:
                st.warning("⚠️ API pública sin vértices. Polígono georreferenciado disponible vía capas secundarias.")
                st.session_state["vertices"] = []

        # ── CÁLCULO DE CENTROIDE (Fallback Automático) ──
        centroide = None
        # 1. Desde vértices si existen
        if st.session_state.get("vertices"):
            lats = [v["lat"] for v in st.session_state["vertices"] if v.get("lat")]
            lons = [v["lon"] for v in st.session_state["vertices"] if v.get("lon")]
            if lats and lons:
                centroide = (sum(lats)/len(lats), sum(lons)/len(lons))
        # 2. Respaldo: Desde el polígono en Base Geometry (FeatureServer/2)
        if not centroide:
            geom = feature.get("geometry", {})
            cords = geom.get("coordinates", [[]])[0] if geom else []
            if cords:
                lons = [c[0] for c in cords if c]
                lats = [c[1] for c in cords if c]
                if lats and lons:
                    centroide = (sum(lats)/len(lats), sum(lons)/len(lons))

        if centroide:
            st.info(f"📍 **Centroide del polígono:** Lat: {centroide[0]:.6f} | Lon: {centroide[1]:.6f}")
            if st.button("🔽 Usar centroide como Punto de Faena Oficial", use_container_width=True):
                from modules.coordenadas import normalizar_coordenadas
                st.session_state["coordenadas"] = normalizar_coordenadas("latlon", centroide[0], centroide[1])
                st.success("✅ ¡Punto oficial actualizado! Ya puedes analizar 🪨 Geología en este sitio.")

        # KMZ y Mapa
        col_kmz, col_map = st.columns(2)
        with col_kmz:
            nombre_faena = st.session_state.get("datos_faena", {}).get("nombre_faena", "Faena")
            nombre_cliente = st.session_state.get("datos_faena", {}).get("cliente", "Cliente")
            
            # Toma las coords de sesión si existen, sino usa el centroide recién calculado
            lon_f = coords["lon"] if coords else (centroide[1] if centroide else -71.09)
            lat_f = coords["lat"] if coords else (centroide[0] if centroide else -30.21)

            kmz_path = exportar_kmz(
                feature, 
                st.session_state.get("vertices", []),
                lon_f, lat_f, nombre_faena, nombre_cliente
            )
            with open(kmz_path, "rb") as f:
                st.download_button(
                    "📥 Descargar KMZ",
                    data=f.read(),
                    file_name=os.path.basename(kmz_path),
                    mime="application/vnd.google-earth.kmz",
                    use_container_width=True,
                )
            if st.button("🌍 Abrir en Google Earth", use_container_width=True):
                abrir_google_earth(kmz_path)

        with col_map:
            if st.button("🗺️ Generar mapas satelitales", use_container_width=True):
                with st.spinner("Generando mapas de alta resolución (esto tomará ~15 seg)..."):
                    mapa20, mapa5, mapa2, mapa025 = generar_mapa_propiedad(
                        feature, lon_f, lat_f, attr.get("NOMBRE", "")
                    )
                    st.session_state["mapa_propiedad_20"] = mapa20
                    st.session_state["mapa_propiedad_5"] = mapa5
                    st.session_state["mapa_propiedad_2"] = mapa2
                    st.session_state["mapa_propiedad_025"] = mapa025
                st.success("Mapas generados ✅")

        if st.session_state.get("mapa_propiedad_20"):
            st.image(st.session_state["mapa_propiedad_20"], caption="Vista 20 km²", use_container_width=True)
            st.image(st.session_state["mapa_propiedad_5"], caption="Vista 5 km²", use_container_width=True)
            st.image(st.session_state["mapa_propiedad_2"], caption="Vista 2 km²", use_container_width=True)
            st.image(st.session_state["mapa_propiedad_025"], caption="Vista 0.25 km²", use_container_width=True)

        return attr

    return None
