# Problemas prontos para testar o sistema e usar na apresentação.
# Cada exemplo cobre uma situação diferente que o professor pode pedir.

EXEMPLOS = {
    "Maximização clássica (2 variáveis)": """max z = 3x1 + 5x2
s.a.
x1 <= 4
2x2 <= 12
3x1 + 2x2 <= 18
x1, x2 >= 0""",

    "Minimização com restrições >=": """min z = 2x1 + 3x2
s.a.
x1 + x2 >= 4
x1 + 3x2 >= 6
x1, x2 >= 0""",

    "Restrição de igualdade": """max z = 2x1 + 3x2
s.a.
x1 + x2 = 5
x1 <= 4
x2 <= 3
x1, x2 >= 0""",

    "Maximização com 3 variáveis": """max z = 5x1 + 4x2 + 3x3
s.a.
2x1 + 3x2 + x3 <= 5
4x1 + x2 + 2x3 <= 11
3x1 + 4x2 + 2x3 <= 8
x1, x2, x3 >= 0""",

    "Soluções ótimas múltiplas": """max z = 2x1 + 4x2
s.a.
x1 + 2x2 <= 8
x1 <= 6
x2 <= 3
x1, x2 >= 0""",

    "Problema ilimitado": """max z = x1 + 2x2
s.a.
x1 - x2 <= 2
x1 <= 4
x1, x2 >= 0""",

    "Problema inviável": """max z = x1 + x2
s.a.
x1 + x2 <= 2
x1 + x2 >= 5
x1, x2 >= 0""",
}
