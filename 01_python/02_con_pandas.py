"""
EJEMPLO 2 - PYTHON con pandas
=============================

Que es:
    La misma tarea del ejemplo 01, pero usando pandas.
    pandas = la libreria de Python para trabajar con tablas de datos.

Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
    python 01_python/02_con_pandas.py

Que produce:
    Muestra las primeras filas de datos/mediciones.csv
    y un resumen (conteo, promedio, minimo, maximo) por sitio.

Fijate en: lo mismo que el ejemplo 01, pero en 3 lineas.
Esa es la gracia de las librerias.
"""

from pathlib import Path
import pandas as pd

RUTA_DATOS = Path(__file__).resolve().parent.parent / "datos" / "mediciones.csv"

# 1. Leer el CSV (una linea)
datos = pd.read_csv(RUTA_DATOS)

# 2. Ver las primeras filas (como espiar la tabla)
print("Primeras 5 filas:")
print(datos.head())
print()

# 3. Resumen por sitio (una linea)
resumen = datos.groupby("sitio")["peso_g"].agg(["count", "mean", "min", "max"])
print("Resumen del peso (g) por sitio:")
print(resumen.round(2))
