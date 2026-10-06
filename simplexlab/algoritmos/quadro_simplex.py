"""
Quadro (tableau) do Simplex e as operações feitas sobre ele.

Convenção usada (a mesma da aula):
    - a última linha é a linha Z, escrita como Z - c1x1 - c2x2 - ... = 0;
    - o problema é sempre tratado como maximização;
    - entra na base a variável com o coeficiente mais negativo na linha Z;
    - sai da base a variável com a menor razão b / coluna (só valores positivos).
"""

from fractions import Fraction

from simplexlab.algoritmos.resultado import Etapa


class QuadroSimplex:

    # Recebe as colunas (nomes), as linhas [A | b], a base (índice da coluna
    # básica de cada linha) e a linha da função objetivo.
    def __init__(self, colunas, linhas, base, linha_objetivo, nome_objetivo="Z"):
        self.colunas = list(colunas)
        self.linhas = [list(linha) for linha in linhas]
        self.base = list(base)
        self.objetivo = list(linha_objetivo)
        self.nome_objetivo = nome_objetivo

    # Variável que entra: coluna com o coeficiente mais negativo na linha Z.
    # Retorna None quando não há negativos, ou seja, o quadro já é ótimo.
    def coluna_que_entra(self):
        escolhida = None
        menor = Fraction(0)
        for j, valor in enumerate(self.objetivo[:-1]):
            if valor < menor:
                menor = valor
                escolhida = j
        return escolhida

    # Calcula a razão b / a de cada linha para a coluna informada.
    # Linhas com valor <= 0 na coluna não participam (razão None).
    def razoes(self, coluna):
        resultado = []
        for linha in self.linhas:
            if linha[coluna] > 0:
                resultado.append(linha[-1] / linha[coluna])
            else:
                resultado.append(None)
        return resultado

    # Variável que sai: linha com a menor razão. Retorna None quando nenhuma
    # linha tem valor positivo na coluna (problema ilimitado).
    def linha_que_sai(self, coluna):
        escolhida = None
        menor = None
        for i, razao in enumerate(self.razoes(coluna)):
            if razao is not None and (menor is None or razao < menor):
                menor = razao
                escolhida = i
        return escolhida

    # Pivoteamento: divide a linha pivô pelo elemento pivô e zera o restante
    # da coluna pivô (inclusive na linha Z) com operações entre linhas.
    def pivotear(self, linha_pivo, coluna_pivo):
        pivo = self.linhas[linha_pivo][coluna_pivo]
        nova_linha_pivo = [valor / pivo for valor in self.linhas[linha_pivo]]
        self.linhas[linha_pivo] = nova_linha_pivo

        for i, linha in enumerate(self.linhas):
            if i != linha_pivo and linha[coluna_pivo] != 0:
                self.linhas[i] = self._subtrair_multiplo(linha, nova_linha_pivo, coluna_pivo)

        if self.objetivo[coluna_pivo] != 0:
            self.objetivo = self._subtrair_multiplo(self.objetivo, nova_linha_pivo, coluna_pivo)

        self.base[linha_pivo] = coluna_pivo

    # Faz linha - k * linha_pivo, onde k é o valor da linha na coluna pivô.
    @staticmethod
    def _subtrair_multiplo(linha, linha_pivo, coluna_pivo):
        fator = linha[coluna_pivo]
        return [a - fator * b for a, b in zip(linha, linha_pivo)]

    # Zera, na linha da função objetivo, os coeficientes das variáveis básicas.
    # É necessário quando a linha Z é montada com variáveis que já estão na base.
    def ajustar_linha_objetivo(self):
        for i, j in enumerate(self.base):
            fator = self.objetivo[j]
            if fator != 0:
                self.objetivo = [a - fator * b for a, b in zip(self.objetivo, self.linhas[i])]

    # Remove colunas do quadro (usado para tirar as artificiais na Fase 2).
    def remover_colunas(self, indices):
        manter = [j for j in range(len(self.colunas)) if j not in indices]
        novo_indice = {antigo: novo for novo, antigo in enumerate(manter)}

        self.colunas = [self.colunas[j] for j in manter]
        self.linhas = [[linha[j] for j in manter] + [linha[-1]] for linha in self.linhas]
        self.objetivo = [self.objetivo[j] for j in manter] + [self.objetivo[-1]]
        self.base = [novo_indice[j] for j in self.base]

    # Remove uma linha do quadro (restrição redundante).
    def remover_linha(self, indice):
        del self.linhas[indice]
        del self.base[indice]

    # Valor de cada variável na solução básica atual (não básicas valem zero).
    def valores_variaveis(self):
        valores = [Fraction(0)] * len(self.colunas)
        for i, j in enumerate(self.base):
            valores[j] = self.linhas[i][-1]
        return valores

    # Valor atual da função objetivo (coluna b da linha Z).
    def valor_objetivo(self):
        return self.objetivo[-1]

    # Variáveis não básicas com coeficiente zero na linha Z. No quadro ótimo
    # isso indica que existem soluções ótimas alternativas.
    def nao_basicas_com_custo_zero(self):
        return [j for j in range(len(self.colunas))
                if j not in self.base and self.objetivo[j] == 0]

    # Guarda uma cópia do quadro atual como uma etapa da resolução.
    def registrar(self, titulo, descricao, linha_pivo=None, coluna_pivo=None):
        return Etapa(
            titulo=titulo,
            descricao=descricao,
            colunas=self.colunas + ["b"],
            rotulos_linhas=[self.colunas[j] for j in self.base] + [self.nome_objetivo],
            linhas=[list(linha) for linha in self.linhas] + [list(self.objetivo)],
            ultima_linha_objetivo=True,
            linha_destaque=linha_pivo,
            coluna_destaque=coluna_pivo,
        )
