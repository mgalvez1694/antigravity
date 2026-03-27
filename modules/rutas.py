import requests
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import shape, Point
from geopy.geocoders import Nominatim
import os
from config import TEMP_DIR

def obtener_elevacion(lat: float, lon: float) -> int | None:
    """Consulta la API de Open-Meteo para obtener m.s.n.m."""
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
        r = requests.get(url, timeout=10).json()
        if "elevation" in r and r["elevation"]:
            return int(r["elevation"][0])
    except:
        pass
    return None

def obtener_pueblo_cercano(lat: float, lon: float) -> str:
    """Usa geopy para ubicar el pueblo, villa o ciudad más cercana."""
    try:
        geolocator = Nominatim(user_agent="LOROS_Prospeccion_API")
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if location and location.raw.get("address"):
            addr = location.raw["address"]
            pueblo = addr.get("village", addr.get("town", addr.get("city", addr.get("county", ""))))
            return pueblo
    except:
        pass
    return ""

def trazar_ruta_acceso(comuna_origen: str, lon_faena: float, lat_faena: float) -> tuple[str | None, float | None, str | None, str | None]:
    """
    Geocodifica la comuna, calcula la ruta óptima usando OSRM hasta la faena,
    guarda mapas y extrae las autopistas/rutas principales transitadas.
    """
    # 1. Geocodificar Origen
    ciudad_busqueda = f"{comuna_origen}, Chile"
    if not comuna_origen or comuna_origen.strip() == "" or comuna_origen == "—":
        ciudad_busqueda = "La Serena, Chile" # Fallback por defecto Coquimbo
        
    try:
        geolocator = Nominatim(user_agent="LOROS_Prospeccion")
        location = geolocator.geocode(ciudad_busqueda)
        if not location:
            # Fallback
            location = geolocator.geocode("Santiago, Chile")
        lon1, lat1 = location.longitude, location.latitude
    except Exception:
        # Fallback a La Serena en caso de fallo de red en Geopy
        lon1, lat1 = -71.2489, -29.9045
        
    # 2. Obtener Ruta OSRM
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon_faena},{lat_faena}?overview=full&geometries=geojson&steps=true"
    try:
        res = requests.get(url, timeout=15).json()
        if 'routes' not in res or not res['routes']:
            return None, None, None, None
            
        geom = shape(res['routes'][0]['geometry'])
        dist_km = res['routes'][0]['distance'] / 1000.0
        
        # Parsear las rutas transitadas
        rutas_set = set()
        for leg in res['routes'][0].get('legs', []):
            for step in leg.get('steps', []):
                ref = step.get('ref', '')
                if ref: 
                    rutas_set.add(ref)
                else:
                    name = step.get('name', '')
                    if name and len(name) > 3:
                        rutas_set.add(name)
        
        rutas_str = " y ".join(list(rutas_set)[:3]) if rutas_set else "caminos locales conectados"
        
    except Exception:
        return None, None, None, None
        
    # 3. Dibujar
    try:
        gdf = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
        gdf_m = gdf.to_crs(epsg=3857)
        
        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1e1e1e")
        gdf_m.plot(ax=ax, color='#D4A017', linewidth=4, alpha=0.9, zorder=3) # Línea dorada
        
        # Puntos de inicio y fin
        pts = gpd.GeoDataFrame(
            {'geometry': [Point(lon1, lat1), Point(lon_faena, lat_faena)]},
            crs="EPSG:4326"
        ).to_crs(epsg=3857)
        
        # Origen verde, Faena amarillo
        pts.plot(ax=ax, color=['#00ff00', 'yellow'], markersize=[150, 300],
                 marker="*", edgecolor="black", zorder=5)
                 
        # Mapa base oscuro -> Google Maps standard
        google_maps = "http://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
        ctx.add_basemap(ax, source=google_maps, zorder=1)
        
        ax.set_title(f"Ruta de Acceso desde {comuna_origen} ({dist_km:.1f} km)",
                     color="white", fontsize=14, fontweight="bold", pad=15)
        ax.set_axis_off()
        
        out_path = os.path.join(TEMP_DIR, "ruta_acceso.png")
        plt.tight_layout()
        plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="#1e1e1e")
        plt.close(fig)
        
        # 4. Mapa Político / Ubicación
        fig2, ax2 = plt.subplots(figsize=(10, 8), facecolor="white")
        
        # Estrella principal
        pts_faena = gpd.GeoDataFrame(
            {'geometry': [Point(lon_faena, lat_faena)]}, crs="EPSG:4326"
        ).to_crs(epsg=3857)
        pts_faena.plot(ax=ax2, color='red', markersize=400, marker="*", edgecolor="black", zorder=5)
        
        # Establecemos un área grande (aprox 100km radio)
        cx, cy = pts_faena.geometry.x.iloc[0], pts_faena.geometry.y.iloc[0]
        radio_vis = 100000  # 100 km
        ax2.set_xlim(cx - radio_vis, cx + radio_vis)
        ax2.set_ylim(cy - radio_vis, cy + radio_vis)
        
        ctx.add_basemap(ax2, source=ctx.providers.CartoDB.Positron, zoom=8, zorder=1)
        ax2.set_title("Ubicación Referencial (Mapa Político)", color="black", fontsize=14, fontweight="bold", pad=15)
        ax2.set_axis_off()
        
        # ── Inset Map (Miniatura Nacional de Chile) ──
        # Posición [left, bottom, width, height] en la esquina inferior izquierda
        axins = ax2.inset_axes([0.02, 0.03, 0.22, 0.38])
        
        # Límites aproximados de Chile continental: lon -76 a -66, lat -56 a -17
        bounds_gdf = gpd.GeoDataFrame(
            {'geometry': [Point(-76, -56), Point(-66, -17)]}, crs="EPSG:4326"
        ).to_crs(epsg=3857)
        bx_min, by_min = bounds_gdf.geometry.x.iloc[0], bounds_gdf.geometry.y.iloc[0]
        bx_max, by_max = bounds_gdf.geometry.x.iloc[1], bounds_gdf.geometry.y.iloc[1]
        
        axins.set_xlim(bx_min, bx_max)
        axins.set_ylim(by_min, by_max)
        
        # Punto rojo grueso en el inset map para ubicar la faena a nivel nacional
        pts_faena.plot(ax=axins, color='red', markersize=180, marker="o", edgecolor="black", zorder=5)
        
        # Basemap nacional de bajo zoom para el recuadro
        ctx.add_basemap(axins, source=ctx.providers.CartoDB.PositronNoLabels, zoom=3, zorder=1, attribution="")
        
        # Bordes para que el recuadro parezca flotante
        axins.set_xticks([])
        axins.set_yticks([])
        for spine in axins.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(2)
        
        out_ubicacion = os.path.join(TEMP_DIR, "mapa_ubicacion_politica.png")
        plt.tight_layout()
        plt.savefig(out_ubicacion, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig2)
        
        return out_path, dist_km, out_ubicacion, rutas_str
    except Exception:
        return None, None, None, None
