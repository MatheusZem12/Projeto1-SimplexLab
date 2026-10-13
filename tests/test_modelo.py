from fractions import Fraction

import pytest

from simplexlab.modelo import (
    EXEMPLOS,
    IGUAL,
    MAIOR_IGUAL,
    MENOR_IGUAL,
    MINIMIZAR,
    ErroLeitura,
    formatar_decimal,
    formatar_numero,
    formatar_resultado,
    ler_modelo,
    montar_expressao,
)


def test_le_modelo_completo():
    problema = ler_modelo(EXEMPLOS["Maximização clássica (2 variáveis)"])

    assert problema.eh_maximizacao
    assert problema.variaveis == ["x1", "x2"]
    assert problema.objetivo == [3, 5]
    assert [r.coeficientes for r in problema.restricoes] == [[1, 0], [0, 2], [3, 2]]
    assert [r.lado_direito for r in problema.restricoes] == [4, 12, 18]
    assert all(r.sinal == MENOR_IGUAL for r in problema.restricoes)


def test_todos_os_exemplos_sao_lidos():
    for texto in EXEMPLOS.values():
        ler_modelo(texto)


def test_sinais_alternativos():
    problema = ler_modelo("min: x1 + x2\nx1 ≥ 1\nx2 => 2\nx1 + x2 == 5")
    assert problema.tipo == MINIMIZAR
    assert [r.sinal for r in problema.restricoes] == [MAIOR_IGUAL, MAIOR_IGUAL, IGUAL]


def test_decimais_fracoes_e_comentarios():
    problema = ler_modelo("max z = 0,5x1 + 1/2x2  # comentário\nsujeito a\n1.5x1 + x2 <= 3/4")
    assert problema.objetivo == [Fraction(1, 2), Fraction(1, 2)]
    assert problema.restricoes[0].coeficientes == [Fraction(3, 2), 1]
    assert problema.restricoes[0].lado_direito == Fraction(3, 4)


def test_variaveis_e_constantes_dos_dois_lados():
    problema = ler_modelo("max z = 2x1 + x2\nx1 + 2 <= x2 + 5")
    restricao = problema.restricoes[0]
    assert restricao.coeficientes == [1, -1]
    assert restricao.lado_direito == 3


def test_ordem_natural_das_variaveis():
    problema = ler_modelo("max z = x10 + x2 + x1\nx1 + x2 + x10 <= 1")
    assert problema.variaveis == ["x1", "x2", "x10"]


def test_nao_negatividade_e_ignorada():
    problema = ler_modelo("max z = x1 + x2\nx1 <= 1\nx1, x2 >= 0")
    assert len(problema.restricoes) == 1


@pytest.mark.parametrize("texto, trecho_da_mensagem", [
    ("", "Digite o modelo"),
    ("z = x1\nx1 <= 1", "primeira linha"),
    ("max z = x1", "pelo menos uma restrição"),
    ("max z = 3x1 5x2\nx1 <= 1", "falta um sinal"),
    ("max z = x1\nx1 <= 2 <= 3", "exatamente um sinal"),
    ("max z = x1\n3 <= 4", "não tem variáveis"),
    ("max z = x1 + 3\nx1 <= 1", "termo constante"),
    ("max z = x1\nx1 <= 2 $", "não foi possível entender"),
])
def test_erros_de_leitura(texto, trecho_da_mensagem):
    with pytest.raises(ErroLeitura, match=trecho_da_mensagem):
        ler_modelo(texto)


def test_formatacao_de_numeros():
    assert formatar_numero(Fraction(4)) == "4"
    assert formatar_numero(Fraction(-3, 2)) == "-3/2"
    assert formatar_decimal(Fraction(1, 3)) == "0,3333"
    assert formatar_resultado(Fraction(9, 2)) == "9/2 (4,5)"


def test_montar_expressao():
    assert montar_expressao([3, -1, 0], ["x1", "x2", "x3"]) == "3x1 - x2"
    assert montar_expressao([-1, 2], ["x1", "x2"]) == "-x1 + 2x2"
    assert montar_expressao([0, 0], ["x1", "x2"]) == "0"


def test_modelo_como_texto():
    problema = ler_modelo("min z = 2x1 + 3x2\nx1 + x2 >= 4")
    assert problema.como_texto() == "Min Z = 2x1 + 3x2\ns.a.\n    x1 + x2 >= 4\n    x1, x2 >= 0"
