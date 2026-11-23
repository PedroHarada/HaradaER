"""Aplicação: um processo, uma janela por documento."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QDateTime, QLibraryInfo, QLocale, QObject, QRectF, QTranslator
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import haradaer
from haradaer import selfupdate
from haradaer.gui.recovery import Leftover, leftovers
from haradaer.gui.settings import RecentFiles, saved_language
from haradaer.gui.theme import apply_theme, saved_theme
from haradaer.gui.theme import manager as theme_manager
from haradaer.gui.window import DocumentWindow
from haradaer.i18n import LOCALES, _, language, language_for_locales, set_language

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

    def restore(self, sobras: list[Leftover]) -> None:
        """Abre cada cópia de recuperação numa janela vazia ou nova."""
        for sobra in sobras:
            vazia = next((j for j in self.windows if j.is_empty), None)
            janela = vazia or self.new_window()
            if not janela.restore(sobra) and vazia is None:
                janela.close()

    def ask_and_open(self, pai: DocumentWindow) -> None:
        arquivos, _filtro = QFileDialog.getOpenFileNames(
            pai,
            _("Abrir modelo"),
            str(pai.path.parent) if pai.path else "",
            _("Modelos do TerraER (*.xml);;Todos os arquivos (*)"),
        )
        for arquivo in arquivos:
            self.open_path(Path(arquivo))


def recovery_question(sobras: list[Leftover]) -> str:
    """Pergunta se recupera as cópias que sobraram. Devolve "recuperar", "descartar" ou
    "depois" (as cópias ficam para a próxima abertura)."""
    linhas = [
        f"• {s.original.name if s.original else _('Sem título')}"
        f" ({s.original.parent if s.original else _('nunca salvo')}),"
        f" {QLocale().toString(QDateTime(s.when), QLocale.FormatType.ShortFormat)}"
        for s in sobras
    ]
    caixa = QMessageBox()
    caixa.setWindowTitle(_("Recuperar alterações"))
    caixa.setText(
        _("O HaradaER fechou sem salvar estes modelos. Recuperar as alterações?")
        + "\n\n"
        + "\n".join(linhas)
    )
    caixa.setInformativeText(
        _("Os modelos abrem como não salvos; os arquivos originais só mudam quando você salvar.")
    )
    recuperar = caixa.addButton(_("Recuperar"), QMessageBox.ButtonRole.AcceptRole)
    descartar = caixa.addButton(_("Descartar"), QMessageBox.ButtonRole.DestructiveRole)
    depois = caixa.addButton(_("Decidir depois"), QMessageBox.ButtonRole.RejectRole)
    caixa.setDefaultButton(recuperar)
    caixa.setEscapeButton(depois)  # Esc nunca apaga nada
    caixa.exec()
    clicado = caixa.clickedButton()
    if clicado is recuperar:
        return "recuperar"
    if clicado is descartar:
        return "descartar"
    return "depois"


def offer_recovery(gerenciador: WindowManager) -> None:
    """Na abertura, oferece as cópias de recuperação que sobraram de um fechamento repentino."""
    sobras = leftovers()
    if not sobras:
        return
    resposta = recovery_question(sobras)
    if resposta == "recuperar":
        gerenciador.restore(sobras)
    elif resposta == "descartar":
        for sobra in sobras:
            sobra.discard()


QT_TRANSLATIONS = {"pt": "qtbase_pt_BR", "es": "qtbase_es"}


def choose_language() -> str:
    """O idioma escolhido em Configurações › Preferências ou, na primeira vez, o do sistema
    (RNF-06).

    Vale até fechar o programa: trocar o idioma só tem efeito ao reabrir.
    """
    escolhido = saved_language()
    if escolhido is None:
        # A lista de idiomas da interface do sistema, e não o formato regional: respeita o
        # idioma escolhido para o app no macOS (Apple) e a variável LANGUAGE no Linux
        sistema = QLocale.system()
        escolhido = language_for_locales(sistema.uiLanguages() or [sistema.name()])
    set_language(escolhido)
    # O idioma também vai para o Qt, para os leitores de tela saberem em que língua ler
    # (WCAG2ICT 3.1.1, idioma do software determinado por programa)
    QLocale.setDefault(QLocale(LOCALES[language()]))
    return language()


def install_translator(app: QApplication) -> bool:
    """Traduz os textos do próprio Qt (botões Salvar/Descartar/Cancelar, diálogos de arquivo).

    Em inglês o Qt já fala a língua dele.
    """
    arquivo = QT_TRANSLATIONS.get(language())
    if arquivo is None:
        return False
    tradutor = QTranslator(app)
    pasta = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not tradutor.load(arquivo, pasta):
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
    offer_recovery(gerenciador)
    selfupdate.cleanup_old(selfupdate.install_target())  # o .old de uma atualização anterior
    gerenciador.windows[0].update_checker.check_if_due()  # no máximo uma vez por dia (RF-22)
    return app.exec()
