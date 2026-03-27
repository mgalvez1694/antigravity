"""
Módulo 4: Procesamiento geológico con shapefile local (PSAD56 UTM 19S)
Genera mapas regional y de detalle desde el shapefile local.
"""
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
import pandas as pd
import streamlit as st
from shapely.geometry import Point
from config import SHAPEFILE_PATH, CSV_ATRIBUTOS, SHAPEFILE_CRS, TEMP_DIR, COLOR_BG

# Cache del shapefile para no recargarlo en cada interacción
@st.cache_resource(show_spinner="Cargando shapefile geológico...")
def cargar_shapefile():
    gdf = gpd.read_file(SHAPEFILE_PATH)
    if gdf.crs is None:
        gdf = gdf.set_crs(SHAPEFILE_CRS)
    return gdf


@st.cache_data(show_spinner=False)
def cargar_atributos():
    df = pd.read_csv(CSV_ATRIBUTOS, encoding="utf-8", on_bad_lines="skip")
    return df


def intersectar_punto(norte_psad56: float, este_psad56: float) -> dict | None:
    """
    Intersecta el punto (PSAD56 UTM 19S) con el shapefile.
    Retorna los atributos de la unidad geológica intersectada.
    """
    gdf = cargar_shapefile()
    punto = Point(este_psad56, norte_psad56)
    resultado = gdf[gdf.geometry.contains(punto)]
    if resultado.empty:
        # Fallback: unidad más cercana
        gdf_copy = gdf.copy()
        gdf_copy["dist"] = gdf_copy.geometry.distance(punto)
        resultado = gdf_copy.nsmallest(1, "dist")

    if resultado.empty:
        return None

    row = resultado.iloc[0]
    # Enriquecer con CSV de atributos si tiene CD_GEOL
    cd_geol = row.get("CD_GEOL", None)
    datos_csv = {}
    if cd_geol:
        df_attr = cargar_atributos()
        mask = df_attr.get("CD_GEOL", pd.Series(dtype=str)).astype(str) == str(cd_geol)
        if mask.any():
            datos_csv = df_attr[mask].iloc[0].to_dict()

    return {
        "CD_GEOL":   str(cd_geol) if cd_geol else "—",
        "EDAD_MAX":  datos_csv.get("EDAD_MAX", row.get("EDAD_MAX", "—")),
        "EDAD_MIN":  datos_csv.get("EDAD_MIN", row.get("EDAD_MIN", "—")),
        "AMBIENTE":  datos_csv.get("AMBIENTE",  row.get("AMBIENTE",  "—")),
        "ROCA1":     datos_csv.get("ROCA1",     row.get("ROCA1",     "—")),
        "PROP_ROC1": datos_csv.get("PROP_ROC1", row.get("PROP_ROC1", "—")),
        "ROCA2":     datos_csv.get("ROCA2",     row.get("ROCA2",     "—")),
        "PROP_ROC2": datos_csv.get("PROP_ROC2", row.get("PROP_ROC2", "—")),
        "ROCA3":     datos_csv.get("ROCA3",     row.get("ROCA3",     "—")),
        "PROP_ROC3": datos_csv.get("PROP_ROC3", row.get("PROP_ROC3", "—")),
        "ROCA4":     datos_csv.get("ROCA4",     row.get("ROCA4",     "—")),
        "PROP_ROC4": datos_csv.get("PROP_ROC4", row.get("PROP_ROC4", "—")),
        "fid":       int(row.get("fid", 0)),
    }


def intersectar_poligono(feature_geojson: dict) -> dict | None:
    """
    Intersecta el polígono de una concesión (API Sernageomin) con el shapefile geológico.
    Retorna porcentajes exactos de las rocas superficiales principales.
    """
    poly_gdf = gpd.GeoDataFrame.from_features([feature_geojson], crs="EPSG:4326")
    try:
        poly_gdf = poly_gdf.to_crs(SHAPEFILE_CRS)
    except Exception:
        return None

    gdf = cargar_shapefile()
    geo_clean = gdf[gdf.is_valid & ~gdf.is_empty]
    
    try:
        cruce = gpd.overlay(geo_clean, poly_gdf, how="intersection", keep_geom_type=True)
    except Exception:
        return None

    if cruce.empty:
        return None

    cruce["area_ha"] = cruce.geometry.area / 10000.0
    area_total = cruce["area_ha"].sum()
    if area_total == 0: 
        return None

    agrupado = cruce.groupby(["CD_GEOL"]).agg({
        "area_ha": "sum", "AMBIENTE": "first", "EDAD_MAX": "first",
        "EDAD_MIN": "first", "ROCA1": "first", "fid": "first"
    }).reset_index().sort_values(by="area_ha", ascending=False)
    
    df_attr = cargar_atributos()
    datos = {}
    
    for i, row in enumerate(agrupado.itertuples()):
        if i >= 4: break
        cd_geol = row.CD_GEOL
        pct = (row.area_ha / area_total) * 100

        if i == 0:
            datos["CD_GEOL"] = str(cd_geol)
            datos["fid"] = row.fid
            datos["AMBIENTE"] = "—"
            datos["EDAD_MAX"] = "—"
            datos["EDAD_MIN"] = "—"
            datos["ROCA1"] = "—"
            
            mask = df_attr.get("CD_GEOL", pd.Series(dtype=str)).astype(str) == str(cd_geol)
            if mask.any():
                csv_r = df_attr[mask].iloc[0]
                datos["AMBIENTE"] = csv_r.get("AMBIENTE", row.AMBIENTE)
                datos["EDAD_MAX"] = csv_r.get("EDAD_MAX", row.EDAD_MAX)
                datos["EDAD_MIN"] = csv_r.get("EDAD_MIN", row.EDAD_MIN)
                datos["ROCA1"]    = csv_r.get("ROCA1", row.ROCA1)

            datos["PROP_ROC1"] = f"{pct:.1f}% del área ({row.area_ha:.1f} há)"
        else:
            datos[f"ROCA{i+1}"] = f"{cd_geol} / {row.ROCA1}"
            datos[f"PROP_ROC{i+1}"] = f"{pct:.1f}% del área"

    for i in range(1, 5):
        if f"ROCA{i}" not in datos: datos[f"ROCA{i}"] = "—"
        if f"PROP_ROC{i}" not in datos: datos[f"PROP_ROC{i}"] = "—"
        
    return datos


def generar_mapa_geologico(norte: float, este: float, 
                            etiqueta: str = "Faena",
                            feature_geojson: dict = None) -> tuple[str, str, str, str, str]:
    """
    Genera cinco PNGs:
    1. Mapa geológico 20 km²
    2. Mapa geológico 5 km²
    3. Mapa geológico 2 km²
    4. Mapa geológico regional
    5. Mapa geológico de detalle
    Retorna (path_20km, path_5km, path_2km, path_regional, path_detalle)
    """
    gdf = cargar_shapefile()
    punto = Point(este, norte)
    punto_gdf = gpd.GeoDataFrame(
        {"geometry": [punto], "label": [etiqueta]},
        crs=SHAPEFILE_CRS
    )

    # Colores por unidad
    unidades = gdf["CD_GEOL"].unique() if "CD_GEOL" in gdf.columns else []
    cmap = plt.cm.get_cmap("tab20", max(len(unidades), 1))
    color_map = {u: cmap(i) for i, u in enumerate(unidades)}

    # Preparar el polígono de la concesión si viene
    gdf_poli = None
    if feature_geojson:
        try:
            gdf_poli = gpd.GeoDataFrame.from_features([feature_geojson], crs="EPSG:4326")
            gdf_poli = gdf_poli.to_crs(gdf.crs)
        except Exception:
            gdf_poli = None

    def _plot_mapa(area_km: float, out_name: str, titulo: str) -> str:
        radio = (area_km ** 0.5) * 1000 / 2.0
        buf_geom = punto.buffer(radio * 1.5)
        recorte = gdf[gdf.geometry.intersects(buf_geom)].copy()

        fig, ax = plt.subplots(figsize=(10, 8), facecolor=COLOR_BG)
        ax.set_facecolor(COLOR_BG)

        if not recorte.empty:
            col_color = "CD_GEOL" if "CD_GEOL" in recorte.columns else None
            if col_color:
                c_list = recorte[col_color].map(color_map)
                recorte.plot(
                    ax=ax,
                    color=c_list,
                    legend=False,
                    edgecolor="white",
                    linewidth=0.3,
                    alpha=0.75,
                )
            else:
                recorte.plot(ax=ax, facecolor="#556B2F", edgecolor="white",
                             linewidth=0.3, alpha=0.75)

        # Polígono de la faena
        if gdf_poli is not None and not gdf_poli.empty:
            gdf_poli.plot(
                ax=ax, facecolor=(1, 0, 0, 0.4), edgecolor="red", linewidth=2.5, zorder=9
            )

        punto_gdf_m = punto_gdf.to_crs(gdf.crs) if punto_gdf.crs != gdf.crs else punto_gdf
        punto_gdf_m.plot(ax=ax, color="yellow", markersize=150,
                          marker="*", edgecolor="black", zorder=10)
        ax.annotate(etiqueta, xy=(este, norte), xytext=(8, 8),
                    textcoords="offset points", color="yellow",
                    fontsize=9, fontweight="bold")

        ax.set_xlim(este - radio, este + radio)
        ax.set_ylim(norte - radio, norte + radio)

        # Leyenda compacta
        if col_color and not recorte.empty:
            uniq = recorte[col_color].unique()
            patches = [mpatches.Patch(color=color_map[u], label=str(u)) for u in uniq[:12] if u in color_map]
            ax.legend(handles=patches, loc="lower right", fontsize=10,
                      facecolor="#2d2d2d", labelcolor="white", framealpha=0.8)

        ax.set_title(titulo, color="white", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("Este (m)", color="#aaa", fontsize=8)
        ax.set_ylabel("Norte (m)", color="#aaa", fontsize=8)
        ax.tick_params(colors="#aaa", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

        plt.tight_layout()
        out_path = os.path.join(TEMP_DIR, out_name)
        plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=COLOR_BG)
        plt.close()
        return out_path

    path_20km = _plot_mapa(20, "mapa_geo_20km.png", "Geología (Vista 20 km²)")
    path_5km  = _plot_mapa(5,  "mapa_geo_5km.png",  "Geología (Vista 5 km²)")
    path_2km  = _plot_mapa(2,  "mapa_geo_2km.png",  "Geología (Vista 2 km²)")
    # Radio 30km -> (30*2)^2 = 3600 km2
    path_regional = _plot_mapa(3600, "mapa_geologico_regional.png", "Geología Regional")
    # Radio 5km -> (5*2)^2 = 100 km2
    path_detalle  = _plot_mapa(100,  "mapa_geologico_detalle.png", "Geología de Detalle")
    # Radio 100km -> (100*2)^2 = 40000 km2
    path_provincial = _plot_mapa(40000, "mapa_geo_provincial.png", "Geología Provincial")
    
    return path_20km, path_5km, path_2km, path_regional, path_detalle, path_provincial


def render_geologia(coords: dict | None) -> dict | None:
    """Widget Streamlit para el módulo geológico."""
    st.subheader("🪨 Contexto Geológico")

    if not coords:
        st.info("Ingresa primero las coordenadas de la faena.")
        return None

    norte = coords["norte_psad56"]
    este  = coords["este_psad56"]

    if st.button("🔍 Analizar Geología de la Faena", use_container_width=True):
        with st.spinner("Intersectando concesión con el shapefile geológico..."):
            concesion_feature = st.session_state.get("concesion")
            datos_geo = None
            
            if concesion_feature and concesion_feature.get("geometry"):
                # Intersección matemática exacta de polígonos
                datos_geo = intersectar_poligono(concesion_feature)
            
            if not datos_geo:
                # Fallback: Intersección de punto central
                datos_geo = intersectar_punto(norte, este)
                
        if datos_geo:
            st.session_state["geologia"] = datos_geo
        else:
            st.warning("No se encontró unidad geológica para ese punto.")

    datos_geo = st.session_state.get("geologia")

    if datos_geo:
        st.success(f"✅ Unidad: **{datos_geo['CD_GEOL']}** — {datos_geo['AMBIENTE']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Código Geológico", datos_geo["CD_GEOL"])
            st.metric("Edad Máxima", str(datos_geo["EDAD_MAX"]))
        with col2:
            st.metric("Edad Mínima", str(datos_geo["EDAD_MIN"]))
            st.metric("Ambiente",    str(datos_geo["AMBIENTE"]))
        with col3:
            st.metric("Roca Principal", str(datos_geo["ROCA1"]))
            st.metric("Proporción",     str(datos_geo["PROP_ROC1"]))

        # Rocas secundarias
        rocas = []
        for i in range(2, 5):
            r = datos_geo.get(f"ROCA{i}", "—")
            p = datos_geo.get(f"PROP_ROC{i}", "—")
            if r and str(r) not in ("—", "nan", "None"):
                rocas.append({"Roca": r, "Proporción": p})
        if rocas:
            st.markdown("**Litología complementaria:**")
            st.dataframe(pd.DataFrame(rocas), use_container_width=True, hide_index=True)

        if st.button("🗺️ Generar mapas geológicos", use_container_width=True):
            nombre_faena = st.session_state.get("datos_faena", {}).get("nombre_faena", "Faena")
            concesion_feature = st.session_state.get("concesion")
            with st.spinner("Generando mapas (esto puede tardar unos segundos)..."):
                p_20, p_5, p_2, p_reg, p_det = generar_mapa_geologico(
                    norte, este, etiqueta=nombre_faena, feature_geojson=concesion_feature
                )
            st.session_state["mapa_geo_20"] = p_20
            st.session_state["mapa_geo_5"]  = p_5
            st.session_state["mapa_geo_2"]  = p_2
            st.session_state["mapa_geo_regional"] = p_reg
            st.session_state["mapa_geo_detalle"]  = p_det
            st.success("Mapas generados ✅")

        col_r, col_c, col_d = st.columns(3)
        with col_r:
            if st.session_state.get("mapa_geo_20"):
                st.image(st.session_state["mapa_geo_20"],
                         caption="Vista 20 km²",
                         use_container_width=True)
        with col_c:
            if st.session_state.get("mapa_geo_5"):
                st.image(st.session_state["mapa_geo_5"],
                         caption="Vista 5 km²",
                         use_container_width=True)
        with col_d:
            if st.session_state.get("mapa_geo_2"):
                st.image(st.session_state["mapa_geo_2"],
                         caption="Vista 2 km²",
                         use_container_width=True)

        return datos_geo

    return None
