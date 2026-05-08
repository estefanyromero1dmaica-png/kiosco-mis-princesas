import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA Y HORA ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")

# Configuración precisa para Venezuela (Caracas)
zona_venezuela = pytz.timezone('America/Caracas')
hora_ahora = datetime.now(zona_venezuela)

# --- 2. ESTILO VISUAL PREMIUM (CSS CUSTOM) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Tarjetas de Métricas Dashboard */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e2130, #161925);
        padding: 25px !important;
        border-radius: 20px;
        border: 1px solid rgba(0, 255, 204, 0.2);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
    }

    /* Tarjeta de Usuario en Sidebar */
    .user-card {
        background: linear-gradient(135deg, #2e3141 0%, #1e2130 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #00ffcc;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }

    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN A DATOS ---
# 🚨 PEGA TU LINK DE GOOGLE SHEETS AQUÍ
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

@st.cache_data(ttl=60)
def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        return df.dropna(how="all").reset_index(drop=True)
    except Exception:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. CONTROL DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0.0
    st.session_state.entrada = None

# --- PANTALLA DE ACCESO (LOGIN) ---
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
                    st.session_state.ventas_acumuladas = 0.0
                    
                    try:
                        f_hoy = hora_ahora.strftime('%Y-%m-%d')
                        h_ent = hora_ahora.strftime('%H:%M:%S')
                        df_asist = cargar_datos("Asistencia")
                        nueva_asistencia = pd.DataFrame([{"Fecha": f_hoy, "Usuario": st.session_state.usuario, "Hora_Entrada": h_ent}])
                        df_total = pd.concat([df_asist, nueva_asistencia], ignore_index=True)
                        st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                    except: pass
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- INTERFAZ PRINCIPAL ---
else:
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc;'>Kiosco Mis Princesas</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(f"📅 **Hoy:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # BOTÓN DE CIERRE DIRECTO (SIN BLOQUEO)
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.session_state.entrada = None
            st.rerun()

    # NAVEGACIÓN
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    with t1:
        st.markdown("### Estado General")
        c1, c2, c3 = st.columns(3)
        stock_num = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0)
        c1.metric("Ventas Turno", f"$ {st.session_state.ventas_acumuladas:,.2f}")
        c2.metric("Stock Tienda", f"{int(stock_num.sum())} und")
        c3.metric("Alertas", len(df_inv[stock_num < 5]), delta_color="inverse")

    with t2:
        st.markdown("### 📦 Inventario")
        filtro = st.text_input("🔍 Buscar...")
        df_mostrar = df_inv[df_inv['Producto'].str.contains(filtro, case=False, na=False)] if filtro else df_inv
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        with st.expander("Añadir Producto"):
            with st.form("nuevo"):
                n = st.text_input("Nombre")
                p = st.number_input("Precio ($)", min_value=0.0)
                s = st.number_input("Stock", min_value=0)
                if st.form_submit_button("GUARDAR"):
                    if n:
                        nuevo = pd.DataFrame([{"Producto": n, "Precio": p, "Stock": s}])
                        df_f = pd.concat([df_inv, nuevo], ignore_index=True)
                        st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_f)
                        st.rerun()

    with t3:
        st.markdown("### 💰 Punto de Venta")
        if not df_inv.empty:
            sel = st.selectbox("Producto:", df_inv['Producto'].tolist())
            d = df_inv[df_inv['Producto'] == sel].iloc[0]
            st.info(f"Precio: ${d['Precio']} | Stock: {d['Stock']}")
            if st.button(f"🛒 VENDER {sel}", use_container_width=True, type="primary"):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                st.session_state.ventas_acumuladas += float(d['Precio'])
                df_inv.at[idx, 'Stock'] = int(pd.to_numeric(d['Stock'])) - 1
                st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                st.toast("Venta registrada")
                st.rerun()

    with t4:
        st.markdown("### 📅 Historial")
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            evs = [{"title": f"{r['Usuario']}", "start": str(r['Fecha']), "color": "#00ffcc"} for i, r in df_as.iterrows()]
            calendar(events=evs, options={"initialView": "dayGridMonth", "locale": "es"})
