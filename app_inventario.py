import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema Kiosco PRO", layout="wide")

# --- 2. GESTIÓN DE DATOS (CSV) ---
INV_FILE = "inventario_kiosco.csv"
if not os.path.exists(INV_FILE):
    df_init = pd.DataFrame(columns=["Producto", "Precio", "Stock"])
    df_init.to_csv(INV_FILE, index=False)

# --- 3. ESTADO DE LA SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.hora_entrada = None
    st.session_state.ventas_acumuladas = 0.0

# --- 4. LÓGICA DE ACCESO RESTRINGIDO ---
if st.session_state.usuario is None:
    st.title("🔐 Acceso Restringido - Kiosco")
    
    # Lista de nombres autorizados (en minúsculas para comparar fácil)
    autorizados = ["estefany", "milagros", "milagro", "gabriela", "mario"]
    
    with st.form("login_form"):
        nombre_input = st.text_input("Nombre del Operador:").strip()
        pin_input = st.text_input("Contraseña (PIN):", type="password")
        boton_entrar = st.form_submit_button("INGRESAR")

        if boton_entrar:
            # Verificamos si el nombre (en minúsculas) está en la lista y si el PIN es correcto
            if nombre_input.lower() in autorizados and pin_input == "2984":
                st.session_state.usuario = nombre_input.capitalize()
                st.session_state.hora_entrada = datetime.now()
                st.success(f"Bienvenido/a {st.session_state.usuario}")
                st.rerun()
            else:
                st.error("❌ Acceso Denegado. Nombre no autorizado o PIN incorrecto.")

else:
    # --- 5. BARRA LATERAL ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.usuario}")
        st.info(f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n⏰ Entrada: {st.session_state.hora_entrada.strftime('%H:%M:%S')}")
        if st.button("🔴 CERRAR TURNO"):
            st.session_state.usuario = None
            st.rerun()

    # --- 6. INTERFAZ PRINCIPAL (Pestañas) ---
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 VENTAS"])

    df = pd.read_csv(INV_FILE)

    with tab1:
        st.header(f"Resumen del Día")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"$ {st.session_state.ventas_acumuladas}")
        c2.metric("Inicio de Turno", st.session_state.hora_entrada.strftime('%H:%M'))
        
        bajos = df[df['Stock'] < 5]
        c3.metric("Stock Crítico", f"{len(bajos)} ítems")
        
        if not bajos.empty:
            st.warning("⚠️ Productos por agotarse:")
            st.dataframe(bajos, use_container_width=True)

    with tab2:
        st.subheader("Control de Productos")
        with st.expander("➕ Añadir Producto"):
            n = st.text_input("Nombre")
            p = st.number_input("Precio", min_value=0.0)
            s = st.number_input("Stock", min_value=0)
            if st.button("Guardar"):
                nuevo = pd.DataFrame([[n, p, s]], columns=["Producto", "Precio", "Stock"])
                df = pd.concat([df, nuevo], ignore_index=True)
                df.to_csv(INV_FILE, index=False)
                st.success("Registrado")
                st.rerun()
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("Registrar Venta")
        if not df.empty:
            opcion = st.selectbox("Producto:", df['Producto'].tolist())
            if st.button("🛒 REGISTRAR VENTA"):
                idx = df[df['Producto'] == opcion].index[0]
                if df.at[idx, 'Stock'] > 0:
                    st.session_state.ventas_acumuladas += df.at[idx, 'Precio']
                    df.at[idx, 'Stock'] -= 1
                    df.to_csv(INV_FILE, index=False)
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Sin stock disponible.")
