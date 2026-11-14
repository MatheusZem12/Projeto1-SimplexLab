# SimplexLab

Projeto da disciplina de Pesquisa Operacional: aplicativo que resolve modelos de
Programação Linear pelo **Método Gráfico** e pelo **Método Simplex**, mostrando as
etapas da resolução.

Integrantes: Lucas Prata Pradella, Ricardo Almeida Amaro, Matheus Lajarin Zem e
Leandro Daniel Lopes Camargo.

## Como executar

Requisitos: Python 3.10 ou superior com Tkinter, e as bibliotecas de
`requirements.txt`. Para importar enunciados com IA, também uma chave de API da
Anthropic (veja abaixo).

No Windows também existe o executável `SimplexLab.exe` (veja "Gerar o executável"),
que não precisa de Python nem de configuração.

```bash
pip install -r requirements.txt
python main.py
```

No Linux também dá para usar `./start.sh`, que prepara o ambiente e abre o programa.

## Como digitar o modelo

```
max z = 3x1 + 5x2
s.a.
x1 <= 4
2x2 <= 12
3x1 + 2x2 <= 18
x1, x2 >= 0
```

- A primeira linha é a função objetivo, começando com `max` ou `min`.
- Cada linha seguinte é uma restrição, com `<=`, `>=` ou `=`.
- A linha `s.a.` e a não negatividade são opcionais (todas as variáveis são
  consideradas >= 0).
- Aceita decimais (`0.5` ou `0,5`) e frações (`1/2`).

## Importar enunciado com IA

O botão **Importar enunciado com IA** (ao lado dos exemplos) abre uma janela onde
você cola o enunciado completo da questão: texto, print (Ctrl+V cola imagem
também) ou um arquivo de imagem. A IA monta o modelo de PL, que entra na lista de
exemplos como `IA: <nome do problema>` e já aparece na caixa do modelo. Depois é o
fluxo normal: conferir o modelo, escolher Simplex ou Gráfico e clicar em Resolver.

A IA usada é o Claude (`claude-opus-5-5`) pela **API da Anthropic**, com o SDK
oficial `anthropic`. O enunciado e as imagens vão da memória direto para a API:
o programa **não grava nenhum arquivo nem histórico** no computador.

A chave de API vem, nesta ordem:

1. da chave embutida no executável (gerada pelo `gerar_executavel.py`);
2. da variável de ambiente `ANTHROPIC_API_KEY`, para quem roda pelo código-fonte:

```bash
# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python main.py
```

Cada importação custa poucos centavos de dólar (veja `ModeloGerado.custo_estimado`).

## Gerar o executável (Windows)

```bash
pip install -r requirements.txt pyinstaller
python gerar_executavel.py
```

Antes, salve a chave de API no arquivo `chave_api.txt` na raiz do projeto. Esse
arquivo está no `.gitignore` e **nunca deve ir para o GitHub**. O script embute a
chave no executável, apaga os arquivos intermediários que contêm a chave e gera
`dist/SimplexLab.exe` e `dist/SimplexLab.zip` (executável + LEIA-ME).

Quem tiver o `.exe` consegue extrair a chave com algum esforço, então use uma
chave de um workspace com **limite de gasto** e desative a chave quando ela não
for mais necessária.

## Estrutura do projeto

O código é separado em três camadas: o modelo não conhece os algoritmos, e os
algoritmos não conhecem a interface. Assim dá para testar os cálculos sem abrir
a janela.

```
main.py                         ponto de entrada da aplicação
gerar_executavel.py             gera o SimplexLab.exe (com a chave embutida) e o zip
simplexlab/
    modelo.py                   ProblemaPL e Restricao, leitura do texto digitado,
                                formatação de números (frações) e exemplos prontos
    gerador_pl.py               gera o PL de um enunciado usando a API do Claude
    algoritmos/
        algoritmo_pl.py         partes comuns: Etapa, Resultado e forma padrão
                                (folga, excesso e artificiais)
        algoritmo_simplex.py    quadro do Simplex, pivoteamento e Método Simplex
        algoritmo_duas_fases.py Simplex de Duas Fases (restrições >= e =)
        algoritmo_grafico.py    Método Gráfico (2 variáveis)
        resolvedor.py           escolhe o algoritmo adequado
    interface/
        estilos.py              cores, fontes e estilos ttk
        componentes/            um arquivo por componente da tela (inclusive a
                                janela de importar enunciado)
        desenho/
            desenho_grafico.py  desenho do método gráfico com Matplotlib
        telas/
            tela_principal.py   monta a tela e liga interface e algoritmos
tests/
    test_modelo.py              leitura do modelo e formatação
    test_algoritmos.py          resultados dos métodos, quadros e casos especiais
    test_gerador_pl.py          gerador de PL com um cliente falso (não gasta créditos)
    test_interface.py           abre a tela, resolve os exemplos e importa enunciado
```

## Testes

```bash
python -m pytest
```

## O que o sistema mostra

- **Resultado:** situação do problema (ótimo, ilimitado ou inviável), valor ótimo de
  Z, valores das variáveis e o modelo como foi interpretado.
- **Gráfico:** retas das restrições, região viável, vértices, reta da função
  objetivo e o ponto ótimo.
- **Etapas:** no Simplex, a forma padrão e cada quadro com o pivô destacado, o teste
  da razão e a explicação da escolha das variáveis que entram e saem da base. No
  método gráfico, a tabela das retas (cortes nos eixos e teste da origem), a
  montagem do gráfico e a tabela dos vértices com o valor de Z em cada um.

Os cálculos são feitos com frações exatas (`fractions.Fraction`), então os quadros
aparecem com os mesmos valores que obtemos resolvendo à mão.
