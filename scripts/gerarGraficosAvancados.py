#!/usr/bin/env python3
"""Gera figuras adicionais a partir da análise avançada."""

import argparse
import csv
from pathlib import Path
import sys


def lerCsv(caminho):
    if not caminho.is_file():
        return []
    with caminho.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def numero(texto):
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


def chaveResolucao(linha):
    return int(linha["largura"]) * int(linha["altura"])


def rotuloSerie(linha):
    base = linha["configuracao"]
    return f"{base} | I={linha['maxIter']}" if linha.get("maxIter") else base


def salvarFigura(figura, pasta, nome):
    pasta.mkdir(parents=True, exist_ok=True)
    figura.savefig(pasta / f"{nome}.png", dpi=300, bbox_inches="tight")
    figura.savefig(pasta / f"{nome}.pdf", bbox_inches="tight")
    figura.savefig(pasta / f"{nome}.svg", bbox_inches="tight")


def gerarThroughput(plt, resumo, pasta):
    linhas = [linha for linha in resumo if numero(linha.get("throughputMedianoMpixPorSegundo")) is not None]
    if not linhas:
        return
    resolucoes = sorted({linha["resolucao"] for linha in linhas}, key=lambda valor: int(valor.split("x")[0]) * int(valor.split("x")[1]))
    figura, eixo = plt.subplots(figsize=(8.5, 4.8))
    for chave in sorted({(linha["implementacao"], linha["configuracao"], linha["maxIter"]) for linha in linhas}):
        selecionadas = [linha for linha in linhas if (linha["implementacao"], linha["configuracao"], linha["maxIter"]) == chave]
        mapa = {linha["resolucao"]: numero(linha["throughputMedianoMpixPorSegundo"]) for linha in selecionadas}
        eixo.plot(resolucoes, [mapa.get(resolucao) for resolucao in resolucoes], marker="o", label=f"{chave[1]} | I={chave[2]}")
    eixo.set_title("Throughput mediano por resolução")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Megapixels/s")
    eixo.grid(True, alpha=0.3)
    eixo.legend(fontsize="small", ncol=2)
    figura.tight_layout()
    salvarFigura(figura, pasta, "throughput_por_resolucao")
    plt.close(figura)


def gerarIntervalosMelhores(plt, resumo, comparacoes, pasta):
    melhores = {
        (linha["largura"], linha["altura"], linha["maxIter"]): linha["melhorConfiguracaoTotal"]
        for linha in comparacoes
        if linha["configuracao"] == linha["melhorConfiguracaoTotal"]
    }
    linhas = [
        linha for linha in resumo
        if linha["implementacao"] == "cuda"
        and melhores.get((linha["largura"], linha["altura"], linha["maxIter"])) == linha["configuracao"]
        and numero(linha.get("medianaTempoTotalMs")) is not None
    ]
    linhas.sort(key=lambda linha: (int(linha["maxIter"]), chaveResolucao(linha)))
    if not linhas:
        return
    nomes = [f"{linha['resolucao']}\nI={linha['maxIter']}" for linha in linhas]
    valores = [numero(linha["medianaTempoTotalMs"]) for linha in linhas]
    inferiores = [valor - numero(linha["ic95MedianaInfMs"]) for linha, valor in zip(linhas, valores)]
    superiores = [numero(linha["ic95MedianaSupMs"]) - valor for linha, valor in zip(linhas, valores)]
    figura, eixo = plt.subplots(figsize=(9.0, 4.8))
    eixo.errorbar(range(len(linhas)), valores, yerr=[inferiores, superiores], fmt="o-", capsize=4)
    eixo.set_title("Tempo total da melhor configuração CUDA com IC 95%")
    eixo.set_xlabel("Resolução e carga")
    eixo.set_ylabel("Tempo total mediano (ms)")
    eixo.set_xticks(range(len(nomes)), nomes, rotation=20, ha="right")
    eixo.grid(True, axis="y", alpha=0.3)
    figura.tight_layout()
    salvarFigura(figura, pasta, "intervalos_confianca_melhores")
    plt.close(figura)


def gerarPenalidadeBlocos(plt, comparacoes, pasta):
    linhas = [linha for linha in comparacoes if numero(linha.get("penalidadeTotalVsMelhorPercentual")) is not None]
    if not linhas:
        return
    resolucoes = sorted({linha["resolucao"] for linha in linhas}, key=lambda valor: int(valor.split("x")[0]) * int(valor.split("x")[1]))
    figura, eixo = plt.subplots(figsize=(8.5, 4.8))
    for chave in sorted({(linha["configuracao"], linha["maxIter"]) for linha in linhas}):
        selecionadas = [linha for linha in linhas if (linha["configuracao"], linha["maxIter"]) == chave]
        mapa = {linha["resolucao"]: numero(linha["penalidadeTotalVsMelhorPercentual"]) for linha in selecionadas}
        eixo.plot(resolucoes, [mapa.get(resolucao) for resolucao in resolucoes], marker="o", label=f"{chave[0]} | I={chave[1]}")
    eixo.axhline(0.0, color="black", linewidth=0.8)
    eixo.set_title("Penalidade do tempo total em relação ao melhor bloco")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Penalidade (%)")
    eixo.grid(True, alpha=0.3)
    eixo.legend(fontsize="small", ncol=2)
    figura.tight_layout()
    salvarFigura(figura, pasta, "penalidade_blocos")
    plt.close(figura)


def gerarOverhead(plt, resumo, pasta):
    linhas = [linha for linha in resumo if linha["implementacao"] == "cuda" and numero(linha.get("overheadGpuPercentual")) is not None]
    if not linhas:
        return
    resolucoes = sorted({linha["resolucao"] for linha in linhas}, key=lambda valor: int(valor.split("x")[0]) * int(valor.split("x")[1]))
    figura, eixo = plt.subplots(figsize=(8.5, 4.8))
    for chave in sorted({(linha["configuracao"], linha["maxIter"]) for linha in linhas}):
        selecionadas = [linha for linha in linhas if (linha["configuracao"], linha["maxIter"]) == chave]
        mapa = {linha["resolucao"]: numero(linha["overheadGpuPercentual"]) for linha in selecionadas}
        eixo.plot(resolucoes, [mapa.get(resolucao) for resolucao in resolucoes], marker="o", label=f"{chave[0]} | I={chave[1]}")
    eixo.set_title("Fração do tempo total fora do kernel CUDA")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Overhead (%)")
    eixo.grid(True, alpha=0.3)
    eixo.legend(fontsize="small", ncol=2)
    figura.tight_layout()
    salvarFigura(figura, pasta, "overhead_gpu")
    plt.close(figura)


def gerarSensibilidade(plt, sensibilidade, pasta):
    max_iters = sorted({int(linha["maxIter"]) for linha in sensibilidade})
    if len(max_iters) < 2:
        return
    resolucoes = sorted({linha["resolucao"] for linha in sensibilidade}, key=lambda valor: int(valor.split("x")[0]) * int(valor.split("x")[1]))
    figura, eixos = plt.subplots(1, len(resolucoes), figsize=(5.0 * len(resolucoes), 4.3), squeeze=False)
    for indice, resolucao in enumerate(resolucoes):
        eixo = eixos[0][indice]
        linhas = [linha for linha in sensibilidade if linha["resolucao"] == resolucao]
        for chave in sorted({(linha["implementacao"], linha["configuracao"]) for linha in linhas}):
            selecionadas = [linha for linha in linhas if (linha["implementacao"], linha["configuracao"]) == chave]
            selecionadas.sort(key=lambda linha: int(linha["maxIter"]))
            eixo.plot([int(linha["maxIter"]) for linha in selecionadas], [numero(linha["tempoMedidoMedianoMs"]) for linha in selecionadas], marker="o", label=f"{chave[1]}")
        eixo.set_title(resolucao)
        eixo.set_xlabel("maxIter")
        eixo.set_ylabel("Tempo mediano (ms)")
        eixo.set_yscale("log")
        eixo.grid(True, alpha=0.3)
        eixo.legend(fontsize="x-small")
    figura.suptitle("Sensibilidade do custo ao número máximo de iterações")
    figura.tight_layout()
    salvarFigura(figura, pasta, "sensibilidade_max_iter")
    plt.close(figura)


def executarPrograma():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processados", type=Path, default=raiz / "results" / "processed" / "avancado")
    parser.add_argument("--saida", type=Path, default=raiz / "results" / "plots" / "avancado")
    argumentos = parser.parse_args()
    resumo = lerCsv(argumentos.processados / "resumo_avancado.csv")
    if not resumo:
        print("Ainda não existem dados avançados processados para gerar gráficos.")
        return 0
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Para gerar gráficos, instale matplotlib.", file=sys.stderr)
        return 1
    comparacoes = lerCsv(argumentos.processados / "comparacao_blocos.csv")
    sensibilidade = lerCsv(argumentos.processados / "sensibilidade_max_iter.csv")
    gerarThroughput(plt, resumo, argumentos.saida)
    gerarIntervalosMelhores(plt, resumo, comparacoes, argumentos.saida)
    gerarPenalidadeBlocos(plt, comparacoes, argumentos.saida)
    gerarOverhead(plt, resumo, argumentos.saida)
    gerarSensibilidade(plt, sensibilidade, argumentos.saida)
    print(f"Gráficos avançados salvos em: {argumentos.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(executarPrograma())
