import streamlit as st
import pandas as pd
import psycopg2

# Configuración de la página
st.set_page_config(layout="wide", page_title="SQL Practice - BAD")

# --- 1. DICCIONARIO DE CONSULTAS (Basado en el documento Northwind) ---
ejercicios = {
    "1. Clasificación de Clientes (CASE)": {
        "enunciado": "Clasifica a los clientes en categorías: 'Menor de edad', 'Joven Universitario' (18-25) o 'Adulto' según su edad.",
        "sql": "SELECT nombre, edad,\n    CASE \n        WHEN edad < 18 THEN 'Menor de edad'\n        WHEN edad BETWEEN 18 AND 25 THEN 'Joven Universitario'\n        ELSE 'Adulto'\n    END AS categoria_cliente\nFROM cliente;"
    },
    "2. Reporte de Registros (JOINs)": {
        "enunciado": "Muestra qué cliente registró cada programa y en qué comercio realizó la operación.",
        "sql": "SELECT c.nombre AS cliente, p.nombre AS programa, com.nombre AS comercio\nFROM registra r\nJOIN cliente c ON r.dni = c.dni\nJOIN programa p ON r.codigo = p.codigo\nJOIN comercio com ON r.cif = com.cif;"
    },
    "3. Comercios TOP (Subconsultas)": {
        "enunciado": "Lista los comercios que distribuyen una cantidad de software mayor al promedio global.",
        "sql": "SELECT nombre, ciudad \nFROM comercio \nWHERE cif IN (\n    SELECT cif \n    FROM distribuye \n    WHERE cantidad > (SELECT AVG(cantidad) FROM distribuye)\n);"
    },
    "4. Programas no Registrados (EXISTS)": {
        "enunciado": "Identifica los fabricantes cuyos programas aún no han sido registrados por ningún cliente.",
        "sql": "SELECT f.nombre, f.pais\nFROM fabricante f\nJOIN desarrolla d ON f.id_fab = d.id_fab\nWHERE NOT EXISTS (\n    SELECT 1 \n    FROM registra r \n    WHERE r.codigo = d.codigo\n);"
    },
    "5. Clientes Activos (Correlacionadas)": {
        "enunciado": "Muestra los clientes que tienen registros realizados y cuántos programas han registrado en total.",
        "sql": "SELECT c.nombre, \n       (SELECT COUNT(*) FROM registra r WHERE r.dni = c.dni) AS total_registros\nFROM cliente c\nWHERE (SELECT COUNT(*) FROM registra r WHERE r.dni = c.dni) > 0;"
    }
}

# --- 2. FUNCIÓN DE CONEXIÓN ---
def ejecutar_query(sql):
    try:
        # Ajusta estos datos con los que pusiste en la instalación
        conn = psycopg2.connect(
            host="localhost",
            database="ClienteDB", 
            user="postgres",
            password="root"
        )
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        return f"Error: {e}"

# --- 3. DISEÑO DE LA INTERFAZ (Tu esquema) ---
st.title("Sistema de Práctica SQL - Ingeniería 💻")

col_izq, col_der = st.columns([0.5, 0.5])

with col_izq:
    st.subheader("Panel de Ejercicios")
    
    # 1. PRIMERO creamos el selector para que la variable 'opcion' exista
    opcion = st.selectbox("Selecciona un nivel de consulta:", list(ejercicios.keys()))
    
    # 2. SEGUNDO mostramos el enunciado
    st.info(f"**Enunciado:** {ejercicios[opcion]['enunciado']}")
    
    # 3. TERCERO manejamos el estado de la consulta
    # Si cambiamos de ejercicio, actualizamos el editor
    if 'ultima_opcion' not in st.session_state:
        st.session_state.ultima_opcion = opcion
        st.session_state.query_actual = ejercicios[opcion]['sql']

    if st.session_state.ultima_opcion != opcion:
        st.session_state.ultima_opcion = opcion
        st.session_state.query_actual = ejercicios[opcion]['sql']

    # 4. CUARTO el área de texto usa el valor del estado
    query_usuario = st.text_area(
        "Editor SQL:", 
        value=st.session_state.query_actual, 
        height=250
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Restablecer consulta 🔄", use_container_width=True):
            st.session_state.query_actual = ejercicios[opcion]['sql']
            st.rerun()
            
    with col_btn2:
        ejecutar = st.button("Ejecutar Consulta ▶️", type="primary", use_container_width=True)

with col_der:
    st.subheader("Resultado de la Base de Datos")
    
    if ejecutar:
        with st.spinner("Consultando PostgreSQL..."):
            resultado = ejecutar_query(query_usuario)
            
            if isinstance(resultado, pd.DataFrame):
                st.success(f"Se encontraron {len(resultado)} registros.")
                st.dataframe(resultado, use_container_width=True)
            else:
                st.error(resultado)
    else:
        st.write("Presiona 'Ejecutar' para ver los datos aquí.")