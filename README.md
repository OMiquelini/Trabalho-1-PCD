# Mandelbrot CUDA

Projeto simples para comparar o cálculo do conjunto de Mandelbrot em uma versão sequencial na CPU, uma versão paralela com OpenMP e uma versão paralela usando CUDA.

## Requisitos

- CMake 3.24 ou mais recente;
- compilador com suporte a C++17;
- CUDA Toolkit e uma GPU NVIDIA;
- OpenMP disponível no compilador C++;
- Python 3.9 ou mais recente para executar o script de testes.

## Compilação

Na pasta do projeto, execute:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

## Como usar

Para conferir se CPU e GPU calculam os mesmos valores:

```powershell
build/Release/validarCpuGpu.exe --largura 256 --altura 256 --max-iter 200 --bloco-x 16 --bloco-y 16
```

Esse comando também compara a CPU sequencial com a versão OpenMP, pixel a pixel.

Na compilação CUDA, a fusão de operações de ponto flutuante é desativada para manter a comparação pixel a pixel entre CPU e GPU.

Para executar um teste rápido:

```powershell
py -3 scripts/executarExperimentos.py --rapido
```

Para executar o teste completo:

```powershell
py -3 scripts/executarExperimentos.py
```

O teste inclui as versões sequencial, OpenMP e CUDA, embaralha as configurações paralelas e pode testar as regiões `padrao` e `zoom`. Para medir a energia da GPU durante um comando:

```powershell
py -3 scripts/medirEnergia.py --saida results/raw/energia_cuda.csv -- build/Release/benchmarkCuda.exe --largura 1920 --altura 1080 --max-iter 1000 --repeticoes 10 --aquecimentos 1 --bloco-x 16 --bloco-y 16 --formato csv
```

O resumo apresenta energia em joules, potência média em watts e EDP em joule-segundo. A janela de energia é o processo completo executado pelo comando.

A medição usa a potência reportada pela GPU NVIDIA e representa uma estimativa da energia da GPU, não do sistema inteiro. O intervalo de amostragem pode afetar a precisão em execuções muito curtas.

Nos CSVs, `tempoComparavelMs` mede somente o cálculo da CPU/OpenMP ou o kernel CUDA. Para comparar energia com tempo, use `duracaoS` do resumo de energia, pois ele corresponde ao processo completo monitorado.

Para gerar imagens de uma execução, use o script `scripts/gerarImagens.py` com os executáveis já compilados. Os arquivos são salvos na pasta indicada por `--saida`.

Os arquivos CSV gerados ficam em `results/raw/`. Também é possível escolher a resolução, o número de repetições e o número máximo de iterações usando `--resolucoes`, `--repeticoes`, `--aquecimentos` e `--max-iter`.

Em geradores do Visual Studio, os executáveis normalmente ficam em `build/Release`. Em outros geradores, eles podem ficar diretamente em `build`.
