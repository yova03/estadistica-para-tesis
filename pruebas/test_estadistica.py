# -*- coding: utf-8 -*-
"""
Comprobacion de las formulas de `estadistica_tesis.py`.

Se compara cada resultado contra:
  - tablas estadisticas clasicas (t de Student, F de Fisher),
  - valores calculados a mano paso a paso,
  - y, si estan instalados, scipy y numpy.

Como se ejecuta (desde la carpeta principal del repositorio):

    python pruebas/test_estadistica.py

Si scipy y numpy no estan instalados, el script lo avisa y comprueba
igual todo lo que no depende de ellos. Termina con codigo 0 si todo
pasa y con codigo 1 si algo falla.
"""

import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import estadistica_tesis as et  # noqa: E402

fallas = []
cuantas = 0


def cerca(nombre, obtenido, esperado, tolerancia=1e-4):
    """Comprueba que dos numeros coincidan dentro de una tolerancia."""
    global cuantas
    cuantas += 1
    ok = abs(obtenido - esperado) <= tolerancia
    marca = "OK   " if ok else "FALLA"
    print(f"  {marca} {nombre:<44} {obtenido:>14.8f}  esperado {esperado:>14.8f}")
    if not ok:
        fallas.append(nombre)


print()
print("=" * 78)
print("  COMPROBACION DE LAS FORMULAS DE estadistica_tesis.py")
print("=" * 78)

# ------------------------------------------------------------
print("\n--- Distribuciones (tablas clasicas) ---")
# En una t con 18 grados de libertad, t = 2.1009 deja 0.05 en las dos colas.
cerca("p de dos colas, t = 2.1009, gl = 18", et.p_valor_t(2.1009, 18), 0.05)
cerca("p de dos colas, t = 2.2281, gl = 10", et.p_valor_t(2.2281, 10), 0.05)
cerca("p de dos colas, t = 1.9600, gl = 10000", et.p_valor_t(1.9600, 10000), 0.05, 1e-3)
cerca("t critico, gl = 18, 95%", et.t_critico(18), 2.1009)
cerca("t critico, gl = 5, 95%", et.t_critico(5), 2.5706)
cerca("t critico, gl = 30, 99%", et.t_critico(30, 0.99), 2.7500)
cerca("p de F = 3.8853, gl = 2 y 12", et.p_valor_f(3.8853, 2, 12), 0.05)
cerca("z de 0.975", et.z_inversa(0.975), 1.959964, 1e-6)
cerca("z de 0.80", et.z_inversa(0.80), 0.841621, 1e-6)
cerca("z de 0.95", et.z_inversa(0.95), 1.644854, 1e-6)

# ------------------------------------------------------------
print("\n--- Descriptivos (datos/mediciones.csv, Sitio A) ---")
datos, _ = et.leer_csv(RAIZ / "datos" / "mediciones.csv")
grupo_a = et.numeros_de(datos, "peso_g")[:10]
grupo_b = et.numeros_de(datos, "peso_g")[10:]
d = et.descriptivos(grupo_a)
cerca("media", d["media"], 11.72)
cerca("mediana", d["mediana"], 11.80)
cerca("desviacion estandar", d["desviacion"], 0.6268085, 1e-6)
cerca("coeficiente de variacion", d["cv"], 5.3481953, 1e-5)
cerca("minimo", d["minimo"], 10.8)
cerca("maximo", d["maximo"], 12.6)

# ------------------------------------------------------------
print("\n--- Prueba t de Student ---")
r = et.prueba_t_independiente(grupo_a, grupo_b)
cerca("estadistico t", r["t"], -11.7275230, 1e-6)
cerca("grados de libertad", r["gl"], 18)
cerca("d de Cohen", r["d_cohen"], -5.2447077, 1e-6)
cerca("F de varianzas", r["f"], 0.4182222 / 0.3928889, 1e-6)
cerca("p de la F de varianzas (2 colas)", r["p_f"], 0.9273660, 1e-6)

# ------------------------------------------------------------
print("\n--- Correlacion ---")
x = [1, 2, 3, 4, 5, 6, 7, 8]
y = [2, 4, 5, 4, 5, 7, 8, 9]
cerca("Pearson r", et.pearson(x, y), 0.95118973, 1e-7)
cerca("Spearman rho", et.spearman(x, y), 0.93982725, 1e-7)
cerca("Pearson con relacion perfecta", et.pearson(x, [2 * v for v in x]), 1.0, 1e-12)
cerca("Pearson con relacion inversa", et.pearson(x, [-2 * v for v in x]), -1.0, 1e-12)
cerca("Spearman con empates", et.spearman([1, 1, 2, 3], [2, 2, 4, 6]), 1.0, 1e-12)

# ------------------------------------------------------------
print("\n--- ANOVA de un factor ---")
g1 = [11.2, 12.4, 10.8, 12.1, 11.9]
g2 = [14.8, 15.3, 14.1, 16.2, 15.0]
g3 = [9.1, 9.8, 8.9, 10.2, 9.5]
a = et.anova(g1, g2, g3)
cerca("estadistico F", a["f"], 91.31793687, 1e-6)
cerca("grados de libertad entre", a["gl_entre"], 2)
cerca("grados de libertad dentro", a["gl_dentro"], 12)
cerca("eta cuadrado", a["eta2"], 0.93834641, 1e-6)

# ------------------------------------------------------------
print("\n--- Alfa de Cronbach (calculado a mano) ---")
matriz = [
    [4, 5, 3, 4],
    [5, 5, 4, 4],
    [3, 4, 3, 3],
    [4, 4, 4, 4],
    [5, 5, 5, 4],
    [3, 3, 2, 3],
]
c = et.alfa_cronbach(matriz)
cerca("alfa de Cronbach", c["alfa"], 0.91819292, 1e-7)
cerca("numero de items", c["k"], 4)

# ------------------------------------------------------------
print("\n--- Escala de lectura del alfa ---")
for valor, palabra in [(0.95, "excelente"), (0.85, "buena"), (0.75, "aceptable"),
                       (0.65, "cuestionable"), (0.50, "insuficiente")]:
    cuantas += 1
    if et.nivel_alfa(valor) != palabra:
        fallas.append(f"nivel_alfa({valor})")
        print(f"  FALLA nivel_alfa({valor}) = {et.nivel_alfa(valor)}, esperado {palabra}")
    else:
        print(f"  OK    nivel_alfa({valor}) = {palabra}")

# ------------------------------------------------------------
try:
    import numpy as np
    from scipy import stats as sp

    print("\n--- Contraste contra scipy y numpy ---")
    cerca("t de Student", r["t"], float(sp.ttest_ind(grupo_a, grupo_b).statistic), 1e-9)
    cerca("p de la t de Student", r["p"], float(sp.ttest_ind(grupo_a, grupo_b).pvalue), 1e-12)
    cerca("p de la t de Welch", r["p_welch"],
          float(sp.ttest_ind(grupo_a, grupo_b, equal_var=False).pvalue), 1e-12)
    cerca("F de varianzas (estadistico)", r["f"],
          float(np.var(grupo_b, ddof=1) / np.var(grupo_a, ddof=1)), 1e-12)
    cerca("p de la F de varianzas", r["p_f"],
          float(2.0 * (1.0 - sp.f.cdf(r["f"], r["gl_f1"], r["gl_f2"]))), 1e-12)
    cerca("p de la t pareada", et.prueba_t_pareada(g1, g2)["p"],
          float(sp.ttest_rel(g1, g2).pvalue), 1e-12)
    cerca("F de ANOVA", a["f"], float(sp.f_oneway(g1, g2, g3).statistic), 1e-12)
    cerca("p de ANOVA", a["p"], float(sp.f_oneway(g1, g2, g3).pvalue), 1e-12)
    cerca("Pearson r", et.pearson(x, y), float(sp.pearsonr(x, y)[0]), 1e-12)
    cerca("Spearman rho", et.spearman(x, y), float(sp.spearmanr(x, y)[0]), 1e-12)
    cerca("asimetria", d["asimetria"], float(sp.skew(grupo_a, bias=False)), 1e-12)
    cerca("curtosis", d["curtosis"], float(sp.kurtosis(grupo_a, bias=False)), 1e-12)
    cerca("t critico, gl = 18", et.t_critico(18), float(sp.t.ppf(0.975, 18)), 1e-9)
    cerca("t critico, gl = 7, 99%", et.t_critico(7, 0.99), float(sp.t.ppf(0.995, 7)), 1e-9)
    cerca("z de 0.975", et.z_inversa(0.975), float(sp.norm.ppf(0.975)), 1e-9)
    cerca("p de F, cola derecha", et.p_valor_f(3.0, 5, 20),
          float(1.0 - sp.f.cdf(3.0, 5, 20)), 1e-12)
except ImportError:
    print("\n  (scipy o numpy no estan instalados: se omite el contraste)")

# ------------------------------------------------------------
print("\n" + "=" * 78)
if fallas:
    print(f"FALLARON {len(fallas)} de {cuantas} comprobaciones:")
    for nombre in fallas:
        print(f"  - {nombre}")
    sys.exit(1)

print(f"PASARON LAS {cuantas} COMPROBACIONES")
print("=" * 78)
