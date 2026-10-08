#include "mandelbrotCuda.hpp"
#include "parametros.hpp"
#include "saidaCsv.hpp"

#include <iostream>
#include <string>
#include <vector>

namespace mandelbrot
{
namespace
{

// Imprime uma execução GPU no esquema CSV compartilhado pelos scripts.
void imprimirLinhaGpu(
    const ParametrosPrograma& parametros,
    int repeticao,
    bool aquecimento,
    const InformacoesGpu& informacoes,
    const MetricasGpu& metricas)
{
    imprimirLinhaCsv(std::cout, {
        "ok",
        obterTimestampAtual(),
        "cuda",
        informacoes.nome,
        informacoes.computeCapability,
        std::to_string(informacoes.maximoThreadsPorBloco),
        std::to_string(informacoes.maximoThreadsPorMultiprocessador),
        std::to_string(parametros.imagem.largura),
        std::to_string(parametros.imagem.altura),
        std::to_string(static_cast<long long>(parametros.imagem.largura) * parametros.imagem.altura),
        std::to_string(parametros.imagem.numeroMaximoIteracoes),
        std::to_string(parametros.blocoX),
        std::to_string(parametros.blocoY),
        std::to_string(parametros.blocoX * parametros.blocoY),
        std::to_string(metricas.numeroBlocosX),
        std::to_string(metricas.numeroBlocosY),
        std::to_string(metricas.numeroBlocosTotal),
        std::to_string(repeticao),
        aquecimento ? "1" : "0",
        "",
        formatarDecimal(metricas.tempoKernelGpuMs),
        formatarDecimal(metricas.tempoTotalGpuMs),
        formatarDecimal(metricas.tempoHostDeviceMs),
        formatarDecimal(metricas.tempoDeviceHostMs),
        formatarDecimal(metricas.tempoAlocacaoGpuMs),
        formatarDecimal(metricas.ocupacaoTeoricaPercentual),
        "nao_verificado",
        "sem_dados_de_entrada_para_transferir",
        formatarDecimal(metricas.tempoKernelGpuMs),
        "kernel",
        parametros.regiao,
        std::to_string(parametros.threadsCpu)
    });
}

// Imprime uma execução GPU em formato legível para um teste manual.
void imprimirLinhaGpuTexto(int repeticao, bool aquecimento, const MetricasGpu& metricas)
{
    std::cout << (aquecimento ? "aquecimento" : "repeticao") << ' ' << repeticao
              << ": kernel=" << formatarDecimal(metricas.tempoKernelGpuMs)
              << " ms, total=" << formatarDecimal(metricas.tempoTotalGpuMs) << " ms\n";
}

// Imprime uma configuração não suportada sem interromper o processamento de outros casos.
void imprimirConfiguracaoNaoSuportada(
    const ParametrosPrograma& parametros,
    const InformacoesGpu& informacoes,
    const std::string& motivo)
{
    imprimirLinhaCsv(std::cout, {
        "nao_suportado",
        obterTimestampAtual(),
        "cuda",
        informacoes.nome,
        informacoes.computeCapability,
        std::to_string(informacoes.maximoThreadsPorBloco),
        std::to_string(informacoes.maximoThreadsPorMultiprocessador),
        std::to_string(parametros.imagem.largura),
        std::to_string(parametros.imagem.altura),
        std::to_string(static_cast<long long>(parametros.imagem.largura) * parametros.imagem.altura),
        std::to_string(parametros.imagem.numeroMaximoIteracoes),
        std::to_string(parametros.blocoX),
        std::to_string(parametros.blocoY),
        std::to_string(parametros.blocoX * parametros.blocoY),
        "", "", "", "0", "0",
        "", "", "", "", "", "", "",
        "nao_verificado",
        motivo,
        "", "", parametros.regiao, std::to_string(parametros.threadsCpu)
    });
}

}

}

// Executa o benchmark CUDA para uma única configuração de bloco.
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

    if (parametros.formato == "csv")
    {
        mandelbrot::imprimirCabecalhoCsv(std::cout);
    }

    mandelbrot::InformacoesGpu informacoes;
    if (!mandelbrot::consultarInformacoesGpu(informacoes, mensagemErro))
    {
        std::cerr << "Erro CUDA: " << mensagemErro << '\n';
        return 2;
    }

    std::string motivo;
    if (!mandelbrot::verificarConfiguracaoGpu(parametros.blocoX, parametros.blocoY, informacoes, motivo))
    {
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirConfiguracaoNaoSuportada(parametros, informacoes, motivo);
            return 0;
        }
        std::cerr << "Configuração não suportada: " << motivo << '\n';
        return 0;
    }

    if (parametros.formato != "csv")
    {
        std::cout << "GPU CUDA: " << informacoes.nome << " (compute capability "
                  << informacoes.computeCapability << ")\n"
                  << "Configuração: " << parametros.blocoX << 'x' << parametros.blocoY << '\n';
    }

    std::vector<int> imagem;
    mandelbrot::MetricasGpu metricas;
    for (int aquecimento = 1; aquecimento <= parametros.aquecimentos; ++aquecimento)
    {
        if (!mandelbrot::calcularMandelbrotGpu(
                parametros.imagem,
                parametros.blocoX,
                parametros.blocoY,
                informacoes,
                imagem,
                metricas,
                mensagemErro))
        {
            std::cerr << "Erro CUDA: " << mensagemErro << '\n';
            return 2;
        }
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaGpu(parametros, 0, true, informacoes, metricas);
        }
        else
        {
            mandelbrot::imprimirLinhaGpuTexto(aquecimento, true, metricas);
        }
    }

    for (int repeticao = 1; repeticao <= parametros.repeticoes; ++repeticao)
    {
        if (!mandelbrot::calcularMandelbrotGpu(
                parametros.imagem,
                parametros.blocoX,
                parametros.blocoY,
                informacoes,
                imagem,
                metricas,
                mensagemErro))
        {
            std::cerr << "Erro CUDA: " << mensagemErro << '\n';
            return 2;
        }
        if (parametros.formato == "csv")
        {
            mandelbrot::imprimirLinhaGpu(parametros, repeticao, false, informacoes, metricas);
        }
        else
        {
            mandelbrot::imprimirLinhaGpuTexto(repeticao, false, metricas);
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
