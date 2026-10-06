"""
Tela principal do SimplexLab.

Organiza os componentes na janela e faz a ligação entre a interface e os
algoritmos: lê o modelo digitado, chama o método escolhido e distribui o
resultado entre as abas Resultado, Gráfico e Etapas.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from simplexlab.algoritmos.resolvedor import METODO_GRAFICO, resolver
from simplexlab.interface.componentes.barra_acoes import BarraAcoes
from simplexlab.interface.componentes.barra_status import BarraStatus
from simplexlab.interface.componentes.cabecalho import Cabecalho
from simplexlab.interface.componentes.painel_entrada import PainelEntrada
from simplexlab.interface.componentes.painel_etapas import PainelEtapas
from simplexlab.interface.componentes.painel_grafico import PainelGrafico
from simplexlab.interface.componentes.painel_resultado import PainelResultado
from simplexlab.interface.componentes.seletor_exemplos import SeletorExemplos
from simplexlab.interface.componentes.seletor_metodo import SeletorMetodo
from simplexlab.interface.estilos import aplicar_estilos
from simplexlab.modelo.exemplos import EXEMPLOS
from simplexlab.modelo.leitor_modelo import ErroLeitura, ler_modelo


class TelaPrincipal:

    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("SimplexLab - Pesquisa Operacional")
        self.janela.geometry("1280x800")
        self.janela.minsize(1000, 650)
        aplicar_estilos(self.janela)

        self._montar_layout()
        self.entrada.definir_texto(next(iter(EXEMPLOS.values())))

    # Cria e posiciona todos os componentes da tela.
    def _montar_layout(self):
        Cabecalho(self.janela).pack(fill="x")

        corpo = ttk.PanedWindow(self.janela, orient="horizontal")
        corpo.pack(fill="both", expand=True, padx=12, pady=12)

        corpo.add(self._montar_coluna_entrada(corpo), weight=0)
        corpo.add(self._montar_abas(corpo), weight=1)

        self.status = BarraStatus(self.janela)
        self.status.pack(fill="x", side="bottom")

        self.janela.bind("<Control-Return>", lambda _evento: self._resolver())

    # Coluna da esquerda: exemplos, modelo, método e botões.
    def _montar_coluna_entrada(self, mestre):
        coluna = ttk.Frame(mestre, padding=(0, 0, 12, 0))

        SeletorExemplos(coluna, ao_carregar=self._carregar_exemplo).pack(fill="x")

        self.entrada = PainelEntrada(coluna)
        self.entrada.pack(fill="both", expand=True, pady=10)

        self.seletor_metodo = SeletorMetodo(coluna)
        self.seletor_metodo.pack(fill="x")

        BarraAcoes(coluna, ao_resolver=self._resolver, ao_limpar=self._limpar).pack(
            fill="x", pady=(10, 0)
        )
        return coluna

    # Lado direito: abas com o resultado, o gráfico e as etapas.
    def _montar_abas(self, mestre):
        self.abas = ttk.Notebook(mestre)

        self.painel_resultado = PainelResultado(self.abas)
        self.painel_grafico = PainelGrafico(self.abas)
        self.painel_etapas = PainelEtapas(self.abas)

        self.abas.add(self.painel_resultado, text="Resultado")
        self.abas.add(self.painel_grafico, text="Gráfico")
        self.abas.add(self.painel_etapas, text="Etapas")
        return self.abas

    # Ação do botão Resolver: lê o modelo, resolve e mostra o resultado.
    def _resolver(self):
        metodo = self.seletor_metodo.metodo_escolhido()
        try:
            problema = ler_modelo(self.entrada.obter_texto())
            resultado = resolver(problema, metodo)
        except ErroLeitura as erro:
            self._mostrar_erro("Erro no modelo", str(erro))
            return
        except (ValueError, RuntimeError) as erro:
            self._mostrar_erro("Não foi possível resolver", str(erro))
            return

        self._exibir_resultado(problema, resultado, metodo)

    # Distribui o resultado entre as abas e escolhe qual aba abrir.
    def _exibir_resultado(self, problema, resultado, metodo):
        self.painel_resultado.mostrar(problema, resultado)
        self.painel_etapas.carregar(resultado.etapas)

        if metodo == METODO_GRAFICO:
            self.painel_grafico.desenhar(problema, resultado)
            self.abas.select(self.painel_grafico)
        else:
            self.painel_grafico.limpar("O gráfico aparece quando o método escolhido é o Gráfico.")
            self.abas.select(self.painel_resultado)

        self.status.informar(f"Método {resultado.metodo}: {resultado.descricao_status}.")

    # Mostra o erro na barra de status e em uma janela de aviso.
    def _mostrar_erro(self, titulo, mensagem):
        self.status.erro(mensagem)
        messagebox.showerror(titulo, mensagem, parent=self.janela)

    # Coloca o texto de um exemplo na caixa de entrada.
    def _carregar_exemplo(self, texto):
        self.entrada.definir_texto(texto)
        self.status.informar("Exemplo carregado. Clique em Resolver.")

    # Limpa a entrada e todas as abas.
    def _limpar(self):
        self.entrada.limpar()
        self.painel_resultado.limpar()
        self.painel_grafico.limpar()
        self.painel_etapas.limpar()
        self.status.informar("Pronto.")

    # Abre a janela e inicia o loop do Tkinter.
    def executar(self):
        self.janela.mainloop()
