PALABRAS_GASOLINA = [
    "petroprix", "repsol", "cepsa", "bp", "plenoil", 
    "e.s.", "e.s ", "gasolinera", "estacion de servicio", "shell",
    "es "
]

def obtener_categoria(descripcion, contraparte):
    texto_completo = f"{descripcion} {contraparte}".lower()
    for palabra in PALABRAS_GASOLINA:
        if palabra in texto_completo:
            return "Gasolina"
    return "Otros"