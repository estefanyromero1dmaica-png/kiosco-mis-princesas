import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")
zona_venezuela = pytz.timezone('America/Caracas')

# --- 2. ESTILO CSS (EL QUE TE GUSTA) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetric"] {
        background: #1e2130;
        padding: 20px !important;
        border-radius: 15px;
        border: 1px solid #00ffcc;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e2130;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: white;
    }
    .user-card {
        background: linear-gradient(135deg, #2e3141, #1e2130);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN (IMPORTANTE: Pon tu link aquí) ---
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        # Limpieza de decimales .00 para que se vea bonito
        for col in ['Precio', 'Stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. MANEJO DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0
    st.session_state.entrada = None

# --- 5. LOGIN ---
if st.session_state.usuario is None:
    col_l, _ = st.columns([1, 1])
    with col_l:
        st.title("🏪 Kiosco Mis Princesas")
        st.subheader("Acceso al Sistema")
        with st.form("login_form"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN:", type="password")
            if st.form_submit_button("🚀 ENTRAR"):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    # Registro silencioso de asistencia
                    try:
                        df_as = cargar_datos("Asistencia")
                        nueva = pd.DataFrame([{"Fecha": st.session_state.entrada.strftime('%Y-%m-%d'), 
                                               "Usuario": st.session_state.usuario, 
                                               "Hora_Entrada": st.session_state.entrada.strftime('%H:%M:%S')}])
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=pd.concat([df_as, nueva]))
                    except: pass
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    # SIDEBAR
    with st.sidebar:
        st.markdown(f"""<div class="user-card">
            <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
            <p style='margin:0; color:#00ffcc;'>Sesión en curso</p>
        </div>""", unsafe_allow_html=True)
        st.write(f"📅 **Fecha:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M')}")
        st.divider()
        if st.button("🔴 CERRAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.rerun()

    # CARGA DE DATOS
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    # TAB 1: DASHBOARD
    with t1:
        st.subheader("Resumen del Kiosco")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Hoy", f"$ {int(st.session_state.ventas_acumuladas)}")
        c2.metric("Stock Total", f"{int(df_inv['Stock'].sum())} und")
        c3.metric("Stock Crítico", len(df_inv[df_inv['Stock'] < 5]))

    # TAB 2: INVENTARIO
    with t2:
        st.markdown("### 📦 Control de Stock")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        with st.expander("✨ Registrar Nuevo Producto"):
            with st.form("nuevo_p"):
                n = st.text_input("Nombre del Producto")
                p = st.number_input("Precio ($)", step=1)
                s = st.number_input("Cantidad Inicial", step=1)
                if st.form_submit_button("💾 GUARDAR"):
                    if n:
                        nuevo = pd.DataFrame([{"Producto": n, "Precio": int(p), "Stock": int(s)}])
                        df_f = pd.concat([df_inv, nuevo], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_f)
                        st.cache_data.clear() # FIX PARA EL ERROR ROJO
                        st.success("¡Guardado!")
                        st.rerun()

    # TAB 3: VENTAS
    with t3:
        st.markdown("### 💰 Punto de Venta")
        if not df_inv.empty:
            sel = st.selectbox("Seleccione Producto:", df_inv['Producto'].tolist())
            datos = df_inv[df_inv['Producto'] == sel].iloc[0]
            st.info(f"Precio: ${int(datos['Precio'])} | Stock disponible: {int(datos['Stock'])}")
            if st.button(f"🛒 REGISTRAR VENTA DE {sel}", use_container_width=True, type="primary"):
                if datos['Stock'] > 0:
                    idx = df_inv[df_inv['Producto'] == sel].index[0]
                    st.session_state.ventas_acumuladas += int(datos['Precio'])
                    df_inv.at[idx, 'Stock'] -= 1
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.cache_data.clear() # FIX PARA EL ERROR ROJO
                    st.rerun()
                else:
                    st.error("¡Sin stock!")

    # TAB 4: HISTORIAL
    with t4:
        st.markdown("### 📅 Registro de Asistencia")
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            st.dataframe(df_as.sort_values(by="Hora_Entrada", ascending=False), use_container_width=True)
            eventos = [{"title": f"{r['Usuario']}", "start": str(r['Fecha']), "color": "#00ffcc"} for i, r in df_as.iterrows()]
            calendar(events=eventos, options={"initialView": "dayGridMonth"})
