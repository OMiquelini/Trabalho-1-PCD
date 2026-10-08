#include "mandelbrotOpenmp.hpp"

#include <omp.h>

namespace mandelbrot
{

void calcularMandelbrotOpenmp(
    const ParametrosImagem& parametros,
    std::vector<int>& imagem,
    int quantidadeThreads)
{
    imagem.resize(static_cast<std::size_t>(parametros.largura) * parametros.altura);

    omp_set_num_threads(quantidadeThreads);
#pragma omp parallel for schedule(static)
    for (int y = 0; y < parametros.altura; ++y)
    {
        for (int x = 0; x < parametros.largura; ++x)
        {
            const std::size_t indice = static_cast<std::size_t>(y) * parametros.largura + x;
            imagem[indice] = calcularMandelbrotPixel(x, y, parametros);
        }
    }
}

}
