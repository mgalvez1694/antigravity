"""
App Principal — Proyecto Prospección LOROS
Gálvez SpA — Sistema de generación de informes técnicos geológico-mineros
"""
import streamlit as st
import os

# ── Configuración de página (debe ser primera llamada) ───────────────────────
st.set_page_config(
    page_title="LOROS — Proyecto Prospección",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Dark Mode Corporativo ────────────────────────────────────────────────
st.markdown("""
<style>
/* === Fondo general === */
.stApp {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* === Sidebar === */
[data-testid="stSidebar"] {
    background-color: #252525;
    border-right: 1px solid #3a3a3a;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #cccccc;
}

/* === Headers === */
h1, h2, h3 { color: #D4A017 !important; }
h4, h5     { color: #e0e0e0 !important; }

/* === Botones === */
.stButton > button {
    background: linear-gradient(135deg, #D4A017, #b8860b);
    color: #1e1e1e;
    border: none;
    font-weight: 700;
    border-radius: 6px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e6b420, #D4A017);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(212,160,23,0.4);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #D4A017, #8B6914);
    font-size: 1.05rem;
    padding: 0.6rem 1rem;
}

/* === Inputs === */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #2d2d2d;
    color: #f0f0f0;
    border: 1px solid #444;
    border-radius: 6px;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #D4A017;
    box-shadow: 0 0 0 2px rgba(212,160,23,0.2);
}

/* === Radio buttons === */
.stRadio label { color: #cccccc !important; }
.stRadio div[role="radiogroup"] label[data-selected="true"] {
    color: #D4A017 !important;
}

/* === Métricas === */
[data-testid="stMetricValue"] {
    color: #D4A017 !important;
    font-weight: 700;
}
[data-testid="stMetricLabel"] { color: #aaaaaa !important; }

/* === Tablas Streamlit === */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {
    background-color: #252525;
    border-bottom: 2px solid #3a3a3a;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #2d2d2d;
    color: #cccccc;
    border-radius: 6px 6px 0 0;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #D4A017 !important;
    color: #1e1e1e !important;
}

/* === Info/Success/Error boxes === */
.stSuccess { background-color: #1a3a1a !important; color: #90EE90 !important; }
.stInfo    { background-color: #1a2a3a !important; color: #87CEEB  !important; }
.stWarning { background-color: #3a2a00 !important; color: #FFD700  !important; }
.stError   { background-color: #3a1a1a !important; color: #FF6B6B  !important; }

/* === Spinner === */
.stSpinner > div { border-color: #D4A017 transparent transparent transparent !important; }

/* === Expander === */
.streamlit-expanderHeader {
    background-color: #2d2d2d !important;
    color: #D4A017 !important;
    border-radius: 6px;
}

/* === Divider === */
hr { border-color: #3a3a3a !important; }

/* === File uploader === */
.stFileUploader label { color: #cccccc !important; }
.stFileUploader [data-testid="stFileDropzone"] {
    background-color: #2d2d2d;
    border: 2px dashed #D4A017;
    border-radius: 8px;
}

/* === Selectbox === */
.stSelectbox > div > div {
    background-color: #2d2d2d;
    color: #f0f0f0;
    border: 1px solid #444;
}

/* === Card personalizada === */
.loros-card {
    background: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-left: 4px solid #D4A017;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Importar módulos ─────────────────────────────────────────────────────────
from modules.auth import check_login, render_login, logout
from modules.coordenadas import render_coordenadas
from modules.sernageomin import render_sernageomin
from modules.geologia import render_geologia
from modules.laboratorio import render_laboratorio
from modules.interpretacion import render_interpretacion
from modules.pdf_export import render_exportar
from config import LOGO_BLANCO, COLOR_ACENTO

# ── Guard de autenticación ────────────────────────────────────────────────────
if not check_login():
    render_login()
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image(LOGO_BLANCO, width=180)
    except Exception:
        st.markdown("## 🦜 LOROS")

    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem;">
            <p style="color:#D4A017; font-weight:700; font-size:1.1rem; margin:0;">
                Proyecto Prospección
            </p>
            <p style="color:#888; font-size:0.8rem; margin:0;">
                Gálvez SpA — Sistema Interno
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # Datos básicos de la faena
    st.markdown("### 📋 Datos de la Faena")
    nombre_faena = st.text_input("Nombre de la Faena", 
                                  value=st.session_state.get("datos_faena", {}).get("nombre_faena", ""),
                                  placeholder="ej: LAS LOAS")
    cliente = st.text_input("Nombre del Cliente",
                             value=st.session_state.get("datos_faena", {}).get("cliente", ""),
                             placeholder="ej: JUAN PÉREZ")
    comuna  = st.text_input("Comuna",
                             value=st.session_state.get("datos_faena", {}).get("comuna", ""),
                             placeholder="ej: Andacollo")
    region  = st.selectbox("Región", [
        "IV Región — Coquimbo",
        "III Región — Atacama",
        "II Región — Antofagasta",
        "I Región — Tarapacá",
        "XV Región — Arica y Parinacota",
        "V Región — Valparaíso",
        "RM — Metropolitana",
        "VI Región — O'Higgins",
        "VII Región — Maule",
        "VIII Región — Biobío",
    ])

    if st.button("💾 Guardar datos faena", use_container_width=True):
        st.session_state["datos_faena"] = {
            "nombre_faena": nombre_faena.upper(),
            "cliente":      cliente.upper(),
            "comuna":       comuna.upper(),
            "region":       region,
        }
        st.success("Datos guardados ✔")

    st.divider()

    # Estado de completitud
    st.markdown("### ✅ Estado del Informe")
    pasos = {
        "Datos faena":     bool(st.session_state.get("datos_faena", {}).get("nombre_faena")),
        "Coordenadas":     st.session_state.get("coordenadas") is not None,
        "Legal (SNGM)":    st.session_state.get("concesion") is not None,
        "Geología":        st.session_state.get("geologia") is not None,
        "Laboratorio":     st.session_state.get("laboratorio") is not None,
        "Interpretación":  bool(st.session_state.get("interpretacion_texto")),
    }
    for paso, ok in pasos.items():
        st.markdown(f"{'✅' if ok else '⬜'} {paso}")

    progreso = sum(pasos.values()) / len(pasos)
    st.progress(progreso, text=f"Completado {int(progreso*100)}%")

    st.divider()

    # Logout
    usuario = st.session_state.get("usuario", "")
    st.markdown(f"<p style='color:#888; font-size:0.8rem;'>👤 {usuario}</p>",
                unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()

# ── Panel principal: Tabs ─────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; margin-bottom:1.5rem;">
        <h1 style="color:#D4A017; margin:0; font-size:2rem;">🦜 LOROS</h1>
        <p style="color:#888; margin:0; font-size:0.9rem;">
            Sistema de Prospección Geológico-Minera — Gálvez SpA
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "📍 Coordenadas",
    "⚖️ Propiedad Minera",
    "🪨 Geología",
    "🧪 Laboratorio",
    "🤖 Interpretación",
    "📄 Exportar PDF",
])

# ── Tab 1: Coordenadas ────────────────────────────────────────────────────────
with tabs[0]:
    coords = render_coordenadas()

# ── Tab 2: Propiedad Minera ───────────────────────────────────────────────────
with tabs[1]:
    if not st.session_state.get("datos_faena", {}).get("nombre_faena"):
        st.warning("⚠️ Guarda primero los datos de la faena en el sidebar.")
    coords_actual = st.session_state.get("coordenadas")
    concesion = render_sernageomin(coords_actual)

# ── Tab 3: Geología ───────────────────────────────────────────────────────────
with tabs[2]:
    coords_actual = st.session_state.get("coordenadas")
    geo = render_geologia(coords_actual)

# ── Tab 4: Laboratorio ────────────────────────────────────────────────────────
with tabs[3]:
    lab = render_laboratorio()

# ── Tab 5: Interpretación ─────────────────────────────────────────────────────
with tabs[4]:
    geo    = st.session_state.get("geologia")
    lab    = st.session_state.get("laboratorio")
    interp = render_interpretacion(geo, lab)

# ── Tab 6: Exportar PDF ───────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### Imágenes Google Earth")
    st.markdown(
        "<p style='color:#aaa; font-size:0.9rem;'>Sube las imágenes capturadas desde Google Earth Pro "
        "(Archivo → Guardar imagen) para incluirlas en el informe.</p>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        img_ubic   = st.file_uploader("📸 Ilustración 1: Ubicación espacial", type=["png","jpg","jpeg"], key="img_ub")
        img_ruta   = st.file_uploader("📸 Ilustración 2: Ruta de acceso",     type=["png","jpg","jpeg"], key="img_rt")
    with col2:
        img_prop   = st.file_uploader("📸 Ilustración 3: Propiedad Minera",   type=["png","jpg","jpeg"], key="img_pr")
        img_ingr   = st.file_uploader("📸 Ilustración 4: Ingreso a faena",    type=["png","jpg","jpeg"], key="img_in")

    # Guardar imágenes en temp
    def _save_img(uploaded, filename) -> str | None:
        if uploaded is None:
            return None
        from config import TEMP_DIR
        path = os.path.join(TEMP_DIR, filename)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        return path

    imagenes_ge = {
        "ubicacion": _save_img(img_ubic, "ge_ubicacion.png"),
        "ruta":      _save_img(img_ruta, "ge_ruta.png"),
        "propiedad": _save_img(img_prop, "ge_propiedad.png"),
        "ingreso":   _save_img(img_ingr, "ge_ingreso.png"),
    }

    st.divider()

    datos_faena   = st.session_state.get("datos_faena", {})
    coords_final  = st.session_state.get("coordenadas")
    concesion_raw = st.session_state.get("concesion")
    concesion_attr = concesion_raw["attributes"] if concesion_raw else None
    geo_final     = st.session_state.get("geologia")
    lab_final     = st.session_state.get("laboratorio")
    interp_final  = st.session_state.get("interpretacion_texto", "")

    render_exportar(
        datos_faena, coords_final, concesion_attr,
        geo_final, lab_final, interp_final, imagenes_ge
    )
