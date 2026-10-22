"""Painel Mensagens (RNF-09): os erros de conexão e os avisos de estrutura, em lista.

Cada linha diz o tipo (erro em vermelho, aviso em laranja), o elemento e o problema. Escolher
uma linha seleciona o elemento e o traz para o centro do desenho.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from haradaer.core.rules import Issue
from haradaer.gui.inspector import display_name
from haradaer.gui.scene.items import PROBLEM_COLOR, WARNING_COLOR
from haradaer.gui.verification import is_warning, message_text, name_of
from haradaer.i18n import N_, _

ERROR_LABEL = N_("Erro")
WARNING_LABEL = N_("Aviso")
EMPTY_TEXT = N_("Nenhum problema no modelo.")
OFF_TEXT = N_("A verificação está desligada (Exibir › Verificar modelo).")


class MessagesPanel(QWidget):
    locate_requested = Signal(object)  # figura a mostrar no desenho

    def __init__(self) -> None:
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([_("Tipo"), _("Elemento"), _("Mensagem")])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemActivated.connect(self._escolhido)
        self.tree.itemClicked.connect(self._escolhido)
        self.status = QLabel()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.tree)
        layout.addWidget(self.status)
        self.show_messages([], [])

    def show_messages(self, problemas: list[Issue], avisos: list[Issue], ligada=True) -> None:
        self.tree.clear()
        for issue in [*problemas, *avisos]:
            aviso = is_warning(issue)
            linha = QTreeWidgetItem(
                [
                    _(WARNING_LABEL) if aviso else _(ERROR_LABEL),
                    f"{display_name(issue.figure)} ({name_of(issue.figure.tag)})",
                    message_text(issue),
                ]
            )
            cor = WARNING_COLOR if aviso else QColor(*PROBLEM_COLOR)
            linha.setForeground(0, QBrush(cor))
            linha.setToolTip(2, message_text(issue))
            linha.setData(0, Qt.ItemDataRole.UserRole, issue.figure)
            self.tree.addTopLevelItem(linha)
        for coluna in range(2):
            self.tree.resizeColumnToContents(coluna)
        if not ligada:
            self.status.setText(_(OFF_TEXT))
        elif not problemas and not avisos:
            self.status.setText(_(EMPTY_TEXT))
        else:
            self.status.setText(
                _("{erros} erro(s), {avisos} aviso(s)").format(
                    erros=len(problemas), avisos=len(avisos)
                )
            )

    def rows(self) -> list[tuple[str, str, str]]:
        return [
            tuple(self.tree.topLevelItem(i).text(c) for c in range(3))
            for i in range(self.tree.topLevelItemCount())
        ]

    def _escolhido(self, linha: QTreeWidgetItem, _coluna: int = 0) -> None:
        figura = linha.data(0, Qt.ItemDataRole.UserRole)
        if figura is not None:
            self.locate_requested.emit(figura)
