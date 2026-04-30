import streamlit as st
import pandas as pd
import pyodbc
import json

# Configuración de la página
st.set_page_config(page_title="Práctica SQL Server - Valeria Trujillo", layout="wide")

# 1. Cargar el JSON de ejercicios
def cargar_datos():
    try:
        with open('ejercicios.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo 'ejercicios.json'. Asegúrate de que esté en la misma carpeta.")
        return []

# 2. Función para conectar a SQL Server de forma dinámica
def ejecutar_db(comando, nombre_base):
    try:
        # Cadena de conexión dinámica
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            f"DATABASE={nombre_base};"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        # Ejecutar y cargar en un DataFrame
        df = pd.read_sql(comando, conn)
        conn.close()
        return df
    except Exception as e:
        return f"❌ Error en la base de datos: {str(e)}"

# --- INTERFAZ ---
st.title("🚀 Sistema de Práctica SQL")
st.markdown("---")

datos = cargar_datos()

if not datos:
    st.stop()

# Sidebar para selección
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Obtener bases únicas del JSON
    bases_disponibles = sorted(list(set(e['base'] for e in datos)))
    base_seleccionada = st.selectbox("1. Selecciona la Base de Datos:", bases_disponibles)
    
    st.divider()
    
    # Filtrar ejercicios por la base seleccionada
    ejercicios_filtrados = [e for e in datos if e['base'] == base_seleccionada]
    
    st.header("📖 Navegación")
    if ejercicios_filtrados:
        titulos = [f"{e['id']}. {e['titulo']}" for e in ejercicios_filtrados]
        seleccion = st.selectbox("2. Selecciona un ejercicio:", titulos)
        
        # Obtener ejercicio actual
        id_actual = int(seleccion.split(".")[0])
        ejercicio = next(e for e in ejercicios_filtrados if e['id'] == id_actual)
    else:
        st.warning("No hay ejercicios para esta base.")
        st.stop()

# Layout principal
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Enunciado")
    st.info(f"{ejercicio['enunciado']}")
    
    # Editor de código con KEY dinámica para refrescarse al cambiar de ejercicio
    codigo_editado = st.text_area(
        "Edita tu consulta SQL aquí:", 
        value=ejercicio['procedimiento'], 
        height=250,
        key=f"editor_{ejercicio['id']}"
    )
    
    st.caption("💡 Sugerencia: Puedes modificar el script o escribir un SELECT directamente.")
    
    if st.button("Ejecutar Consulta ▶️", use_container_width=True):
        with col2:
            st.subheader("📊 Resultado")
            # Mostrar un spinner mientras carga
            with st.spinner("Consultando SQL Server..."):
                resultado = ejecutar_db(codigo_editado, base_seleccionada)
            
            if isinstance(resultado, pd.DataFrame):
                st.success(f"Ejecutado con éxito en: {base_seleccionada}")
                st.dataframe(resultado, use_container_width=True)
            else:
                # Mostrar el error detallado que devuelve SQL Server
                st.error(resultado)