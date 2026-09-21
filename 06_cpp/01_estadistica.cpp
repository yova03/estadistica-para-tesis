// ============================================================
// EJEMPLO - C++: el mismo calculo, a maxima velocidad
// ============================================================
//
// Que es:
//   C++ es el lenguaje de los programas rapidos: videojuegos,
//   simulaciones, motores de calculo. Es mas verboso que Python,
//   pero puede ser 50 veces mas rapido en calculos pesados.
//   Es parte de lo que trabaja "por debajo" de numpy/pandas.
//
// Como se compila y ejecuta:
//     g++ 06_cpp/01_estadistica.cpp -o estadistica
//     ./estadistica          (en Windows: estadistica.exe)
//
// OJO: no hay compilador de C++ en esta computadora (ver 00_LEEME.md).
//      Descarga GRATIS: https://www.mingw-w64.org
//      o instala con: winget install GnuWin32.Make (o MinGW completo)
//
// Que produce:
//   Estadisticas basicas de dos series de numeros.
//   Comparalo con 01_python/01_sin_librerias.py: mismo resultado,
//   mas codigo... pero muchisimo mas rapido en millones de datos.
// ============================================================

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

// Calcula el promedio de una serie
double promedio(const std::vector<double>& x) {
    return std::accumulate(x.begin(), x.end(), 0.0) / x.size();
}

// Calcula la desviacion estandar
double desviacion(const std::vector<double>& x) {
    double media = promedio(x);
    double suma = 0.0;
    for (double v : x) suma += (v - media) * (v - media);
    return std::sqrt(suma / x.size());
}

// Imprime el reporte de una serie
void reportar(const std::string& nombre, const std::vector<double>& x) {
    std::cout << nombre << ":\n";
    std::cout << "  muestras   : " << x.size() << "\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "  promedio   : " << promedio(x) << " g\n";
    std::cout << "  desviacion : " << desviacion(x) << " g\n";
    std::cout << "  minimo     : " << *std::min_element(x.begin(), x.end()) << " g\n";
    std::cout << "  maximo     : " << *std::max_element(x.begin(), x.end()) << " g\n\n";
}

int main() {
    std::vector<double> sitio_a = {11.2, 12.4, 10.8, 12.1, 11.9,
                                   12.6, 11.4, 12.2, 10.9, 11.7};
    std::vector<double> sitio_b = {14.8, 15.3, 14.1, 16.2, 15.0,
                                   14.6, 15.8, 14.4, 15.5, 14.9};

    std::cout << "=== Estadisticas en C++ ===\n";
    reportar("Sitio A", sitio_a);
    reportar("Sitio B", sitio_b);

    return 0;
}
