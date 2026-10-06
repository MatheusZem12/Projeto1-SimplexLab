from fractions import Fraction


# Converte um número para texto. Inteiros aparecem sem casas decimais e os
# demais aparecem como fração (ex.: 3/2), que é como montamos os quadros em aula.
def formatar_numero(valor):
    valor = Fraction(valor)
    if valor.denominator == 1:
        return str(valor.numerator)
    if valor.denominator <= 1000:
        return f"{valor.numerator}/{valor.denominator}"
    return formatar_decimal(valor)


# Mostra o número em decimal com no máximo 4 casas, usando vírgula.
def formatar_decimal(valor):
    texto = f"{float(valor):.4f}".rstrip("0").rstrip(".")
    if texto == "-0":
        texto = "0"
    return texto.replace(".", ",")


# Usado nos resultados finais: mostra a fração e, se não for inteiro,
# também o valor aproximado em decimal. Ex.: "9/2 (4,5)".
def formatar_resultado(valor):
    valor = Fraction(valor)
    if valor.denominator == 1:
        return str(valor.numerator)
    return f"{formatar_numero(valor)} ({formatar_decimal(valor)})"


# Monta uma expressão linear legível a partir dos coeficientes.
# Ex.: [3, -1, 0] com ["x1", "x2", "x3"] vira "3x1 - x2".
def montar_expressao(coeficientes, nomes):
    partes = []
    for coeficiente, nome in zip(coeficientes, nomes):
        if coeficiente == 0:
            continue
        sinal = "-" if coeficiente < 0 else "+"
        modulo = abs(coeficiente)
        termo = nome if modulo == 1 else f"{formatar_numero(modulo)}{nome}"
        if not partes:
            partes.append(f"-{termo}" if sinal == "-" else termo)
        else:
            partes.append(f"{sinal} {termo}")
    return " ".join(partes) if partes else "0"
