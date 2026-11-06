"""Campos de texto flutuantes para editar no próprio desenho: o nome de um elemento (RF-18) e o
conteúdo de um Texto (RF-26)."""

from __future__ import annotations

import math
from collections.abc import Callable

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFocusEvent, QFont, QKeyEvent, QTextCursor
from PySide6.QtWidgets import QFrame, QLineEdit, QTextEdit, QWidget


class InlineEdit(QLineEdit):
    """Enter (ou clicar fora) confirma; Esc cancela. Chama `on_finish(texto)` só se confirmar."""

    def __init__(
        self,
        pai: QWidget,
        retangulo: QRect,
        texto: str,
        fonte: QFont,
        on_finish: Callable[[str], None],
        on_close: Callable[[], None],
    ):
        super().__init__(texto, pai)
        self._on_finish, self._on_close = on_finish, on_close
        self._cancelled = False
        self._done = False
        self.setFont(fonte)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setGeometry(retangulo)
        self.editingFinished.connect(self._finish)
        self.show()
        self.setFocus()
        self.selectAll()

    def cancel(self) -> None:
        self._cancelled = True
        self._finish()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return
        super().keyPressEvent(event)

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        texto = self.text()
        self.hide()
        if not self._cancelled:
            self._on_finish(texto)
        self._on_close()
        self.deleteLater()


# Ctrl + tecla: o marcador do Markdown em volta da seleção.
MARKERS = {Qt.Key.Key_B: "**", Qt.Key.Key_I: "*"}


class InlineTextEdit(QTextEdit):
    """Editor de várias linhas para o Texto (RF-26). Enter quebra a linha; Ctrl+Enter (ou clicar
    fora) confirma; Esc cancela. Cresce para baixo conforme o texto, como a caixa do Texto.

    O texto aparece com os marcadores do Markdown (RF-28); Ctrl+B e Ctrl+I põem `**` e `*` em
    volta da seleção (ou do cursor)."""

    def __init__(
        self,
        pai: QWidget,
        retangulo: QRect,
        texto: str,
        fonte: QFont,
        margem: float,
        on_finish: Callable[[str], None],
        on_close: Callable[[], None],
    ):
        super().__init__(pai)
        self._on_finish, self._on_close = on_finish, on_close
        self._cancelled = False
        self._done = False
        self._min_height = retangulo.height()
        self.setAcceptRichText(False)
        self.setFont(fonte)
        self.document().setDocumentMargin(margem)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "QTextEdit { background: white; color: black; border: 1px solid black; }"
        )
        self.setPlainText(texto)
        self.setGeometry(retangulo)
        self.textChanged.connect(self._fit)
        self._fit()
        self.show()
        self.setFocus()
        self.selectAll()

    def _fit(self) -> None:
        altura = math.ceil(self.document().size().height()) + 2
        self.resize(self.width(), max(self._min_height, altura))

    def cancel(self) -> None:
        self._cancelled = True
        self._finish()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
            return
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if ctrl and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish()
            return
        if ctrl and event.key() in MARKERS:
            self.wrap_selection(MARKERS[event.key()])
            return
        super().keyPressEvent(event)

    def wrap_selection(self, marcador: str) -> None:
        """Põe o marcador antes e depois da seleção; sem seleção, o cursor fica entre os dois."""
        cursor = self.textCursor()
        selecionado = cursor.selectedText().replace("\u2029", "\n")  # o Qt troca \n por U+2029
        cursor.insertText(f"{marcador}{selecionado}{marcador}")
        if not selecionado:
            cursor.movePosition(
                QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(marcador)
            )
        self.setTextCursor(cursor)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self._finish()

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        texto = self.toPlainText()
        self.hide()
        if not self._cancelled:
            self._on_finish(texto)
        self._on_close()
        self.deleteLater()
