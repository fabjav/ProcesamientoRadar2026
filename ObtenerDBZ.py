import os
from PIL import Image
import numpy as np
from osgeo import gdal

# =========================
# CONFIG
# =========================
input_dir = "tormenta_test"
output_tif_dir = "rasters_salida_mendoza"
output_png_dir = "png_control"
cantidad = "todo"  # int o "todo"

# TIFS estándar
tif_700_path = "tif700.tif"
tif_800_path = "tif800.tif"

os.makedirs(output_tif_dir, exist_ok=True)
os.makedirs(output_png_dir, exist_ok=True)

# =========================
# MAPEO dBZ
# =========================
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

dbz_a_color = {v: k for k, v in niveles_dbz.items()}

# =========================
# FUNCIONES
# =========================
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

                if len(vecinos) >= 2:
                    nueva[i][j] = int(sum(vecinos) / len(vecinos))

    return nueva


def leer_wld(ruta_wld):
    with open(ruta_wld, "r") as f:
        lineas = f.readlines()

    A = float(lineas[0])
    D = float(lineas[1])
    B = float(lineas[2])
    E = float(lineas[3])
    C = float(lineas[4])
    F = float(lineas[5])

    return (A, B, C, D, E, F)


def cargar_georef(ancho):
    """
    Selección de grilla según tamaño
    """
    if ancho > 790:
        ds = gdal.Open(tif_800_path)
    else:
        ds = gdal.Open(tif_700_path)

    return ds.GetGeoTransform(), ds.GetProjection()


# =========================
# PROCESAMIENTO
# =========================
archivos = [f for f in os.listdir(input_dir) if f.endswith(".png")]

if cantidad != "todo":
    archivos = archivos[:cantidad]

for archivo in archivos:

    try:
        ruta_png = os.path.join(input_dir, archivo)
        ruta_wld = ruta_png.replace(".png", ".wld")

        if not os.path.exists(ruta_wld):
            print(f"Sin WLD: {archivo}")
            continue

        img = Image.open(ruta_png).convert("RGB")
        ancho, alto = img.size

        # =========================
        # MATRIZ dBZ
        # =========================
        matriz_dbz = []

        for y in range(alto):
            fila = []
            for x in range(ancho):
                color = img.getpixel((x, y))
                valor = color_mas_cercano(color, niveles_dbz)
                fila.append(valor)
            matriz_dbz.append(fila)

        # =========================
        # RELLENO DE HUECOS
        # =========================
        for _ in range(20):
            nueva = rellenar_huecos(matriz_dbz)
            if nueva == matriz_dbz:
                break
            matriz_dbz = nueva

        matriz_np = np.array(matriz_dbz, dtype=np.float32)

        # =========================
        # PNG CONTROL
        # =========================
        img_dbz = Image.new("RGBA", (ancho, alto))

        for y in range(alto):
            for x in range(ancho):
                valor = matriz_dbz[y][x]

                if valor == 0:
                    img_dbz.putpixel((x, y), (0, 0, 0, 0))
                elif valor in dbz_a_color:
                    r, g, b = dbz_a_color[valor]
                    img_dbz.putpixel((x, y), (r, g, b, 255))
                else:
                    img_dbz.putpixel((x, y), (0, 0, 0, 0))

        img_dbz.save(os.path.join(output_png_dir, archivo))

        # =========================
        # GEOREFERENCIA SEGÚN TIPO
        # =========================
        geotransform, projection = cargar_georef(ancho)

        # =========================
        # EXPORTAR GeoTIFF
        # =========================
        nombre_salida = archivo.replace(".png", ".tif")
        ruta_tif = os.path.join(output_tif_dir, nombre_salida)

        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(ruta_tif, ancho, alto, 1, gdal.GDT_Float32)

        ds.SetGeoTransform(geotransform)
        ds.SetProjection(projection)

        band = ds.GetRasterBand(1)
        band.WriteArray(matriz_np)
        band.SetNoDataValue(-9999)

        ds = None

        print(f"✔ {archivo}")

    except Exception as e:
        print(f"Error con {archivo}: {e}")

print("Procesamiento terminado.")