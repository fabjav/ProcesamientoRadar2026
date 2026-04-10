import os
from PIL import Image


carpeta_entrada = "radar_mendoza"
carpeta_salida = "recortadas"


os.makedirs(carpeta_salida, exist_ok=True)


medida = {
    "izq": 5,
    "derecha": 146,
    "arriba": 58,
    "abajo": 29
}

# recortar imagen
def recortar_imagen(imagen):
    ancho, alto = imagen.size
    x_inicio = medida["izq"]
    y_inicio = medida["arriba"]
    x_fin = ancho - medida["derecha"]
    y_fin = alto - medida["abajo"]

    # Crop devuelve una nueva imagen con solo la región útil
    nueva_imagen = imagen.crop((x_inicio, y_inicio, x_fin, y_fin))
    return nueva_imagen

# procesar todas las imágenes de la carpeta 
for archivo in os.listdir(carpeta_entrada):
    # Solo archivos .gif
    if not archivo.lower().endswith(".gif"):
        continue

    ruta_entrada = os.path.join(carpeta_entrada, archivo)
    ruta_salida = os.path.join(carpeta_salida, archivo)

    # evitar duplicados
    if os.path.exists(ruta_salida):
        print(f"Ya existe: {archivo}, saltando...")
        continue

    # abrir recortar y guardar
    imagen = Image.open(ruta_entrada)
    imagen_recortada = recortar_imagen(imagen)
    imagen_recortada.save(ruta_salida)
    print(f"Guardada: {archivo}")