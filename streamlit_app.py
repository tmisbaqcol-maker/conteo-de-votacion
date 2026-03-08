import streamlit as st
import pandas as pd
from supabase import create_client, Client
from typing import Optional

st.set_page_config(
    page_title="Control de Votación",
    page_icon="🗳️",
    layout="wide"
)

# =========================
# CONFIGURACIÓN SUPABASE
# =========================
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()
TABLE_NAME = "votacion"

# =========================
# FUNCIONES CRUD
# =========================
def cargar_datos() -> pd.DataFrame:
    response = (
        supabase.table(TABLE_NAME)
        .select("*")
        .order("id", desc=False)
        .execute()
    )
    data = response.data if response.data else []
    return pd.DataFrame(data)

def insertar_registro(lugar: str, mesa: str, votos_blanco: int, votos_nulo: int):
    payload = {
        "lugar_votacion": lugar,
        "mesa": mesa,
        "votos_blanco": votos_blanco,
        "votos_nulo": votos_nulo,
    }
    return supabase.table(TABLE_NAME).insert(payload).execute()

def actualizar_registro(registro_id: int, lugar: str, mesa: str, votos_blanco: int, votos_nulo: int):
    payload = {
        "lugar_votacion": lugar,
        "mesa": mesa,
        "votos_blanco": votos_blanco,
        "votos_nulo": votos_nulo,
    }
    return (
        supabase.table(TABLE_NAME)
        .update(payload)
        .eq("id", registro_id)
        .execute()
    )

def eliminar_registro(registro_id: int):
    return (
        supabase.table(TABLE_NAME)
        .delete()
        .eq("id", registro_id)
        .execute()
    )

# =========================
# INTERFAZ
# =========================
st.title("🗳️ Base de datos electoral online")
st.caption("Registro y edición de Lugar de votación, Mesa, Votos en blanco y Votos nulo")

tab1, tab2, tab3 = st.tabs(["📋 Ver registros", "➕ Agregar registro", "✏️ Editar / Eliminar"])

with tab1:
    st.subheader("Registros actuales")
    df = cargar_datos()

    if df.empty:
        st.info("No hay registros guardados todavía.")
    else:
        columnas_mostrar = ["id", "lugar_votacion", "mesa", "votos_blanco", "votos_nulo"]
        st.dataframe(df[columnas_mostrar], use_container_width=True)

        total_blanco = int(df["votos_blanco"].fillna(0).sum())
        total_nulo = int(df["votos_nulo"].fillna(0).sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Total registros", len(df))
        c2.metric("Total votos en blanco", total_blanco)
        c3.metric("Total votos nulo", total_nulo)

        csv = df[columnas_mostrar].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv,
            file_name="base_votacion.csv",
            mime="text/csv"
        )

with tab2:
    st.subheader("Agregar nuevo registro")

    with st.form("form_agregar", clear_on_submit=True):
        lugar = st.text_input("Lugar de votación")
        mesa = st.text_input("Mesa")
        votos_blanco = st.number_input("Votos en blanco", min_value=0, step=1, value=0)
        votos_nulo = st.number_input("Votos nulo", min_value=0, step=1, value=0)

        guardar = st.form_submit_button("Guardar registro")

        if guardar:
            if not lugar.strip():
                st.error("Debes escribir el lugar de votación.")
            elif not mesa.strip():
                st.error("Debes escribir la mesa.")
            else:
                try:
                    insertar_registro(
                        lugar=lugar.strip(),
                        mesa=mesa.strip(),
                        votos_blanco=int(votos_blanco),
                        votos_nulo=int(votos_nulo),
                    )
                    st.success("Registro guardado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

with tab3:
    st.subheader("Editar o eliminar registro")
    df = cargar_datos()

    if df.empty:
        st.warning("No hay registros para editar o eliminar.")
    else:
        opciones = {
            f'ID {row["id"]} | {row["lugar_votacion"]} | Mesa {row["mesa"]}': row["id"]
            for _, row in df.iterrows()
        }

        seleccion = st.selectbox("Selecciona un registro", list(opciones.keys()))
        registro_id = opciones[seleccion]

        fila = df[df["id"] == registro_id].iloc[0]

        with st.form("form_editar"):
            lugar_edit = st.text_input("Lugar de votación", value=str(fila["lugar_votacion"]))
            mesa_edit = st.text_input("Mesa", value=str(fila["mesa"]))
            votos_blanco_edit = st.number_input(
                "Votos en blanco",
                min_value=0,
                step=1,
                value=int(fila["votos_blanco"])
            )
            votos_nulo_edit = st.number_input(
                "Votos nulo",
                min_value=0,
                step=1,
                value=int(fila["votos_nulo"])
            )

            col1, col2 = st.columns(2)
            actualizar = col1.form_submit_button("Actualizar")
            borrar = col2.form_submit_button("Eliminar")

            if actualizar:
                try:
                    actualizar_registro(
                        registro_id=registro_id,
                        lugar=lugar_edit.strip(),
                        mesa=mesa_edit.strip(),
                        votos_blanco=int(votos_blanco_edit),
                        votos_nulo=int(votos_nulo_edit),
                    )
                    st.success("Registro actualizado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")

            if borrar:
                try:
                    eliminar_registro(registro_id)
                    st.success("Registro eliminado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

st.divider()
st.markdown("### Campos de la base")
st.write(
    {
        "lugar_votacion": "Texto",
        "mesa": "Texto",
        "votos_blanco": "Número entero",
        "votos_nulo": "Número entero",
    }
)
