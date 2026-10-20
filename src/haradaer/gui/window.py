"""Janela de um documento (RF-19): cada modelo abre na sua própria janela."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox

from haradaer.core import io
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.gui.scene import DiagramScene
from haradaer.gui.view import DiagramView

TITLE = "HaradaER"


class DocumentWindow(QMainWindow):
    closed = Signal(object)
    open_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.path: Path | None = None
        self.diagram_scene = DiagramScene()
        self.view = DiagramView(self.diagram_scene)
        self.setCentralWidget(self.view)
        self.resize(960, 640)

        self._zoom_label = QLabel("100%")
        self.statusBar().addPermanentWidget(self._zoom_label)
        self.view.zoom_changed.connect(self._show_zoom)
        self._build_menus()
        self._update_title()

    # --- menus -------------------------------------------------------------------------------

    def _action(self, texto: str, atalho, funcao) -> QAction:
        acao = QAction(texto, self)
        if atalho is not None:
            acao.setShortcut(atalho)
        acao.triggered.connect(funcao)
        return acao

    def _build_menus(self) -> None:
        arquivo = self.menuBar().addMenu("&Arquivo")
        self.action_open = self._action(
            "&Abrir...", QKeySequence.StandardKey.Open, self.open_requested.emit
        )
        self.action_close = self._action("&Fechar", QKeySequence.StandardKey.Close, self.close)
        self.action_quit = self._action("&Sair", QKeySequence.StandardKey.Quit, self._quit)
        arquivo.addActions([self.action_open, self.action_close])
        arquivo.addSeparator()
        arquivo.addAction(self.action_quit)

        exibir = self.menuBar().addMenu("&Exibir")
        self.action_zoom_in = self._action(
            "&Ampliar", QKeySequence.StandardKey.ZoomIn, self.view.zoom_in
        )
        self.action_zoom_out = self._action(
            "&Reduzir", QKeySequence.StandardKey.ZoomOut, self.view.zoom_out
        )
        self.action_zoom_actual = self._action("&Tamanho real", "Ctrl+0", self.view.zoom_actual)
        self.action_zoom_fit = self._action("A&justar à janela", "Ctrl+9", self.view.zoom_fit)
        exibir.addActions(
            [
                self.action_zoom_in,
                self.action_zoom_out,
                self.action_zoom_actual,
                self.action_zoom_fit,
            ]
        )

    @staticmethod
    def _quit() -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.closeAllWindows()

    # --- documento ---------------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        return self.path is None

    def load(self, caminho: Path) -> bool:
        """Abre o arquivo nesta janela. Em caso de erro mostra a mensagem e devolve `False`."""
        try:
            documento = io.load(caminho)
        except (ArquivoInvalidoError, OSError) as erro:
            QMessageBox.critical(
                self, "Não foi possível abrir o arquivo", f"{caminho.name}\n\n{erro}"
            )
            return False
        self.path = caminho
        self.diagram_scene.set_document(documento)
        self.view.zoom_actual()
        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())
        self._update_title()
        return True

    def _update_title(self) -> None:
        self.setWindowTitle(f"{self.path.name} - {TITLE}" if self.path else TITLE)

    def _show_zoom(self, zoom: float) -> None:
        self._zoom_label.setText(f"{round(zoom * 100)}%")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closed.emit(self)
        super().closeEvent(event)
