import os
import streamlit as st
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from config import LOGO_COLOR, TEMP_DIR, PDF_AUTHOR, PDF_SUBJECT

def generar_pdf(filepath: str, datos: dict) -> str:
    """
    Genera el informe PDF usando ReportLab.
    Retorna la ruta absoluta del archivo generado.
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
        author=PDF_AUTHOR,
        subject=PDF_SUBJECT,
        title=f"Informe_Geologico_{datos.get('nombre_faena', 'Faena')}"
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#003366"),
        spaceAfter=20,
        alignment=1
    )
    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#003366"),
        spaceBefore=15,
        spaceAfter=10
    )
    normal_style = styles["Normal"]
    
    story = []

    # Logo
    if os.path.exists(LOGO_COLOR):
        story.append(Image(LOGO_COLOR, width=1.5*inch, height=1.5*inch))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"INFORME GEOLÓGICO: {datos.get('nombre_faena', 'SIN NOMBRE').upper()}", title_style))
    story.append(Paragraph(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}", normal_style))
    story.append(Spacer(1, 20))

    # 1. Datos del Solicitante
    story.append(Paragraph("1. DATOS DEL SOLICITANTE", heading_style))
    data_solicitante = [
        ["Nombre Faena:", datos.get("nombre_faena", "—")],
        ["Titular:", datos.get("nombre_titular", "—")],
        ["RUT:", datos.get("rut_titular", "—")]
    ]
    t = Table(data_solicitante, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # 2. Coordenadas
    story.append(Paragraph("2. UBICACIÓN", heading_style))
    c = datos.get("coordenadas", {})
    if c:
        data_coord = [
            ["Norte (PSAD56)", f"{c.get('norte_psad56', 0):.2f}"],
            ["Este (PSAD56)", f"{c.get('este_psad56', 0):.2f}"],
            ["Latitud (WGS84)", f"{c.get('lat', 0):.6f}"],
            ["Longitud (WGS84)", f"{c.get('lon', 0):.6f}"]
        ]
        t2 = Table(data_coord, colWidths=[2*inch, 4*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightblue),
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]))
        story.append(t2)
    else:
        story.append(Paragraph("No se registraron coordenadas.", normal_style))
        
    story.append(Spacer(1, 10))

    # 3. Geología
    story.append(Paragraph("3. CONTEXTO GEOLÓGICO", heading_style))
    g = datos.get("geologia", {})
    if g:
        data_geo = [
            ["Unidad", g.get("CD_GEOL", "—")],
            ["Ambiente", g.get("AMBIENTE", "—")],
            ["Edad", f"{g.get('EDAD_MIN', '—')} - {g.get('EDAD_MAX', '—')}"],
            ["Roca Principal", g.get("ROCA1", "—")],
            ["Porcentaje Área", str(g.get("PROP_ROC1", "—"))]
        ]
        t3 = Table(data_geo, colWidths=[2*inch, 4*inch])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgreen),
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]))
        story.append(t3)
    else:
        story.append(Paragraph("Sin datos de geología.", normal_style))

    # Incorporar mapa_geo_5km si existe
    if os.path.exists(datos.get("mapa_geo_5", "")):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Mapa Geológico (5 km x 5 km)", normal_style))
        story.append(Image(datos.get("mapa_geo_5"), width=4.5*inch, height=4*inch))

    story.append(PageBreak())

    # 4. Catastro Minero (Sernageomin)
    story.append(Paragraph("4. CATASTRO MINERO", heading_style))
    if os.path.exists(datos.get("catastro_img", "")):
        story.append(Image(datos.get("catastro_img"), width=5*inch, height=5*inch))
        story.append(Spacer(1, 15))
        
    df_catastro = datos.get("catastro_df", pd.DataFrame())
    if not df_catastro.empty:
        # Convertir a matriz para tabla
        tabla_cat = [df_catastro.columns.tolist()] + df_catastro.head(10).values.tolist()
        tc = Table(tabla_cat, colWidths=[1.5*inch]*len(df_catastro.columns))
        tc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        story.append(tc)

    story.append(Spacer(1, 15))

    # 5. Laboratorio
    story.append(Paragraph("5. RESULTADOS DE LABORATORIO", heading_style))
    l = datos.get("laboratorio", {})
    if l:
        muestras = l.get("muestras", [])
        if muestras:
            # Asume dicts con Muestra y Ley Au
            keys = list(muestras[0].keys())
            tabla_lab = [keys] + [[str(m.get(k, "")) for k in keys] for m in muestras]
            tl = Table(tabla_lab, colWidths=[2*inch, 2*inch])
            tl.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.gold),
                ('GRID', (0,0), (-1,-1), 1, colors.grey)
            ]))
            story.append(tl)
            
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Retalla / Oro libre: {l.get('retalla', 0)} g/t", normal_style))

    story.append(Spacer(1, 15))

    # 6. Interpretación
    story.append(Paragraph("6. CONCLUSIONES GEOLÓGICO-MINERAS", heading_style))
    inter_text = datos.get("interpretacion", "No se adjuntaron conclusiones.")
    story.append(Paragraph(inter_text, normal_style))

    # Guardar
    doc.build(story)
    return filepath


def render_exportar(datos_faena, coords_final, concesion_attr, geo_final, lab_final, interp_final, imagenes_ge):
    st.subheader("📄 Generación de Informe PDF")
    
    if st.button("🖨️ Generar Informe Final", use_container_width=True, type="primary"):
        with st.spinner("Compilando el documento técnico..."):
            datos = {
                "nombre_faena": datos_faena.get("nombre_faena", "Faena 1") if datos_faena else "Faena 1",
                "nombre_titular": datos_faena.get("cliente", "S/N") if datos_faena else "S/N",
                "rut_titular": "S/N",
                "coordenadas": coords_final or {},
                "geologia": geo_final or {},
                "mapa_geo_5": st.session_state.get("mapa_geo_5", ""),
                "catastro_img": st.session_state.get("mapa_propiedad_5", ""), 
                "laboratorio": lab_final or {},
                "interpretacion": interp_final or ""
            }
            
            os.makedirs(TEMP_DIR, exist_ok=True)
            out_file = os.path.join(TEMP_DIR, "Informe_Prospeccion.pdf")
            try:
                generar_pdf(out_file, datos)
                st.success("✅ Informe PDF generado exitosamente.")
                with open(out_file, "rb") as pdf_file:
                    st.download_button(
                        label="⬇️ Descargar Informe PDF",
                        data=pdf_file,
                        file_name="Informe_Prospeccion.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error generando PDF: {str(e)}")
