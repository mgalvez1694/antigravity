"""
Módulo 6: Generación de interpretación geológica
Lógica determinística + texto editable por el usuario
"""
import streamlit as st


def generar_interpretacion(geo: dict, lab: dict | None) -> str:
    """
    Genera un texto interpretativo en base a los datos geológicos y de laboratorio.
    Lógica determinística (no requiere LLM externo).
    """
    if not geo:
        return ""

    cd_geol  = geo.get("CD_GEOL", "—")
    ambiente = str(geo.get("AMBIENTE", "—")).lower()
    roca1    = str(geo.get("ROCA1", "—"))
    edad_max = str(geo.get("EDAD_MAX", "—"))
    edad_min = str(geo.get("EDAD_MIN", "—"))

    # Determinar tipo de sistema mineral
    if "pluton" in ambiente or "intrusiv" in ambiente:
        tipo_sistema = "intrusivo cuarzomonzonítico/diorítico"
        tipo_oro     = "oro fino diseminado, asociado a microfracturas y veinlets de cuarzo"
        recomend_met = "molienda fina y cianuración o concentración gravimétrica"
        control      = "Alteración propilítica y argílica con disseminación fina de sulfuros (pirita, calcopirita, arsenopirita)"
    elif "volcan" in ambiente:
        tipo_sistema = "volcánico andesítico/brecha"
        tipo_oro     = "oro libre y oro grueso, alojado en brechas hidrotermales y vetas de cuarzo de mayor apertura"
        recomend_met = "gravimetría de alta eficiencia y concentración de oro libre"
        control      = "Fracturamiento intenso con circulación de fluidos hidrotermales tardíos (pulsos mesotermales)"
    elif "sedimentari" in ambiente:
        tipo_sistema = "sedimentario continental"
        tipo_oro     = "oro aluvial o detrítico, asociado a paleo-canales y quebradas"
        recomend_met = "jigs gravitacionales y canaletas"
        control      = "Control estratigráfico con concentración en zonas de baja energía hidráulica"
    else:
        tipo_sistema = f"unidad {cd_geol}"
        tipo_oro     = "mineralización polimetálica"
        recomend_met = "ensayos metalúrgicos específicos"
        control      = "Control estructural y litológico a definir"

    # Enriquecer con datos de laboratorio si existen
    parrafo_lab = ""
    if lab and lab.get("resultados") is not None:
        df = lab["resultados"]
        # Buscar columna Au
        cols_au = [c for c in df.columns if "au" in str(c).lower() and "fino" not in str(c).lower() and "grue" not in str(c).lower()]
        if cols_au:
            try:
                valores = df[cols_au[0]].astype(str).str.replace(",", ".").apply(
                    lambda x: float(x) if x.replace(".", "").isdigit() else None
                ).dropna()
                if len(valores) > 0:
                    max_au = valores.max()
                    min_au = valores.min()
                    parrafo_lab = (
                        f" Las leyes obtenidas oscilan entre {min_au:.2f} y {max_au:.2f} g/t Au, "
                        f"{'indicando alto potencial' if max_au > 5 else 'confirmando mineralización moderada'}. "
                    )
            except Exception:
                pass

    texto = f"""La zona de estudio se emplaza en una unidad geológica correspondiente a rocas de ambiente {ambiente} ({cd_geol}), de edad {edad_max} a {edad_min}. La litología principal corresponde a {roca1}, representativa de un sistema {tipo_sistema}.

El área se caracteriza por la presencia de {tipo_oro}.{parrafo_lab}{control}.

Desde el punto de vista metalogénico, el ambiente es favorable para sistemas hidrotermales de tipo mesotermal, con potencial para mineralización en vetas, stockworks y brechas estructuralmente controladas.

Conclusiones y Recomendaciones:
• El sector presenta potencial {'alto' if 'volcan' in ambiente else 'moderado'} para mineralización aurífera.
• Se recomienda {recomend_met} como método de procesamiento prioritario.
• Se sugiere levantamiento estructural detallado para identificar zonas de intersección y clavos mineralizados.
• Aumentar la densidad de muestreo en las zonas de mayor ley para definir continuidad espacial."""

    return texto


def render_interpretacion(geo: dict | None, lab: dict | None) -> str | None:
    """Widget Streamlit para revisión y edición de la interpretación."""
    st.subheader("🤖 Interpretación Geológica")

    if not geo:
        st.info("La interpretación se generará automáticamente una vez tengas los datos geológicos.")
        return None

    if "interpretacion_texto" not in st.session_state:
        st.session_state["interpretacion_texto"] = generar_interpretacion(geo, lab)

    col_auto, col_reset = st.columns([3, 1])
    with col_auto:
        st.markdown("*El texto fue generado automáticamente. Puedes editarlo directamente:*")
    with col_reset:
        if st.button("🔄 Regenerar"):
            st.session_state["interpretacion_texto"] = generar_interpretacion(geo, lab)

    texto_final = st.text_area(
        "Interpretación y Recomendaciones",
        value=st.session_state["interpretacion_texto"],
        height=350,
        key="text_interpretacion",
    )
    st.session_state["interpretacion_texto"] = texto_final
    return texto_final
