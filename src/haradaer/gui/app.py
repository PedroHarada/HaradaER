"""Aplicação: um processo, uma janela por documento."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QObject, QTranslator
from PySide6.QtWidgets import QApplication, QFileDialog

from haradaer.gui.settings import RecentFiles
from haradaer.gui.window import DocumentWindow


class WindowManager(QObject):
    """Guarda as janelas abertas e decide em qual abrir cada arquivo."""

    def __init__(self) -> None:
        super().__init__()
        self.windows: list[DocumentWindow] = []
        self.recent = RecentFiles()  # a única coisa compartilhada entre as janelas

    def new_window(self) -> DocumentWindow:
        janela = DocumentWindow(self.recent)
        janela.open_path_requested.connect(self.open_path)
        janela.closed.connect(self._window_closed)
        janela.open_requested.connect(lambda j=janela: self.ask_and_open(j))
        janela.new_requested.connect(self.new_window)
        self.windows.append(janela)
        janela.show()
        return janela

    def _window_closed(self, janela: DocumentWindow) -> None:
        if janela in self.windows:
            self.windows.remove(janela)

    def open_path(self, caminho: Path) -> DocumentWindow | None:
        """Abre o arquivo: traz a janela dele se já estiver aberto, ou usa uma janela vazia."""
        caminho = caminho.resolve()
        for janela in self.windows:
            if janela.path == caminho:
                janela.raise_()
                janela.activateWindow()
                return janela
        vazia = next((j for j in self.windows if j.is_empty), None)
        janela = vazia or self.new_window()
        if not janela.load(caminho):
            if vazia is None:
                janela.close()
            return None
        janela.raise_()
        return janela

    def ask_and_open(self, pai: DocumentWindow) -> None:
        arquivos, _ = QFileDialog.getOpenFileNames(
            pai,
            "Abrir modelo",
            str(pai.path.parent) if pai.path else "",
            "Modelos do TerraER (*.xml);;Todos os arquivos (*)",
        )
        for arquivo in arquivos:
            self.open_path(Path(arquivo))


def install_translator(app: QApplication) -> bool:
    """Traduz os textos do próprio Qt (botões Salvar/Descartar/Cancelar, diálogos de arquivo)."""
    tradutor = QTranslator(app)
    pasta = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not tradutor.load("qtbase_pt_BR", pasta):
        return False
    return app.installTranslator(tradutor)


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = list(sys.argv if argv is None else argv)
    app = QApplication(argumentos)
    app.setApplicationName("HaradaER")
    install_translator(app)
    gerenciador = WindowManager()
    caminhos = [Path(a) for a in argumentos[1:]]
    if not caminhos:
        gerenciador.new_window()
    for caminho in caminhos:
        gerenciador.open_path(caminho)
    if not gerenciador.windows:
        return 1
    return app.exec()
