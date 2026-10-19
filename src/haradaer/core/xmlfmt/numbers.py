"""Números no formato que o TerraER grava.

O TerraER usa `Double.toString` do Java e remove o `.0` final: `100.0` vira `100`, mas `1.0E10`
continua `1.0E10` (não termina em `.0`). Notação decimal entre 10⁻³ (inclusive) e 10⁷ (exclusive);
fora disso, notação científica com ao menos um dígito depois do ponto.
"""

import math
from decimal import ROUND_HALF_EVEN, Context, Decimal

_DOIS_DIGITOS = Context(prec=2, rounding=ROUND_HALF_EVEN)


def java_double_str(valor: float) -> str:
    """Equivalente a `Double.toString` do Java (dígitos mais curtos que identificam o valor)."""
    if math.isnan(valor):
        return "NaN"
    if math.isinf(valor):
        return "Infinity" if valor > 0 else "-Infinity"
    if valor == 0:
        return "-0.0" if math.copysign(1.0, valor) < 0 else "0.0"

    sinal = "-" if valor < 0 else ""
    _, algarismos, expoente = Decimal(repr(abs(valor))).as_tuple()
    digitos = list(algarismos)
    while len(digitos) > 1 and digitos[-1] == 0:
        digitos.pop()
        expoente += 1
    if len(digitos) == 1:
        # O Java mostra ao menos dois dígitos: entre os decimais de 2 dígitos que ainda
        # identificam o número, escolhe o mais próximo do valor exato (4.9E-324, não 5.0E-324).
        dois = _DOIS_DIGITOS.create_decimal(Decimal(abs(valor)))
        if float(dois) == abs(valor):
            _, algarismos, expoente = dois.as_tuple()
            digitos = list(algarismos)
            while len(digitos) > 1 and digitos[-1] == 0:
                digitos.pop()
                expoente += 1
    ds = "".join(map(str, digitos))
    e10 = len(digitos) + expoente - 1  # expoente na forma d.ddd × 10^e10

    if -3 <= e10 < 7:
        if e10 >= 0:
            inteira = ds[: e10 + 1].ljust(e10 + 1, "0")
            fracao = ds[e10 + 1 :] or "0"
        else:
            inteira = "0"
            fracao = "0" * (-e10 - 1) + ds
        return f"{sinal}{inteira}.{fracao}"
    return f"{sinal}{ds[0]}.{ds[1:] or '0'}E{e10}"


def format_number(valor: float) -> str:
    """Como o TerraER grava um número em atributo ou em `<double>`."""
    texto = java_double_str(valor)
    return texto[:-2] if texto.endswith(".0") else texto


def parse_number(texto: str) -> float:
    """Lê um número gravado pelo TerraER (aceita `1.0E-5`, `-0`, `Infinity`, `NaN`)."""
    return float(texto)
