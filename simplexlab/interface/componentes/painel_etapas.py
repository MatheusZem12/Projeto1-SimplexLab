import tkinter as tk
from tkinter import ttk

from simplexlab.interface.componentes.tabela_quadro import TabelaQuadro
from simplexlab.interface.estilos import CORES, FONTE_MONO

LEGENDA = "Amarelo: linha e coluna do pivô     Laranja: elemento pivô"


# Aba "Etapas": mostra a resolução passo a passo, com navegação entre as
# etapas, a explicação de cada uma e o quadro correspondente.
class PainelEtapas(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre, padding=12)
        self.etapas = []
        self.indice = 0

        self._montar_navegacao()

        self.titulo = ttk.Label(self, text="", style="Secao.TLabel")
        self.titulo.pack(anchor="w", pady=(10, 4))

        divisor = ttk.PanedWindow(self, orient="vertical")
        divisor.pack(fill="both", expand=True)

        self.descricao = tk.Text(
            divisor, font=FONTE_MONO, height=10, wrap="word", relief="solid",
            borderwidth=1, highlightthickness=0, bg=CORES["painel"], padx=10, pady=8,
        )
        self.tabela = TabelaQuadro(divisor)
        divisor.add(self.descricao, weight=1)
        divisor.add(self.tabela, weight=2)

        self.legenda = ttk.Label(self, text="", style="Dica.TLabel")
        self.legenda.pack(anchor="w", pady=(6, 0))

        self.limpar()

    # Botões Anterior / Próxima e a lista para pular direto para uma etapa.
    def _montar_navegacao(self):
        barra = ttk.Frame(self)
        barra.pack(fill="x")

        self.botao_anterior = ttk.Button(barra, text="< Anterior", command=self._anterior)
        self.botao_anterior.pack(side="left")

        self.lista_etapas = ttk.Combobox(barra, state="readonly", width=45)
        self.lista_etapas.pack(side="left", padx=8)
        self.lista_etapas.bind("<<ComboboxSelected>>", self._ao_escolher_na_lista)

        self.botao_proxima = ttk.Button(barra, text="Próxima >", command=self._proxima)
        self.botao_proxima.pack(side="left")

        self.posicao = ttk.Label(barra, text="", style="Dica.TLabel")
        self.posicao.pack(side="right")

    # Recebe as etapas de uma nova resolução e mostra a primeira.
    def carregar(self, etapas):
        self.etapas = etapas
        self.lista_etapas.configure(
            values=[f"{i}. {etapa.titulo}" for i, etapa in enumerate(etapas, start=1)]
        )
        self._mostrar(0)

    # Volta o painel para o estado inicial, sem etapas.
    def limpar(self):
        self.etapas = []
        self.lista_etapas.configure(values=[])
        self.lista_etapas.set("")
        self.titulo.configure(text="Nenhuma resolução ainda")
        self._escrever_descricao("Resolva um modelo para ver as etapas aqui.")
        self.tabela.limpar()
        self.legenda.configure(text="")
        self.posicao.configure(text="")
        self._atualizar_botoes()

    # Exibe a etapa do índice informado.
    def _mostrar(self, indice):
        if not self.etapas:
            return
        self.indice = indice
        etapa = self.etapas[indice]

        self.lista_etapas.current(indice)
        self.titulo.configure(text=etapa.titulo)
        self.posicao.configure(text=f"Etapa {indice + 1} de {len(self.etapas)}")
        self._escrever_descricao(etapa.descricao)
        self.tabela.mostrar(etapa)

        tem_pivo = etapa.ultima_linha_objetivo and etapa.coluna_destaque is not None
        self.legenda.configure(text=LEGENDA if tem_pivo else "")
        self._atualizar_botoes()

    # Coloca o texto na caixa de descrição (que fica somente leitura).
    def _escrever_descricao(self, texto):
        self.descricao.configure(state="normal")
        self.descricao.delete("1.0", "end")
        self.descricao.insert("1.0", texto)
        self.descricao.configure(state="disabled")

    # Habilita ou desabilita os botões conforme a posição atual.
    def _atualizar_botoes(self):
        tem_anterior = bool(self.etapas) and self.indice > 0
        tem_proxima = bool(self.etapas) and self.indice < len(self.etapas) - 1
        self.botao_anterior.configure(state="normal" if tem_anterior else "disabled")
        self.botao_proxima.configure(state="normal" if tem_proxima else "disabled")

    # Vai para a etapa anterior.
    def _anterior(self):
        if self.indice > 0:
            self._mostrar(self.indice - 1)

    # Vai para a próxima etapa.
    def _proxima(self):
        if self.indice < len(self.etapas) - 1:
            self._mostrar(self.indice + 1)

    # Mostra a etapa escolhida na lista.
    def _ao_escolher_na_lista(self, _evento):
        self._mostrar(self.lista_etapas.current())
