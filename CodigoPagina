# Instalar dependencias
!pip install flask pymongo

from flask import Flask, request, jsonify
from pymongo import MongoClient
import threading

# 🔗 PON TU URI REAL
URI = "mongodb+srv://USUARIO:CONTRASEÑA@proyectonodb.rhyoteu.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(URI)
db = client["videojuegos_terror"]

app = Flask(__name__)

# -----------------------------
# HTML
# -----------------------------
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Juegos de Terror</title>
        <style>
            body { background:#0d0d0d; color:white; font-family:Arial; }
            h1 { color:red; }
            input, textarea { width:300px; margin:5px; padding:8px; }
            button { background:red; color:white; padding:10px; border:none; }
        </style>
    </head>
    <body>
        <h1>🎮 Juegos de Terror</h1>

        <h3>Agregar Reseña</h3>
        <input id="usuario" placeholder="Usuario"><br>
        <input id="juego" placeholder="Juego"><br>
        <textarea id="texto" placeholder="Reseña"></textarea><br>
        <button onclick="enviar()">Enviar</button>

        <h3>Recomendaciones</h3>
        <button onclick="recomendar()">Ver recomendaciones</button>
        <ul id="lista"></ul>

        <script>
        function enviar(){
            fetch('/resena', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({
                    usuario:document.getElementById('usuario').value,
                    juego:document.getElementById('juego').value,
                    texto:document.getElementById('texto').value
                })
            }).then(r=>r.json()).then(d=>alert(d.msg))
        }

        function recomendar(){
            let usuario = document.getElementById('usuario').value
            fetch('/recomendar?usuario='+usuario)
            .then(r=>r.json())
            .then(data=>{
                let lista = document.getElementById('lista')
                lista.innerHTML=""
                data.forEach(j=>{
                    let li=document.createElement('li')
                    li.innerText=j
                    lista.appendChild(li)
                })
            })
        }
        </script>
    </body>
    </html>
    """

# -----------------------------
# Guardar reseña
# -----------------------------
@app.route("/resena", methods=["POST"])
def guardar_resena():
    data = request.json
    db.resenas.insert_one(data)
    return jsonify({"msg": "Reseña guardada"})

# -----------------------------
# Recomendación simple
# -----------------------------
@app.route("/recomendar")
def recomendar():
    usuario = request.args.get("usuario")
    resenas = list(db.resenas.find({"usuario": usuario}))

    palabras = ["miedo","historia","oscuridad","monstruos"]
    perfil = {}

    for r in resenas:
        for p in palabras:
            if p in r["texto"].lower():
                perfil[p] = perfil.get(p,0)+1

    juegos = list(db.juegos.find())
    resultado = []

    for j in juegos:
        score = 0
        for tag in j.get("tags",[]):
            if tag in perfil:
                score += perfil[tag]
        resultado.append((j["nombre"],score))

    resultado.sort(key=lambda x:x[1], reverse=True)

    return jsonify([r[0] for r in resultado])

# -----------------------------
# Ejecutar en segundo plano
# -----------------------------
def run_app():
    app.run(port=5000)

threading.Thread(target=run_app).start()

print("Servidor corriendo en Colab (puerto 5000)")
