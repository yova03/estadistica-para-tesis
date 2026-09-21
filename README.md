---
objetivo: "Presentar el repositorio: un programa de estadística para tesis en Python y once colecciones de ejemplos comparativos de lenguajes."
uso: "Leer como portada: qué calcula el programa, cómo se ejecuta sin instalar nada, cómo preparar los datos y qué se verificó."
---

# Estadística para tesis

Un programa de Python que resuelve las cuentas que más se piden en un informe de tesis.

**No hay que instalar nada.** Solo se necesita Python, que ya viene en la mayoría de
computadoras o se instala una vez desde <https://python.org>. No usa pandas, ni numpy,
ni scipy: todo el cálculo está escrito dentro del mismo archivo.

    python estadistica_tesis.py

Eso es todo. Aparece un menú y se elige el cálculo.

---

## Qué calcula

| Opción | Cálculo | Para qué sirve en la tesis |
|---|---|---|
| 1 | **Tamaño de muestra** | Estimar una media, estimar una proporción, comparar dos medias o comparar dos proporciones. Incluye ajuste por población finita y recargo por pérdidas. |
| 2 | **Descriptivos** | Media, mediana, desviación estándar, coeficiente de variación, IC 95 %, asimetría y curtosis, con aviso de normalidad. |
| 3 | **Comparar dos grupos** | Prueba t de Student, para grupos independientes o para muestras relacionadas (antes y después). Informa también la t de Welch y la prueba F de varianzas. |
| 4 | **Comparar tres o más grupos** | ANOVA de un factor con eta cuadrado y comparaciones por pares con corrección de Bonferroni. |
| 5 | **Correlación** | Pearson y Spearman, con el coeficiente de determinación y la fuerza de la relación. |
| 6 | **Confiabilidad** | Alfa de Cronbach, alfa si se elimina el ítem y correlación ítem-total corregida. |
| 7 | **Analizar un CSV** | Lee tu archivo, detecta las columnas solo y ofrece todo lo anterior. |

Cada resultado viene con su lectura en palabras simples y una frase sugerida para
redactar en la tesis.

---

## Cómo empezar

### 1. Ten Python instalado

Comprueba en una terminal:

    python --version

Si dice `Python 3.8` o mayor, ya está. Si no, descárgalo de <https://python.org>
y marca la casilla **"Add Python to PATH"** durante la instalación.

### 2. Descarga el programa

Descarga el repositorio con el botón verde **Code → Download ZIP** y descomprímelo,
o usa git:

    git clone https://github.com/yova03/estadistica-para-tesis.git

### 3. Ejecútalo

Abre una terminal **en la carpeta donde quedó el archivo** y escribe:

    python estadistica_tesis.py

Si prefieres empezar directo con tus datos:

    python estadistica_tesis.py mis_datos.csv

---

## Cómo preparar tus datos

El programa lee archivos **CSV**: un archivo de texto donde cada fila es un caso y
cada columna una variable. La primera fila lleva los nombres.

```csv
id,sitio,peso_g,longitud_mm
1,Sitio A,11.2,46
2,Sitio A,12.4,51
3,Sitio B,14.8,63
```

Si tus datos están en Excel: **Archivo → Guardar como → CSV UTF-8 (delimitado por comas)**.

Sirven tanto los decimales con punto (`11.2`) como con coma (`11,2`), y tanto la coma
como el punto y coma como separador. El programa lo detecta solo.

> **Tus datos no salen de tu computadora.** Todo se calcula localmente, sin conexión.

---

## Cómo se ve

Ejemplo real con `datos/mediciones.csv`, comparando el peso entre dos sitios:

```
----------------------------------------------------------------
  PRUEBA T DE STUDENT (varianzas iguales)
----------------------------------------------------------------
  Diferencia de medias           -3.4000
  IC 95% de la diferencia        [-4.4436 ; -2.3564]
  Grados de libertad             8
  Estadistico t                  -7.5130
  Valor p (dos colas)            0.000068
  d de Cohen                     -4.7516

  CONCLUSION
    Valor p = 0.000068 < 0.05: hay diferencia estadisticamente
    significativa entre las medias de Sitio A y Sitio B.

  Redaccion sugerida:
    "Se encontro diferencia significativa entre Sitio A y Sitio B
     (p = 0.0001)."
```

Opcionalmente, la opción **8** guarda todo lo que se mostró en un archivo
`resultados_estadistica.txt`, listo para copiar al informe.

---

## Las siete opciones, en detalle

<details>
<summary><b>Tamaño de muestra</b></summary>

Cuatro fórmulas, con el valor Z calculado automáticamente:

- Estimar una media: `n = (Z · S / E)²`
- Estimar una proporción: `n = Z² · p · q / E²`
- Comparar dos medias: `n por grupo = 2 · (Z_α + Z_β)² · S² / d²`
- Comparar dos proporciones: `n por grupo = 2 · p̄ · q̄ · (Z_α + Z_β)² / (p₁ − p₂)²`

Pide el nivel de confianza y la potencia, y luego ofrece el ajuste por población
finita `n / (1 + (n−1)/N)`, el reparto entre estratos y el recargo por pérdidas.
</details>

<details>
<summary><b>Descriptivos y normalidad</b></summary>

Además del resumen habitual, informa asimetría y curtosis como las informa SPSS y
compara cada una contra su error estándar. Si `|z| > 1.96`, avisa que los datos se
alejan de la normal y sugiere las pruebas no paramétricas correspondientes.
</details>

<details>
<summary><b>Prueba t y ANOVA</b></summary>

La prueba t se informa en las dos versiones (Student y Welch) junto con la prueba F
de igualdad de varianzas, para que se pueda justificar cuál corresponde usar.
El tamaño del efecto se informa como d de Cohen o eta cuadrado.
</details>

<details>
<summary><b>Alfa de Cronbach</b></summary>

Además del coeficiente, muestra una tabla por ítem con la correlación ítem-total
corregida y cuánto subiría el alfa si se eliminara ese ítem. Los ítems problemáticos
se listan al final.
</details>

---

## Los once ejemplos de lenguajes

El repositorio incluye, en las carpetas `01_python` a `11_jupyter`, **la misma tarea
resuelta en once lenguajes y herramientas**, para comparar cuánto código necesita cada
uno y qué tan legible resulta:

| Carpeta | Lenguaje o herramienta | ¿Se ejecuta sin instalar nada? |
|---|---|---|
| `01_python` | Python (4 ejemplos) | Sí, con Python |
| `02_r` | R | No, requiere R |
| `03_julia` | Julia | No, requiere Julia |
| `04_matlab` | MATLAB / Octave | No, requiere Octave o MATLAB |
| `05_fortran` | Fortran | No, requiere gfortran |
| `06_cpp` | C++ | No, requiere g++ |
| `07_sql` | SQL | Sí, en <https://sqliteonline.com> |
| `08_javascript` | JavaScript | Sí, doble clic en el navegador |
| `09_latex` | LaTeX | Sí, en <https://overleaf.com> |
| `10_quarto` | Quarto | No, requiere Quarto |
| `11_jupyter` | Jupyter | No, requiere Jupyter |

El detalle de cada carpeta está en [`00_LEEME.md`](./00_LEEME.md).

**La conclusión práctica:** Python cubre casi todo el trabajo de una tesis. Las demás
herramientas (C, Fortran, LaTeX) suelen trabajar por debajo sin que haga falta
escribirlas a mano.

---

## Verificación

Las fórmulas no se piden a una librería externa: están escritas dentro del programa.
Por eso se comprueban aparte, contra tablas estadísticas clásicas y contra
`scipy` y `numpy`:

    python pruebas/test_estadistica.py

    PASARON LAS 53 COMPROBACIONES

Se verifican la t de Student, la t de Welch, la F de varianzas, la ANOVA, la t
pareada, Pearson, Spearman, la asimetría, la curtosis, el alfa de Cronbach y todos
los valores críticos y valores p.

---

## Requisitos

- **Python 3.8 o mayor.** Nada más.
- Opcional: `scipy` y `numpy`, solo para ejecutar el archivo de comprobación.

---

## Licencia

MIT. En palabras simples: puedes usar, copiar, modificar y compartir este
programa libremente, incluso con fines comerciales y en trabajos de
investigación y publicaciones. La única condición es mantener el aviso de
autoría. El programa se entrega sin garantía.

El texto legal completo está en [`LICENSE`](./LICENSE) (en inglés, que es la
versión que rige).
