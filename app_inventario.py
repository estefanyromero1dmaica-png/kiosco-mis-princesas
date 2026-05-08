import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Kiosco PRO", page_icon="🏪", layout="wide")

# Estilo corregido para que no de error
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN ---
# 🚨 PEGA AQUÍ TU LINK DE GOOGLE SHEETS
URL_HOJA = "https://docs.google.com/spreadsheets/d/108HEgQ1pkzxjxwYEU2YqhvkWGdkar7rvEPTVyI2CUAE/edit?gid=2121698156#gid=2121698156"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        data = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        return data.dropna(how="all")
    except Exception:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 3. SEGURIDAD ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0.0

if st.session_state.usuario is None:
    st.title(" Acceso al Sistema")
    with st.form("login"):
        u = st.text_input("Usuario:").strip().lower()
        p = st.text_input("PIN (4 dígitos):", type="password")
        if st.form_submit_button("INGRESAR"):
            # Acceso para estefany, milagros, gabriela o mario
            if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                st.session_state.usuario = u.capitalize()
                st.session_state.entrada = datetime.now()
                
                # REGISTRO AUTOMÁTICO DE ASISTENCIA
                try:
                    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
                    df_asist = cargar_datos("Asistencia")
                    if df_asist.empty or fecha_hoy not in df_asist["Fecha"].values:
                        nueva_f = pd.DataFrame([[fecha_hoy]], columns=["Fecha"])
                        df_total = pd.concat([df_asist, nueva_f], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                except Exception:
                    st.toast("⚠️ Nota: Asistencia guardada localmente por ahora.")
                
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
else:
    # --- 4. INTERFAZ ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.usuario}")
        st.write(f"⏰ Entrada: {st.session_state.entrada.strftime('%H:%M')}")
        if st.button(" CERRAR TURNO"):
            st.session_state.usuario = None
            st.rerun()

    df_inv = cargar_datos("Hoja 1")
    
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 CALENDARIO"])

    with t1:
        st.title("Panel Principal")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Turno", f"$ {st.session_state.ventas_acumuladas}")
        
        try:
            total_stk = pd.to_numeric(df_inv['Stock']).sum()
        except:
            total_stk = 0
        c2.metric("Stock Total", f"{total_stk} und")
        
        try:
            criticos = len(df_inv[pd.to_numeric(df_inv['Stock']) < 5])
        except:
            criticos = 0
        c3.metric("Stock Crítico", criticos)

    with t2:
        st.subheader("Inventario en Nube")
        busq = st.text_input("🔍 Buscar...")
        df_f = df_inv[df_inv['Producto'].str.contains(busq, case=False, na=False)] if busq else df_inv
        
        with st.expander("➕ Añadir Producto"):
            col1, col2, col3 = st.columns(3)
            n = col1.text_input("Nombre")
            pr = col2.number_input("Precio", min_value=0.0)
            stk = col3.number_input("Stock", min_value=0)
            if st.button("Guardar"):
                nuevo = pd.DataFrame([[n, pr, stk]], columns=["Producto", "Precio", "Stock"])
                df_final = pd.concat([df_inv, nuevo], ignore_index=True)
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_final)
                st.success("¡Guardado!")
                st.rerun()
        st.dataframe(df_f, use_container_width=True)

    with t3:
        st.subheader("Registrar Venta")
        if not df_inv.empty:
            sel = st.selectbox("Producto:", df_inv['Producto'].tolist())
            if st.button("🛒 REGISTRAR"):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                if int(df_inv.at[idx, 'Stock']) > 0:
                    st.session_state.ventas_acumuladas += float(df_inv.at[idx, 'Precio'])
                    df_inv.at[idx, 'Stock'] = int(df_inv.at[idx, 'Stock']) - 1
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.balloons()
                    st.rerun()

    with t4:
        st.header("Días Laborados")
        df_as = cargar_datos("Asistencia")
        eventos = [{"title": "TRABAJADO", "color": "#00FF00", "start": str(f), "end": str(f)} for f in df_as["Fecha"]] if not df_as.empty else []
        calendar(events=eventos, options={"initialView": "dayGridMonth"})
