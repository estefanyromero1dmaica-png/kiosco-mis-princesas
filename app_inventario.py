import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN Y ESTÉTICA DARK NEÓN (PRO) ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", layout="wide")
zona_ve = pytz.timezone('America/Caracas')

st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: #00ffcc; font-family: 'monospace'; }
    
    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background: #161a23;
        border: 2px solid #00ffcc;
        box-shadow: 8px 8px 0px #005544;
        padding: 20px;
    }
    
    /* Botones Estilo Brutalista */
    .stButton>button {
        border-radius: 0px;
        background: #161a23;
        color: #00ffcc;
        border: 2px solid #00ffcc;
        font-weight: bold;
        width: 100%;
        height: 3.5em;
        transition: 0.4s;
    }
    .stButton>button:hover { 
        background: #00ffcc; 
        color: #161a23; 
        box-shadow: 0 0 20px #00ffcc; 
    }
    
    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161a23;
        color: white;
        border-radius: 5px 5px 0px 0px;
        padding: 12px 30px;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] { 
        border: 1px solid #00ffcc !important; 
        color: #00ffcc !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (CONTROL TOTAL DE ESTEFANY) ---
if 'inventario' not in st.session_state:
    # Arranca vacío, tú ingresas todo
    st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    st.session_state.ventas_totales = 0

# --- 3. FUNCIONES DE OPERACIÓN ---
def agregar_producto(nombre, precio, cantidad):
    nueva_fila = pd.DataFrame([{
        "Producto": nombre.strip().upper(), 
        "Precio": int(precio), 
        "Stock": int(cantidad)
    }])
    st.session_state.inventario = pd.concat([st.session_state.inventario, nueva_fila], ignore_index=True)

def procesar_venta(indice):
    if st.session_state.inventario.at[indice, 'Stock'] > 0:
        st.session_state.inventario.at[indice, 'Stock'] -= 1
        st.session_state.ventas_totales += st.session_state.inventario.at[indice, 'Precio']
        return True
    return False

# --- 4. CUERPO DE LA APLICACIÓN ---
st.title("👑 KIOSCO MIS PRINCESAS v6.0")
st.markdown("---")

# Las tres pestañas clave
tab1, tab2, tab3 = st.tabs(["📊 ESTADO DE TIENDA", "💰 REGISTRAR VENTA", "📥 INGRESAR MERCANCÍA"])

# --- PESTAÑA 3: TU TERMINAL DE CARGA ---
with tab3:
    st.header("📥 Panel de Carga Manual")
    st.write("Aquí es donde tú sola construyes tu inventario.")
    
    with st.form("formulario_carga", clear_on_submit=True):
        col_nom, col_pre, col_can = st.columns([2, 1, 1])
        with col_nom:
            nuevo_nombre = st.text_input("Nombre del Artículo:")
        with col_pre:
            nuevo_precio = st.number_input("Precio Unitario ($):", min_value=0, step=1)
        with col_can:
            nuevo_stock = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        
        if st.form_submit_button("💾 GUARDAR EN SISTEMA"):
            if nuevo_nombre:
                agregar_producto(nuevo_nombre, nuevo_precio, nuevo_stock)
                st.success(f"¡{nuevo_nombre.upper()} REGISTRADO!")
                st.rerun()
            else:
                st.error("Error: El nombre es obligatorio.")

# --- PESTAÑA 1: DASHBOARD ---
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Acumuladas", f"$ {int(st.session_state.ventas_totales)}")
    c2.metric("Tipos de Productos", len(st.session_state.inventario))
    
    stock_fisico = int(st.session_state.inventario['Stock'].sum()) if not st.session_state.inventario.empty else 0
    c3.metric("Unidades en Estante", stock_fisico)
    
    st.divider()
    st.subheader("📋 Inventario Detallado")
    if not st.session_state.inventario.empty:
        # Mostramos la tabla sin decimales
        st.dataframe(st.session_state.inventario, use_container_width=True, hide_index=True)
    else:
        st.info("Sistema vacío. Ingresa productos en la pestaña correspondiente.")

# --- PESTAÑA 2: PUNTO DE VENTA ---
with tab2:
    st.header("💰 Terminal de Venta")
    if not st.session_state.inventario.empty:
        lista_nombres = st.session_state.inventario['Producto'].tolist()
        seleccion = st.selectbox("Buscar artículo vendido:", lista_nombres)
        
        # Localizar datos
        idx = st.session_state.inventario[st.session_state.inventario['Producto'] == seleccion].index[0]
        item = st.session_state.inventario.iloc[idx]
        
        col_p, col_s = st.columns(2)
        col_p.info(f"💵 Precio: ${int(item['Precio'])}")
        col_s.warning(f"📦 Disponible: {int(item['Stock'])} und")
        
        if st.button("🛒 CONFIRMAR VENTA"):
            if procesar_venta(idx):
                st.balloons()
                st.rerun()
            else:
                st.error("STOCK AGOTADO")
    else:
        st.warning("No hay productos cargados.")

# --- BARRA LATERAL (DATOS DE SESIÓN) ---
with st.sidebar:
    st.markdown(f"### 👤 Operador: Estefany")
    st.write(f"⏰ {datetime.now(zona_ve).strftime('%H:%M:%S')}")
    st.divider()
    if st.button("🗑️ RESET TOTAL"):
        st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
        st.session_state.ventas_totales = 0
        st.rerun()
