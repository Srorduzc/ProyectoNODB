import streamlit as st
from pymongo import MongoClient
import os

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
try:
    URI = st.secrets["MONGO_URI"]
except:
    URI = os.getenv("MONGO_URI")

if not URI:
    st.error("❌ No se encontró MONGO_URI")
    st.stop()

# -----------------------------
# CONEXIÓN
# -----------------------------
@st.cache_resource
def conectar():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        st.stop()

client = conectar()
db = client["videojuegos_terror"]

coleccion_juegos = db["juegos"]
coleccion_resenas = db["resenas"]

# -----------------------------
# ESTADO
# -----------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

if "juego_seleccionado" not in st.session_state:
    st.session_state.juego_seleccionado = None

# -----------------------------
# FUNCIONES
# -----------------------------
def extraer_keywords(texto):
    palabras = ["miedo", "historia", "oscuridad", "monstruos", "tension"]
    score = {}

    texto = texto.lower()

    for p in palabras:
        if p in texto:
            score[p] = score.get(p, 0) + 1

    return score


def perfil_usuario(usuario):
    perfil = {}
    resenas = coleccion_resenas.find({"usuario": usuario})

    for r in resenas:
        keywords = extraer_keywords(r.get("texto", ""))
        for k, v in keywords.items():
            perfil[k] = perfil.get(k, 0) + v

    return perfil


def recomendar(usuario):
    perfil = perfil_usuario(usuario)
    juegos = coleccion_juegos.find()

    resultados = []

    for juego in juegos:
        puntaje = 0
        for tag in juego.get("tags", []):
            if tag in perfil:
                puntaje += perfil[tag]

        resultados.append((juego.get("nombre", "Sin nombre"), puntaje))

    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="🎮 Juegos de Terror", layout="centered")

st.title("🎮 Sistema de Reseñas de Terror")

# -----------------------------
# MENÚ SUPERIOR
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🎮 Juegos"):
        st.session_state.pagina = "inicio"

with col2:
    if st.button("👤 Perfil"):
        st.session_state.pagina = "perfil"

# -----------------------------
# PÁGINA: LISTA DE JUEGOS
# -----------------------------
if st.session_state.pagina == "inicio":

    st.subheader("🎮 Lista de Juegos")

    busqueda = st.text_input("Buscar juego")

    juegos = list(coleccion_juegos.find())

    for j in juegos:
        nombre = j.get("nombre", "")

        if busqueda.lower() in nombre.lower():

            col1, col2 = st.columns([3,1])

            with col1:
                st.write(f"🎮 {nombre}")

            with col2:
                if st.button("Reseñar", key=nombre):
                    st.session_state.juego_seleccionado = nombre
                    st.session_state.pagina = "resena"

# -----------------------------
# PÁGINA: RESEÑA
# -----------------------------
elif st.session_state.pagina == "resena":

    st.subheader("✍️ Nueva Reseña")

    juego = st.session_state.juego_seleccionado

    if not juego:
        st.warning("No hay juego seleccionado")
        st.session_state.pagina = "inicio"
        st.stop()

    st.write(f"Juego: **{juego}**")

    usuario = st.text_input("Usuario")
    texto = st.text_area("Escribe tu reseña")

    if st.button("Guardar Reseña"):
        if usuario and texto:
            try:
                coleccion_resenas.insert_one({
                    "usuario": usuario,
                    "juego": juego,
                    "texto": texto
                })
                st.success("✅ Reseña guardada")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.error("Completa los campos")

    if st.button("⬅️ Volver"):
        st.session_state.pagina = "inicio"

# -----------------------------
# PÁGINA: PERFIL
# -----------------------------
elif st.session_state.pagina == "perfil":

    st.subheader("👤 Perfil")

    usuario = st.text_input("Ingresa tu usuario")

    if usuario:

        resenas = list(coleccion_resenas.find({"usuario": usuario}))

        st.write("### 📝 Tus reseñas")

        if resenas:
            for r in resenas:
                st.write(f"🎮 {r.get('juego')} → {r.get('texto')}")
        else:
            st.warning("No tienes reseñas")

        st.write("### 🎯 Recomendaciones")

        resultados = recomendar(usuario)

        if resultados:
            for nombre, score in resultados[:5]:
                st.write(f"🎮 {nombre} — {score}")
        else:
            st.warning("Sin recomendaciones")
