#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESTADISTICA PARA TESIS
======================
Un solo archivo. No necesita instalar nada: usa unicamente lo que ya trae
Python. Sirve para las cuentas que mas se piden en un informe de tesis.

QUE CALCULA
-----------
  1. Tamano de muestra (una media, una proporcion, dos medias, dos proporciones)
  2. Descriptivos: media, mediana, desviacion estandar, CV, IC 95%, asimetria,
     curtosis y un aviso de normalidad
  3. Comparar dos grupos: prueba t de Student (independiente o pareada),
     con la prueba F de varianzas y la alternativa de Welch
  4. Comparar mas de dos grupos: ANOVA de un factor y comparaciones por pares
     con correccion de Bonferroni
  5. Relacion entre dos variables: correlacion de Pearson y de Spearman
  6. Confiabilidad de un cuestionario: alfa de Cronbach, alfa si se elimina
     el item y correlacion item-total corregida
  7. Analizar un archivo CSV completo (detecta las columnas solo)

COMO SE USA
-----------
  Opcion A (recomendada): un CSV como argumento.

      python estadistica_tesis.py mis_datos.csv

  Opcion B: sin argumentos, aparece un menu y eliges.

      python estadistica_tesis.py

  Opcion C: ayuda rapida.

      python estadistica_tesis.py --ayuda

  En cualquier momento puedes escribir "0" para volver al menu.

COMO PREPARAR TU CSV
--------------------
  Primera fila: los nombres de las columnas.
  Una fila por participante o por muestra. Ejemplo:

      id,sitio,peso_g,longitud_mm
      1,Sitio A,11.2,46
      2,Sitio A,12.4,51
      3,Sitio B,14.8,63

  Guardalo como CSV UTF-8. Si lo hiciste en Excel: Archivo > Guardar como >
  CSV UTF-8 (delimitado por comas). Los decimales pueden ir con punto o coma.

QUE NO HACE
-----------
  No reemplaza el criterio del investigador ni la lectura de un estadistico.
  No hace regresion multiple, ni analisis factorial, ni modelos mixtos.
  Los datos no salen de tu computadora: todo se calcula localmente.

Autor: material de asesoria de tesis. Licencia MIT.
"""

import csv
import math
import statistics
import sys
from pathlib import Path

VERSION = "1.0"

# Se guarda todo lo que se muestra, para poder exportarlo a un archivo.
_SALIDA = []


# ============================================================
# 1. HERRAMIENTAS MATEMATICAS INTERNAS
#    (funciones de distribucion escritas a mano para no
#     depender de scipy ni de numpy)
# ============================================================

def _betacf(a, b, x):
    """Fraccion continua de Lentz para la funcion beta incompleta."""
    MAXIT, EPS, TINY = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0

    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < TINY:
        d = TINY
    d = 1.0 / d
    h = d

    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY:
            d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY:
            c = TINY
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY:
            d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY:
            c = TINY
        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < EPS:
            break

    return h


def _beta_incompleta(a, b, x):
    """Funcion beta incompleta regularizada I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    logbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
               + a * math.log(x) + b * math.log(1.0 - x))

    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(logbeta) * _betacf(a, b, x) / a
    return 1.0 - math.exp(logbeta) * _betacf(b, a, 1.0 - x) / b


def p_valor_t(t, gl):
    """Valor p de dos colas para una t con gl grados de libertad."""
    if gl <= 0:
        return 1.0
    return _beta_incompleta(gl / 2.0, 0.5, gl / (gl + t * t))


def p_valor_f(f, gl1, gl2):
    """Valor p de la cola derecha para una F con gl1 y gl2 grados de libertad."""
    if f <= 0 or gl1 <= 0 or gl2 <= 0:
        return 1.0
    return _beta_incompleta(gl2 / 2.0, gl1 / 2.0, gl2 / (gl2 + gl1 * f))


def t_critico(gl, confianza=0.95):
    """Cuantil t de dos colas, por biseccion (evita depender de tablas)."""
    objetivo = 1.0 - confianza
    bajo, alto = 0.0, 1000.0
    for _ in range(200):
        medio = (bajo + alto) / 2.0
        if p_valor_t(medio, gl) > objetivo:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2.0


def _normal_cdf(x):
    """Funcion de distribucion acumulada de la normal estandar."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def z_inversa(p):
    """Cuantil de la normal estandar.

    Usa la aproximacion de Acklam y luego un paso de refinamiento de
    Halley, con lo que el resultado queda en precision de maquina.
    """
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]

    if not 0.0 < p < 1.0:
        raise ValueError("La probabilidad debe estar entre 0 y 1.")

    limite = 0.02425
    if p < limite:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p > 1.0 - limite:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)

    # Refinamiento de Halley: corrige el error de la aproximacion.
    if 1e-12 < p < 1.0 - 1e-12:
        error = _normal_cdf(x) - p
        u = error * math.sqrt(2.0 * math.pi) * math.exp(0.5 * x * x)
        x = x - u / (1.0 + 0.5 * x * u)

    return x


def z_confianza(confianza):
    """Valor Z para un nivel de confianza (0.95 -> 1.96)."""
    return z_inversa(1.0 - (1.0 - confianza) / 2.0)


def z_potencia(potencia):
    """Valor Z para una potencia estadistica (0.80 -> 0.84)."""
    return z_inversa(potencia)


# ============================================================
# 2. ENTRADA Y SALIDA
# ============================================================

def decir(texto=""):
    """Muestra en pantalla y guarda copia para exportar."""
    print(texto)
    _SALIDA.append(str(texto))


def titulo(texto):
    decir()
    decir("=" * 64)
    decir("  " + texto)
    decir("=" * 64)


def subtitulo(texto):
    decir()
    decir("-" * 64)
    decir("  " + texto)
    decir("-" * 64)


def dato(etiqueta, valor, unidad=""):
    decir(f"  {etiqueta:<30} {valor}{unidad}")


def pausar():
    try:
        input("\n  Enter para volver al menu... ")
    except (EOFError, KeyboardInterrupt):
        decir()


def preguntar(texto, defecto=None):
    sufijo = f" [{defecto}]" if defecto is not None else ""
    try:
        respuesta = input(f"  {texto}{sufijo}: ").strip()
    except (EOFError, KeyboardInterrupt):
        decir()
        return defecto if defecto is not None else ""
    return respuesta if respuesta else (defecto if defecto is not None else "")


def preguntar_flotante(texto, defecto=None, minimo=None, maximo=None):
    while True:
        crudo = preguntar(texto, defecto)
        try:
            valor = float(str(crudo).replace(",", "."))
        except ValueError:
            decir("  Escribe un numero (por ejemplo 0.05).")
            continue
        if minimo is not None and valor < minimo:
            decir(f"  El valor debe ser mayor o igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            decir(f"  El valor debe ser menor o igual a {maximo}.")
            continue
        return valor


def preguntar_entero(texto, defecto=None, minimo=None, maximo=None):
    while True:
        valor = preguntar_flotante(texto, defecto, minimo, maximo)
        if abs(valor - round(valor)) > 1e-9:
            decir("  Escribe un numero entero.")
            continue
        return int(round(valor))


def preguntar_si_no(texto, defecto="s"):
    while True:
        respuesta = preguntar(texto + " (s/n)", defecto).strip().lower()
        if respuesta in ("s", "si", "sí", "y", "1"):
            return True
        if respuesta in ("n", "no", "0"):
            return False
        decir("  Responde s o n.")


def _a_numero(texto):
    """Convierte a float aceptando punto o coma decimal. None si no es numero."""
    t = str(texto).strip().replace(" ", "")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        pass
    if t.count(",") == 1 and "." not in t:
        try:
            return float(t.replace(",", "."))
        except ValueError:
            return None
    return None


def _partir_en_numeros(linea):
    limpia = linea.replace(",", " ").replace(";", " ").replace("\t", " ")
    return limpia.split()


def pedir_columna(etiqueta, minimo=2):
    """Pide una lista de numeros pegados, o la ruta de un archivo."""
    decir()
    decir(f"  {etiqueta}")
    decir("  Pega los numeros separados por espacio, coma o punto y coma.")
    decir("  Tambien vale la ruta de un archivo .csv o .txt (toma su primera")
    decir("  columna de numeros). Deja una linea vacia para terminar.")

    valores = []
    while True:
        try:
            linea = input("    > ").strip()
        except (EOFError, KeyboardInterrupt):
            decir()
            break

        if not linea:
            break

        if not valores and linea.lower().endswith((".csv", ".txt", ".tsv")):
            ruta = Path(linea.strip('"').strip("'"))
            if ruta.exists():
                valores = columna_de_archivo(ruta)
                decir(f"  (se leyeron {len(valores)} numeros de {ruta.name})")
                break
            decir("  No encuentro ese archivo. Pega los numeros directamente.")
            continue

        for trozo in _partir_en_numeros(linea):
            numero = _a_numero(trozo)
            if numero is None:
                decir(f"  Aviso: '{trozo}' no es un numero, se omite.")
            else:
                valores.append(numero)

    if len(valores) < minimo:
        decir()
        decir(f"  Se necesitan al menos {minimo} numeros. Se cancela el calculo.")
        return []
    return valores


def pedir_matriz(k_columnas, etiqueta="Pega una fila por participante."):
    """Pide una matriz: una fila por sujeto, con k_columnas valores."""
    decir()
    decir(f"  {etiqueta}")
    decir(f"  Cada fila necesita {k_columnas} numeros (los items separados")
    decir("  por coma, espacio o punto y coma). Deja una linea vacia al final.")

    matriz = []
    while True:
        try:
            linea = input(f"    fila {len(matriz) + 1:>3} > ").strip()
        except (EOFError, KeyboardInterrupt):
            decir()
            break

        if not linea:
            break

        if not matriz and linea.lower().endswith(".csv"):
            ruta = Path(linea.strip('"').strip("'"))
            if ruta.exists():
                matriz = matriz_de_archivo(ruta)
                decir(f"  (se leyeron {len(matriz)} filas de {ruta.name})")
                break
            decir("  No encuentro ese archivo.")
            continue

        fila = [_a_numero(t) for t in _partir_en_numeros(linea)]
        if any(v is None for v in fila):
            decir("  Hay algo que no es numero en esa fila. Se omite.")
            continue
        if len(fila) != k_columnas:
            decir(f"  Esa fila tiene {len(fila)} valores y se esperan {k_columnas}.")
            continue
        matriz.append(fila)

    if len(matriz) < 3:
        decir()
        decir("  Se necesitan al menos 3 filas. Se cancela el calculo.")
        return []
    return matriz


def leer_csv(ruta):
    """Lee un CSV y devuelve (filas, delimitador)."""
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        muestra = archivo.read(8192)
        archivo.seek(0)
        try:
            delimitador = csv.Sniffer().sniff(muestra, delimiters=",;\t|").delimiter
        except csv.Error:
            delimitador = ","
        return list(csv.DictReader(archivo, delimiter=delimitador)), delimitador


def columna_de_archivo(ruta):
    """Devuelve la primera columna de numeros que encuentre en el archivo."""
    if ruta.suffix.lower() in (".txt", ".tsv") and ruta.suffix.lower() != ".csv":
        with open(ruta, encoding="utf-8-sig") as archivo:
            valores = []
            for linea in archivo:
                for trozo in _partir_en_numeros(linea):
                    numero = _a_numero(trozo)
                    if numero is not None:
                        valores.append(numero)
            return valores

    filas, _ = leer_csv(ruta)
    if not filas:
        return []
    numericas, _ = clasificar_columnas(filas, list(filas[0].keys()))
    if not numericas:
        return []
    return [v for v in (_a_numero(f.get(numericas[0], "")) for f in filas) if v is not None]


def matriz_de_archivo(ruta):
    """Lee un CSV sin encabezado numerico: todas las celdas numericas."""
    filas, _ = leer_csv(ruta)
    matriz = []
    for fila in filas:
        valores = [_a_numero(v) for v in fila.values()]
        if all(v is not None for v in valores) and valores:
            matriz.append(valores)
    return matriz


def clasificar_columnas(filas, columnas):
    """Separa las columnas en numericas y categoricas (candidatas a grupo)."""
    numericas, categoricas = [], []

    for columna in columnas:
        crudos = [f.get(columna, "") for f in filas]
        con_dato = [c for c in crudos if str(c).strip() != ""]
        if not con_dato:
            continue

        convertidos = [_a_numero(c) for c in con_dato]
        if all(v is not None for v in convertidos):
            numericas.append(columna)
            continue

        distintos = {str(c).strip() for c in con_dato}
        if 2 <= len(distintos) <= 12:
            categoricas.append(columna)

    return numericas, categoricas


def valores_de(filas, columna):
    return [f.get(columna, "") for f in filas]


def numeros_de(filas, columna):
    return [v for v in (_a_numero(f.get(columna, "")) for f in filas) if v is not None]


def grupos_de(filas, columna_categorica, columna_numerica):
    """Devuelve {etiqueta: [numeros]} conservando el orden de aparicion."""
    grupos = {}
    for fila in filas:
        etiqueta = str(fila.get(columna_categorica, "")).strip()
        numero = _a_numero(fila.get(columna_numerica, ""))
        if etiqueta == "" or numero is None:
            continue
        grupos.setdefault(etiqueta, []).append(numero)
    return grupos


def guardar_salida(nombre="resultados_estadistica.txt"):
    if not _SALIDA:
        decir("  Todavia no hay resultados que guardar.")
        return
    ruta = Path.cwd() / nombre
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("\n".join(_SALIDA) + "\n")
    except OSError as error:
        decir(f"  No se pudo guardar: {error}")
        return
    decir()
    decir(f"  Resultados guardados en: {ruta}")


# ============================================================
# 3. CALCULOS
# ============================================================

def descriptivos(valores):
    """Resumen descriptivo completo de una lista de numeros."""
    n = len(valores)
    media = statistics.fmean(valores)
    desviacion = statistics.stdev(valores) if n > 1 else 0.0
    error_estandar = desviacion / math.sqrt(n) if n else 0.0
    t_crit = t_critico(n - 1) if n > 1 else 0.0

    return {
        "n": n,
        "media": media,
        "mediana": statistics.median(valores),
        "desviacion": desviacion,
        "varianza": desviacion ** 2,
        "error_estandar": error_estandar,
        "cv": (desviacion / media * 100.0) if media else 0.0,
        "minimo": min(valores),
        "maximo": max(valores),
        "rango": max(valores) - min(valores),
        "ic_inferior": media - t_crit * error_estandar,
        "ic_superior": media + t_crit * error_estandar,
        "asimetria": asimetria(valores),
        "error_asimetria": error_asimetria(n),
        "curtosis": curtosis(valores),
        "error_curtosis": error_curtosis(n),
    }


def asimetria(valores):
    """Asimetria ajustada (la misma que informa SPSS)."""
    n = len(valores)
    if n < 3:
        return 0.0
    desviacion = statistics.stdev(valores)
    if desviacion == 0:
        return 0.0
    media = statistics.fmean(valores)
    suma = sum(((v - media) / desviacion) ** 3 for v in valores)
    return n * suma / ((n - 1) * (n - 2))


def error_asimetria(n):
    if n < 3:
        return 0.0
    return math.sqrt(6.0 * n * (n - 1) / ((n - 2) * (n + 1) * (n + 3)))


def curtosis(valores):
    """Curtosis de exceso (la misma que informa SPSS)."""
    n = len(valores)
    if n < 4:
        return 0.0
    desviacion = statistics.stdev(valores)
    if desviacion == 0:
        return 0.0
    media = statistics.fmean(valores)
    suma = sum(((v - media) / desviacion) ** 4 for v in valores)
    a = n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
    b = 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return a * suma - b


def error_curtosis(n):
    if n < 4:
        return 0.0
    return 2.0 * error_asimetria(n) * math.sqrt((n * n - 1) / ((n - 3) * (n + 5)))


def mostrar_descriptivos(valores, nombre="Variable", con_interpretacion=True):
    d = descriptivos(valores)
    decir()
    decir(f"  {nombre}")
    decir(f"  {'-' * 58}")
    dato("n (casos validos)", d["n"])
    dato("Media", f"{d['media']:.4f}")
    dato("Mediana", f"{d['mediana']:.4f}")
    dato("Desviacion estandar", f"{d['desviacion']:.4f}")
    dato("Varianza", f"{d['varianza']:.4f}")
    dato("Error estandar", f"{d['error_estandar']:.4f}")
    dato("Coeficiente de variacion", f"{d['cv']:.2f}", " %")
    dato("Minimo", f"{d['minimo']:.4f}")
    dato("Maximo", f"{d['maximo']:.4f}")
    dato("Rango", f"{d['rango']:.4f}")
    decir(f"  {'IC 95% de la media':<30} "
          f"[{d['ic_inferior']:.4f} ; {d['ic_superior']:.4f}]")
    dato("Asimetria", f"{d['asimetria']:.4f}")
    dato("Curtosis", f"{d['curtosis']:.4f}")

    if con_interpretacion:
        decir()
        decir("  Lectura rapida")
        if abs(d["cv"]) < 20:
            decir("    - El coeficiente de variacion es bajo: los datos son homogeneos.")
        elif abs(d["cv"]) < 33:
            decir("    - El coeficiente de variacion es medio: dispersion moderada.")
        else:
            decir("    - El coeficiente de variacion es alto: los datos son dispersos.")

        z_asim = d["asimetria"] / d["error_asimetria"] if d["error_asimetria"] else 0.0
        z_curt = d["curtosis"] / d["error_curtosis"] if d["error_curtosis"] else 0.0
        if abs(z_asim) <= 1.96 and abs(z_curt) <= 1.96:
            decir("    - Asimetria y curtosis dentro de lo esperado (|z| <= 1.96):")
            decir("      la distribucion es compatible con una normal.")
        else:
            decir("    - Asimetria o curtosis fuera de lo esperado (|z| > 1.96):")
            decir("      la distribucion se aleja de la normal; usa pruebas no")
            decir("      parametricas (U de Mann-Whitney, H de Kruskal-Wallis,")
            decir("      Rho de Spearman) o revisa valores atipicos.")
    return d


def prueba_t_independiente(a, b):
    """t de Student para dos muestras independientes, mas Welch y F de varianzas."""
    n1, n2 = len(a), len(b)
    media1, media2 = statistics.fmean(a), statistics.fmean(b)
    var1 = statistics.variance(a)
    var2 = statistics.variance(b)

    var_comun = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    error = math.sqrt(var_comun * (1.0 / n1 + 1.0 / n2))
    t = (media1 - media2) / error if error else 0.0
    gl = n1 + n2 - 2
    p = p_valor_t(t, gl)

    # Prueba F de igualdad de varianzas (la que acompana a la t clasica)
    if var1 >= var2 and var2 > 0:
        f, gl_f1, gl_f2 = var1 / var2, n1 - 1, n2 - 1
    elif var2 > 0:
        f, gl_f1, gl_f2 = var2 / var1, n2 - 1, n1 - 1
    else:
        f, gl_f1, gl_f2 = 1.0, 1, 1
    # A dos colas: se contrasta si una varianza es mayor O menor que la otra.
    p_f = min(1.0, 2.0 * p_valor_f(f, gl_f1, gl_f2))

    # Welch, por si las varianzas no son iguales
    denominador = var1 / n1 + var2 / n2
    t_welch = (media1 - media2) / math.sqrt(denominador) if denominador else 0.0
    if n1 > 1 and n2 > 1 and denominador:
        gl_welch = denominador ** 2 / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1))
    else:
        gl_welch = 1.0
    p_welch = p_valor_t(t_welch, gl_welch)

    # D de Cohen para el tamano del efecto
    d_cohen = (media1 - media2) / math.sqrt(var_comun) if var_comun else 0.0

    return {
        "n1": n1, "n2": n2,
        "media1": media1, "media2": media2,
        "var1": var1, "var2": var2,
        "desv1": math.sqrt(var1), "desv2": math.sqrt(var2),
        "gl": gl, "t": t, "p": p,
        "f": f, "p_f": p_f, "gl_f1": gl_f1, "gl_f2": gl_f2,
        "t_welch": t_welch, "gl_welch": gl_welch, "p_welch": p_welch,
        "d_cohen": d_cohen,
        "diferencia": media1 - media2,
        "ic_inferior": (media1 - media2) - t_critico(gl) * error,
        "ic_superior": (media1 - media2) + t_critico(gl) * error,
    }


def prueba_t_pareada(antes, despues):
    """t de Student para muestras relacionadas (antes y despues)."""
    diferencias = [d - a for a, d in zip(antes, despues)]
    n = len(diferencias)
    media_d = statistics.fmean(diferencias)
    desv_d = statistics.stdev(diferencias) if n > 1 else 0.0
    error = desv_d / math.sqrt(n) if n else 0.0
    t = media_d / error if error else 0.0
    gl = n - 1
    p = p_valor_t(t, gl)
    d_cohen = media_d / desv_d if desv_d else 0.0

    return {
        "n": n, "media_d": media_d, "desv_d": desv_d,
        "gl": gl, "t": t, "p": p, "d_cohen": d_cohen,
        "ic_inferior": media_d - t_critico(gl) * error,
        "ic_superior": media_d + t_critico(gl) * error,
    }


def anova(*grupos):
    """ANOVA de un factor."""
    k = len(grupos)
    n_total = sum(len(g) for g in grupos)
    gran_media = sum(sum(g) for g in grupos) / n_total
    gl_entre = k - 1
    gl_dentro = n_total - k

    ss_entre = sum(len(g) * (statistics.fmean(g) - gran_media) ** 2 for g in grupos)
    ss_dentro = sum(sum((v - statistics.fmean(g)) ** 2 for v in g) for g in grupos)
    ss_total = ss_entre + ss_dentro

    ms_entre = ss_entre / gl_entre if gl_entre else 0.0
    ms_dentro = ss_dentro / gl_dentro if gl_dentro else 0.0
    f = ms_entre / ms_dentro if ms_dentro else 0.0
    p = p_valor_f(f, gl_entre, gl_dentro)

    return {
        "k": k, "n": n_total,
        "gl_entre": gl_entre, "gl_dentro": gl_dentro,
        "ss_entre": ss_entre, "ss_dentro": ss_dentro, "ss_total": ss_total,
        "ms_entre": ms_entre, "ms_dentro": ms_dentro,
        "f": f, "p": p,
        "eta2": ss_entre / ss_total if ss_total else 0.0,
    }


def comparaciones_por_pares(grupos, etiquetas):
    """t de Student por pares con correccion de Bonferroni."""
    parejas = []
    cuantas = len(etiquetas) * (len(etiquetas) - 1) / 2
    for i in range(len(etiquetas)):
        for j in range(i + 1, len(etiquetas)):
            a, b = grupos[i], grupos[j]
            if len(a) < 2 or len(b) < 2:
                continue
            resultado = prueba_t_independiente(a, b)
            p_ajustado = min(1.0, resultado["p"] * cuantas)
            parejas.append({
                "a": etiquetas[i], "b": etiquetas[j],
                "diferencia": resultado["diferencia"],
                "p": resultado["p"], "p_ajustado": p_ajustado,
            })
    return parejas


def pearson(x, y):
    n = len(x)
    media_x, media_y = statistics.fmean(x), statistics.fmean(y)
    suma_xy = sum((a - media_x) * (b - media_y) for a, b in zip(x, y))
    suma_x2 = sum((a - media_x) ** 2 for a in x)
    suma_y2 = sum((b - media_y) ** 2 for b in y)
    if suma_x2 == 0 or suma_y2 == 0:
        return 0.0
    return suma_xy / math.sqrt(suma_x2 * suma_y2)


def rangos_con_empates(valores):
    """Rangos de 1 a n promediando los empates."""
    orden = sorted(range(len(valores)), key=lambda i: valores[i])
    rangos = [0.0] * len(valores)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and valores[orden[j + 1]] == valores[orden[i]]:
            j += 1
        promedio = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            rangos[orden[k]] = promedio
        i = j + 1
    return rangos


def spearman(x, y):
    return pearson(rangos_con_empates(x), rangos_con_empates(y))


def fuerza_correlacion(r):
    """Escala de interpretacion clasica en tesis."""
    a = abs(r)
    if a < 0.10:
        return "muy debil o nula"
    if a < 0.30:
        return "debil"
    if a < 0.50:
        return "moderada"
    if a < 0.70:
        return "moderada a fuerte"
    if a < 0.90:
        return "fuerte"
    return "muy fuerte"


def nivel_alfa(alfa):
    """Palabra que describe la magnitud del alfa de Cronbach."""
    if alfa >= 0.90:
        return "excelente"
    if alfa >= 0.80:
        return "buena"
    if alfa >= 0.70:
        return "aceptable"
    if alfa >= 0.60:
        return "cuestionable"
    return "insuficiente"


def alfa_cronbach(matriz):
    """Alfa de Cronbach e indicadores por item. Filas = sujetos, columnas = items."""
    n = len(matriz)
    k = len(matriz[0])
    var_items = [statistics.variance([fila[j] for fila in matriz]) for j in range(k)]
    totales = [sum(fila) for fila in matriz]
    var_total = statistics.variance(totales)

    alfa = (k / (k - 1)) * (1.0 - sum(var_items) / var_total) if var_total else 0.0

    detalle = []
    for j in range(k):
        otros = [sum(fila[i] for i in range(k) if i != j) for fila in matriz]
        if k > 2:
            var_resto = statistics.variance(otros)
            alfa_sin = ((k - 1) / (k - 2)) * (1.0 - (sum(var_items) - var_items[j]) / var_resto) \
                if var_resto else 0.0
        else:
            alfa_sin = 0.0
        item = [fila[j] for fila in matriz]
        detalle.append({
            "item": j + 1,
            "media": statistics.fmean(item),
            "desviacion": math.sqrt(var_items[j]),
            "item_total": pearson(item, otros),
            "alfa_sin": alfa_sin,
        })

    return {"n": n, "k": k, "alfa": alfa, "detalle": detalle}


# ============================================================
# 4. OPCIONES DEL MENU
# ============================================================

def opcion_tamano_muestra():
    titulo("TAMANO DE MUESTRA")
    decir("  Elige el tipo de estudio:")
    decir("    1. Estimar una media (una sola poblacion)")
    decir("    2. Estimar una proporcion (una sola poblacion)")
    decir("    3. Comparar dos medias (dos grupos)")
    decir("    4. Comparar dos proporciones (dos grupos)")

    opcion = preguntar("Tipo", "1")
    confianza = preguntar_flotante("Nivel de confianza (0.90, 0.95 o 0.99)",
                                   0.95, 0.50, 0.9999)
    z_alfa = z_confianza(confianza)

    if opcion == "1":
        desviacion = preguntar_flotante("Desviacion estandar esperada (S)", None, 0.0000001)
        error = preguntar_flotante("Error de precision aceptable (E)", None, 0.0000001)
        n = (z_alfa * desviacion / error) ** 2
        formula = "n = (Z * S / E)^2"

    elif opcion == "2":
        proporcion = preguntar_flotante("Proporcion esperada (p, entre 0 y 1)",
                                        None, 0.000001, 0.999999)
        error = preguntar_flotante("Error de precision aceptable (E)", None, 0.0000001)
        n = (z_alfa ** 2) * proporcion * (1 - proporcion) / (error ** 2)
        formula = "n = Z^2 * p * q / E^2"

    elif opcion == "3":
        desviacion = preguntar_flotante("Desviacion estandar esperada (S)", None, 0.0000001)
        diferencia = preguntar_flotante("Diferencia minima que quieres detectar (d)",
                                        None, 0.0000001)
        potencia = preguntar_flotante("Potencia estadistica (0.80 o 0.90)", 0.80, 0.50, 0.9999)
        z_beta = z_potencia(potencia)
        n = 2 * ((z_alfa + z_beta) ** 2) * (desviacion ** 2) / (diferencia ** 2)
        formula = "n por grupo = 2 * (Z_alfa + Z_beta)^2 * S^2 / d^2"

    elif opcion == "4":
        p1 = preguntar_flotante("Proporcion esperada en el grupo 1 (p1, 0 a 1)",
                                None, 0.000001, 0.999999)
        p2 = preguntar_flotante("Proporcion esperada en el grupo 2 (p2, 0 a 1)",
                                None, 0.000001, 0.999999)
        potencia = preguntar_flotante("Potencia estadistica (0.80 o 0.90)", 0.80, 0.50, 0.9999)
        z_beta = z_potencia(potencia)
        p_promedio = (p1 + p2) / 2.0
        diferencia = abs(p1 - p2)
        if diferencia == 0:
            decir("  Las dos proporciones no pueden ser iguales.")
            return
        n = 2 * p_promedio * (1 - p_promedio) * ((z_alfa + z_beta) ** 2) / (diferencia ** 2)
        formula = "n por grupo = 2 * p_promedio * q_promedio * (Z_alfa + Z_beta)^2 / (p1-p2)^2"

    else:
        decir("  Opcion no valida.")
        return

    n_redondeado = math.ceil(n)

    subtitulo("RESULTADO")
    dato("Formula usada", formula)
    dato("Nivel de confianza", f"{confianza * 100:.1f}", " %")
    dato("Valor Z", f"{z_alfa:.4f}")
    dato("Tamano calculado (exacto)", f"{n:.4f}")
    dato("Tamano a usar (redondeado)", n_redondeado)

    poblacion = preguntar_flotante(
        "Tamano de la poblacion (N) si es finita, o 0 si es ilimitada", 0, 0)
    base = n_redondeado
    if poblacion > 0:
        if poblacion < n_redondeado:
            decir()
            decir("  Aviso: la poblacion es menor que la muestra calculada.")
            decir("  Corresponde trabajar con toda la poblacion (censo).")
            base = int(poblacion)
        else:
            base = math.ceil(n_redondeado / (1.0 + (n_redondeado - 1.0) / poblacion))
        subtitulo("AJUSTE POR POBLACION FINITA")
        decir("  n ajustado = n / (1 + (n - 1) / N)")
        dato("Poblacion (N)", f"{int(poblacion)}")
        dato("Tamano ajustado", base)
        decir()
        decir(f"  CONCLUSION: necesitas {base} unidades de analisis.")

        if preguntar_si_no("Quieres repartirlo entre estratos o grupos", "n"):
            cuantos = preguntar_entero("Cuantos estratos o grupos", 2, 2, 100)
            por_grupo = math.ceil(base / cuantos)
            dato("Casos por grupo", f"{por_grupo} (repartidos en {cuantos} grupos)")
    else:
        decir()
        decir(f"  CONCLUSION: necesitas {base} unidades de analisis.")

    decir()
    decir("  Recuerda: suma las perdidas (cuestionarios incompletos, ausencias).")
    if preguntar_si_no("Quieres agregar un porcentaje por perdidas", "n"):
        perdida = preguntar_flotante("Porcentaje de perdidas (por ejemplo 10)", 10, 0, 90)
        ajustado = math.ceil(base / (1.0 - perdida / 100.0))
        dato(f"Ajustando {base} por {perdida:.0f}% de perdidas", ajustado)


def opcion_descriptivos():
    titulo("DESCRIPTIVOS")
    valores = pedir_columna("Escribe los datos de tu variable:")
    if not valores:
        return
    nombre = preguntar("Nombre de la variable", "Variable") or "Variable"
    mostrar_descriptivos(valores, nombre)


def opcion_prueba_t():
    titulo("COMPARAR DOS GRUPOS (PRUEBA T)")
    decir("    1. Grupos independientes (dos grupos distintos de personas)")
    decir("    2. Muestras relacionadas (los mismos antes y despues)")

    tipo = preguntar("Tipo", "1")
    if tipo == "2":
        antes = pedir_columna("Datos del ANTES (o del primer momento):")
        if not antes:
            return
        despues = pedir_columna("Datos del DESPUES (o del segundo momento):")
        if not despues:
            return
        if len(antes) != len(despues):
            decir()
            decir(f"  En una prueba pareada deben ser los mismos casos:")
            decir(f"  antes tiene {len(antes)} y despues {len(despues)}.")
            decir("  Revisa los datos y vuelve a intentarlo.")
            return

        mostrar_descriptivos(antes, "Momento 1 (antes)", False)
        mostrar_descriptivos(despues, "Momento 2 (despues)", False)

        r = prueba_t_pareada(antes, despues)
        subtitulo("PRUEBA T PARA MUESTRAS RELACIONADAS")
        dato("n de pares", r["n"])
        dato("Diferencia media", f"{r['media_d']:.4f}")
        dato("Desviacion de las diferencias", f"{r['desv_d']:.4f}")
        decir(f"  {'IC 95% de la diferencia':<30} "
              f"[{r['ic_inferior']:.4f} ; {r['ic_superior']:.4f}]")
        dato("Grados de libertad", r["gl"])
        dato("Estadistico t", f"{r['t']:.4f}")
        dato("Valor p (dos colas)", f"{r['p']:.6f}")
        dato("d de Cohen", f"{r['d_cohen']:.4f}")
        conclusion(r["p"], "los dos momentos", "las medias del antes y el despues")

    else:
        a = pedir_columna("Datos del GRUPO 1:")
        if not a:
            return
        b = pedir_columna("Datos del GRUPO 2:")
        if not b:
            return
        nombre1 = preguntar("Nombre del grupo 1", "Grupo 1") or "Grupo 1"
        nombre2 = preguntar("Nombre del grupo 2", "Grupo 2") or "Grupo 2"

        mostrar_descriptivos(a, nombre1, False)
        mostrar_descriptivos(b, nombre2, False)

        r = prueba_t_independiente(a, b)
        subtitulo("PRUEBA F DE IGUALDAD DE VARIANZAS (razon de varianzas)")
        dato("Estadistico F", f"{r['f']:.4f}")
        dato("Grados de libertad", f"{r['gl_f1']}, {r['gl_f2']}")
        dato("Valor p", f"{r['p_f']:.6f}")
        if r["p_f"] < 0.05:
            decir()
            decir("  Las varianzas son distintas (p < 0.05): usa la t de WELCH.")
        else:
            decir()
            decir("  No hay evidencia de varianzas distintas (p >= 0.05):")
            decir("  usa la t de STUDENT, que es la que se informa normalmente.")
        decir()
        decir("  Nota: esta prueba F supone datos normales. Si los tuyos no lo")
        decir("  son, la prueba de Levene es mas robusta y la opcion segura es")
        decir("  informar directamente la t de Welch.")

        subtitulo("PRUEBA T DE STUDENT (varianzas iguales)")
        dato("Diferencia de medias", f"{r['diferencia']:.4f}")
        decir(f"  {'IC 95% de la diferencia':<30} "
              f"[{r['ic_inferior']:.4f} ; {r['ic_superior']:.4f}]")
        dato("Grados de libertad", r["gl"])
        dato("Estadistico t", f"{r['t']:.4f}")
        dato("Valor p (dos colas)", f"{r['p']:.6f}")
        dato("d de Cohen", f"{r['d_cohen']:.4f}")

        subtitulo("PRUEBA T DE WELCH (varianzas distintas)")
        dato("Grados de libertad", f"{r['gl_welch']:.2f}")
        dato("Estadistico t", f"{r['t_welch']:.4f}")
        dato("Valor p (dos colas)", f"{r['p_welch']:.6f}")

        decir()
        decir("  Tamano del efecto (d de Cohen):")
        decir("    0.20 = pequeno | 0.50 = mediano | 0.80 = grande")

        usado = r["p_welch"] if r["p_f"] < 0.05 else r["p"]
        conclusion(usado, nombre1 + " y " + nombre2,
                   f"las medias de {nombre1} y {nombre2}")


def conclusion(p, etiqueta, que_se_compara):
    decir()
    decir("  CONCLUSION")
    if p < 0.05:
        decir(f"    Valor p = {p:.6f} < 0.05: hay diferencia estadisticamente")
        decir(f"    significativa entre {que_se_compara}.")
        decir("    Se rechaza la hipotesis nula (H0) y se acepta la alternativa.")
    else:
        decir(f"    Valor p = {p:.6f} >= 0.05: NO hay diferencia estadisticamente")
        decir(f"    significativa entre {que_se_compara}.")
        decir("    No se rechaza la hipotesis nula (H0).")
    decir()
    decir("  Redaccion sugerida:")
    if p < 0.05:
        decir(f"    \"Se encontro diferencia significativa entre {etiqueta} "
              f"(p = {p:.4f}).\"")
    else:
        decir(f"    \"No se encontro diferencia significativa entre {etiqueta} "
              f"(p = {p:.4f}).\"")


def opcion_anova():
    titulo("COMPARAR MAS DE DOS GRUPOS (ANOVA)")
    cuantos = preguntar_entero("Cuantos grupos vas a comparar", 3, 3, 20)

    grupos, etiquetas = [], []
    for i in range(cuantos):
        valores = pedir_columna(f"Datos del GRUPO {i + 1}:")
        if not valores:
            return
        nombre = preguntar(f"Nombre del grupo {i + 1}", f"Grupo {i + 1}") or f"Grupo {i + 1}"
        grupos.append(valores)
        etiquetas.append(nombre)

    for nombre, valores in zip(etiquetas, grupos):
        mostrar_descriptivos(valores, nombre, False)

    r = anova(*grupos)
    subtitulo("TABLA DE ANOVA DE UN FACTOR")
    decir(f"  {'Fuente':<14}{'SC':>12}{'gl':>6}{'CM':>12}{'F':>10}{'p':>12}")
    decir("  " + "-" * 62)
    decir(f"  {'Entre grupos':<14}{r['ss_entre']:>12.4f}{r['gl_entre']:>6}"
          f"{r['ms_entre']:>12.4f}{r['f']:>10.4f}{r['p']:>12.6f}")
    decir(f"  {'Dentro':<14}{r['ss_dentro']:>12.4f}{r['gl_dentro']:>6}"
          f"{r['ms_dentro']:>12.4f}{'':>10}{'':>12}")
    decir(f"  {'Total':<14}{r['ss_total']:>12.4f}{r['gl_entre'] + r['gl_dentro']:>6}")
    decir()
    dato("Eta cuadrado (tamano del efecto)", f"{r['eta2']:.4f}")

    decir()
    if r["p"] < 0.05:
        decir(f"  Valor p = {r['p']:.6f} < 0.05: SI hay diferencias significativas")
        decir("  entre al menos dos de los grupos.")
        if r["eta2"] < 0.06:
            decir(f"  Eta cuadrado = {r['eta2']:.3f}: efecto pequeno.")
        elif r["eta2"] < 0.14:
            decir(f"  Eta cuadrado = {r['eta2']:.3f}: efecto mediano.")
        else:
            decir(f"  Eta cuadrado = {r['eta2']:.3f}: efecto grande.")

        parejas = comparaciones_por_pares(grupos, etiquetas)
        if parejas:
            subtitulo("COMPARACIONES POR PARES (con correccion de Bonferroni)")
            decir(f"  {'Par':<34}{'Diferencia':>12}{'p':>11}{'p ajustado':>12}")
            decir("  " + "-" * 68)
            for p in parejas:
                par = f"{p['a']} vs {p['b']}"
                marca = " *" if p["p_ajustado"] < 0.05 else ""
                decir(f"  {par[:33]:<34}{p['diferencia']:>12.4f}"
                      f"{p['p']:>11.4f}{p['p_ajustado']:>12.4f}{marca}")
            decir()
            decir("  (*) El par marcado tiene diferencia significativa despues de")
            decir("      ajustar por el numero de comparaciones.")
    else:
        decir(f"  Valor p = {r['p']:.6f} >= 0.05: NO hay diferencias significativas")
        decir("  entre los grupos.")
        decir("  No hace falta revisar las comparaciones por pares.")

    decir()
    decir("  Nota: la ANOVA pide varianzas parecidas y datos sin sesgo fuerte.")
    decir("  Si los datos se alejan de la normal, usa la prueba H de Kruskal-Wallis.")


def opcion_correlacion():
    titulo("RELACION ENTRE DOS VARIABLES (CORRELACION)")
    x = pedir_columna("Datos de la PRIMERA variable (X):")
    if not x:
        return
    y = pedir_columna("Datos de la SEGUNDA variable (Y):")
    if not y:
        return
    if len(x) != len(y):
        decir()
        decir("  Las dos variables deben tener el mismo numero de casos:")
        decir(f"  X tiene {len(x)} y Y tiene {len(y)}. Se cancela el calculo.")
        return

    nombre_x = preguntar("Nombre de X", "Variable X") or "Variable X"
    nombre_y = preguntar("Nombre de Y", "Variable Y") or "Variable Y"

    r = pearson(x, y)
    rho = spearman(x, y)
    n = len(x)

    if abs(r) < 1.0:
        t = r * math.sqrt((n - 2) / (1 - r ** 2))
        p = p_valor_t(t, n - 2)
    else:
        t, p = float("inf"), 0.0

    if abs(rho) < 1.0:
        t_rho = rho * math.sqrt((n - 2) / (1 - rho ** 2))
        p_rho = p_valor_t(t_rho, n - 2)
    else:
        p_rho = 0.0

    subtitulo("RESULTADOS")
    decir(f"  Variables: {nombre_x} (X) y {nombre_y} (Y)")
    dato("n de casos", n)
    decir()
    decir("  PEARSON (relacion lineal; pide datos normales)")
    dato("Coeficiente r", f"{r:.4f}")
    dato("Significancia p (dos colas)", f"{p:.6f}")
    dato("Coeficiente de determinacion r2", f"{r ** 2:.4f}")
    dato("Fuerza de la relacion", fuerza_correlacion(r))
    decir()
    decir("  SPEARMAN (por rangos; usa esta si los datos no son normales")
    decir("  o si tienes variables ordinales)")
    dato("Coeficiente rho", f"{rho:.4f}")
    dato("Significancia p (dos colas)", f"{p_rho:.6f}")
    dato("Fuerza de la relacion", fuerza_correlacion(rho))

    decir()
    decir("  INTERPRETACION")
    if abs(r) >= 0.70 and abs(rho) >= 0.70:
        decir("    Pearson y Spearman coinciden: la relacion es consistente.")
    elif abs(r - rho) > 0.20:
        decir("    Pearson y Spearman difieren bastante: puede haber valores")
        decir("    atipicos o la relacion no es lineal. Informa Spearman.")
    else:
        decir("    Los dos coeficientes apuntan en el mismo sentido.")

    sentido = "directa (cuando una sube, la otra tambien)" if r > 0 \
        else "inversa (cuando una sube, la otra baja)"

    if p < 0.05:
        decir(f"    La correlacion es significativa (p = {p:.4f} < 0.05), de tipo")
        decir(f"    {sentido}, y su fuerza es {fuerza_correlacion(r)}.")
        decir(f"    r2 = {r ** 2:.4f} significa que {r ** 2 * 100:.1f} % de la variacion")
        decir(f"    de {nombre_y} se explica por {nombre_x}.")
    else:
        decir(f"    La correlacion NO es significativa (p = {p:.4f} >= 0.05).")
        decir("    No se puede afirmar que exista relacion entre las variables.")

    decir()
    decir("  Ojo: correlacion no es causa. Que dos cosas se muevan juntas")
    decir("  no prueba que una cause la otra.")


def opcion_cronbach():
    titulo("CONFIABILIDAD DE UN CUESTIONARIO (ALFA DE CRONBACH)")
    decir("  Necesitas la matriz de respuestas: una fila por encuestado y")
    decir("  una columna por item. Ejemplo con 4 items y 3 encuestados:")
    decir()
    decir("      4, 5, 3, 4")
    decir("      5, 5, 4, 4")
    decir("      3, 4, 3, 3")

    k = preguntar_entero("Cuantos items (preguntas) tiene tu instrumento", None, 2, 200)
    if k < 2:
        decir("  Se necesitan al menos 2 items.")
        return

    matriz = pedir_matriz(k, "Pega las respuestas de tus encuestados:")
    if not matriz:
        return

    r = alfa_cronbach(matriz)
    subtitulo("RESULTADOS")
    dato("Encuestados validos", r["n"])
    dato("Numero de items", r["k"])
    decir()
    decir(f"  ALFA DE CRONBACH = {r['alfa']:.4f}")

    decir()
    decir("  Criterio de lectura:")
    if r["alfa"] >= 0.90:
        decir("    Excelente (>= 0.90). El instrumento es muy consistente.")
    elif r["alfa"] >= 0.80:
        decir("    Buena (0.80 a 0.89). El instrumento es confiable.")
    elif r["alfa"] >= 0.70:
        decir("    Aceptable (0.70 a 0.79). Sirve para investigacion.")
    elif r["alfa"] >= 0.60:
        decir("    Cuestionable (0.60 a 0.69). Revisa los items flojos.")
    else:
        decir("    Insuficiente (< 0.60). Hay que rehacer o depurar el instrumento.")

    subtitulo("DETALLE POR ITEM")
    decir(f"  {'Item':<8}{'Media':>10}{'Desv.':>10}{'Item-total':>13}{'Alfa si se quita':>19}")
    decir("  " + "-" * 62)
    for d in r["detalle"]:
        decir(f"  {d['item']:<8}{d['media']:>10.3f}{d['desviacion']:>10.3f}"
              f"{d['item_total']:>13.4f}{d['alfa_sin']:>19.4f}")

    decir()
    decir("  Como leer el detalle:")
    decir("    - 'Item-total' menor a 0.30: ese item no mide lo mismo que el")
    decir("      resto. Candidato a eliminarlo o reescribirlo.")
    decir("    - 'Alfa si se quita' mayor que el alfa general: el instrumento")
    decir("      mejora si eliminas ese item.")

    candidatos = [d["item"] for d in r["detalle"]
                  if d["item_total"] < 0.30 or d["alfa_sin"] > r["alfa"]]
    if candidatos:
        lista = ", ".join(str(c) for c in candidatos)
        decir()
        decir(f"  Items a revisar: {lista}")
    else:
        decir()
        decir("  Ningun item desmejora el instrumento. Todos aportan.")

    decir()
    decir(f"  Redaccion sugerida:")
    decir(f"    \"El instrumento obtuvo un alfa de Cronbach de {r['alfa']:.3f},")
    decir(f"     lo que indica una confiabilidad {nivel_alfa(r['alfa'])}.\"")


def opcion_analizar_csv(ruta=None):
    """Lee un CSV, muestra sus columnas y ofrece los analisis posibles."""
    titulo("ANALIZAR MI ARCHIVO DE DATOS")

    if ruta is None:
        decir("  Escribe la ruta de tu archivo .csv")
        decir("  (si esta en la misma carpeta, basta el nombre: mis_datos.csv)")
        ruta = preguntar("Archivo")
        if not ruta:
            return
    ruta = Path(str(ruta).strip().strip('"').strip("'"))

    if not ruta.exists():
        decir()
        decir(f"  No encuentro el archivo: {ruta}")
        decir("  Revisa la ruta o pega el archivo en esta misma carpeta.")
        return

    try:
        filas, delimitador = leer_csv(ruta)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        decir()
        decir(f"  No se pudo leer el archivo: {error}")
        decir("  Guardalo como CSV UTF-8 (delimitado por comas).")
        return

    if not filas:
        decir("  El archivo esta vacio.")
        return

    columnas = list(filas[0].keys())
    if len(columnas) < 2:
        decir("  El archivo necesita al menos dos columnas.")
        return

    numericas, categoricas = clasificar_columnas(filas, columnas)

    decir()
    decir(f"  Archivo: {ruta.name}")
    dato("Filas de datos", len(filas))
    dato("Separador detectado", repr(delimitador))
    dato("Columnas", len(columnas))

    subtitulo("COLUMNAS ENCONTRADAS")
    for i, columna in enumerate(numericas, 1):
        valores = numeros_de(filas, columna)
        decir(f"    {i:>2}. [numerica]    {columna}   ({len(valores)} datos)")
    for columna in categoricas:
        distintos = {str(v).strip() for v in valores_de(filas, columna)
                     if str(v).strip() != ""}
        decir(f"        [categoria]   {columna}   ({len(distintos)} grupos)")

    if not numericas:
        decir()
        decir("  No encontre ninguna columna numerica. Revisa los decimales:")
        decir("  deben ser numeros, no texto.")
        return

    subtitulo("QUE QUIERES HACER")
    decir("    1. Descriptivos de una variable")
    decir("    2. Comparar dos grupos (prueba t)")
    decir("    3. Comparar tres o mas grupos (ANOVA)")
    decir("    4. Correlacion entre dos variables")
    decir("    5. Todo lo que se pueda calcular automaticamente")
    decir("    0. Volver al menu")

    eleccion = preguntar("Elige", "1")

    if eleccion == "1":
        columna = elegir_columna(numericas, "Cual es la variable a describir")
        if columna:
            mostrar_descriptivos(numeros_de(filas, columna), columna)

    elif eleccion in ("2", "3"):
        columna_num = elegir_columna(numericas, "Cual es la variable NUMERICA (el resultado)")
        if not columna_num:
            return
        if not categoricas:
            decir()
            decir("  No encontre una columna de grupos (de 2 a 12 categorias).")
            decir("  Si tu columna de grupos tiene numeros, avisame igual:")
            if preguntar_si_no("Quieres elegirla entre las numericas", "n"):
                columna_grupo = elegir_columna(numericas,
                                               "Cual es la variable de GRUPOS")
            else:
                return
        else:
            columna_grupo = elegir_columna(categoricas, "Cual es la variable de GRUPOS")
        if not columna_grupo:
            return

        grupos = grupos_de(filas, columna_grupo, columna_num)
        grupos = {k: v for k, v in grupos.items() if len(v) >= 2}
        if len(grupos) < 2:
            decir()
            decir("  Necesito al menos dos grupos con dos datos cada uno.")
            return

        decir()
        decir(f"  Grupos encontrados para '{columna_grupo}':")
        for etiqueta, valores in grupos.items():
            decir(f"    - {etiqueta}: {len(valores)} casos")

        for etiqueta, valores in grupos.items():
            mostrar_descriptivos(valores, f"{columna_num} en {etiqueta}", False)

        etiquetas = list(grupos.keys())
        if len(grupos) == 2:
            a, b = grupos[etiquetas[0]], grupos[etiquetas[1]]
            r = prueba_t_independiente(a, b)
            subtitulo("PRUEBA F DE IGUALDAD DE VARIANZAS")
            dato("Estadistico F", f"{r['f']:.4f}")
            dato("Valor p", f"{r['p_f']:.6f}")
            subtitulo("PRUEBA T DE STUDENT")
            dato("Diferencia de medias", f"{r['diferencia']:.4f}")
            dato("Grados de libertad", r["gl"])
            dato("Estadistico t", f"{r['t']:.4f}")
            dato("Valor p (dos colas)", f"{r['p']:.6f}")
            dato("d de Cohen", f"{r['d_cohen']:.4f}")
            subtitulo("PRUEBA T DE WELCH")
            dato("Grados de libertad", f"{r['gl_welch']:.2f}")
            dato("Estadistico t", f"{r['t_welch']:.4f}")
            dato("Valor p (dos colas)", f"{r['p_welch']:.6f}")
            usado = r["p_welch"] if r["p_f"] < 0.05 else r["p"]
            conclusion(usado, f"{etiquetas[0]} y {etiquetas[1]}",
                       f"las medias de {etiquetas[0]} y {etiquetas[1]}")
        else:
            r = anova(*[grupos[e] for e in etiquetas])
            subtitulo("TABLA DE ANOVA DE UN FACTOR")
            decir(f"  {'Fuente':<14}{'SC':>12}{'gl':>6}{'CM':>12}{'F':>10}{'p':>12}")
            decir("  " + "-" * 62)
            decir(f"  {'Entre grupos':<14}{r['ss_entre']:>12.4f}{r['gl_entre']:>6}"
                  f"{r['ms_entre']:>12.4f}{r['f']:>10.4f}{r['p']:>12.6f}")
            decir(f"  {'Dentro':<14}{r['ss_dentro']:>12.4f}{r['gl_dentro']:>6}"
                  f"{r['ms_dentro']:>12.4f}{'':>10}{'':>12}")
            dato("Eta cuadrado", f"{r['eta2']:.4f}")
            if r["p"] < 0.05:
                parejas = comparaciones_por_pares([grupos[e] for e in etiquetas], etiquetas)
                if parejas:
                    subtitulo("COMPARACIONES POR PARES (Bonferroni)")
                    for p in parejas:
                        marca = " *" if p["p_ajustado"] < 0.05 else ""
                        decir(f"  {p['a']} vs {p['b']}: "
                              f"diferencia {p['diferencia']:.4f}, "
                              f"p ajustado {p['p_ajustado']:.4f}{marca}")
            conclusion(r["p"], "los grupos", "al menos dos de los grupos")

    elif eleccion == "4":
        if len(numericas) < 2:
            decir("  Necesito al menos dos columnas numericas para correlacionar.")
            return
        col_x = elegir_columna(numericas, "Primera variable (X)")
        if not col_x:
            return
        col_y = elegir_columna(numericas, "Segunda variable (Y)")
        if not col_y:
            return
        if col_x == col_y:
            decir("  Elegiste la misma columna dos veces.")
            return
        x, y = numeros_de(filas, col_x), numeros_de(filas, col_y)
        if len(x) != len(y):
            decir()
            decir(f"  Hay celdas vacias: {col_x} tiene {len(x)} datos y "
                  f"{col_y} tiene {len(y)}.")
            decir("  La correlacion necesita pares completos. Se cancela.")
            return
        r = pearson(x, y)
        rho = spearman(x, y)
        n = len(x)
        p = p_valor_t(r * math.sqrt((n - 2) / (1 - r ** 2)), n - 2) if abs(r) < 1 else 0.0
        subtitulo("CORRELACION")
        dato("n de casos", n)
        dato("Pearson r", f"{r:.4f}")
        dato("Valor p de r", f"{p:.6f}")
        dato("Coeficiente de determinacion r2", f"{r ** 2:.4f}")
        dato("Spearman rho", f"{rho:.4f}")
        dato("Fuerza de la relacion", fuerza_correlacion(r))
        if p < 0.05:
            decir()
            decir(f"  Hay correlacion significativa entre {col_x} y {col_y}.")
        else:
            decir()
            decir(f"  No hay correlacion significativa entre {col_x} y {col_y}.")

    elif eleccion == "5":
        decir()
        decir("  MODO AUTOMATICO")
        decir("  Se calculan los descriptivos de cada columna numerica y las")
        decir("  correlaciones entre todas ellas.")
        for columna in numericas:
            mostrar_descriptivos(numeros_de(filas, columna), columna, False)
        if len(numericas) >= 2:
            subtitulo("MATRIZ DE CORRELACIONES DE PEARSON")
            encabezado = "  " + " " * 20 + "".join(f"{c[:10]:>12}" for c in numericas)
            decir(encabezado)
            for i, col_i in enumerate(numericas):
                xi = numeros_de(filas, col_i)
                linea = f"  {col_i[:18]:<20}"
                for j, col_j in enumerate(numericas):
                    if j > i:
                        linea += f"{'':>12}"
                        continue
                    xj = numeros_de(filas, col_j)
                    if len(xi) != len(xj):
                        linea += f"{'--':>12}"
                    else:
                        linea += f"{pearson(xi, xj):>12.3f}"
                decir(linea)
            decir()
            decir("  Cada celda es el coeficiente r entre dos columnas.")
        if categoricas:
            subtitulo("COLUMNAS DE GRUPOS DISPONIBLES")
            for columna in categoricas:
                distintos = sorted({str(v).strip() for v in valores_de(filas, columna)
                                    if str(v).strip() != ""})
                decir(f"  {columna}: {', '.join(distintos[:12])}")
            decir()
            decir("  Para comparar grupos, vuelve a entrar y elige la opcion 2 o 3.")

    elif eleccion == "0":
        return
    else:
        decir("  Opcion no valida.")


def elegir_columna(columnas, etiqueta):
    """Muestra una lista numerada de columnas y devuelve la elegida."""
    decir()
    decir(f"  {etiqueta}:")
    for i, columna in enumerate(columnas, 1):
        decir(f"    {i}. {columna}")
    eleccion = preguntar_entero("Numero de columna", 1, 1, len(columnas))
    return columnas[eleccion - 1]


# ============================================================
# 5. MENU PRINCIPAL
# ============================================================

def mostrar_portada():
    print()
    print("=" * 64)
    print("   ESTADISTICA PARA TESIS")
    print("   Calculos frecuentes de un informe de tesis")
    print(f"   Version {VERSION}  -  no necesita instalar nada")
    print("=" * 64)


def mostrar_menu():
    decir()
    decir("-" * 64)
    decir("  MENU PRINCIPAL")
    decir("-" * 64)
    decir("    1. Tamano de muestra")
    decir("    2. Descriptivos de una variable")
    decir("    3. Comparar dos grupos (prueba t)")
    decir("    4. Comparar tres o mas grupos (ANOVA)")
    decir("    5. Relacion entre dos variables (correlacion)")
    decir("    6. Confiabilidad de un cuestionario (alfa de Cronbach)")
    decir("    7. Analizar mi archivo CSV de datos")
    decir("    8. Guardar los resultados en un archivo .txt")
    decir("    9. Ver la ayuda")
    decir("    0. Salir")


def mostrar_ayuda():
    print(__doc__)


def main():
    argumentos = sys.argv[1:]

    if argumentos and argumentos[0].lower() in ("-h", "--ayuda", "--help", "/?", "help"):
        mostrar_ayuda()
        return 0

    mostrar_portada()

    if argumentos:
        opcion_analizar_csv(argumentos[0])
        decir()
        if preguntar_si_no("Quieres guardar estos resultados en un archivo .txt", "n"):
            guardar_salida()
        pausar()

    while True:
        mostrar_menu()
        try:
            eleccion = input("  Opcion: ").strip()
        except (EOFError, KeyboardInterrupt):
            decir()
            break

        if eleccion == "0":
            decir()
            decir("  Listo. Si te sirvio, comparte el repositorio con tus companeros.")
            break
        elif eleccion == "1":
            opcion_tamano_muestra()
        elif eleccion == "2":
            opcion_descriptivos()
        elif eleccion == "3":
            opcion_prueba_t()
        elif eleccion == "4":
            opcion_anova()
        elif eleccion == "5":
            opcion_correlacion()
        elif eleccion == "6":
            opcion_cronbach()
        elif eleccion == "7":
            opcion_analizar_csv()
        elif eleccion == "8":
            guardar_salida()
        elif eleccion == "9":
            mostrar_ayuda()
            continue
        else:
            decir("  Opcion no valida. Elige un numero del 0 al 9.")
            continue

        if eleccion in ("1", "2", "3", "4", "5", "6", "7"):
            pausar()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  Interrumpido por el usuario.")
        sys.exit(0)
