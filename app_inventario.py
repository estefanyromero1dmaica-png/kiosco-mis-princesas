import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE ALTO NIVEL ---
st.set_page_config(
    page_title="Kiosco Inteligente PRO - Gestión Total",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para mejorar la visualización
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    </style>
    """, unsafe_allow_context=True)

# --- 2. CONEXIÓN Y CARGA DE DATOS ---
# 🚨 PEGA TU LINK AQUÍ:
URL_HOJA = "https://docs.google.com/spreadsheets/d/108HEgQ1pkzxjxwYEU2YqhvkWGdkar7rvEPTVyI2CUAE/edit?gid=0#gid=0"

def conectar_nube():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None

def cargar_datos(sheet_name):
    conn = conectar_nube()
    if conn:
        try:
            data = conn.read(spreadsheet=URL_HOJA, worksheet=sheet_name)
            return data.dropna(how="all")
        except:
            # Si la pestaña no existe, devolvemos un DataFrame con las columnas correctas
            if sheet_name == "Asistencia":
                return pd.DataFrame(columns=["Fecha"])
            return pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    return pd.DataFrame()

# --- 3. GESTIÓN DE SESIÓN Y SEGURIDAD ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.entrada = None
    st.session_state.ventas_acumuladas = 0.0

# Lógica de Login
if st.session_state.usuario is None:
    st.title(" Acceso de Seguridad - Kiosco")
    st.markdown("---")
    
    col_login, _ = st.columns([1, 2])
    with col_login:
        with st.form("login_form"):
            u = st.text_input("Usuario / Operador (Nombre):").strip().lower()
            p = st.text_input("PIN de Acceso (4 dígitos):", type="password")
            boton = st.form_submit_button("INGRESAR AL SISTEMA")

            if boton:
                autorizados = ["estefany", "milagros", "milagro", "gabriela", "mario"]
                if u in autorizados and p == "2984":
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now()
                    
                    # REGISTRO AUTOMÁTICO EN EL CALENDARIO
                    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
                    df_asistencia = cargar_datos("Asistencia")
                    
                    if df_asistencia.empty or fecha_hoy not in df_asistencia["Fecha"].values:
                        nueva_fecha = pd.DataFrame([[fecha_hoy]], columns=["Fecha"])
                        df_final_asistencia = pd.concat([df_asistencia, nueva_fecha], ignore_index=True)
                        conn = conectar_nube()
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_final_asistencia)
                    
                    st.success(" Acceso concedido. Registro de asistencia guardado.")
                    st.rerun()
                else:
                    st.error(" Credenciales incorrectas. Verifique nombre y PIN.")
else:
    # --- 4. BARRA LATERAL PROFESIONAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.title(f"Operador: {st.session_state.usuario}")
        st.write(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        st.write(f"⏰ Hora Entrada: {st.session_state.entrada.strftime('%H:%M:%S')}")
        st.divider()
        
        if st.button(" CERRAR TURNO Y SALIR"):
            duracion = datetime.now() - st.session_state.entrada
            st.warning(f"Resumen de sesión: ${st.session_state.ventas_acumuladas} vendidos en {str(duracion).split('.')[0]}")
            st.session_state.usuario = None
            st.rerun()

    # Carga de datos de inventario
    df_inventario = cargar_datos("Hoja1") # Asegúrate de que sea "Hoja1" o el nombre de tu pestaña
    conn_global = conectar_nube()

    # --- 5. INTERFAZ POR PESTAÑAS (TABS) ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS", "📅 CALENDARIO"])

    # --- PESTAÑA 1: MÉTRICAS ---
    with tab1:
        st.title("Panel de Control del Kiosco")
        c1, c2, c3 = st.columns(3)
        
        c1.metric("Ventas del Turno", f"$ {st.session_state.ventas_acumuladas}", help="Dinero acumulado desde que entraste.")
        
        total_items = df_inventario['Stock'].astype(int).sum() if not df_inventario.empty else 0
        c2.metric("Total Productos en Stock", total_items)
        
        bajos = df_inventario[df_inventario['Stock'].astype(int) < 5] if not df_inventario.empty else pd.DataFrame()
        c3.metric("Alertas Críticas", len(bajos), delta_color="inverse")

        if not bajos.empty:
            st.subheader("⚠️ PRODUCTOS POR AGOTARSE")
            st.dataframe(bajos, use_container_width=True)

    # --- PESTAÑA 2: INVENTARIO + BUSCADOR ---
    with tab2:
        st.subheader("Gestión de Inventario en la Nube")
        
        # BUSCADOR
        query = st.text_input(" Buscar por nombre de producto...", placeholder="Escribe para filtrar...")
        
        df_filtrado = df_inventario[df_inventario['Producto'].str.contains(query, case=False, na=False)] if query else df_inventario

        with st.expander("➕ Registrar Nuevo Producto"):
            col_a, col_b, col_c = st.columns(3)
            nom = col_a.text_input("Nombre del Artículo")
            pre = col_b.number_input("Precio de Venta ($)", min_value=0.0, step=0.5)
            sto = col_c.number_input("Stock Inicial", min_value=0, step=1)
            
            if st.button("Guardar en Google Sheets"):
                if nom:
                    nuevo_item = pd.DataFrame([[nom, pre, sto]], columns=["Producto", "Precio", "Stock"])
                    df_final_inv = pd.concat([df_inventario, nuevo_item], ignore_index=True)
                    conn_global.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_final_inv)
                    st.success(f"✅ {nom} añadido correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor, ingresa el nombre.")

        st.dataframe(df_filtrado, use_container_width=True)

    # --- PESTAÑA 3: SISTEMA DE VENTAS ---
    with tab3:
        st.subheader("Terminal de Venta")
        if not df_inventario.empty:
            prod_lista = df_inventario['Producto'].tolist()
            seleccion = st.selectbox("Seleccione el producto vendido:", prod_lista)
            
            if st.button("🛒 REGISTRAR VENTA (1 UNIDAD)"):
                idx = df_inventario[df_inventario['Producto'] == seleccion].index[0]
                stock_actual = int(df_inventario.at[idx, 'Stock'])
                
                if stock_actual > 0:
                    # Actualizar sesión y datos
                    st.session_state.ventas_acumuladas += float(df_inventario.at[idx, 'Precio'])
                    df_inventario.at[idx, 'Stock'] = stock_actual - 1
                    # Sincronizar
                    conn_global.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_inventario)
                    st.balloons()
                    st.success(f"Venta de {seleccion} procesada.")
                    st.rerun()
                else:
                    st.error(f"¡Error! No hay stock suficiente de {seleccion}")
        else:
            st.info("Agregue productos en la pestaña de Inventario primero.")

    # --- PESTAÑA 4: CALENDARIO DE ASISTENCIA ---
    with tab4:
        st.header("Historial de Días Trabajados")
        df_asistencia = cargar_datos("Asistencia")
        
        eventos_calendario = []
        if not df_asistencia.empty:
            for f in df_asistencia["Fecha"]:
                eventos_calendario.append({
                    "title": "TRABAJADO",
                    "color": "#00FF00", # Verde brillante
                    "start": f,
                    "end": f,
                    "allDay": True
                })
        
        cal_options = {
            "initialView": "dayGridMonth",
            "selectable": False,
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        }
        
        calendar(events=eventos_calendario, options=cal_options)
        st.write(" El calendario marca automáticamente los días en los que iniciaste sesión.")
