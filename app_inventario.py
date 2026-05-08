import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE ALTO NIVEL ---
st.set_page_config(
    page_title="Kiosco Inteligente PRO",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado (CORREGIDO: unsafe_allow_html)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN Y CARGA DE DATOS ---
# 🚨 PEGA TU LINK AQUÍ:
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

def conectar_nube():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def cargar_datos(sheet_name):
    conn = conectar_nube()
    if conn:
        try:
            data = conn.read(spreadsheet=URL_HOJA, worksheet=sheet_name)
            return data.dropna(how="all")
        except:
            if sheet_name == "Asistencia":
                return pd.DataFrame(columns=["Fecha"])
            return pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    return pd.DataFrame()

# --- 3. GESTIÓN DE SESIÓN Y SEGURIDAD ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.entrada = None
    st.session_state.ventas_acumuladas = 0.0

if st.session_state.usuario is None:
    st.title("🔐 Acceso de Seguridad - Kiosco")
    col_login, _ = st.columns([1, 2])
    with col_login:
        with st.form("login_form"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN (4 dígitos):", type="password")
            if st.form_submit_button("INGRESAR"):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now()
                    
                    # Registro de asistencia
                    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
                    df_asistencia = cargar_datos("Asistencia")
                    if df_asistencia.empty or fecha_hoy not in df_asistencia["Fecha"].values:
                        nueva_fecha = pd.DataFrame([[fecha_hoy]], columns=["Fecha"])
                        df_final_asist = pd.concat([df_asistencia, nueva_fecha], ignore_index=True)
                        con = conectar_nube()
                        con.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_final_asist)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
else:
    # --- 4. INTERFAZ PRINCIPAL ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.usuario}")
        st.write(f"⏰ Entrada: {st.session_state.entrada.strftime('%H:%M')}")
        if st.button("🔴 CERRAR TURNO"):
            st.session_state.usuario = None
            st.rerun()

    df_inv = cargar_datos("Hoja1") # Asegúrate que tu pestaña se llame Hoja1
    conn_global = conectar_nube()

    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 CALENDARIO"])

    with t1:
        st.title("Panel de Control")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Turno", f"$ {st.session_state.ventas_acumuladas}")
        total = df_inv['Stock'].astype(int).sum() if not df_inv.empty else 0
        c2.metric("Stock Total", total)
        bajos = df_inv[df_inv['Stock'].astype(int) < 5] if not df_inv.empty else pd.DataFrame()
        c3.metric("Stock Crítico", len(bajos))
        if not bajos.empty:
            st.warning("⚠️ Reponer pronto:")
            st.table(bajos)

    with t2:
        st.subheader("Inventario Nube")
        query = st.text_input("🔍 Buscar producto...")
        df_f = df_inv[df_inv['Producto'].str.contains(query, case=False, na=False)] if query else df_inv
        
        with st.expander("➕ Añadir"):
            n = st.text_input("Nombre")
            pr = st.number_input("Precio", min_value=0.0)
            stk = st.number_input("Stock", min_value=0)
            if st.button("Guardar"):
                nuevo = pd.DataFrame([[n, pr, stk]], columns=["Producto", "Precio", "Stock"])
                df_f_inv = pd.concat([df_inv, nuevo], ignore_index=True)
                conn_global.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_f_inv)
                st.success("Guardado")
                st.rerun()
        st.dataframe(df_f, use_container_width=True)

    with t3:
        st.subheader("Vender")
        if not df_inv.empty:
            sel = st.selectbox("Producto:", df_inv['Producto'].tolist())
            if st.button("🛒 REGISTRAR"):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                if int(df_inv.at[idx, 'Stock']) > 0:
                    st.session_state.ventas_acumuladas += float(df_inv.at[idx, 'Precio'])
                    df_inv.at[idx, 'Stock'] = int(df_inv.at[idx, 'Stock']) - 1
                    conn_global.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_inv)
                    st.balloons()
                    st.rerun()

    with t4:
        st.header("Asistencia")
        df_asist = cargar_datos("Asistencia")
        eventos = [{"title": "TRABAJADO", "color": "#00FF00", "start": f, "end": f} for f in df_asist["Fecha"]] if not df_asist.empty else []
        calendar(events=eventos, options={"initialView": "dayGridMonth"})
