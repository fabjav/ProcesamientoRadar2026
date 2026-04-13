from osgeo import gdal
import numpy as np
import os

# 1. Leer georreferencia base
ds_base = gdal.Open("datos_geo.tif")

geotransform = ds_base.GetGeoTransform()
projection = ds_base.GetProjection()

# 2. Carpeta de entrada y salida
carpeta_csv = "matrices_dbz"
carpeta_salida = "rasters_salida"

# crear carpeta si no existe
os.makedirs(carpeta_salida, exist_ok=True)

# 3. Procesar CSVs
for archivo in os.listdir(carpeta_csv):
    if archivo.endswith(".csv"):

        ruta_csv = os.path.join(carpeta_csv, archivo)

        # cargar matriz
        data = np.loadtxt(ruta_csv, delimiter=",")

        rows, cols = data.shape

        # nombre de salida
        nombre_salida = archivo.replace(".csv", ".tif")
        ruta_salida = os.path.join(carpeta_salida, nombre_salida)

        # crear raster
        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(ruta_salida, cols, rows, 1, gdal.GDT_Float32)

        # aplicar georreferencia
        ds.SetGeoTransform(geotransform)
        ds.SetProjection(projection)

        # escribir datos
        band = ds.GetRasterBand(1)
        band.WriteArray(data)
        band.SetNoDataValue(-9999)

        ds = None  # guardar

        print(f"✔ creado: {ruta_salida}")