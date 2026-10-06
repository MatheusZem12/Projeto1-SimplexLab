from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from simplexlab.interface.desenho.desenho_grafico import desenhar_metodo_grafico


# Aba "Gráfico": área do Matplotlib dentro do Tkinter, com a barra de
# ferramentas (zoom, mover, salvar imagem).
class PainelGrafico(ttk.Frame):

    def __init__(self, mestre):
        super().__init__(mestre, padding=8)

        self.figura = Figure(figsize=(6, 5), dpi=100)
        self.eixo = self.figura.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figura, master=self)

        barra = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        barra.update()
        barra.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.limpar()

    # Desenha o resultado do método gráfico.
    def desenhar(self, problema, resultado):
        self.eixo.set_axis_on()
        desenhar_metodo_grafico(self.eixo, problema, resultado)
        self.figura.tight_layout()
        self.canvas.draw_idle()

    # Deixa o gráfico vazio, com uma mensagem no meio.
    def limpar(self, mensagem="Resolva um modelo com 2 variáveis pelo Método Gráfico."):
        self.eixo.clear()
        self.eixo.set_axis_off()
        self.eixo.text(0.5, 0.5, mensagem, ha="center", va="center", fontsize=11, color="#666666")
        self.canvas.draw_idle()
