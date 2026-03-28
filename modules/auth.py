import streamlit as st
from config import USUARIOS

def check_login():
    """Valida si hay un usuario logueado en la sesión"""
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

def render_login():
    """Muestra el formulario de inicio de sesión"""
    st.markdown("## 🔒 Inicio de Sesión")
    st.markdown("Introduce tus credenciales para acceder a LOROS.")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        # Ojo: width="stretch" en lugar del obsoleto use_container_width=True
        submit = st.form_submit_button("Ingresar", use_container_width=True)

        if submit:
            if username in USUARIOS and USUARIOS[username] == password:
                st.session_state["usuario"] = username
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas. Verifica tu usuario y contraseña.")

def logout():
    """Cierra la sesión actual"""
    st.session_state["usuario"] = None
    st.rerun()
