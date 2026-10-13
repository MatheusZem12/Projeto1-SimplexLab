from fractions import Fraction

import pytest

from simplexlab.algoritmos.algoritmo_pl import ILIMITADO, INVIAVEL, OTIMO, montar_forma_padrao
from simplexlab.algoritmos.algoritmo_simplex import MetodoSimplex
from simplexlab.algoritmos.resolvedor import METODO_GRAFICO, METODO_SIMPLEX, resolver
from simplexlab.modelo import EXEMPLOS, ler_modelo

METODOS = [METODO_SIMPLEX, METODO_GRAFICO]


def resolver_texto(texto, metodo):
    return resolver(ler_modelo(texto), metodo)


# Resultado esperado de cada exemplo: (status, Z ótimo).
ESPERADO = {
    "Maximização clássica (2 variáveis)": (OTIMO, 36),
    "Minimização com restrições >=": (OTIMO, 9),
    "Restrição de igualdade": (OTIMO, 13),
    "Maximização com 3 variáveis": (OTIMO, 13),
    "Soluções ótimas múltiplas": (OTIMO, 16),
    "Problema ilimitado": (ILIMITADO, None),
    "Problema inviável": (INVIAVEL, None),
}


def test_todos_os_exemplos_tem_resultado_esperado():
    assert set(ESPERADO) == set(EXEMPLOS)


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("nome", list(ESPERADO))
def test_exemplos(nome, metodo):
    problema = ler_modelo(EXEMPLOS[nome])
    if metodo == METODO_GRAFICO and problema.num_variaveis != 2:
        pytest.skip("método gráfico só com 2 variáveis")

    resultado = resolver(problema, metodo)
    status, valor = ESPERADO[nome]
    assert resultado.status == status
    assert resultado.valor_otimo == valor
    assert resultado.etapas

    # A solução encontrada precisa atender as restrições e dar o valor ótimo.
    if status == OTIMO:
        ponto = [resultado.solucao[v] for v in problema.variaveis]
        assert all(r.atendida_por(ponto) for r in problema.restricoes)
        assert all(x >= 0 for x in ponto)
        assert problema.calcular_objetivo(ponto) == valor


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("texto, valor", [
    # lado direito negativo é multiplicado por -1
    ("max z = x1 + x2\nx1 - x2 >= -2\nx1 <= 3\nx2 <= 4", 7),
    # minimização só com <=
    ("min z = -x1 - x2\nx1 + 2x2 <= 4\n3x1 + x2 <= 6", Fraction(-14, 5)),
    # restrições de igualdade redundantes (artificial fica na base com valor 0)
    ("max z = x1 + x2\nx1 + x2 = 2\n2x1 + 2x2 = 4\nx1 <= 1", 2),
    # variável no lado direito
    ("max z = 2x1 + x2\nx1 <= x2 + 1\nx2 <= 3", 11),
    # reta que passa pela origem
    ("max z = x1 + x2\nx1 - x2 = 0\nx1 <= 2", 4),
    # região ilimitada, mas com mínimo finito
    ("min z = x1 + x2\nx1 + x2 >= 2", 2),
])
def test_casos_especiais(texto, valor, metodo):
    resultado = resolver_texto(texto, metodo)
    assert resultado.status == OTIMO
    assert resultado.valor_otimo == valor


@pytest.mark.parametrize("metodo", METODOS)
def test_minimizacao_ilimitada(metodo):
    assert resolver_texto("min z = x1 - x2\nx1 >= 1", metodo).status == ILIMITADO


def test_simplex_e_duas_fases_sao_escolhidos_automaticamente():
    so_folgas = resolver_texto(EXEMPLOS["Maximização clássica (2 variáveis)"], METODO_SIMPLEX)
    com_artificiais = resolver_texto(EXEMPLOS["Minimização com restrições >="], METODO_SIMPLEX)
    assert so_folgas.metodo == "Simplex"
    assert com_artificiais.metodo == "Simplex - Duas Fases"


def test_quadros_do_exemplo_classico():
    resultado = resolver_texto(EXEMPLOS["Maximização clássica (2 variáveis)"], METODO_SIMPLEX)
    quadros = [e for e in resultado.etapas if e.tem_tabela]

    inicial = quadros[0]
    assert inicial.colunas == ["x1", "x2", "f1", "f2", "f3", "b"]
    assert inicial.rotulos_linhas == ["f1", "f2", "f3", "Z"]
    assert inicial.linhas[-1] == [-3, -5, 0, 0, 0, 0]
    # entra x2 (mais negativo) e sai f2 (razão 12/2 = 6)
    assert (inicial.linha_destaque, inicial.coluna_destaque) == (1, 1)

    final = quadros[-1]
    assert final.linhas[-1] == [0, 0, 0, Fraction(3, 2), 1, 36]
    assert resultado.variaveis_auxiliares == {"f1": 2, "f2": 0, "f3": 0}


def test_forma_padrao_com_excesso_e_artificial():
    forma = montar_forma_padrao(ler_modelo("min z = x1 + x2\nx1 + x2 >= 4\nx1 = 1\nx2 <= 5"))
    assert forma.colunas == ["x1", "x2", "e1", "f3", "a1", "a2"]
    assert [forma.colunas[j] for j in forma.base] == ["a1", "a2", "f3"]
    assert forma.linhas[0] == [1, 1, -1, 0, 1, 0, 4]


def test_simplex_comum_recusa_problema_com_artificiais():
    with pytest.raises(ValueError, match="Duas Fases"):
        MetodoSimplex().resolver(ler_modelo(EXEMPLOS["Minimização com restrições >="]))


def test_solucoes_multiplas_sao_avisadas():
    texto = EXEMPLOS["Soluções ótimas múltiplas"]
    simplex = resolver_texto(texto, METODO_SIMPLEX)
    grafico = resolver_texto(texto, METODO_GRAFICO)
    assert any("alternativas" in obs for obs in simplex.observacoes)
    assert len(grafico.pontos_otimos) == 2


def test_problema_degenerado_que_cicla_termina():
    # Exemplo de Beale: com a regra do mais negativo o Simplex entra em ciclo.
    texto = (
        "max z = 3/4x1 - 20x2 + 1/2x3 - 6x4\n"
        "1/4x1 - 8x2 - x3 + 9x4 <= 0\n"
        "1/2x1 - 12x2 - 1/2x3 + 3x4 <= 0\n"
        "x3 <= 1"
    )
    resultado = resolver_texto(texto, METODO_SIMPLEX)
    assert resultado.status == OTIMO
    assert resultado.valor_otimo == Fraction(5, 4)
    assert any("regra de Bland" in e.descricao for e in resultado.etapas)


def test_metodo_grafico_exige_duas_variaveis():
    with pytest.raises(ValueError, match="2 variáveis"):
        resolver_texto(EXEMPLOS["Maximização com 3 variáveis"], METODO_GRAFICO)


def test_vertices_do_metodo_grafico():
    resultado = resolver_texto(EXEMPLOS["Maximização clássica (2 variáveis)"], METODO_GRAFICO)
    assert set(resultado.vertices) == {(0, 0), (4, 0), (4, 3), (2, 6), (0, 6)}
    assert resultado.pontos_otimos == [(2, 6)]
    assert not resultado.regiao_ilimitada
