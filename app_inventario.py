import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")
zona_venezuela = pytz.timezone('America/Caracas')

# --- 2. ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetric"] {
        background: #1e2130;
        padding: 20px !important;
        border-radius: 15px;
        border: 1px solid #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN (IMPORTANTE: REEMPLAZA TU LINK) ---
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        # Limpieza de decimales .00
        for col in ['Precio', 'Stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0
    st.session_state.entrada = None

# --- 5. LOGIN ---
if st.session_state.usuario is None:
    col_l, _ = st.columns([1, 1])
    with col_l:
        st.title("🔐 Acceso")
        with st.form("login"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN:", type="password")
            if st.form_submit_button("INICIAR"):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    st.rerun()
                else:
                    st.error("PIN incorrecto")

# --- 6. APP PRINCIPAL ---
else:
    with st.sidebar:
        st.header(f"👤 {st.session_state.usuario}")
        st.write(f"⏰ Entrada: {st.session_state.entrada.strftime('%H:%M')}")
        if st.button("🔴 CERRAR TURNO"):
            st.session_state.usuario = None
            st.rerun()

    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Turno", f"$ {int(st.session_state.ventas_acumuladas)}")
        c2.metric("Stock Total", f"{int(df_inv['Stock'].sum())}")
        c3.metric("Stock Crítico", len(df_inv[df_inv['Stock'] < 5]))

    with t2:
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        with st.expander("➕ Añadir Producto"):
            with st.form("nuevo"):
                n = st.text_input("Nombre")
                p = st.number_input("Precio", step=1)
                s = st.number_input("Stock", step=1)
                if st.form_submit_button("GUARDAR"):
                    nuevo = pd.DataFrame([{"Producto": n, "Precio": int(p), "Stock": int(s)}])
                    df_f = pd.concat([df_inv, nuevo], ignore_index=True)
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_f)
                    st.cache_data.clear()
                    st.rerun()

    with t3:
        if not df_inv.empty:
            sel = st.selectbox("Producto:", df_inv['Producto'].tolist())
            if st.button(f"🛒 VENDER {sel}", use_container_width=True):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                if df_inv.at[idx, 'Stock'] > 0:
                    st.session_state.ventas_acumuladas += df_inv.at[idx, 'Precio']
                    df_inv.at[idx, 'Stock'] -= 1
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.cache_data.clear()
                    st.rerun()

    with t4:
        st.markdown("### Historial")
        st.table(cargar_datos("Asistencia"))
