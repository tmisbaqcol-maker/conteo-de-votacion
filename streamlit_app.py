# streamlit_app.py

import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Base de datos electoral online",
    page_icon="🗳️",
    layout="wide"
)

st.title("🗳️ Base de datos electoral online")
st.caption("Editable desde Streamlit Cloud, sin SQL")

COLUMNAS = ["Lugar de votación", "Mesa", "Votos en blanco", "Votos nulo"]

def dataframe_inicial() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS)

if "df" not in st.session_state:
    st.session_state.df = dataframe_inicial()

with st.sidebar:
    st.header("Opciones")

    archivo = st.file_uploader(
        "Cargar base en CSV o Excel",
        type=["csv", "xlsx"]
    )

    if archivo is not None:
        try:
            if archivo.name.endswith(".csv"):
                df_cargado = pd.read_csv(archivo)
            else:
                df_cargado = pd.read_excel(archivo)

            for col in COLUMNAS:
                if col not in df_cargado.columns:
                    df_cargado[col] = ""

            df_cargado = df_cargado[COLUMNAS].copy()
            df_cargado["Votos en blanco"] = pd.to_numeric(
                df_cargado["Votos en blanco"], errors="coerce"
            ).fillna(0).astype(int)
            df_cargado["Votos nulo"] = pd.to_numeric(
                df_cargado["Votos nulo"], errors="coerce"
            ).fillna(0).astype(int)

            st.session_state.df = df_cargado
            st.success("Base cargada correctamente.")
        except Exception as e:
            st.error(f"Error al cargar archivo: {e}")

    if st.button("Nueva base vacía"):
        st.session_state.df = dataframe_inicial()
        st.success("Se creó una base vacía.")

    if st.button("Limpiar todo"):
        st.session_state.df = dataframe_inicial()
        st.warning("Se eliminaron los datos actuales.")

tab1, tab2, tab3 = st.tabs(
    ["📋 Base editable", "➕ Agregar registro", "⬇️ Descargar"]
)

with tab1:
    st.subheader("Editar datos en línea")

    df_editado = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Lugar de votación": st.column_config.TextColumn(
                "Lugar de votación",
                required=True
            ),
            "Mesa": st.column_config.TextColumn(
                "Mesa",
                required=True
            ),
            "Votos en blanco": st.column_config.NumberColumn(
                "Votos en blanco",
                min_value=0,
                step=1,
                format="%d"
            ),
            "Votos nulo": st.column_config.NumberColumn(
                "Votos nulo",
                min_value=0,
                step=1,
                format="%d"
            ),
        }
    )

    df_editado["Votos en blanco"] = pd.to_numeric(
        df_editado["Votos en blanco"], errors="coerce"
    ).fillna(0).astype(int)
    df_editado["Votos nulo"] = pd.to_numeric(
        df_editado["Votos nulo"], errors="coerce"
    ).fillna(0).astype(int)

    st.session_state.df = df_editado.copy()

    total_registros = len(st.session_state.df)
    total_blanco = int(st.session_state.df["Votos en blanco"].sum()) if total_registros else 0
    total_nulo = int(st.session_state.df["Votos nulo"].sum()) if total_registros else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total registros", total_registros)
    c2.metric("Total votos en blanco", total_blanco)
    c3.metric("Total votos nulo", total_nulo)

with tab2:
    st.subheader("Agregar registro manualmente")

    with st.form("form_agregar", clear_on_submit=True):
        lugar = st.text_input("Lugar de votación")
        mesa = st.text_input("Mesa")
        votos_blanco = st.number_input("Votos en blanco", min_value=0, step=1, value=0)
        votos_nulo = st.number_input("Votos nulo", min_value=0, step=1, value=0)

        guardar = st.form_submit_button("Guardar registro")

        if guardar:
            if not lugar.strip():
                st.error("Debes ingresar el lugar de votación.")
            elif not mesa.strip():
                st.error("Debes ingresar la mesa.")
            else:
                nuevo = pd.DataFrame([{
                    "Lugar de votación": lugar.strip(),
                    "Mesa": mesa.strip(),
                    "Votos en blanco": int(votos_blanco),
                    "Votos nulo": int(votos_nulo),
                }])

                st.session_state.df = pd.concat(
                    [st.session_state.df, nuevo],
                    ignore_index=True
                )
                st.success("Registro agregado correctamente.")

with tab3:
    st.subheader("Descargar base de datos")

    csv_data = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV",
        data=csv_data,
        file_name="base_votacion.csv",
        mime="text/csv"
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.df.to_excel(writer, index=False, sheet_name="Base")
    excel_data = buffer.getvalue()

    st.download_button(
        label="Descargar Excel",
        data=excel_data,
        file_name="base_votacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.info(
    "Esta versión funciona solo dentro de la sesión activa de Streamlit Cloud. "
    "Para conservar cambios de forma permanente sin base de datos, debes cargar un archivo y volver a descargarlo."
)
