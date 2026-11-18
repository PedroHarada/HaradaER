"""Ícones de traço da barra de comandos (menu, novo, abrir e salvar).

Desenhos simples em SVG, de uma linha, na cor do texto do tema: trocar de tema os redesenha.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

COMMAND_ICON_SIZE = QSize(18, 18)
_ESCALA_TELA = 2  # o dobro de pixels, para ficar nítido em telas de alta densidade

_DESENHOS = {
    "menu": '<path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11" stroke-width="1.4"/>',
    "novo": '<path d="M4 1.5h5l3 3v10H4z M9 1.5v3h3"/>',
    "abrir": '<path d="M1.5 4h5l1 1.5h7v8h-13z"/>',
    "salvar": '<path d="M2 2h10l2 2v10H2z M5 2v4h6V2 M5 14v-4h6v4"/>',
}
NAMES = tuple(_DESENHOS)


def command_icon(nome: str) -> QIcon:
    """O ícone com o traço na cor do texto da paleta atual."""
    cor = QApplication.palette().windowText().color().name()
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        f'<g fill="none" stroke="{cor}" stroke-width="1.1" stroke-linejoin="round">'
        f"{_DESENHOS[nome]}</g></svg>"
    )
    imagem = QPixmap(COMMAND_ICON_SIZE * _ESCALA_TELA)
    imagem.setDevicePixelRatio(_ESCALA_TELA)
    imagem.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagem)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode())).render(pintor, QRectF(0, 0, 18, 18))
    pintor.end()
    return QIcon(imagem)
