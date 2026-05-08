import streamlit as st
import pandas as pd
from datetime import datetime
import pytz  # Librería para la hora exacta
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE HORA Y PÁGINA ---
st.set_page_config(page_title="Kiosco PRO", page_icon="🏪", layout="wide")
zona_venezuela = pytz.timezone('America/Caracas')
hora_actual = datetime.now(zona_venezuela)

# --- ESTILO VISUAL MEJORADO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Tarjetas de Métricas (Dashboard) */
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #3e4250;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Tarjeta de Usuario en Sidebar */
    .user-card {
        background: linear-gradient(135deg, #2e3141 0%, #1e2130 100%);
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
# --- 2. CONEXIÓN ESTRUCTURADA A GOOGLE SHEETS ---
# 🚨 Asegúrate de que el link termine en /edit?usp=sharing
URL_HOJA = "https://docs.google.com/spreadsheets/d/108HEgQ1pkzxjxwYEU2YqhvkWGdkar7rvEPTVyI2CUAE/edit?gid=2121698156#gid=2121698156"

@st.cache_data(ttl=60) # Optimiza la carga para que sea más rápida
def cargar_datos(pestana):
    try:
        # Establece conexión con el conector oficial de Streamlit
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Intenta leer la pestaña específica
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        
        # Limpieza profesional: quita filas vacías que ensucian el inventario
        return df.dropna(how="all").reset_index(drop=True)
        
    except Exception as e:
        # Log interno del error para que sepas qué falló sin romper la interfaz
        st.error(f"⚠️ Error al conectar con {pestana}. Revisa el enlace o permisos.")
        
        # Creación de DataFrame de respaldo para que la app siga funcionando
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Entrada", "Salida"])
        
        # Estructura base para el inventario
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])
# --- 3. SEGURIDAD Y ACCESO (INTERFAZ Y LÓGICA PRO) ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0.0

if st.session_state.usuario is None:
    # Contenedor centrado para el Login
    col_login, _ = st.columns([1, 1]) 
    with col_login:
        st.title("🔐 Acceso al Sistema")
        st.markdown("---")
        
        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Identificador de Usuario:").strip().lower()
            p = st.text_input("PIN de Seguridad:", type="password", help="Introduce tu código de 4 dígitos")
            
            submit = st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True)
            
            if submit:
                authorized_users = ["estefany", "milagros", "gabriela", "mario"]
                if u in authorized_users and p == "2984":
                    # Configuración de sesión
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = hora_actual 
                    
                    # --- REGISTRO DE ASISTENCIA INTELIGENTE ---
                    try:
                        fecha_hoy = hora_actual.strftime('%Y-%m-%d')
                        df_asist = cargar_datos("Asistencia")
                        
                        # Verificamos si la fecha ya existe para no duplicar filas innecesariamente
                        if df_asist.empty or fecha_hoy not in df_asist["Fecha"].astype(str).values:
                            nueva_fila = pd.DataFrame([{"Fecha": fecha_hoy}])
                            df_actualizado = pd.concat([df_asist, nueva_fila], ignore_index=True)
                            
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_actualizado)
                            st.toast(f"✅ Asistencia registrada: {fecha_hoy}")
                    except Exception as e:
                        st.toast("⚠️ Error de sincronización: El turno se guardó localmente.")
                    
                    st.success(f"¡Bienvenida de nuevo, {u.capitalize()}!")
                    st.rerun()
                else:
                    st.error("🚫 Acceso denegado. Verifica el usuario o el PIN.")
else:
  # --- 4. INTERFAZ PRINCIPAL (CENTRO DE CONTROL) ---
with st.sidebar:
    st.markdown(f"""
        <div class="user-card">
            <h2 style='margin:0; color:white;'>👤 {st.session_state.usuario}</h2>
            <p style='margin:0; color:#00ffcc; font-size: 0.9rem;'>Kiosco Mis Princesas</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_side1, col_side2 = st.columns(2)
    col_side1.metric("📅 Fecha", st.session_state.entrada.strftime('%d/%m'))
    col_side2.metric("⏰ Entrada", st.session_state.entrada.strftime('%H:%M'))
    
    st.divider()
    
    if st.button("🔴 CERRAR TURNO Y SALIR", use_container_width=True, type="primary"):
        st.session_state.usuario = None
        st.rerun()

# Carga de datos centralizada
df_inv = cargar_datos("Hoja 1")
t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 PUNTO DE VENTA", "📅 ASISTENCIA"])

with t1:
    st.markdown("### Resumen de Operaciones")
    c1, c2, c3 = st.columns(3)
    
    # Cálculos seguros con manejo de errores
    total_stk = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0).sum()
    alertas = len(df_inv[pd.to_numeric(df_inv['Stock'], errors='coerce') < 5])
    
    c1.metric("Ingresos del Turno", f"$ {st.session_state.ventas_acumuladas:,.2f}", delta="Ventas")
    c2.metric("Productos en Tienda", f"{int(total_stk)} und")
    c3.metric("Alertas de Reposición", alertas, delta="- Críticos", delta_color="inverse")
    
    if alertas > 0:
        st.warning(f"⚠️ Tienes {alertas} productos con stock bajo. Revisa la pestaña de Inventario.")

with t2:
    st.markdown("### 📦 Gestión de Mercancía")
    busq = st.text_input("🔍 Filtrar por nombre de producto...", placeholder="Ej: Harina, Refresco...")
    
    # Filtro avanzado
    df_f = df_inv[df_inv['Producto'].str.contains(busq, case=False, na=False)] if busq else df_inv
    
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    
    with st.expander("✨ Registrar Nuevo Producto"):
        with st.form("new_product"):
            c1, c2, c3 = st.columns([2, 1, 1])
            n = c1.text_input("Nombre del Artículo")
            pr = c2.number_input("Precio Venta ($)", min_value=0.0, step=0.1)
            stk = c3.number_input("Stock Inicial", min_value=0, step=1)
            
            if st.form_submit_button("📥 GUARDAR EN INVENTARIO"):
                if n:
                    nuevo = pd.DataFrame([{"Producto": n, "Precio": pr, "Stock": stk}])
                    df_final = pd.concat([df_inv, nuevo], ignore_index=True)
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_final)
                    st.success(f"✅ {n} añadido correctamente.")
                    st.rerun()

with t3:
    st.markdown("### 💰 Punto de Venta Rápido")
    if not df_inv.empty:
        col_v1, col_v2 = st.columns([2, 1])
        
        with col_v1:
            sel = st.selectbox("Seleccionar producto para vender:", df_inv['Producto'].tolist())
            datos_prod = df_inv[df_inv['Producto'] == sel].iloc[0]
            precio_und = float(datos_prod['Precio'])
            stock_disp = int(datos_prod['Stock'])
        
        with col_v2:
            st.markdown(f"**Precio:** ${precio_und:,.2f}")
            st.markdown(f"**Disponible:** {stock_disp} und")

        if stock_disp > 0:
            if st.button("🚀 CONFIRMAR VENTA Y DESCONTAR", use_container_width=True, type="primary"):
                idx = df_inv[df_inv['Producto'] == sel].index[0]
                st.session_state.ventas_acumuladas += precio_und
                df_inv.at[idx, 'Stock'] = stock_disp - 1
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                st.balloons()
                st.toast(f"¡Venta registrada! - ${precio_und}")
                st.rerun()
        else:
            st.error("❌ Producto agotado. No se puede realizar la venta.")

with t4:
    st.markdown("### 📅 Registro de Actividad")
    df_as = cargar_datos("Asistencia")
    
    # Formateo de eventos para el calendario
    eventos = []
    if not df_as.empty:
        for f in df_as["Fecha"]:
            eventos.append({
                "title": "TURNO CUMPLIDO",
                "start": str(f),
                "end": str(f),
                "color": "#00ffcc",
                "textColor": "#0e1117"
            })
    
    calendar(events=eventos, options={"initialView": "dayGridMonth", "locale": "es"})
