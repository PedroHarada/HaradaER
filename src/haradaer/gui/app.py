"""Aplicação: um processo, uma janela por documento."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QObject, QRectF, QTranslator
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QFileDialog

import haradaer
from haradaer.gui.settings import RecentFiles, saved_language
from haradaer.gui.theme import apply_theme, saved_theme
from haradaer.gui.theme import manager as theme_manager
from haradaer.gui.window import DocumentWindow
from haradaer.i18n import _, language, language_for_locale, set_language

ICON_PATH = Path(haradaer.__file__).parent / "resources" / "haradaer.svg"
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def app_icon() -> QIcon:
    """O ícone das janelas (barra de título, barra de tarefas, Alt+Tab), desenhado do SVG em
    vários tamanhos. Vazio se o arquivo faltar: o programa abre do mesmo jeito."""
    renderizador = QSvgRenderer(str(ICON_PATH))
    icone = QIcon()
    if not renderizador.isValid():
        return icone
    for lado in ICON_SIZES:
        imagem = QImage(lado, lado, QImage.Format.Format_ARGB32)
        imagem.fill(0)
        pintor = QPainter(imagem)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderizador.render(pintor, QRectF(0, 0, lado, lado))
        pintor.end()
        icone.addPixmap(QPixmap.fromImage(imagem))
    return icone


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
        arquivos, _filtro = QFileDialog.getOpenFileNames(
            pai,
            _("Abrir modelo"),
            str(pai.path.parent) if pai.path else "",
            _("Modelos do TerraER (*.xml);;Todos os arquivos (*)"),
        )
        for arquivo in arquivos:
            self.open_path(Path(arquivo))


def choose_language() -> str:
    """O idioma escolhido em Exibir › Idioma ou, na primeira vez, o do sistema (RNF-06).

    Vale até fechar o programa: trocar no menu só tem efeito ao reabrir.
    """
    set_language(saved_language() or language_for_locale(QLocale.system().name()))
    return language()


def install_translator(app: QApplication) -> bool:
    """Traduz os textos do próprio Qt (botões Salvar/Descartar/Cancelar, diálogos de arquivo).

    Só em português: em inglês o Qt já fala a língua dele.
    """
    if language() != "pt":
        return False
    tradutor = QTranslator(app)
    pasta = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not tradutor.load("qtbase_pt_BR", pasta):
        return False
    return app.installTranslator(tradutor)


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = list(sys.argv if argv is None else argv)
    app = QApplication(argumentos)
    app.setApplicationName("HaradaER")
    app.setDesktopFileName("io.github.pedroharada.haradaer")  # liga a janela ao atalho e ícone
    app.setWindowIcon(app_icon())
    choose_language()
    install_translator(app)
    apply_theme(saved_theme(), save=False)
    theme_manager().watch_system()  # segue a troca de tema do sistema (qt6ct)
    gerenciador = WindowManager()
    caminhos = [Path(a) for a in argumentos[1:]]
    if not caminhos:
        gerenciador.new_window()
    for caminho in caminhos:
        gerenciador.open_path(caminho)
    if not gerenciador.windows:
        return 1
    return app.exec()
