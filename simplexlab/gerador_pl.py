"""
Geração do modelo de PL a partir de um enunciado (texto e/ou imagem) usando IA.

Em vez de usar uma chave de API, chamamos o Codex CLI instalado na máquina
(comando "codex"), que usa a conta do ChatGPT em que o usuário já fez login.
Assim nenhuma chave fica no projeto e o consumo sai da assinatura do usuário.

Pré-requisitos (uma vez só):
    npm install -g @openai/codex
    codex login

Se o executável estiver em um lugar fora do PATH, informe o caminho na
variável de ambiente SIMPLEXLAB_CODEX.
"""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from simplexlab.modelo import ErroLeitura, ler_modelo

TEMPO_LIMITE = 300  # segundos

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


# Procura o executável do Codex: primeiro na variável SIMPLEXLAB_CODEX e
# depois no PATH (no Windows o npm instala como codex.cmd, o which acha também).
def encontrar_codex():
    caminho = os.environ.get("SIMPLEXLAB_CODEX") or shutil.which("codex")
    if not caminho:
        raise ErroIA(
            "Não encontrei o Codex CLI nesta máquina.\n\n"
            "Instale com: npm install -g @openai/codex\n"
            "Depois entre na sua conta com: codex login"
        )
    return caminho


# Envia o enunciado para o Codex e devolve o modelo de PL gerado.
# "processo_iniciado" recebe o Popen, para a interface poder cancelar.
def gerar_pl(texto="", imagens=(), processo_iniciado=None):
    texto = texto.strip()
    if not texto and not imagens:
        raise ErroIA("Cole o texto do enunciado ou uma imagem antes de gerar o PL.")

    codex = encontrar_codex()
    with tempfile.TemporaryDirectory(prefix="simplexlab_") as pasta:
        pasta = Path(pasta)
        esquema = pasta / "esquema.json"
        saida = pasta / "resposta.json"
        esquema.write_text(json.dumps(ESQUEMA_RESPOSTA), encoding="utf-8")

        comando = [
            codex, "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox", "read-only",
            "--color", "never",
            "-C", str(pasta),
            "--output-schema", str(esquema),
            "-o", str(saida),
        ]
        for imagem in imagens:
            comando += ["-i", str(imagem)]
        comando.append("-")

        prompt = INSTRUCOES + "\nEnunciado:\n" + (texto or "(veja a imagem anexada)")
        _executar(comando, prompt, processo_iniciado)

        if not saida.exists():
            raise ErroIA("O Codex terminou sem devolver resposta.")
        return _interpretar_resposta(saida.read_text(encoding="utf-8"))


# Roda o Codex passando o prompt pela entrada padrão.
def _executar(comando, prompt, processo_iniciado):
    try:
        processo = subprocess.Popen(
            comando,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as erro:
        raise ErroIA(f"Não foi possível executar o Codex: {erro}") from erro

    if processo_iniciado is not None:
        processo_iniciado(processo)

    try:
        _, erros = processo.communicate(prompt, timeout=TEMPO_LIMITE)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.communicate()
        raise ErroIA(f"O Codex passou de {TEMPO_LIMITE} segundos sem responder.")

    if processo.returncode != 0:
        raise ErroIA(_mensagem_de_falha(erros))


# Monta uma mensagem curta a partir do que o Codex escreveu no stderr.
def _mensagem_de_falha(erros):
    linhas = [linha for linha in erros.strip().splitlines() if linha.strip()]
    detalhe = "\n".join(linhas[-5:]) or "sem detalhes"
    if "login" in detalhe.lower() or "auth" in detalhe.lower():
        return f"O Codex não está logado. Rode 'codex login' no terminal.\n\n{detalhe}"
    return f"O Codex retornou um erro:\n\n{detalhe}"


# Lê o JSON devolvido e confere se o modelo está no formato que o leitor aceita.
def _interpretar_resposta(conteudo):
    try:
        dados = json.loads(conteudo)
        titulo = str(dados["titulo"]).strip() or "Enunciado importado"
        modelo = str(dados["modelo"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as erro:
        raise ErroIA(f"A resposta do Codex não veio no formato esperado:\n\n{conteudo}") from erro

    gerado = ModeloGerado(titulo=titulo, texto=modelo)
    try:
        ler_modelo(modelo)
    except ErroLeitura as erro:
        gerado.erro = str(erro)
    return gerado
