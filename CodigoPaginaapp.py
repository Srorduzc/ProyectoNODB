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
# ESTILO (TIPO STEAM CLARO)
# -----------------------------
st.set_page_config(page_title="🎮 Juegos de Terror", layout="centered")

st.markdown("""
<style>
body { background-color: #f5f7fa; }

.card {
    background: white;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.muted {
    color: #6b7280;
    font-size: 14px;
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
# ESTADO
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "inicio"

if "juego_seleccionado" not in st.session_state:
    st.session_state.juego_seleccionado = None

# -----------------------------
# HEADER
# -----------------------------
st.title("🎮 Sistema de Reseñas de Terror")

col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.page = "inicio"

with col2:
    if st.button("👤 Perfil", use_container_width=True):
        st.session_state.page = "perfil"

# -----------------------------
# INICIO (CATÁLOGO)
# -----------------------------
if st.session_state.page == "inicio":

    st.subheader("🎮 Catálogo de Juegos")

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
                    <div style="font-size:18px; font-weight:bold;">🎮 {nombre}</div>
                    <div class="muted">Juego de terror</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("Reseñar", key=f"btn_{_id}", use_container_width=True):
                    st.session_state.juego_seleccionado = nombre
                    st.session_state.page = "resena"

# -----------------------------
# RESEÑA
# -----------------------------
elif st.session_state.page == "resena":

    st.subheader("✍️ Nueva Reseña")

    usuario = st.text_input("Usuario")

    juegos_disponibles = [j.get("nombre") for j in coleccion_juegos.find() if j.get("nombre")]

    juego = st.selectbox(
        "Selecciona juego",
        juegos_disponibles,
        index=juegos_disponibles.index(st.session_state.juego_seleccionado)
        if st.session_state.juego_seleccionado in juegos_disponibles else 0
    )

    texto = st.text_area("Escribe tu reseña")
    rating = st.slider("⭐ Calificación", 1, 5, 3)

    if st.button("Guardar Reseña", use_container_width=True):

        if usuario and texto:

            coleccion_resenas.insert_one({
                "usuario": usuario,
                "juego": juego,
                "texto": texto,
                "rating": rating
            })

            st.success("✅ Reseña guardada")

        else:
            st.error("Completa los campos")

    if st.button("⬅ Volver", use_container_width=True):
        st.session_state.page = "inicio"

# -----------------------------
# PERFIL
# -----------------------------
elif st.session_state.page == "perfil":

    st.subheader("👤 Perfil")

    usuario = st.text_input("Usuario")

    if usuario:

        st.write("### 📝 Tus reseñas")

        resenas = list(coleccion_resenas.find({"usuario": usuario}))

        if resenas:
            for r in resenas:
                st.markdown(f"""
                <div class="card">
                    🎮 <b>{r.get("juego")}</b><br>
                    ⭐ {r.get("rating", "N/A")}<br>
                    {r.get("texto")}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tienes reseñas")

        st.write("### 🎯 Recomendaciones")

        resultados = recomendar(usuario)

        for nombre, score in resultados[:5]:
            st.write(f"🎮 {nombre} — {score}")
