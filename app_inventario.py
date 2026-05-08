import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA Y HORA ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")

# Configuración de zona horaria para Venezuela
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
    }
    
    /* Evitar que los números se corten */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }

    /* Botones Pro */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN A DATOS (GOOGLE SHEETS) ---
# 🚨 PEGA TU LINK DE GOOGLE SHEETS AQUÍ ABAJO
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        
        # ELIMINAR DECIMALES (.00): Convertimos a entero para vista limpia
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

# --- PANTALLA DE ACCESO (LOGIN) ---
if st.session_state.usuario is None:
    col_login, _ = st.columns([1, 1]) 
    with col_login:
        st.title("🔐 Acceso al Sistema")
        st.markdown("---")
        with st.form("login_form"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN de Seguridad:", type="password")
            
            if st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    st.session_state.ventas_acumuladas = 0
                    
                    try:
                        df_asist = cargar_datos("Asistencia")
                        nueva_asist = pd.DataFrame([{
                            "Fecha": st.session_state.entrada.strftime('%Y-%m-%d'),
                            "Usuario": st.session_state.usuario,
                            "Hora_Entrada": st.session_state.entrada.strftime('%H:%M:%S')
                        }])
                        df_total = pd.concat([df_asist, nueva_asist], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                    except:
                        pass
                    st.rerun()
                else:
                    st.error("🚫 Credenciales incorrectas")

# --- INTERFAZ PRINCIPAL (APP ACTIVA) ---
else:
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc;'>Kiosco Activo</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(f"📅 **Hoy:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.session_state.entrada = None
            st.rerun()

    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    # TAB 1: DASHBOARD
    with t1:
        st.markdown("### Resumen Operativo")
        c1, c2, c3 = st.columns(3)
        
        stk_val = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0)
        total_und = int(stk_val.sum())
        bajos = len(df_inv[stk_val < 5])
        
        c1.metric("Ventas Turno", f"$ {int(st.session_state.ventas_acumuladas)}")
        c2.metric("Stock en Tienda", f"{total_und} und")
        c3.metric("Stock Crítico", bajos, delta_color="inverse")

    # TAB 2: INVENTARIO
    with t2:
        st.markdown("### 📦 Control de Mercancía")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        
        with st.expander("✨ Registrar Nuevo Producto"):
            with st.form("form_nuevo"):
                n_prod = st.text_input("Nombre del Producto")
                p_prod = st.number_input("Precio ($)", min_value=0, step=1)
                s_prod = st.number_input("Stock Inicial", min_value=0, step=1)
                
                if st.form_submit_button("📥 GUARDAR PRODUCTO"):
                    if n_prod:
                        nuevo_df = pd.DataFrame([{"Producto": n_prod, "Precio": int(p_prod), "Stock": int(s_prod)}])
                        df_act = pd.concat([df_inv, nuevo_df], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_act)
                        st.cache_data.clear() 
                        st.rerun()

    # TAB 3: PUNTO DE VENTA
    with t3:
        st.markdown("### 💰 Registro de Venta")
        if not df_inv.empty:
            sel_p = st.selectbox("Producto:", df_inv['Producto'].tolist())
            datos_v = df_inv[df_inv['Producto'] == sel_p].iloc[0]
            
            p_v = int(datos_v['Precio'])
            s_v = int(datos_v['Stock'])
            
            st.info(f"💵 Precio: ${p_v} | 📦 Disponibles: {s_v}")
            
            if st.button(f"🛒 VENDER {sel_p}", use_container_width=True, type="primary"):
                if s_v > 0:
                    idx_v = df_inv[df_inv['Producto'] == sel_p].index[0]
                    st.session_state.ventas_acumuladas += p_v
                    df_inv.at[idx_v, 'Stock'] = s_v - 1
                    
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Producto agotado.")

    # TAB 4: HISTORIAL DE ASISTENCIA
    with t4:
        st.markdown("### 📅 Registro de Entradas")
        df_asis = cargar_datos("Asistencia")
        if not df_asis.empty:
            st.dataframe(df_asis.sort_values(by="Hora_Entrada", ascending=False), use_container_width=True, hide_index=True)
            evs = [{"title": f"{r['Usuario']} - {r['Hora_Entrada']}", "start": str(r['Fecha']), "color": "#00ffcc"} for i, r in df_asis.iterrows()]
            calendar(events=evs, options={"initialView": "dayGridMonth", "locale": "es"})
