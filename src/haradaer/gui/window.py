"""Janela de um documento (RF-19): cada modelo abre na sua própria janela."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from haradaer.core import io
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.model.document import Document
from haradaer.gui.editor import Editor
from haradaer.gui.palette import CONNECTIONS, ELEMENTS
from haradaer.gui.scene import DiagramScene
from haradaer.gui.view import SELECT, DiagramView, Tool

TITLE = "HaradaER"
UNTITLED = "Sem título"


class DocumentWindow(QMainWindow):
    closed = Signal(object)
    open_requested = Signal()
    new_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.path: Path | None = None
        self.diagram_scene = DiagramScene()
        self.view = DiagramView(self.diagram_scene)
        self.setCentralWidget(self.view)
        self.resize(960, 640)
        self._tool_actions: dict[Tool, QAction] = {}

        self._zoom_label = QLabel("100%")
        self.statusBar().addPermanentWidget(self._zoom_label)
        self.view.zoom_changed.connect(self._show_zoom)
        self.view.message.connect(self.statusBar().showMessage)
        self.view.tool_changed.connect(self._tool_changed)
        self._build_menus()
        self._build_toolbar()
        self._attach(Document.new(), None)

    # --- menus e ferramentas -----------------------------------------------------------------

    def _action(self, texto: str, atalho, funcao) -> QAction:
        acao = QAction(texto, self)
        if atalho is not None:
            acao.setShortcut(atalho)
        acao.triggered.connect(funcao)
        return acao

    def _build_menus(self) -> None:
        arquivo = self.menuBar().addMenu("&Arquivo")
        self.action_new = self._action(
            "&Novo", QKeySequence.StandardKey.New, self.new_requested.emit
        )
        self.action_open = self._action(
            "&Abrir...", QKeySequence.StandardKey.Open, self.open_requested.emit
        )
        self.action_save = self._action("&Salvar", QKeySequence.StandardKey.Save, self.save)
        self.action_save_as = self._action(
            "Salvar &como...", QKeySequence.StandardKey.SaveAs, self.save_as
        )
        self.action_close = self._action("&Fechar", QKeySequence.StandardKey.Close, self.close)
        self.action_quit = self._action("&Sair", QKeySequence.StandardKey.Quit, self._quit)
        arquivo.addActions([self.action_new, self.action_open])
        arquivo.addSeparator()
        arquivo.addActions([self.action_save, self.action_save_as])
        arquivo.addSeparator()
        arquivo.addActions([self.action_close, self.action_quit])

        editar = self.menuBar().addMenu("&Editar")
        self.action_undo = self._action("&Desfazer", QKeySequence.StandardKey.Undo, self._undo)
        self.action_redo = self._action("&Refazer", QKeySequence.StandardKey.Redo, self._redo)
        self.action_delete = self._action("E&xcluir", QKeySequence.StandardKey.Delete, self._delete)
        editar.addActions([self.action_undo, self.action_redo])
        editar.addSeparator()
        editar.addAction(self.action_delete)

        exibir = self.menuBar().addMenu("E&xibir")
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

    def _build_toolbar(self) -> None:
        barra = QToolBar("Ferramentas", self)
        barra.setOrientation(Qt.Orientation.Vertical)
        barra.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, barra)
        grupo = QActionGroup(self)

        def adicionar(tool: Tool, texto: str) -> None:
            acao = QAction(texto, self)
            acao.setCheckable(True)
            acao.triggered.connect(lambda _=False, t=tool: self.view.set_tool(t))
            grupo.addAction(acao)
            barra.addAction(acao)
            self._tool_actions[tool] = acao

        adicionar(SELECT, "Selecionar")
        barra.addSeparator()
        for tag, nome in ELEMENTS:
            adicionar(Tool("create", tag), nome)
        barra.addSeparator()
        for tag, nome in CONNECTIONS:
            adicionar(Tool("connect", tag), nome)
        self._tool_actions[SELECT].setChecked(True)

    def _tool_changed(self, tool: Tool) -> None:
        self._tool_actions[tool].setChecked(True)
        self.statusBar().clearMessage()

    @staticmethod
    def _quit() -> None:
        QApplication.closeAllWindows()

    # --- documento ---------------------------------------------------------------------------

    @property
    def editor(self) -> Editor:
        return self._editor

    @property
    def is_empty(self) -> bool:
        """Janela virgem, que pode ser reaproveitada para abrir um arquivo."""
        return self.path is None and not self._editor.history.is_dirty

    def _attach(self, documento: Document, caminho: Path | None) -> None:
        self.path = caminho
        self._editor = Editor(documento)
        self._editor.history.subscribe(self._history_changed)
        self.diagram_scene.set_document(documento)
        self.view.set_editor(self._editor)
        self.view.set_tool(SELECT)
        self._history_changed()

    def load(self, caminho: Path) -> bool:
        """Abre o arquivo nesta janela. Em caso de erro mostra a mensagem e devolve `False`."""
        try:
            documento = io.load(caminho)
        except (ArquivoInvalidoError, OSError) as erro:
            QMessageBox.critical(
                self, "Não foi possível abrir o arquivo", f"{caminho.name}\n\n{erro}"
            )
            return False
        self._attach(documento, caminho)
        self.view.zoom_actual()
        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())
        return True

    def save(self) -> bool:
        """Grava no arquivo atual (ou pergunta onde). Devolve `False` se não gravou."""
        if self.path is None:
            return self.save_as()
        return self._write(self.path)

    def save_as(self) -> bool:
        inicial = str(self.path) if self.path else f"{UNTITLED}.xml"
        nome, _ = QFileDialog.getSaveFileName(
            self, "Salvar modelo", inicial, "Modelos do TerraER (*.xml)"
        )
        if not nome:
            return False
        caminho = Path(nome)
        if caminho.suffix.lower() != ".xml":
            caminho = caminho.with_name(caminho.name + ".xml")
        return self._write(caminho)

    def _write(self, caminho: Path) -> bool:
        try:
            io.save(self._editor.document, caminho)
        except OSError as erro:
            QMessageBox.critical(
                self, "Não foi possível salvar o arquivo", f"{caminho.name}\n\n{erro}"
            )
            return False
        self.path = caminho.resolve()
        self._editor.history.mark_clean()
        self.statusBar().showMessage(f"Salvo em {caminho}", 4000)
        return True

    # --- edição ------------------------------------------------------------------------------

    def _undo(self) -> None:
        self._editor.history.undo()

    def _redo(self) -> None:
        self._editor.history.redo()

    def _delete(self) -> None:
        self._editor.delete(self.diagram_scene.selected_figures())

    def _history_changed(self) -> None:
        historico = self._editor.history
        self.action_undo.setEnabled(historico.can_undo)
        self.action_redo.setEnabled(historico.can_redo)
        self.action_undo.setText(f"&Desfazer {historico.undo_label}".rstrip())
        self.action_redo.setText(f"&Refazer {historico.redo_label}".rstrip())
        self._update_title()

    def _update_title(self) -> None:
        nome = self.path.name if self.path else UNTITLED
        self.setWindowTitle(f"{nome}[*] - {TITLE}")
        self.setWindowModified(self._editor.history.is_dirty)

    def _show_zoom(self, zoom: float) -> None:
        self._zoom_label.setText(f"{round(zoom * 100)}%")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._editor.history.is_dirty and not self._confirm_discard():
            event.ignore()
            return
        self.closed.emit(self)
        super().closeEvent(event)

    def _confirm_discard(self) -> bool:
        """Pergunta o que fazer com as alterações. `False` cancela o fechamento."""
        botoes = QMessageBox.StandardButton
        resposta = QMessageBox.question(
            self,
            TITLE,
            f"Salvar as alterações em {self.path.name if self.path else UNTITLED}?",
            botoes.Save | botoes.Discard | botoes.Cancel,
            botoes.Save,
        )
        if resposta == botoes.Save:
            return self.save()
        return resposta == botoes.Discard
