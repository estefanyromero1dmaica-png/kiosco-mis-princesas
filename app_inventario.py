 import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA Y HORA ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")

zona_venezuela = pytz.timezone('America/Caracas')
hora_ahora = datetime.now(zona_venezuela)

# --- 2. ESTILO VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e2130, #161925);
        padding: 25px !important;
        border-radius: 20px;
        border: 1px solid rgba(0, 255, 204, 0.2);
    }
    .user-card {
        background: linear-gradient(135deg, #2e3141 0%, #1e2130 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN A DATOS ---
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

@st.cache_data(ttl=60)
def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        # Convertimos a entero para eliminar el .00 en la visualización
        if 'Precio' in df.columns:
            df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce').fillna(0).astype(int)
        if 'Stock' in df.columns:
            df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. CONTROL DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0
    st.session_state.entrada = None

# --- PANTALLA DE ACCESO ---
if st.session_state.usuario is None:
    col_login, _ = st.columns([1, 1]) 
    with col_login:
        st.title("🔐 Acceso al Sistema")
        with st.form("login_form"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN:", type="password")
            if st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    st.session_state.ventas_acumuladas = 0
                    
                    try:
                        df_asist = cargar_datos("Asistencia")
                        nueva_fila = pd.DataFrame([{
                            "Fecha": st.session_state.entrada.strftime('%Y-%m-%d'), 
                            "Usuario": st.session_state.usuario, 
                            "Hora_Entrada": st.session_state.entrada.strftime('%H:%M:%S')
                        }])
                        df_total = pd.concat([df_asist, nueva_fila], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                    except: pass
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

else:
    with st.sidebar:
        st.markdown(f'<div class="user-card"><h2>👤 {st.session_state.usuario}</h2></div>', unsafe_allow_html=True)
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        st.divider()
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.rerun()

    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Turno", f"$ {int(st.session_state.ventas_acumuladas)}")
        c2.metric("Stock Tienda", f"{int(df_inv['Stock'].sum())} und")
        c3.metric("Alertas", len(df_inv[df_inv['Stock'] < 5]))

    with t2:
        st.markdown("### 📦 Inventario")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        
        with st.expander("Añadir Nuevo Producto"):
            with st.form("nuevo"):
                n = st.text_input("Nombre")
                p = st.number_input("Precio ($)", min_value=0, step=1) # Step=1 para evitar decimales
                s = st.number_input("Stock", min_value=0, step=1)
                if st.form_submit_button("GUARDAR"):
                    if n:
                        # Aseguramos que los datos nuevos sean enteros antes de enviar
                        nuevo = pd.DataFrame([{"Producto": n, "Precio": int(p), "Stock": int(s)}])
                        df_f = pd.concat([df_inv, nuevo], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_f)
                        st.cache_data.clear() # Limpiar cache para ver el cambio
                        st.rerun()

    with t3:
        st.markdown("### 💰 Punto de Venta")
        if not df_inv.empty:
            sel = st.selectbox("Producto:", df_inv['Producto'].tolist())
            d = df_inv[df_inv['Producto'] == sel].iloc[0]
            st.info(f"Precio: ${int(d['Precio'])} | Stock: {int(d['Stock'])}")
            if st.button(f"🛒 VENDER {sel}", use_container_width=True):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                if d['Stock'] > 0:
                    st.session_state.ventas_acumuladas += int(d['Precio'])
                    df_inv.at[idx, 'Stock'] = int(d['Stock']) - 1
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.cache_data.clear()
                    st.rerun()

    with t4:
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            st.dataframe(df_as, use_container_width=True)
