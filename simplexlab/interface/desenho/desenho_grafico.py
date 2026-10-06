"""
Desenho do método gráfico com Matplotlib.

Recebe um eixo (Axes) já criado, o problema e o resultado do MetodoGrafico,
e desenha: as retas das restrições, a região viável, os vértices, a reta da
função objetivo passando pelo ótimo e o ponto ótimo.
"""

from fractions import Fraction

from simplexlab.algoritmos.metodo_grafico import (
    calcular_vertices,
    formatar_ponto,
    restricoes_nao_negatividade,
)
from simplexlab.algoritmos.resultado import ILIMITADO, INVIAVEL
from simplexlab.modelo.problema import MENOR_IGUAL, Restricao

CORES_RETAS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf"]
COR_REGIAO = "#9ecae1"
COR_OTIMO = "#d62728"


# Função principal: desenha tudo no eixo informado.
def desenhar_metodo_grafico(eixo, problema, resultado):
    eixo.clear()
    limite_x, limite_y = _calcular_limites(problema, resultado)

    _desenhar_regiao(eixo, problema, limite_x, limite_y)
    _desenhar_restricoes(eixo, problema, limite_x, limite_y)
    _desenhar_vertices(eixo, resultado)

    if resultado.pontos_otimos:
        _desenhar_objetivo(eixo, problema, resultado, limite_x, limite_y)

    x1, x2 = problema.variaveis
    eixo.set_xlim(0, limite_x)
    eixo.set_ylim(0, limite_y)
    eixo.set_xlabel(x1)
    eixo.set_ylabel(x2)
    eixo.set_title(_titulo(resultado))
    eixo.grid(True, linestyle=":", alpha=0.6)
    eixo.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, borderaxespad=0)


# Define até onde os eixos vão: considera os vértices e os pontos em que as
# retas cortam os eixos, com uma margem. Se a região for ilimitada, aumenta
# a área para dar para perceber que ela continua.
def _calcular_limites(problema, resultado):
    xs = [Fraction(1)]
    ys = [Fraction(1)]
    for x, y in resultado.vertices:
        xs.append(x)
        ys.append(y)
    for restricao in problema.restricoes:
        a1, a2 = restricao.coeficientes
        b = restricao.lado_direito
        if a1 != 0 and b / a1 > 0:
            xs.append(b / a1)
        if a2 != 0 and b / a2 > 0:
            ys.append(b / a2)

    if resultado.regiao_ilimitada:
        limite = float(max(xs + ys)) * 1.6
        return limite, limite
    return float(max(xs)) * 1.25, float(max(ys)) * 1.25


# Pinta a região viável. Para conseguir desenhar regiões ilimitadas, a região
# é cortada pelo retângulo visível do gráfico antes de calcular o contorno.
def _desenhar_regiao(eixo, problema, limite_x, limite_y):
    caixa = [
        Restricao([Fraction(1), Fraction(0)], MENOR_IGUAL, Fraction(limite_x)),
        Restricao([Fraction(0), Fraction(1)], MENOR_IGUAL, Fraction(limite_y)),
    ]
    restricoes = problema.restricoes + restricoes_nao_negatividade() + caixa
    contorno = calcular_vertices(restricoes)

    if len(contorno) >= 3:
        xs = [float(p[0]) for p in contorno]
        ys = [float(p[1]) for p in contorno]
        eixo.fill(xs, ys, color=COR_REGIAO, alpha=0.45, label="Região viável")
    elif len(contorno) == 2:
        # Região que é só um segmento (ex.: restrição de igualdade).
        xs = [float(p[0]) for p in contorno]
        ys = [float(p[1]) for p in contorno]
        eixo.plot(xs, ys, color=COR_REGIAO, linewidth=6, alpha=0.8, label="Região viável")


# Desenha uma reta para cada restrição.
def _desenhar_restricoes(eixo, problema, limite_x, limite_y):
    for i, restricao in enumerate(problema.restricoes):
        a1, a2 = (float(a) for a in restricao.coeficientes)
        b = float(restricao.lado_direito)
        cor = CORES_RETAS[i % len(CORES_RETAS)]
        rotulo = f"R{i + 1}: {restricao.como_texto(problema.variaveis)}"

        if a2 != 0:
            xs = [0, limite_x]
            ys = [(b - a1 * x) / a2 for x in xs]
        else:
            xs = [b / a1, b / a1]
            ys = [0, limite_y]
        eixo.plot(xs, ys, color=cor, linewidth=1.6, label=rotulo)


# Marca os vértices da região viável com as coordenadas.
def _desenhar_vertices(eixo, resultado):
    for ponto in resultado.vertices:
        x, y = float(ponto[0]), float(ponto[1])
        eixo.plot(x, y, "o", color="#333333", markersize=5)
        eixo.annotate(formatar_ponto(ponto), (x, y), textcoords="offset points",
                      xytext=(6, 6), fontsize=8)


# Desenha a reta da função objetivo passando pelo ponto ótimo (Z = valor ótimo)
# e destaca o(s) ponto(s) ótimo(s).
def _desenhar_objetivo(eixo, problema, resultado, limite_x, limite_y):
    c1, c2 = (float(c) for c in problema.objetivo)
    z = float(resultado.valor_otimo)
    rotulo = f"Z = {z:g}".replace(".", ",")

    if c2 != 0:
        xs = [0, limite_x]
        ys = [(z - c1 * x) / c2 for x in xs]
    else:
        xs = [z / c1, z / c1]
        ys = [0, limite_y]
    eixo.plot(xs, ys, linestyle="--", color="#555555", linewidth=1.4, label=rotulo)

    for indice, ponto in enumerate(resultado.pontos_otimos):
        eixo.plot(float(ponto[0]), float(ponto[1]), marker="*", color=COR_OTIMO,
                  markersize=16, linestyle="none",
                  label="Ponto ótimo" if indice == 0 else None, zorder=5)


# Título do gráfico conforme a situação do problema.
def _titulo(resultado):
    if resultado.status == INVIAVEL:
        return "Região viável vazia (problema inviável)"
    if resultado.status == ILIMITADO:
        return "Região ilimitada (problema ilimitado)"
    return "Método Gráfico"
