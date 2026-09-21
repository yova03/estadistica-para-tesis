"""
EJEMPLO 4 - PYTHON con scipy (estadistica de verdad)
=====================================================

Que es:
    Una prueba estadistica clasica: comparar dos grupos.
    scipy.stats.ttest_ind hace la prueba t de Student, igual que en R, SPSS o Stata.

Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
    python 01_python/04_estadistica.py

Que produce:
    El valor t, el valor p, y una interpretacion en palabras simples.

Como se lee el valor p:
    p < 0.05  -> hay diferencia estadisticamente significativa entre los sitios.
    p >= 0.05 -> no se puede afirmar que haya diferencia.
"""

from pathlib import Path
import pandas as pd
from scipy import stats

RUTA_DATOS = Path(__file__).resolve().parent.parent / "datos" / "mediciones.csv"

# 1. Leer datos y separar los dos grupos
datos = pd.read_csv(RUTA_DATOS)
grupo_a = datos.loc[datos["sitio"] == "Sitio A", "peso_g"]
grupo_b = datos.loc[datos["sitio"] == "Sitio B", "peso_g"]

# 2. Prueba t de Student para dos muestras independientes
t, p = stats.ttest_ind(grupo_a, grupo_b)

# 3. Mostrar resultados
print("Prueba t de Student (peso_g: Sitio A vs Sitio B)")
print(f"  media Sitio A : {grupo_a.mean():.2f} g")
print(f"  media Sitio B : {grupo_b.mean():.2f} g")
print(f"  valor t       : {t:.3f}")
print(f"  valor p       : {p:.6f}")
print()

if p < 0.05:
    print("Conclusion: SI hay diferencia significativa entre los sitios (p < 0.05).")
else:
    print("Conclusion: NO hay diferencia significativa (p >= 0.05).")
