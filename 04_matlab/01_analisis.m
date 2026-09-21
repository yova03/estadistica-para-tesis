% ============================================================
% EJEMPLO - MATLAB: analisis y grafico
% ============================================================
%
% Que es:
%   MATLAB es el clasico de las ingenierias (software de pago).
%   Su alternativa GRATIS se llama Octave y usa casi el mismo codigo:
%       https://octave.org
%
% Como se ejecuta:
%   - En MATLAB/Octave, abre este archivo y pulsa Ejecutar (Run), o
%   - En la terminal (si tienes Octave):  octave 04_matlab/01_analisis.m
%
% OJO: MATLAB NO esta instalado en esta computadora (ver 00_LEEME.md).
%
% Que produce:
%   Estadisticas por sitio en la ventana de comandos y una figura.
% ============================================================

% 1. Leer el CSV como tabla (ruta relativa a este archivo)
ruta = fullfile(fileparts(mfilename('fullpath')), '..', 'datos', 'mediciones.csv');
T = readtable(ruta, 'Encoding', 'UTF-8');

% 2. Separar los grupos
pesoA = T.peso_g(strcmp(T.sitio, 'Sitio A'));
pesoB = T.peso_g(strcmp(T.sitio, 'Sitio B'));

% 3. Estadisticas basicas
fprintf('Sitio A: n=%d, promedio=%.2f g, desv=%.2f g\n', numel(pesoA), mean(pesoA), std(pesoA));
fprintf('Sitio B: n=%d, promedio=%.2f g, desv=%.2f g\n', numel(pesoB), mean(pesoB), std(pesoB));

% 4. Grafico de barras comparativo
figure;
bar([mean(pesoA), mean(pesoB)]);
set(gca, 'XTickLabel', {'Sitio A', 'Sitio B'});
ylabel('Peso (g)');
title('Peso promedio por sitio');
grid on;
