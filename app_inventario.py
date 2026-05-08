import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Kiosco: Mis princesas", page_icon="👑", layout="centered")

# Estilo Personalizado (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #ff4bad; }
    
    /* Estilo para el botón */
    div.stButton > button:first-child {
        background-color: #ff4bad; color: white; border-radius: 8px; width: 100%; border: none; font-weight: bold; height: 3em;
    }
    
    /* Estilo para el título principal */
    .titulo-principal { text-align: center; font-size: 45px; font-weight: bold; color: #ff4bad; margin-bottom: 5px; }
    .subtitulo { text-align: center; font-size: 20px; color: #f0f2f6; margin-bottom: 30px; letter-spacing: 2px; }
    
    /* Eliminar bordes innecesarios */
    .stForm { border: 1px solid #3e4255 !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Manejo de base de datos
DB_FILE = "datos_kiosco.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Verificación de columnas por si acaso cambiaste el nombre del archivo
        columnas_necesarias = ["Artículo", "Precio (Pesos)", "Cantidad", "Fecha de Ingreso"]
        for col in columnas_necesarias:
            if col not in df.columns:
                df[col] = 0 if col != "Artículo" else "Producto"
        return df
    return pd.DataFrame(columns=["Artículo", "Precio (Pesos)", "Cantidad", "Fecha de Ingreso"])

df = cargar_datos()

# 3. Encabezado Personalizado
st.markdown('<div class="titulo-principal">Kiosco: Mis princesas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">SISTEMA DE INVENTARIO</div>', unsafe_allow_html=True)

# Resumen de métricas
if not df.empty:
    m1, m2 = st.columns(2)
    total_unidades = int(df["Cantidad"].sum())
    valor_total = (df["Precio (Pesos)"] * df["Cantidad"]).sum()
    m1.metric("Unidades en Stock", total_unidades)
    m2.metric("Valor del Inventario", f"${valor_total:,.0f} Pesos")

st.divider()

# 4. Formulario de Registro
st.subheader("Registro de Nueva Mercancía")
with st.form("registro_form", clear_on_submit=True):
    col_nom = st.text_input("Nombre del Producto", placeholder="Ej: Caramelos, Refrescos...")
    c1, c2 = st.columns(2)
    precio = c1.number_input("Precio (Pesos)", min_value=0.0, step=50.0, format="%f")
    cantidad = c2.number_input("Cantidad", min_value=1, step=1)
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    
    submit = st.form_submit_button("Guardar en Inventario")

if submit:
    if col_nom:
        # Lógica para sumar si ya existe o agregar nuevo
        if col_nom in df["Artículo"].values:
            df.loc[df["Artículo"] == col_nom, "Cantidad"] += cantidad
            df.loc[df["Artículo"] == col_nom, "Precio (Pesos)"] = precio
            df.loc[df["Artículo"] == col_nom, "Fecha de Ingreso"] = fecha_actual
        else:
            nueva_fila = pd.DataFrame([[col_nom, precio, cantidad, fecha_actual]], columns=df.columns)
            df = pd.concat([df, nueva_fila], ignore_index=True)
        
        df.to_csv(DB_FILE, index=False)
        st.success(f"¡{col_nom} guardado exitosamente!")
        st.rerun()
    else:
        st.error("Debes ingresar el nombre del producto.")

st.divider()

# 5. Visualización de Datos
if not df.empty:
    st.subheader("Inventario Detallado")
    # Configuración de la tabla para que se vea profesional
    st.dataframe(
        df.sort_values(by="Fecha de Ingreso", ascending=False), 
        use_container_width=True, 
        hide_index=True
    )
    
    # Opción para quitar productos
    with st.expander("Modificar / Eliminar"):
        prod_sel = st.selectbox("Selecciona un artículo", df["Artículo"].unique())
        col_btn1, col_btn2 = st.columns(2)
        
        if col_btn1.button("Vender / Quitar 1 unidad"):
            idx = df[df["Artículo"] == prod_sel].index[0]
            if df.at[idx, "Cantidad"] > 0:
                df.at[idx, "Cantidad"] -= 1
                df.to_csv(DB_FILE, index=False)
                st.rerun()
        
        if col_btn2.button("Eliminar Producto Totalmente"):
            df = df[df["Artículo"] != prod_sel]
            df.to_csv(DB_FILE, index=False)
            st.warning(f"Eliminado: {prod_sel}")
            st.rerun()
else:
    st.info("El inventario está vacío actualmente.")