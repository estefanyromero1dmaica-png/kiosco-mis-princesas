import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Kiosco Pro - Nube", layout="wide")

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
# 🚨 PEGA AQUÍ EL LINK DE TU HOJA DE GOOGLE (Asegúrate de que sea "Editor")
URL_HOJA = "https://docs.google.com/spreadsheets/d/108HEgQ1pkzxjxwYEU2YqhvkWGdkar7rvEPTVyI2CUAE/edit?gid=0#gid=0"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=URL_HOJA)
    # Limpiar datos nulos
    df = df.dropna(how="all")
except:
    st.error("Error de conexión. Revisa que el link de Google Sheets sea correcto y esté en modo 'Editor'.")
    df = pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 3. ESTADO DE LA SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.hora_entrada = None
    st.session_state.ventas_acumuladas = 0.0

# --- 4. ACCESO CON PIN ---
if st.session_state.usuario is None:
    st.title("🔐 Acceso al Kiosco")
    autorizados = ["estefany", "milagros", "milagro", "gabriela", "mario"]
    
    with st.form("login"):
        u = st.text_input("Nombre:")
        p = st.text_input("PIN:", type="password")
        if st.form_submit_button("ENTRAR"):
            if u.lower() in autorizados and p == "2984":
                st.session_state.usuario = u.capitalize()
                st.session_state.hora_entrada = datetime.now()
                st.rerun()
            else:
                st.error("PIN o Usuario incorrecto")
else:
    # --- 5. INTERFAZ ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.usuario}")
        if st.button("CERRAR TURNO"):
            st.session_state.usuario = None
            st.rerun()

    t1, t2, t3 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS"])

    with t1:
        st.metric("Ventas Totales", f"$ {st.session_state.ventas_acumuladas}")
        st.write(f"Turno iniciado: {st.session_state.hora_entrada.strftime('%H:%M')}")

    with t2:
        st.subheader("Productos en la Nube")
        with st.expander("➕ Añadir Producto"):
            n = st.text_input("Nombre")
            p = st.number_input("Precio", min_value=0.0)
            s = st.number_input("Stock", min_value=0)
            if st.button("Guardar en Google Sheets"):
                nuevo = pd.DataFrame([[n, p, s]], columns=["Producto", "Precio", "Stock"])
                df_final = pd.concat([df, nuevo], ignore_index=True)
                # GUARDAR EN LA NUBE
                conn.update(spreadsheet=URL_HOJA, data=df_final)
                st.success("¡Datos guardados permanentemente!")
                st.rerun()
        
        st.dataframe(df, use_container_width=True)

    with t3:
        st.subheader("Registrar Venta")
        if not df.empty:
            prod = st.selectbox("Selecciona:", df['Producto'].tolist())
            if st.button("VENDER"):
                idx = df[df['Producto'] == prod].index[0]
                if df.at[idx, 'Stock'] > 0:
                    st.session_state.ventas_acumuladas += df.at[idx, 'Precio']
                    df.at[idx, 'Stock'] -= 1
                    # ACTUALIZAR EN LA NUBE
                    conn.update(spreadsheet=URL_HOJA, data=df)
                    st.balloons()
                    st.rerun()
