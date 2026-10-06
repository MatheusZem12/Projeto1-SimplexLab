# SimplexLab

Projeto da disciplina de Pesquisa Operacional: aplicativo que resolve modelos de
Programação Linear pelo **Método Gráfico** e pelo **Método Simplex**, mostrando as
etapas da resolução.

Integrantes: Lucas Prata Pradella, Ricardo Almeida Amaro, Matheus Lajarin Zem e
Leandro Daniel Lopes Camargo.

## Como executar

Requisitos: Python 3.10 ou superior com Tkinter, e a biblioteca Matplotlib.

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

## Estrutura do projeto

```
main.py                         ponto de entrada da aplicação
simplexlab/
    modelo/
        problema.py             classes ProblemaPL e Restricao
        leitor_modelo.py        converte o texto digitado em um ProblemaPL
        exemplos.py             problemas prontos para teste
    algoritmos/
        resultado.py            classes de resultado e de etapa
        forma_padrao.py         adiciona folga, excesso e artificiais
        quadro_simplex.py       quadro do Simplex e o pivoteamento
        simplex.py              Método Simplex
        duas_fases.py           Simplex de Duas Fases (restrições >= e =)
        metodo_grafico.py       Método Gráfico (2 variáveis)
        resolvedor.py           escolhe o algoritmo adequado
    interface/
        estilos.py              cores, fontes e estilos ttk
        componentes/            um arquivo por componente da tela
        desenho/
            desenho_grafico.py  desenho do método gráfico com Matplotlib
        telas/
            tela_principal.py   monta a tela e liga interface e algoritmos
    util/
        formatacao.py           formatação de números (frações) e expressões
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
