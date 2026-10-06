from tkinter import ttk


# Botões principais da tela. As ações são recebidas por parâmetro para que
# o componente não precise conhecer a lógica da tela.
class BarraAcoes(ttk.Frame):

    def __init__(self, mestre, ao_resolver, ao_limpar):
        super().__init__(mestre)
        ttk.Button(self, text="Resolver", style="Primario.TButton", command=ao_resolver).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(self, text="Limpar", command=ao_limpar).pack(side="left", padx=(8, 0))
