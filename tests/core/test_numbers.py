import re

import pytest

from haradaer.core.xmlfmt import format_number, java_double_str, parse_number


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0.0, "0"),
        (-0.0, "-0"),
        (1.0, "1"),
        (-3.5, "-3.5"),
        (100.0, "100"),
        (0.001, "0.001"),
        (0.0009999, "9.999E-4"),
        (1.0e-5, "1.0E-5"),
        (9999999.0, "9999999"),
        (10000000.0, "1.0E7"),
        (12345678.9, "1.23456789E7"),
        (1.0e10, "1.0E10"),
        (1.0e22, "1.0E22"),
        (4.9e-324, "4.9E-324"),
        (2e-323, "2.0E-323"),
        (1e23, "1.0E23"),
        (5e-3, "0.005"),
        (1.7976931348623157e308, "1.7976931348623157E308"),
        (0.1 + 0.2, "0.30000000000000004"),
        (1 / 3, "0.3333333333333333"),
    ],
)
def test_formato_dos_numeros(valor, esperado):
    assert format_number(valor) == esperado


def test_java_double_str_mantem_o_ponto_zero():
    assert java_double_str(100.0) == "100.0"
    assert java_double_str(1.0e10) == "1.0E10"


def test_valores_especiais():
    assert java_double_str(float("nan")) == "NaN"
    assert java_double_str(float("inf")) == "Infinity"
    assert java_double_str(float("-inf")) == "-Infinity"


def test_numeros_do_terraer_voltam_iguais(referencia):
    """Cada número que o TerraER gravou em `amostra-numeros.xml` sai igual ao ser formatado."""
    texto = (referencia / "amostra-numeros.xml").read_text(encoding="ascii")
    numeros = re.findall(r'\b[xywh]="([^"]*)"', texto)
    assert len(numeros) > 100
    for gravado in numeros:
        assert format_number(parse_number(gravado)) == gravado
