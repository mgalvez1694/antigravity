import pandas as pd
import streamlit as st

def render_laboratorio() -> dict | None:
    """UI para ingresar resultados de laboratorio Au (g/t)"""
    st.subheader("🧪 Resultados de Laboratorio (Oro)")
    st.markdown("Ingresa las leyes de oro (Au g/t) reportadas para las distintas muestras.")

    datos_por_defecto = {
        "Muestra": ["P1", "P2", "P3"],
        "Ley Au (g/t)": [0.0, 0.0, 0.0],
    }
    
    df_lab = pd.DataFrame(datos_por_defecto)
    
    # st.data_editor con width="stretch" (use_container_width=True deprecado)
    df_editado = st.data_editor(df_lab, use_container_width=True, num_rows="dynamic", key="lab_oro")
    
    st.markdown("**Retallas / Grava aurífera (Opcional)**")
    retalla_val = st.number_input("Oro libre / Retalla (g/t)", value=0.0, format="%.2f")

    if st.button("💾 Guardar Datos de Laboratorio", use_container_width=True):
        st.session_state["laboratorio"] = {
            "muestras": df_editado.to_dict("records"),
            "retalla": retalla_val
        }
        st.success("Resultados de laboratorio guardados correctamente.")
        
    return st.session_state.get("laboratorio")
