"""Conversões entre os tipos do núcleo (cores, fontes) e os do Qt."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontMetricsF

from haradaer.core.appearance import FontSpec
from haradaer.core.appearance.style import RGBA


def qcolor(rgba: RGBA) -> QColor:
    r, g, b, a = rgba
    return QColor(r, g, b, a)


def qfont(spec: FontSpec) -> QFont:
    """Fonte do Qt. `Dialog` é a fonte lógica do Java; no Qt vira a fonte sem serifa do sistema."""
    fonte = QFont()
    if spec.family and spec.family != "Dialog":
        fonte.setFamily(spec.family)
    else:
        fonte.setStyleHint(QFont.StyleHint.SansSerif)
        fonte.setFamily("sans-serif")
    fonte.setPixelSize(max(1, round(spec.size)))  # o Java usa pontos a 72 dpi: 1 pt = 1 px
    fonte.setBold(spec.bold)
    fonte.setItalic(spec.italic)
    fonte.setUnderline(spec.underline)
    return fonte


class QtMeasurer:
    """Mede texto com as fontes do Qt (`TextMeasurer` do núcleo)."""

    def size(self, text: str, font: FontSpec) -> tuple[float, float]:
        metricas = QFontMetricsF(qfont(font))
        return (metricas.horizontalAdvance(text), metricas.height())
