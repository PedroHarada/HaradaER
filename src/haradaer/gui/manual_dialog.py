"""Ajuda › Manual do HaradaER (F1): o manual instalado junto com o programa, numa janela.

Como no KDE (o manual do aplicativo abre no sistema de ajuda, a partir do F1) e na Apple (a
ajuda abre num visualizador, não num site), mas com o mesmo visualizador nos três sistemas: o
Markdown de `docs/` vira HTML com o markdown-it-py e aparece num `QTextBrowser`. Funciona sem
internet e corresponde à versão instalada. Busca (Ctrl+F) e tamanho do texto (Ctrl++, Ctrl+-,
Ctrl+0) ficam na própria janela; links para seções pulam para elas, links para os manuais nos
outros idiomas trocam o manual, e os da web abrem no navegador.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

from markdown_it import MarkdownIt
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QKeySequence, QPalette, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import haradaer
from haradaer.i18n import _

MANUAL_FILES = {
    "pt": "PRIMEIROS-PASSOS.md",
    "en": "GETTING-STARTED.md",
    "es": "PRIMEROS-PASOS.md",
}


def manual_path(idioma: str) -> Path | None:
    """O manual do idioma: no pacote (`haradaer/manuais`, posto pelo PyInstaller) ou, rodando
    do código, em `docs/`. `None` se não estiver em nenhum dos dois."""
    nome = MANUAL_FILES.get(idioma, MANUAL_FILES["pt"])
    pacote = Path(haradaer.__file__).parent
    for pasta in (pacote / "manuais", pacote.parents[1] / "docs"):
        if (pasta / nome).is_file():
            return pasta / nome
    return None


def heading_id(texto: str) -> str:
    """O identificador que o GitHub dá a um título ("Depois de abrir" -> "depois-de-abrir"), o
    mesmo dos links internos do manual."""
    texto = re.sub(r"<[^>]+>", "", texto).strip().lower()
    texto = re.sub(r"[^\w\- ]", "", texto)
    return texto.replace(" ", "-")


def manual_html(markdown: str) -> str:
    """O manual em HTML: tabelas ligadas, sem os comentários e sem a linha que manda ao README
    (que só existe no repositório), e com uma âncora em cada título."""
    linhas = [linha for linha in markdown.splitlines() if "README.md" not in linha]
    texto = re.sub(r"<!--.*?-->", "", "\n".join(linhas), flags=re.DOTALL)
    html = MarkdownIt("commonmark").enable("table").render(texto)

    def ancora(achado: re.Match) -> str:
        nivel, conteudo = achado.group(1), achado.group(2)
        return f'<h{nivel}><a name="{escape(heading_id(conteudo))}"></a>{conteudo}</h{nivel}>'

    return re.sub(r"<h([1-6])>(.*?)</h\1>", ancora, html)


class _FindField(QLineEdit):
    """Campo da busca: Enter vai ao próximo resultado, Shift+Enter ao anterior."""

    def __init__(self, dialogo: ManualDialog) -> None:
        super().__init__()
        self._dialogo = dialogo

    def keyPressEvent(self, evento) -> None:  # noqa: N802 (nome do Qt)
        if evento.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if evento.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._dialogo.find_previous()
            else:
                self._dialogo.find_next()
            return
        super().keyPressEvent(evento)


class ManualDialog(QDialog):
    """A busca segue as barras de busca do KDE (Kate, Okular): procura enquanto se digita,
    destaca todos os resultados, diz "3 de 12" e anda com Próximo e Anterior (Enter e F3,
    Shift+Enter e Shift+F3)."""

    def __init__(self, parent: QWidget, idioma: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Manual do HaradaER"))
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self._link)
        self.find_field = _FindField(self)
        self.find_field.setPlaceholderText(_("Buscar no manual…"))
        self.find_field.textChanged.connect(self._search)
        self.previous_button = QPushButton(_("&Anterior"))
        self.previous_button.clicked.connect(self.find_previous)
        self.next_button = QPushButton(_("Pró&ximo"))
        self.next_button.clicked.connect(self.find_next)
        self.not_found = QLabel()  # "3 de 12" ou "Nada encontrado"
        busca = QHBoxLayout()
        busca.addWidget(self.find_field, 1)
        busca.addWidget(self.previous_button)
        busca.addWidget(self.next_button)
        busca.addWidget(self.not_found)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        # Enter na busca anda nos resultados: sem botão padrão, o diálogo não fecha com ele
        for botao in [*botoes.buttons(), self.previous_button, self.next_button]:
            botao.setAutoDefault(False)
            botao.setDefault(False)
        layout = QVBoxLayout(self)
        layout.addLayout(busca)
        layout.addWidget(self.browser, 1)
        layout.addWidget(botoes)
        for tecla, funcao in (
            (QKeySequence.StandardKey.Find, self._focus_find),
            (QKeySequence.StandardKey.FindNext, self.find_next),
            (QKeySequence.StandardKey.FindPrevious, self.find_previous),
            (QKeySequence.StandardKey.ZoomIn, lambda: self.browser.zoomIn(2)),
            (QKeySequence.StandardKey.ZoomOut, lambda: self.browser.zoomOut(2)),
            ("Ctrl+0", self._zoom_reset),
        ):
            QShortcut(QKeySequence(tecla), self, funcao)
        self._base_font = self.browser.font()
        self._matches: list[QTextCursor] = []
        self._current = -1
        self.resize(760, 640)
        self.show_language(idioma)

    def show_language(self, idioma: str) -> bool:
        caminho = manual_path(idioma)
        if caminho is None:
            return False
        self.browser.setHtml(manual_html(caminho.read_text(encoding="utf-8")))
        self._search()
        return True

    def _link(self, url: QUrl) -> None:
        if url.scheme() in ("http", "https", "mailto"):
            QDesktopServices.openUrl(url)
            return
        nome = Path(url.path()).name
        outro = next((c for c, n in MANUAL_FILES.items() if n == nome), None)
        if outro is not None:
            self.show_language(outro)
        if url.fragment():
            self.browser.scrollToAnchor(url.fragment())

    def _focus_find(self) -> None:
        self.find_field.setFocus()
        self.find_field.selectAll()

    def _search(self) -> None:
        """Acha todas as ocorrências (sem diferenciar maiúsculas), destaca e vai à primeira."""
        texto = self.find_field.text()
        documento = self.browser.document()
        self._matches = []
        if texto:
            cursor = documento.find(texto, 0)
            while not cursor.isNull():
                self._matches.append(cursor)
                cursor = documento.find(texto, cursor)
        self._current = -1
        self._highlight()
        if self._matches:
            self._go(0)
        else:
            self.browser.setTextCursor(QTextCursor(documento))
            self.not_found.setText(_("Nada encontrado") if texto else "")
        tem = len(self._matches) > 0
        self.previous_button.setEnabled(tem)
        self.next_button.setEnabled(tem)

    def _highlight(self) -> None:
        """Todos os resultados em amarelo e o atual na cor de seleção, como no Kate; aparece
        mesmo com o cursor no campo de busca, nos dois temas."""
        paleta = self.palette()
        clara = QColor(255, 200, 0, 110)
        destaques = []
        for indice, achado in enumerate(self._matches):
            destaque = QTextEdit.ExtraSelection()
            destaque.cursor = achado
            if indice == self._current:
                destaque.format.setBackground(paleta.color(QPalette.ColorRole.Highlight))
                destaque.format.setForeground(paleta.color(QPalette.ColorRole.HighlightedText))
            else:
                destaque.format.setBackground(clara)
            destaques.append(destaque)
        self.browser.setExtraSelections(destaques)

    def _go(self, indice: int) -> None:
        self._current = indice % len(self._matches)
        # o cursor vai ao resultado sem selecionar: a seleção do Qt cobriria o destaque
        cursor = QTextCursor(self._matches[self._current])
        cursor.setPosition(cursor.selectionStart())
        self.browser.setTextCursor(cursor)
        self.browser.ensureCursorVisible()
        self._highlight()
        self.not_found.setText(
            _("{atual} de {total}").format(atual=self._current + 1, total=len(self._matches))
        )

    def find_next(self) -> bool:
        """O próximo resultado; depois do último, volta ao primeiro."""
        if not self._matches:
            return False
        self._go(self._current + 1)
        return True

    def find_previous(self) -> bool:
        """O resultado anterior; antes do primeiro, vai ao último."""
        if not self._matches:
            return False
        self._go(self._current - 1)
        return True

    def _zoom_reset(self) -> None:
        self.browser.setFont(self._base_font)
