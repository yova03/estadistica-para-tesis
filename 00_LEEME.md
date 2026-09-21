---
objetivo: "Documentar la investigación 02: once ejemplos comparativos de lenguajes de programación y herramientas de documentos aplicados a una misma tarea de análisis de datos."
uso: "Leer como punto de entrada: resumen, pregunta, corpus, método, resultados, cómo ejecutar los ejemplos y limitaciones."
---

# Ejemplos de lenguajes para investigación

## Resumen

El repositorio tiene dos partes.

**Primera: un programa para usar.** `estadistica_tesis.py` resuelve las cuentas que más se piden en un informe de tesis (tamaño de muestra, descriptivos, prueba t, ANOVA, correlación y alfa de Cronbach). Funciona solo con Python, sin instalar librerías, y también analiza el archivo CSV del propio tesista. Detalle en el [README](./README.md).

**Segunda: once colecciones de ejemplos.** Resuelven **la misma tarea** (leer `datos/mediciones.csv`, promediar por grupo, aplicar una prueba t y graficar) en distintos lenguajes y herramientas:

- **Lenguajes de programación:** Python (4 ejemplos), R (2), Julia, MATLAB, Fortran, C++, SQL y JavaScript.
- **Herramientas de documentos:** LaTeX, Quarto y Jupyter (no son lenguajes de programación: sirven para redactar y publicar).

Todos los archivos están comentados en español y declaran cómo ejecutarse. La verificación se hizo el 18 de septiembre de 2026; el programa de estadística se verificó el 21 de septiembre de 2026.

## El programa de estadística

| Elemento | Detalle |
|---|---|
| Archivo | `estadistica_tesis.py` (un solo archivo) |
| Dependencias | Ninguna: solo Python 3.8 o mayor |
| Cálculos | Tamaño de muestra (4 fórmulas), descriptivos con normalidad, prueba t (independiente y pareada), ANOVA con Bonferroni, Pearson y Spearman, alfa de Cronbach, y lectura automática de un CSV |
| Entrada | Teclado (se pegan los datos) o un archivo CSV propio |
| Salida | Pantalla y, si se pide, `resultados_estadistica.txt` |
| Comprobación | `pruebas/test_estadistica.py`: 53 comprobaciones contra tablas clásicas y contra scipy/numpy |


## Pregunta

¿Cuánto cambia el mismo análisis según el lenguaje? ¿Cuál conviene aprender primero cuando el objetivo es investigar y redactar una tesis?

## Corpus

| Elemento | Detalle |
|---|---|
| Datos | `datos/mediciones.csv`: 20 muestras con peso (g) y longitud (mm) de dos sitios |
| Código | Un ejemplo mínimo por lenguaje, en las subcarpetas `01_python` a `11_jupyter` |
| Producto generado | `01_python/grafico_python.png` (barras con barras de error) |

## Método

1. Se escribió el mismo tipo de análisis en cada lenguaje, sin librerías innecesarias.
2. Se ejecutó o validó lo que el entorno permitía: Python 3.12 (pandas, matplotlib, scipy), SQLite para el SQL y Node para la sintaxis del JavaScript.
3. Los lenguajes sin entorno instalado quedaron documentados con su ruta de instalación.

## Resultados

| Carpeta | Contenido | Estado |
|---|---|---|
| `estadistica_tesis.py` | Programa de estadística para tesis | **Ejecutado: 53 comprobaciones correctas** |
| `pruebas/` | Comprobación de las fórmulas contra scipy y numpy | **Ejecutado: todo pasa** |
| `01_python/` | Sin librerías, con pandas, gráfico y prueba t | **Ejecutado: 4 de 4 correctos** |
| `02_r/` | Análisis estadístico y boxplot | Preparado; falta instalar R |
| `03_julia/` | Promedio y desviación estándar | Preparado; falta instalar Julia |
| `04_matlab/` | Tabla, estadísticas y figura | Preparado; requiere MATLAB u Octave |
| `05_fortran/` | Subrutinas y funciones numéricas | Preparado; requiere gfortran |
| `06_cpp/` | Estadísticas con vectores | Preparado; requiere g++ |
| `07_sql/` | Consultas con `GROUP BY` y filtros | **Validado en SQLite** |
| `08_javascript/` | Gráfico interactivo en el navegador | Abrible con doble clic, sin instalar nada |
| `09_latex/` | Fórmula, tabla y referencias automáticas | Probable en Overleaf (navegador) |
| `10_quarto/` | Informe que se regenera al compilar | Preparado; falta instalar Quarto |
| `11_jupyter/` | Cuaderno con cuatro celdas | Preparado; falta instalar Jupyter |

## Cómo probar los ejemplos disponibles

El programa de estadística, desde esta carpeta:

```
python estadistica_tesis.py

python estadistica_tesis.py datos/mediciones.csv
```

Sus comprobaciones internas:

```
python pruebas/test_estadistica.py
```

Los ejemplos de Python, desde esta carpeta, en una terminal:

```
python 01_python/01_sin_librerias.py
python 01_python/02_con_pandas.py
python 01_python/03_grafico.py
python 01_python/04_estadistica.py
```

Sin instalar nada más:

- **JavaScript:** doble clic en `08_javascript/01_grafico.html`.
- **SQL:** pegar `07_sql/01_consultas.sql` en <https://sqliteonline.com>.
- **LaTeX:** pegar `09_latex/01_documento.tex` en <https://overleaf.com>.

## Enlaces de instalación (opcional)

| Herramienta | Enlace |
|---|---|
| R | <https://cran.r-project.org> |
| Julia | <https://julialang.org> |
| Octave (alternativa gratuita a MATLAB) | <https://octave.org> |
| MinGW (compiladores g++ y gfortran) | <https://www.mingw-w64.org> |
| Quarto | <https://quarto.org> |
| MiKTeX (LaTeX) | <https://miktex.org> |
| Jupyter | En terminal: `pip install jupyter` |

## Qué observar al comparar

1. Cuánto código necesita cada lenguaje para la misma tarea.
2. La legibilidad: Python y R se leen casi como inglés; C++ y Fortran son más técnicos.
3. La conclusión práctica: Python cubre casi todo el trabajo; las demás herramientas (C, Fortran, LaTeX) trabajan por debajo sin necesidad de escribirlas a mano.

## Limitaciones

- Los ejemplos de R, Julia, MATLAB, Fortran y C++ no se ejecutaron en esta computadora: sus entornos no están instalados.
- El código de LaTeX no se compiló aquí; su prueba natural es Overleaf o MiKTeX.
- El informe de Quarto y el cuaderno de Jupyter no se renderizaron (faltan Quarto y Jupyter).
- Los datos son sintéticos y pequeños (20 filas): material didáctico, no un análisis real.
