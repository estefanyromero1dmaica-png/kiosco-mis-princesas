import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Kiosco Mis Princesas PRO", layout="wide")
zona_ve = pytz.timezone('America/Caracas')

st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: #00ffcc; font-family: 'monospace'; }
    div[data-testid="stMetric"] {
        background: #161a23;
        border: 2px solid #00ffcc;
        border-radius: 10px;
        padding: 20px;
    }
    .stButton>button {
        border-radius: 5px;
        background: #161a23;
        color: #00ffcc;
        border: 1px solid #00ffcc;
        font-weight: bold;
        width: 100%;
        height: 3em;
    }
    .stButton>button:hover { background: #00ffcc; color: #161a23; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE DATOS (SESIÓN LOCAL) ---
if 'inventario' not in st.session_state:
    # Empezamos con una lista vacía para que tú la llenes
    st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    st.session_state.ventas_totales = 0

# --- 3. CUERPO DE LA APP ---
st.title("👑 KIOSCO MIS PRINCESAS: CONTROL TOTAL")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "💰 REGISTRAR VENTA", "📥 INGRESAR PRODUCTOS"])

# --- TAB 3: AQUÍ INGRESAS TÚ SOLA LOS PRODUCTOS ---
with tab3:
    st.subheader("Añadir Mercancía Nueva")
    with st.form("nuevo_item", clear_on_submit=True):
        col_n, col_p, col_s = st.columns([2, 1, 1])
        nombre = col_n.text_input("Nombre del Producto")
        precio = col_p.number_input("Precio ($)", min_value=0, step=1)
        cantidad = col_s.number_input("Cantidad", min_value=0, step=1)
        
        if st.form_submit_button("AÑADIR AL INVENTARIO"):
            if nombre:
                nueva_fila = pd.DataFrame([{"Producto": nombre, "Precio": int(precio), "Stock": int(cantidad)}])
                st.session_state.inventario = pd.concat([st.session_state.inventario, nueva_fila], ignore_index=True)
                st.success(f"✅ {nombre} agregado correctamente.")
            else:
                st.error("Escribe un nombre para el producto.")

# --- TAB 1: DASHBOARD ---
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas del Turno", f"$ {int(st.session_state.ventas_totales)}")
    c2.metric("Total Productos", len(st.session_state.inventario))
    c3.metric("Stock Total", int(st.session_state.inventario['Stock'].sum()) if not st.session_state.inventario.empty else 0)
    
    st.divider()
    st.subheader("Lista de Productos")
    st.dataframe(st.session_state.inventario, use_container_width=True, hide_index=True)

# --- TAB 2: REGISTRAR VENTA ---
with tab2:
    st.subheader("Punto de Venta")
    if not st.session_state.inventario.empty:
        prod_sel = st.selectbox("Seleccione lo que vendió:", st.session_state.inventario['Producto'].tolist())
        
        # Buscar datos del producto
        idx = st.session_state.inventario[st.session_state.inventario['Producto'] == prod_sel].index[0]
        item = st.session_state.inventario.iloc[idx]
        
        st.info(f"Precio: ${int(item['Precio'])} | Disponible: {int(item['Stock'])} unidades")
        
        if st.button("CONFIRMAR VENTA"):
            if item['Stock'] > 0:
                st.session_state.inventario.at[idx, 'Stock'] -= 1
                st.session_state.ventas_totales += int(item['Precio'])
                st.balloons()
                st.rerun()
            else:
                st.error("No queda stock de este producto.")
    else:
        st.warning("Primero ingresa productos en la pestaña 'INGRESAR PRODUCTOS'.")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 Usuario: Estefany")
    st.write(f"⏰ {datetime.now(zona_ve).strftime('%H:%M:%S')}")
    st.divider()
    if st.button("🗑️ REINICIAR TODO (BORRAR TODO)"):
        st.session_state.inventario = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
        st.session_state.ventas_totales = 0
        st.rerun()
