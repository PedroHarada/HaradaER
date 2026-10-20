"""Leitura dos atributos de estilo (`<a>`) de uma figura.

Os nomes e a forma dos valores foram verificados em arquivos gravados pelo TerraER
(`docs/referencia-terraer/amostra-estilos.xml` e as demais amostras).
"""

from __future__ import annotations

from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import parse_number

RGBA = tuple[int, int, int, int]

BLACK: RGBA = (0, 0, 0, 255)
WHITE: RGBA = (255, 255, 255, 255)


def parse_color(texto: str) -> RGBA:
    """`#aarrggbb` (como o TerraER grava) para `(r, g, b, a)`."""
    texto = texto.lstrip("#")
    if len(texto) == 6:
        texto = "ff" + texto
    alfa, vermelho, verde, azul = (int(texto[i : i + 2], 16) for i in (0, 2, 4, 6))
    return (vermelho, verde, azul, alfa)


class Style:
    """Os atributos de estilo de uma figura. Vários blocos `<a>` se juntam; o último vence."""

    def __init__(self, entradas: dict[str, Element] | None = None):
        self._entradas = entradas or {}

    @classmethod
    def of(cls, elemento: Element) -> Style:
        entradas: dict[str, Element] = {}
        for bloco in elemento.children_named("a"):
            for entrada in bloco.children:
                if entrada.children:
                    entradas[entrada.tag] = entrada.children[0]
        return cls(entradas)

    def has(self, nome: str) -> bool:
        return nome in self._entradas

    def string(self, nome: str, padrao: str | None = None) -> str | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag != "string":
            return padrao
        return valor.text or ""

    def boolean(self, nome: str, padrao: bool | None = None) -> bool | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag != "boolean":
            return padrao
        return (valor.text or "").strip() == "true"

    def double(self, nome: str, padrao: float | None = None) -> float | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag not in ("double", "float", "int", "long") or not valor.text:
            return padrao
        return parse_number(valor.text)

    def color(self, nome: str, padrao: RGBA | None = None) -> RGBA | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag != "color" or "rgba" not in valor.attrs:
            return padrao
        return parse_color(valor.attrs["rgba"])

    def doubles(self, nome: str) -> tuple[float, ...] | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag != "doubleArray":
            return None
        return tuple(parse_number(f.text or "0") for f in valor.children_named("double"))

    def enum(self, nome: str, padrao: str | None = None) -> str | None:
        valor = self._entradas.get(nome)
        if valor is None or valor.tag != "enum":
            return padrao
        return valor.text or padrao

    def font_face(self) -> tuple[str, int, float] | None:
        """(família, estilo, tamanho) de `<fontFace><font name style size/>`."""
        valor = self._entradas.get("fontFace")
        if valor is None or valor.tag != "font":
            return None
        return (
            valor.attrs.get("name", "Dialog"),
            int(valor.attrs.get("style", "0")),
            float(valor.attrs.get("size", "12")),
        )
