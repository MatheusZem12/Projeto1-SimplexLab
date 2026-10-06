"""
Leitura do modelo de PL digitado pelo usuário (entrada por expressão).

Formato aceito, uma informação por linha:

    max z = 3x1 + 5x2
    s.a.
    x1 <= 4
    2x2 <= 12
    3x1 + 2x2 <= 18
    x1, x2 >= 0

A linha "s.a." e a de não negatividade são opcionais, pois o sistema
sempre considera todas as variáveis >= 0.
"""

import re
from fractions import Fraction

from simplexlab.modelo.problema import (
    IGUAL,
    MAIOR_IGUAL,
    MAXIMIZAR,
    MENOR_IGUAL,
    MINIMIZAR,
    ProblemaPL,
    Restricao,
)

PADRAO_OBJETIVO = re.compile(r"^(max|min)[a-z]*\s*:?\s*(?:[a-z]\w*\s*=)?\s*(.*)$")
PADRAO_SUJEITO_A = re.compile(r"^(s\.\s*a\.?|sujeito\s+a|subject\s+to|s\.\s*t\.?)\s*:?\s*")
PADRAO_SINAL = re.compile(r"(<=|>=|=<|=>|≤|≥|==|=|<|>)")
PADRAO_TERMO = re.compile(r"([+-])?(\d+(?:\.\d+)?(?:/\d+)?)?\*?([a-z_]\w*)?")
PADRAO_LISTA_VARIAVEIS = re.compile(r"^[a-z_]\w*(\s*,\s*[a-z_]\w*)*$")
PADRAO_TERMOS_COLADOS = re.compile(r"\w\s+\d|[a-z_]\w*\s+[a-z_]")

SINAIS = {
    "<=": MENOR_IGUAL, "=<": MENOR_IGUAL, "≤": MENOR_IGUAL, "<": MENOR_IGUAL,
    ">=": MAIOR_IGUAL, "=>": MAIOR_IGUAL, "≥": MAIOR_IGUAL, ">": MAIOR_IGUAL,
    "=": IGUAL, "==": IGUAL,
}


class ErroLeitura(Exception):
    pass


# Ponto de entrada da leitura: recebe o texto completo e devolve o ProblemaPL.
def ler_modelo(texto):
    linhas = _linhas_uteis(texto)
    if not linhas:
        raise ErroLeitura("Digite o modelo antes de resolver.")

    numero, primeira = linhas[0]
    tipo, objetivo = _ler_objetivo(primeira, numero)

    restricoes_lidas = []
    for numero, linha in linhas[1:]:
        restricao = _ler_restricao(linha, numero)
        if restricao is not None:
            restricoes_lidas.append(restricao)

    if not restricoes_lidas:
        raise ErroLeitura("Informe pelo menos uma restrição.")

    variaveis = _ordenar_variaveis(objetivo, restricoes_lidas)
    restricoes = [
        Restricao(
            coeficientes=[coeficientes.get(nome, Fraction(0)) for nome in variaveis],
            sinal=sinal,
            lado_direito=lado_direito,
        )
        for coeficientes, sinal, lado_direito in restricoes_lidas
    ]

    return ProblemaPL(
        tipo=tipo,
        objetivo=[objetivo.get(nome, Fraction(0)) for nome in variaveis],
        restricoes=restricoes,
        variaveis=variaveis,
    )


# Separa o texto em linhas, tirando comentários (#), linhas vazias e o "s.a.".
# Guarda o número original da linha para mostrar nas mensagens de erro.
def _linhas_uteis(texto):
    resultado = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        linha = linha.split("#")[0].strip().lower()
        linha = PADRAO_SUJEITO_A.sub("", linha).strip()
        if linha:
            resultado.append((numero, linha))
    return resultado


# Lê a linha da função objetivo (ex.: "max z = 3x1 + 5x2").
def _ler_objetivo(linha, numero):
    encontrado = PADRAO_OBJETIVO.match(linha)
    if encontrado is None:
        raise ErroLeitura(
            f"Linha {numero}: a primeira linha deve ser a função objetivo, "
            "começando com 'max' ou 'min'. Ex.: max z = 3x1 + 5x2"
        )

    tipo = MAXIMIZAR if encontrado.group(1) == "max" else MINIMIZAR
    coeficientes, constante = _ler_expressao(encontrado.group(2), numero)

    if constante != 0:
        raise ErroLeitura(f"Linha {numero}: a função objetivo não deve ter termo constante.")
    if not coeficientes:
        raise ErroLeitura(f"Linha {numero}: a função objetivo não tem variáveis.")
    return tipo, coeficientes


# Lê uma restrição. Retorna None quando a linha é só a não negatividade
# (ex.: "x1, x2 >= 0"), já que ela é considerada automaticamente.
def _ler_restricao(linha, numero):
    partes = PADRAO_SINAL.split(linha)
    if len(partes) != 3:
        raise ErroLeitura(
            f"Linha {numero}: a restrição deve ter exatamente um sinal (<=, >= ou =)."
        )

    esquerda, sinal_texto, direita = (parte.strip() for parte in partes)
    sinal = SINAIS[sinal_texto]

    if _eh_nao_negatividade(esquerda, sinal, direita):
        return None

    coef_esquerda, const_esquerda = _ler_expressao(esquerda, numero)
    coef_direita, const_direita = _ler_expressao(direita, numero)

    # Passa as variáveis para a esquerda e as constantes para a direita.
    coeficientes = dict(coef_esquerda)
    for nome, valor in coef_direita.items():
        coeficientes[nome] = coeficientes.get(nome, Fraction(0)) - valor
    lado_direito = const_direita - const_esquerda

    if all(valor == 0 for valor in coeficientes.values()):
        raise ErroLeitura(f"Linha {numero}: a restrição não tem variáveis.")
    return coeficientes, sinal, lado_direito


# Confere se a linha é do tipo "x1, x2 >= 0".
def _eh_nao_negatividade(esquerda, sinal, direita):
    return (
        sinal == MAIOR_IGUAL
        and direita == "0"
        and PADRAO_LISTA_VARIAVEIS.match(esquerda) is not None
    )


# Lê uma expressão linear (ex.: "3x1 - 2x2 + 4") e devolve um dicionário
# variável -> coeficiente e a soma das constantes que aparecerem.
def _ler_expressao(texto, numero):
    if PADRAO_TERMOS_COLADOS.search(texto):
        raise ErroLeitura(
            f"Linha {numero}: falta um sinal (+ ou -) entre os termos de '{texto.strip()}'."
        )

    expressao = texto.replace(" ", "").replace(",", ".")
    if not expressao:
        raise ErroLeitura(f"Linha {numero}: expressão vazia.")

    coeficientes = {}
    constante = Fraction(0)
    posicao = 0

    while posicao < len(expressao):
        termo = PADRAO_TERMO.match(expressao, posicao)
        sinal, valor_texto, variavel = termo.groups()

        if termo.end() == posicao or (valor_texto is None and variavel is None):
            raise ErroLeitura(
                f"Linha {numero}: não foi possível entender o trecho '{expressao[posicao:]}'."
            )
        if posicao > 0 and sinal is None:
            raise ErroLeitura(
                f"Linha {numero}: falta um sinal (+ ou -) antes de '{termo.group(0)}'."
            )

        valor = Fraction(valor_texto) if valor_texto else Fraction(1)
        if sinal == "-":
            valor = -valor

        if variavel:
            coeficientes[variavel] = coeficientes.get(variavel, Fraction(0)) + valor
        else:
            constante += valor
        posicao = termo.end()

    return coeficientes, constante


# Junta todas as variáveis usadas no modelo e ordena de forma natural
# (x1, x2, ..., x10), para que a ordem não dependa de como o usuário digitou.
def _ordenar_variaveis(objetivo, restricoes):
    nomes = set(objetivo)
    for coeficientes, _, _ in restricoes:
        nomes.update(coeficientes)

    def chave_natural(nome):
        return [int(parte) if parte.isdigit() else parte for parte in re.findall(r"\d+|\D+", nome)]

    return sorted(nomes, key=chave_natural)
