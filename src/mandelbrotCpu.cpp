#include "mandelbrotCpu.hpp"

namespace mandelbrot
{

// Preenche uma matriz com os valores do Mandelbrot calculados sequencialmente.
void calcularMandelbrotCpu(const ParametrosImagem& parametros, std::vector<int>& imagem)
{
    imagem.resize(static_cast<std::size_t>(parametros.largura) * static_cast<std::size_t>(parametros.altura));

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
