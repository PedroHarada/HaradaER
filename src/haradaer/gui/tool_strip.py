"""Faixa de ferramentas que rola na horizontal.

Todos os botões ficam numa linha só. O que não couber fica fora da vista e se alcança rolando:
dois dedos no trackpad, a roda do mouse (que aqui rola para os lados) ou as setas das pontas,
que só aparecem quando falta espaço. Substitui o menu "»" do `QToolBar`, que escondia botões.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAction, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from haradaer.gui.tool_icons import ICON_SIZE

ARROW_STEP = 120  # pixels por clique nas setas
BUTTON_STYLE = "QToolButton { padding: 1px 2px; font-size: 8pt; }"


class ToolStrip(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._botoes: dict[QAction, QToolButton] = {}

        self._conteudo = QWidget()
        self._linha = QHBoxLayout(self._conteudo)
        self._linha.setContentsMargins(2, 2, 2, 2)
        self._linha.setSpacing(1)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self._conteudo)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.viewport().installEventFilter(self)
        self.scroll.horizontalScrollBar().rangeChanged.connect(self._update_arrows)
        self.scroll.horizontalScrollBar().valueChanged.connect(self._update_arrows)

        self.left = self._arrow(Qt.ArrowType.LeftArrow, -ARROW_STEP)
        self.right = self._arrow(Qt.ArrowType.RightArrow, ARROW_STEP)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.left)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(self.right)
        self._update_arrows()

    def _arrow(self, direcao: Qt.ArrowType, passo: int) -> QToolButton:
        seta = QToolButton()
        seta.setArrowType(direcao)
        seta.setAutoRepeat(True)  # segurar o clique continua rolando
        seta.setAutoRaise(True)
        seta.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        seta.clicked.connect(lambda: self.scroll_by(passo))
        return seta

    # --- conteúdo ----------------------------------------------------------------------------

    def add_action(self, acao: QAction) -> QToolButton:
        botao = QToolButton()
        botao.setDefaultAction(acao)
        botao.setIconSize(ICON_SIZE)
        botao.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        botao.setAutoRaise(True)
        botao.setStyleSheet(BUTTON_STYLE)
        self._linha.addWidget(botao)
        self._botoes[acao] = botao
        self._fit_height()
        return botao

    def add_separator(self) -> None:
        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.VLine)
        linha.setFrameShadow(QFrame.Shadow.Sunken)
        self._linha.addWidget(linha)

    def finish(self) -> None:
        """Depois do último botão: o espaço que sobra fica à direita."""
        self._linha.addStretch(1)
        self._fit_height()

    def button_for(self, acao: QAction) -> QToolButton:
        return self._botoes[acao]

    def _fit_height(self) -> None:
        altura = self._conteudo.sizeHint().height()
        self.scroll.setFixedHeight(altura)
        self.setFixedHeight(altura)

    # --- rolagem -----------------------------------------------------------------------------

    def scroll_by(self, pixels: int) -> None:
        barra = self.scroll.horizontalScrollBar()
        barra.setValue(barra.value() + pixels)

    def ensure_visible(self, acao: QAction) -> None:
        """Rola até o botão da ação ficar à vista."""
        botao = self._botoes.get(acao)
        if botao is not None:
            self.scroll.ensureWidgetVisible(botao, 8, 0)

    def overflows(self) -> bool:
        return self.scroll.horizontalScrollBar().maximum() > 0

    def _update_arrows(self, *_args) -> None:
        barra = self.scroll.horizontalScrollBar()
        sobra = barra.maximum() > 0
        self.left.setVisible(sobra)
        self.right.setVisible(sobra)
        self.left.setEnabled(barra.value() > barra.minimum())
        self.right.setEnabled(barra.value() < barra.maximum())

    def eventFilter(self, objeto: QObject, evento: QEvent) -> bool:
        if evento.type() == QEvent.Type.Wheel and isinstance(evento, QWheelEvent):
            pixels = evento.pixelDelta()
            if not pixels.isNull():  # trackpad: dois dedos, em qualquer direção
                passo = pixels.x() if abs(pixels.x()) >= abs(pixels.y()) else pixels.y()
            else:  # roda do mouse: para cima rola para a esquerda
                angulo = evento.angleDelta()
                passo = (angulo.x() if angulo.x() else angulo.y()) // 2
            self.scroll_by(-passo)
            evento.accept()
            return True
        return super().eventFilter(objeto, evento)
