#pragma once

#include <cstddef>
#include <fstream>
#include <string>
#include <vector>

#ifdef __CUDACC__
#define MANDELBROT_HOST_DEVICE __host__ __device__
#else
#define MANDELBROT_HOST_DEVICE
#endif

namespace mandelbrot
{

// Armazena a resolução e os parâmetros matemáticos comuns às duas implementações.
struct ParametrosImagem
{
    int largura = 512;
    int altura = 512;
    int numeroMaximoIteracoes = 1000;
    double minimoReal = -2.5;
    double maximoReal = 1.0;
    double minimoImaginario = -1.2;
    double maximoImaginario = 1.2;
};

// Calcula o número de iterações de um pixel usando a fórmula compartilhada por CPU e GPU.
MANDELBROT_HOST_DEVICE inline int calcularMandelbrotPixel(
    int x,
    int y,
    const ParametrosImagem& parametros)
{
    const double proporcaoX = static_cast<double>(x) / static_cast<double>(parametros.largura - 1);
    const double proporcaoY = static_cast<double>(y) / static_cast<double>(parametros.altura - 1);
    const double constanteReal = parametros.minimoReal + proporcaoX *
        (parametros.maximoReal - parametros.minimoReal);
    const double constanteImaginaria = parametros.minimoImaginario + proporcaoY *
        (parametros.maximoImaginario - parametros.minimoImaginario);

    double parteReal = 0.0;
    double parteImaginaria = 0.0;
    int iteracao = 0;

    while (iteracao < parametros.numeroMaximoIteracoes)
    {
        const double novoParteReal = parteReal * parteReal - parteImaginaria * parteImaginaria + constanteReal;
        const double novoParteImaginaria = 2.0 * parteReal * parteImaginaria + constanteImaginaria;
        parteReal = novoParteReal;
        parteImaginaria = novoParteImaginaria;

        if (parteReal * parteReal + parteImaginaria * parteImaginaria > 4.0)
        {
            break;
        }

        ++iteracao;
    }

    return iteracao;
}

// Salva a matriz de iterações em um arquivo PGM sem afetar as medições de desempenho.
inline bool salvarImagemPgm(
    const std::string& caminho,
    const std::vector<int>& imagem,
    const ParametrosImagem& parametros,
    std::string& mensagemErro)
{
    std::ofstream arquivo(caminho, std::ios::binary);
    if (!arquivo)
    {
        mensagemErro = "Não foi possível abrir o arquivo de imagem: " + caminho;
        return false;
    }

    arquivo << "P5\n" << parametros.largura << ' ' << parametros.altura << "\n255\n";
    for (const int valor : imagem)
    {
        const int intensidade = parametros.numeroMaximoIteracoes > 0
            ? (valor * 255) / parametros.numeroMaximoIteracoes
            : 0;
        const unsigned char pixel = static_cast<unsigned char>(intensidade < 255 ? intensidade : 255);
        arquivo.write(reinterpret_cast<const char*>(&pixel), sizeof(pixel));
    }

    if (!arquivo)
    {
        mensagemErro = "Falha ao escrever a imagem: " + caminho;
        return false;
    }

    return true;
}

// Soma a matriz fora da região medida para evitar que o compilador descarte o cálculo.
inline std::size_t calcularSomaImagem(const std::vector<int>& imagem)
{
    std::size_t soma = 0;
    for (const int valor : imagem)
    {
        soma += static_cast<std::size_t>(valor);
    }
    return soma;
}

}

#undef MANDELBROT_HOST_DEVICE
