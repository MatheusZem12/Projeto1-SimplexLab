"""
Geração do modelo de PL a partir de um enunciado (texto e/ou imagem) usando IA.

Usamos a API da Anthropic (modelo Claude) pelo SDK oficial "anthropic". A chave
de API vem, nesta ordem:
    1. da chave embutida no executável (gerada pelo gerar_executavel.py);
    2. da variável de ambiente ANTHROPIC_API_KEY (para rodar pelo código-fonte).

Nada é gravado em disco: o enunciado e as imagens vão da memória direto para a
API, e a resposta só volta para a tela. Não existe histórico das importações.
"""

import base64
import io
import json
import os
from dataclasses import dataclass

import anthropic
from PIL import Image

from simplexlab.modelo import ErroLeitura, ler_modelo

MODELO_IA = "claude-opus-5-5"
ESFORCO = "high"           # quanto o modelo pensa antes de responder
MAX_TOKENS = 16000         # teto da resposta (inclui o raciocínio); limita o custo por chamada
TEMPO_LIMITE = 300         # segundos
LADO_MAXIMO_IMAGEM = 2048  # px; imagens maiores são reduzidas antes do envio
TAMANHO_MAXIMO_PNG = 3_500_000  # bytes; acima disso a imagem vai como JPEG

# Preço do claude-opus-5-5 em US$ por milhão de tokens (usado só para estimar o custo).
PRECO_ENTRADA = 4.00
PRECO_SAIDA = 20.00

INSTRUCOES = """\
Você é um professor de Pesquisa Operacional. Leia o enunciado enviado (texto e/ou
imagem) e formule o modelo de Programação Linear.

Responda só no formato JSON pedido, com os campos:
- "titulo": um nome curto para o problema (até 40 caracteres, em português);
- "modelo": o modelo de PL, exatamente no formato abaixo.

Formato do campo "modelo" (uma informação por linha):
# x1: significado da variável x1
# x2: significado da variável x2
max z = 3x1 + 5x2
s.a.
x1 <= 4
2x2 <= 12
3x1 + 2x2 <= 18
x1, x2 >= 0

Regras do formato:
- comece com uma linha de comentário (#) para cada variável dizendo o que ela significa;
- a primeira linha que não é comentário é a função objetivo, começando com "max z =" ou "min z =";
- use as variáveis x1, x2, x3, ... e coloque o número colado na variável (3x1, não 3*x1);
- uma restrição por linha, usando só <=, >= ou =, com as variáveis à esquerda e o número à direita;
- números com ponto decimal (0.5) ou fração (1/2), sem unidades, sem "R$" e sem separador de milhar;
- não escreva explicações fora dos comentários.

Se o enunciado não tiver informação suficiente para um modelo de PL, faça a
melhor interpretação possível e explique a suposição em um comentário (#).
"""

ESQUEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"},
        "modelo": {"type": "string"},
    },
    "required": ["titulo", "modelo"],
    "additionalProperties": False,
}


class ErroIA(Exception):
    pass


# Modelo devolvido pela IA. "erro" guarda a mensagem do leitor quando o texto
# gerado não estiver no formato certo; nesse caso o usuário pode corrigir à mão.
@dataclass
class ModeloGerado:
    titulo: str
    texto: str
    erro: str | None = None
    tokens_entrada: int = 0
    tokens_saida: int = 0

    # Custo aproximado da chamada, em dólares.
    @property
    def custo_estimado(self):
        return (self.tokens_entrada * PRECO_ENTRADA + self.tokens_saida * PRECO_SAIDA) / 1_000_000


# Chave de API: primeiro a embutida no executável, depois a variável de ambiente.
def obter_chave():
    try:
        from simplexlab._chave_embutida import chave as chave_embutida
    except ImportError:
        chave_embutida = None
    chave = (chave_embutida() if chave_embutida else "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not chave.strip():
        raise ErroIA(
            "Chave de API não configurada.\n\n"
            "Rodando pelo código-fonte, defina a variável de ambiente ANTHROPIC_API_KEY."
        )
    return chave.strip()


def _criar_cliente():
    return anthropic.Anthropic(api_key=obter_chave(), timeout=TEMPO_LIMITE, max_retries=2)


# Envia o enunciado para o Claude e devolve o modelo de PL gerado.
# "imagens" aceita imagens do Pillow (já em memória) ou caminhos de arquivo.
# "cancelado" é um threading.Event: se for marcado, a geração é interrompida.
def gerar_pl(texto="", imagens=(), cancelado=None):
    texto = texto.strip()
    if not texto and not imagens:
        raise ErroIA("Cole o texto do enunciado ou uma imagem antes de gerar o PL.")

    conteudo = [_bloco_imagem(imagem) for imagem in imagens]
    conteudo.append({"type": "text", "text": "Enunciado:\n" + (texto or "(veja a imagem anexada)")})

    cliente = _criar_cliente()
    try:
        # Usamos streaming para poder interromper no meio quando o usuário cancela.
        # "fallbacks" faz a própria API tentar outro modelo se este recusar o pedido.
        with cliente.beta.messages.stream(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            system=INSTRUCOES,
            messages=[{"role": "user", "content": conteudo}],
            output_config={
                "effort": ESFORCO,
                "format": {"type": "json_schema", "schema": ESQUEMA_RESPOSTA},
            },
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as fluxo:
            for _evento in fluxo:
                if cancelado is not None and cancelado.is_set():
                    raise ErroIA("Geração cancelada.")
            resposta = fluxo.get_final_message()
    except anthropic.APIError as erro:
        raise ErroIA(_mensagem_de_falha(erro)) from erro

    if resposta.stop_reason == "refusal":
        raise ErroIA("A IA se recusou a responder este enunciado. Tente reescrever o texto.")
    if resposta.stop_reason == "max_tokens":
        raise ErroIA("A resposta da IA ficou longa demais e foi cortada. Tente de novo.")

    texto_resposta = "".join(bloco.text for bloco in resposta.content if bloco.type == "text")
    gerado = _interpretar_resposta(texto_resposta)
    gerado.tokens_entrada = resposta.usage.input_tokens
    gerado.tokens_saida = resposta.usage.output_tokens
    return gerado


# Converte a imagem em um bloco base64 da API, sem gravar nada em disco.
# Imagens grandes são reduzidas (economiza envio) e formatos que a API não
# aceita (BMP, por exemplo) viram PNG.
def _bloco_imagem(imagem):
    try:
        if isinstance(imagem, Image.Image):
            imagem = imagem.copy()
        else:
            with Image.open(imagem) as aberta:
                aberta.load()
                imagem = aberta.copy()
    except OSError as erro:
        raise ErroIA(f"Não consegui abrir a imagem: {erro}") from erro

    imagem.thumbnail((LADO_MAXIMO_IMAGEM, LADO_MAXIMO_IMAGEM))
    if imagem.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
        imagem = imagem.convert("RGB")

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    tipo = "image/png"
    if buffer.tell() > TAMANHO_MAXIMO_PNG:
        buffer = io.BytesIO()
        imagem.convert("RGB").save(buffer, format="JPEG", quality=90)
        tipo = "image/jpeg"

    dados = base64.standard_b64encode(buffer.getvalue()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": tipo, "data": dados}}


# Traduz os erros da API para uma mensagem curta em português.
def _mensagem_de_falha(erro):
    if isinstance(erro, anthropic.AuthenticationError):
        return "A chave de API foi recusada (inválida, expirada ou desativada)."
    if isinstance(erro, anthropic.PermissionDeniedError):
        return "A chave de API não tem permissão para usar este modelo."
    if isinstance(erro, anthropic.RateLimitError):
        return "Muitas requisições em pouco tempo. Espere um minuto e tente de novo."
    if isinstance(erro, anthropic.APITimeoutError):
        return f"A IA passou de {TEMPO_LIMITE} segundos sem responder. Tente de novo."
    if isinstance(erro, anthropic.APIConnectionError):
        return "Não consegui falar com a API da Anthropic. Confira a conexão com a internet."
    if isinstance(erro, anthropic.APIStatusError):
        detalhe = str(erro.message)
        minusculo = detalhe.lower()
        if "usage limit" in minusculo or "spend limit" in minusculo or "credit balance" in minusculo:
            return "O limite de gasto da chave de API do projeto foi atingido.\n\n" + detalhe
        if erro.status_code >= 500:
            return f"A API da Anthropic está instável agora (erro {erro.status_code}). Tente de novo."
        return f"A API retornou um erro ({erro.status_code}):\n\n{detalhe}"
    return f"Erro ao chamar a IA: {erro}"


# Lê o JSON devolvido e confere se o modelo está no formato que o leitor aceita.
def _interpretar_resposta(conteudo):
    try:
        dados = json.loads(conteudo)
        titulo = str(dados["titulo"]).strip() or "Enunciado importado"
        modelo = str(dados["modelo"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as erro:
        raise ErroIA(f"A resposta da IA não veio no formato esperado:\n\n{conteudo}") from erro

    gerado = ModeloGerado(titulo=titulo, texto=modelo)
    try:
        ler_modelo(modelo)
    except ErroLeitura as erro:
        gerado.erro = str(erro)
    return gerado
