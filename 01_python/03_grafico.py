"""
EJEMPLO 3 - PYTHON con matplotlib (graficos)
============================================

Que es:
    Python dibujando un grafico con la libreria matplotlib.
    Este es el uso tipico en investigacion: datos -> figura para el informe.

Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
    python 01_python/03_grafico.py

Que produce:
    - Un grafico comparando el promedio de peso por sitio con barras de error.
    - El archivo 01_python/grafico_python.png (aqui al lado).
"""

# Usamos el motor "Agg" para que funcione tambien sin ventana (servidor, terminal)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

RUTA_DATOS = Path(__file__).resolve().parent.parent / "datos" / "mediciones.csv"
RUTA_SALIDA = Path(__file__).resolve().parent / "grafico_python.png"

# 1. Leer datos y calcular promedio + desviacion por sitio
datos = pd.read_csv(RUTA_DATOS)
resumen = datos.groupby("sitio")["peso_g"].agg(["mean", "std"])

# 2. Dibujar el grafico
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(
    resumen.index,
    resumen["mean"],
    yerr=resumen["std"],
    capsize=6,
    color=["#4c72b0", "#dd8452"],
    edgecolor="black",
)
ax.set_title("Peso promedio por sitio")
ax.set_xlabel("Sitio")
ax.set_ylabel("Peso (g)")
ax.grid(axis="y", linestyle="--", alpha=0.4)

# 3. Guardar la imagen
fig.tight_layout()
fig.savefig(RUTA_SALIDA, dpi=150)
print(f"Grafico guardado en: {RUTA_SALIDA}")
