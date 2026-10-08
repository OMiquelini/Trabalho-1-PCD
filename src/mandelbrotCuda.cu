#include "mandelbrotCuda.hpp"

#include <cuda_runtime.h>

#include <chrono>
#include <sstream>

namespace mandelbrot
{
namespace
{

// Calcula os pixels do Mandelbrot em paralelo na GPU.
__global__ void calcularMandelbrotKernel(
    int* imagem,
    ParametrosImagem parametros)
{
    const int x = blockIdx.x * blockDim.x + threadIdx.x;
    const int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= parametros.largura || y >= parametros.altura)
    {
        return;
    }

    const std::size_t indice = static_cast<std::size_t>(y) * parametros.largura + x;
    imagem[indice] = calcularMandelbrotPixel(x, y, parametros);
}

// Traduz um erro CUDA em uma mensagem contextualizada.
bool verificarCuda(cudaError_t codigo, const std::string& operacao, std::string& mensagemErro)
{
    if (codigo == cudaSuccess)
    {
        return true;
    }

    mensagemErro = operacao + ": " + cudaGetErrorString(codigo);
    return false;
}

// Retorna o tempo transcorrido entre dois pontos do relógio de alta resolução.
double calcularMilissegundos(
    const std::chrono::steady_clock::time_point& inicio,
    const std::chrono::steady_clock::time_point& fim)
{
    return std::chrono::duration<double, std::milli>(fim - inicio).count();
}

}

// Consulta os limites do primeiro dispositivo CUDA disponível.
bool consultarInformacoesGpu(InformacoesGpu& informacoes, std::string& mensagemErro)
{
    int quantidadeDispositivos = 0;
    if (!verificarCuda(cudaGetDeviceCount(&quantidadeDispositivos), "cudaGetDeviceCount", mensagemErro))
    {
        return false;
    }
    if (quantidadeDispositivos == 0)
    {
        mensagemErro = "Nenhuma GPU CUDA foi encontrada.";
        return false;
    }

    cudaDeviceProp propriedades{};
    if (!verificarCuda(cudaGetDeviceProperties(&propriedades, 0), "cudaGetDeviceProperties", mensagemErro))
    {
        return false;
    }

    informacoes.nome = propriedades.name;
    informacoes.computeCapability = std::to_string(propriedades.major) + "." + std::to_string(propriedades.minor);
    informacoes.maximoThreadsPorBloco = propriedades.maxThreadsPerBlock;
    informacoes.maximoThreadsPorMultiprocessador = propriedades.maxThreadsPerMultiProcessor;
    informacoes.quantidadeMultiprocessadores = propriedades.multiProcessorCount;
    return true;
}

// Verifica se uma configuração de bloco pode ser usada no dispositivo selecionado.
bool verificarConfiguracaoGpu(
    int blocoX,
    int blocoY,
    const InformacoesGpu& informacoes,
    std::string& motivo)
{
    if (blocoX <= 0 || blocoY <= 0)
    {
        motivo = "As dimensões do bloco devem ser positivas.";
        return false;
    }
    if (blocoX * blocoY > informacoes.maximoThreadsPorBloco)
    {
        motivo = "A quantidade de threads excede o máximo permitido por bloco.";
        return false;
    }

    cudaDeviceProp propriedades{};
    const cudaError_t codigo = cudaGetDeviceProperties(&propriedades, 0);
    if (codigo != cudaSuccess)
    {
        motivo = "Não foi possível consultar as dimensões máximas do bloco: ";
        motivo += cudaGetErrorString(codigo);
        return false;
    }
    if (blocoX > propriedades.maxThreadsDim[0] || blocoY > propriedades.maxThreadsDim[1])
    {
        motivo = "Uma dimensão do bloco excede o limite da GPU.";
        return false;
    }

    return true;
}

// Executa uma geração completa do Mandelbrot e mede suas etapas principais.
bool calcularMandelbrotGpu(
    const ParametrosImagem& parametros,
    int blocoX,
    int blocoY,
    const InformacoesGpu& informacoes,
    std::vector<int>& imagem,
    MetricasGpu& metricas,
    std::string& mensagemErro)
{
    const dim3 dimensaoBloco(static_cast<unsigned int>(blocoX), static_cast<unsigned int>(blocoY), 1);
    const dim3 dimensaoGrade(
        static_cast<unsigned int>((parametros.largura + blocoX - 1) / blocoX),
        static_cast<unsigned int>((parametros.altura + blocoY - 1) / blocoY),
        1);

    metricas.numeroBlocosX = static_cast<int>(dimensaoGrade.x);
    metricas.numeroBlocosY = static_cast<int>(dimensaoGrade.y);
    metricas.numeroBlocosTotal = static_cast<long long>(dimensaoGrade.x) * dimensaoGrade.y;

    int blocosAtivosPorMultiprocessador = 0;
    if (!verificarCuda(
            cudaOccupancyMaxActiveBlocksPerMultiprocessor(
                &blocosAtivosPorMultiprocessador,
                calcularMandelbrotKernel,
                blocoX * blocoY,
                0),
            "cudaOccupancyMaxActiveBlocksPerMultiprocessor",
            mensagemErro))
    {
        return false;
    }
    metricas.ocupacaoTeoricaPercentual = 100.0 *
        static_cast<double>(blocosAtivosPorMultiprocessador * blocoX * blocoY) /
        static_cast<double>(informacoes.maximoThreadsPorMultiprocessador);

    const std::size_t quantidadePixels = static_cast<std::size_t>(parametros.largura) * parametros.altura;
    imagem.resize(quantidadePixels);
    int* imagemDispositivo = nullptr;

    const auto inicioTotal = std::chrono::steady_clock::now();
    const auto inicioAlocacao = std::chrono::steady_clock::now();
    if (!verificarCuda(cudaMalloc(&imagemDispositivo, quantidadePixels * sizeof(int)), "cudaMalloc", mensagemErro))
    {
        return false;
    }
    const auto fimAlocacao = std::chrono::steady_clock::now();
    metricas.tempoAlocacaoGpuMs = calcularMilissegundos(inicioAlocacao, fimAlocacao);

    cudaEvent_t eventoInicioKernel = nullptr;
    cudaEvent_t eventoFimKernel = nullptr;
    if (!verificarCuda(cudaEventCreate(&eventoInicioKernel), "cudaEventCreate", mensagemErro) ||
        !verificarCuda(cudaEventCreate(&eventoFimKernel), "cudaEventCreate", mensagemErro))
    {
        cudaFree(imagemDispositivo);
        if (eventoInicioKernel != nullptr) cudaEventDestroy(eventoInicioKernel);
        if (eventoFimKernel != nullptr) cudaEventDestroy(eventoFimKernel);
        return false;
    }

    // Não há dados de entrada para transferir: somente os escalares são passados ao kernel.
    metricas.tempoHostDeviceMs = 0.0;

    if (!verificarCuda(cudaEventRecord(eventoInicioKernel), "cudaEventRecord", mensagemErro))
    {
        cudaEventDestroy(eventoInicioKernel);
        cudaEventDestroy(eventoFimKernel);
        cudaFree(imagemDispositivo);
        return false;
    }
    calcularMandelbrotKernel<<<dimensaoGrade, dimensaoBloco>>>(imagemDispositivo, parametros);
    float tempoKernelGpuMs = 0.0f;
    if (!verificarCuda(cudaGetLastError(), "lançamento do kernel", mensagemErro) ||
        !verificarCuda(cudaEventRecord(eventoFimKernel), "cudaEventRecord", mensagemErro) ||
        !verificarCuda(cudaEventSynchronize(eventoFimKernel), "cudaEventSynchronize", mensagemErro) ||
        !verificarCuda(cudaEventElapsedTime(&tempoKernelGpuMs, eventoInicioKernel, eventoFimKernel), "cudaEventElapsedTime", mensagemErro))
    {
        cudaEventDestroy(eventoInicioKernel);
        cudaEventDestroy(eventoFimKernel);
        cudaFree(imagemDispositivo);
        return false;
    }
    metricas.tempoKernelGpuMs = static_cast<double>(tempoKernelGpuMs);

    const auto inicioDeviceHost = std::chrono::steady_clock::now();
    if (!verificarCuda(
            cudaMemcpy(imagem.data(), imagemDispositivo, quantidadePixels * sizeof(int), cudaMemcpyDeviceToHost),
            "cudaMemcpy DeviceToHost",
            mensagemErro))
    {
        cudaEventDestroy(eventoInicioKernel);
        cudaEventDestroy(eventoFimKernel);
        cudaFree(imagemDispositivo);
        return false;
    }
    if (!verificarCuda(cudaDeviceSynchronize(), "cudaDeviceSynchronize", mensagemErro))
    {
        cudaEventDestroy(eventoInicioKernel);
        cudaEventDestroy(eventoFimKernel);
        cudaFree(imagemDispositivo);
        return false;
    }
    const auto fimDeviceHost = std::chrono::steady_clock::now();
    metricas.tempoDeviceHostMs = calcularMilissegundos(inicioDeviceHost, fimDeviceHost);

    if (!verificarCuda(cudaEventDestroy(eventoInicioKernel), "cudaEventDestroy", mensagemErro) ||
        !verificarCuda(cudaEventDestroy(eventoFimKernel), "cudaEventDestroy", mensagemErro) ||
        !verificarCuda(cudaFree(imagemDispositivo), "cudaFree", mensagemErro))
    {
        return false;
    }

    const auto fimTotal = std::chrono::steady_clock::now();
    metricas.tempoTotalGpuMs = calcularMilissegundos(inicioTotal, fimTotal);
    return true;
}

}
