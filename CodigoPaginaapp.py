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
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client

client = conectar()
db = client["videojuegos_terror"]

coleccion_juegos = db["juegos"]
coleccion_resenas = db["resenas"]

# -----------------------------
# UI
# -----------------------------
st.title("🎮 Sistema de Reseñas de Terror")

# 🔥 Estado de navegación
if "page" not in st.session_state:
    st.session_state.page = "inicio"

if "juego_seleccionado" not in st.session_state:
    st.session_state.juego_seleccionado = None

# 🔝 Header (reemplaza sidebar)
col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 Inicio"):
        st.session_state.page = "inicio"

with col2:
    if st.button("👤 Usuario / Perfil"):
        st.session_state.page = "perfil"

# -----------------------------
# INICIO (LISTA DE JUEGOS)
# -----------------------------
if st.session_state.page == "inicio":

    st.subheader("🎮 Catálogo")

    busqueda = st.text_input("🔍 Buscar juego")

    juegos = list(coleccion_juegos.find())

    for j in juegos:
        nombre = j.get("nombre")
        _id = str(j.get("_id"))

        if not nombre:
            continue

        if busqueda.lower() in nombre.lower():

            col1, col2 = st.columns([4,1])

            with col1:
                st.markdown(f"""
                <div class="card">
                    <div style="font-size:18px; font-weight:600;">🎮 {nombre}</div>
                    <div class="muted">Juego de terror</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("Reseñar", key=f"resena_{_id}"):
                    st.session_state.juego_seleccionado = nombre
                    st.session_state.page = "resena"

# -----------------------------
# AGREGAR RESEÑA
# -----------------------------
elif st.session_state.page == "resena":

    st.subheader("✍️ Nueva Reseña")

    usuario = st.text_input("Usuario")

    juegos_disponibles = [j.get("nombre") for j in coleccion_juegos.find() if j.get("nombre")]

    # 🔥 Si viene de botón, usar ese juego
    if st.session_state.juego_seleccionado:
        juego = st.selectbox(
            "Selecciona juego",
            juegos_disponibles,
            index=juegos_disponibles.index(st.session_state.juego_seleccionado)
        )
    else:
        juego = st.selectbox("Selecciona juego", juegos_disponibles)

    texto = st.text_area("Escribe tu reseña")
    rating = st.slider("⭐ Calificación", 1, 5, 3)

    if st.button("Guardar Reseña"):
        if usuario and texto and juego:

            existe = coleccion_resenas.find_one({
                "usuario": usuario,
                "juego": juego
            })

            if existe:
                st.warning("⚠️ Ya reseñaste este juego")
            else:
                coleccion_resenas.insert_one({
                    "usuario": usuario,
                    "juego": juego,
                    "texto": texto,
                    "rating": rating
                })
                st.success("✅ Reseña guardada")

        else:
            st.error("Completa todos los campos")

    if st.button("⬅ Volver"):
        st.session_state.page = "inicio"

# -----------------------------
# PERFIL
# -----------------------------
elif st.session_state.page == "perfil":

    st.subheader("👤 Perfil")

    usuario = st.text_input("Ingresa tu usuario")

    if usuario:

        st.write("### 📝 Tus reseñas")

        resenas = coleccion_resenas.find({"usuario": usuario})

        for r in resenas:
            st.markdown(f"""
            <div class="card">
                🎮 <b>{r.get("juego")}</b><br>
                ⭐ {r.get("rating", "N/A")}<br>
                {r.get("texto")}
            </div>
            """, unsafe_allow_html=True)

        st.write("### 🎯 Recomendaciones")

        resultados = recomendar(usuario)

        for nombre, score in resultados[:5]:
            st.write(f"🎮 {nombre} — {score}")
