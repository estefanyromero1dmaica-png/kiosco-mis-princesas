import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE ESCENARIO ---
st.set_page_config(
    page_title="Kiosco Mis Princesas PRO v4.0", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración Horaria
zona_ve = pytz.timezone('America/Caracas')
ahora = datetime.now(zona_ve)

# --- 2. DISEÑO DE ALTO NIVEL (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    
    /* Tarjetas de Dashboard Estilo Cristal */
    div[data-testid="stMetric"] {
        background: rgba(30, 33, 48, 0.7);
        backdrop-filter: blur(10px);
        padding: 25px !important;
        border-radius: 20px;
        border: 1px solid rgba(0, 255, 204, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* Sidebar Personalizada */
    .sidebar .sidebar-content { background-image: linear-gradient(#1e2130, #0e1117); }
    
    .user-profile {
        padding: 20px;
        background: linear-gradient(135deg, #2e3141, #1e2130);
        border-radius: 15px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
    }

    /* Tabs y Botones */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e2130;
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 10px 25px;
    }
    .stButton>button {
        border-radius: 12px;
        font-weight: bold;
        transition: 0.3s;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MOTOR DE DATOS (NÚCLEO DEL SISTEMA) ---
# Enlace actualizado según tu petición
URL_SISTEMA = "https://docs.google.com/spreadsheets/d/1xNrFyCRFpU4LeBehOQwJQOS2pwEnNMVP35iUWrrjvwc/edit?pli=1#gid=0"

def obtener_conexion():
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_seguro(pestana):
    try:
        conn = obtener_conexion()
        df = conn.read(spreadsheet=URL_SISTEMA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        # Limpieza de tipos de datos para evitar errores de Google
        if 'Precio' in df.columns:
            df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce').fillna(0).astype(int)
        if 'Stock' in df.columns:
            df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

def guardar_cambios(pestana, df_actualizado):
    try:
        conn = obtener_conexion()
        conn.update(spreadsheet=URL_SISTEMA, worksheet=pestana, data=df_actualizado)
        st.cache_data.clear() # ELIMINA EL ERROR DE SINCRONIZACIÓN
        return True
    except Exception as e:
        st.error(f"Error Crítico de Sincronización: {e}")
        return False

# --- 4. LÓGICA DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.admin = ""
    st.session_state.ventas_sesion = 0

if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.title("🔐 Kiosco PRO")
        st.markdown("### Control de Acceso")
        with st.form("login"):
            u = st.text_input("Usuario:").strip().lower()
            p = st.text_input("PIN:", type="password")
            if st.form_submit_button("INGRESAR"):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    st.session_state.auth = True
                    st.session_state.admin = u.capitalize()
                    st.session_state.inicio = ahora
                    
                    # Registro de Entrada
                    df_as = cargar_datos_seguro("Asistencia")
                    nuevo_reg = pd.DataFrame([{
                        "Fecha": ahora.strftime('%Y-%m-%d'),
                        "Usuario": st.session_state.admin,
                        "Hora_Entrada": ahora.strftime('%H:%M:%S')
                    }])
                    guardar_cambios("Asistencia", pd.concat([df_as, nuevo_reg], ignore_index=True))
                    st.rerun()
                else:
                    st.error("Credenciales Inválidas")

# --- 5. CUERPO DE LA APLICACIÓN ---
else:
    # Sidebar Profesional
    with st.sidebar:
        st.markdown(f"""<div class="user-profile">
            <h2 style='margin:0;'>👤 {st.session_state.admin}</h2>
            <p style='margin:0; color:#00ffcc;'>Operador de Turno</p>
        </div>""", unsafe_allow_html=True)
        
        st.info(f"📅 {st.session_state.inicio.strftime('%d/%m/%Y')}\n\n⏰ Entrada: {st.session_state.inicio.strftime('%H:%M')}")
        
        st.divider()
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    # Carga Maestra de Datos
    df_inv = cargar_datos_seguro("Hoja 1")
    
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 PUNTO DE VENTA", "📅 REGISTROS"])

    # TAB 1: DASHBOARD
    with t1:
        st.subheader("Estado del Negocio")
        c1, c2, c3 = st.columns(3)
        
        stock_total = int(df_inv['Stock'].sum())
        criticos = df_inv[df_inv['Stock'] < 5]
        
        c1.metric("Ventas (Turno)", f"$ {int(st.session_state.ventas_sesion)}")
        c2.metric("Artículos en Stock", f"{stock_total} unidades")
        c3.metric("Stock Crítico", len(criticos), delta_color="inverse")
        
        if not criticos.empty:
            st.warning("⚠️ Los siguientes productos necesitan reposición urgente:")
            st.table(criticos[['Producto', 'Stock']])

    # TAB 2: GESTIÓN DE INVENTARIO
    with t2:
        st.markdown("### 🔍 Administración de Productos")
        
        col_filtro, col_accion = st.columns([3, 1])
        busqueda = col_filtro.text_input("Filtrar inventario...")
        
        df_filtrado = df_inv[df_inv['Producto'].str.contains(busqueda, case=False, na=False)] if busqueda else df_inv
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        st.divider()
        with st.expander("✨ Registrar Nuevo Artículo"):
            with st.form("nuevo_item"):
                c_n, c_p, c_s = st.columns([2, 1, 1])
                nom = c_n.text_input("Nombre:")
                pre = c_p.number_input("Precio ($):", step=1)
                stk = c_s.number_input("Stock Inicial:", step=1)
                if st.form_submit_button("GUARDAR EN NUBE"):
                    if nom:
                        nuevo_df = pd.concat([df_inv, pd.DataFrame([{"Producto": nom, "Precio": int(pre), "Stock": int(stk)}])], ignore_index=True)
                        if guardar_cambios("Hoja 1", nuevo_df):
                            st.success("¡Producto añadido con éxito!")
                            st.rerun()

    # TAB 3: VENTAS (POS)
    with t3:
        st.markdown("### 💰 Registro de Ventas Rápidas")
        if not df_inv.empty:
            col_sel, col_info = st.columns([2, 1])
            
            with col_sel:
                producto_sel = st.selectbox("Seleccione producto:", df_inv['Producto'].tolist())
                datos_item = df_inv[df_inv['Producto'] == producto_sel].iloc[0]
            
            with col_info:
                st.markdown(f"**Precio:** ${int(datos_item['Precio'])}")
                st.markdown(f"**Stock:** {int(datos_item['Stock'])} und")

            if st.button(f"🛒 COMPLETAR VENTA (${int(datos_item['Precio'])})", use_container_width=True, type="primary"):
                if datos_item['Stock'] > 0:
                    idx = df_inv[df_inv['Producto'] == producto_sel].index[0]
                    st.session_state.ventas_sesion += int(datos_item['Precio'])
                    df_inv.at[idx, 'Stock'] -= 1
                    
                    if guardar_cambios("Hoja 1", df_inv):
                        st.balloons()
                        st.rerun()
                else:
                    st.error("Producto agotado en inventario.")

    # TAB 4: HISTORIAL
    with t4:
        st.markdown("### 📅 Registros de Sistema")
        df_log = cargar_datos_seguro("Asistencia")
        st.dataframe(df_log.sort_values(by="Hora_Entrada", ascending=False), use_container_width=True)
        
        # Calendario de Actividad
        eventos = [{"title": f"Turno: {r['Usuario']}", "start": str(r['Fecha']), "color": "#00ffcc"} for i, r in df_log.iterrows()]
        calendar(events=eventos, options={"initialView": "dayGridMonth"})
