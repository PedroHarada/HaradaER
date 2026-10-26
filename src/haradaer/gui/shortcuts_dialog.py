"""Ajuda › Atalhos do teclado: a lista sai das ações dos menus, então um atalho novo entra nela
sozinho e segue o idioma da interface. Só a parte da Edição rápida e a do mouse são escritas.

A mesma lista vai para os manuais (`docs/PRIMEIROS-PASSOS.md` e `docs/GETTING-STARTED.md`),
entre os marcadores `MARK_BEGIN` e `MARK_END`. Para atualizá-los:
`python -m haradaer.gui.shortcuts_dialog`; `tests/gui/test_atalhos_manual.py` falha se ficarem
diferentes do programa.
"""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QLineEdit,
    QMenuBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from haradaer.gui.shortcuts import FAMILIES
from haradaer.i18n import N_, _

MOUSE: list[tuple[str, str]] = [
    (N_("Zoom"), N_("Pinça, ou Ctrl + roda do mouse")),
    (N_("Rolar o desenho"), N_("Dois dedos, ou a roda do mouse")),
    (N_("Mover o desenho"), N_("Botão do meio e arrastar")),
    (N_("Manter a ferramenta depois de criar"), N_("Shift + clique")),
    (N_("Editar o nome"), N_("Duplo clique no elemento")),
    (N_("Novo vértice na conexão"), N_("Duplo clique na linha")),
    (N_("Tirar um vértice"), N_("Duplo clique no vértice")),
]


def _plain(texto: str) -> str:
    return texto.replace("&", "").replace("...", "").replace("…", "").strip()


def menu_shortcuts(barra: QMenuBar, *, nativo: bool = True) -> list[tuple[str, str, str]]:
    """(menu, ação, atalho) de cada ação com atalho, na ordem dos menus."""
    linhas = []
    for menu_acao in barra.actions():
        menu = menu_acao.menu()
        if menu is None:
            continue
        pilha = list(menu.actions())
        while pilha:
            acao: QAction = pilha.pop(0)
            if acao.menu() is not None:
                pilha[0:0] = acao.menu().actions()
                continue
            formato = QKeySequence.SequenceFormat
            atalho = acao.shortcut().toString(
                formato.NativeText if nativo else formato.PortableText
            )
            if atalho:
                linhas.append((_plain(menu_acao.text()), _plain(acao.text()), atalho))
    return linhas


def quick_edit_rows(nome_da_ferramenta) -> list[tuple[str, str]]:
    linhas = []
    for tecla, ferramentas in FAMILIES:
        nomes = " → ".join(nome_da_ferramenta(t) for t in ferramentas)
        linhas.append((nomes, tecla))
    linhas += [
        (_("Voltar uma posição no ciclo"), _("Shift + letra")),
        (_("Trocar o tipo do elemento selecionado (com Selecionar)"), _("Letra da família")),
        (_("Criar onde está o mouse"), _("Espaço")),
        (_("Voltar para Selecionar"), "Esc"),
    ]
    return linhas


def all_rows(
    barra: QMenuBar, nome_da_ferramenta, *, nativo: bool = True
) -> list[tuple[str, str, str]]:
    """(grupo, ação, atalho): os menus, a Edição rápida e o mouse. Sem `nativo`, as teclas saem
    iguais em qualquer sistema (Ctrl, e não ⌘), como nos manuais."""
    linhas: list[tuple[str, str, str]] = list(menu_shortcuts(barra, nativo=nativo))
    grupo = _("Edição rápida (Editar › Edição rápida)")
    linhas += [(grupo, a, t) for a, t in quick_edit_rows(nome_da_ferramenta)]
    linhas += [(_("Mouse e gestos"), _(a), _(t)) for a, t in MOUSE]
    return linhas


MARK_BEGIN = "<!-- atalhos: início (gerado por python -m haradaer.gui.shortcuts_dialog) -->"
MARK_END = "<!-- atalhos: fim -->"


def markdown(linhas: list[tuple[str, str, str]]) -> str:
    """A lista como tabelas Markdown, uma por grupo."""
    partes: list[str] = []
    ultimo = None
    for grupo, acao, atalho in linhas:
        if grupo != ultimo:
            if ultimo is not None:
                partes.append("")
            partes += [f"**{grupo}**", "", f"| {_('Ação')} | {_('Atalho')} |", "|---|---|"]
            ultimo = grupo
        teclas = " ".join(f"`{t}`" for t in atalho.split(", ")) if atalho else ""
        partes.append(f"| {acao.replace('|', '\\|')} | {teclas} |")
    return "\n".join(partes) + "\n"


def replace_block(texto: str, bloco: str) -> str:
    """O manual com o bloco entre os marcadores trocado."""
    inicio = texto.index(MARK_BEGIN) + len(MARK_BEGIN)
    fim = texto.index(MARK_END)
    return texto[:inicio] + "\n\n" + bloco + "\n" + texto[fim:]


MANUALS = {"pt": "docs/PRIMEIROS-PASSOS.md", "en": "docs/GETTING-STARTED.md"}


def manual_block(idioma: str) -> str:
    """A tabela de atalhos no idioma dado, montada de uma janela nova (precisa de QApplication)."""
    from haradaer.gui.window import DocumentWindow  # a janela importa este módulo
    from haradaer.i18n import language, set_language

    antes = language()
    set_language(idioma)
    try:
        janela = DocumentWindow()
        bloco = markdown(
            all_rows(janela.menuBar(), lambda t: janela._tool_actions[t].statusTip(), nativo=False)
        )
        janela.deleteLater()
        return bloco
    finally:
        set_language(antes)


class ShortcutsDialog(QDialog):
    def __init__(self, parent: QWidget, barra: QMenuBar, nome_da_ferramenta) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Atalhos do teclado"))
        self.resize(560, 600)
        self.search = QLineEdit()
        self.search.setPlaceholderText(_("Buscar atalho…"))
        self.search.setClearButtonEnabled(True)
        self.table = QTableWidget(0, 2)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setShowGrid(False)
        cabecalho = self.table.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.table)

        self._rows = all_rows(barra, nome_da_ferramenta)
        self.search.textChanged.connect(self._fill)
        self._fill("")

    def _fill(self, busca: str) -> None:
        busca = busca.casefold()
        self.table.setRowCount(0)
        ultimo = None
        for grupo, acao, atalho in self._rows:
            if busca and busca not in f"{grupo} {acao} {atalho}".casefold():
                continue
            if grupo != ultimo:
                self._add(grupo, "", titulo=True)
                ultimo = grupo
            self._add(acao, atalho)

    def _add(self, texto: str, atalho: str, *, titulo: bool = False) -> None:
        linha = self.table.rowCount()
        self.table.insertRow(linha)
        item = QTableWidgetItem(texto)
        if titulo:
            fonte = item.font()
            fonte.setBold(True)
            item.setFont(fonte)
        self.table.setItem(linha, 0, item)
        self.table.setItem(linha, 1, QTableWidgetItem(atalho))

    def visible_rows(self) -> list[tuple[str, str]]:
        return [
            (self.table.item(i, 0).text(), self.table.item(i, 1).text())
            for i in range(self.table.rowCount())
        ]


if __name__ == "__main__":
    import os
    from pathlib import Path

    from PySide6.QtWidgets import QApplication

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication([])
    for idioma, caminho in MANUALS.items():
        arquivo = Path(caminho)
        arquivo.write_text(
            replace_block(arquivo.read_text(encoding="utf-8"), manual_block(idioma)),
            encoding="utf-8",
        )
        print(caminho)
