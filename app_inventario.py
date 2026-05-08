import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Kiosco Inteligente PRO",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CONEXIÓN A LA NUBE (GOOGLE SHEETS) ---
# 🚨 PEGA TU LINK AQUÍ:
URL_HOJA = "https://docs.google.com/spreadsheets/d/108HEgQ1pkzxjxwYEU2YqhvkWGdkar7rvEPTVyI2CUAE/edit?gid=0#gid=0"

def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        data = conn.read(spreadsheet=URL_HOJA)
        return data.dropna(how="all")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(columns=["Producto", "Precio", "Stock"])

# --- 3. LÓGICA DE SESIÓN Y SEGURIDAD ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.entrada = None
    st.session_state.ventas_acumuladas = 0.0

# Pantalla de Login
if st.session_state.usuario is None:
    st.title(" Acceso al Sistema de Gestión")
    autorizados = ["estefany", "milagros", "milagro", "gabriela", "mario"]
    
    with st.form("login_form"):
        u = st.text_input("Usuario / Operador:").strip().lower()
        p = st.text_input("PIN de Seguridad:", type="password")
        if st.form_submit_button("INGRESAR"):
            if u in autorizados and p == "2984":
                st.session_state.usuario = u.capitalize()
                st.session_state.entrada = datetime.now()
                st.success(f"Bienvenida {st.session_state.usuario}")
                st.rerun()
            else:
                st.error(" Usuario o PIN incorrectos")
else:
    # --- 4. BARRA LATERAL ---
    with st.sidebar:
        st.header(f" {st.session_state.usuario}")
        st.info(f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n⏰ Entrada: {st.session_state.entrada.strftime('%H:%M:%S')}")
        
        if st.button(" CERRAR TURNO Y GENERAR REPORTE"):
            duracion = datetime.now() - st.session_state.entrada
            st.warning(f"Resumen: Vendiste ${st.session_state.ventas_acumuladas} en {str(duracion).split('.')[0]}")
            st.session_state.usuario = None
            st.rerun()

    # Cargar datos desde la nube
    df = cargar_datos()
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- 5. CUERPO PRINCIPAL (PESTAÑAS) ---
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📦 INVENTARIO", "💰 REGISTRAR VENTA"])

    # PESTAÑA 1: MÉTRICAS Y ALERTAS
    with tab1:
        st.title("Estado General del Negocio")
        c1, c2, c3 = st.columns(3)
        
        c1.metric("Ventas del Turno", f"$ {st.session_state.ventas_acumuladas}")
        
        stock_total = df['Stock'].astype(int).sum() if not df.empty else 0
        c2.metric("Total de Productos", stock_total)
        
        bajos = df[df['Stock'].astype(int) < 5] if not df.empty else pd.DataFrame()
        c3.metric("Alertas de Stock", len(bajos), delta_color="inverse")

        if not bajos.empty:
            st.subheader("⚠️ Productos con Stock Crítico")
            st.dataframe(bajos, use_container_width=True)

    # PESTAÑA 2: INVENTARIO CON BUSCADOR
    with tab2:
        st.subheader("Gestión de Mercancía")
        
        # Buscador inteligente
        busqueda = st.text_input("🔍 Buscar por nombre de producto...")
        
        if busqueda:
            df_mostrar = df[df['Producto'].str.contains(busqueda, case=False, na=False)]
        else:
            df_mostrar = df

        with st.expander("➕ Añadir Nuevo Producto"):
            col_n, col_p, col_s = st.columns(3)
            nuevo_n = col_n.text_input("Nombre")
            nuevo_p = col_p.number_input("Precio ($)", min_value=0.0, step=0.5)
            nuevo_s = col_s.number_input("Stock Inicial", min_value=0, step=1)
            
            if st.button("Guardar en Nube"):
                if nuevo_n:
                    nuevo_prod = pd.DataFrame([[nuevo_n, nuevo_p, nuevo_s]], columns=["Producto", "Precio", "Stock"])
                    df_final = pd.concat([df, nuevo_prod], ignore_index=True)
                    conn.update(spreadsheet=URL_HOJA, data=df_final)
                    st.success("✅ Guardado en Google Sheets")
                    st.rerun()

        st.dataframe(df_mostrar, use_container_width=True)

    # PESTAÑA 3: VENTAS Y ACTUALIZACIÓN
    with tab3:
        st.subheader("Registrar Venta Rápida")
        if not df.empty:
            lista_productos = df['Producto'].tolist()
            prod_vender = st.selectbox("Seleccione el producto vendido:", lista_productos)
            
            if st.button(" CONFIRMAR VENTA"):
                idx = df[df['Producto'] == prod_vender].index[0]
                if int(df.at[idx, 'Stock']) > 0:
                    # Actualizar memoria de ventas
                    st.session_state.ventas_acumuladas += float(df.at[idx, 'Precio'])
                    # Restar del DataFrame
                    df.at[idx, 'Stock'] = int(df.at[idx, 'Stock']) - 1
                    # Sincronizar con Google Sheets
                    conn.update(spreadsheet=URL_HOJA, data=df)
                    st.balloons()
                    st.success(f"Venta de {prod_vender} registrada con éxito")
                    st.rerun()
                else:
                    st.error(" No hay suficiente stock para vender este producto.")
        else:
            st.info("No hay productos registrados. Agrégalos en la pestaña de Inventario.")
