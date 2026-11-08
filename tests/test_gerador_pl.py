"""
Testes do gerador de PL com IA. Em vez do Claude de verdade (que gastaria a
assinatura a cada execução), usamos um "claude" falso que só imprime a resposta.
"""

import json
import sys

import pytest

from simplexlab import gerador_pl
from simplexlab.gerador_pl import ErroIA, gerar_pl

MODELO = "# x1: mesas\n# x2: cadeiras\nmax z = 30x1 + 20x2\ns.a.\n4x1 + 3x2 <= 240\n2x1 + x2 <= 100"


# Monta a saída que o "claude -p --output-format json" imprime.
def saida_claude(estruturado=None, resultado="", erro=False):
    dados = {"type": "result", "is_error": erro, "result": resultado}
    if estruturado is not None:
        dados["structured_output"] = estruturado
    return json.dumps(dados)


# Cria um executável que imita o "claude -p": guarda os argumentos, o prompt
# e a pasta de trabalho e imprime a resposta no stdout.
@pytest.fixture
def claude_falso(tmp_path, monkeypatch):
    registro = tmp_path / "chamada.json"

    def criar(resposta, codigo_saida=0, stderr=""):
        programa = tmp_path / "claude_falso.py"
        programa.write_text(
            "import json, os, sys\n"
            "args = sys.argv[1:]\n"
            "prompt = sys.stdin.read()\n"
            f"json.dump({{'args': args, 'prompt': prompt, 'cwd': os.getcwd()}},"
            f" open({str(registro)!r}, 'w'))\n"
            f"sys.stderr.write({stderr!r})\n"
            f"sys.stdout.write({resposta!r})\n"
            f"sys.exit({codigo_saida})\n",
            encoding="utf-8",
        )
        # Script de shell que chama o Python (o caminho pode ter espaços).
        script = tmp_path / "claude"
        script.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{programa}" "$@"\n')
        script.chmod(0o755)
        monkeypatch.setenv("SIMPLEXLAB_CLAUDE", str(script))
        # O histórico vai para a pasta temporária do teste, não para o projeto.
        monkeypatch.setattr(gerador_pl, "PASTA_HISTORICO", tmp_path / "historico_ia")
        return lambda: json.loads(registro.read_text())

    return criar


def test_gera_modelo_a_partir_de_texto(claude_falso):
    chamada = claude_falso(saida_claude({"titulo": "Mesas e cadeiras", "modelo": MODELO}))

    gerado = gerar_pl("Uma fábrica produz mesas e cadeiras...")

    assert gerado.titulo == "Mesas e cadeiras"
    assert gerado.texto == MODELO
    assert gerado.erro is None

    args = chamada()["args"]
    assert args[0] == "-p"
    assert args[args.index("--output-format") + 1] == "json"
    assert json.loads(args[args.index("--json-schema") + 1])["required"] == ["titulo", "modelo"]
    assert "--no-session-persistence" not in args
    assert chamada()["cwd"] == str(gerador_pl.PASTA_HISTORICO)
    assert "--tools=Read" in args
    assert "Uma fábrica produz mesas e cadeiras" in chamada()["prompt"]


def test_imagens_vao_para_a_pasta_de_trabalho(claude_falso, tmp_path):
    chamada = claude_falso(saida_claude({"titulo": "Print", "modelo": MODELO}))
    imagem = tmp_path / "questao.PNG"
    imagem.write_bytes(b"")

    gerar_pl("", [imagem])

    pastas = list(gerador_pl.PASTA_HISTORICO.glob("pl_*"))
    assert len(pastas) == 1
    assert sorted(a.name for a in pastas[0].iterdir()) == ["imagem1.png", "resposta.json"]
    prompt = chamada()["prompt"]
    assert "veja a imagem anexada" in prompt
    assert str(pastas[0] / "imagem1.png") in prompt and "Read" in prompt


def test_historico_guarda_resposta_e_session_id(claude_falso):
    saida = json.loads(saida_claude({"titulo": "Mesas", "modelo": MODELO}))
    saida["session_id"] = "abc-123"
    claude_falso(json.dumps(saida))

    gerar_pl("Uma fábrica produz mesas")
    gerar_pl("Outro enunciado no mesmo minuto")

    pastas = sorted(gerador_pl.PASTA_HISTORICO.glob("pl_*"))
    assert len(pastas) == 2 and pastas[1].name.endswith("_2")
    registro = json.loads((pastas[0] / "resposta.json").read_text(encoding="utf-8"))
    assert registro["session_id"] == "abc-123"
    assert registro["enunciado"] == "Uma fábrica produz mesas"
    assert registro["titulo"] == "Mesas" and registro["modelo"] == MODELO
    assert registro["retorno_claude"]["session_id"] == "abc-123"


def test_historico_guarda_erro(claude_falso):
    claude_falso("não é json")
    with pytest.raises(ErroIA):
        gerar_pl("enunciado")
    pasta = next(gerador_pl.PASTA_HISTORICO.glob("pl_*"))
    registro = json.loads((pasta / "resposta.json").read_text(encoding="utf-8"))
    assert "formato esperado" in registro["erro"]
    assert registro["retorno_claude"] == "não é json"


def test_aceita_resposta_em_texto_sem_structured_output(claude_falso):
    texto = "```json\n" + json.dumps({"titulo": "Texto", "modelo": MODELO}) + "\n```"
    claude_falso(saida_claude(resultado=texto))
    gerado = gerar_pl("enunciado")
    assert gerado.titulo == "Texto"
    assert gerado.texto == MODELO


def test_modelo_fora_do_formato_volta_com_erro(claude_falso):
    claude_falso(saida_claude({"titulo": "Ruim", "modelo": "maximizar o lucro"}))
    gerado = gerar_pl("enunciado")
    assert gerado.texto == "maximizar o lucro"
    assert gerado.erro.startswith("Linha 1")


def test_resposta_que_nao_e_json(claude_falso):
    claude_falso("não é json")
    with pytest.raises(ErroIA, match="formato esperado"):
        gerar_pl("enunciado")


def test_claude_sem_login(claude_falso):
    claude_falso(saida_claude(resultado="Not logged in · Please run /login", erro=True),
                 codigo_saida=1)
    with pytest.raises(ErroIA, match="/login"):
        gerar_pl("enunciado")


def test_sem_enunciado():
    with pytest.raises(ErroIA, match="Cole o texto"):
        gerar_pl("   ")


def test_claude_nao_instalado(monkeypatch):
    monkeypatch.delenv("SIMPLEXLAB_CLAUDE", raising=False)
    monkeypatch.setattr(gerador_pl.shutil, "which", lambda _nome: None)
    with pytest.raises(ErroIA, match="npm install -g @anthropic-ai/claude-code"):
        gerar_pl("enunciado")
