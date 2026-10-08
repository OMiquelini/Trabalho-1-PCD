#!/usr/bin/env python3
"""Gera figuras para o artigo usando somente CSVs processados e brutos."""

import argparse
import csv
from pathlib import Path
import sys


# Lê um CSV em uma lista de dicionários.
def lerCsv(caminhoCsv):
    with caminhoCsv.open("r", newline="", encoding="utf-8") as arquivoCsv:
        return list(csv.DictReader(arquivoCsv))


# Converte uma coluna numérica sem transformar ausência de dados em zero.
def converterNumeroOpcional(texto):
    if texto is None or texto == "":
        return None
    try:
        return float(texto)
    except ValueError:
        return None


# Obtém o rótulo de resolução, aceitando tanto CSVs processados quanto brutos.
def obterResolucao(registro):
    resolucao = registro.get("resolucao")
    if resolucao:
        return resolucao
    largura = registro.get("largura")
    altura = registro.get("altura")
    if largura and altura:
        return f"{int(float(largura))}x{int(float(altura))}"
    return ""


# Salva a figura em PNG de alta resolução e nos formatos vetoriais PDF e SVG.
def salvarFigura(figura, pastaSaida, nomeBase):
    pastaSaida.mkdir(parents=True, exist_ok=True)
    figura.savefig(pastaSaida / f"{nomeBase}.png", dpi=300, bbox_inches="tight")
    figura.savefig(pastaSaida / f"{nomeBase}.pdf", bbox_inches="tight")
    figura.savefig(pastaSaida / f"{nomeBase}.svg", bbox_inches="tight")


# Cria um gráfico de linhas com uma série para cada configuração CUDA.
def plotarSeries(grafico, registros, colunaY, titulo, nomeBase, pastaSaida, rotuloY):
    figura, eixo = grafico.subplots(figsize=(7.2, 4.2))
    configuracoes = sorted({registro["configuracao"] for registro in registros})
    for configuracao in configuracoes:
        selecionados = [
            registro for registro in registros
            if registro["configuracao"] == configuracao and registro.get(colunaY)
        ]
        if not selecionados:
            continue
        selecionados.sort(key=lambda registro: int(registro["largura"]) * int(registro["altura"]))
        eixo.plot(
            [obterResolucao(registro) for registro in selecionados],
            [float(registro[colunaY]) for registro in selecionados],
            marker="o",
            label=configuracao,
        )
    eixo.set_title(titulo)
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel(rotuloY)
    eixo.grid(True, alpha=0.3)
    eixo.legend(title="Bloco", fontsize="small")
    figura.tight_layout()
    salvarFigura(figura, pastaSaida, nomeBase)
    grafico.close(figura)


# Cria o gráfico de tempo CPU em função da resolução.
def gerarGraficoCpu(grafico, registrosCpu, pastaSaida):
    if not registrosCpu:
        return
    registrosCpu = sorted(registrosCpu, key=lambda registro: int(registro["largura"]) * int(registro["altura"]))
    figura, eixo = grafico.subplots(figsize=(7.2, 4.2))
    eixo.plot(
        [obterResolucao(registro) for registro in registrosCpu],
        [float(registro["medianaTempoCpuMs"]) for registro in registrosCpu],
        marker="o",
        color="#333333",
        label="CPU sequencial",
    )
    eixo.set_title("Tempo mediano da CPU por resolução")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Tempo (ms)")
    eixo.grid(True, alpha=0.3)
    eixo.legend()
    figura.tight_layout()
    salvarFigura(figura, pastaSaida, "tempo_cpu_resolucao")
    grafico.close(figura)


# Compara as configurações CUDA dentro de cada resolução.
def gerarGraficoBarras(grafico, registrosCuda, pastaSaida):
    resolucoes = sorted({obterResolucao(registro) for registro in registrosCuda}, key=lambda valor: (int(valor.split("x")[0]) * int(valor.split("x")[1])))
    configuracoes = sorted({registro["configuracao"] for registro in registrosCuda})
    if not resolucoes or not configuracoes:
        return
    figura, eixo = grafico.subplots(figsize=(8.5, 4.8))
    larguraBarra = 0.8 / len(configuracoes)
    posicoes = list(range(len(resolucoes)))
    for indiceConfiguracao, configuracao in enumerate(configuracoes):
        valores = []
        for resolucao in resolucoes:
            registro = next((item for item in registrosCuda if obterResolucao(item) == resolucao and item["configuracao"] == configuracao), None)
            valores.append(float(registro["medianaTempoKernelGpuMs"]) if registro and registro["medianaTempoKernelGpuMs"] else 0.0)
        deslocamento = (indiceConfiguracao - (len(configuracoes) - 1) / 2) * larguraBarra
        eixo.bar([posicao + deslocamento for posicao in posicoes], valores, larguraBarra, label=configuracao)
    eixo.set_title("Comparação das configurações CUDA")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Tempo mediano do kernel (ms)")
    eixo.set_xticks(posicoes, resolucoes)
    eixo.grid(True, axis="y", alpha=0.3)
    eixo.legend(title="Bloco", fontsize="small", ncol=2)
    figura.tight_layout()
    salvarFigura(figura, pastaSaida, "comparacao_blocos_por_resolucao")
    grafico.close(figura)


# Mostra a dispersão das execuções válidas de CPU, kernel e tempo total CUDA.
def gerarGraficoDispersao(grafico, linhasBrutas, pastaSaida):
    pontos = []
    for linha in linhasBrutas:
        if linha.get("status") != "ok" or linha.get("aquecimento") != "0":
            continue
        if linha.get("implementacao") == "cpu":
            valor = converterNumeroOpcional(linha.get("tempoCpuMs"))
            serie = "CPU"
            configuracao = "sequencial"
        else:
            valor = converterNumeroOpcional(linha.get("tempoKernelGpuMs"))
            serie = "CUDA kernel"
            configuracao = linha.get("blocoX", "") + "x" + linha.get("blocoY", "")
        if valor is not None:
            pontos.append((obterResolucao(linha), f"{serie} {configuracao}", valor))
    if not pontos:
        return
    grupos = {}
    for resolucao, serie, valor in pontos:
        grupos.setdefault((resolucao, serie), []).append(valor)
    figura, eixo = grafico.subplots(figsize=(9.0, 4.8))
    nomes = sorted(
        {resolucao for resolucao, _, _ in pontos},
        key=lambda valor: int(valor.split("x")[0]) * int(valor.split("x")[1]),
    )
    series = sorted({serie for _, serie, _ in pontos})
    posicoes = {nome: indice for indice, nome in enumerate(nomes)}
    for indiceSerie, serie in enumerate(series):
        valoresX = []
        valoresY = []
        for nome in nomes:
            valores = grupos.get((nome, serie), [])
            deslocamento = (indiceSerie - (len(series) - 1) / 2) * 0.08
            valoresX.extend([posicoes[nome] + deslocamento] * len(valores))
            valoresY.extend(valores)
        if valoresY:
            eixo.scatter(valoresX, valoresY, alpha=0.7, s=18, label=serie)
    eixo.set_title("Dispersão das execuções válidas")
    eixo.set_xlabel("Resolução")
    eixo.set_ylabel("Tempo (ms)")
    eixo.set_xticks(list(posicoes.values()), list(posicoes.keys()))
    eixo.grid(True, alpha=0.3)
    eixo.legend(fontsize="small")
    figura.tight_layout()
    salvarFigura(figura, pastaSaida, "dispersao_execucoes")
    grafico.close(figura)


# Gera todas as figuras possíveis sem inventar séries ausentes.
def executarPrograma():
    raizProjeto = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processados", dest="pastaProcessados", type=Path, default=raizProjeto / "results" / "processed")
    parser.add_argument("--brutos", dest="pastaBrutos", type=Path, default=raizProjeto / "results" / "raw")
    parser.add_argument("--saida", dest="pastaSaida", type=Path, default=raizProjeto / "results" / "plots")
    argumentos = parser.parse_args()

    caminhoResumo = argumentos.pastaProcessados / "summary.csv"
    if not caminhoResumo.is_file():
        print("Ainda não existem resultados processados suficientes para gerar gráficos.")
        return 0
    registrosResumo = lerCsv(caminhoResumo)
    registrosCpu = [registro for registro in registrosResumo if registro.get("implementacao") == "cpu" and registro.get("medianaTempoCpuMs")]
    registrosCuda = [registro for registro in registrosResumo if registro.get("implementacao") == "cuda" and registro.get("medianaTempoKernelGpuMs")]
    if not registrosCpu and not registrosCuda:
        print("Ainda não existem resultados processados suficientes para gerar gráficos.")
        return 0

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as grafico
    except ImportError:
        print("Para gerar gráficos, instale matplotlib: py -3 -m pip install matplotlib", file=sys.stderr)
        return 1

    gerarGraficoCpu(grafico, registrosCpu, argumentos.pastaSaida)
    if registrosCuda:
        plotarSeries(grafico, registrosCuda, "medianaTempoKernelGpuMs", "Tempo mediano do kernel CUDA", "tempo_kernel_cuda_blocos", argumentos.pastaSaida, "Tempo (ms)")
        plotarSeries(grafico, registrosCuda, "medianaTempoTotalGpuMs", "Tempo total mediano da execução CUDA", "tempo_total_cuda_blocos", argumentos.pastaSaida, "Tempo (ms)")
        plotarSeries(grafico, registrosCuda, "speedupTotal", "Speedup CPU/GPU por resolução", "speedup_cpu_gpu", argumentos.pastaSaida, "Speedup (vezes)")
        gerarGraficoBarras(grafico, registrosCuda, argumentos.pastaSaida)
    linhasBrutas = []
    for caminhoCsv in sorted(argumentos.pastaBrutos.glob("*.csv")):
        linhasBrutas.extend(lerCsv(caminhoCsv))
    gerarGraficoDispersao(grafico, linhasBrutas, argumentos.pastaSaida)
    print(f"Gráficos salvos em: {argumentos.pastaSaida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(executarPrograma())
