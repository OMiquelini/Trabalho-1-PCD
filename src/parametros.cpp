#include "parametros.hpp"

#include <cstdlib>
#include <iostream>

namespace mandelbrot
{
namespace
{

// Converte um argumento inteiro e informa entradas inválidas ao chamador.
bool converterInteiro(const std::string& texto, int& valor)
{
    char* fim = nullptr;
    const long convertido = std::strtol(texto.c_str(), &fim, 10);
    if (fim == texto.c_str() || *fim != '\0')
    {
        return false;
    }

    valor = static_cast<int>(convertido);
    return true;
}

// Lê o valor que vem imediatamente depois de uma opção nomeada.
bool lerValorInteiro(
    int quantidadeArgumentos,
    char** argumentos,
    int& indice,
    const std::string& nome,
    int& valor,
    std::string& mensagemErro)
{
    if (indice + 1 >= quantidadeArgumentos)
    {
        mensagemErro = "Falta o valor da opção " + nome;
        return false;
    }

    ++indice;
    if (!converterInteiro(argumentos[indice], valor))
    {
        mensagemErro = "Valor inválido para a opção " + nome + ": " + argumentos[indice];
        return false;
    }

    return true;
}

bool aplicarRegiao(const std::string& nome, ParametrosImagem& imagem)
{
    if (nome == "padrao")
    {
        imagem.minimoReal = -2.5;
        imagem.maximoReal = 1.0;
        imagem.minimoImaginario = -1.2;
        imagem.maximoImaginario = 1.2;
        return true;
    }
    if (nome == "zoom")
    {
        imagem.minimoReal = -0.9;
        imagem.maximoReal = -0.6;
        imagem.minimoImaginario = 0.0;
        imagem.maximoImaginario = 0.3;
        return true;
    }
    return false;
}

}

// Analisa os argumentos comuns e retorna uma mensagem legível em caso de erro.
bool analisarArgumentos(
    int quantidadeArgumentos,
    char** argumentos,
    ParametrosPrograma& parametros,
    std::string& mensagemErro)
{
    for (int indice = 1; indice < quantidadeArgumentos; ++indice)
    {
        const std::string opcao = argumentos[indice];

        if (opcao == "--ajuda" || opcao == "-h")
        {
            parametros.mostrarAjuda = true;
        }
        else if (opcao == "--largura")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.imagem.largura, mensagemErro)) return false;
        }
        else if (opcao == "--altura")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.imagem.altura, mensagemErro)) return false;
        }
        else if (opcao == "--max-iter")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.imagem.numeroMaximoIteracoes, mensagemErro)) return false;
        }
        else if (opcao == "--bloco-x")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.blocoX, mensagemErro)) return false;
        }
        else if (opcao == "--bloco-y")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.blocoY, mensagemErro)) return false;
        }
        else if (opcao == "--threads")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.threadsCpu, mensagemErro)) return false;
        }
        else if (opcao == "--repeticoes")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.repeticoes, mensagemErro)) return false;
        }
        else if (opcao == "--aquecimentos")
        {
            if (!lerValorInteiro(quantidadeArgumentos, argumentos, indice, opcao, parametros.aquecimentos, mensagemErro)) return false;
        }
        else if (opcao == "--formato")
        {
            if (indice + 1 >= quantidadeArgumentos)
            {
                mensagemErro = "Falta o valor da opção " + opcao;
                return false;
            }
            parametros.formato = argumentos[++indice];
        }
        else if (opcao == "--imagem")
        {
            if (indice + 1 >= quantidadeArgumentos)
            {
                mensagemErro = "Falta o valor da opção " + opcao;
                return false;
            }
            parametros.caminhoImagem = argumentos[++indice];
        }
        else if (opcao == "--regiao")
        {
            if (indice + 1 >= quantidadeArgumentos)
            {
                mensagemErro = "Falta o valor da opção " + opcao;
                return false;
            }
            parametros.regiao = argumentos[++indice];
            if (!aplicarRegiao(parametros.regiao, parametros.imagem))
            {
                mensagemErro = "Região inválida: " + parametros.regiao + ". Use padrao ou zoom.";
                return false;
            }
        }
        else
        {
            mensagemErro = "Opção desconhecida: " + opcao;
            return false;
        }
    }

    return true;
}

// Verifica limites básicos antes de iniciar uma execução experimental.
bool validarParametros(const ParametrosPrograma& parametros, std::string& mensagemErro)
{
    if (parametros.imagem.largura < 2 || parametros.imagem.altura < 2)
    {
        mensagemErro = "Largura e altura devem ser pelo menos 2.";
        return false;
    }
    if (parametros.imagem.numeroMaximoIteracoes <= 0)
    {
        mensagemErro = "O número máximo de iterações deve ser positivo.";
        return false;
    }
    if (parametros.blocoX <= 0 || parametros.blocoY <= 0)
    {
        mensagemErro = "As dimensões do bloco devem ser positivas.";
        return false;
    }
    if (parametros.threadsCpu <= 0)
    {
        mensagemErro = "A quantidade de threads da CPU deve ser positiva.";
        return false;
    }
    if (parametros.repeticoes < 0 || parametros.aquecimentos < 0)
    {
        mensagemErro = "Repetições e aquecimentos não podem ser negativos.";
        return false;
    }
    if (parametros.formato != "texto" && parametros.formato != "csv")
    {
        mensagemErro = "O formato deve ser texto ou csv.";
        return false;
    }

    return true;
}

// Imprime as opções aceitas por um executável de benchmark.
void imprimirAjuda(const char* nomePrograma, bool suportaBloco)
{
    std::cout
        << "Uso: " << nomePrograma << " [opções]\n"
        << "  --largura N              Largura da imagem (padrão: 512)\n"
        << "  --altura N               Altura da imagem (padrão: 512)\n"
        << "  --max-iter N             Número máximo de iterações (padrão: 1000)\n"
        << "  --repeticoes N           Execuções válidas (padrão: 10)\n"
        << "  --aquecimentos N         Execuções descartadas (padrão: 1)\n"
        << "  --formato texto|csv      Formato da saída (padrão: texto)\n"
        << "  --imagem CAMINHO         Salva a última matriz como PGM\n"
        << "  --threads N              Threads OpenMP (padrão: 4)\n"
        << "  --regiao padrao|zoom     Região do plano complexo\n";
    if (suportaBloco)
    {
        std::cout
            << "  --bloco-x N              Dimensão X do bloco (padrão: 16)\n"
            << "  --bloco-y N              Dimensão Y do bloco (padrão: 16)\n";
    }
    std::cout << "  --ajuda                  Mostra esta mensagem\n";
}

}
