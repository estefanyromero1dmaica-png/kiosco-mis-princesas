import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema Kiosco PRO", layout="wide", initial_sidebar_state="expanded")

# --- 2. GESTIÓN DE DATOS (CSV) ---
# Archivo para el inventario
INV_FILE = "inventario_kiosco.csv"
if not os.path.exists(INV_FILE):
    df_init = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    df_init.to_csv(INV_FILE, index=False)

# --- 3. ESTADO DE LA SESIÓN (MEMORIA DE LA APP) ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.hora_entrada = None
    st.session_state.ventas_acumuladas = 0.0

# --- 4. LÓGICA DE ACCESO (LOGIN) ---
if st.session_state.usuario is None:
    st.title("🏪 Bienvenido al Sistema del Kiosco")
    st.subheader("Por favor, inicia tu turno para continuar")
    
    with st.container():
        nombre_operador = st.text_input("Nombre del Operador:", placeholder="Ej. Estefany")
        if st.button("🚀 INICIAR TURNO Y ABRIR CAJA"):
            if nombre_operador:
                st.session_state.usuario = nombre_operador
                st.session_state.hora_entrada = datetime.now()
                st.success(f"Turno iniciado por {nombre_operador}")
                st.rerun()
            else:
                st.error("Debes ingresar un nombre para trabajar.")
else:
    # --- 5. BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.header(f"👤 Operador: {st.session_state.usuario}")
        st.info(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}\n\n⏰ Entrada: {st.session_state.hora_entrada.strftime('%H:%M:%S')}")
        
        if st.button("🔴 FINALIZAR TURNO Y SALIR"):
            hora_salida = datetime.now().strftime('%H:%M:%S')
            st.warning(f"Turno de {st.session_state.usuario} cerrado a las {hora_salida}")
            st.session_state.usuario = None # Resetear sesión
            st.rerun()

    # --- 6. PANTALLA PRINCIPAL CON PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 REGISTRAR VENTA"])

    # --- PESTAÑA 1: RESUMEN DEL DÍA ---
    with tab1:
        st.title(f"Resumen de Ventas - {st.session_state.usuario}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Venta Total del Día", f"$ {st.session_state.ventas_acumuladas}")
        col2.metric("Hora de Inicio", st.session_state.hora_entrada.strftime('%H:%M'))
        
        # Alerta de Stock Bajo
        df = pd.read_csv(INV_FILE)
        stock_critico = df[df['Stock'] < 5]
        col3.metric("Alertas de Stock", f"{len(stock_critico)} productos")
        
        if not stock_critico.empty:
            st.error("⚠️ ¡PRODUCTOS POR AGOTARSE!")
            st.table(stock_critico)

    # --- PESTAÑA 2: CONTROL DE INVENTARIO ---
    with tab2:
        st.header("Gestión de Mercancía")
        
        with st.expander("➕ Añadir Nuevo Producto"):
            c_nom, c_pre, c_can = st.columns(3)
            nuevo_nom = c_nom.text_input("Nombre del Producto")
            nuevo_pre = c_pre.number_input("Precio ($)", min_value=0.0, step=0.5)
            nuevo_can = c_can.number_input("Cantidad Inicial", min_value=1, step=1)
            
            if st.button("Guardar en Base de Datos"):
                nuevo_prod = pd.DataFrame([[nuevo_nom, nuevo_pre, nuevo_can]], columns=["Producto", "Precio", "Stock"])
                df = pd.concat([df, nuevo_prod], ignore_index=True)
                df.to_csv(INV_FILE, index=False)
                st.success("¡Producto registrado!")
                st.rerun()

        st.subheader("Inventario Actual")
        st.dataframe(df, use_container_width=True)

    # --- PESTAÑA 3: VENTAS RÁPIDAS ---
    with tab3:
        st.header("Nueva Venta")
        if not df.empty:
            prod_seleccionado = st.selectbox("Selecciona el producto vendido:", df['Producto'].tolist())
            
            if st.button("✅ REGISTRAR VENTA (1 unidad)"):
                # Obtener precio y restar stock
                idx = df[df['Producto'] == prod_seleccionado].index[0]
                if df.at[idx, 'Stock'] > 0:
                    precio_venta = df.at[idx, 'Precio']
                    df.at[idx, 'Stock'] -= 1
                    df.to_csv(INV_FILE, index=False)
                    
                    st.session_state.ventas_acumuladas += precio_venta
                    st.balloons()
                    st.success(f"Venta registrada: {prod_seleccionado} por ${precio_venta}")
                else:
                    st.error("¡No queda stock de este producto!")
        else:
            st.info("Primero agrega productos en la pestaña de Inventario.")
