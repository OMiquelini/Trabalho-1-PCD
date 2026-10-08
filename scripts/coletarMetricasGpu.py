#!/usr/bin/env python3
"""Coleta amostras opcionais de utilização, memória, temperatura e potência via nvidia-smi."""

import argparse
import csv
import datetime as dataHora
from pathlib import Path
import shutil
import subprocess
import sys
import time


camposConsulta = [
    "timestamp", "index", "name", "utilization.gpu", "utilization.memory",
    "memory.used", "memory.total", "power.draw", "temperature.gpu",
]


# Consulta uma amostra instantânea sem substituir valores não suportados pelo driver.
def coletarAmostra():
    if shutil.which("nvidia-smi") is None:
        raise RuntimeError("nvidia-smi não foi encontrado no PATH.")
    comando = ["nvidia-smi", f"--query-gpu={','.join(camposConsulta)}", "--format=csv,noheader,nounits"]
    processo = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if processo.returncode != 0:
        raise RuntimeError(processo.stderr.strip() or "nvidia-smi falhou.")
    linhas = []
    for linhaTexto in processo.stdout.splitlines():
        valores = next(csv.reader([linhaTexto], skipinitialspace=True), [])
        linha = {campo: (valores[indice] if indice < len(valores) else "") for indice, campo in enumerate(camposConsulta)}
        linhas.append(linha)
    return linhas


# Coleta amostras durante um intervalo opcional para acompanhar um benchmark externo.
def executarPrograma():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("results/raw/monitoramento_gpu.csv"))
    parser.add_argument("--duracao-segundos", dest="duracaoSegundos", type=float, default=0.0)
    parser.add_argument("--intervalo-segundos", dest="intervaloSegundos", type=float, default=0.2)
    argumentos = parser.parse_args()
    if argumentos.duracaoSegundos < 0 or argumentos.intervaloSegundos <= 0:
        raise SystemExit("A duração deve ser não negativa e o intervalo deve ser positivo.")

    argumentos.saida.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic()
    primeiraAmostra = True
    with argumentos.saida.open("w", newline="", encoding="utf-8") as arquivoCsv:
        escritor = None
        while primeiraAmostra or time.monotonic() - inicio < argumentos.duracaoSegundos:
            amostras = coletarAmostra()
            if escritor is None:
                campos = camposConsulta + ["timestampColeta"]
                escritor = csv.DictWriter(arquivoCsv, fieldnames=campos)
                escritor.writeheader()
            timestampColeta = dataHora.datetime.now().astimezone().isoformat(timespec="milliseconds")
            for amostra in amostras:
                amostra["timestampColeta"] = timestampColeta
                escritor.writerow(amostra)
            arquivoCsv.flush()
            primeiraAmostra = False
            if argumentos.duracaoSegundos > 0:
                time.sleep(argumentos.intervaloSegundos)
    print(f"Monitoramento salvo em: {argumentos.saida}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(executarPrograma())
    except (OSError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1)
