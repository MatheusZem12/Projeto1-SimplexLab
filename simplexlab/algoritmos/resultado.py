from dataclasses import dataclass, field
from fractions import Fraction

OTIMO = "otimo"
ILIMITADO = "ilimitado"
INVIAVEL = "inviavel"

DESCRICAO_STATUS = {
    OTIMO: "Solução ótima encontrada",
    ILIMITADO: "Problema ilimitado (sem solução ótima finita)",
    INVIAVEL: "Problema inviável (não existe solução que atenda todas as restrições)",
}


# Uma etapa da resolução. Sempre tem título e explicação, e pode ter uma
# tabela (quadro do Simplex ou tabela de vértices do método gráfico).
@dataclass
class Etapa:
    titulo: str
    descricao: str
    colunas: list = field(default_factory=list)
    rotulos_linhas: list = field(default_factory=list)
    linhas: list = field(default_factory=list)
    rotulo_base: str = "Base"
    ultima_linha_objetivo: bool = False
    linha_destaque: int | None = None
    coluna_destaque: int | None = None

    @property
    def tem_tabela(self):
        return bool(self.linhas)


# Resultado comum aos dois métodos.
@dataclass
class Resultado:
    metodo: str
    status: str
    valor_otimo: Fraction | None = None
    solucao: dict = field(default_factory=dict)
    variaveis_auxiliares: dict = field(default_factory=dict)
    etapas: list = field(default_factory=list)
    observacoes: list = field(default_factory=list)

    @property
    def descricao_status(self):
        return DESCRICAO_STATUS[self.status]


# Resultado do método gráfico, com as informações extras para desenhar o gráfico.
@dataclass
class ResultadoGrafico(Resultado):
    vertices: list = field(default_factory=list)
    pontos_otimos: list = field(default_factory=list)
    regiao_ilimitada: bool = False
