"""
Conversão do modelo para a forma padrão usada pelo Simplex.

Regras aplicadas em cada restrição:
    <=  soma uma variável de folga (f)
    >=  subtrai uma variável de excesso (e) e soma uma artificial (a)
    =   soma uma variável artificial (a)

Se o lado direito for negativo, a restrição é multiplicada por -1 antes,
invertendo o sinal da desigualdade.
"""

from dataclasses import dataclass
from fractions import Fraction

from simplexlab.modelo.problema import IGUAL, MAIOR_IGUAL, MENOR_IGUAL, Restricao
from simplexlab.util.formatacao import formatar_numero, montar_expressao

INVERSO = {MENOR_IGUAL: MAIOR_IGUAL, MAIOR_IGUAL: MENOR_IGUAL, IGUAL: IGUAL}


@dataclass
class FormaPadrao:
    colunas: list
    linhas: list
    base: list
    custos: list
    artificiais: list
    descricao: str


# Monta a forma padrão do problema: colunas (nomes das variáveis), linhas
# da matriz [A | b], base inicial e custos já no sentido de maximização.
def montar_forma_padrao(problema):
    n = problema.num_variaveis
    explicacao = []

    if problema.eh_maximizacao:
        custos_originais = list(problema.objetivo)
    else:
        custos_originais = [-c for c in problema.objetivo]
        explicacao.append(
            "Problema de minimização: resolvemos Max (-Z), multiplicando a função "
            "objetivo por -1. No final o sinal do valor ótimo é trocado de volta."
        )
        explicacao.append("")

    restricoes = [_ajustar_lado_direito(r, i, problema, explicacao)
                  for i, r in enumerate(problema.restricoes, start=1)]

    # Primeiro descobrimos quais variáveis auxiliares cada restrição precisa,
    # para depois montar as colunas na ordem: originais, folga/excesso, artificiais.
    auxiliares = []
    artificiais = []
    for i, restricao in enumerate(restricoes, start=1):
        if restricao.sinal == MENOR_IGUAL:
            auxiliares.append((f"f{i}", Fraction(1)))
            artificiais.append(None)
        elif restricao.sinal == MAIOR_IGUAL:
            auxiliares.append((f"e{i}", Fraction(-1)))
            artificiais.append(f"a{i}")
        else:
            auxiliares.append(None)
            artificiais.append(f"a{i}")

    colunas = list(problema.variaveis)
    colunas += [aux[0] for aux in auxiliares if aux is not None]
    colunas += [nome for nome in artificiais if nome is not None]
    indice = {nome: j for j, nome in enumerate(colunas)}

    linhas = []
    base = []
    explicacao.append("Restrições na forma padrão:")
    for i, restricao in enumerate(restricoes):
        linha = [Fraction(0)] * len(colunas) + [restricao.lado_direito]
        linha[:n] = restricao.coeficientes

        if auxiliares[i] is not None:
            nome, valor = auxiliares[i]
            linha[indice[nome]] = valor
        if artificiais[i] is not None:
            linha[indice[artificiais[i]]] = Fraction(1)

        # A variável básica inicial é a folga (<=) ou a artificial (>= e =).
        if artificiais[i] is not None:
            base.append(indice[artificiais[i]])
        else:
            base.append(indice[auxiliares[i][0]])

        linhas.append(linha)
        explicacao.append(
            f"    R{i + 1}: {montar_expressao(linha[:-1], colunas)} = "
            f"{formatar_numero(restricao.lado_direito)}"
        )

    custos = custos_originais + [Fraction(0)] * (len(colunas) - n)

    folgas = [aux[0] for aux in auxiliares if aux is not None and aux[1] > 0]
    excessos = [aux[0] for aux in auxiliares if aux is not None and aux[1] < 0]
    nomes_artificiais = [nome for nome in artificiais if nome is not None]

    explicacao.append("")
    if folgas:
        explicacao.append(f"Variáveis de folga: {', '.join(folgas)}")
    if excessos:
        explicacao.append(f"Variáveis de excesso: {', '.join(excessos)}")
    if nomes_artificiais:
        explicacao.append(f"Variáveis artificiais: {', '.join(nomes_artificiais)}")
    explicacao.append(f"Base inicial: {', '.join(colunas[j] for j in base)}")

    return FormaPadrao(
        colunas=colunas,
        linhas=linhas,
        base=base,
        custos=custos,
        artificiais=[indice[nome] for nome in nomes_artificiais],
        descricao="\n".join(explicacao),
    )


# Se o lado direito (b) for negativo, multiplica a restrição por -1.
# O Simplex precisa de b >= 0 para começar de uma solução básica viável.
def _ajustar_lado_direito(restricao, numero, problema, explicacao):
    if restricao.lado_direito >= 0:
        return restricao

    ajustada = Restricao(
        coeficientes=[-a for a in restricao.coeficientes],
        sinal=INVERSO[restricao.sinal],
        lado_direito=-restricao.lado_direito,
    )
    explicacao.append(
        f"R{numero} tem lado direito negativo, multiplicamos por -1: "
        f"{ajustada.como_texto(problema.variaveis)}"
    )
    return ajustada
