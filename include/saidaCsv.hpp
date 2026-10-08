#pragma once

#include <chrono>
#include <ctime>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <string>
#include <vector>

namespace mandelbrot
{

constexpr const char* cabecalhoCsv =
    "status,timestamp,implementacao,gpuNome,computeCapability,maxThreadsPorBloco,maxThreadsPorMultiprocessador,"
    "largura,altura,totalPixels,maxIter,blocoX,blocoY,threadsPorBloco,"
    "numeroBlocosX,numeroBlocosY,numeroBlocosTotal,repeticao,aquecimento,tempoCpuMs,tempoKernelGpuMs,"
    "tempoTotalGpuMs,tempoHostDeviceMs,tempoDeviceHostMs,tempoAlocacaoGpuMs,ocupacaoTeoricaPercentual,"
    "validacaoOk,observacao,tempoComparavelMs,escopoTempo,regiao,threadsCpu";

// Gera a data e hora da execução.
inline std::string obterTimestampAtual()
{
    const auto agora = std::chrono::system_clock::now();
    const std::time_t tempo = std::chrono::system_clock::to_time_t(agora);
    std::tm calendario{};

#ifdef _WIN32
    localtime_s(&calendario, &tempo);
#else
    localtime_r(&tempo, &calendario);
#endif

    std::ostringstream texto;
    texto << std::put_time(&calendario, "%Y-%m-%dT%H:%M:%S");
    return texto.str();
}

// Imprime o cabeçalho do CSV.
inline void imprimirCabecalhoCsv(std::ostream& saida)
{
    saida << cabecalhoCsv << '\n';
}

// Imprime uma linha CSV.
inline void imprimirLinhaCsv(std::ostream& saida, const std::vector<std::string>& campos)
{
    for (std::size_t indice = 0; indice < campos.size(); ++indice)
    {
        if (indice > 0)
        {
            saida << ',';
        }
        saida << campos[indice];
    }
    saida << '\n';
}

// Formata um tempo em milissegundos.
inline std::string formatarDecimal(double valor)
{
    std::ostringstream texto;
    texto << std::fixed << std::setprecision(6) << valor;
    return texto.str();
}

}
