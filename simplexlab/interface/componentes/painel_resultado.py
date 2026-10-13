import tkinter as tk
from tkinter import ttk

from simplexlab.algoritmos.algoritmo_pl import ILIMITADO, INVIAVEL, OTIMO
from simplexlab.interface.estilos import CORES, FAMILIA, FONTE_MONO, FONTE_SECAO
from simplexlab.modelo import formatar_decimal, formatar_numero

COR_STATUS = {OTIMO: CORES["sucesso"], ILIMITADO: CORES["alerta"], INVIAVEL: CORES["erro"]}


# Aba "Resultado": situação do problema, valor ótimo, valores das variáveis,
# observações e o modelo como o sistema entendeu.
class PainelResultado(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre, padding=16)

        self.status = ttk.Label(self, text="", font=FONTE_SECAO)
        self.status.pack(anchor="w")

        self.metodo = ttk.Label(self, text="", style="Dica.TLabel")
        self.metodo.pack(anchor="w", pady=(2, 10))

        self.valor_otimo = ttk.Label(self, text="", font=(FAMILIA, 14, "bold"))
        self.valor_otimo.pack(anchor="w", pady=(0, 10))

        conteudo = ttk.Frame(self)
        conteudo.pack(fill="both", expand=True)
        conteudo.columnconfigure(0, weight=1)
        conteudo.columnconfigure(1, weight=1)
        conteudo.rowconfigure(1, weight=1)

        ttk.Label(conteudo, text="Variáveis").grid(row=0, column=0, sticky="w")
        ttk.Label(conteudo, text="Modelo interpretado").grid(row=0, column=1, sticky="w", padx=(16, 0))

        self.tabela = self._criar_tabela_variaveis(conteudo)
        self.tabela.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self.modelo = tk.Text(
            conteudo, font=FONTE_MONO, height=10, wrap="none", relief="solid",
            borderwidth=1, highlightthickness=0, bg=CORES["painel"], padx=10, pady=8,
        )
        self.modelo.grid(row=1, column=1, sticky="nsew", padx=(16, 0), pady=(4, 0))

        self.observacoes = ttk.Label(self, text="", wraplength=700, justify="left")
        self.observacoes.pack(anchor="w", pady=(12, 0))

        self.limpar()

    # Cria a tabela (Treeview) com as colunas Variável, Valor e Decimal.
    def _criar_tabela_variaveis(self, mestre):
        tabela = ttk.Treeview(mestre, columns=("variavel", "valor", "decimal"),
                              show="headings", height=8)
        tabela.heading("variavel", text="Variável")
        tabela.heading("valor", text="Valor")
        tabela.heading("decimal", text="Decimal")
        for coluna in ("variavel", "valor", "decimal"):
            tabela.column(coluna, anchor="center", width=100)
        tabela.tag_configure("auxiliar", foreground=CORES["texto_suave"])
        return tabela

    # Preenche o painel com o resultado de uma resolução.
    def mostrar(self, problema, resultado):
        self.limpar()

        self.status.configure(text=resultado.descricao_status,
                              foreground=COR_STATUS[resultado.status])
        self.metodo.configure(text=f"Método utilizado: {resultado.metodo}")

        if resultado.valor_otimo is not None:
            tipo = "máximo" if problema.eh_maximizacao else "mínimo"
            self.valor_otimo.configure(
                text=f"Z {tipo} = {formatar_numero(resultado.valor_otimo)}"
            )

        for nome, valor in resultado.solucao.items():
            self.tabela.insert("", "end", values=(nome, formatar_numero(valor), formatar_decimal(valor)))
        for nome, valor in resultado.variaveis_auxiliares.items():
            self.tabela.insert("", "end", values=(nome, formatar_numero(valor), formatar_decimal(valor)),
                               tags=("auxiliar",))

        self._escrever_modelo(problema.como_texto())
        self.observacoes.configure(text="\n".join(resultado.observacoes))

    # Limpa todas as informações do painel.
    def limpar(self):
        self.status.configure(text="Nenhum modelo resolvido", foreground=CORES["texto_suave"])
        self.metodo.configure(text="Digite ou carregue um modelo e clique em Resolver.")
        self.valor_otimo.configure(text="")
        self.tabela.delete(*self.tabela.get_children())
        self._escrever_modelo("")
        self.observacoes.configure(text="")

    # Escreve o modelo na caixa de texto somente leitura.
    def _escrever_modelo(self, texto):
        self.modelo.configure(state="normal")
        self.modelo.delete("1.0", "end")
        self.modelo.insert("1.0", texto)
        self.modelo.configure(state="disabled")
