"""Campo de texto flutuante para editar o nome de um elemento no próprio desenho (RF-18)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QLineEdit, QWidget


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
