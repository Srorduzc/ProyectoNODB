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
# UI CONFIG
# -----------------------------
st.set_page_config(page_title="🎮 Juegos de Terror", layout="centered")

# 🎨 ESTILO CLARO (AQUÍ VA)
st.markdown("""
<style>

/* Fondo */
.stApp {
    background-color: #f5f7fb;
    color: #1f2937;
}

/* Títulos */
h1, h2, h3 {
    color: #111827;
}

/* Cards */
.card {
    background-color: white;
    padding: 16px;
    border-radius: 12px;
    margin: 10px 0;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    transition: 0.2s;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
}

/* Botones */
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 14px;
}

.stButton>button:hover {
    background-color: #1d4ed8;
}

/* Inputs */
input, textarea {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 6px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* Texto secundario */
.muted {
    color: #6b7280;
}

</style>
""", unsafe_allow_html=True)

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
st.title("🎮 Sistema de Reseñas de Terror")

menu = st.sidebar.selectbox("Menú", [
    "Lista de Juegos",
    "Agregar Reseña",
    "Perfil"
])

# -----------------------------
# LISTA DE JUEGOS
# -----------------------------
if menu == "Lista de Juegos":

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
                    st.session_state.juego = nombre
                    st.session_state.menu = "Agregar Reseña"

# -----------------------------
# AGREGAR RESEÑA
# -----------------------------
elif menu == "Agregar Reseña":

    st.subheader("✍️ Nueva Reseña")

    usuario = st.text_input("Usuario")

    juegos_disponibles = [j.get("nombre") for j in coleccion_juegos.find() if j.get("nombre")]

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

# -----------------------------
# PERFIL
# -----------------------------
elif menu == "Perfil":

    usuario = st.text_input("Usuario")

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
