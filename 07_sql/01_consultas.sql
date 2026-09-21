-- ============================================================
-- EJEMPLO - SQL: el lenguaje de las bases de datos
-- ============================================================
--
-- Que es:
--   SQL no sirve para "hacer programas", sino para PREGUNTARLE
--   cosas a una base de datos (que es una tabla gigante).
--   Todo lo usan: bancos, hospitales, tiendas... y la investigacion
--   cuando hay miles o millones de registros.
--
-- Como se prueba (sin instalar nada):
--   Opcion 1: abre https://sqliteonline.com y pega todo este archivo.
--   Opcion 2: con Python (ya esta instalado), en la carpeta
--             02_EJEMPLOS_LENGUAJES_2026 escribe:
--                 python -c "import sqlite3; con=sqlite3.connect(':memory:'); con.executescript(open('07_sql/01_consultas.sql',encoding='utf-8').read())"
--   (La opcion 2 ejecuta el script completo.)
--
-- Que produce:
--   Crea una mini tabla con los datos y muestra consultas tipicas:
--   promedios por grupo, filtros y conteos.
-- ============================================================

-- 1. Crear la tabla (como una hoja de calculo con columnas fijas)
CREATE TABLE muestras (
    id          INTEGER PRIMARY KEY,
    sitio       TEXT,
    peso_g      REAL,
    longitud_mm REAL
);

-- 2. Insertar algunos datos (los mismos del archivo mediciones.csv)
INSERT INTO muestras (id, sitio, peso_g, longitud_mm) VALUES
    (1,  'Sitio A', 11.2, 46),
    (2,  'Sitio A', 12.4, 51),
    (3,  'Sitio A', 10.8, 44),
    (4,  'Sitio B', 14.8, 63),
    (5,  'Sitio B', 15.3, 67),
    (6,  'Sitio B', 14.1, 60);

-- 3. Consulta: promedio, minimo, maximo y conteo POR SITIO
--    (esto equivale al groupby de pandas o al tapply de R)
SELECT
    sitio,
    COUNT(*)          AS muestras,
    ROUND(AVG(peso_g), 2)      AS promedio_peso,
    ROUND(MIN(peso_g), 1)      AS minimo,
    ROUND(MAX(peso_g), 1)      AS maximo
FROM muestras
GROUP BY sitio;

-- 4. Consulta con filtro: solo las muestras con peso mayor a 14 g
SELECT sitio, peso_g
FROM muestras
WHERE peso_g > 14
ORDER BY peso_g DESC;

-- 5. Consulta ordenada por longitud
SELECT id, sitio, longitud_mm
FROM muestras
ORDER BY longitud_mm;

-- NOTA: en una investigacion real, este archivo no "hace" nada solo:
-- normalmente un programa (Python, R...) se conecta a la base de datos
-- y le lanza consultas como las de arriba.
