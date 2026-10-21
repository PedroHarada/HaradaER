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
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from haradaer.gui.tool_icons import ICON_SIZE

ARROW_STEP = 120  # pixels por clique nas setas
# A folha de estilo (fonte menor) faz o Qt desenhar os destaques com cores fixas, claras;
# por isso eles são definidos aqui com as cores da paleta, que seguem o tema claro ou escuro.
BUTTON_STYLE = (
    "QToolButton { padding: 1px 2px; font-size: 8pt; border: 1px solid transparent;"
    " border-radius: 3px; }"
    "QToolButton:hover { background: palette(midlight); }"
    "QToolButton:checked { background: palette(midlight); border-color: palette(highlight); }"
    "QToolButton:pressed { background: palette(mid); }"
    # Conexão aceita entre os dois elementos selecionados (RF-10): o fundo de destaque do tema.
    'QToolButton[recomendado="true"] { background: palette(highlight);'
    " color: palette(highlighted-text); border-color: palette(highlight); font-weight: bold; }"
)
DIMMED_OPACITY = 0.3  # as conexões que não servem para o par selecionado


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

    def refresh_style(self) -> None:
        """Depois de trocar o tema: o Qt só resolve as cores `palette(...)` da folha de estilo
        quando ela é aplicada, então ela é aplicada de novo."""
        for botao in self._botoes.values():
            botao.setStyleSheet("")
            botao.setStyleSheet(BUTTON_STYLE)

    def set_recommendation(self, candidatas: list[QAction], aceitas: set[QAction] | None) -> None:
        """Com `aceitas`, destaca essas e apaga as outras `candidatas`; com `None`, volta ao
        normal. As apagadas continuam clicáveis (a conexão livre e as vermelhas também valem).
        A faixa rola até a primeira aceita."""
        for acao in candidatas:
            botao = self._botoes[acao]
            destaque = aceitas is not None and acao in aceitas
            if botao.property("recomendado") != destaque:
                botao.setProperty("recomendado", destaque)
                botao.style().unpolish(botao)
                botao.style().polish(botao)
            apagado = aceitas is not None and not destaque
            if apagado and botao.graphicsEffect() is None:
                efeito = QGraphicsOpacityEffect(botao)
                efeito.setOpacity(DIMMED_OPACITY)
                botao.setGraphicsEffect(efeito)
            elif not apagado and botao.graphicsEffect() is not None:
                botao.setGraphicsEffect(None)
        primeira = next((a for a in candidatas if aceitas and a in aceitas), None)
        if primeira is not None:
            self.ensure_visible(primeira)

    def is_highlighted(self, acao: QAction) -> bool:
        return bool(self._botoes[acao].property("recomendado"))

    def is_dimmed(self, acao: QAction) -> bool:
        return self._botoes[acao].graphicsEffect() is not None

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
