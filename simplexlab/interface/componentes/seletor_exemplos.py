from tkinter import ttk

from simplexlab.modelo import EXEMPLOS


# Lista de exemplos prontos e de enunciados importados com IA. Ao clicar em
# "Carregar", chama ao_carregar passando o texto do modelo escolhido; o botão
# "Importar enunciado" chama ao_importar.
class SeletorExemplos(ttk.LabelFrame):

    def __init__(self, mestre, ao_carregar, ao_importar):
        super().__init__(mestre, text="Exemplos", padding=10)
        self._ao_carregar = ao_carregar
        self._modelos = dict(EXEMPLOS)

        linha = ttk.Frame(self)
        linha.pack(fill="x")

        self.combo = ttk.Combobox(linha, values=list(self._modelos), state="readonly")
        self.combo.current(0)
        self.combo.pack(side="left", fill="x", expand=True)

        ttk.Button(linha, text="Carregar", command=self._carregar).pack(side="left", padx=(8, 0))

        ttk.Button(self, text="Importar enunciado com IA (texto ou imagem)",
                   command=ao_importar).pack(fill="x", pady=(8, 0))

    # Coloca um modelo importado no topo da lista e já deixa ele selecionado.
    def adicionar(self, titulo, texto):
        nome = f"IA: {titulo}"
        numero = 2
        while nome in self._modelos:
            nome = f"IA: {titulo} ({numero})"
            numero += 1

        self._modelos = {nome: texto, **self._modelos}
        self.combo.configure(values=list(self._modelos))
        self.combo.current(0)

    # Envia o texto do modelo selecionado para quem criou o componente.
    def _carregar(self):
        self._ao_carregar(self._modelos[self.combo.get()])
