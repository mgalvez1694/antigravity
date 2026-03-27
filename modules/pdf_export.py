"""
Módulo 7: Generador de informe técnico en PDF
Motor: ReportLab — Estructura basada en plantilla JEOVANA CORONADO
"""
import os
import io
from datetime import datetime
from typing import Optional

import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white, red
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus import ListFlowable, ListItem
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from config import LOGO_COLOR, LOGO_BLANCO, PDF_AUTHOR, PDF_SUBJECT, OUTPUT_DIR


# ── Colores corporativos ─────────────────────────────────────────────────────
DORADO   = HexColor("#D4A017")
OSCURO   = HexColor("#1e1e1e")
GRIS     = HexColor("#4a4a4a")
GRIS_CLR = HexColor("#f5f5f5")
ROJO_SEG = HexColor("#8B1A1A")

W, H = A4  # 595.28 x 841.89 pts


# ── Estilos ──────────────────────────────────────────────────────────────────
def _estilos():
    ss = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TituloPortada",
        parent=ss["Title"],
        fontSize=22,
        textColor=DORADO,
        spaceAfter=6,
        leading=28,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "SubPortada",
        parent=ss["Normal"],
        fontSize=14,
        textColor=white,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica",
    )
    h1 = ParagraphStyle(
        "H1",
        parent=ss["Heading1"],
        fontSize=13,
        textColor=DORADO,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        borderPad=2,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=ss["Heading2"],
        fontSize=11,
        textColor=GRIS,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body = ParagraphStyle(
        "Body",
        parent=ss["Normal"],
        fontSize=10,
        leading=15,
        textColor=HexColor("#222222"),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )
    tabla_header = ParagraphStyle(
        "TablaH",
        parent=ss["Normal"],
        fontSize=9,
        textColor=white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    return {
        "title": title_style, "sub": sub_style, "h1": h1,
        "h2": h2, "body": body, "tabla_h": tabla_header,
    }


# ── Header/Footer ─────────────────────────────────────────────────────────────
class _HeaderFooter:
    def __init__(self, nombre_faena: str, cliente: str):
        self.faena   = nombre_faena
        self.cliente = cliente
        self.logo    = LOGO_BLANCO if os.path.exists(LOGO_BLANCO) else (LOGO_COLOR if os.path.exists(LOGO_COLOR) else None)

    def __call__(self, canvas_obj: canvas.Canvas, doc):
        canvas_obj.saveState()
        # Header
        canvas_obj.setFillColor(OSCURO)
        canvas_obj.rect(0, H - 1.4 * cm, W, 1.4 * cm, fill=1, stroke=0)
        if self.logo:
            try:
                canvas_obj.drawImage(self.logo, 0.5 * cm, H - 1.25 * cm,
                                     width=2.5 * cm, height=1.0 * cm,
                                     preserveAspectRatio=True, mask="auto")
            except Exception:
                pass
        canvas_obj.setFillColor(DORADO)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(3.5 * cm, H - 0.9 * cm,
                              f"Proyecto Prospección — {self.faena}")
        canvas_obj.setFillColor(white)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(W - 0.8 * cm, H - 0.9 * cm,
                                   f"Gálvez SpA — {self.cliente}")
        # Footer
        canvas_obj.setFillColor(OSCURO)
        canvas_obj.rect(0, 0, W, 0.9 * cm, fill=1, stroke=0)
        canvas_obj.setFillColor(DORADO)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(0.8 * cm, 0.3 * cm, PDF_AUTHOR)
        canvas_obj.setFillColor(white)
        canvas_obj.drawRightString(W - 0.8 * cm, 0.3 * cm,
                                   f"Pág. {doc.page}")
        canvas_obj.restoreState()


# ── Portada ───────────────────────────────────────────────────────────────────
def _portada(datos: dict, e: dict) -> list:
    story = []
    # Fondo oscuro simulado con tabla
    story.append(Spacer(1, 1.5 * cm))

    # Logo centrado
    if os.path.exists(LOGO_COLOR):
        try:
            story.append(Image(LOGO_COLOR, width=7 * cm, height=2.5 * cm,
                                kind="proportional"))
        except Exception:
            pass
    story.append(Spacer(1, 0.5 * cm))

    # Mapa satelital en la portada
    mapa_portada = datos.get("mapa_propiedad_5")
    if mapa_portada and os.path.exists(mapa_portada):
        try:
            story.append(Image(mapa_portada, width=14 * cm, height=9 * cm, kind="proportional"))
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            pass

    # Línea dorada
    story.append(HRFlowable(width="90%", thickness=2, color=DORADO, spaceAfter=20))

    story.append(Paragraph(
        f"FAENAS SECTOR {datos.get('nombre_faena', '').upper()}",
        e["title"]
    ))
    story.append(Paragraph(
        f"SECTOR {datos.get('nombre_faena', '').upper()}",
        e["sub"]
    ))
    story.append(Paragraph(
        f"COMUNA DE {datos.get('comuna', '').upper()} — {datos.get('region', 'IV REGIÓN')} — CHILE",
        e["sub"]
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="90%", thickness=1, color=DORADO, spaceAfter=20))

    # Datos de identificación
    tabla_datos = [
        ["Cliente:", datos.get("cliente", "—")],
        ["Fecha:",   datetime.now().strftime("%d de %B de %Y")],
        ["Elaborado por:", "Gálvez SpA — Equipo de Prospección"],
    ]
    t = Table(tabla_datos, colWidths=[4 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), DORADO),
        ("TEXTCOLOR", (1, 0), (1, -1), HexColor("#333333")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story


# ── Sección genérica ───────────────────────────────────────────────────────────
def _seccion(titulo: str, contenido: str, e: dict) -> list:
    story = [Paragraph(titulo, e["h1"])]
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS, spaceAfter=8))
    for parrafo in contenido.strip().split("\n\n"):
        parrafo = parrafo.strip()
        if parrafo:
            story.append(Paragraph(parrafo.replace("\n", " "), e["body"]))
    return story


# ── Tabla de coordenadas ──────────────────────────────────────────────────────
def _tabla_coordenadas(coords: dict, e: dict) -> list:
    story = [Paragraph("Coordenadas del Punto de Faena", e["h2"])]
    data = [
        ["Sistema", "Norte / Latitud", "Este / Longitud"],
        ["PSAD56 UTM 19S",  f"{coords.get('norte_psad56', '—'):,.3f} m",
                             f"{coords.get('este_psad56', '—'):,.3f} m"],
        ["WGS84 UTM 19S",   f"{coords.get('norte_wgs84', '—'):,.3f} m",
                             f"{coords.get('este_wgs84', '—'):,.3f} m"],
        ["Lat / Lon WGS84", f"{coords.get('lat', '—'):.6f}°",
                             f"{coords.get('lon', '—'):.6f}°"],
    ]
    t = Table(data, colWidths=[5 * cm, 6 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), OSCURO),
        ("TEXTCOLOR",    (0, 0), (-1, 0), DORADO),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_CLR, white]),
        ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))
    return story


# ── Tabla propiedad minera ────────────────────────────────────────────────────
def _tabla_propiedad(concesion: dict, e: dict) -> list:
    story = []
    campos = [
        ("Nombre Concesión", concesion.get("NOMBRE", "—")),
        ("Titular",          concesion.get("TITULAR_NOMBRE", "—")),
        ("RUT Titular",      concesion.get("TITULAR_RUT", "—")),
        ("Rol Nacional",     f"{concesion.get('NUMERO_ROL', '—')}-{concesion.get('DV_ROL', '')}"),
        ("Tipo",             concesion.get("TIPO_CONCESION", "—")),
        ("Situación",        concesion.get("SITUACION_CONCESION", "—")),
        ("Hectáreas",        f"{concesion.get('HECTAREAS', '—')} há"),
        ("Comuna",           concesion.get("COMUNA", "—")),
        ("Origen",           concesion.get("ORIGEN", "—").replace("_", " ")),
        ("Fojas",            concesion.get("FOJAS", "—")),
        ("N° Inscripción",   concesion.get("NRO_INSCRIPCION", "—")),
        ("Año Inscripción",  concesion.get("ANO_INSCRIPCION", "—")),
    ]
    data = [["Campo", "Valor"]] + list(campos)
    t = Table(data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), OSCURO),
        ("TEXTCOLOR",    (0, 0), (-1, 0), DORADO),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_CLR, white]),
        ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    return story


# ── Tabla laboratorio ─────────────────────────────────────────────────────────
def _tabla_lab(df, titulo: str, e: dict) -> list:
    if df is None or len(df) == 0:
        return []
    story = [Paragraph(titulo, e["h2"])]
    headers = list(df.columns)
    data = [headers] + df.values.tolist()
    col_w = max(2.5 * cm, (17 * cm) / len(headers))
    t = Table(data, colWidths=[col_w] * len(headers))
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), OSCURO),
        ("TEXTCOLOR",    (0, 0), (-1, 0), DORADO),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_CLR, white]),
        ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    return story


# ── Imagen inline ─────────────────────────────────────────────────────────────
def _imagen(path: str, caption: str, e: dict, max_w: float = 15 * cm) -> list:
    if not path or not os.path.exists(path):
        return []
    story = []
    try:
        img = Image(path, width=max_w, height=9 * cm, kind="proportional")
        story.append(img)
        cap_style = ParagraphStyle("Caption", parent=e["body"],
                                   fontSize=8, textColor=GRIS, alignment=TA_CENTER,
                                   italics=True)
        story.append(Paragraph(caption, cap_style))
        story.append(Spacer(1, 0.4 * cm))
    except Exception:
        pass
    return story


# ── Generador principal ───────────────────────────────────────────────────────
def generar_pdf(
    datos_faena:   dict,
    coords:        dict | None,
    concesion:     dict | None,
    geo:           dict | None,
    lab:           dict | None,
    interpretacion: str,
    imagenes_ge:   dict,   # {"ubicacion": path, "ruta": path, "ingreso": path}
) -> str:
    """
    Genera el informe PDF completo y retorna la ruta del archivo.
    """
    nombre_faena  = datos_faena.get("nombre_faena", "Faena")
    cliente       = datos_faena.get("cliente", "Cliente")
    fecha_str     = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename  = f"Informe_{nombre_faena.replace(' ', '_')}_{fecha_str}.pdf"
    out_path      = os.path.join(OUTPUT_DIR, out_filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # ── Módulo Inteligencia (Generación dinámica de texto) ─────────────────
    import pandas as pd
    textos = {}
    tipo_yac = "mineral de prospección"
    max_au, max_cu = 0.0, 0.0
    if lab and lab.get("resultados") is not None:
        df_l = lab["resultados"]
        has_au, has_cu = False, False
        for c in df_l.columns:
            cu_col = str(c).upper()
            if "AU" in cu_col:
                has_au = True
                try: max_au = max(max_au, pd.to_numeric(df_l[c], errors='coerce').max())
                except: pass
            if "CU" in cu_col:
                has_cu = True
                try: max_cu = max(max_cu, pd.to_numeric(df_l[c], errors='coerce').max())
                except: pass
        if has_au and has_cu: tipo_yac = "mineralización mixta de oro y cobre"
        elif has_au: tipo_yac = "mineralización aurífera"
        elif has_cu: tipo_yac = "mineralización cuprífera"

    comuna = datos_faena.get("comuna", "la localidad")
    region = datos_faena.get("region", "IV Región")
    dist_km = datos_faena.get("dist_km")
    pueblo = datos_faena.get("pueblo_cercano")
    msnm = datos_faena.get("msnm")
    rutas_str = datos_faena.get("rutas_str", "caminos locales")

    dist_s = f" a unos {int(dist_km)} km de la ciudad capital, " if dist_km else " "
    pueblo_s = f" aledaño a la localidad de {pueblo}" if pueblo else ""
    ambiente = str(geo.get('AMBIENTE', 'rocas')).lower() if geo else "rocas formativas"
    cd_geol = geo.get('CD_GEOL', '') if geo else ""
    lito = str(geo.get('LITOLOGIA', 'unidades fracturadas')).lower() if geo else "unidades matriz"
    edad = geo.get('EDAD_MAX', 'histórica') if geo else "histórica"

    textos["intro"] = (
        f"El presente informe corresponde al estudio técnico de las muestras de {tipo_yac} obtenidas en el sector "
        f"{nombre_faena}, ubicado en la comuna de {comuna}{dist_s}y{pueblo_s} en {region}, Chile.\n\n"
        f"Este sector se emplaza en un ambiente geológico dominado por alteración hidrotermal "
        f"asociada a unidades de {ambiente}{', correspondientes a la unidad ' + cd_geol if cd_geol else ''}."
    )

    relieve = "relieve pre-cordillerano"
    if msnm:
        if msnm > 2500: relieve = "relieve cordillerano abrupto"
        elif msnm < 1000: relieve = "relieve pampa o llano"
    
    textos["accesos"] = (f"El Sector {nombre_faena} presenta características de {relieve}, situándose a una elevación "
                         f"media de {int(msnm)} m.s.n.m.\n\n" if msnm else "")
    textos["accesos"] += (f"El acceso principal a la zona de estudio se realiza transitando a través de las vías "
                          f"{rutas_str}, las cuales conectan directamente con los trazados internos de la operación.\n\n"
                          f"Las coordenadas referenciales de ingreso son:")

    ctx_geo = (f"Estructuralmente, el área de prospección está contenida dentro de {ambiente} ({lito}) "
               f"originadas en una edad {edad}. El control estructural evidencia favorabilidad para la circulación de fluidos.\n\n")
    if max_au > 0 or max_cu > 0:
        ctx_geo += (f"**Interpretación Analítica:** La campaña constata la presencia de {tipo_yac}, con valores máximos "
                    f"detectados de {f'{max_au:.2f} g/t Au' if max_au > 0 else ''}{' y ' if max_au>0 and max_cu>0 else ''}"
                    f"{f'{max_cu:.2f}% Cu' if max_cu > 0 else ''}. Estas anomalías apuntan a una posible "
                    f"fuente vinculada al fallamiento principal de {lito}.\n\n")
                    
    proc = "Lixiviación" if "óxido" in lito or "oxida" in ambiente else "Flotación"
    if "pórfido" in ambiente or "sulfuro" in lito: proc = "Flotación"
    ctx_geo += (f"**Procesamiento Metalúrgico Estimado:** Dada la naturaleza descrita ({lito}) y la mineralogía, el "
                f"procesamiento base pre-evaluado apunta a circuitos de beneficio por **{proc}**, sujeto a futuras "
                f"recuperaciones de prueba metalúrgica.")
    textos["contexto"] = ctx_geo
    # ── Fin Inteligencia ───────────────────────────────────────────────────────

    e = _estilos()
    hf = _HeaderFooter(nombre_faena, cliente)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=1.5 * cm,
        title=f"Informe Prospección — {nombre_faena}",
        author=PDF_AUTHOR,
        subject=PDF_SUBJECT,
    )

    story = []

    # ── 1. Portada ──────────────────────────────────────────────────────────
    story += _portada(datos_faena, e)
    # ── 2. Introducción ─────────────────────────────────────────────────────
    story += _seccion("1. INTRODUCCIÓN", textos["intro"], e)

    # ── 3. Ubicación y Accesos ───────────────────────────────────────────────
    story += _seccion("2. UBICACIÓN Y ACCESOS", textos["accesos"], e)
    if coords:
        story += _tabla_coordenadas(coords, e)

    # Imágenes Google Earth (subidas o automáticas)
    img_ubicacion = imagenes_ge.get("ubicacion") or datos_faena.get("mapa_ubicacion")
    if img_ubicacion:
        story += _imagen(img_ubicacion,
                         "Ilustración: Ubicación espacial referencial (Mapa Político)", e)
                         
    img_ruta = imagenes_ge.get("ruta") or datos_faena.get("mapa_ruta")
    if img_ruta:
        story += _imagen(img_ruta,
                         "Ilustración: Ruta de acceso desde ciudad principal", e)

    # ── 4. Propiedad Minera ──────────────────────────────────────────────────
    story.append(Paragraph("3. PROPIEDAD Y CATASTRO MINERO", e["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS, spaceAfter=8))
    if concesion:
        prop_text = (
            f"La zona de estudio cubre las hectáreas amparadas por la concesión "
            f"{concesion.get('TIPO_CONCESION', 'de exploración/explotación')} denominada "
            f"{concesion.get('NOMBRE', '—')}, con rol nacional "
            f"{concesion.get('NUMERO_ROL', '—')}-{concesion.get('DV_ROL', '')}."
        )
        story.append(Paragraph(prop_text, e["body"]))
        story.append(Spacer(1, 0.3 * cm))
        story += _tabla_propiedad(concesion, e)
    else:
        story.append(Paragraph("Sin datos de concesión registrados.", e["body"]))

    # Mapa propiedad minera
    mapa_prop_20 = datos_faena.get("mapa_propiedad_20")
    mapa_prop_5 = datos_faena.get("mapa_propiedad_5")
    mapa_prop_2 = datos_faena.get("mapa_propiedad_2")
    
    if mapa_prop_20:
        story += _imagen(mapa_prop_20, "Ilustración: Propiedad Minera (Vista 20 km²) — Sernageomin", e)
        
    mapa_catastro = datos_faena.get("mapa_catastro")
    if mapa_catastro:
        story += _imagen(mapa_catastro, "Ilustración: Catastro Minero (Radio ~2.5 km) con Roles Nacionales", e)
        
    if mapa_prop_5:
        story += _imagen(mapa_prop_5, "Ilustración: Propiedad Minera (Vista 5 km²) — Sernageomin", e)
    if mapa_prop_2:
        story += _imagen(mapa_prop_2, "Ilustración: Propiedad Minera (Vista 2 km²) — Sernageomin", e)
        
    img_ingreso = imagenes_ge.get("ingreso") or datos_faena.get("mapa_propiedad_025")
    if img_ingreso:
        story += _imagen(img_ingreso,
                         "Ilustración: Ubicación ingreso a faena", e)

    # ── 5. Contexto Geológico ────────────────────────────────────────────────
    story.append(Paragraph("4. CONTEXTO GEOLÓGICO", e["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS, spaceAfter=8))
    if geo:
        geo_text = (
            f"La zona de estudio se emplaza en unidades geológicas correspondientes a "
            f"{geo.get('CD_GEOL', '—')} ({geo.get('AMBIENTE', '—')}), "
            f"de edad {geo.get('EDAD_MAX', '—')} a {geo.get('EDAD_MIN', '—')}.\n\n"
            f"Litología principal: {geo.get('ROCA1', '—')} ({geo.get('PROP_ROC1', '—')})."
        )
        if str(geo.get("ROCA2", "—")) not in ("—", "nan", "None", ""):
            geo_text += f" Litología secundaria: {geo.get('ROCA2')} ({geo.get('PROP_ROC2')})."
        story.append(Paragraph(geo_text, e["body"]))
    else:
        story.append(Paragraph("Sin datos geológicos registrados.", e["body"]))

    # Mapas geológicos
    if datos_faena.get("mapa_geo_provincial"):
        story += _imagen(datos_faena["mapa_geo_provincial"],
                         "Ilustración: Geología Provincial", e)
                         
    if datos_faena.get("mapa_geo_regional"):
        story += _imagen(datos_faena["mapa_geo_regional"],
                         "Ilustración: Geología Regional", e)
    if datos_faena.get("mapa_geo_detalle"):
        story += _imagen(datos_faena["mapa_geo_detalle"],
                         "Ilustración: Geología de Detalle", e)

    if datos_faena.get("mapa_geo_20"):
        story += _imagen(datos_faena["mapa_geo_20"],
                         "Ilustración: Geología (Vista 20 km²)", e)
    if datos_faena.get("mapa_geo_5"):
        story += _imagen(datos_faena["mapa_geo_5"],
                         "Ilustración: Geología (Vista 5 km²)", e)

    # ── 6. Resultados Analíticos ─────────────────────────────────────────────
    story.append(Paragraph("5. RESULTADOS ANALÍTICOS", e["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS, spaceAfter=8))
    if lab and lab.get("resultados") is not None:
        if lab.get("folio"):
            story.append(Paragraph(f"Folio laboratorio: **{lab['folio']}**", e["body"]))
        story += _tabla_lab(lab["resultados"], "Tabla de resultados de análisis", e)
        if lab.get("retallas") is not None:
            story += _tabla_lab(lab["retallas"], "Resumen de Retallas", e)
    else:
        story.append(Paragraph("Sin datos de laboratorio registrados.", e["body"]))

    # ── 7. Interpretación y Conclusiones ─────────────────────────────────────
    if interpretacion:
        story += _seccion("6. INTERPRETACIÓN GEOLÓGICA Y CONCLUSIONES",
                          interpretacion, e)

    # ── Construir el PDF base ─────────────────────────────────────────────────
    doc.build(story, onFirstPage=hf, onLaterPages=hf)

    # ── Anexar PDF de laboratorio si existe ──────────────────────────────────
    pdf_lab_path = lab.get("pdf_path") if lab else None
    if pdf_lab_path and os.path.exists(pdf_lab_path):
        try:
            writer = PdfWriter()
            # Páginas del informe base
            base_reader = PdfReader(out_path)
            for page in base_reader.pages:
                writer.add_page(page)
            # Páginas del PDF de laboratorio
            lab_reader = PdfReader(pdf_lab_path)
            for page in lab_reader.pages:
                writer.add_page(page)
            # Guardar combinado
            with open(out_path, "wb") as f_out:
                writer.write(f_out)
        except Exception as e_pdf:
            pass  # Si falla la unión, el informe base igual se entrega

    return out_path


# ── Widget Streamlit ──────────────────────────────────────────────────────────
def render_exportar(datos_faena: dict, coords, concesion, geo, lab,
                    interpretacion: str, imagenes_ge: dict):
    """Panel de exportación final del informe."""
    st.subheader("📄 Exportar Informe")

    # Resumen de completitud
    checks = {
        "Datos faena":        bool(datos_faena.get("nombre_faena")),
        "Coordenadas":        coords is not None,
        "Propiedad minera":   concesion is not None,
        "Geología":           geo is not None,
        "Laboratorio":        lab is not None,
        "Interpretación":     bool(interpretacion),
    }
    for item, ok in checks.items():
        icon = "✅" if ok else "⚠️"
        st.markdown(f"{icon} {item}")

    st.divider()

    if st.button("🖨️ Generar Informe PDF", type="primary", use_container_width=True):
        # Enriquecer datos_faena con rutas de mapas
        datos_faena["mapa_propiedad_20"] = st.session_state.get("mapa_propiedad_20")
        datos_faena["mapa_propiedad_5"] = st.session_state.get("mapa_propiedad_5")
        datos_faena["mapa_propiedad_2"] = st.session_state.get("mapa_propiedad_2")
        datos_faena["mapa_propiedad_025"] = st.session_state.get("mapa_propiedad_025")
        datos_faena["mapa_geo_20"] = st.session_state.get("mapa_geo_20")
        datos_faena["mapa_geo_5"] = st.session_state.get("mapa_geo_5")
        datos_faena["mapa_geo_2"] = st.session_state.get("mapa_geo_2")
        datos_faena["mapa_geo_regional"] = st.session_state.get("mapa_geo_regional")
        datos_faena["mapa_geo_detalle"] = st.session_state.get("mapa_geo_detalle")
        datos_faena["mapa_geo_provincial"] = st.session_state.get("mapa_geo_provincial")
        datos_faena["mapa_ruta"] = st.session_state.get("mapa_ruta")
        datos_faena["mapa_catastro"] = st.session_state.get("mapa_catastro")
        datos_faena["mapa_ubicacion"] = st.session_state.get("mapa_ubicacion")
        datos_faena["dist_km"] = st.session_state.get("dist_km")

        with st.spinner("Generando informe técnico..."):
            try:
                pdf_path = generar_pdf(
                    datos_faena, coords, concesion, geo,
                    lab, interpretacion, imagenes_ge
                )
                st.success("✅ Informe generado correctamente")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "📥 Descargar Informe PDF",
                        data=f.read(),
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as ex:
                st.error(f"Error al generar PDF: {ex}")
