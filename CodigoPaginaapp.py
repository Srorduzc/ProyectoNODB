import streamlit as st
from pymongo import MongoClient
import os

# -----------------------------
# CONFIGURACIÓN (CORRECTA)
# -----------------------------
try:
    URI = st.secrets["MONGO_URI"]  # Streamlit Cloud
except:
    URI = os.getenv("MONGO_URI")   # Local

if not URI:
    st.error("❌ No se encontró MONGO_URI")
    st.stop()

# -----------------------------
# CONEXIÓN (CACHEADA)
# -----------------------------
@st.cache_resource
def conectar():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # prueba real
        return client
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        st.stop()

client = conectar()
db = client["videojuegos_terror"]

coleccion_juegos = db["juegos"]
coleccion_resenas = db["resenas"]

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

menu = st.sidebar.selectbox("Menú", [
    "Agregar Juego",
    "Agregar Reseña",
    "Ver Recomendaciones"
])

# -----------------------------
# AGREGAR JUEGO
# -----------------------------
if menu == "Agregar Juego":
    st.subheader("Nuevo Juego")

    nombre = st.text_input("Nombre del juego")
    anio = st.number_input("Año", min_value=2000, max_value=2030)

    opciones_descripcion = [
        "miedo",
        "historia",
        "oscuridad",
        "monstruos",
        "tension"
    ]

    descripcion = st.multiselect("Descripción del juego", opciones_descripcion)

    if st.button("Guardar Juego"):
        if nombre:
            juego = {
                "nombre": nombre,
                "genero": "terror",
                "anio": int(anio),
                "tags": [d.lower().strip() for d in descripcion]
            }

            try:
                coleccion_juegos.update_one(
                    {"nombre": nombre},
                    {"$set": juego},
                    upsert=True
                )
                st.success("✅ Juego guardado")
            except Exception as e:
                st.error(f"❌ Error guardando juego: {e}")
        else:
            st.error("Falta nombre")

# -----------------------------
# AGREGAR RESEÑA
# -----------------------------
elif menu == "Agregar Reseña":
    st.subheader("Nueva Reseña")

    usuario = st.text_input("Usuario")

    # 🔥 Selección real de juegos
    juegos_disponibles = [j["nombre"] for j in coleccion_juegos.find()]
    
    if juegos_disponibles:
        juego = st.selectbox("Selecciona juego", juegos_disponibles)
    else:
        st.warning("⚠️ No hay juegos registrados")
        juego = None

    texto = st.text_area("Escribe tu reseña")

    if st.button("Guardar Reseña"):
        if usuario and texto and juego:
            resena = {
                "usuario": usuario,
                "juego": juego,
                "texto": texto
            }

            try:
                coleccion_resenas.insert_one(resena)
                st.success("✅ Reseña guardada")
            except Exception as e:
                st.error(f"❌ Error guardando reseña: {e}")
        else:
            st.error("Completa todos los campos")

# -----------------------------
# RECOMENDACIONES
# -----------------------------
elif menu == "Ver Recomendaciones":
    st.subheader("Recomendaciones")

    usuario = st.text_input("Usuario")

    if st.button("Buscar"):
        if usuario:
            perfil = perfil_usuario(usuario)
            resultados = recomendar(usuario)

            st.write("### Perfil del usuario")
            st.write(perfil if perfil else "Sin datos")

            st.write("### Juegos recomendados")
            if resultados:
                for nombre, score in resultados:
                    st.write(f"🎮 {nombre} — Puntaje: {score}")
            else:
                st.warning("No hay resultados")
        else:
            st.error("Ingresa un usuario")
