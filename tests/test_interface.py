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
