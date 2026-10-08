#!/usr/bin/env python3
"""Executa um comando e estima a energia da GPU pela potência amostrada."""

import argparse
import csv
import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import time


def ler_potencia():
    comando = [
        "nvidia-smi",
        "--query-gpu=index,name,power.draw",
        "--format=csv,noheader,nounits",
    ]
    processo = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if processo.returncode != 0:
        raise RuntimeError(processo.stderr.strip() or "nvidia-smi falhou.")

    amostras = []
    for linha in csv.reader(processo.stdout.splitlines(), skipinitialspace=True):
        if len(linha) < 3:
            continue
        try:
            potencia = float(linha[2])
        except ValueError:
            continue
        amostras.append({
            "index": linha[0].strip(),
            "name": linha[1].strip(),
            "power_w": potencia,
        })
    return amostras


def integrar(amostras):
    por_gpu = {}
    for amostra in amostras:
        chave = amostra["index"]
        por_gpu.setdefault(chave, []).append(amostra)

    resultados = []
    for indice, valores in por_gpu.items():
        energia = 0.0
        for anterior, atual in zip(valores, valores[1:]):
            intervalo = atual["elapsed_s"] - anterior["elapsed_s"]
            energia += (anterior["power_w"] + atual["power_w"]) * intervalo / 2.0
        duracao = valores[-1]["elapsed_s"] - valores[0]["elapsed_s"]
        if duracao <= 0:
            duracao = 0.0
        potencia_media = energia / duracao if duracao > 0 else 0.0
        resultados.append({
            "index": indice,
            "name": valores[0]["name"],
            "duracaoS": f"{duracao:.6f}",
            "energiaJ": f"{energia:.6f}",
            "potenciaMediaW": f"{potencia_media:.6f}",
            "edpJ_s": f"{energia * duracao:.6f}",
        })
    return resultados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--intervalo", type=float, default=0.1)
    parser.add_argument("comando", nargs=argparse.REMAINDER)
    argumentos = parser.parse_args()
    comando = list(argumentos.comando)
    if comando and comando[0] == "--":
        comando = comando[1:]
    if not comando:
        raise SystemExit("Informe o comando depois de --.")
    if argumentos.intervalo <= 0:
        raise SystemExit("O intervalo deve ser positivo.")
    if shutil.which("nvidia-smi") is None:
        raise SystemExit("nvidia-smi não foi encontrado no PATH.")

    amostras = []
    inicio = time.monotonic()
    processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while processo.poll() is None:
        instante = time.monotonic() - inicio
        for amostra in ler_potencia():
            amostra["elapsed_s"] = instante
            amostra["timestamp"] = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
            amostras.append(amostra)
        time.sleep(argumentos.intervalo)

    stdout, stderr = processo.communicate()
    instante = time.monotonic() - inicio
    for amostra in ler_potencia():
        amostra["elapsed_s"] = instante
        amostra["timestamp"] = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
        amostras.append(amostra)

    if stdout:
        print(stdout, end="")
    if processo.returncode != 0:
        if stderr:
            print(stderr, file=sys.stderr, end="")
        raise SystemExit(processo.returncode)

    argumentos.saida.parent.mkdir(parents=True, exist_ok=True)
    with argumentos.saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=["timestamp", "elapsed_s", "index", "name", "power_w"],
        )
        escritor.writeheader()
        escritor.writerows(amostras)

    resumo = argumentos.saida.with_name(argumentos.saida.stem + "_resumo.csv")
    resultados = integrar(amostras)
    with resumo.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=["index", "name", "duracaoS", "energiaJ", "potenciaMediaW", "edpJ_s"],
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print(f"Amostras salvas em: {argumentos.saida}")
    print(f"Resumo de energia salvo em: {resumo}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1)
