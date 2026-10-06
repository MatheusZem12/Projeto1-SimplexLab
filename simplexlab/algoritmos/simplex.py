"""
Método Simplex (tabular) para problemas em que a base inicial é formada
só por variáveis de folga, ou seja, todas as restrições são do tipo <=
com lado direito não negativo.

Quando o problema tem restrições >= ou =, é preciso usar o método das
Duas Fases (duas_fases.py), que reaproveita as iterações desta classe.
"""

from fractions import Fraction

from simplexlab.algoritmos.forma_padrao import montar_forma_padrao
from simplexlab.algoritmos.quadro_simplex import QuadroSimplex
from simplexlab.algoritmos.resultado import ILIMITADO, OTIMO, Etapa, Resultado
from simplexlab.util.formatacao import formatar_numero, formatar_resultado

LIMITE_ITERACOES = 100


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

        for iteracao in range(1, LIMITE_ITERACOES + 1):
            coluna = quadro.coluna_que_entra()
            if coluna is None:
                etapas.append(quadro.registrar(titulo, self._explicar_otimo(quadro)))
                return OTIMO

            linha = quadro.linha_que_sai(coluna)
            if linha is None:
                etapas.append(quadro.registrar(
                    titulo, self._explicar_ilimitado(quadro, coluna), coluna_pivo=coluna
                ))
                return ILIMITADO

            etapas.append(quadro.registrar(
                titulo, self._explicar_pivo(quadro, linha, coluna), linha, coluna
            ))
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
    def _explicar_pivo(self, quadro, linha, coluna):
        entra = quadro.colunas[coluna]
        sai = quadro.colunas[quadro.base[linha]]
        texto = [
            f"Variável que entra: {entra} "
            f"(coeficiente mais negativo na linha {quadro.nome_objetivo}: "
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
