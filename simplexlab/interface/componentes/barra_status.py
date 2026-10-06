from tkinter import ttk

from simplexlab.interface.estilos import CORES


# Linha no rodapé da janela com mensagens curtas para o usuário.
class BarraStatus(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre, padding=(12, 4))
        self.rotulo = ttk.Label(self, text="Pronto.", style="Dica.TLabel")
        self.rotulo.pack(anchor="w")

    # Mostra uma mensagem normal.
    def informar(self, mensagem):
        self.rotulo.configure(text=mensagem, foreground=CORES["texto_suave"])

    # Mostra uma mensagem de erro em vermelho.
    def erro(self, mensagem):
        self.rotulo.configure(text=mensagem, foreground=CORES["erro"])
