import streamlit as st
from pymongo import MongoClient
import os

# -----------------------------
# CONFIG
# -----------------------------
try:
    URI = st.secrets["MONGO_URI"]
except:
    URI = os.getenv("MONGO_URI")

if not URI:
    st.error("❌ No se encontró MONGO_URI")
    st.stop()

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
# ESTADO
# -----------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

if "juego" not in st.session_state:
    st.session_state.juego = None

# -----------------------------
# ESTILO STEAM
# -----------------------------
st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: white;
}

.card {
    background-color: #1b2838;
    padding: 15px;
    border-radius: 12px;
    margin: 10px;
    transition: 0.3s;
}

.card:hover {
    transform: scale(1.03);
    background-color: #2a475e;
}

.titulo {
    font-size: 18px;
    font-weight: bold;
}

.precio {
    color: #66c0f4;
}

.stButton>button {
    background-color: #66c0f4;
    color: black;
    border-radius: 8px;
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
        kw = extraer_keywords(r.get("texto", ""))
        for k, v in kw.items():
            perfil[k] = perfil.get(k, 0) + v

    return perfil


def recomendar(usuario):
    perfil = perfil_usuario(usuario)
    juegos = coleccion_juegos.find()

    resultados = []

    for j in juegos:
        nombre = j.get("nombre")
        if not nombre:
            continue

        score = 0
        for tag in j.get("tags", []):
            if tag in perfil:
                score += perfil[tag]

        resultados.append((nombre, score))

    return sorted(resultados, key=lambda x: x[1], reverse=True)

# -----------------------------
# HEADER
# -----------------------------
st.title("🎮 Steam Terror")

col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 Inicio"):
        st.session_state.pagina = "inicio"

with col2:
    if st.button("👤 Perfil"):
        st.session_state.pagina = "perfil"

# -----------------------------
# INICIO (CATÁLOGO)
# -----------------------------
if st.session_state.pagina == "inicio":

    st.subheader("🔥 Catálogo")

    busqueda = st.text_input("🔍 Buscar juego")

    juegos = list(coleccion_juegos.find())

    cols = st.columns(3)  # GRID

    i = 0
    for j in juegos:
        nombre = j.get("nombre")
        _id = str(j.get("_id"))

        if not nombre:
            continue

        if busqueda.lower() not in nombre.lower():
            continue

        with cols[i % 3]:
            st.markdown(f"""
            <div class="card">
                <img src="https://via.placeholder.com/300x150" width="100%">
                <div class="titulo">{nombre}</div>
                <div class="precio">🎮 Terror</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Ver / Reseñar", key=f"btn_{_id}"):
                st.session_state.juego = nombre
                st.session_state.pagina = "detalle"

        i += 1

# -----------------------------
# DETALLE DEL JUEGO
# -----------------------------
elif st.session_state.pagina == "detalle":

    juego = st.session_state.juego

    st.subheader(f"🎮 {juego}")

    usuario = st.text_input("Usuario")
    texto = st.text_area("Escribe tu reseña")
    rating = st.slider("⭐ Calificación", 1, 5, 3)

    if st.button("Guardar Reseña"):
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

    # Mostrar reseñas
    st.write("### 📝 Reseñas")

    resenas = coleccion_resenas.find({"juego": juego})

    for r in resenas:
        st.markdown(f"""
        <div class="card">
        👤 {r.get("usuario")} <br>
        ⭐ {r.get("rating", "N/A")} <br>
        {r.get("texto")}
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Volver"):
        st.session_state.pagina = "inicio"

# -----------------------------
# PERFIL
# -----------------------------
elif st.session_state.pagina == "perfil":

    usuario = st.text_input("Ingresa tu usuario")

    if usuario:

        st.write("### 📝 Tus reseñas")

        resenas = list(coleccion_resenas.find({"usuario": usuario}))

        for r in resenas:
            st.markdown(f"""
            <div class="card">
            🎮 {r.get("juego")} <br>
            ⭐ {r.get("rating", "N/A")} <br>
            {r.get("texto")}
            </div>
            """, unsafe_allow_html=True)

        st.write("### 🔥 Recomendaciones")

        recs = recomendar(usuario)

        for nombre, score in recs[:5]:
            st.write(f"🎮 {nombre} — {score}")
