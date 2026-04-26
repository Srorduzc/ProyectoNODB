from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# -----------------------------
# Config
# -----------------------------
load_dotenv()
URI = os.getenv("MONGO_URI")

if not URI:
    raise ValueError("Falta MONGO_URI en .env")

client = MongoClient(URI, serverSelectionTimeoutMS=5000)

try:
    client.server_info()
    print("Conectado a MongoDB")
except Exception as e:
    print("Error de conexión:", e)

db = client["videojuegos_terror"]

app = Flask(__name__)

# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return {"msg": "API funcionando"}

# -----------------------------
# Guardar reseña
# -----------------------------
@app.route("/resena", methods=["POST"])
def guardar_resena():
    data = request.json

    # Validación mínima (antes no tenías nada)
    if not data or "usuario" not in data or "texto" not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    db.resenas.insert_one(data)
    return jsonify({"msg": "Reseña guardada"})

# -----------------------------
# Recomendaciones
# -----------------------------
@app.route("/recomendar")
def recomendar():
    usuario = request.args.get("usuario")

    if not usuario:
        return jsonify({"error": "Falta usuario"}), 400

    resenas = list(db.resenas.find({"usuario": usuario}))

    palabras = ["miedo", "historia", "oscuridad", "monstruos"]
    perfil = {}

    for r in resenas:
        texto = r.get("texto", "").lower()
        for p in palabras:
            if p in texto:
                perfil[p] = perfil.get(p, 0) + 1

    juegos = list(db.juegos.find())
    resultado = []

    for j in juegos:
        score = 0
        for tag in j.get("tags", []):
            if tag in perfil:
                score += perfil[tag]

        resultado.append({
            "nombre": j.get("nombre", "Sin nombre"),
            "puntaje": score
        })

    resultado.sort(key=lambda x: x["puntaje"], reverse=True)

    return jsonify(resultado)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
