"""
Gera o executável do SimplexLab para Windows, com a chave de API embutida, e
monta o zip de entrega.

Uso (no Windows, com as dependências e o PyInstaller instalados):
    1. Salve a chave de API (sk-ant-...) no arquivo chave_api.txt, na raiz do
       projeto. Esse arquivo está no .gitignore: nunca envie ele para o GitHub.
    2. python gerar_executavel.py

Resultado: dist/SimplexLab.exe e dist/SimplexLab.zip (executável + LEIA-ME.txt).

A chave vai para dentro do executável embaralhada (não fica em texto puro), mas
quem tiver o .exe consegue extraí-la com algum esforço. Por isso a chave deve
ficar em um workspace com limite de gasto e ser desativada depois da avaliação.
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent
ARQUIVO_CHAVE = RAIZ / "chave_api.txt"
MODULO_CHAVE = RAIZ / "simplexlab" / "_chave_embutida.py"
PASTA_BUILD = RAIZ / "build"
PASTA_DIST = RAIZ / "dist"
NOME = "SimplexLab"

LEIA_ME = """\
SimplexLab - Pesquisa Operacional

Para abrir: dê dois cliques em SimplexLab.exe. Não precisa instalar nada.
O programa demora alguns segundos para abrir na primeira vez.

Se o Windows mostrar "O Windows protegeu o computador", clique em
"Mais informações" e depois em "Executar assim mesmo" (o executável não é
assinado digitalmente, por isso o aviso).

O botão "Importar enunciado com IA" precisa de internet. A chave de API já vem
dentro do programa, não é preciso configurar nada. O programa não grava
arquivos nem histórico no computador.
"""


def ler_chave():
    if not ARQUIVO_CHAVE.exists():
        sys.exit(f"Crie o arquivo {ARQUIVO_CHAVE.name} com a chave de API (sk-ant-...).")
    chave = ARQUIVO_CHAVE.read_text(encoding="utf-8-sig").strip()  # -sig: tolera o BOM do Bloco de Notas
    if not chave.startswith("sk-ant-"):
        sys.exit(f"O {ARQUIVO_CHAVE.name} não parece ter uma chave de API (deve começar com sk-ant-).")
    return chave


# Grava a chave embaralhada com uma máscara aleatória (XOR), para ela não
# aparecer em texto puro dentro do executável.
def escrever_modulo_chave(chave):
    dados = chave.encode("utf-8")
    mascara = os.urandom(len(dados))
    embaralhado = bytes(a ^ b for a, b in zip(dados, mascara))
    MODULO_CHAVE.write_text(
        "# Gerado por gerar_executavel.py e apagado ao final. NÃO versionar.\n"
        f"_MASCARA = {mascara!r}\n"
        f"_DADOS = {embaralhado!r}\n\n\n"
        "def chave():\n"
        "    return bytes(a ^ b for a, b in zip(_DADOS, _MASCARA)).decode('utf-8')\n",
        encoding="utf-8",
    )


# Apaga tudo o que tem a chave, menos o executável: o módulo gerado, os .pyc
# dele e a pasta de trabalho do PyInstaller.
def limpar_rastros_da_chave():
    MODULO_CHAVE.unlink(missing_ok=True)
    for compilado in (RAIZ / "simplexlab" / "__pycache__").glob("_chave_embutida*.pyc"):
        compilado.unlink()
    shutil.rmtree(PASTA_BUILD, ignore_errors=True)


def gerar_executavel():
    PyInstaller.__main__.run([
        str(RAIZ / "main.py"),
        "--name", NOME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath", str(PASTA_DIST),
        "--workpath", str(PASTA_BUILD),
        "--specpath", str(PASTA_BUILD),
        "--hidden-import", "simplexlab._chave_embutida",
        "--exclude-module", "pytest",
    ])
    return PASTA_DIST / f"{NOME}.exe"


def montar_zip(executavel):
    destino = PASTA_DIST / f"{NOME}.zip"
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
        arquivo_zip.write(executavel, f"{NOME}/{executavel.name}")
        arquivo_zip.writestr(f"{NOME}/LEIA-ME.txt", LEIA_ME.replace("\n", "\r\n"))
    return destino


def main():
    escrever_modulo_chave(ler_chave())
    try:
        executavel = gerar_executavel()
    finally:
        limpar_rastros_da_chave()
    destino = montar_zip(executavel)
    tamanho = destino.stat().st_size / 1_000_000
    print(f"\nPronto: {executavel}\nZip de entrega: {destino} ({tamanho:.1f} MB)")


if __name__ == "__main__":
    main()
