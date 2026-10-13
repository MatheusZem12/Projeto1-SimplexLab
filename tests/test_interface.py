"""
Teste de fumaça da interface: abre a janela (sem mostrar o loop), resolve
todos os exemplos pelos dois métodos e percorre as etapas. É pulado quando
não há tela disponível (ex.: servidor sem interface gráfica).
"""

import tkinter as tk

import pytest

from simplexlab.algoritmos.resolvedor import METODO_GRAFICO, METODO_SIMPLEX
from simplexlab.interface.telas import tela_principal
from simplexlab.modelo import EXEMPLOS


@pytest.fixture
def tela(monkeypatch):
    erros = []
    monkeypatch.setattr(tela_principal.messagebox, "showerror",
                        lambda titulo, mensagem, **_: erros.append(mensagem))
    try:
        tela = tela_principal.TelaPrincipal()
    except tk.TclError:
        pytest.skip("sem tela disponível")
    tela.janela.withdraw()
    tela.erros = erros
    yield tela
    tela.janela.update()  # termina os desenhos pendentes do Matplotlib
    tela.janela.destroy()


@pytest.mark.parametrize("metodo", [METODO_SIMPLEX, METODO_GRAFICO])
def test_resolve_todos_os_exemplos(tela, metodo):
    tela.seletor_metodo._metodo.set(metodo)
    for nome, texto in EXEMPLOS.items():
        tela.erros.clear()
        tela._carregar_exemplo(texto)
        tela._resolver()
        tela.janela.update()

        if metodo == METODO_GRAFICO and "3 variáveis" in nome:
            assert tela.erros and "2 variáveis" in tela.erros[0]
            continue

        assert not tela.erros, nome
        painel = tela.painel_etapas
        assert painel.etapas
        for _ in painel.etapas:
            painel._proxima()
        assert painel.indice == len(painel.etapas) - 1


def test_erro_de_leitura_aparece_na_barra_de_status(tela):
    tela.entrada.definir_texto("max z = 3x1 5x2\nx1 <= 1")
    tela._resolver()
    assert "falta um sinal" in tela.status.rotulo.cget("text")
    assert tela.erros


def test_limpar(tela):
    tela._resolver()
    tela._limpar()
    assert tela.entrada.obter_texto() == ""
    assert tela.painel_etapas.etapas == []


def test_importar_enunciado_com_ia(tela, monkeypatch):
    from simplexlab.gerador_pl import ModeloGerado
    from simplexlab.interface.componentes import janela_importar

    modelo = "# x1: mesas\nmax z = 30x1 + 20x2\n4x1 + 3x2 <= 240\n2x1 + x2 <= 100"
    monkeypatch.setattr(janela_importar, "gerar_pl",
                        lambda texto, imagens, processo_iniciado: ModeloGerado("Mesas", modelo))

    tela._importar_enunciado()
    janela = next(w for w in tela.janela.winfo_children()
                  if isinstance(w, janela_importar.JanelaImportar))
    janela.texto.insert("1.0", "Uma fábrica produz mesas...")
    janela._gerar()
    while janela.winfo_exists():
        tela.janela.update()

    assert tela.entrada.obter_texto() == modelo
    assert tela.seletor_exemplos.combo.get() == "IA: Mesas"

    # Depois de importado, segue o fluxo normal.
    tela._resolver()
    assert tela.painel_resultado.valor_otimo.cget("text") == "Z máximo = 1700"


def test_solucoes_multiplas_no_resultado(tela):
    tela.entrada.definir_texto("max z = 100x1 + 150x2\n2x1 + 3x2 <= 120\nx1 <= 40\nx2 <= 30")
    tela.seletor_metodo._metodo.set(METODO_GRAFICO)
    tela._resolver()

    linhas = [tela.painel_resultado.tabela.item(i, "values")
              for i in tela.painel_resultado.tabela.get_children()]
    assert linhas == [
        ("Ótimo 1", "", ""), ("x1", "15", "15"), ("x2", "30", "30"),
        ("Ótimo 2", "", ""), ("x1", "40", "40"), ("x2", "40/3", "13,3333"),
    ]
    assert "2 vértices ótimos" in tela.painel_resultado.valor_otimo.cget("text")
