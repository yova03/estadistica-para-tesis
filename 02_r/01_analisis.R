# ============================================================
# EJEMPLO - R: analisis estadistico
# ============================================================
#
# Que es:
#   R es el lenguaje favorito de la estadistica y las ciencias
#   sociales/salud. En R, TODO gira alrededor de datos.
#
# Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
#     Rscript 02_r/01_analisis.R
#
# OJO: R NO esta instalado en esta computadora (ver 00_LEEME.md).
#      Descarga gratis: https://cran.r-project.org
#
# Que produce:
#   Imprime promedios por sitio y una prueba t de Student.
# ============================================================

# 1. Leer el CSV (como read.csv en un CSV cualquiera)
datos <- read.csv("datos/mediciones.csv", fileEncoding = "UTF-8")

# 2. Ver las primeras filas
print(head(datos))

# 3. Promedio de peso por sitio (tapply = "aplicar por grupo")
promedios <- tapply(datos$peso_g, datos$sitio, mean)
print(round(promedios, 2))

# 4. Prueba t de Student (la misma del ejemplo de Python/scipy)
prueba <- t.test(peso_g ~ sitio, data = datos)
print(prueba)

# 5. Nivel de significancia en palabras simples
if (prueba$p.value < 0.05) {
  cat("Conclusion: SI hay diferencia significativa entre los sitios.\n")
} else {
  cat("Conclusion: NO hay diferencia significativa.\n")
}
