from simplexlab.algoritmos.algoritmo_duas_fases import MetodoDuasFases
from simplexlab.algoritmos.algoritmo_grafico import MetodoGrafico
from simplexlab.algoritmos.algoritmo_pl import montar_forma_padrao
from simplexlab.algoritmos.algoritmo_simplex import MetodoSimplex

METODO_GRAFICO = "grafico"
METODO_SIMPLEX = "simplex"


# Escolhe o algoritmo certo para o problema e devolve o resultado.
# No caso do Simplex, se a forma padrão precisar de variáveis artificiais
# (restrições >= ou =), usa automaticamente o método das Duas Fases.
def resolver(problema, metodo):
    if metodo == METODO_GRAFICO:
        return MetodoGrafico().resolver(problema)

    if montar_forma_padrao(problema).artificiais:
        return MetodoDuasFases().resolver(problema)
    return MetodoSimplex().resolver(problema)
