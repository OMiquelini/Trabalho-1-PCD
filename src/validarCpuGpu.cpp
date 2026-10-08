#include "mandelbrotCpu.hpp"
#include "mandelbrotCuda.hpp"
#include "mandelbrotOpenmp.hpp"
#include "parametros.hpp"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace mandelbrot
{
namespace
{

// Compara duas matrizes e imprime as divergências observadas.
bool compararImagens(
    const std::string& nome,
    const std::vector<int>& imagemCpu,
    const std::vector<int>& imagemGpu)
{
    const std::size_t totalPixels = std::max(imagemCpu.size(), imagemGpu.size());
    std::size_t pixelsDivergentes = 0;
    int maiorDiferenca = 0;

    for (std::size_t indice = 0; indice < totalPixels; ++indice)
    {
        const int valorCpu = indice < imagemCpu.size() ? imagemCpu[indice] : -1;
        const int valorGpu = indice < imagemGpu.size() ? imagemGpu[indice] : -1;
        const int diferenca = std::abs(valorCpu - valorGpu);
        if (diferenca != 0)
        {
            ++pixelsDivergentes;
            if (diferenca > maiorDiferenca)
            {
                maiorDiferenca = diferenca;
            }
        }
    }

    const double percentualDivergencia = totalPixels == 0
        ? 0.0
        : 100.0 * static_cast<double>(pixelsDivergentes) / static_cast<double>(totalPixels);

    std::cout << nome << '\n'
              << "Total de pixels: " << totalPixels << '\n'
              << "Pixels divergentes: " << pixelsDivergentes << '\n'
              << "Percentual de divergência: " << percentualDivergencia << "%\n"
              << "Maior diferença: " << maiorDiferenca << '\n'
              << "Validação: " << (pixelsDivergentes == 0 ? "OK" : "FALHOU") << "\n\n";
    return pixelsDivergentes == 0;
}

}

}

// Executa uma comparação pixel a pixel entre CPU, OpenMP e CUDA.
int main(int quantidadeArgumentos, char** argumentos)
{
    mandelbrot::ParametrosPrograma parametros;
    std::string mensagemErro;
    if (!mandelbrot::analisarArgumentos(quantidadeArgumentos, argumentos, parametros, mensagemErro))
    {
        std::cerr << "Erro: " << mensagemErro << '\n';
        mandelbrot::imprimirAjuda(argumentos[0], true);
        return 1;
    }
    if (parametros.mostrarAjuda)
    {
        mandelbrot::imprimirAjuda(argumentos[0], true);
        return 0;
    }
    if (!mandelbrot::validarParametros(parametros, mensagemErro))
    {
        std::cerr << "Erro: " << mensagemErro << '\n';
        return 1;
    }

    mandelbrot::InformacoesGpu informacoes;
    if (!mandelbrot::consultarInformacoesGpu(informacoes, mensagemErro))
    {
        std::cerr << "Erro CUDA: " << mensagemErro << '\n';
        return 2;
    }
    if (!mandelbrot::verificarConfiguracaoGpu(parametros.blocoX, parametros.blocoY, informacoes, mensagemErro))
    {
        std::cerr << "Configuração CUDA não suportada: " << mensagemErro << '\n';
        return 2;
    }

    std::vector<int> imagemCpu;
    std::vector<int> imagemOpenmp;
    std::vector<int> imagemGpu;
    mandelbrot::calcularMandelbrotCpu(parametros.imagem, imagemCpu);
    mandelbrot::calcularMandelbrotOpenmp(
        parametros.imagem, imagemOpenmp, parametros.threadsCpu);

    mandelbrot::MetricasGpu metricas;
    if (!mandelbrot::calcularMandelbrotGpu(
            parametros.imagem,
            parametros.blocoX,
            parametros.blocoY,
            informacoes,
            imagemGpu,
            metricas,
            mensagemErro))
    {
        std::cerr << "Erro CUDA: " << mensagemErro << '\n';
        return 2;
    }

    std::cout << "GPU: " << informacoes.nome << " (compute capability "
              << informacoes.computeCapability << ")\n"
              << "Entrada: " << parametros.imagem.largura << 'x'
              << parametros.imagem.altura << ", maxIter="
              << parametros.imagem.numeroMaximoIteracoes << '\n'
              << "Bloco: " << parametros.blocoX << 'x' << parametros.blocoY << '\n'
              << "Threads OpenMP: " << parametros.threadsCpu << '\n' << '\n';

    const bool cpuOpenmpOk = mandelbrot::compararImagens(
        "CPU sequencial x CPU OpenMP", imagemCpu, imagemOpenmp);
    const bool cpuGpuOk = mandelbrot::compararImagens(
        "CPU sequencial x CUDA", imagemCpu, imagemGpu);
    return cpuOpenmpOk && cpuGpuOk ? 0 : 3;
}
