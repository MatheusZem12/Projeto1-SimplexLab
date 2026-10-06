from dataclasses import dataclass
from fractions import Fraction

from simplexlab.util.formatacao import formatar_numero, montar_expressao

MAXIMIZAR = "max"
MINIMIZAR = "min"

MENOR_IGUAL = "<="
MAIOR_IGUAL = ">="
IGUAL = "="


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
