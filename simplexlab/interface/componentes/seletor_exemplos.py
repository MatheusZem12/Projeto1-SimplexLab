from tkinter import ttk

from simplexlab.modelo.exemplos import EXEMPLOS


# Lista de exemplos prontos. Ao clicar em "Carregar", chama a função
# recebida em ao_carregar passando o texto do modelo escolhido.
class SeletorExemplos(ttk.LabelFrame):

    def __init__(self, mestre, ao_carregar):
        super().__init__(mestre, text="Exemplos", padding=10)
        self._ao_carregar = ao_carregar

        self.combo = ttk.Combobox(self, values=list(EXEMPLOS), state="readonly")
        self.combo.current(0)
        self.combo.pack(side="left", fill="x", expand=True)

        ttk.Button(self, text="Carregar", command=self._carregar).pack(side="left", padx=(8, 0))

    # Envia o texto do exemplo selecionado para quem criou o componente.
    def _carregar(self):
        self._ao_carregar(EXEMPLOS[self.combo.get()])
