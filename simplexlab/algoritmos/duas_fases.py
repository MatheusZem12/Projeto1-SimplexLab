"""
Método Simplex das Duas Fases.

Fase 1: minimiza W = soma das variáveis artificiais. Se o mínimo for
        maior que zero, o problema é inviável.
Fase 2: remove as artificiais e resolve o problema original partindo
        da base encontrada na Fase 1.

As iterações são as mesmas do Simplex comum, por isso a classe herda
de MetodoSimplex.
"""

from fractions import Fraction

from simplexlab.algoritmos.forma_padrao import montar_forma_padrao
from simplexlab.algoritmos.quadro_simplex import QuadroSimplex
from simplexlab.algoritmos.resultado import INVIAVEL, Etapa, Resultado
from simplexlab.algoritmos.simplex import MetodoSimplex
from simplexlab.util.formatacao import formatar_numero


class MetodoDuasFases(MetodoSimplex):
    nome = "Simplex - Duas Fases"

    # Resolve o problema passando pelas duas fases e devolve o Resultado.
    def resolver(self, problema):
        forma = montar_forma_padrao(problema)
        etapas = [Etapa("Forma padrão", forma.descricao)]

        quadro = self._executar_fase_1(forma, etapas)
        if quadro is None:
            return Resultado(
                metodo=self.nome,
                status=INVIAVEL,
                etapas=etapas,
                observacoes=["Ao final da Fase 1 ainda há variáveis artificiais com valor positivo."],
            )

        self._preparar_fase_2(quadro, forma, etapas)
        status = self.executar_iteracoes(quadro, etapas, "Fase 2 - ")
        return self.montar_resultado(problema, quadro, status, etapas)

    # Fase 1: monta a linha W, zera as artificiais que estão na base e roda
    # o Simplex. Retorna o quadro final, ou None se o problema for inviável.
    def _executar_fase_1(self, forma, etapas):
        # Minimizar W = a1 + a2 + ... equivale a maximizar -W. Na convenção
        # da linha Z (W + ... = 0) as artificiais entram com coeficiente 1.
        linha_w = [Fraction(0)] * (len(forma.colunas) + 1)
        for j in forma.artificiais:
            linha_w[j] = Fraction(1)

        quadro = QuadroSimplex(forma.colunas, forma.linhas, forma.base, linha_w, "W")
        nomes = " + ".join(forma.colunas[j] for j in forma.artificiais)
        etapas.append(quadro.registrar(
            "Fase 1 - Montagem da linha W",
            f"Objetivo da Fase 1: minimizar W = {nomes}.\n\n"
            "As variáveis artificiais estão na base, então seus coeficientes na "
            "linha W precisam ser zerados. Para isso subtraímos da linha W cada "
            "linha em que há uma artificial na base.",
        ))

        quadro.ajustar_linha_objetivo()
        self.executar_iteracoes(quadro, etapas, "Fase 1 - ")

        # O valor em b da linha W é -W, por causa da convenção de maximização.
        w = -quadro.valor_objetivo()
        if w != 0:
            etapas.append(Etapa(
                "Fim da Fase 1",
                f"O menor valor possível de W é {formatar_numero(w)}, maior que zero.\n"
                "Não foi possível zerar as variáveis artificiais, portanto o "
                "problema original não tem solução viável.",
            ))
            return None

        etapas.append(Etapa(
            "Fim da Fase 1",
            "W = 0: todas as artificiais foram zeradas e encontramos uma solução "
            "básica viável para o problema original. Podemos ir para a Fase 2.",
        ))
        return quadro

    # Fase 2: tira as artificiais do quadro, coloca a função objetivo original
    # na última linha e zera os coeficientes das variáveis básicas.
    def _preparar_fase_2(self, quadro, forma, etapas):
        self._retirar_artificiais_da_base(quadro, forma.artificiais)
        quadro.remover_colunas(forma.artificiais)

        custos = [c for j, c in enumerate(forma.custos) if j not in forma.artificiais]
        quadro.objetivo = [-c for c in custos] + [Fraction(0)]
        quadro.nome_objetivo = "Z"

        etapas.append(quadro.registrar(
            "Fase 2 - Montagem da linha Z",
            "As colunas das variáveis artificiais foram removidas e a função "
            "objetivo original foi colocada na linha Z.\n\n"
            "As variáveis básicas que tiverem coeficiente diferente de zero na "
            "linha Z são zeradas com operações entre linhas antes de continuar.",
        ))
        quadro.ajustar_linha_objetivo()

    # Pode acontecer de uma artificial terminar a Fase 1 na base com valor zero.
    # Nesse caso trocamos ela por qualquer variável não artificial da mesma
    # linha; se a linha inteira for zero, a restrição é redundante e sai.
    def _retirar_artificiais_da_base(self, quadro, artificiais):
        redundantes = []
        for i, j in enumerate(quadro.base):
            if j not in artificiais:
                continue
            for coluna in range(len(quadro.colunas)):
                if coluna not in artificiais and quadro.linhas[i][coluna] != 0:
                    quadro.pivotear(i, coluna)
                    break
            else:
                redundantes.append(i)

        for i in reversed(redundantes):
            quadro.remover_linha(i)
