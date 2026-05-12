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
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            f"DATABASE={nombre_base};"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(comando)
        conn.commit()

        if cursor.description:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame.from_records(rows, columns=columns)
        else:
            df = pd.DataFrame()

        cursor.close()
        conn.close()
        return df
    except Exception as e:
        return f"❌ Error en la base de datos: {str(e)}"

# Mostrar los resultados de un SELECT o procedimiento almacenado
def mostrar_dataframe_resultado(df):
    if not isinstance(df, pd.DataFrame):
        st.error("❌ Resultado inesperado de la base de datos.")
        return
    if df.empty:
        st.info("La consulta no devolvió filas.")
        return

    mensaje_col = next((c for c in df.columns if str(c).strip().lower() == "mensaje"), None)
    if mensaje_col is not None and len(df) == 1:
        st.success(str(df.iloc[0][mensaje_col]))
        return

    if df.shape == (1, 1):
        st.success(str(df.iat[0, 0]))
        return

    st.dataframe(df, use_container_width=True)

# --- NUEVA FUNCIÓN PARA OBTENER EL CÓDIGO DEL SP ---
def obtener_definicion_sp(nombre_sp, nombre_base):
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            f"DATABASE={nombre_base};"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        nombre_limpio = nombre_sp.replace("EXEC", "").replace("exec", "").strip()
        query = f"SELECT OBJECT_DEFINITION(OBJECT_ID('{nombre_limpio}'))"
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado and resultado[0]:
            return resultado[0]
        return f"-- No se encontró definición para: {nombre_limpio}"
    except Exception as e:
        return f"-- Error al extraer código: {str(e)}"

# --- INTERFAZ ---
st.title("🚀 Sistema de Práctica SQL")
st.markdown("---")

datos = cargar_datos()

if not datos:
    st.stop()

# Sidebar para selección
with st.sidebar:
    st.header("⚙️ Configuración")
    
    bases_disponibles = sorted(list(set(e['base'] for e in datos)))
    base_seleccionada = st.selectbox("1. Selecciona la Base de Datos:", bases_disponibles)
    
    st.divider()
    
    ejercicios_filtrados = [e for e in datos if e['base'] == base_seleccionada]
    
    st.header("📖 Navegación")
    if ejercicios_filtrados:
        titulos = [f"{e['id']}. {e['titulo']}" for e in ejercicios_filtrados]
        seleccion = st.selectbox("2. Selecciona un ejercicio:", titulos)
        
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

    # --- LÓGICA PARA CARGAR EL CÓDIGO COMPLETO ---
    # Usamos session_state para mantener el código cargado
    key_editor = f"editor_{ejercicio['id']}"
    
    if st.button("🔍 Ver Código Fuente del Procedimiento"):
        codigo_fuente = obtener_definicion_sp(ejercicio['procedimiento'], base_seleccionada)
        st.session_state[key_editor] = codigo_fuente

    # Editor de código
    codigo_editado = st.text_area(
        "Edita tu consulta SQL aquí:", 
        value=st.session_state.get(key_editor, ejercicio['procedimiento']), 
        height=300,
        key=key_editor
    )
    
    st.caption("💡 Puedes editar el código del SP y presionar ejecutar para aplicar los cambios (ALTER) o probarlo.")
    
    if st.button("Ejecutar Consulta ▶️", use_container_width=True):
        with col2:
            st.subheader("📊 Resultado")
            with st.spinner("Consultando SQL Server..."):
                import re
                
                # 1. Limpieza y preparación: cambiamos CREATE por ALTER si es necesario
                if "CREATE PROCEDURE" in codigo_editado.upper():
                    codigo_final = re.sub(r'CREATE\s+PROCEDURE', 'ALTER PROCEDURE', codigo_editado, flags=re.IGNORECASE)
                else:
                    codigo_final = codigo_editado

                # 2. Lógica de ejecución
                if any(word in codigo_final.upper() for word in ["ALTER PROCEDURE", "CREATE PROCEDURE"]):
                    try:
                        conn_str = (
                            "DRIVER={ODBC Driver 17 for SQL Server};"
                            "SERVER=localhost\\SQLEXPRESS;"
                            f"DATABASE={base_seleccionada};"
                            "Trusted_Connection=yes;"
                        )
                        conn = pyodbc.connect(conn_str)
                        conn.autocommit = True
                        cursor = conn.cursor()
                        # Ejecutamos la actualización (ALTER)
                        cursor.execute(codigo_final)
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("✅ Estructura actualizada correctamente.")

                        # --- AQUÍ ESTÁ EL TRUCO PARA MOSTRAR LA TABLA ---
                        # Intentamos extraer el nombre del SP para ejecutarlo automáticamente
                        match = re.search(r'PROCEDURE\s+([\w\.]+)', codigo_final, re.IGNORECASE)
                        if match:
                            nombre_sp = match.group(1)
                            st.info(f"Ejecutando {nombre_sp} para obtener datos...")
                            try:
                                df_resultado = ejecutar_db(f"EXEC {nombre_sp}", base_seleccionada)
                                if isinstance(df_resultado, pd.DataFrame):
                                    mostrar_dataframe_resultado(df_resultado)
                                else:
                                    st.warning(df_resultado)
                            except Exception as e_read:
                                st.warning(f"No se pudo ejecutar el procedimiento: {str(e_read)}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    # Si es un EXEC o SELECT simple, se ejecuta como siempre
                    resultado = ejecutar_db(codigo_final, base_seleccionada)
                    if isinstance(resultado, pd.DataFrame):
                            mostrar_dataframe_resultado(resultado)
