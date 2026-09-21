"""
EJEMPLO 1 - PYTHON "puro" (sin librerias externas)
===================================================

Que es:
    Python usando SOLO lo que ya trae de fabrica.
    Aqui ni pandas ni matplotlib: todo a mano con el modulo csv.

Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
    python 01_python/01_sin_librerias.py

Que produce:
    Imprime en pantalla un resumen de datos/mediciones.csv
    (promedio, minimo y maximo de peso por sitio).

Fijate en: hay que escribir BASTANTE codigo a mano para algo simple.
En el ejemplo 02 veras como pandas reduce todo esto a 3 lineas.
"""

import csv
from pathlib import Path

# Ruta al archivo de datos (funciona sin importar desde donde lo ejecutes)
RUTA_DATOS = Path(__file__).resolve().parent.parent / "datos" / "mediciones.csv"

# 1. Leer el CSV y agrupar los pesos por sitio
pesos_por_sitio = {}

with open(RUTA_DATOS, encoding="utf-8") as archivo:
    lector = csv.DictReader(archivo)
    for fila in lector:
        sitio = fila["sitio"]
        peso = float(fila["peso_g"])
        pesos_por_sitio.setdefault(sitio, []).append(peso)

# 2. Calcular e imprimir resultados
print(f"Datos leidos de: {RUTA_DATOS.name}")
print()

for sitio, valores in pesos_por_sitio.items():
    promedio = sum(valores) / len(valores)
    print(f"{sitio}:")
    print(f"  muestras : {len(valores)}")
    print(f"  promedio : {promedio:.2f} g")
    print(f"  minimo   : {min(valores):.1f} g")
    print(f"  maximo   : {max(valores):.1f} g")
    print()
