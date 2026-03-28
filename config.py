"""
Configuración central de la app LOROS — Proyecto Prospección Gálvez SpA
"""
import os

# ── Rutas base ─────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SPECS_DIR  = os.path.join(BASE_DIR, "especificaciones")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# En nube Linux (Streamlit Cloud) usamos /tmp que siempre existe y es escribible.
# En Windows usamos carpetas locales junto al proyecto.
if os.name == "nt":  # Windows local
    TEMP_DIR   = os.path.join(BASE_DIR, "temp")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
else:               # Linux / Streamlit Cloud
    TEMP_DIR   = "/tmp/loros_temp"
    OUTPUT_DIR = "/tmp/loros_output"

os.makedirs(TEMP_DIR,   exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Shapefile geológico ─────────────────────────────────────────────────────
SHAPEFILE_PATH = os.path.join(SPECS_DIR, "shape geo", "mapa geo chile.shp")
CSV_ATRIBUTOS  = os.path.join(SPECS_DIR, "shape geo", "tabla de atributos.csv")
SHAPEFILE_CRS  = "EPSG:24879"   # PSAD56 / UTM zone 19S

# ── Logos ───────────────────────────────────────────────────────────────────
LOGO_COLOR  = os.path.join(ASSETS_DIR, "logo_color.png")
LOGO_BLANCO = os.path.join(ASSETS_DIR, "logo_blanco.png")

# ── Google Earth ────────────────────────────────────────────────────────────
GOOGLE_EARTH_EXE = r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe"

# ── API Sernageomin (ArcGIS) ────────────────────────────────────────────────
SERNAGEOMIN_BASE   = "https://services1.arcgis.com/OyjvVdFTl5hfSdX3/ArcGIS/rest/services/Marcelo_Layer/FeatureServer"
SERNAGEOMIN_LAYER_CONCESION = f"{SERNAGEOMIN_BASE}/2/query"
SERNAGEOMIN_LAYER_VERTICE   = f"{SERNAGEOMIN_BASE}/0/query"

# ── Usuarios del sistema ─────────────────────────────────────────────────────
USUARIOS = {
    "marcelo": "marcelo2026",
    "kenny": "kenny2026",
    "carlos": "carlos2026",
    "galvez": "loros2024",
    "admin":  "admin2024"
}

# ── Colores corporativos (Dark Mode) ─────────────────────────────────────────
COLOR_BG       = "#1e1e1e"
COLOR_SIDEBAR  = "#252525"
COLOR_ACENTO   = "#D4A017"   # Dorado corporativo
COLOR_TEXTO    = "#F0F0F0"
COLOR_CARD     = "#2d2d2d"

# ── Parámetros del PDF ───────────────────────────────────────────────────────
PDF_AUTHOR  = "Gálvez SpA — Proyecto Prospección"
PDF_SUBJECT = "Informe Técnico de Prospección Geológico-Minera"
