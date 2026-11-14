"""
Testes do gerador de PL com IA. Em vez da API de verdade (que gastaria créditos
a cada execução), usamos um cliente falso que só devolve a resposta combinada.
"""

import base64
import io
import json
import sys
import threading
import types
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from PIL import Image

from simplexlab import gerador_pl
from simplexlab.gerador_pl import ErroIA, ModeloGerado, gerar_pl, obter_chave

MODELO = "# x1: mesas\n# x2: cadeiras\nmax z = 30x1 + 20x2\ns.a.\n4x1 + 3x2 <= 240\n2x1 + x2 <= 100"
REQUISICAO = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


# Monta uma mensagem no formato que o SDK devolve em get_final_message().
def resposta(estruturado=None, texto=None, stop_reason="end_turn", entrada=1000, saida=500):
    texto = json.dumps(estruturado) if texto is None else texto
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking=""),
                 SimpleNamespace(type="text", text=texto)],
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=entrada, output_tokens=saida),
    )


class FluxoFalso:
    def __init__(self, mensagem):
        self._mensagem = mensagem

    def __enter__(self):
        return self

    def __exit__(self, *_erro):
        return False

    def __iter__(self):
        return iter(["evento"])

    def get_final_message(self):
        return self._mensagem


# Imita anthropic.Anthropic(): guarda os argumentos de cada chamada.
class ClienteFalso:
    def __init__(self, mensagem=None, erro=None):
        self.chamadas = []
        self._mensagem = mensagem
        self._erro = erro
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **argumentos):
        self.chamadas.append(argumentos)
        if self._erro is not None:
            raise self._erro
        return FluxoFalso(self._mensagem)


@pytest.fixture
def ia_falsa(monkeypatch):
    def criar(mensagem=None, erro=None):
        cliente = ClienteFalso(mensagem, erro)
        monkeypatch.setattr(gerador_pl, "_criar_cliente", lambda: cliente)
        return cliente
    return criar


def test_gera_modelo_a_partir_de_texto(ia_falsa):
    cliente = ia_falsa(resposta({"titulo": "Mesas e cadeiras", "modelo": MODELO}))

    gerado = gerar_pl("Uma fábrica produz mesas e cadeiras...")

    assert gerado.titulo == "Mesas e cadeiras"
    assert gerado.texto == MODELO
    assert gerado.erro is None
    assert (gerado.tokens_entrada, gerado.tokens_saida) == (1000, 500)

    chamada = cliente.chamadas[0]
    assert chamada["model"] == gerador_pl.MODELO_IA
    assert chamada["system"] == gerador_pl.INSTRUCOES
    assert chamada["output_config"]["format"]["schema"]["required"] == ["titulo", "modelo"]
    assert chamada["fallbacks"] == "default"
    conteudo = chamada["messages"][0]["content"]
    assert conteudo[-1]["type"] == "text"
    assert "Uma fábrica produz mesas e cadeiras" in conteudo[-1]["text"]


def test_imagens_vao_em_memoria_e_nada_e_gravado(ia_falsa, tmp_path, monkeypatch):
    cliente = ia_falsa(resposta({"titulo": "Print", "modelo": MODELO}))
    arquivo_bmp = tmp_path / "questao.bmp"
    Image.new("RGB", (40, 30), "white").save(arquivo_bmp)
    print_grande = Image.new("RGB", (4000, 1000), "white")
    pasta_trabalho = tmp_path / "trabalho"
    pasta_trabalho.mkdir()
    monkeypatch.chdir(pasta_trabalho)

    gerar_pl("", [print_grande, arquivo_bmp])

    conteudo = cliente.chamadas[0]["messages"][0]["content"]
    assert [bloco["type"] for bloco in conteudo] == ["image", "image", "text"]
    assert "veja a imagem anexada" in conteudo[-1]["text"]
    tamanhos = []
    for bloco in conteudo[:2]:
        assert bloco["source"]["media_type"] == "image/png"
        dados = base64.standard_b64decode(bloco["source"]["data"])
        tamanhos.append(Image.open(io.BytesIO(dados)).size)
    assert tamanhos == [(2048, 512), (40, 30)]
    # A imagem original não é alterada e nenhum arquivo é criado.
    assert print_grande.size == (4000, 1000)
    assert list(pasta_trabalho.iterdir()) == []


def test_modelo_fora_do_formato_volta_com_erro(ia_falsa):
    ia_falsa(resposta({"titulo": "Ruim", "modelo": "maximizar o lucro"}))
    gerado = gerar_pl("enunciado")
    assert gerado.texto == "maximizar o lucro"
    assert gerado.erro.startswith("Linha 1")


def test_resposta_que_nao_e_json(ia_falsa):
    ia_falsa(resposta(texto="não é json"))
    with pytest.raises(ErroIA, match="formato esperado"):
        gerar_pl("enunciado")


def test_recusa_da_ia(ia_falsa):
    ia_falsa(resposta(texto="", stop_reason="refusal"))
    with pytest.raises(ErroIA, match="recusou"):
        gerar_pl("enunciado")


def test_resposta_cortada(ia_falsa):
    ia_falsa(resposta(texto='{"titulo": "Cor', stop_reason="max_tokens"))
    with pytest.raises(ErroIA, match="cortada"):
        gerar_pl("enunciado")


def test_cancelar_interrompe_a_geracao(ia_falsa):
    ia_falsa(resposta({"titulo": "Mesas", "modelo": MODELO}))
    cancelado = threading.Event()
    cancelado.set()
    with pytest.raises(ErroIA, match="cancelada"):
        gerar_pl("enunciado", cancelado=cancelado)


@pytest.mark.parametrize("erro, mensagem", [
    (anthropic.AuthenticationError(
        "invalid x-api-key", response=httpx2.Response(401, request=REQUISICAO), body=None),
     "chave de API foi recusada"),
    (anthropic.BadRequestError(
        "You have reached your specified workspace API usage limits.",
        response=httpx2.Response(400, request=REQUISICAO), body=None),
     "limite de gasto"),
    (anthropic.APIConnectionError(request=REQUISICAO), "conexão com a internet"),
])
def test_erros_da_api_viram_mensagens(ia_falsa, erro, mensagem):
    ia_falsa(erro=erro)
    with pytest.raises(ErroIA, match=mensagem):
        gerar_pl("enunciado")


def test_sem_enunciado():
    with pytest.raises(ErroIA, match="Cole o texto"):
        gerar_pl("   ")


def test_sem_chave(monkeypatch):
    monkeypatch.setitem(sys.modules, "simplexlab._chave_embutida", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ErroIA, match="Chave de API não configurada"):
        obter_chave()


def test_chave_embutida_tem_prioridade(monkeypatch):
    modulo = types.ModuleType("simplexlab._chave_embutida")
    modulo.chave = lambda: "sk-ant-embutida"
    monkeypatch.setitem(sys.modules, "simplexlab._chave_embutida", modulo)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ambiente")
    assert obter_chave() == "sk-ant-embutida"


def test_chave_da_variavel_de_ambiente(monkeypatch):
    monkeypatch.setitem(sys.modules, "simplexlab._chave_embutida", None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", " sk-ant-ambiente\n")
    assert obter_chave() == "sk-ant-ambiente"


def test_custo_estimado():
    gerado = ModeloGerado("Mesas", MODELO, tokens_entrada=1000, tokens_saida=500)
    assert gerado.custo_estimado == pytest.approx(0.014)
