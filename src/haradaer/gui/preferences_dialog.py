"""Editar › Preferências (Ctrl+,): as configurações do programa numa janela só, em abas.

Cada opção é a mesma ação da janela (`DocumentWindow`), ligada nos dois sentidos: mudar aqui
vale na hora, como clicar no menu antes; o atalho de teclado da ação continua mudando a opção.
Só o idioma vale ao reabrir, como sempre (RNF-06).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import haradaer
from haradaer.gui.settings import saved_language
from haradaer.gui.theme import available_themes
from haradaer.i18n import LANGUAGES, _, language

if TYPE_CHECKING:
    from haradaer.gui.window import DocumentWindow


def _caixa(acao: QAction, texto: str, dica: str = "") -> QCheckBox:
    """Uma caixa de marcar presa a uma ação marcável, nos dois sentidos."""
    caixa = QCheckBox(texto)
    caixa.setChecked(acao.isChecked())
    caixa.toggled.connect(acao.setChecked)
    acao.toggled.connect(caixa.setChecked)
    if dica:
        caixa.setToolTip(dica)
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


def _atalho(acao: QAction) -> str:
    """O atalho que liga e desliga a opção, que não está mais em nenhum menu."""
    return _("Atalho: {tecla}").format(
        tecla=acao.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
    )


def _aba(*grupos: QWidget) -> QWidget:
    pagina = QWidget()
    layout = QVBoxLayout(pagina)
    for grupo in grupos:
        layout.addWidget(grupo)
    layout.addStretch(1)
    return pagina


class PreferencesDialog(QDialog):
    def __init__(self, janela: DocumentWindow) -> None:
        super().__init__(janela)
        self.setWindowTitle(_("Preferências"))
        self.tabs = QTabWidget()
        self.tabs.addTab(self._aparencia(janela), _("Aparência"))
        self.tabs.addTab(self._verificacao(janela), _("Verificação"))
        self.tabs.addTab(self._edicao(janela), _("Edição"))
        self.tabs.addTab(self._arquivos(janela), _("Arquivos"))
        self.tabs.addTab(self._atualizacoes(janela), _("Atualizações"))
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(botoes)
        self.resize(460, 380)

    def _aparencia(self, janela: DocumentWindow) -> QWidget:
        self.theme_buttons: dict[str, QRadioButton] = {}
        self._theme_actions = janela.theme_actions
        botoes = QButtonGroup(self)
        temas = []
        for tema in available_themes():
            acao = janela.theme_actions[tema.name]
            botao = QRadioButton(acao.text())
            botao.setChecked(acao.isChecked())
            botao.clicked.connect(acao.trigger)
            acao.toggled.connect(self._theme_toggled)  # método: desliga sozinho ao fechar
            botoes.addButton(botao)
            temas.append(botao)
            self.theme_buttons[tema.name] = botao
        self.language_box = QComboBox()
        for codigo, nome in LANGUAGES.items():
            self.language_box.addItem(nome, codigo)  # cada idioma com o próprio nome
        self.language_box.setCurrentIndex(
            self.language_box.findData(saved_language() or language())
        )
        self.language_box.activated.connect(
            lambda i: janela._language_chosen(self.language_box.itemData(i))
        )
        self.grid_box = _caixa(janela.action_grid, _("Mostrar a &grade"))
        self.panel_boxes = [
            _caixa(dock.toggleViewAction(), dock.windowTitle())
            for dock in (janela.inspector_dock, janela.properties_dock, janela.messages_dock)
        ]
        return _aba(
            _grupo(_("Tema"), *temas),
            _grupo(
                _("Idioma"),
                self.language_box,
                _dica(_("Vale quando o HaradaER for fechado e aberto de novo.")),
            ),
            _grupo(_("Desenho"), self.grid_box, _dica(_atalho(janela.action_grid))),
            _grupo(_("Painéis"), *self.panel_boxes),
        )

    def _theme_toggled(self, ligado: bool) -> None:
        if ligado:
            nome = next(n for n, a in self._theme_actions.items() if a is self.sender())
            self.theme_buttons[nome].setChecked(True)

    def _verificacao(self, janela: DocumentWindow) -> QWidget:
        self.validate_box = _caixa(janela.action_validate, _("&Verificar modelo"))
        self.structure_box = _caixa(janela.action_structure, _("&Avisos de estrutura"))
        return _aba(
            _grupo(
                _("Verificação"),
                self.validate_box,
                _dica(_("Marca em vermelho as conexões que o tipo não aceita.")),
                self.structure_box,
                _dica(janela.action_structure.toolTip()),
            )
        )

    def _edicao(self, janela: DocumentWindow) -> QWidget:
        self.quick_edit_box = _caixa(janela.action_quick_edit, _("Edição rápid&a"))
        return _aba(
            _grupo(
                _("Edição rápida"),
                self.quick_edit_box,
                _dica(janela.action_quick_edit.statusTip()),
                _dica(_atalho(janela.action_quick_edit)),
            )
        )

    def _arquivos(self, janela: DocumentWindow) -> QWidget:
        self.clear_recent_button = QPushButton(_("&Limpar lista"))
        self.clear_recent_button.clicked.connect(janela.recent.clear)
        linha = QWidget()
        layout = QHBoxLayout(linha)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.clear_recent_button)
        layout.addStretch(1)
        return _aba(_grupo(_("Arquivos recentes"), linha))

    def _atualizacoes(self, janela: DocumentWindow) -> QWidget:
        self.auto_updates_box = _caixa(janela.auto_updates_action, _("Verificar ao a&brir"))
        self.check_now_button = QPushButton(_("Verificar &agora"))
        self.check_now_button.clicked.connect(janela.check_updates_action.trigger)
        linha = QWidget()
        layout = QHBoxLayout(linha)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check_now_button)
        layout.addWidget(_dica(_("Você tem a {atual}.").format(atual=haradaer.__version__)), 1)
        return _aba(
            _grupo(
                _("Atualizações"),
                self.auto_updates_box,
                _dica(_("No máximo uma vez por dia, no GitHub.")),
                linha,
            )
        )
