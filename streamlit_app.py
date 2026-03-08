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
st.caption("Editable desde Streamlit Cloud, sin SQL, con votos por agrupación")

# =========================
# CONFIGURACIÓN DE COLUMNAS
# =========================
AGRUPACIONES = [
    "Pacto Historico",
    "Partido Liberal",
    "Partido Conservador",
    "Partido de la U",
    "Cambio Radical",
    "Centro Democratico",
    "Comunes",
    "MIRA",
    "ASI",
    "AICO",
]

COLUMNAS_BASE = [
    "Lugar de votación",
    "Mesa",
    "Votos en blanco",
    "Votos nulo"
]

COLUMNAS = COLUMNAS_BASE + AGRUPACIONES

# =========================
# FUNCIONES
# =========================
def dataframe_inicial() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS)

def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for col in COLUMNAS:
        if col not in df.columns:
            if col in ["Lugar de votación", "Mesa"]:
                df[col] = ""
            else:
                df[col] = 0

    df = df[COLUMNAS].copy()

    columnas_numericas = [col for col in COLUMNAS if col not in ["Lugar de votación", "Mesa"]]
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["Lugar de votación"] = df["Lugar de votación"].fillna("").astype(str)
    df["Mesa"] = df["Mesa"].fillna("").astype(str)

    return df

# =========================
# ESTADO DE SESIÓN
# =========================
if "df" not in st.session_state:
    st.session_state.df = dataframe_inicial()

# =========================
# SIDEBAR
# =========================
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

            st.session_state.df = normalizar_dataframe(df_cargado)
            st.success("Base cargada correctamente.")
        except Exception as e:
            st.error(f"Error al cargar archivo: {e}")

    if st.button("Nueva base vacía"):
        st.session_state.df = dataframe_inicial()
        st.success("Se creó una base vacía.")

    if st.button("Limpiar todo"):
        st.session_state.df = dataframe_inicial()
        st.warning("Se eliminaron los datos actuales.")

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(
    ["📋 Base editable", "➕ Agregar registro", "⬇️ Descargar"]
)

# =========================
# TAB 1: EDITAR
# =========================
with tab1:
    st.subheader("Editar datos en línea")

    column_config = {
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

    for agrupacion in AGRUPACIONES:
        column_config[agrupacion] = st.column_config.NumberColumn(
            agrupacion,
            min_value=0,
            step=1,
            format="%d"
        )

    df_editado = st.data_editor(
        normalizar_dataframe(st.session_state.df),
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

    df_editado = normalizar_dataframe(df_editado)
    st.session_state.df = df_editado.copy()

    total_registros = len(st.session_state.df)
    total_blanco = int(st.session_state.df["Votos en blanco"].sum()) if total_registros else 0
    total_nulo = int(st.session_state.df["Votos nulo"].sum()) if total_registros else 0

    columnas_agrupaciones = AGRUPACIONES
    total_agrupaciones = int(st.session_state.df[columnas_agrupaciones].sum().sum()) if total_registros else 0
    total_general = total_blanco + total_nulo + total_agrupaciones

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total registros", total_registros)
    c2.metric("Votos en blanco", total_blanco)
    c3.metric("Votos nulo", total_nulo)
    c4.metric("Total votos agrupaciones", total_agrupaciones)

    st.markdown("### Totales por agrupación")
    resumen = pd.DataFrame({
        "Agrupación": AGRUPACIONES,
        "Total votos": [int(st.session_state.df[col].sum()) for col in AGRUPACIONES]
    })
    st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.metric("Total general registrado", total_general)

# =========================
# TAB 2: AGREGAR REGISTRO
# =========================
with tab2:
    st.subheader("Agregar registro manualmente")

    with st.form("form_agregar", clear_on_submit=True):
        lugar = st.text_input("Lugar de votación")
        mesa = st.text_input("Mesa")
        votos_blanco = st.number_input("Votos en blanco", min_value=0, step=1, value=0)
        votos_nulo = st.number_input("Votos nulo", min_value=0, step=1, value=0)

        st.markdown("### Votos por agrupación")

        valores_agrupaciones = {}
        col1, col2 = st.columns(2)

        for i, agrupacion in enumerate(AGRUPACIONES):
            with col1 if i % 2 == 0 else col2:
                valores_agrupaciones[agrupacion] = st.number_input(
                    agrupacion,
                    min_value=0,
                    step=1,
                    value=0,
                    key=f"agr_{agrupacion}"
                )

        guardar = st.form_submit_button("Guardar registro")

        if guardar:
            if not lugar.strip():
                st.error("Debes ingresar el lugar de votación.")
            elif not mesa.strip():
                st.error("Debes ingresar la mesa.")
            else:
                nuevo_registro = {
                    "Lugar de votación": lugar.strip(),
                    "Mesa": mesa.strip(),
                    "Votos en blanco": int(votos_blanco),
                    "Votos nulo": int(votos_nulo),
                }

                for agrupacion in AGRUPACIONES:
                    nuevo_registro[agrupacion] = int(valores_agrupaciones[agrupacion])

                nuevo = pd.DataFrame([nuevo_registro])

                st.session_state.df = pd.concat(
                    [normalizar_dataframe(st.session_state.df), nuevo],
                    ignore_index=True
                )
                st.success("Registro agregado correctamente.")
                st.rerun()

# =========================
# TAB 3: DESCARGAR
# =========================
with tab3:
    st.subheader("Descargar base de datos")

    df_descarga = normalizar_dataframe(st.session_state.df)

    csv_data = df_descarga.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV",
        data=csv_data,
        file_name="base_votacion.csv",
        mime="text/csv"
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_descarga.to_excel(writer, index=False, sheet_name="Base")

        resumen = pd.DataFrame({
            "Agrupación": AGRUPACIONES,
            "Total votos": [int(df_descarga[col].sum()) for col in AGRUPACIONES]
        })
        resumen.to_excel(writer, index=False, sheet_name="Resumen")

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
