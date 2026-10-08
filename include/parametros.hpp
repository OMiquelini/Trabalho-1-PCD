#pragma once

#include "mandelbrotComum.hpp"

#include <string>

namespace mandelbrot
{

// Agrupa os parâmetros de linha de comando usados pelos executáveis de benchmark.
struct ParametrosPrograma
{
    ParametrosImagem imagem;
    int blocoX = 16;
    int blocoY = 16;
    int threadsCpu = 4;
    int repeticoes = 10;
    int aquecimentos = 1;
    std::string formato = "texto";
    std::string caminhoImagem;
    std::string regiao = "padrao";
    bool mostrarAjuda = false;
};

// Analisa os argumentos comuns e retorna uma mensagem legível em caso de erro.
bool analisarArgumentos(
    int quantidadeArgumentos,
    char** argumentos,
    ParametrosPrograma& parametros,
    std::string& mensagemErro);

// Verifica limites básicos antes de iniciar uma execução experimental.
bool validarParametros(const ParametrosPrograma& parametros, std::string& mensagemErro);

// Imprime as opções aceitas por um executável de benchmark.
void imprimirAjuda(const char* nomePrograma, bool suportaBloco);

}
