! ============================================================
! EJEMPLO - FORTRAN: calculo numerico
! ============================================================
!
! Que es:
!   Fortran es de 1957, el abuelo de todos, y SIGUE siendo el rey
!   del calculo pesado: clima, fisica, ingenieria. Es lo que corre
!   por debajo de numpy/scipy cuando usas Python.
!
! Como se compila y ejecuta:
!     gfortran 05_fortran/01_estadistica.f90 -o estadistica
!     ./estadistica            (en Windows: estadistica.exe)
!
! OJO: no hay compilador de Fortran en esta computadora (ver 00_LEEME.md).
!      Descarga GRATIS: https://www.mingw-w64.org  (incluye gfortran)
!      o instala con: winget install GnuFortran
!
! Que produce:
!   Imprime estadisticas basicas de dos series de numeros.
!   Nota: los datos van dentro del codigo para no complicar la
!   lectura de archivos (en Fortran eso requiere mas codigo).
! ============================================================

program estadistica
    implicit none

    ! Dos series de mediciones (como los pesos de cada sitio)
    real, dimension(10) :: sitio_a = [11.2, 12.4, 10.8, 12.1, 11.9, &
                                      12.6, 11.4, 12.2, 10.9, 11.7]
    real, dimension(10) :: sitio_b = [14.8, 15.3, 14.1, 16.2, 15.0, &
                                      14.6, 15.8, 14.4, 15.5, 14.9]

    print '(A)', '=== Estadisticas en Fortran ==='
    call reportar('Sitio A', sitio_a)
    call reportar('Sitio B', sitio_b)

contains

    ! Subrutina que imprime las estadisticas de una serie
    subroutine reportar(nombre, x)
        character(len=*), intent(in) :: nombre
        real, dimension(:), intent(in) :: x

        print '(A)', nombre // ':'
        print '(A, I3)',   '  muestras : ', size(x)
        print '(A, F6.2)', '  promedio : ', promedio(x)
        print '(A, F6.2)', '  minimo   : ', minval(x)
        print '(A, F6.2)', '  maximo   : ', maxval(x)
        print '(A)', ''
    end subroutine reportar

    ! Funcion que calcula el promedio
    function promedio(x) result(p)
        real, dimension(:), intent(in) :: x
        real :: p
        p = sum(x) / size(x)
    end function promedio

end program estadistica
