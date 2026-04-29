import streamlit as st
import pandas as pd
import pyodbc
import json
import os

# Configuración de la página
st.set_page_config(page_title="Práctica SQL Server", layout="wide")

# 1. Cargar el JSON de ejercicios
def cargar_datos():
    with open('ejercicios.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 2. Función para conectar a SQL Server
def ejecutar_db(comando):
    try:
        # Cadena de conexión (Autenticación de Windows)
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=ClienteDB;"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(comando, conn)
        conn.close()
        return df
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- INTERFAZ ---
st.title("🚀 Sistema de Práctica SQL")

datos = cargar_datos()

# Sidebar para selección
with st.sidebar:
    st.header("Navegación")
    titulos = [f"{e['id']}. {e['titulo']}" for e in datos]
    seleccion = st.selectbox("Selecciona un ejercicio:", titulos)

# Obtener ejercicio actual
id_actual = int(seleccion.split(".")[0])
ejercicio = next(e for e in datos if e['id'] == id_actual)

# Layout principal
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Enunciado")
    st.info(f"**Nivel: {ejercicio['nivel']}**\n\n{ejercicio['enunciado']}")
    
    st.code(ejercicio['procedimiento'], language="sql")
    
    if st.button("Ejecutar Procedimiento ▶️"):
        with col2:
            st.subheader("📊 Resultado")
            resultado = ejecutar_db(ejercicio['procedimiento'])
            
            if isinstance(resultado, pd.DataFrame):
                st.success("Consulta ejecutada con éxito")
                st.dataframe(resultado, use_container_width=True)
            else:
                st.error(resultado)