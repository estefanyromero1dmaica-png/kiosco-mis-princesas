import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA Y HORA ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")

# Configuración precisa para Venezuela (Palmira)
zona_venezuela = pytz.timezone('America/Caracas')
hora_actual = datetime.now(zona_venezuela)

# --- 2. ESTILO VISUAL PROFESIONAL (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Tarjetas de Métricas Dinámicas */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e2130, #161925);
        padding: 25px !important;
        border-radius: 20px;
        border: 1px solid rgba(0, 255, 204, 0.2);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-8px);
        border-color: #00ffcc;
        box-shadow: 0 12px 20px rgba(0, 255, 204, 0.15);
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
    
    /* Botones y Tabs */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: 0.2s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN A GOOGLE SHEETS ---
# 🚨 RECUERDA PEGAR TU LINK AQUÍ
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

@st.cache_data(ttl=60)
def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        return df.dropna(how="all").reset_index(drop=True)
    except Exception:
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. SEGURIDAD Y ESTADO DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.ventas_acumuladas = 0.0
    st.session_state.entrada = None

# --- PANTALLA DE ACCESO (LOGIN) ---
if st.session_state.usuario is None:
    col_login, _ = st.columns([1, 1]) 
    with col_login:
        st.title("🔐 Acceso al Sistema")
        st.markdown("---")
        with st.form("login_form"):
            u = st.text_input("Identificador de Usuario:").strip().lower()
            p = st.text_input("PIN de Seguridad (4 dígitos):", type="password")
            
            if st.form_submit_button("🚀 INICIAR TURNO", use_container_width=True):
                if u in ["estefany", "milagros", "gabriela", "mario"] and p == "2984":
                    # Configuración inmediata de sesión
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = hora_actual 
                    
                    # Sincronización de asistencia
                    try:
                        fecha_hoy = hora_actual.strftime('%Y-%m-%d')
                        df_asist = cargar_datos("Asistencia")
                        if df_asist.empty or fecha_hoy not in df_asist["Fecha"].astype(str).values:
                            nueva_fila = pd.DataFrame([{"Fecha": fecha_hoy}])
                            df_total = pd.concat([df_asist, nueva_fila], ignore_index=True)
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                            st.toast(f"✅ Asistencia registrada: {fecha_hoy}")
                    except Exception:
                        st.toast("⚠️ Nota: Turno iniciado localmente (Sin red).")
                    
                    st.rerun()
                else:
                    st.error("🚫 Acceso denegado. Revisa tus datos.")

# --- INTERFAZ PRINCIPAL (SOLO TRAS LOGIN EXITOSO) ---
else:
    # 1. Sidebar de Control
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0; color:white;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc; font-size: 0.9rem;'>Kiosco Activo</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.entrada:
            c_side1, c_side2 = st.columns(2)
            c_side1.metric("Fecha", st.session_state.entrada.strftime('%d/%m'))
            c_side2.metric("Hora", st.session_state.entrada.strftime('%H:%M'))
        
        st.divider()
        
        if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.session_state.entrada = None
            st.rerun()

    # 2. Tabs de Operación
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 PUNTO DE VENTA", "📅 ASISTENCIA"])

    # TAB 1: DASHBOARD
    with t1:
        st.markdown("### Resumen de Hoy")
        c1, c2, c3 = st.columns(3)
        
        # Cálculos de stock con limpieza de datos
        stock_limpio = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0)
        total_stk = stock_limpio.sum()
        alertas = len(df_inv[stock_limpio < 5])
        
        c1.metric("Ingresos Turno", f"$ {st.session_state.ventas_acumuladas:,.2f}")
        c2.metric("Stock Total", f"{int(total_stk)} und")
        c3.metric("Alertas Críticas", alertas, delta_color="inverse")
        
        if alertas > 0:
            st.warning(f"⚠️ ¡Atención! Hay {alertas} productos con stock menor a 5 unidades.")

    # TAB 2: INVENTARIO
    with t2:
        st.markdown("### 📦 Gestión de Mercancía")
        busq = st.text_input("🔍 Filtrar productos...", placeholder="Escribe el nombre...")
        
        df_f = df_inv[df_inv['Producto'].str.contains(busq, case=False, na=False)] if busq else df_inv
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        
        with st.expander("✨ Registrar Nuevo Artículo"):
            with st.form("form_add"):
                col_n, col_p, col_s = st.columns([2, 1, 1])
                n_new = col_n.text_input("Nombre del producto")
                p_new = col_p.number_input("Precio ($)", min_value=0.0, step=0.01)
                s_new = col_s.number_input("Stock inicial", min_value=0, step=1)
                
                if st.form_submit_button("📥 GUARDAR EN NUBE"):
                    if n_new:
                        nuevo_df = pd.DataFrame([{"Producto": n_new, "Precio": p_new, "Stock": s_new}])
                        df_actualizado = pd.concat([df_inv, nuevo_df], ignore_index=True)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_actualizado)
                        st.success("✅ Producto registrado con éxito.")
                        st.rerun()

    # TAB 3: PUNTO DE VENTA
    with t3:
        st.markdown("### 💰 Ventas del Turno")
        if not df_inv.empty:
            col_v1, col_v2 = st.columns([2, 1])
            with col_v1:
                sel = st.selectbox("Seleccionar producto:", df_inv['Producto'].tolist())
                datos_sel = df_inv[df_inv['Producto'] == sel].iloc[0]
                precio_v = float(datos_sel['Precio'])
                stock_v = int(pd.to_numeric(datos_sel['Stock'], errors='coerce') or 0)
            
            with col_v2:
                st.info(f"**Precio:** ${precio_v:,.2f}  \n**Disponible:** {stock_v} und")
            
            if stock_v > 0:
                if st.button(f"🛒 CONFIRMAR VENTA - ${precio_v}", use_container_width=True, type="primary"):
                    idx = df_inv[df_inv['Producto'] == sel].index[0]
                    st.session_state.ventas_acumuladas += precio_v
                    df_inv.at[idx, 'Stock'] = stock_v - 1
                    
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.balloons()
                    st.toast(f"¡Venta registrada! - {sel}")
                    st.rerun()
            else:
                st.error("❌ No hay stock disponible para este producto.")

    # TAB 4: CALENDARIO DE ASISTENCIA
    with t4:
        st.markdown("### 📅 Historial de Turnos")
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            eventos_cal = []
            for fecha in df_as["Fecha"]:
                eventos_cal.append({
                    "title": "Turno",
                    "start": str(fecha),
                    "end": str(fecha),
                    "color": "#00ffcc",
                    "textColor": "#0e1117"
                })
            calendar(events=eventos_cal, options={"initialView": "dayGridMonth", "locale": "es"})
