# ============================================================
# EJEMPLO - R: grafico
# ============================================================
#
# Que hace:
#   Guarda un diagrama de cajas (boxplot) que compara el peso
#   entre Sitio A y Sitio B.
#
# Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
#     Rscript 02_r/02_grafico_r.R
#
# OJO: R NO esta instalado en esta computadora (ver 00_LEEME.md).
#      Descarga gratis: https://cran.r-project.org
#
# Que produce:
#   El archivo 02_r/grafico_r.png
# ============================================================

datos <- read.csv("datos/mediciones.csv", fileEncoding = "UTF-8")

# png() abre un "archivo imagen" donde se dibujara todo
png("02_r/grafico_r.png", width = 700, height = 500)

boxplot(
  peso_g ~ sitio,
  data = datos,
  col = c("#4c72b0", "#dd8452"),
  main = "Peso por sitio",
  xlab = "Sitio",
  ylab = "Peso (g)"
)

# dev.off() cierra el archivo imagen (importantisimo, si no, no se guarda)
dev.off()

cat("Grafico guardado en 02_r/grafico_r.png\n")
