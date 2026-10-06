import tkinter as tk
from tkinter import ttk

from simplexlab.algoritmos.resolvedor import METODO_GRAFICO, METODO_SIMPLEX


# Opções de método de resolução.
class SeletorMetodo(ttk.LabelFrame):

    def __init__(self, mestre):
        super().__init__(mestre, text="Método de resolução", padding=10)
        self._metodo = tk.StringVar(value=METODO_SIMPLEX)

        ttk.Radiobutton(
            self, text="Simplex (mostra os quadros)", value=METODO_SIMPLEX, variable=self._metodo
        ).pack(anchor="w")
        ttk.Radiobutton(
            self, text="Gráfico (apenas 2 variáveis)", value=METODO_GRAFICO, variable=self._metodo
        ).pack(anchor="w", pady=(4, 0))

    # Retorna o método marcado (METODO_SIMPLEX ou METODO_GRAFICO).
    def metodo_escolhido(self):
        return self._metodo.get()
