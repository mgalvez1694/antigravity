"""
Módulo 1: Autenticación y gestión de sesión
"""
import streamlit as st
from config import USUARIOS, LOGO_COLOR, COLOR_ACENTO


def check_login() -> bool:
    """Retorna True si el usuario está autenticado."""
    return st.session_state.get("autenticado", False)


def logout():
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.rerun()


def render_login():
    """Renderiza la pantalla de login."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image(LOGO_COLOR, width=280)
        except Exception:
            st.markdown("## 🦜 LOROS")

        st.markdown(
            f"""
            <div style='text-align:center; margin-bottom:2rem;'>
                <h2 style='color:{COLOR_ACENTO}; font-family:Inter,sans-serif;'>
                    Proyecto Prospección
                </h2>
                <p style='color:#aaa; font-size:0.9rem;'>Gálvez SpA — Sistema Interno</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            clave   = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submit  = st.form_submit_button("Ingresar", use_container_width=True)

        if submit:
            if usuario in USUARIOS and USUARIOS[usuario] == clave:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.success(f"Bienvenido, {usuario} ✔")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
