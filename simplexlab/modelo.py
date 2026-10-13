"""
Modelo de Programação Linear: as classes do problema, a leitura do texto
digitado pelo usuário, a formatação de números e os exemplos prontos.

Formato aceito na entrada, uma informação por linha:

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
from dataclasses import dataclass
from fractions import Fraction

MAXIMIZAR = "max"
MINIMIZAR = "min"

MENOR_IGUAL = "<="
MAIOR_IGUAL = ">="
IGUAL = "="


# ---------------------------------------------------------------------------
# Formatação de números e expressões
# ---------------------------------------------------------------------------

# Converte um número para texto. Inteiros aparecem sem casas decimais e os
# demais aparecem como fração (ex.: 3/2), que é como montamos os quadros em aula.
def formatar_numero(valor):
    valor = Fraction(valor)
    if valor.denominator == 1:
        return str(valor.numerator)
    if valor.denominator <= 1000:
        return f"{valor.numerator}/{valor.denominator}"
    return formatar_decimal(valor)


# Mostra o número em decimal com no máximo 4 casas, usando vírgula.
def formatar_decimal(valor):
    texto = f"{float(valor):.4f}".rstrip("0").rstrip(".")
    if texto == "-0":
        texto = "0"
    return texto.replace(".", ",")


# Usado nos resultados finais: mostra a fração e, se não for inteiro,
# também o valor aproximado em decimal. Ex.: "9/2 (4,5)".
def formatar_resultado(valor):
    valor = Fraction(valor)
    if valor.denominator == 1:
        return str(valor.numerator)
    return f"{formatar_numero(valor)} ({formatar_decimal(valor)})"


# Formata um ponto como "(2, 6)".
def formatar_ponto(ponto):
    return f"({formatar_numero(ponto[0])}, {formatar_numero(ponto[1])})"


# Monta uma expressão linear legível a partir dos coeficientes.
# Ex.: [3, -1, 0] com ["x1", "x2", "x3"] vira "3x1 - x2".
def montar_expressao(coeficientes, nomes):
    partes = []
    for coeficiente, nome in zip(coeficientes, nomes):
        if coeficiente == 0:
            continue
        sinal = "-" if coeficiente < 0 else "+"
        modulo = abs(coeficiente)
        termo = nome if modulo == 1 else f"{formatar_numero(modulo)}{nome}"
        if not partes:
            partes.append(f"-{termo}" if sinal == "-" else termo)
        else:
            partes.append(f"{sinal} {termo}")
    return " ".join(partes) if partes else "0"


# ---------------------------------------------------------------------------
# Classes do problema
# ---------------------------------------------------------------------------

@dataclass
class Restricao:
    coeficientes: list
    sinal: str
    lado_direito: Fraction

    # Calcula o valor do lado esquerdo da restrição em um ponto.
    def valor_em(self, ponto):
        return sum(a * x for a, x in zip(self.coeficientes, ponto))

    # Verifica se o ponto informado respeita a restrição.
    def atendida_por(self, ponto):
        esquerdo = self.valor_em(ponto)
        if self.sinal == MENOR_IGUAL:
            return esquerdo <= self.lado_direito
        if self.sinal == MAIOR_IGUAL:
            return esquerdo >= self.lado_direito
        return esquerdo == self.lado_direito

    # Texto da restrição usando os nomes das variáveis do problema.
    def como_texto(self, nomes):
        expressao = montar_expressao(self.coeficientes, nomes)
        return f"{expressao} {self.sinal} {formatar_numero(self.lado_direito)}"


@dataclass
class ProblemaPL:
    tipo: str
    objetivo: list
    restricoes: list
    variaveis: list

    @property
    def num_variaveis(self):
        return len(self.variaveis)

    @property
    def eh_maximizacao(self):
        return self.tipo == MAXIMIZAR

    # Calcula o valor da função objetivo em um ponto.
    def calcular_objetivo(self, ponto):
        return sum(c * x for c, x in zip(self.objetivo, ponto))

    # Devolve o modelo escrito no formato que usamos em aula.
    def como_texto(self):
        tipo = "Max" if self.eh_maximizacao else "Min"
        linhas = [f"{tipo} Z = {montar_expressao(self.objetivo, self.variaveis)}", "s.a."]
        for restricao in self.restricoes:
            linhas.append(f"    {restricao.como_texto(self.variaveis)}")
        linhas.append(f"    {', '.join(self.variaveis)} >= 0")
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Leitura do modelo digitado (entrada por expressão)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Exemplos prontos
# ---------------------------------------------------------------------------

# Problemas prontos para testar o sistema e usar na apresentação.
# Cada exemplo cobre uma situação diferente que o professor pode pedir.
EXEMPLOS = {
    "Maximização clássica (2 variáveis)": """max z = 3x1 + 5x2
s.a.
x1 <= 4
2x2 <= 12
3x1 + 2x2 <= 18
x1, x2 >= 0""",

    "Minimização com restrições >=": """min z = 2x1 + 3x2
s.a.
x1 + x2 >= 4
x1 + 3x2 >= 6
x1, x2 >= 0""",

    "Restrição de igualdade": """max z = 2x1 + 3x2
s.a.
x1 + x2 = 5
x1 <= 4
x2 <= 3
x1, x2 >= 0""",

    "Maximização com 3 variáveis": """max z = 5x1 + 4x2 + 3x3
s.a.
2x1 + 3x2 + x3 <= 5
4x1 + x2 + 2x3 <= 11
3x1 + 4x2 + 2x3 <= 8
x1, x2, x3 >= 0""",

    "Soluções ótimas múltiplas": """max z = 2x1 + 4x2
s.a.
x1 + 2x2 <= 8
x1 <= 6
x2 <= 3
x1, x2 >= 0""",

    "Problema ilimitado": """max z = x1 + 2x2
s.a.
x1 - x2 <= 2
x1 <= 4
x1, x2 >= 0""",

    "Problema inviável": """max z = x1 + x2
s.a.
x1 + x2 <= 2
x1 + x2 >= 5
x1, x2 >= 0""",
}
