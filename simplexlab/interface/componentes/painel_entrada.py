import tkinter as tk
from tkinter import ttk

from simplexlab.interface.estilos import CORES, FONTE_MONO

DICA_FORMATO = (
    "1ª linha: função objetivo (max ou min)\n"
    "Demais linhas: uma restrição por linha (<=, >= ou =)\n"
    "A não negatividade (x1, x2 >= 0) é opcional"
)


# Área onde o usuário digita o modelo de PL (entrada por expressão).
class PainelEntrada(ttk.LabelFrame):

    def __init__(self, mestre):
        super().__init__(mestre, text="Modelo de Programação Linear", padding=10)

        moldura = ttk.Frame(self)
        moldura.pack(fill="both", expand=True)

        self.texto = tk.Text(
            moldura,
            font=FONTE_MONO,
            width=34,
            height=14,
            wrap="none",
            undo=True,
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            bg=CORES["painel"],
            padx=8,
            pady=6,
        )
        rolagem = ttk.Scrollbar(moldura, orient="vertical", command=self.texto.yview)
        self.texto.configure(yscrollcommand=rolagem.set)

        self.texto.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")

        ttk.Label(self, text=DICA_FORMATO, style="Dica.TLabel", justify="left").pack(
            anchor="w", pady=(8, 0)
        )

    # Retorna o texto digitado.
    def obter_texto(self):
        return self.texto.get("1.0", "end").strip()

    # Substitui o conteúdo da caixa de texto.
    def definir_texto(self, conteudo):
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", conteudo)

    # Apaga o modelo digitado.
    def limpar(self):
        self.texto.delete("1.0", "end")
