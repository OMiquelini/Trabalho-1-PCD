#pragma once

#include "mandelbrotComum.hpp"

namespace mandelbrot
{

// Preenche uma matriz com os valores do Mandelbrot calculados sequencialmente.
void calcularMandelbrotCpu(const ParametrosImagem& parametros, std::vector<int>& imagem);

}
