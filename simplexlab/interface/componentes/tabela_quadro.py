import tkinter as tk
from tkinter import ttk

from simplexlab.interface.estilos import CORES, FONTE_MONO, FAMILIA_MONO
from simplexlab.modelo import formatar_numero

FONTE_CELULA_NEGRITO = (FAMILIA_MONO, 11, "bold")


# Tabela usada para mostrar o quadro do Simplex (ou as tabelas do método
# gráfico). Destaca a linha e a coluna do pivô e o elemento pivô.
# Fica dentro de um Canvas para ter rolagem quando o quadro for grande.
class TabelaQuadro(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre)

        self.canvas = tk.Canvas(self, bg=CORES["painel"], highlightthickness=0)
        rolagem_v = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        rolagem_h = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=rolagem_v.set, xscrollcommand=rolagem_h.set)

        self.grade = tk.Frame(self.canvas, bg=CORES["painel"], padx=10, pady=10)
        self.canvas.create_window((0, 0), window=self.grade, anchor="nw")
        self.grade.bind("<Configure>", self._atualizar_area_rolagem)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        rolagem_v.grid(row=0, column=1, sticky="ns")
        rolagem_h.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    # Desenha a tabela da etapa. Se a etapa não tiver tabela, só limpa.
    def mostrar(self, etapa):
        self.limpar()
        if etapa is None or not etapa.tem_tabela:
            return

        cabecalho = [etapa.rotulo_base] + etapa.colunas
        textos = [[self._texto(v) for v in valores] for valores in etapa.linhas]
        larguras = self._calcular_larguras(cabecalho, etapa.rotulos_linhas, textos)

        for j, texto in enumerate(cabecalho):
            self._criar_celula(0, j, texto, CORES["cabecalho_tabela"], larguras[j], negrito=True)

        total = len(etapa.linhas)
        for i, (rotulo, valores) in enumerate(zip(etapa.rotulos_linhas, textos)):
            eh_objetivo = etapa.ultima_linha_objetivo and i == total - 1
            fundo_linha = CORES["linha_objetivo"] if eh_objetivo else CORES["painel"]

            self._criar_celula(i + 1, 0, rotulo, fundo_linha, larguras[0], negrito=True)
            for j, texto in enumerate(valores):
                fundo = self._cor_da_celula(etapa, i, j, fundo_linha)
                self._criar_celula(i + 1, j + 1, texto, fundo, larguras[j + 1],
                                   negrito=eh_objetivo)

    # Números aparecem como fração; textos (ex.: equação da reta) ficam como estão.
    @staticmethod
    def _texto(valor):
        return valor if isinstance(valor, str) else formatar_numero(valor)

    # Largura de cada coluna (em caracteres): no mínimo 8, ou o maior texto dela.
    @staticmethod
    def _calcular_larguras(cabecalho, rotulos, textos):
        colunas = [[cabecalho[0], *rotulos]]
        for j in range(1, len(cabecalho)):
            colunas.append([cabecalho[j], *(linha[j - 1] for linha in textos)])
        return [max(8, *(len(texto) for texto in coluna)) for coluna in colunas]

    # Remove todas as células da tabela.
    def limpar(self):
        for celula in self.grade.winfo_children():
            celula.destroy()

    # Decide a cor de fundo da célula conforme o pivô da etapa.
    @staticmethod
    def _cor_da_celula(etapa, linha, coluna, padrao):
        na_linha = etapa.linha_destaque == linha
        na_coluna = etapa.coluna_destaque == coluna
        if na_linha and na_coluna:
            return CORES["destaque_pivo"]
        if na_linha or na_coluna:
            return CORES["destaque_linha"]
        return padrao

    # Cria uma célula (Label com borda) na posição da grade.
    def _criar_celula(self, linha, coluna, texto, fundo, largura, negrito=False):
        tk.Label(
            self.grade,
            text=texto,
            bg=fundo,
            fg=CORES["texto"],
            font=FONTE_CELULA_NEGRITO if negrito else FONTE_MONO,
            width=largura,
            padx=6,
            pady=4,
            relief="solid",
            borderwidth=1,
        ).grid(row=linha, column=coluna, sticky="nsew")

    # Atualiza o tamanho da área de rolagem quando a tabela muda.
    def _atualizar_area_rolagem(self, _evento):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
