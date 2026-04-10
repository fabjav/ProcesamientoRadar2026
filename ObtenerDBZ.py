import os
import re
from PIL import Image
import numpy as np
from datetime import datetime, timedelta

# 🔹 Mapeo color → dBZ (RGB)
niveles_dbz = {
    (66, 63, 140): 10,
    (0, 88, 5): 20,
    (0, 111, 9): 30,
    (0, 132, 220): 35,
    (0, 82, 233): 36,
    (108, 39, 199): 39,
    (210, 30, 133): 42,
    (200, 102, 135): 45,
    (219, 136, 52): 48,
    (255, 195, 41): 51,
    (255, 248, 7): 54,
    (255, 155, 83): 57,
    (255, 95, 0): 60,
    (255, 52, 0): 65,
    (191, 191, 191): 70,
    (212, 212, 212): 80
}

# 🔹 Invertir diccionario (dBZ → color)
dbz_a_color = {v: k for k, v in niveles_dbz.items()}

# 🔹 Función: color más cercano
def color_mas_cercano(color, mapa, umbral=500):
    min_dist = float("inf")
    mejor_valor = 0

    for ref_color, dbz in mapa.items():
        dist = sum((c1 - c2) ** 2 for c1, c2 in zip(color, ref_color))

        if dist < min_dist:
            min_dist = dist
            mejor_valor = dbz

    if min_dist > umbral:
        return 0

    return mejor_valor

# 🔹 Relleno de huecos (marca de agua)
def rellenar_huecos(matriz):
    alto = len(matriz)
    ancho = len(matriz[0])

    nueva = [fila[:] for fila in matriz]

    for i in range(alto):
        for j in range(ancho):

            if matriz[i][j] == 0:

                vecinos = []

                for di, dj in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ni, nj = i + di, j + dj

                    if 0 <= ni < alto and 0 <= nj < ancho:
                        if matriz[ni][nj] != 0:
                            vecinos.append(matriz[ni][nj])

                # 🔥 condición (ajustable)
                if len(vecinos) >= 2:
                    nueva[i][j] = int(sum(vecinos) / len(vecinos))

    return nueva

# 🔹 Carpetas
input_dir = "recortadas"
output_img_dir = "imagen_dbz"
output_csv_dir = "matrices_dbz"

os.makedirs(output_img_dir, exist_ok=True)
os.makedirs(output_csv_dir, exist_ok=True)

# 🔹 Nombre corregido
def obtener_nombre(fecha_str, hora_str):
    dt = datetime.strptime(fecha_str + hora_str, "%Y%m%d%H%M")
    dt = dt - timedelta(hours=3, minutes=2)
    return dt.strftime("mendoza_%Y%m%d_%H%M")

# 🔹 Procesamiento
for archivo in os.listdir(input_dir):

    if not archivo.endswith(".gif"):
        continue

    match = re.match(r"radar_(\d{8})_(\d{4})_\d+\.gif", archivo)

    if not match:
        print(f"Ignorado: {archivo}")
        continue

    fecha = match.group(1)
    hora = match.group(2)

    try:
        nombre_base = obtener_nombre(fecha, hora)
        ruta = os.path.join(input_dir, archivo)

        img = Image.open(ruta).convert("RGB")
        ancho, alto = img.size

        matriz_dbz = []

        # 🔹 1. Construcción matriz dBZ
        for y in range(alto):
            fila = []
            for x in range(ancho):

                color = img.getpixel((x, y))
                valor = color_mas_cercano(color, niveles_dbz)

                fila.append(valor)

            matriz_dbz.append(fila)

        # 🔥 2. Relleno (AHORA 20 PASADAS)
        for _ in range(20):
            nueva = rellenar_huecos(matriz_dbz)

            if nueva == matriz_dbz:
                break

            matriz_dbz = nueva

        # 🔹 3. Reconstrucción imagen
        img_dbz = Image.new("RGB", (ancho, alto))

        for y in range(alto):
            for x in range(ancho):

                valor = matriz_dbz[y][x]

                if valor in dbz_a_color:
                    img_dbz.putpixel((x, y), dbz_a_color[valor])
                else:
                    img_dbz.putpixel((x, y), (0, 0, 0))

        matriz_np = np.array(matriz_dbz)

        # 🔹 Guardar imagen
        img_dbz.save(os.path.join(output_img_dir, nombre_base + ".png"))

        # 🔹 Guardar CSV
        np.savetxt(
            os.path.join(output_csv_dir, nombre_base + ".csv"),
            matriz_np,
            fmt="%d",
            delimiter=","
        )

        print(f"Procesado: {archivo} → {nombre_base}")

    except Exception as e:
        print(f"Error con {archivo}: {e}")

print("✅ Procesamiento terminado.")