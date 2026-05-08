import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTÉTICA DARK NEÓN ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", layout="wide")
zona_ve = pytz.timezone('America/Caracas')

st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: #00ffcc; font-family: 'monospace'; }
    div[data-testid="stMetric"] {
        background: #161a23;
        border: 2px solid #00ffcc;
        box-shadow: 8px 8px 0px #005544;
        padding: 20px;
    }
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
    .stButton>button:hover { background: #00ffcc; color: #161a23; box-shadow: 0 0 20px #00ffcc; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161a23;
        color: white;
        border-radius: 5px 5px 0px 0px;
        padding: 12px 30px;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] { border: 1px solid #00ffcc !important; color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INICIALIZACIÓN DE BASE DE DATOS (VACÍA POR DEFECTO) ---
if 'inventario' not in st.session_state:
    # El sistema arranca sin ningún producto, tal como pediste.
    st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    st.session_state.ventas_totales = 0

# --- 3. FUNCIONES OPERATIVAS ---
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

# --- 4. INTERFAZ DE USUARIO ---
st.title("👑 KIOSCO MIS PRINCESAS v6.0")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 ESTADO DE TIENDA", "💰 REGISTRAR VENTA", "📥 INGRESAR MERCANCÍA"])

# --- PESTAÑA: INGRESAR PRODUCTOS ---
with tab3:
    st.header("📥 Panel de Carga de Inventario")
    st.write("Ingresa los datos de los nuevos productos para habilitarlos en el sistema.")
    
    with st.form("formulario_carga", clear_on_submit=True):
        col_nom, col_pre, col_can = st.columns([2, 1, 1])
        with col_nom:
            nuevo_nombre = st.text_input("Nombre del Artículo:")
        with col_pre:
            nuevo_precio = st.number_input("Precio Unitario ($):", min_value=0, step=1)
        with col_can:
            nuevo_stock = st.number_input("Cantidad Inicial:", min_value=0, step=1)
        
        if st.form_submit_button("💾 GUARDAR PRODUCTO EN SISTEMA"):
            if nuevo_nombre:
                agregar_producto(nuevo_nombre, nuevo_precio, nuevo_stock)
                st.success(f"¡{nuevo_nombre.upper()} registrado exitosamente!")
                st.rerun()
            else:
                st.error("Error: El nombre del producto no puede estar vacío.")

# --- PESTAÑA: DASHBOARD ---
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas Acumuladas", f"$ {int(st.session_state.ventas_totales)}")
    c2.metric("Variedad de Productos", len(st.session_state.inventario))
    
    total_unidades = int(st.session_state.inventario['Stock'].sum()) if not st.session_state.inventario.empty else 0
    c3.metric("Stock Físico Total", total_unidades)
    
    st.divider()
    st.subheader("📋 Inventario Detallado")
    if not st.session_state.inventario.empty:
        st.dataframe(st.session_state.inventario, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no has ingresado ningún producto. Ve a la pestaña 'INGRESAR MERCANCÍA'.")

# --- PESTAÑA: PUNTO DE VENTA ---
with tab2:
    st.header("💰 Terminal de Venta Rápida")
    if not st.session_state.inventario.empty:
        # Buscador rápido para ventas
        lista_nombres = st.session_state.inventario['Producto'].tolist()
        seleccion = st.selectbox("Buscar producto vendido:", lista_nombres)
        
        idx = st.session_state.inventario[st.session_state.inventario['Producto'] == seleccion].index[0]
        datos_item = st.session_state.inventario.iloc[idx]
        
        col_info1, col_info2 = st.columns(2)
        col_info1.info(f"💵 Precio: ${int(datos_item['Precio'])}")
        col_info2.warning(f"📦 Disponible: {int(datos_item['Stock'])} unidades")
        
        if st.button("🛒 CONFIRMAR VENTA"):
            if procesar_venta(idx):
                st.balloons()
                st.success(f"Venta de {seleccion} realizada.")
                st.rerun()
            else:
                st.error("No hay stock suficiente para realizar la venta.")
    else:
        st.warning("No hay artículos registrados para vender.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 👤 Administrador: Estefany")
    st.write(f"⏰ {datetime.now(zona_ve).strftime('%H:%M:%S')}")
    st.divider()
    if st.button("🗑️ RESETEAR SISTEMA (BORRADO TOTAL)"):
        st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
        st.session_state.ventas_totales = 0
        st.rerun()
