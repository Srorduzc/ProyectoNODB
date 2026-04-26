import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv


URI = st.secrets["MONGO_URI"]

try:
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    st.success("Conectado correctamente")
except Exception as e:
    st.error(f"Error: {e}")

# -----------------------------
# Configuración
# -----------------------------
load_dotenv()
URI = os.getenv("MONGO_URI")

if not URI:
    st.error("Falta configurar MONGO_URI en .env")
    st.stop()

client = MongoClient(URI, serverSelectionTimeoutMS=5000)
db = client["videojuegos_terror"]

coleccion_juegos = db["juegos"]
coleccion_resenas = db["resenas"]

# -----------------------------
# Funciones
# -----------------------------
def extraer_keywords(texto):
    palabras = ["miedo", "historia", "oscuridad", "monstruos", "tension"]
    score = {}

    for p in palabras:
        if p in texto.lower():
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
# Agregar Juego
# -----------------------------
if menu == "Agregar Juego":
    st.subheader("Nuevo Juego")

    nombre = st.text_input("Nombre del juego")
    anio = st.number_input("Año", min_value=2000, max_value=2030)
    tags = st.text_input("Tags (separados por coma)")

    if st.button("Guardar Juego"):
        if nombre:
            lista_tags = [t.strip() for t in tags.split(",") if t.strip()]

            juego = {
                "nombre": nombre,
                "genero": "terror",
                "anio": int(anio),
                "tags": lista_tags
            }

            coleccion_juegos.update_one(
                {"nombre": nombre},
                {"$set": juego},
                upsert=True
            )

            st.success("Juego guardado")
        else:
            st.error("Falta nombre")

# -----------------------------
# Agregar Reseña
# -----------------------------
elif menu == "Agregar Reseña":
    st.subheader("Nueva Reseña")

    usuario = st.text_input("Usuario")
    juego = st.text_input("Juego")
    texto = st.text_area("Escribe tu reseña")

    if st.button("Guardar Reseña"):
        if usuario and texto:
            resena = {
                "usuario": usuario,
                "juego": juego,
                "texto": texto
            }

            coleccion_resenas.insert_one(resena)
            st.success("Reseña guardada")
        else:
            st.error("Completa los campos")

# -----------------------------
# Recomendaciones
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
