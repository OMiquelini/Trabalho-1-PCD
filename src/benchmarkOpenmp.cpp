#include "mandelbrotOpenmp.hpp"
#include "parametros.hpp"
#include "saidaCsv.hpp"

#include <chrono>
#include <iostream>
#include <string>
#include <vector>

namespace mandelbrot
{
namespace
{

double executarCalculoOpenmp(
    const ParametrosImagem& parametros,
    std::vector<int>& imagem,
    int quantidadeThreads)
{
    const auto inicio = std::chrono::steady_clock::now();
    calcularMandelbrotOpenmp(parametros, imagem, quantidadeThreads);
    const auto fim = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::milli>(fim - inicio).count();
}

void imprimirLinhaOpenmp(
    const ParametrosPrograma& parametros,
    int repeticao,
    bool aquecimento,
    double tempoMs)
{
    imprimirLinhaCsv(std::cout, {
        "ok",
        obterTimestampAtual(),
        "openmp",
        "", "", "", "",
        std::to_string(parametros.imagem.largura),
        std::to_string(parametros.imagem.altura),
        std::to_string(static_cast<long long>(parametros.imagem.largura) * parametros.imagem.altura),
        std::to_string(parametros.imagem.numeroMaximoIteracoes),
        "", "", "", "", "", "",
        std::to_string(repeticao),
        aquecimento ? "1" : "0",
        formatarDecimal(tempoMs),
        "", "", "", "", "", "",
        "nao_verificado",
        "",
        formatarDecimal(tempoMs),
        "calculo",
        parametros.regiao,
        std::to_string(parametros.threadsCpu)
    });
}

void imprimirLinhaTexto(int repeticao, bool aquecimento, double tempoMs)
{
    std::cout << (aquecimento ? "aquecimento" : "repeticao") << ' ' << repeticao
              << ": " << formatarDecimal(tempoMs) << " ms\n";
}

}
}

int main(int quantidadeArgumentos, char** argumentos)
{
    mandelbrot::ParametrosPrograma parametros;
    std::string mensagemErro;
    if (!mandelbrot::analisarArgumentos(quantidadeArgumentos, argumentos, parametros, mensagemErro))
    {
        std::cerr << "Erro: " << mensagemErro << '\n';
        mandelbrot::imprimirAjuda(argumentos[0], false);
        return 1;
    }
    if (parametros.mostrarAjuda)
    {
        mandelbrot::imprimirAjuda(argumentos[0], false);
        return 0;
    }
    if (!mandelbrot::validarParametros(parametros, mensagemErro))
    {
        std::cerr << "Erro: " << mensagemErro << '\n';
        return 1;
    }

    std::vector<int> imagem(
        static_cast<std::size_t>(parametros.imagem.largura) * parametros.imagem.altura);
    if (parametros.formato == "csv")
    {
        mandelbrot::imprimirCabecalhoCsv(std::cout);
    }
    else
    {
        std::cout << "CPU OpenMP — " << parametros.imagem.largura << 'x'
                  << parametros.imagem.altura << ", threads="
                  << parametros.threadsCpu << ", regiao=" << parametros.regiao << '\n';
    }

    for (int aquecimento = 1; aquecimento <= parametros.aquecimentos; ++aquecimento)
    {
        const double tempo = mandelbrot::executarCalculoOpenmp(
            parametros.imagem, imagem, parametros.threadsCpu);
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaOpenmp(parametros, 0, true, tempo);
        }
        else
        {
            mandelbrot::imprimirLinhaTexto(aquecimento, true, tempo);
        }
    }

    for (int repeticao = 1; repeticao <= parametros.repeticoes; ++repeticao)
    {
        const double tempo = mandelbrot::executarCalculoOpenmp(
            parametros.imagem, imagem, parametros.threadsCpu);
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaOpenmp(parametros, repeticao, false, tempo);
        }
        else
        {
            mandelbrot::imprimirLinhaTexto(repeticao, false, tempo);
        }
    }

    if (!parametros.caminhoImagem.empty())
    {
        if (!mandelbrot::salvarImagemPgm(parametros.caminhoImagem, imagem, parametros.imagem, mensagemErro))
        {
            std::cerr << "Erro: " << mensagemErro << '\n';
            return 1;
        }
    }

    if (parametros.formato != "csv")
    {
        std::cout << "Soma da matriz: " << mandelbrot::calcularSomaImagem(imagem) << '\n';
    }
    return 0;
}
