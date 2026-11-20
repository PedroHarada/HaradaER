"""Conversões entre os tipos do núcleo (cores, fontes) e os do Qt, e pequenos ajudantes de Qt."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF
from PySide6.QtWidgets import QLineEdit

from haradaer.core.appearance import FontSpec
from haradaer.core.appearance.style import RGBA


def qcolor(rgba: RGBA) -> QColor:
    r, g, b, a = rgba
    return QColor(r, g, b, a)


def qfont(spec: FontSpec) -> QFont:
    """Fonte do Qt. `Dialog` e `Monospaced` são fontes lógicas do Java; no Qt viram a fonte sem
    serifa e a monoespaçada do sistema."""
    fonte = QFont()
    if spec.family == "Monospaced":
        fonte.setStyleHint(QFont.StyleHint.Monospace)
        fonte.setFamily("monospace")
    elif spec.family and spec.family != "Dialog":
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


class ClearOnEscape(QObject):
    """Esc num campo de busca com texto apaga o texto; vazio, o Esc segue adiante (fecha a
    janela, por exemplo). Soma-se ao botão de limpar do campo."""

    def eventFilter(self, campo, evento) -> bool:  # noqa: N802 (nome do Qt)
        if (
            evento.type() == QEvent.Type.KeyPress
            and evento.key() == Qt.Key.Key_Escape
            and isinstance(campo, QLineEdit)
            and campo.text()
        ):
            campo.clear()
            return True
        return False


def clear_on_escape(campo: QLineEdit) -> None:
    filtro = ClearOnEscape(campo)
    campo.installEventFilter(filtro)
