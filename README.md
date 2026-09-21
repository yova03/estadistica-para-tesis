---
objetivo: "Presentar el repositorio: un scraper de repositorios de datos arqueológicos, un programa de estadística para tesis y once ejemplos comparativos de lenguajes."
uso: "Leer como portada: qué hace cada herramienta, cómo se ejecutan sin instalar nada, qué se verificó y qué limitaciones tienen."
---

# Herramientas para tesis de arqueología

Dos programas de Python que resuelven dos trabajos repetidos de una tesis, más once
ejemplos para comparar lenguajes.

**No hay que instalar nada.** Solo se necesita Python, que ya viene en la mayoría de
computadoras o se instala una vez desde <https://python.org>. Ninguno de los dos
programas usa pandas, numpy ni scipy: todo está escrito dentro del mismo archivo.

| Herramienta | Para qué sirve |
|---|---|
| **`scraper_arqueologia.py`** | Busca en repositorios de datos arqueológicos y devuelve una tabla con todo lo que encuentre sobre un tema. |
| **`estadistica_tesis.py`** | Calcula lo que se pide en el informe: tamaño de muestra, descriptivos, prueba t, ANOVA, correlación y alfa de Cronbach. |

---

# 1. Scraper de repositorios de arqueología

Busca en cuatro repositorios científicos a la vez y guarda una tabla con título,
autores, año, DOI y enlace de cada hallazgo. Sirve para armar el estado de la
cuestión, ver qué datos ya existen sobre una zona o un período, y citar sin inventar
referencias. Recorre la paginación solo, así que no hay que ir resultado por resultado.

    python scraper_arqueologia.py "arqueologia Peru" --maximo 100

## Qué repositorios consulta

| Repositorio | Qué es | Clave |
|---|---|---|
| **Zenodo** | Investigación y datos abiertos del CERN. Busca en texto completo. | No pide |
| **ARIADNE** | Agregador europeo de arqueología: 2,6 millones de registros. Indexa a su vez ADS, tDAR y Open Context. | No pide |
| **Harvard Dataverse** | Datos de investigación de Harvard y de miles de instituciones. | No pide |
| **OSF** | Open Science Framework. **Solo busca en títulos**, así que aporta poco en arqueología andina. | No pide |

tDAR, ADS y Open Context bloquean el acceso automático, por eso no se consultan
directo: su contenido llega a través de ARIADNE.

## Lo que hay que saber antes de usarlo

**Busca en español y en inglés, y eso no es un adorno.** Los catálogos de ARIADNE y
Zenodo son casi enteros en inglés, y Dataverse busca con OR. Medido el 21 de
septiembre de 2026 con `arqueologia Peru`:

| | Zenodo | Dataverse | ARIADNE | OSF |
|---|---|---|---|---|
| `arqueologia Peru` | 70 | 1 451 | **0** | **0** |
| `arqueologia` solo | — | 5 | 11 | — |
| `archaeology` | — | — | 2 683 731 | 107 |

Con la consulta en español, ARIADNE y OSF no devuelven **nada**, y los primeros
resultados de Dataverse son encuestas de papa y de ivermectina, no arqueología. Por
eso el programa traduce los términos con un glosario propio de arqueología andina
(unos 150 términos) y busca las dos versiones, quitando los repetidos. Con
`--solo-espanol` se desactiva.

**Corrige el OR de Dataverse y de OSF.** Esos dos no saben exigir que aparezcan todas
las palabras. Sin corrección, buscar `arqueologia Peru` devuelve
*«Peru Potato Producer Survey»*. El programa revisa uno por uno y descarta los que no
cumplen: en una corrida real revisó 500 registros de Dataverse y conservó 4. Con
`--sin-filtro` se desactiva y se ve el ruido.

## Cómo se usa

    # Lo básico
    python scraper_arqueologia.py "arqueologia Peru" --maximo 100

    # Elegir repositorios y años
    python scraper_arqueologia.py "ceramica Nasca" -r zenodo,ariadne --desde 2015

    # Sin argumentos: modo interactivo, preguntando todo
    python scraper_arqueologia.py

    # Ver todas las opciones
    python scraper_arqueologia.py --ayuda

Opciones útiles: `-n/--maximo`, `-r/--repos`, `-o/--salida`, `--desde`, `--hasta`,
`--recientes`, `--json`, `--solo-espanol`, `--sin-filtro`, `--callado`.

## Qué produce

Un CSV que Excel abre directamente, con una fila por hallazgo:

| Columna | Contenido |
|---|---|
| `repositorio` | De dónde salió |
| `titulo`, `autores`, `anio`, `fecha` | La referencia |
| `tipo` | Dataset, artículo, informe, colección… |
| `idioma`, `pais` | Cuando el repositorio lo informa |
| `doi` | Solo si es un DOI de verdad; sirve para citar |
| `url` | El enlace para abrirlo |
| `materias`, `descripcion` | Para decidir si sirve, sin abrir el enlace |

Con `--json` se guarda además el JSON crudo. Al terminar muestra un resumen por
repositorio, por año y por tipo de recurso.

## Limitaciones, dichas claras

- **Los nombres de lugar se confunden con calles.** Buscar `Peru` trae un informe
  arqueológico de *Peru Street*, en Salford, Inglaterra. Es inevitable al buscar por
  palabra; conviene revisar los títulos.
- **Zenodo busca en el texto completo**, así que un artículo de botánica que menciona
  «arqueología» de pasada entra en la lista.
- **El filtro exige que aparezcan todas las palabras.** Es estricto a propósito: es
  preferible una tabla corta y pertinente a una larga con ruido.
- **Los años se filtran después de descargar**, así que `--desde` no ahorra tiempo.
- **OSF aporta casi nada** en arqueología andina: si molesta, se quita con
  `-r zenodo,dataverse,ariadne`.
- Los metadatos son de cada repositorio, y cada uno tiene sus propias condiciones de
  uso. Hay que citar el repositorio, no solo el DOI del registro.

---

# 2. Estadística para tesis

Resuelve las cuentas que más se piden en un informe, con la lectura en palabras
simples y una frase sugerida para redactar.

    python estadistica_tesis.py

| Opción | Cálculo | Para qué sirve |
|---|---|---|
| 1 | **Tamaño de muestra** | Estimar una media, una proporción, comparar dos medias o dos proporciones. Con ajuste por población finita y recargo por pérdidas. |
| 2 | **Descriptivos** | Media, mediana, desviación estándar, coeficiente de variación, IC 95 %, asimetría y curtosis, con aviso de normalidad. |
| 3 | **Comparar dos grupos** | Prueba t de Student, para grupos independientes o muestras relacionadas (antes y después). Informa también la t de Welch y la prueba F de varianzas. |
| 4 | **Comparar tres o más grupos** | ANOVA de un factor con eta cuadrado y comparaciones por pares con corrección de Bonferroni. |
| 5 | **Correlación** | Pearson y Spearman, con el coeficiente de determinación y la fuerza de la relación. |
| 6 | **Confiabilidad** | Alfa de Cronbach, alfa si se elimina el ítem y correlación ítem-total corregida. |
| 7 | **Analizar un CSV** | Lee tu archivo, detecta las columnas solo y ofrece todo lo anterior. |

También acepta el archivo como argumento:

    python estadistica_tesis.py mis_datos.csv

**Cómo preparar tus datos.** Un CSV donde cada fila es un caso y cada columna una
variable, con los nombres en la primera fila:

```csv
id,sitio,peso_g,longitud_mm
1,Sitio A,11.2,46
2,Sitio A,12.4,51
3,Sitio B,14.8,63
```

Si tus datos están en Excel: **Archivo → Guardar como → CSV UTF-8 (delimitado por
comas)**. Sirven los decimales con punto (`11.2`) y con coma (`11,2`), y tanto la coma
como el punto y coma como separador: el programa lo detecta solo.

**Cómo se ve.** Ejemplo real con `datos/mediciones.csv`:

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
```

La opción **8** guarda todo lo mostrado en `resultados_estadistica.txt`, listo para
copiar al informe.

> **Tus datos no salen de tu computadora.** Todo se calcula localmente, sin conexión.
> El scraper, en cambio, sí consulta internet: es su trabajo.

---

# 3. Los once ejemplos de lenguajes

En las carpetas `01_python` a `11_jupyter`, **la misma tarea resuelta en once
lenguajes y herramientas**, para comparar cuánto código necesita cada uno:

| Carpeta | Lenguaje o herramienta | ¿Funciona sin instalar nada? |
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

El detalle está en [`00_LEEME.md`](./00_LEEME.md). **La conclusión práctica:** Python
cubre casi todo el trabajo de una tesis; las demás herramientas suelen trabajar por
debajo sin que haga falta escribirlas a mano.

---

# Verificación

Las fórmulas de `estadistica_tesis.py` no se piden a una librería externa: están
escritas dentro del programa. Por eso se comprueban aparte, contra tablas
estadísticas clásicas y contra `scipy` y `numpy`:

    python pruebas/test_estadistica.py

    PASARON LAS 53 COMPROBACIONES

Se verifican la t de Student, la t de Welch, la F de varianzas, la ANOVA, la t
pareada, Pearson, Spearman, la asimetría, la curtosis, el alfa de Cronbach y todos
los valores críticos y valores p.

El scraper no tiene pruebas automáticas porque depende de servicios externos que
cambian. Lo que sí se comprobó, contra las API reales el 21 de septiembre de 2026:

- Los cuatro repositorios responden sin clave.
- Los campos de cada uno están mapeados (por ejemplo, ARIADNE manda el título como
  `{"text": ..., "language": ...}`, no como texto).
- Open Context, tDAR y ADS bloquean el acceso automático y por eso quedaron fuera.
- Los recuentos de la tabla comparativa de arriba salieron de consultar las API.

---

# Requisitos

- **Python 3.8 o mayor.** Nada más.
- El scraper necesita conexión a internet.
- Opcional: `scipy` y `numpy`, solo para ejecutar el archivo de comprobación.

---

# Licencia

MIT. En palabras simples: puedes usar, copiar, modificar y compartir estos programas
libremente, incluso con fines comerciales y en trabajos de investigación y
publicaciones. La única condición es mantener el aviso de autoría. Se entregan sin
garantía.

El texto legal completo está en [`LICENSE`](./LICENSE) (en inglés, que es la versión
que rige).
