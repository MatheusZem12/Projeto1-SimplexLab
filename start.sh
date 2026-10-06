#!/usr/bin/env bash
# Prepara o ambiente (só na primeira vez) e abre o SimplexLab.
set -e
cd "$(dirname "$0")"

# Cria o ambiente virtual com um Python que já vem com Tkinter.
if [ ! -x .venv/bin/python ]; then
    echo "Preparando o ambiente pela primeira vez..."
    if command -v uv >/dev/null 2>&1; then
        uv venv -q -p 3.13 --managed-python .venv
        uv pip install -q -p .venv/bin/python -r requirements.txt
    else
        python3 -m venv .venv
        .venv/bin/pip install -q -r requirements.txt
    fi
fi

# Confere se o Tkinter está disponível antes de abrir a tela.
if ! .venv/bin/python -c "import tkinter" 2>/dev/null; then
    echo "Erro: o Python do ambiente não tem Tkinter."
    echo "Instale o uv (https://docs.astral.sh/uv/) ou o pacote tk do sistema,"
    echo "apague a pasta .venv e rode este script de novo."
    exit 1
fi

.venv/bin/python main.py
