"""
Método Gráfico (somente 2 variáveis).

Passos:
    1. cada restrição vira uma reta a1*x1 + a2*x2 = b, e a tabela das retas
       mostra onde cada uma corta os eixos (x1 = 0 e x2 = 0);
    2. com essas retas o gráfico é montado e a região viável é delimitada;
    3. os vértices da região viável são as interseções entre essas retas
       (incluindo os eixos) que atendem todas as restrições;
    4. a função objetivo é avaliada em cada vértice e o melhor valor é o ótimo.

Antes do passo 4 verificamos se a região é ilimitada na direção em que a
função objetivo melhora, pois nesse caso não existe ótimo finito.
"""

import math
from fractions import Fraction
from itertools import combinations

from simplexlab.algoritmos.algoritmo_pl import ILIMITADO, INVIAVEL, OTIMO, Etapa, ResultadoGrafico
from simplexlab.modelo import (
    IGUAL,
    MAIOR_IGUAL,
    MENOR_IGUAL,
    Restricao,
    formatar_numero,
    formatar_ponto,
    formatar_resultado,
)


class MetodoGrafico:
    nome = "Gráfico"

    # Resolve o problema pelo método gráfico (somente 2 variáveis).
    def resolver(self, problema):
        if problema.num_variaveis != 2:
            raise ValueError(
                f"O método gráfico só funciona com 2 variáveis "
                f"(o modelo tem {problema.num_variaveis}). Use o Simplex."
            )

        restricoes = problema.restricoes + restricoes_nao_negatividade()
        resultado = ResultadoGrafico(metodo=self.nome, status=OTIMO)
        resultado.etapas.append(self._etapa_retas(problema))
        resultado.etapas.append(self._etapa_montagem(problema))

        resultado.vertices = calcular_vertices(restricoes)
        if not resultado.vertices:
            resultado.status = INVIAVEL
            resultado.etapas.append(Etapa(
                "Região viável",
                "Nenhum ponto atende todas as restrições ao mesmo tempo.\n"
                "A região viável é vazia, portanto o problema é inviável.",
            ))
            return resultado

        direcoes = direcoes_ilimitadas(restricoes)
        resultado.regiao_ilimitada = bool(direcoes)
        resultado.etapas.append(self._etapa_vertices(problema, resultado))

        if self._objetivo_cresce_sem_limite(problema, direcoes):
            resultado.status = ILIMITADO
            resultado.observacoes.append(
                "A região viável é ilimitada no sentido em que a função objetivo melhora."
            )
            resultado.etapas.append(Etapa(
                "Conclusão",
                "A região viável não é fechada e a função objetivo melhora sempre que "
                "andamos em uma das direções em que a região se estende.\n"
                "Portanto o problema é ilimitado (não há solução ótima finita).",
            ))
            return resultado

        self._escolher_otimo(problema, resultado)
        return resultado

    # Avalia Z nos vértices e guarda o(s) melhor(es).
    def _escolher_otimo(self, problema, resultado):
        valores = [problema.calcular_objetivo(v) for v in resultado.vertices]
        melhor = max(valores) if problema.eh_maximizacao else min(valores)

        resultado.valor_otimo = melhor
        # Em soluções múltiplas os vértices ótimos ficam em ordem de x1.
        resultado.pontos_otimos = sorted(v for v, z in zip(resultado.vertices, valores) if z == melhor)
        resultado.solucao = dict(zip(problema.variaveis, resultado.pontos_otimos[0]))

        if len(resultado.pontos_otimos) > 1:
            vertices = " e ".join(formatar_ponto(p) for p in resultado.pontos_otimos)
            resultado.observacoes.append(
                f"Os vértices {vertices} têm o mesmo valor ótimo Z = "
                f"{formatar_numero(melhor)}: todos os pontos do segmento entre eles "
                "também são soluções ótimas (soluções múltiplas)."
            )

        x1, x2 = problema.variaveis
        tipo = "maior" if problema.eh_maximizacao else "menor"
        pontos = ", ".join(formatar_ponto(p) for p in resultado.pontos_otimos)
        resultado.etapas.append(Etapa(
            "Conclusão",
            f"O {tipo} valor de Z entre os vértices é {formatar_resultado(melhor)}, "
            f"obtido em {pontos}.\n\n"
            f"Solução ótima: {x1} = {formatar_resultado(resultado.solucao[x1])}, "
            f"{x2} = {formatar_resultado(resultado.solucao[x2])}, "
            f"Z = {formatar_resultado(melhor)}",
        ))

    # Verifica se existe uma direção da região em que Z melhora sem parar.
    def _objetivo_cresce_sem_limite(self, problema, direcoes):
        for direcao in direcoes:
            variacao = problema.calcular_objetivo(direcao)
            if (problema.eh_maximizacao and variacao > 0) or (
                not problema.eh_maximizacao and variacao < 0
            ):
                return True
        return False

    # Etapa 1: tabela das retas. Cada restrição vira uma igualdade e, para
    # desenhar a reta, calculamos onde ela corta os eixos (x1 = 0 e x2 = 0).
    # O teste da origem mostra de que lado da reta fica a região permitida.
    def _etapa_retas(self, problema):
        x1, x2 = problema.variaveis
        linhas = []
        for restricao in problema.restricoes:
            a1, a2 = restricao.coeficientes
            b = restricao.lado_direito
            reta = Restricao(restricao.coeficientes, IGUAL, b)

            corte_x2 = _corte_no_eixo(a2, b)
            corte_x1 = _corte_no_eixo(a1, b)
            linhas.append([
                reta.como_texto(problema.variaveis),
                f"{x2} = {corte_x2}" if corte_x2 else "não corta",
                f"{x1} = {corte_x1}" if corte_x1 else "não corta",
                _pontos_da_reta(a1, a2, b),
                _teste_da_origem(restricao),
            ])

        descricao = (
            "Primeiro trocamos o sinal de cada restrição por '=' para obter a reta.\n"
            f"Para desenhar a reta, fazemos {x1} = 0 e calculamos {x2}, depois "
            f"fazemos {x2} = 0 e calculamos {x1}. Esses dois pontos definem a reta.\n"
            "O teste da origem substitui (0, 0) na restrição para saber de que lado "
            "da reta ficam os pontos permitidos."
        )
        return Etapa(
            titulo="Tabela das retas",
            descricao=descricao,
            colunas=["Equação da reta", f"Se {x1} = 0", f"Se {x2} = 0", "Pontos", "Teste (0, 0)"],
            rotulos_linhas=[f"R{i}" for i in range(1, len(linhas) + 1)],
            linhas=linhas,
            rotulo_base="Reta",
        )

    # Etapa 2: explica como o gráfico é montado a partir da tabela das retas.
    def _etapa_montagem(self, problema):
        x1, x2 = problema.variaveis
        return Etapa(
            "Montagem do gráfico",
            "Com a tabela das retas montamos o gráfico:\n\n"
            f"1. Desenhamos os eixos {x1} e {x2}. Como {x1} >= 0 e {x2} >= 0, "
            "usamos só o primeiro quadrante.\n"
            "2. Marcamos os dois pontos de cada reta e ligamos esses pontos.\n"
            "3. Para cada restrição ficamos com o lado indicado pelo teste da origem "
            "(<= e >=) ou com a própria reta (=).\n"
            "4. A região viável é a parte do gráfico que atende todas as restrições "
            "ao mesmo tempo (área pintada na aba Gráfico).\n"
            "5. Os vértices da região viável são os cantos dessa área, ou seja, os "
            "pontos em que as retas se cruzam dentro das restrições.",
        )

    # Etapa 3: tabela com os vértices da região viável, as retas que se cruzam
    # em cada um e o valor de Z.
    def _etapa_vertices(self, problema, resultado):
        x1, x2 = problema.variaveis
        valores = [problema.calcular_objetivo(v) for v in resultado.vertices]
        melhor = max(valores) if problema.eh_maximizacao else min(valores)

        nomes_retas = [f"R{i}" for i in range(1, len(problema.restricoes) + 1)]
        nomes_retas += [f"eixo {x2} ({x1} = 0)", f"eixo {x1} ({x2} = 0)"]
        restricoes = problema.restricoes + restricoes_nao_negatividade()

        linhas = []
        for vertice, z in zip(resultado.vertices, valores):
            cruzamento = [nome for nome, r in zip(nomes_retas, restricoes)
                          if r.valor_em(vertice) == r.lado_direito]
            linhas.append([" e ".join(cruzamento), vertice[0], vertice[1], z])

        texto = (
            "Os vértices são os pontos em que duas retas se cruzam e que atendem "
            "todas as restrições (pontos de cruzamento fora da região viável são "
            "descartados).\n"
            "Em cada vértice calculamos o valor da função objetivo Z. "
            "A linha destacada é a de melhor valor."
        )
        if resultado.regiao_ilimitada:
            texto += "\n\nObservação: a região viável é ilimitada (não é um polígono fechado)."

        return Etapa(
            titulo="Vértices da região viável",
            descricao=texto,
            colunas=["Retas que se cruzam", x1, x2, "Z"],
            rotulos_linhas=[f"P{i}" for i in range(1, len(valores) + 1)],
            linhas=linhas,
            rotulo_base="Vértice",
            linha_destaque=valores.index(melhor),
        )


# Valor de uma variável quando a outra é zero (a*x = b). Retorna None quando
# a reta não corta esse eixo (coeficiente zero).
def _corte_no_eixo(coeficiente, b):
    if coeficiente == 0:
        return None
    return formatar_numero(b / coeficiente)


# Pontos usados para desenhar a reta a1*x1 + a2*x2 = b. Quando um dos
# coeficientes é zero a reta é paralela a um eixo e basta um ponto. Se a reta
# passa pela origem, usamos x1 = 1 para achar o segundo ponto.
def _pontos_da_reta(a1, a2, b):
    if a2 == 0:
        return f"{formatar_ponto((b / a1, Fraction(0)))}, reta vertical"
    if a1 == 0:
        return f"{formatar_ponto((Fraction(0), b / a2))}, reta horizontal"

    pontos = [(Fraction(0), b / a2), (b / a1, Fraction(0))]
    if b == 0:
        pontos = [(Fraction(0), Fraction(0)), (Fraction(1), -a1 / a2)]
    return " e ".join(formatar_ponto(p) for p in pontos)


# Substitui (0, 0) na restrição e diz se a origem fica do lado permitido.
def _teste_da_origem(restricao):
    b = formatar_numero(restricao.lado_direito)
    if restricao.lado_direito == 0:
        return "reta passa pela origem"
    if restricao.sinal == IGUAL:
        return "só os pontos da reta"
    atende = restricao.atendida_por((0, 0))
    lado = "verdadeiro: lado da origem" if atende else "falso: lado oposto à origem"
    return f"0 {restricao.sinal} {b} ({lado})"


# Restrições x1 >= 0 e x2 >= 0, tratadas como retas comuns (os eixos).
def restricoes_nao_negatividade():
    return [
        Restricao([Fraction(1), Fraction(0)], MAIOR_IGUAL, Fraction(0)),
        Restricao([Fraction(0), Fraction(1)], MAIOR_IGUAL, Fraction(0)),
    ]


# Ponto em que duas retas se cruzam (regra de Cramer). None se forem paralelas.
def intersecao(r1, r2):
    a1, b1 = r1.coeficientes
    a2, b2 = r2.coeficientes
    c1, c2 = r1.lado_direito, r2.lado_direito

    determinante = a1 * b2 - a2 * b1
    if determinante == 0:
        return None
    x = (c1 * b2 - c2 * b1) / determinante
    y = (a1 * c2 - a2 * c1) / determinante
    return (x, y)


# Calcula os vértices da região definida pelas restrições: cruza todas as
# retas duas a duas e mantém só os pontos que atendem todas as restrições.
def calcular_vertices(restricoes):
    vertices = []
    for r1, r2 in combinations(restricoes, 2):
        ponto = intersecao(r1, r2)
        if ponto is None or ponto in vertices:
            continue
        if all(r.atendida_por(ponto) for r in restricoes):
            vertices.append(ponto)
    return ordenar_vertices(vertices)


# Ordena os vértices em volta do centro, para formar o contorno do polígono.
def ordenar_vertices(vertices):
    if len(vertices) < 3:
        return vertices
    cx = sum(float(v[0]) for v in vertices) / len(vertices)
    cy = sum(float(v[1]) for v in vertices) / len(vertices)
    return sorted(vertices, key=lambda v: math.atan2(float(v[1]) - cy, float(v[0]) - cx))


# Procura direções em que a região viável se estende infinitamente.
# As candidatas são os eixos e as direções ao longo de cada reta; uma direção
# d é válida se, andando sobre ela, nenhuma restrição é violada.
def direcoes_ilimitadas(restricoes):
    candidatas = [(Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))]
    for restricao in restricoes:
        a, b = restricao.coeficientes
        candidatas += [(b, -a), (-b, a)]

    validas = []
    for direcao in candidatas:
        if direcao == (0, 0) or direcao in validas:
            continue
        if all(_direcao_respeita(r, direcao) for r in restricoes):
            validas.append(direcao)
    return validas


# Uma direção respeita a restrição se andar nela não piora o lado esquerdo.
def _direcao_respeita(restricao, direcao):
    variacao = restricao.valor_em(direcao)
    if restricao.sinal == MENOR_IGUAL:
        return variacao <= 0
    if restricao.sinal == MAIOR_IGUAL:
        return variacao >= 0
    return variacao == 0
