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
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }

    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
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
                    # Definimos datos de la sesión actual
                    nombre_usuario = u.capitalize()
                    hora_entrada_exacta = datetime.now(zona_venezuela)
                    
                    st.session_state.usuario = nombre_usuario
                    st.session_state.entrada = hora_entrada_exacta
                    st.session_state.ventas_acumuladas = 0.0
                    
                    # REGISTRO DE ASISTENCIA EN LA NUBE
                    try:
                        f_hoy = hora_entrada_exacta.strftime('%Y-%m-%d')
                        h_exacta = hora_entrada_exacta.strftime('%H:%M:%S')
                        
                        df_asist = cargar_datos("Asistencia")
                        
                        # Creamos la nueva fila con quién y a qué hora exacta entró
                        nueva_fila = pd.DataFrame([{
                            "Fecha": f_hoy, 
                            "Usuario": nombre_usuario, 
                            "Hora_Entrada": h_exacta
                        }])
                        
                        df_total = pd.concat([df_asist, nueva_fila], ignore_index=True)
                        
                        # Actualizamos la hoja de Google
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                        st.toast(f"✅ Entrada registrada: {nombre_usuario} a las {h_exacta}")
                    except Exception as e:
                        st.error(f"Error al registrar asistencia: {e}")
                    
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- INTERFAZ PRINCIPAL ---
else:
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc;'>Sesión iniciada</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Información visible de la entrada actual
        st.write(f"📅 **Día:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Hora de Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.session_state.entrada = None
            st.rerun()

    # NAVEGACIÓN
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    with t1:
        st.markdown("### Resumen del Turno")
        c1, c2, c3 = st.columns(3)
        stock_num = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0)
        c1.metric("Ventas Acumuladas", f"$ {st.session_state.ventas_acumuladas:,.2f}")
        c2.metric("Productos en Stock", f"{int(stock_num.sum())} und")
        c3.metric("Alertas de Stock", len(df_inv[stock_num < 5]), delta_color="inverse")

    with t2:
        st.markdown("### 📦 Control de Inventario")
        filtro = st.text_input("🔍 Buscar producto...")
        df_mostrar = df_inv[df_inv['Producto'].str.contains(filtro, case=False, na=False)] if filtro else df_inv
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        with st.expander("Añadir Nuevo Producto"):
            with st.form("nuevo"):
                n = st.text_input("Nombre del Producto")
                p = st.number_input("Precio Unitario ($)", min_value=0.0)
                s = st.number_input("Cantidad inicial", min_value=0)
                if st.form_submit_button("GUARDAR PRODUCTO"):
                    if n:
                        nuevo = pd.DataFrame([{"Producto": n, "Precio": p, "Stock": s}])
                        df_f = pd.concat([df_inv, nuevo], ignore_index=True)
                        st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_f)
                        st.success("Guardado exitosamente")
                        st.rerun()

    with t3:
        st.markdown("### 💰 Punto de Venta")
        if not df_inv.empty:
            sel = st.selectbox("Producto a vender:", df_inv['Producto'].tolist())
            d = df_inv[df_inv['Producto'] == sel].iloc[0]
            st.info(f"💰 Precio: ${d['Precio']} | 📦 Disponibles: {d['Stock']}")
            
            if st.button(f"🛒 REGISTRAR VENTA DE {sel}", use_container_width=True, type="primary"):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                if int(d['Stock']) > 0:
                    st.session_state.ventas_acumuladas += float(d['Precio'])
                    df_inv.at[idx, 'Stock'] = int(d['Stock']) - 1
                    st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.toast(f"Venta de {sel} realizada")
                    st.rerun()
                else:
                    st.error("No hay stock suficiente")

    with t4:
        st.markdown("### 📅 Registro Histórico de Entradas")
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            # Mostramos una tabla con el historial de quién entró y a qué hora
            st.dataframe(df_as.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
            
            # Calendario visual
            evs = [{"title": f"{r['Usuario']} ({r['Hora_Entrada']})", "start": str(r['Fecha']), "color": "#00ffcc"} for i, r in df_as.iterrows()]
            calendar(events=evs, options={"initialView": "dayGridMonth", "locale": "es"})
