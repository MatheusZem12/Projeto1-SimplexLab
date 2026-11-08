"""
Geração do modelo de PL a partir de um enunciado (texto e/ou imagem) usando IA.

Em vez de usar uma chave de API, chamamos o Claude Code instalado na máquina
(comando "claude"), que usa a conta do Claude em que o usuário já fez login.
Assim nenhuma chave fica no projeto e o consumo sai da assinatura do usuário.

Pré-requisitos (uma vez só):
    npm install -g @anthropic-ai/claude-code
    claude            (e faça o login com /login)

Se o executável estiver em um lugar fora do PATH, informe o caminho na
variável de ambiente SIMPLEXLAB_CLAUDE.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from simplexlab.modelo import ErroLeitura, ler_modelo

TEMPO_LIMITE = 300  # segundos

# Histórico das importações. Cada geração ganha uma pasta própria, que nunca é
# apagada:
#     historico_ia/pl_AAAAMMDD_HHMM/
#         imagem1.png      as imagens do enunciado (se houver)
#         resposta.json    o enunciado, o PL devolvido e o retorno completo do Claude
# O Claude roda a partir de historico_ia/, então as sessões ficam no histórico do
# Claude Code dessa pasta. Para reabrir uma, entre em historico_ia/ e rode
# "claude --resume <session_id>" (o session_id está no resposta.json).
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_HISTORICO = PASTA_PROJETO / "historico_ia"

INSTRUCOES = """\
Você é um professor de Pesquisa Operacional. Leia o enunciado abaixo (texto e/ou
imagem anexada) e formule o modelo de Programação Linear.

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


# Procura o executável do Claude Code: primeiro na variável SIMPLEXLAB_CLAUDE
# e depois no PATH (no Windows o npm instala como claude.cmd, o which acha também).
def encontrar_claude():
    caminho = os.environ.get("SIMPLEXLAB_CLAUDE") or shutil.which("claude")
    if not caminho:
        raise ErroIA(
            "Não encontrei o Claude Code nesta máquina.\n\n"
            "Instale com: npm install -g @anthropic-ai/claude-code\n"
            "Depois entre na sua conta: rode 'claude' e use /login"
        )
    return caminho


# Envia o enunciado para o Claude e devolve o modelo de PL gerado.
# "processo_iniciado" recebe o Popen, para a interface poder cancelar.
def gerar_pl(texto="", imagens=(), processo_iniciado=None):
    texto = texto.strip()
    if not texto and not imagens:
        raise ErroIA("Cole o texto do enunciado ou uma imagem antes de gerar o PL.")

    claude = encontrar_claude()
    pasta = _criar_pasta_historico()

    # O Claude não recebe imagem por parâmetro: guardamos cada uma na pasta do
    # histórico e pedimos para ele abrir com a ferramenta Read.
    anexos = []
    for numero, imagem in enumerate(imagens, start=1):
        imagem = Path(imagem)
        destino = pasta / f"imagem{numero}{imagem.suffix.lower() or '.png'}"
        shutil.copyfile(imagem, destino)
        anexos.append(destino)

    comando = [
        claude, "-p",
        "--output-format", "json",
        "--json-schema", json.dumps(ESQUEMA_RESPOSTA),
        "--name", f"SimplexLab: {pasta.name}",
        "--strict-mcp-config",
        # Só a leitura de arquivos fica disponível (para abrir as imagens).
        "--tools=Read",
        "--allowedTools=Read",
        "--permission-mode", "dontAsk",
    ]

    prompt = INSTRUCOES + "\nEnunciado:\n" + (texto or "(veja a imagem anexada)")
    if anexos:
        prompt += "\n\nImagens do enunciado (abra cada uma com a ferramenta Read):\n"
        prompt += "\n".join(str(anexo) for anexo in anexos)

    registro = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "enunciado": texto,
        "imagens": [anexo.name for anexo in anexos],
    }
    try:
        saida = _executar(comando, prompt, PASTA_HISTORICO, processo_iniciado, registro)
        gerado = _interpretar_resposta(_extrair_resultado(saida))
    except ErroIA as erro:
        registro["erro"] = str(erro)
        _salvar_registro(pasta, registro)
        raise

    registro["titulo"] = gerado.titulo
    registro["modelo"] = gerado.texto
    if gerado.erro:
        registro["erro_formato"] = gerado.erro
    _salvar_registro(pasta, registro)
    return gerado


# Cria historico_ia/pl_AAAAMMDD_HHMM. Se já existir uma no mesmo minuto,
# acrescenta _2, _3, ...
def _criar_pasta_historico():
    PASTA_HISTORICO.mkdir(parents=True, exist_ok=True)
    nome = "pl_" + datetime.now().strftime("%Y%m%d_%H%M")
    pasta = PASTA_HISTORICO / nome
    numero = 2
    while pasta.exists():
        pasta = PASTA_HISTORICO / f"{nome}_{numero}"
        numero += 1
    pasta.mkdir()
    return pasta


# Grava o resposta.json da pasta do histórico. O session_id vem do retorno do
# Claude e serve para reabrir a conversa com "claude --resume".
def _salvar_registro(pasta, registro):
    retorno = registro.get("retorno_claude")
    if isinstance(retorno, dict) and retorno.get("session_id"):
        registro = {"session_id": retorno["session_id"], **registro}
    conteudo = json.dumps(registro, ensure_ascii=False, indent=2)
    (pasta / "resposta.json").write_text(conteudo + "\n", encoding="utf-8")


# Roda o Claude passando o prompt pela entrada padrão e devolve o stdout.
# O retorno bruto também vai para o registro do histórico.
def _executar(comando, prompt, pasta, processo_iniciado, registro):
    try:
        processo = subprocess.Popen(
            comando,
            cwd=pasta,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as erro:
        raise ErroIA(f"Não foi possível executar o Claude: {erro}") from erro

    if processo_iniciado is not None:
        processo_iniciado(processo)

    try:
        saida, erros = processo.communicate(prompt, timeout=TEMPO_LIMITE)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.communicate()
        raise ErroIA(f"O Claude passou de {TEMPO_LIMITE} segundos sem responder.")

    try:
        registro["retorno_claude"] = json.loads(saida)
    except json.JSONDecodeError:
        registro["retorno_claude"] = saida

    if processo.returncode != 0:
        # Com --output-format json o motivo do erro costuma vir no stdout.
        raise ErroIA(_mensagem_de_falha(erros + "\n" + _texto_do_erro(saida)))
    return saida


# Tira a mensagem de erro do JSON do Claude (campo "result"), se houver.
def _texto_do_erro(saida):
    try:
        return str(json.loads(saida).get("result", ""))
    except (json.JSONDecodeError, AttributeError):
        return saida


# O stdout do Claude é um JSON com o resultado da execução. A resposta no
# formato do esquema vem em "structured_output"; se não vier, tentamos "result".
def _extrair_resultado(saida):
    try:
        dados = json.loads(saida)
    except json.JSONDecodeError as erro:
        raise ErroIA(f"A resposta do Claude não veio no formato esperado:\n\n{saida}") from erro
    if not isinstance(dados, dict):
        raise ErroIA(f"A resposta do Claude não veio no formato esperado:\n\n{saida}")

    if dados.get("is_error"):
        raise ErroIA(_mensagem_de_falha(str(dados.get("result", ""))))

    estruturado = dados.get("structured_output")
    if isinstance(estruturado, dict):
        return json.dumps(estruturado)
    return _sem_cercas(str(dados.get("result", "")))


# Remove o bloco ```json ... ``` que às vezes envolve a resposta em texto.
def _sem_cercas(texto):
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1] if "\n" in texto else ""
        texto = texto.rsplit("```", 1)[0]
    return texto.strip()


# Monta uma mensagem curta a partir do que o Claude escreveu.
def _mensagem_de_falha(erros):
    linhas = [linha for linha in erros.strip().splitlines() if linha.strip()]
    detalhe = "\n".join(linhas[-5:]) or "sem detalhes"
    minusculo = detalhe.lower()
    if "login" in minusculo or "auth" in minusculo or "api key" in minusculo:
        return ("O Claude não está logado. Rode 'claude' no terminal e use /login.\n\n"
                f"{detalhe}")
    return f"O Claude retornou um erro:\n\n{detalhe}"


# Lê o JSON devolvido e confere se o modelo está no formato que o leitor aceita.
def _interpretar_resposta(conteudo):
    try:
        dados = json.loads(conteudo)
        titulo = str(dados["titulo"]).strip() or "Enunciado importado"
        modelo = str(dados["modelo"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as erro:
        raise ErroIA(f"A resposta do Claude não veio no formato esperado:\n\n{conteudo}") from erro

    gerado = ModeloGerado(titulo=titulo, texto=modelo)
    try:
        ler_modelo(modelo)
    except ErroLeitura as erro:
        gerado.erro = str(erro)
    return gerado
