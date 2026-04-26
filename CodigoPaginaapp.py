# -----------------------------
# Agregar Juego
# -----------------------------
if menu == "Agregar Juego":
    st.subheader("Nuevo Juego")

    nombre = st.text_input("Nombre del juego")
    anio = st.number_input("Año", min_value=2000, max_value=2030)

    # Opciones base
    opciones_base = [
        "miedo",
        "historia",
        "oscuridad",
        "monstruos",
        "tension"
    ]

    # Selección múltiple
    seleccion = st.multiselect("Descripción del juego", opciones_base)

    # Campo adicional (mejora)
    nueva_desc = st.text_input("Agregar otra descripción (opcional)")

    if st.button("Guardar Juego"):
        if nombre:
            # 🔥 NORMALIZACIÓN
            descripcion_final = [d.lower().strip() for d in seleccion]

            if nueva_desc:
                descripcion_final.append(nueva_desc.lower().strip())

            # 🔥 ELIMINAR DUPLICADOS
            descripcion_final = list(set(descripcion_final))

            juego = {
                "nombre": nombre,
                "genero": "terror",
                "anio": int(anio),
                "tags": descripcion_final
            }

            coleccion_juegos.update_one(
                {"nombre": nombre},
                {"$set": juego},
                upsert=True
            )

            st.success("Juego guardado correctamente")
        else:
            st.error("Falta el nombre del juego")
