#!/usr/bin/env python3
"""Executa CPU, OpenMP e CUDA e salva as medições brutas em CSV."""

import argparse
import csv
import datetime
import io
from pathlib import Path
import random
import subprocess
import sys


BLOCOS_CUDA = [(8, 8), (16, 16), (32, 8), (32, 16), (32, 32)]
THREADS_OPENMP = [2, 4, 8, 16]
RESOLUCOES = [(512, 512), (1920, 1080), (3840, 2160), (7680, 4320)]
REGIOES = ["padrao", "zoom"]


def encontrar_executavel(pasta, nome):
    possibilidades = [
        pasta / nome,
        pasta / f"{nome}.exe",
        pasta / "Release" / nome,
        pasta / "Release" / f"{nome}.exe",
    ]
    for caminho in possibilidades:
        if caminho.is_file():
            return caminho

    encontrados = [caminho for caminho in pasta.rglob(f"{nome}*") if caminho.is_file()]
    if encontrados:
        return encontrados[0]
    raise FileNotFoundError(f"Executável não encontrado: {nome}")


def ler_resolucao(texto):
    try:
        largura, altura = texto.lower().split("x")
        return int(largura), int(altura)
    except ValueError as erro:
        raise argparse.ArgumentTypeError(f"Resolução inválida: {texto}") from erro


def executar(comando):
    processo = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if processo.stdout:
        print(processo.stdout, end="")
    if processo.returncode != 0:
        if processo.stderr:
            print(processo.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"Falha ao executar: {' '.join(map(str, comando))}")
    return processo.stdout


def ler_csv(texto):
    leitor = csv.DictReader(io.StringIO(texto))
    if leitor.fieldnames is None:
        raise RuntimeError("O programa não produziu um cabeçalho CSV.")
    return list(leitor), leitor.fieldnames


def montar_comando(executavel, largura, altura, argumentos, regiao):
    return [
        str(executavel),
        "--largura", str(largura),
        "--altura", str(altura),
        "--max-iter", str(argumentos.max_iter),
        "--repeticoes", str(argumentos.repeticoes),
        "--aquecimentos", str(argumentos.aquecimentos),
        "--regiao", regiao,
        "--formato", "csv",
    ]


def adicionar_metadados(linhas, ordem, semente, validacao_ok):
    for linha in linhas:
        linha["ordemExecucao"] = str(ordem)
        linha["semente"] = str(semente)
        linha["validacaoOk"] = "1" if validacao_ok else "0"
    return linhas


def validar(executavel, largura, altura, argumentos, regiao):
    comando = [
        str(executavel),
        "--largura", str(largura),
        "--altura", str(altura),
        "--max-iter", str(argumentos.max_iter),
        "--bloco-x", "16",
        "--bloco-y", "16",
        "--threads", str(argumentos.threads_openmp[0]),
        "--regiao", regiao,
    ]
    saida = executar(comando)
    return "Validação: OK" in saida


def executar_resolucao(
    executavel_cpu,
    executavel_openmp,
    executavel_cuda,
    executavel_validacao,
    largura,
    altura,
    argumentos,
    regiao,
    semente,
):
    linhas = []
    tarefas = [("openmp", threads) for threads in argumentos.threads_openmp]
    tarefas.extend(("cuda", bloco) for bloco in BLOCOS_CUDA)
    random.Random(semente).shuffle(tarefas)

    validacao_ok = True
    if not argumentos.sem_validacao:
        print(f"Validando {regiao} {largura}x{altura}")
        validacao_ok = validar(executavel_validacao, largura, altura, argumentos, regiao)
        if not validacao_ok:
            raise RuntimeError("A validação CPU/OpenMP/CUDA falhou.")

    print(f"CPU {regiao} {largura}x{altura}")
    comando = montar_comando(executavel_cpu, largura, altura, argumentos, regiao)
    linhas_cpu, campos = ler_csv(executar(comando))
    linhas.extend(adicionar_metadados(linhas_cpu, 0, semente, validacao_ok))

    for ordem, tarefa in enumerate(tarefas, start=1):
        implementacao, configuracao = tarefa
        if implementacao == "openmp":
            threads = configuracao
            print(f"OpenMP {regiao} {largura}x{altura}, threads {threads} (ordem {ordem})")
            comando = montar_comando(executavel_openmp, largura, altura, argumentos, regiao)
            comando.extend(["--threads", str(threads)])
        else:
            bloco_x, bloco_y = configuracao
            print(f"CUDA {regiao} {largura}x{altura}, bloco {bloco_x}x{bloco_y} (ordem {ordem})")
            comando = montar_comando(executavel_cuda, largura, altura, argumentos, regiao)
            comando.extend(["--bloco-x", str(bloco_x), "--bloco-y", str(bloco_y)])

        novas_linhas, campos_novas = ler_csv(executar(comando))
        if campos_novas != campos:
            raise RuntimeError("Os executáveis produziram CSVs diferentes.")
        linhas.extend(adicionar_metadados(novas_linhas, ordem, semente, validacao_ok))

    return linhas, campos + ["ordemExecucao", "semente"]


def criar_parser():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=raiz / "build")
    parser.add_argument("--resolucoes", nargs="+", type=ler_resolucao)
    parser.add_argument("--regioes", nargs="+", choices=REGIOES, default=REGIOES)
    parser.add_argument("--threads-openmp", nargs="+", type=int, default=THREADS_OPENMP)
    parser.add_argument("--repeticoes", type=int, default=10)
    parser.add_argument("--aquecimentos", type=int, default=1)
    parser.add_argument("--max-iter", dest="max_iter", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--sem-validacao", action="store_true")
    parser.add_argument("--rapido", action="store_true")
    return parser


def main():
    argumentos = criar_parser().parse_args()
    raiz = Path(__file__).resolve().parents[1]

    resolucoes = argumentos.resolucoes or RESOLUCOES
    regioes = argumentos.regioes
    if argumentos.rapido:
        resolucoes = [(256, 256)]
        regioes = ["padrao"]
        argumentos.threads_openmp = [2, 4]
        argumentos.repeticoes = 1
        argumentos.aquecimentos = 1
        argumentos.max_iter = 100

    if argumentos.repeticoes <= 0 or argumentos.aquecimentos < 0 or argumentos.max_iter <= 0:
        raise SystemExit("Use valores positivos para repeticoes e max-iter.")
    if any(threads <= 0 for threads in argumentos.threads_openmp):
        raise SystemExit("As quantidades de threads OpenMP devem ser positivas.")

    pasta_build = argumentos.build_dir.resolve()
    executavel_cpu = encontrar_executavel(pasta_build, "benchmarkCpu")
    executavel_openmp = encontrar_executavel(pasta_build, "benchmarkOpenmp")
    executavel_cuda = encontrar_executavel(pasta_build, "benchmarkCuda")
    executavel_validacao = encontrar_executavel(pasta_build, "validarCpuGpu")

    linhas = []
    campos = None
    contador = 0
    for regiao in regioes:
        for largura, altura in resolucoes:
            semente = argumentos.seed + contador
            novas_linhas, campos = executar_resolucao(
                executavel_cpu,
                executavel_openmp,
                executavel_cuda,
                executavel_validacao,
                largura,
                altura,
                argumentos,
                regiao,
                semente,
            )
            linhas.extend(novas_linhas)
            contador += 1

    if argumentos.saida:
        caminho_saida = argumentos.saida.resolve()
    else:
        pasta_saida = raiz / "results" / "raw"
        caminho_saida = pasta_saida / f"execucoes_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with caminho_saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"CSV salvo em: {caminho_saida}")
    print(f"Linhas gravadas: {len(linhas)}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1)
