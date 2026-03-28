import streamlit as st

def render_interpretacion() -> dict | None:
    """Widget de texto estructurado para conclusiones y recomendaciones geológicas"""
    st.subheader("📝 Interpretación y Conclusiones")
    
    st.markdown("Escribe un detalle técnico de la faena y su potencial mineral.")
    
    text_input = st.text_area(
        "Conclusiones Geológico-Mineras",
        height=200,
        placeholder="Ej: La veta principal presenta mineralización de sulfuros primarios de Cu-Au asociadas a rocas intrusivas graníticas..."
    )
    
    if st.button("💾 Guardar Interpretación", use_container_width=True):
        if len(text_input) < 10:
            st.warning("Escribe al menos una conclusión sustancial.")
        else:
            st.session_state["interpretacion"] = text_input
            st.success("Interpretación guardada correctamente.")
            
    return st.session_state.get("interpretacion")
