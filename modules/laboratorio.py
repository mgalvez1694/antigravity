"""
Módulo 5: Extracción de datos de laboratorio desde PDF o Excel
Compatible con informes FGF Análisis Minero (formato Coquimbo)
"""
import os
import re
import pdfplumber
import pandas as pd
import streamlit as st
from config import TEMP_DIR


def _extraer_tabla_pdf(pdf_path: str) -> pd.DataFrame | None:
    """
    Extrae las tablas del informe FGF.
    Detecta la tabla de resultados y la tabla de retallas.
    """
    dfs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                # Limpiar tabla
                df = pd.DataFrame(table[1:], columns=table[0])
                df.columns = [str(c).strip() if c else f"col_{i}"
                              for i, c in enumerate(df.columns)]
                df = df.dropna(how="all").reset_index(drop=True)
                if len(df) > 0 and len(df.columns) >= 2:
                    dfs.append(df)

    if not dfs:
        return None

    # Buscar la tabla con columnas de análisis (Au, Ag, etc.)
    for df in dfs:
        cols_str = " ".join(df.columns).lower()
        if any(x in cols_str for x in ["au", "ag", "cu", "código", "codigo", "descripcion"]):
            return df

    return dfs[0] if dfs else None


def _extraer_texto_pdf(pdf_path: str) -> str:
    """Extrae todo el texto del PDF para parsing alternativo."""
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"
    return texto


def _parsear_texto_laboratorio(texto: str) -> pd.DataFrame | None:
    """
    Parsing de texto cuando las tablas no se detectan correctamente.
    Busca patrones de código + descripción + valores numéricos.
    """
    lineas = texto.split("\n")
    filas = []
    cabecera = None

    for linea in lineas:
        linea = linea.strip()
        # Buscar encabezado
        if re.search(r'(c[oó]d|código|descripci)', linea, re.I):
            partes = re.split(r'\s{2,}|\t', linea)
            if len(partes) >= 3:
                cabecera = [p.strip() for p in partes if p.strip()]
            continue
        # Buscar filas de datos (código numérico + descripción + número)
        m = re.match(r'(\d{5,})\s+(.+?)\s+([\d.,]+)', linea)
        if m:
            codigo = m.group(1)
            desc   = m.group(2).strip()
            val    = m.group(3)
            filas.append({"Código": codigo, "Descripción": desc, "Au (g/t)": val})

    if filas:
        return pd.DataFrame(filas)
    return None


def _extraer_retallas(texto: str) -> pd.DataFrame | None:
    """Extrae la tabla de resumen de retallas."""
    filas = []
    en_retallas = False
    for linea in texto.split("\n"):
        if "retalla" in linea.lower():
            en_retallas = True
            continue
        if en_retallas:
            # Buscar líneas con código + valores numéricos separados
            nums = re.findall(r'[\d.,]+', linea)
            desc = re.sub(r'[\d.,]+', '', linea).strip()
            if len(nums) >= 4 and desc:
                filas.append({
                    "Código":       nums[0] if len(nums) > 0 else "",
                    "Descripción":  desc,
                    "Au Fino (g/t)":   nums[1] if len(nums) > 1 else "",
                    "Au Grueso (g/t)": nums[2] if len(nums) > 2 else "",
                    "Promedio (g/t)":  nums[3] if len(nums) > 3 else "",
                    "Ley Retalla":     nums[-1] if len(nums) > 4 else "",
                })
        if en_retallas and len(filas) > 10:
            break

    return pd.DataFrame(filas) if filas else None


def procesar_laboratorio(archivo) -> dict:
    """
    Procesa un archivo subido (PDF o Excel).
    Retorna dict con: 'resultados' (DataFrame), 'retallas' (DataFrame), 'texto' (str)
    """
    nombre = archivo.name.lower()
    resultado = {"resultados": None, "retallas": None, "texto": "", "folio": ""}

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        df = pd.read_excel(archivo)
        resultado["resultados"] = df

    elif nombre.endswith(".pdf"):
        # Guardar temporalmente
        tmp_path = os.path.join(TEMP_DIR, archivo.name)
        with open(tmp_path, "wb") as f:
            f.write(archivo.read())

        texto = _extraer_texto_pdf(tmp_path)
        resultado["texto"] = texto

        # Extraer folio
        m_folio = re.search(r'[Ff]olio\s*[:\s]*(\d+)', texto)
        if m_folio:
            resultado["folio"] = m_folio.group(1)

        # Intentar extracción de tablas
        df_tabla = _extraer_tabla_pdf(tmp_path)
        if df_tabla is not None and len(df_tabla) > 0:
            resultado["resultados"] = df_tabla
        else:
            df_texto = _parsear_texto_laboratorio(texto)
            resultado["resultados"] = df_texto

        # Retallas
        df_ret = _extraer_retallas(texto)
        resultado["retallas"] = df_ret

        # Guardar path del PDF original para el anexo del informe final
        resultado["pdf_path"] = tmp_path

    return resultado


def render_laboratorio() -> dict | None:
    """Widget Streamlit para el módulo de laboratorio."""
    st.subheader("🧪 Datos de Laboratorio")

    archivo = st.file_uploader(
        "Sube el informe de laboratorio (PDF o Excel)",
        type=["pdf", "xlsx", "xls"],
        help="Compatible con informes FGF Análisis Minero",
    )

    if archivo:
        with st.spinner("Procesando informe de laboratorio..."):
            datos = procesar_laboratorio(archivo)
        st.session_state["laboratorio"] = datos

        if datos.get("folio"):
            st.info(f"📄 Folio detectado: **{datos['folio']}**")

        if datos["resultados"] is not None and len(datos["resultados"]) > 0:
            st.markdown("**Resultados de análisis:**")
            df_edit = st.data_editor(
                datos["resultados"],
                use_container_width=True,
                num_rows="dynamic",
                key="editor_lab",
            )
            st.session_state["laboratorio"]["resultados"] = df_edit
        else:
            st.warning("No se detectaron tablas automáticamente. Ingresa los datos manualmente:")
            df_manual = pd.DataFrame({
                "Código":       [""],
                "Descripción":  [""],
                "Au (g/t)":     [""],
                "Au Fino (g/t)":[""],
                "Au Grueso (g/t)":[""],
            })
            df_edit = st.data_editor(df_manual, use_container_width=True,
                                      num_rows="dynamic", key="editor_manual")
            if not df_edit.empty:
                st.session_state["laboratorio"] = {
                    "resultados": df_edit, "retallas": None, "texto": "", "folio": ""
                }

        if datos.get("retallas") is not None and len(datos["retallas"]) > 0:
            st.markdown("**Resumen de Retallas:**")
            st.dataframe(datos["retallas"], use_container_width=True)

        return st.session_state.get("laboratorio")

    return st.session_state.get("laboratorio")
