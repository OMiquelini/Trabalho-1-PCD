#pragma once

#include "mandelbrotComum.hpp"

#include <string>

namespace mandelbrot
{

// Armazena os limites e a identificação do dispositivo CUDA selecionado.
struct InformacoesGpu
{
    std::string nome;
    std::string computeCapability;
    int maximoThreadsPorBloco = 0;
    int maximoThreadsPorMultiprocessador = 0;
    int quantidadeMultiprocessadores = 0;
};

// Armazena os tempos e os metadados de uma execução do kernel CUDA.
struct MetricasGpu
{
    double tempoKernelGpuMs = 0.0;
    double tempoTotalGpuMs = 0.0;
    double tempoHostDeviceMs = 0.0;
    double tempoDeviceHostMs = 0.0;
    double tempoAlocacaoGpuMs = 0.0;
    double ocupacaoTeoricaPercentual = 0.0;
    int numeroBlocosX = 0;
    int numeroBlocosY = 0;
    long long numeroBlocosTotal = 0;
};

// Consulta os limites do primeiro dispositivo CUDA disponível.
bool consultarInformacoesGpu(InformacoesGpu& informacoes, std::string& mensagemErro);

// Verifica se uma configuração de bloco pode ser usada no dispositivo selecionado.
bool verificarConfiguracaoGpu(
    int blocoX,
    int blocoY,
    const InformacoesGpu& informacoes,
    std::string& motivo);

// Executa uma geração completa do Mandelbrot e mede suas etapas principais.
bool calcularMandelbrotGpu(
    const ParametrosImagem& parametros,
    int blocoX,
    int blocoY,
    const InformacoesGpu& informacoes,
    std::vector<int>& imagem,
    MetricasGpu& metricas,
    std::string& mensagemErro);

}
