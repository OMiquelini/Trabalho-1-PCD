#pragma once

#include "mandelbrotComum.hpp"

namespace mandelbrot
{

// Calcula o conjunto usando várias threads OpenMP.
void calcularMandelbrotOpenmp(
    const ParametrosImagem& parametros,
    std::vector<int>& imagem,
    int quantidadeThreads);

}
