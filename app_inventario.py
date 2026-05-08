import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Kiosco Mis Princesas PRO v2.0", 
    page_icon="🏪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de zona horaria precisa para Venezuela
zona_venezuela = pytz.timezone('America/Caracas')
hora_actual = datetime.now(zona_venezuela)

# --- 2. DISEÑO ESTÉTICO PERSONALIZADO (CSS) ---
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Estilo de las métricas (Dashboard) */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e2130, #161925);
        padding: 25px !important;
        border-radius: 20px;
        border: 1px solid rgba(0, 255, 204, 0.3);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #00ffcc;
    }

    /* Tarjeta de Usuario en Sidebar */
    .user-card {
        background: linear-gradient(135deg, #2e3141 0%, #1e2130 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #00ffcc;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #1e2130;
        border-radius: 10px 10px 0px 0px;
        color: #ffffff;
        font-weight: bold;
        border: none;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ffcc !important;
        color: #0e1117 !important;
    }

    /* Botones Pro */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN Y CARGA DE DATOS ---
# 🚨 REEMPLAZA ESTO CON TU LINK REAL
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xNrFyCRFpU4LeBehOQwJQOS2pwEnNMVP35iUWrrjvwc/edit?pli=1&gid=549178331#gid=549178331"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        
        # ELIMINAR DECIMALES .00 DE RAÍZ
        for col in ['Precio', 'Stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        # Estructura por defecto si falla la carga
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. GESTIÓN DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0
    st.session_state.entrada = None

# --- 5. PANTALLA DE ACCESO (LOGIN) ---
if st.session_state.usuario is None:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.title("🏪 Sistema Mis Princesas")
        st.markdown("### Control de Acceso")
        with st.form("login_form"):
            u = st.text_input("👤 Nombre de Usuario:").strip().lower()
            p = st.text_input("🔑 PIN de Seguridad:", type="password")
            
            if st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True):
                usuarios_validos = ["estefany", "milagros", "gabriela", "mario"]
                if u in usuarios_validos and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    st.session_state.ventas_acumuladas = 0
                    
                    # Registro Automático en la Hoja de Asistencia
                    try:
                        df_asis = cargar_datos("Asistencia")
                        registro = pd.DataFrame([{
                            "Fecha": st.session_state.entrada.strftime('%Y-%m-%d'),
                            "Usuario": st.session_state.usuario,
                            "Hora_Entrada": st.session_state.entrada.strftime('%H:%M:%S')
                        }])
                        df_final_asis = pd.concat([df_asis, registro], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_final_asis)
                    except:
                        pass
                    
                    st.success(f"Bienvenida, {st.session_state.usuario}")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Verifique e intente de nuevo.")

# --- 6. INTERFAZ OPERATIVA ---
else:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc;'>Panel de Control</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(f"📅 **Hoy:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        if st.button("🔴 CERRAR TURNO Y SALIR", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.rerun()

    # --- NAVEGACIÓN POR TABS ---
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 HISTORIAL"])

    # --- TAB 1: DASHBOARD ---
    with t1:
        st.markdown("### Resumen de Operaciones")
        c1, c2, c3 = st.columns(3)
        
        total_stock = int(df_inv['Stock'].sum())
        criticos = len(df_inv[df_inv['Stock'] < 5])
        
        c1.metric("Ventas del Turno", f"$ {int(st.session_state.ventas_acumuladas)}")
        c2.metric("Stock en Kiosco", f"{total_stock} und")
        c3.metric("Alertas de Stock", criticos, delta="- Reponer" if criticos > 0 else "OK")
        
        if criticos > 0:
            st.error(f"⚠️ ¡Atención! Hay {criticos} productos con stock muy bajo.")

    # --- TAB 2: INVENTARIO COMPLETO ---
    with t2:
        st.markdown("### 📦 Gestión de Mercancía")
        col_bus, col_refresh = st.columns([4, 1])
        busqueda = col_bus.text_input("🔍 Buscar por nombre...", placeholder="Escribe el nombre del producto...")
        
        df_ver = df_inv[df_inv['Producto'].str.contains(busqueda, case=False, na=False)] if busqueda else df_inv
        st.dataframe(df_ver, use_container_width=True, hide_index=True)
        
        with st.expander("✨ AÑADIR NUEVA MERCANCÍA"):
            with st.form("nuevo_producto_form"):
                cn, cp, cs = st.columns([2, 1, 1])
                nom = cn.text_input("Nombre del Producto:")
                pre = cp.number_input("Precio ($):", min_value=0, step=1)
                stk = cs.number_input("Stock Inicial:", min_value=0, step=1)
                
                if st.form_submit_button("💾 GUARDAR EN INVENTARIO", use_container_width=True):
                    if nom:
                        nuevo_item = pd.DataFrame([{"Producto": nom, "Precio": int(pre), "Stock": int(stk)}])
                        df_total_inv = pd.concat([df_inv, nuevo_item], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_total_inv)
                        st.cache_data.clear() # Limpia el cache para evitar el error UnsupportedOperation
                        st.success(f"✅ {nom} agregado exitosamente.")
                        st.rerun()

    # --- TAB 3: PUNTO DE VENTA (CAJA) ---
    with t3:
        st.markdown("### 💰 Registro de Ventas")
        if not df_inv.empty:
            col_sel, col_det = st.columns([2, 1])
            with col_sel:
                lista_prod = df_inv['Producto'].tolist()
                p_seleccionado = st.selectbox("Seleccione producto para la venta:", lista_prod)
                datos_p = df_inv[df_inv['Producto'] == p_seleccionado].iloc[0]
            
            with col_det:
                st.markdown(f"**Precio:** ${int(datos_p['Precio'])}")
                st.markdown(f"**Disponibles:** {int(datos_p['Stock'])}")

            if datos_p['Stock'] > 0:
                if st.button(f"🛒 COMPLETAR VENTA (${int(datos_p['Precio'])})", use_container_width=True, type="primary"):
                    idx = df_inv[df_inv['Producto'] == p_seleccionado].index[0]
                    st.session_state.ventas_acumuladas += int(datos_p['Precio'])
                    df_inv.at[idx, 'Stock'] = int(datos_p['Stock']) - 1
                    
                    # Actualizar Nube
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.cache_data.clear()
                    st.balloons()
                    st.rerun()
            else:
                st.error("❌ PRODUCTO AGOTADO. No se puede realizar la venta.")

    # --- TAB 4: HISTORIAL DE ASISTENCIA ---
    with t4:
        st.markdown("### 📅 Registro de Entradas y Turnos")
        df_asistencia = cargar_datos("Asistencia")
        if not df_asistencia.empty:
            st.dataframe(df_asistencia.sort_values(by="Hora_Entrada", ascending=False), use_container_width=True, hide_index=True)
            
            # Calendario Interactivo
            eventos_calendar = []
            for _, row in df_asistencia.iterrows():
                eventos_calendar.append({
                    "title": f"Turno: {row['Usuario']}",
                    "start": str(row['Fecha']),
                    "end": str(row['Fecha']),
                    "color": "#00ffcc",
                    "textColor": "#0e1117"
                })
            
            calendar(events=eventos_calendar, options={"initialView": "dayGridMonth", "locale": "es"})
