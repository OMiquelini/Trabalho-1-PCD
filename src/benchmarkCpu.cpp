#include "mandelbrotCpu.hpp"
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

// Mede uma execução da implementação sequencial sem incluir a geração de arquivos.
double executarCalculoCpu(
    const ParametrosImagem& parametros,
    std::vector<int>& imagem)
{
    const auto inicio = std::chrono::steady_clock::now();
    calcularMandelbrotCpu(parametros, imagem);
    const auto fim = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::milli>(fim - inicio).count();
}

// Imprime uma execução CPU no esquema CSV compartilhado pelos scripts.
void imprimirLinhaCpu(
    const ParametrosPrograma& parametros,
    int repeticao,
    bool aquecimento,
    double tempoCpuMs)
{
    imprimirLinhaCsv(std::cout, {
        "ok",
        obterTimestampAtual(),
        "cpu",
        "", "", "", "",
        std::to_string(parametros.imagem.largura),
        std::to_string(parametros.imagem.altura),
        std::to_string(static_cast<long long>(parametros.imagem.largura) * parametros.imagem.altura),
        std::to_string(parametros.imagem.numeroMaximoIteracoes),
        "", "", "", "", "", "",
        std::to_string(repeticao),
        aquecimento ? "1" : "0",
        formatarDecimal(tempoCpuMs),
        "", "", "", "", "", "",
        "nao_verificado",
        "",
        formatarDecimal(tempoCpuMs),
        "calculo",
        parametros.regiao,
        std::to_string(parametros.threadsCpu)
    });
}

// Imprime uma linha textual curta para execução manual fora do modo CSV.
void imprimirLinhaCpuTexto(int repeticao, bool aquecimento, double tempoCpuMs)
{
    std::cout << (aquecimento ? "aquecimento" : "repeticao") << ' ' << repeticao
              << ": " << formatarDecimal(tempoCpuMs) << " ms\n";
}

}

}

// Executa o benchmark sequencial com aquecimento e repetições configuráveis.
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
        std::cout << "CPU sequencial — " << parametros.imagem.largura << 'x'
                  << parametros.imagem.altura << ", maxIter="
                  << parametros.imagem.numeroMaximoIteracoes << '\n';
    }

    for (int aquecimento = 1; aquecimento <= parametros.aquecimentos; ++aquecimento)
    {
        const double tempo = mandelbrot::executarCalculoCpu(parametros.imagem, imagem);
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaCpu(parametros, 0, true, tempo);
        }
        else
        {
            mandelbrot::imprimirLinhaCpuTexto(aquecimento, true, tempo);
        }
    }

    for (int repeticao = 1; repeticao <= parametros.repeticoes; ++repeticao)
    {
        const double tempo = mandelbrot::executarCalculoCpu(parametros.imagem, imagem);
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaCpu(parametros, repeticao, false, tempo);
        }
        else
        {
            mandelbrot::imprimirLinhaCpuTexto(repeticao, false, tempo);
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
