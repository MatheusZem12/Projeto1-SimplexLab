"""
Método Simplex (tabular): o quadro, o pivoteamento e as iterações.

O Simplex comum serve quando a base inicial é formada só por variáveis de
folga, ou seja, todas as restrições são do tipo <= com lado direito não
negativo. Com restrições >= ou = é usado o método das Duas Fases
(algoritmo_duas_fases.py), que reaproveita as iterações deste arquivo.

Convenção usada (a mesma da aula):
    - a última linha é a linha Z, escrita como Z - c1x1 - c2x2 - ... = 0;
    - o problema é sempre tratado como maximização;
    - entra na base a variável com o coeficiente mais negativo na linha Z;
    - sai da base a variável com a menor razão b / coluna (só valores positivos).

Se o Simplex voltar a uma base que já visitou (ciclagem, só acontece em
problemas degenerados), passa a usar a regra de Bland: entra a primeira
variável com coeficiente negativo e, no empate da razão, sai a de menor
índice. Essa regra sempre termina.
"""

from fractions import Fraction

from simplexlab.algoritmos.algoritmo_pl import ILIMITADO, OTIMO, Etapa, Resultado, montar_forma_padrao
from simplexlab.modelo import formatar_numero, formatar_resultado

LIMITE_ITERACOES = 100


class QuadroSimplex:

    # Recebe as colunas (nomes), as linhas [A | b], a base (índice da coluna
    # básica de cada linha) e a linha da função objetivo.
    def __init__(self, colunas, linhas, base, linha_objetivo, nome_objetivo="Z"):
        self.colunas = list(colunas)
        self.linhas = [list(linha) for linha in linhas]
        self.base = list(base)
        self.objetivo = list(linha_objetivo)
        self.nome_objetivo = nome_objetivo

    # Variável que entra: coluna com o coeficiente mais negativo na linha Z
    # (ou a primeira negativa, na regra de Bland).
    # Retorna None quando não há negativos, ou seja, o quadro já é ótimo.
    def coluna_que_entra(self, bland=False):
        escolhida = None
        menor = Fraction(0)
        for j, valor in enumerate(self.objetivo[:-1]):
            if valor < menor:
                if bland:
                    return j
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

    # Variável que sai: linha com a menor razão. No empate fica a primeira
    # linha, ou, na regra de Bland, a variável básica de menor índice.
    # Retorna None quando nenhuma linha tem valor positivo na coluna
    # (problema ilimitado).
    def linha_que_sai(self, coluna, bland=False):
        escolhida = None
        menor = None
        for i, razao in enumerate(self.razoes(coluna)):
            if razao is None:
                continue
            empate_bland = (bland and razao == menor
                            and self.base[i] < self.base[escolhida])
            if menor is None or razao < menor or empate_bland:
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


class MetodoSimplex:
    nome = "Simplex"

    # Resolve o problema e devolve o Resultado com todas as etapas.
    def resolver(self, problema):
        forma = montar_forma_padrao(problema)
        if forma.artificiais:
            raise ValueError(
                "O problema tem restrições >= ou =. Use o método das Duas Fases."
            )

        etapas = [Etapa("Forma padrão", forma.descricao)]
        linha_z = [-c for c in forma.custos] + [Fraction(0)]
        quadro = QuadroSimplex(forma.colunas, forma.linhas, forma.base, linha_z)

        status = self.executar_iteracoes(quadro, etapas)
        return self.montar_resultado(problema, quadro, status, etapas)

    # Laço principal do Simplex. A cada passo registra o quadro atual com o
    # pivô destacado e a explicação da escolha, e depois faz o pivoteamento.
    # Retorna OTIMO ou ILIMITADO.
    def executar_iteracoes(self, quadro, etapas, prefixo=""):
        titulo = f"{prefixo}Quadro inicial"
        bases_visitadas = set()
        bland = False

        for iteracao in range(1, LIMITE_ITERACOES + 1):
            base_atual = frozenset(quadro.base)
            aviso_ciclo = not bland and base_atual in bases_visitadas
            bland = bland or aviso_ciclo
            bases_visitadas.add(base_atual)

            coluna = quadro.coluna_que_entra(bland)
            if coluna is None:
                etapas.append(quadro.registrar(titulo, self._explicar_otimo(quadro)))
                return OTIMO

            linha = quadro.linha_que_sai(coluna, bland)
            if linha is None:
                etapas.append(quadro.registrar(
                    titulo, self._explicar_ilimitado(quadro, coluna), coluna_pivo=coluna
                ))
                return ILIMITADO

            descricao = self._explicar_pivo(quadro, linha, coluna, bland)
            if aviso_ciclo:
                descricao = (
                    "Este quadro tem a mesma base de um quadro anterior: o Simplex "
                    "entrou em ciclo (problema degenerado). A partir daqui usamos a "
                    "regra de Bland, que garante que o método termina.\n\n" + descricao
                )
            etapas.append(quadro.registrar(titulo, descricao, linha, coluna))
            quadro.pivotear(linha, coluna)
            titulo = f"{prefixo}Iteração {iteracao}"

        raise RuntimeError(
            f"O Simplex passou de {LIMITE_ITERACOES} iterações sem terminar."
        )

    # Lê o quadro final e monta o objeto Resultado.
    def montar_resultado(self, problema, quadro, status, etapas):
        resultado = Resultado(metodo=self.nome, status=status, etapas=etapas)
        if status != OTIMO:
            if status == ILIMITADO:
                resultado.observacoes.append(
                    "A função objetivo pode crescer indefinidamente dentro da região viável."
                )
            return resultado

        valores = quadro.valores_variaveis()
        n = problema.num_variaveis

        resultado.solucao = dict(zip(problema.variaveis, valores[:n]))
        resultado.variaveis_auxiliares = dict(zip(quadro.colunas[n:], valores[n:]))

        # A linha Z guarda o valor de Max Z. Para minimização resolvemos
        # Max (-Z), então o sinal precisa ser trocado de volta.
        valor = quadro.valor_objetivo()
        resultado.valor_otimo = valor if problema.eh_maximizacao else -valor

        alternativas = quadro.nao_basicas_com_custo_zero()
        if alternativas:
            nomes = ", ".join(quadro.colunas[j] for j in alternativas)
            resultado.observacoes.append(
                f"A variável não básica {nomes} tem coeficiente zero na linha Z do "
                "quadro ótimo: o problema possui soluções ótimas alternativas."
            )

        etapas.append(Etapa("Solução", self._explicar_solucao(problema, resultado)))
        return resultado

    # Texto da etapa em que há pivoteamento: quem entra, teste da razão e quem sai.
    def _explicar_pivo(self, quadro, linha, coluna, bland=False):
        entra = quadro.colunas[coluna]
        sai = quadro.colunas[quadro.base[linha]]
        criterio = "primeiro coeficiente negativo" if bland else "coeficiente mais negativo"
        texto = [
            f"Variável que entra: {entra} "
            f"({criterio} na linha {quadro.nome_objetivo}: "
            f"{formatar_numero(quadro.objetivo[coluna])})",
            "",
            f"Teste da razão (b / coluna {entra}):",
        ]

        for i, razao in enumerate(quadro.razoes(coluna)):
            nome = quadro.colunas[quadro.base[i]]
            b = formatar_numero(quadro.linhas[i][-1])
            a = formatar_numero(quadro.linhas[i][coluna])
            if razao is None:
                texto.append(f"    {nome}: {b} / {a}  ->  não entra no teste")
            else:
                marcador = "   <- menor" if i == linha else ""
                texto.append(f"    {nome}: {b} / {a} = {formatar_numero(razao)}{marcador}")

        texto += [
            "",
            f"Variável que sai: {sai}",
            f"Elemento pivô: {formatar_numero(quadro.linhas[linha][coluna])}",
        ]
        return "\n".join(texto)

    # Texto quando a coluna que entra não tem nenhum valor positivo.
    def _explicar_ilimitado(self, quadro, coluna):
        entra = quadro.colunas[coluna]
        return (
            f"Variável que entra: {entra}.\n\n"
            f"Nenhum valor da coluna {entra} é positivo, então não existe razão válida "
            f"e nenhuma variável limita o crescimento de {entra}.\n"
            "Conclusão: o problema é ilimitado."
        )

    # Texto do quadro ótimo.
    def _explicar_otimo(self, quadro):
        return (
            f"Não há coeficientes negativos na linha {quadro.nome_objetivo}, "
            "portanto este quadro é ótimo."
        )

    # Texto final com os valores encontrados.
    def _explicar_solucao(self, problema, resultado):
        linhas = ["Valores das variáveis de decisão:"]
        for nome, valor in resultado.solucao.items():
            linhas.append(f"    {nome} = {formatar_resultado(valor)}")

        if resultado.variaveis_auxiliares:
            linhas += ["", "Variáveis de folga/excesso:"]
            for nome, valor in resultado.variaveis_auxiliares.items():
                linhas.append(f"    {nome} = {formatar_resultado(valor)}")

        tipo = "Máximo" if problema.eh_maximizacao else "Mínimo"
        linhas += ["", f"Valor {tipo.lower()} de Z = {formatar_resultado(resultado.valor_otimo)}"]
        return "\n".join(linhas)
