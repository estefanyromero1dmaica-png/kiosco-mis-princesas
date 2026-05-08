import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE ALTO NIVEL ---
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
    .main {
        background-color: #0e1117;
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Estilo de las métricas (Dashboard) */
    div[data-testid="stMetric"] {
        background-color: #1e2130;
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
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        df = df.dropna(how="all").reset_index(drop=True)
        
        # Forzar limpieza de decimales si existen en la carga
        for col in ['Precio', 'Stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        # Estructura por defecto si falla la carga
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

def actualizar_nube(pestana, df_actualizado):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Limpieza final de decimales antes de guardar
        for col in ['Precio', 'Stock']:
            if col in df_actualizado.columns:
                df_actualizado[col] = pd.to_numeric(df_actualizado[col], errors='coerce').fillna(0).astype(int)
        
        conn.update(spreadsheet=URL_HOJA, worksheet=pestana, data=df_actualizado)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Fallo al sincronizar: {e}")
        return False

# --- 4. GESTIÓN DE SESIÓN ---
if 'usuario_activo' not in st.session_state:
    st.session_state.usuario_activo = None
    st.session_state.ventas_turno = 0
    st.session_state.hora_entrada = None

# --- 5. PANTALLA DE ACCESO (LOGIN) ---
if st.session_state.usuario_activo is None:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.title("🏪 Sistema Mis Princesas")
        st.markdown("### Control de Acceso Operadores")
        with st.form("login_form"):
            usuario_ingresado = st.text_input("👤 Nombre de Usuario:", placeholder="Ej: Milagros").strip()
            pin_seguridad = st.text_input("🔑 PIN de Seguridad:", type="password")
            
            if st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True):
                # Validamos usuarios (ajusta la lógica si usas un PIN)
                if usuario_ingresado.lower() in ["estefany", "milagros", "gabriela", "mario"] and pin_seguridad == "2984":
                    st.session_state.usuario_activo = usuario_ingresado.capitalize()
                    st.session_state.hora_entrada = datetime.now(zona_venezuela)
                    st.session_state.ventas_turno = 0
                    
                    # Registro Automático en la Hoja de Asistencia
                    df_asis = cargar_datos("Asistencia")
                    nuevo_registro = pd.DataFrame([{
                        "Fecha": st.session_state.hora_entrada.strftime('%Y-%m-%d'),
                        "Usuario": st.session_state.usuario_activo,
                        "Hora_Entrada": st.session_state.hora_entrada.strftime('%H:%M:%S')
                    }])
                    df_final_asis = pd.concat([df_asis, nuevo_registro], ignore_index=True)
                    actualizar_nube("Asistencia", df_final_asis)
                    
                    st.success(f"Bienvenida, {st.session_state.usuario_activo}")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Verifique e intente de nuevo.")

# --- 6. INTERFAZ OPERATIVA PRINCIPAL ---
else:
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        # Tarjeta de Usuario Elegante
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario_activo}</h2>
                <p style='margin:0; color:#00ffcc;'>Panel de Control</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Información de Turno
        st.write(f"📅 **Hoy:** {st.session_state.hora_entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.hora_entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # Botón de Cerrar Sesión Claro y Visible
        if st.button("🔴 CERRAR TURNO Y SALIR", use_container_width=True, type="primary"):
            st.session_state.usuario_activo = None
            st.rerun()

    # --- NAVEGACIÓN POR TABS (Pestañas Masivas) ---
    # Carga base de inventario para las tabs
    df_inv = cargar_datos("Hoja 1")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO COMPLETO", "💰 PUNTO DE VENTA", "📅 REGISTRO ASISTENCIA"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.markdown("### Estado General de Operaciones")
        col1, col2, col3 = st.columns(3)
        
        total_stock = int(df_inv['Stock'].sum())
        criticos = len(df_inv[df_inv['Stock'] < 5])
        
        col1.metric("Ventas del Turno Activo", f"$ {int(st.session_state.ventas_turno)}")
        col2.metric("Total Unidades Stock", f"{total_stock} und")
        col3.metric("Alertas Stock Crítico", criticos, delta="- Reponer" if criticos > 0 else "OK")
        
        if criticos > 0:
            st.error(f"⚠️ ¡Atención! Hay {criticos} productos con stock menor a 5 unidades.")

    # --- TAB 2: INVENTARIO COMPLETO ---
    with tab2:
        st.markdown("### 📦 Gestión Completa de Mercancía")
        
        # Buscador Avanzado
        col_busqueda, col_vacia = st.columns([3, 1])
        busqueda = col_busqueda.text_input("🔍 Buscar por nombre...", placeholder="Escribe el nombre del producto...")
        
        if busqueda:
            df_ver = df_inv[df_inv['Producto'].str.contains(busqueda, case=False, na=False)]
        else:
            df_ver = df_inv
            
        st.dataframe(df_ver, use_container_width=True, hide_index=True)
        
        # Sección elegante para Añadir Mercancía
        st.divider()
        with st.expander("✨ AÑADIR NUEVA MERCANCÍA AL INVENTARIO", expanded=False):
            with st.form("nuevo_producto_form"):
                cnom, cpre, cstk = st.columns([2, 1, 1])
                nom = cnom.text_input("Nombre del Artículo:", placeholder="Ej: Esmalte Noche")
                pre = cpre.number_input("Precio ($):", min_value=0, step=1)
                stk = cstk.number_input("Stock Inicial:", min_value=0, step=1)
                
                if st.form_submit_button("💾 GUARDAR PRODUCTO", use_container_width=True):
                    if nom:
                        nuevo_item = pd.DataFrame([{"Producto": nom, "Precio": int(pre), "Stock": int(stk)}])
                        df_total_inv = pd.concat([df_inv, nuevo_item], ignore_index=True)
                        if actualizar_nube("Hoja 1", df_total_inv):
                            st.success(f"✅ {nom} agregado exitosamente.")
                            st.rerun()
                    else:
                        st.error("❌ El nombre es obligatorio.")

    # --- TAB 3: PUNTO DE VENTA (CAJA) ---
    with tab3:
        st.markdown("### 💰 Registro de Ventas Directas")
        if not df_inv.empty:
            lista_productos = df_inv['Producto'].tolist()
            col_sel, col_det = st.columns([2, 1])
            with col_sel:
                p_sel = st.selectbox("Seleccione producto vendido:", lista_productos)
                datos_p = df_inv[df_inv['Producto'] == p_sel].iloc[0]
            
            with col_det:
                st.markdown(f"**Precio:** ${int(datos_p['Precio'])}")
                st.markdown(f"**Disponibles:** {int(datos_p['Stock'])}")

            if datos_p['Stock'] > 0:
                if st.button(f"🛒 COMPLETAR VENTA (${int(datos_p['Precio'])})", use_container_width=True, type="primary"):
                    # Actualizar en memoria y nube
                    idx = df_inv[df_inv['Producto'] == p_sel].index[0]
                    st.session_state.ventas_turno += int(datos_p['Precio'])
                    df_inv.at[idx, 'Stock'] = int(datos_p['Stock']) - 1
                    
                    if actualizar_nube("Hoja 1", df_inv):
                        st.balloons() # Feedback festivo
                        st.rerun()
            else:
                st.error("❌ PRODUCTO AGOTADO. No se puede realizar la venta.")

    # --- TAB 4: HISTORIAL DE ASISTENCIA ---
    with tab4:
        st.markdown("### 📅 Registro de Entradas y Turnos de Operadores")
        df_asistencia = cargar_datos("Asistencia")
        if not df_asistencia.empty:
            st.dataframe(df_asistencia.sort_values(by="Hora_Entrada", ascending=False), use_container_width=True, hide_index=True)
            
            # Calendario Interactivo Profesional
            st.divider()
            st.markdown("#### Vista de Calendario de Actividad")
            eventos_calendar = []
            for _, row in df_asistencia.iterrows():
                eventos_calendar.append({
                    "title": f"Entrada: {row['Usuario']}",
                    "start": str(row['Fecha']),
                    "end": str(row['Fecha']),
                    "color": "#00ffcc",
                    "textColor": "#0e1117"
                })
            
            calendar(events=eventos_calendar, options={"initialView": "dayGridMonth", "locale": "es"})
