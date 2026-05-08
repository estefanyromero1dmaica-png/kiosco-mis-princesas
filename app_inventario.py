import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA Y HORA ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", page_icon="🏪", layout="wide")

# Configuración precisa para Venezuela (Caracas/Palmira)
zona_venezuela = pytz.timezone('America/Caracas')
hora_ahora = datetime.now(zona_venezuela)

# --- 2. ESTILO VISUAL PREMIUM (CSS CUSTOM COMPLETO) ---
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
    
    /* Ajuste de valores para que no se corten (...) */
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
# 🚨 RECUERDA VERIFICAR QUE ESTE LINK SEA EL CORRECTO
URL_HOJA = "TU_LINK_DE_GOOGLE_SHEETS_AQUI"

@st.cache_data(ttl=60)
def cargar_datos(pestana):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
        return df.dropna(how="all").reset_index(drop=True)
    except Exception as e:
        # Crea estructuras básicas si la hoja está vacía o falla la red
        if pestana == "Asistencia":
            return pd.DataFrame(columns=["Fecha", "Usuario", "Hora_Entrada"])
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 4. CONTROL DE SESIÓN Y SEGURIDAD ---
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
                usuarios_autorizados = ["estefany", "milagros", "gabriela", "mario"]
                if u in usuarios_autorizados and p == "2984":
                    # REGISTRO DE DATOS EN SESIÓN
                    st.session_state.usuario = u.capitalize()
                    st.session_state.entrada = datetime.now(zona_venezuela)
                    st.session_state.ventas_acumuladas = 0.0
                    
                    # SINCRONIZACIÓN CON GOOGLE SHEETS
                    try:
                        f_hoy = hora_ahora.strftime('%Y-%m-%d')
                        h_ent = hora_ahora.strftime('%H:%M:%S')
                        df_asist = cargar_datos("Asistencia")
                        
                        # Añadimos registro completo: Fecha, Quién y Hora
                        nueva_asistencia = pd.DataFrame([{"Fecha": f_hoy, "Usuario": st.session_state.usuario, "Hora_Entrada": h_ent}])
                        df_total = pd.concat([df_asist, nueva_asistencia], ignore_index=True)
                        
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Asistencia", data=df_total)
                        st.toast(f"✅ Turno de {st.session_state.usuario} registrado.")
                    except:
                        st.toast("⚠️ Trabajando en modo local (Sin conexión)")
                    
                    st.rerun()
                else:
                    st.error("🚫 PIN o Usuario incorrecto. Inténtalo de nuevo.")

# --- INTERFAZ PRINCIPAL (SISTEMA ACTIVO) ---
else:
    # --- SIDEBAR: ESTADO DEL TURNO ---
    with st.sidebar:
        st.markdown(f"""
            <div class="user-card">
                <h2 style='margin:0;'>👤 {st.session_state.usuario}</h2>
                <p style='margin:0; color:#00ffcc;'>Kiosco Mis Princesas</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Información de tiempo real
        st.write(f"📅 **Hoy:** {st.session_state.entrada.strftime('%d/%m/%Y')}")
        st.write(f"⏰ **Entrada:** {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # LÓGICA DE CIERRE SEGURO (MÍNIMO 5 MINUTOS)
        ahora_actual = datetime.now(zona_venezuela)
        diferencia = ahora_actual - st.session_state.entrada
        segundos_restantes = 300 - diferencia.total_seconds() # 300 seg = 5 min
        
        if segundos_restantes > 0:
            st.warning(f"🔒 Cierre bloqueado. Faltan {int(segundos_restantes)} segundos.")
            st.button("🔴 CERRAR TURNO", use_container_width=True, disabled=True, help="Debes cumplir al menos 5 minutos de turno.")
        else:
            if st.button("🔴 FINALIZAR TURNO", use_container_width=True, type="primary"):
                st.session_state.usuario = None
                st.session_state.entrada = None
                st.rerun()

    # --- CUERPO PRINCIPAL: NAVEGACIÓN ---
    df_inv = cargar_datos("Hoja 1")
    t1, t2, t3, t4 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 PUNTO DE VENTA", "📅 HISTORIAL"])

    # TAB 1: DASHBOARD (MÉTRICAS)
    with t1:
        st.markdown("### Estado General del Kiosco")
        c1, c2, c3 = st.columns(3)
        
        # Cálculos de stock dinámicos
        stock_num = pd.to_numeric(df_inv['Stock'], errors='coerce').fillna(0)
        total_articulos = int(stock_num.sum())
        productos_bajos = len(df_inv[stock_num < 5])
        
        c1.metric("Ventas del Turno", f"$ {st.session_state.ventas_acumuladas:,.2f}")
        c2.metric("Stock en Tienda", f"{total_articulos} unidades")
        c3.metric("Alertas Críticas", productos_bajos, delta="- Reponer pronto", delta_color="inverse")
        
        if productos_bajos > 0:
            st.error(f"🚨 ¡Atención! Tienes {productos_bajos} productos casi agotados.")

    # TAB 2: INVENTARIO (GESTIÓN)
    with t2:
        st.markdown("### 📦 Control de Mercancía")
        filtro = st.text_input("🔍 Buscar por nombre de producto...", placeholder="Escribe aquí...")
        
        df_mostrar = df_inv[df_inv['Producto'].str.contains(filtro, case=False, na=False)] if filtro else df_inv
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        with st.expander("✨ Registrar Entrada de Nuevo Producto"):
            with st.form("nuevo_item"):
                c_n, c_p, c_s = st.columns([2,1,1])
                nom = c_n.text_input("Nombre del Producto")
                pre = c_p.number_input("Precio ($)", min_value=0.0, step=0.01)
                stk = c_s.number_input("Cantidad Inicial", min_value=0, step=1)
                
                if st.form_submit_button("📥 GUARDAR EN INVENTARIO", use_container_width=True):
                    if nom:
                        nuevo_df = pd.DataFrame([{"Producto": nom, "Precio": pre, "Stock": stk}])
                        df_final = pd.concat([df_inv, nuevo_df], ignore_index=True)
                        st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_final)
                        st.success(f"✅ {nom} añadido correctamente.")
                        st.rerun()

    # TAB 3: PUNTO DE VENTA (CAJA)
    with t3:
        st.markdown("### 💰 Punto de Venta Rápido")
        if not df_inv.empty:
            col_sel, col_info = st.columns([2, 1])
            with col_sel:
                producto_sel = st.selectbox("Seleccione el producto a vender:", df_inv['Producto'].tolist())
                info_prod = df_inv[df_inv['Producto'] == producto_sel].iloc[0]
                precio_actual = float(info_prod['Precio'])
                stock_actual = int(pd.to_numeric(info_prod['Stock'], errors='coerce') or 0)
            
            with col_info:
                st.markdown(f"**Precio:** ${precio_actual:,.2f}")
                st.markdown(f"**Stock:** {stock_actual} und")

            if stock_actual > 0:
                if st.button(f"🛒 CONFIRMAR VENTA (${precio_actual})", use_container_width=True, type="primary"):
                    idx_venta = df_inv[df_inv['Producto'] == producto_sel].index[0]
                    st.session_state.ventas_acumuladas += precio_actual
                    df_inv.at[idx_venta, 'Stock'] = stock_actual - 1
                    
                    # Guardar cambio en Google Sheets
                    st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_HOJA, worksheet="Hoja 1", data=df_inv)
                    st.balloons()
                    st.toast(f"Venta registrada: {producto_sel}")
                    st.rerun()
            else:
                st.error("❌ No queda stock de este producto.")

    # TAB 4: CALENDARIO (ASISTENCIA)
    with t4:
        st.markdown("### 📅 Registro de Actividad")
        df_as = cargar_datos("Asistencia")
        if not df_as.empty:
            # Creamos eventos para el calendario basados en la hoja de Asistencia
            eventos_lista = []
            for i, r in df_as.iterrows():
                eventos_lista.append({
                    "title": f"Turno: {r['Usuario']}",
                    "start": str(r['Fecha']),
                    "end": str(r['Fecha']),
                    "color": "#00ffcc",
                    "textColor": "#0e1117"
                })
            calendar(events=eventos_lista, options={"initialView": "dayGridMonth", "locale": "es"})
