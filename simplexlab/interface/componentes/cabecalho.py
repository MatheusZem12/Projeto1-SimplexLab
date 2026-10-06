from tkinter import ttk


# Faixa azul no topo da janela com o nome do projeto.
class Cabecalho(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre, style="Cabecalho.TFrame", padding=(20, 12))
        ttk.Label(self, text="SimplexLab", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Resolução de modelos de Programação Linear pelo Método Gráfico e pelo Simplex",
            style="Subtitulo.TLabel",
        ).pack(anchor="w")
