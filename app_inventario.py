import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# --- CONFIGURACIÓN DE APARIENCIA ---
st.set_page_config(page_title="Kiosco Mis Princesas V7", layout="wide")
zona_ve = pytz.timezone('America/Caracas')

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background: #1e2130; border-radius: 15px; padding: 20px; border: 1px solid #00ffcc; }
    .vender-btn { background-color: #00ffcc !important; color: black !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS LOCAL (Para evitar errores de Cloud) ---
# Si no quieres Cloud, lo mejor es manejar una sesión activa
if 'inventario' not in st.session_state:
    # Inventario inicial de ejemplo (Luego puedes cargar tu CSV)
    st.session_state.inventario = pd.DataFrame([
        {"Producto": "Esmalte Rojo", "Precio": 5, "Stock": 10},
        {"Producto": "Brillo Labial", "Precio": 3, "Stock": 15},
        {"Producto": "Polvo Compacto", "Precio": 12, "Stock": 5}
    ])
    st.session_state.ventas_totales = 0

# --- FUNCIONES ---
def registrar_venta(nombre_prod):
    df = st.session_state.inventario
    idx = df[df['Producto'] == nombre_prod].index[0]
    if df.at[idx, 'Stock'] > 0:
        df.at[idx, 'Stock'] -= 1
        st.session_state.ventas_totales += df.at[idx, 'Precio']
        st.toast(f"✅ Venta registrada: {nombre_prod}")
    else:
        st.error("❌ Sin stock")

# --- INTERFAZ PROFESIONAL ---
st.title("👑 Kiosco Mis Princesas PRO")
st.subheader("Gestión Local de Alta Velocidad (Sin Bloqueos de Cloud)")

tab1, tab2, tab3 = st.tabs(["📊 ESTADO ACTUAL", "💰 TERMINAL DE VENTAS", "⚙️ CONFIGURACIÓN"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos del Turno", f"$ {st.session_state.ventas_totales}")
    c2.metric("Productos en Tienda", len(st.session_state.inventario))
    c3.metric("Stock Crítico", len(st.session_state.inventario[st.session_state.inventario['Stock'] < 3]))
    
    st.divider()
    st.dataframe(st.session_state.inventario, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### ⚡ Punto de Venta Rápido")
    # Crear una cuadrícula de botones para vender rápido
    items = st.session_state.inventario['Producto'].tolist()
    cols = st.columns(3)
    for i, p in enumerate(items):
        with cols[i % 3]:
            precio_p = st.session_state.inventario.iloc[i]['Precio']
            stock_p = st.session_state.inventario.iloc[i]['Stock']
            if st.button(f"{p}\n(${precio_p}) | Stock: {stock_p}", key=f"btn_{i}"):
                registrar_venta(p)
                st.rerun()

with tab3:
    st.subheader("📥 Cargar/Descargar Datos")
    st.write("Como no usaremos Cloud, puedes subir tu archivo Excel cada mañana y descargarlo al cerrar el kiosco.")
    
    # Subir Excel
    archivo = st.file_uploader("Subir Inventario (Excel/CSV)", type=["csv", "xlsx"])
    if archivo:
        if archivo.name.endswith('.csv'):
            st.session_state.inventario = pd.read_csv(archivo)
        else:
            st.session_state.inventario = pd.read_excel(archivo)
        st.success("¡Inventario actualizado!")
    
    st.divider()
    
    # Descargar Excel
    csv = st.session_state.inventario.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 DESCARGAR INVENTARIO FINAL (CIERRE DE CAJA)",
        data=csv,
        file_name=f"inventario_{datetime.now().strftime('%d_%m')}.csv",
        mime='text/csv',
    )

st.sidebar.markdown(f"**Usuario:** Estefany")
st.sidebar.markdown(f"**Hora:** {datetime.now(zona_ve).strftime('%H:%M:%S')}")
