#!/usr/bin/env python3
"""Registra o ambiente de compilação e execução disponível na máquina."""

import argparse
import datetime as dataHora
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


# Executa um comando opcional e retorna sua saída sem interromper a coleta.
def executarComando(comando):
    caminhoComando = shutil.which(comando[0])
    if caminhoComando is None:
        return {"disponivel": False, "comando": comando, "saida": ""}
    processo = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {
        "disponivel": processo.returncode == 0,
        "codigoRetorno": processo.returncode,
        "comando": comando,
        "saida": (processo.stdout + processo.stderr).strip(),
    }


# Consulta dados básicos do sistema operacional e do processador.
def coletarSistema():
    nucleosLogicos = os.cpu_count()
    nucleosFisicos = None
    consultaNucleos = None
    if platform.system() == "Windows":
        consultaNucleos = executarComando([
            "powershell", "-NoProfile", "-Command",
            "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum",
        ])
        if consultaNucleos["disponivel"]:
            try:
                nucleosFisicos = int(consultaNucleos["saida"].splitlines()[-1].strip())
            except (ValueError, IndexError):
                nucleosFisicos = None
    else:
        consultaNucleos = executarComando(["lscpu", "-p=CORE"])
        if consultaNucleos["disponivel"]:
            nucleos = {
                linha.split(",")[-1].strip()
                for linha in consultaNucleos["saida"].splitlines()
                if linha.strip() and not linha.startswith("#")
            }
            nucleosFisicos = len(nucleos) if nucleos else None
    return {
        "sistemaOperacional": platform.platform(),
        "nomeSistema": platform.system(),
        "versaoSistema": platform.version(),
        "arquitetura": platform.machine(),
        "processador": platform.processor(),
        "nomeNo": platform.node(),
        "nucleosLogicos": nucleosLogicos,
        "nucleosFisicos": nucleosFisicos,
        "consultaNucleosFisicos": consultaNucleos,
        "python": sys.version,
    }


# Coleta informações da memória quando o sistema expõe o comando correspondente.
def coletarMemoria():
    if platform.system() == "Windows":
        consulta = executarComando(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        return {"consulta": consulta}
    consulta = executarComando(["free", "-b"])
    return {"consulta": consulta}


# Registra versões do compilador C++, do CUDA Toolkit e do driver NVIDIA.
def coletarFerramentas():
    return {
        "nvcc": executarComando(["nvcc", "--version"]),
        "compiladorGpp": executarComando(["g++", "--version"]),
        "compiladorCl": executarComando(["cl"]),
        "cmake": executarComando(["cmake", "--version"]),
        "nvidiaSmi": executarComando(["nvidia-smi"]),
        "nvidiaSmiGpu": executarComando([
            "nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]),
    }


# Coleta o commit atual sem exigir que o repositório seja Git.
def coletarGit():
    return {
        "commit": executarComando(["git", "rev-parse", "HEAD"]),
        "ramo": executarComando(["git", "branch", "--show-current"]),
    }


# Salva o inventário do ambiente em JSON para acompanhar os CSVs experimentais.
def executarPrograma():
    raizProjeto = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=raizProjeto / "results" / "environment.json")
    argumentos = parser.parse_args()
    registro = {
        "timestamp": dataHora.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sistema": coletarSistema(),
        "memoria": coletarMemoria(),
        "ferramentas": coletarFerramentas(),
        "git": coletarGit(),
        "flagsCompilacao": {
            "CXX": "-O3 -ffp-contract=off ou /O2 /fp:strict",
            "CUDA": "-O3 --fmad=false --prec-div=true --prec-sqrt=true",
        },
    }
    argumentos.saida.parent.mkdir(parents=True, exist_ok=True)
    with argumentos.saida.open("w", encoding="utf-8") as arquivoJson:
        json.dump(registro, arquivoJson, ensure_ascii=False, indent=2)
        arquivoJson.write("\n")
    print(f"Ambiente salvo em: {argumentos.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(executarPrograma())
