"""Medida de texto. O núcleo não tem fontes; a interface fornece a medida real."""

from __future__ import annotations

from typing import Protocol

from haradaer.core.appearance.ops import FontSpec


class TextMeasurer(Protocol):
    def size(self, text: str, font: FontSpec) -> tuple[float, float]:
        """Largura e altura do texto numa linha."""
        ...


class FixedMeasurer:
    """Medida fixa e previsível, para testes: largura proporcional ao tamanho da fonte."""

    def __init__(self, largura_por_caractere: float = 0.6, altura: float = 1.36):
        self._largura = largura_por_caractere
        self._altura = altura

    def size(self, text: str, font: FontSpec) -> tuple[float, float]:
        return (len(text) * font.size * self._largura, font.size * self._altura)
