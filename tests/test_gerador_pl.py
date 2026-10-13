"""
Testes do gerador de PL com IA. Em vez do Codex de verdade (que gastaria a
assinatura a cada execução), usamos um "codex" falso que só grava a resposta.
"""

import json
import sys

import pytest

from simplexlab import gerador_pl
from simplexlab.gerador_pl import ErroIA, gerar_pl

MODELO = "# x1: mesas\n# x2: cadeiras\nmax z = 30x1 + 20x2\ns.a.\n4x1 + 3x2 <= 240\n2x1 + x2 <= 100"


# Cria um executável que imita o "codex exec": guarda os argumentos e o
# prompt recebidos e escreve a resposta no arquivo indicado em -o.
@pytest.fixture
def codex_falso(tmp_path, monkeypatch):
    registro = tmp_path / "chamada.json"

    def criar(resposta, codigo_saida=0, stderr=""):
        programa = tmp_path / "codex_falso.py"
        programa.write_text(
            "import json, sys\n"
            "args = sys.argv[1:]\n"
            "prompt = sys.stdin.read()\n"
            f"json.dump({{'args': args, 'prompt': prompt}}, open({str(registro)!r}, 'w'))\n"
            f"sys.stderr.write({stderr!r})\n"
            f"if {codigo_saida}: sys.exit({codigo_saida})\n"
            f"open(args[args.index('-o') + 1], 'w').write({resposta!r})\n",
            encoding="utf-8",
        )
        # Script de shell que chama o Python (o caminho pode ter espaços).
        script = tmp_path / "codex"
        script.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{programa}" "$@"\n')
        script.chmod(0o755)
        monkeypatch.setenv("SIMPLEXLAB_CODEX", str(script))
        return lambda: json.loads(registro.read_text())

    return criar


def test_gera_modelo_a_partir_de_texto(codex_falso):
    chamada = codex_falso(json.dumps({"titulo": "Mesas e cadeiras", "modelo": MODELO}))

    gerado = gerar_pl("Uma fábrica produz mesas e cadeiras...")

    assert gerado.titulo == "Mesas e cadeiras"
    assert gerado.texto == MODELO
    assert gerado.erro is None

    args = chamada()["args"]
    assert args[0] == "exec"
    assert "--output-schema" in args and "--ephemeral" in args
    assert args[args.index("--sandbox") + 1] == "read-only"
    assert "Uma fábrica produz mesas e cadeiras" in chamada()["prompt"]


def test_imagens_vao_como_anexo(codex_falso, tmp_path):
    chamada = codex_falso(json.dumps({"titulo": "Print", "modelo": MODELO}))
    imagem = tmp_path / "questao.png"
    imagem.write_bytes(b"")

    gerar_pl("", [imagem])

    args = chamada()["args"]
    assert args[args.index("-i") + 1] == str(imagem)
    assert "veja a imagem anexada" in chamada()["prompt"]


def test_modelo_fora_do_formato_volta_com_erro(codex_falso):
    codex_falso(json.dumps({"titulo": "Ruim", "modelo": "maximizar o lucro"}))
    gerado = gerar_pl("enunciado")
    assert gerado.texto == "maximizar o lucro"
    assert gerado.erro.startswith("Linha 1")


def test_resposta_que_nao_e_json(codex_falso):
    codex_falso("não é json")
    with pytest.raises(ErroIA, match="formato esperado"):
        gerar_pl("enunciado")


def test_codex_sem_login(codex_falso):
    codex_falso("", codigo_saida=1, stderr="Error: not logged in, run codex login\n")
    with pytest.raises(ErroIA, match="codex login"):
        gerar_pl("enunciado")


def test_sem_enunciado():
    with pytest.raises(ErroIA, match="Cole o texto"):
        gerar_pl("   ")


def test_codex_nao_instalado(monkeypatch):
    monkeypatch.delenv("SIMPLEXLAB_CODEX", raising=False)
    monkeypatch.setattr(gerador_pl.shutil, "which", lambda _nome: None)
    with pytest.raises(ErroIA, match="npm install -g @openai/codex"):
        gerar_pl("enunciado")
