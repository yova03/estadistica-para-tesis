# ============================================================
# EJEMPLO - JULIA: estadistica rapida
# ============================================================
#
# Que es:
#   Julia es un lenguaje moderno pensado para calculo cientifico.
#   Se ve como Python, pero corre casi tan rapido como C.
#   Solo usa librerias que ya vienen incluidas (DelimitedFiles, Statistics).
#
# Como se ejecuta (desde la carpeta 02_EJEMPLOS_LENGUAJES_2026):
#     julia 03_julia/01_estadistica.jl
#
# OJO: Julia NO esta instalado en esta computadora (ver 00_LEEME.md).
#      Descarga gratis: https://julialang.org
#
# Que produce:
#   Promedio y desviacion estandar del peso por sitio.
# ============================================================

using DelimitedFiles
using Statistics

# 1. Ruta al CSV y lectura de lineas (quitando el encabezado)
ruta = joinpath(@__DIR__, "..", "datos", "mediciones.csv")
lineas = readlines(ruta)[2:end]

# 2. Separar los pesos en dos listas segun el sitio
pesos_a = Float64[]
pesos_b = Float64[]

for linea in lineas
    campos = split(linea, ",")
    sitio = campos[2]
    peso = parse(Float64, campos[3])
    if sitio == "Sitio A"
        push!(pesos_a, peso)
    else
        push!(pesos_b, peso)
    end
end

# 3. Estadisticas basicas
for (nombre, pesos) in [("Sitio A", pesos_a), ("Sitio B", pesos_b)]
    println(nombre, ":")
    println("  muestras   : ", length(pesos))
    println("  promedio   : ", round(mean(pesos), digits = 2), " g")
    println("  desviacion : ", round(std(pesos), digits = 2), " g")
    println()
end

# Dato: en Julia, mean([11, 12, 13]) tambien funciona directo con vectores.
println("Promedio directo: ", round(mean(pesos_a), digits = 2), " g")
