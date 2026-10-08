#!/usr/bin/env python3
"""Gera imagens PNG coloridas a partir das matrizes Mandelbrot CPU/CUDA."""

import argparse
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib


def localizarExecutavel(pastaBuild, nome):
    candidatos = [
        pastaBuild / nome,
        pastaBuild / f"{nome}.exe",
        pastaBuild / "Release" / nome,
        pastaBuild / "Release" / f"{nome}.exe",
        pastaBuild / "Debug" / nome,
        pastaBuild / "Debug" / f"{nome}.exe",
    ]
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    encontrados = [caminho for caminho in pastaBuild.rglob(f"{nome}*") if caminho.is_file()]
    if encontrados:
        return encontrados[0]
    raise FileNotFoundError(f"Executável não encontrado: {nome} em {pastaBuild}")


def lerToken(dados, posicao):
    tamanho = len(dados)
    while posicao < tamanho:
        if dados[posicao] in b" \t\r\n":
            posicao += 1
        elif dados[posicao] == ord("#"):
            while posicao < tamanho and dados[posicao] not in b"\r\n":
                posicao += 1
        else:
            break
    inicio = posicao
    while posicao < tamanho and dados[posicao] not in b" \t\r\n":
        posicao += 1
    return dados[inicio:posicao].decode("ascii"), posicao


def lerPgm(caminho):
    dados = caminho.read_bytes()
    posicao = 0
    magic, posicao = lerToken(dados, posicao)
    largura, posicao = lerToken(dados, posicao)
    altura, posicao = lerToken(dados, posicao)
    maximo, posicao = lerToken(dados, posicao)
    if magic != "P5":
        raise ValueError(f"Formato de imagem não suportado: {magic}")
    largura = int(largura)
    altura = int(altura)
    maximo = int(maximo)
    if maximo != 255:
        raise ValueError("O gerador espera PGM com profundidade de 8 bits.")
    if posicao >= len(dados) or dados[posicao] not in b" \t\r\n":
        raise ValueError("Cabeçalho PGM sem separador antes dos pixels.")
    posicao += 1
    quantidade = largura * altura
    pixels = dados[posicao:posicao + quantidade]
    if len(pixels) != quantidade:
        raise ValueError("Imagem PGM truncada.")
    return largura, altura, list(pixels)


def corFractal(valor):
    if valor >= 255:
        return 2, 5, 18
    t = max(0.0, min(1.0, valor / 255.0))
    vermelho = int(255 * (9.0 * (1.0 - t) * t * t * t))
    verde = int(255 * (15.0 * (1.0 - t) * (1.0 - t) * t * t))
    azul = int(255 * (8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t))
    return min(255, vermelho), min(255, verde), min(255, azul)


def converterCores(pixels):
    coloridos = bytearray()
    for pixel in pixels:
        coloridos.extend(corFractal(pixel))
    return bytes(coloridos)


def escreverPng(caminho, largura, altura, pixelsRgb):
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xffffffff)

    linhas = bytearray()
    passo = largura * 3
    for inicio in range(0, len(pixelsRgb), passo):
        linhas.append(0)
        linhas.extend(pixelsRgb[inicio:inicio + passo])
    cabecalho = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", cabecalho) + bloco(b"IDAT", zlib.compress(bytes(linhas), 9)) + bloco(b"IEND", b"")
    caminho.write_bytes(png)


def escreverPgm(caminho, largura, altura, pixels):
    caminho.write_bytes(f"P5\n{largura} {altura}\n255\n".encode("ascii") + bytes(pixels))


def gerarImagem(executavel, implementacao, argumentos, pastaSaida, pastaTemporaria):
    nome = f"mandelbrot_{implementacao}_{argumentos.largura}x{argumentos.altura}_iter{argumentos.maxIter}"
    if implementacao == "cuda":
        nome += f"_bloco{argumentos.blocoX}x{argumentos.blocoY}"
    caminhoPgm = pastaTemporaria / f"{nome}.pgm"
    comando = [
        str(executavel),
        "--largura", str(argumentos.largura),
        "--altura", str(argumentos.altura),
        "--max-iter", str(argumentos.maxIter),
        "--repeticoes", "1",
        "--aquecimentos", "0",
        "--formato", "texto",
        "--imagem", str(caminhoPgm),
    ]
    if implementacao == "cuda":
        comando.extend(["--bloco-x", str(argumentos.blocoX), "--bloco-y", str(argumentos.blocoY)])
    processo = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if processo.returncode != 0:
        raise RuntimeError(processo.stderr.strip() or processo.stdout.strip() or f"Falha em {implementacao}.")
    largura, altura, pixels = lerPgm(caminhoPgm)
    caminhoPng = pastaSaida / f"{nome}.png"
    escreverPng(caminhoPng, largura, altura, converterCores(pixels))
    if argumentos.salvarPgm:
        escreverPgm(pastaSaida / f"{nome}.pgm", largura, altura, pixels)
    print(f"Imagem {implementacao} salva em: {caminhoPng}")


def executarPrograma():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", dest="pastaBuild", type=Path, default=raiz / "build")
    parser.add_argument("--saida", dest="pastaSaida", type=Path, default=raiz / "results" / "images")
    parser.add_argument("--largura", type=int, default=1024)
    parser.add_argument("--altura", type=int, default=768)
    parser.add_argument("--max-iter", dest="maxIter", type=int, default=1000)
    parser.add_argument("--bloco-x", dest="blocoX", type=int, default=8)
    parser.add_argument("--bloco-y", dest="blocoY", type=int, default=8)
    parser.add_argument("--implementacoes", nargs="+", choices=["cpu", "cuda"], default=["cpu", "cuda"])
    parser.add_argument("--salvar-pgm", dest="salvarPgm", action="store_true", help="Preserva também a matriz PGM em escala de cinza.")
    argumentos = parser.parse_args()
    if argumentos.largura < 2 or argumentos.altura < 2 or argumentos.maxIter <= 0:
        raise SystemExit("Largura, altura e maxIter devem ser válidos.")
    if argumentos.blocoX <= 0 or argumentos.blocoY <= 0:
        raise SystemExit("As dimensões do bloco devem ser positivas.")
    argumentos.pastaSaida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mandelbrot_imagem_") as temporario:
        pastaTemporaria = Path(temporario)
        for implementacao in argumentos.implementacoes:
            executavel = localizarExecutavel(argumentos.pastaBuild, f"benchmark{implementacao.capitalize()}")
            gerarImagem(executavel, implementacao, argumentos, argumentos.pastaSaida, pastaTemporaria)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(executarPrograma())
    except (OSError, RuntimeError, ValueError, FileNotFoundError) as erro:
        print(f"Erro ao gerar imagens: {erro}")
        raise SystemExit(1)
