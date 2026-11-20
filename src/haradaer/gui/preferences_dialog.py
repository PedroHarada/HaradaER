"""Configurações › Preferências (Ctrl+,): o que muda raramente e precisa de explicação.

Pelo guia da Apple (Settings), a janela guarda só opções gerais e mudadas raramente: o idioma,
as atualizações e o Restaurar padrões. O que se usa durante o trabalho fica nos menus
(Configurações e Exibir), como no menu Configurações do KDE. Uma página só, sem abas.

Cada caixa é a mesma ação da janela (`DocumentWindow`), ligada nos dois sentidos, e vale na
hora; só o idioma vale ao reabrir, como sempre (RNF-06).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import haradaer
from haradaer.gui.settings import saved_language
from haradaer.gui.theme import LIGHT
from haradaer.i18n import LANGUAGES, _, language

if TYPE_CHECKING:
    from haradaer.gui.window import DocumentWindow


def _caixa(acao: QAction, texto: str) -> QCheckBox:
    """Uma caixa de marcar presa a uma ação marcável, nos dois sentidos."""
    caixa = QCheckBox(texto)
    caixa.setChecked(acao.isChecked())
    caixa.toggled.connect(acao.setChecked)
    acao.toggled.connect(caixa.setChecked)
    return caixa


def _grupo(titulo: str, *widgets: QWidget) -> QGroupBox:
    grupo = QGroupBox(titulo)
    layout = QVBoxLayout(grupo)
    for widget in widgets:
        layout.addWidget(widget)
    return grupo


def _dica(texto: str) -> QLabel:
    rotulo = QLabel(texto)
    rotulo.setWordWrap(True)
    rotulo.setEnabled(False)  # cinza, como texto de apoio
    return rotulo


def _linha(*widgets: QWidget) -> QWidget:
    linha = QWidget()
    layout = QHBoxLayout(linha)
    layout.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch(1)
    return linha


class PreferencesDialog(QDialog):
    def __init__(self, janela: DocumentWindow) -> None:
        super().__init__(janela)
        self._janela = janela
        self.setWindowTitle(_("Preferências"))

        self.language_box = QComboBox()
        for codigo, nome in LANGUAGES.items():
            self.language_box.addItem(nome, codigo)  # cada idioma com o próprio nome
        self.language_box.setCurrentIndex(
            self.language_box.findData(saved_language() or language())
        )
        self.language_box.activated.connect(
            lambda i: janela._language_chosen(self.language_box.itemData(i))
        )

        self.auto_updates_box = _caixa(janela.auto_updates_action, _("Verificar ao a&brir"))
        self.check_now_button = QPushButton(_("Verificar &agora"))
        self.check_now_button.clicked.connect(janela.check_updates_action.trigger)

        self.restore_button = QPushButton(_("&Restaurar todos os padrões"))
        self.restore_button.clicked.connect(self._ask_restore)
        # A confirmação fica na própria janela, sem outra caixa por cima
        self.confirm_label = QLabel(
            _(
                "Voltar ao padrão o tema, as barras, a grade, os painéis, a verificação, a"
                " Edição rápida e as atualizações? O idioma e os arquivos recentes não mudam."
            )
        )
        self.confirm_label.setWordWrap(True)
        self.confirm_button = QPushButton(_("Restaurar"))
        self.confirm_button.clicked.connect(self.restore_defaults)
        self.cancel_button = QPushButton(_("Cancelar"))
        self.cancel_button.clicked.connect(self._hide_confirm)
        self.confirm_row = QWidget()
        linha = QHBoxLayout(self.confirm_row)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.addWidget(self.confirm_label, 1)
        linha.addWidget(self.confirm_button)
        linha.addWidget(self.cancel_button)
        self.confirm_row.hide()

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        botoes.addButton(self.restore_button, QDialogButtonBox.ButtonRole.ResetRole)
        layout = QVBoxLayout(self)
        layout.addWidget(
            _grupo(
                _("Idioma"),
                self.language_box,
                _dica(_("Vale quando o HaradaER for fechado e aberto de novo.")),
            )
        )
        layout.addWidget(
            _grupo(
                _("Atualizações"),
                self.auto_updates_box,
                _dica(_("No máximo uma vez por dia, no GitHub.")),
                _linha(
                    self.check_now_button,
                    _dica(_("Você tem a {atual}.").format(atual=haradaer.__version__)),
                ),
            )
        )
        layout.addStretch(1)
        layout.addWidget(self.confirm_row)
        layout.addWidget(botoes)
        self.resize(460, 300)

    def _ask_restore(self) -> None:
        self.confirm_row.show()
        self.cancel_button.setFocus()

    def _hide_confirm(self) -> None:
        self.confirm_row.hide()

    def restore_defaults(self) -> None:
        """Tema claro, faixa e barra de status à vista, grade desligada, painéis à vista,
        verificação e avisos ligados, Edição rápida desligada e verificação de atualizações ao
        abrir. Idioma e recentes ficam."""
        janela = self._janela
        janela.theme_actions[LIGHT.name].trigger()
        janela.action_show_tools.setChecked(True)
        janela.action_show_status.setChecked(True)
        janela.action_grid.setChecked(False)
        for dock in (janela.inspector_dock, janela.properties_dock, janela.messages_dock):
            dock.toggleViewAction().setChecked(True)
        janela.action_validate.setChecked(True)
        janela.action_structure.setChecked(True)
        janela.action_quick_edit.setChecked(False)
        janela.auto_updates_action.setChecked(True)
        self._hide_confirm()
