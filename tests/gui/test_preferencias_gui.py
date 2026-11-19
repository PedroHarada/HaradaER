"""Barra de comandos no lugar da barra de menus, e a janela Preferências."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.preferences_dialog import PreferencesDialog
from haradaer.gui.settings import saved_language
from haradaer.gui.theme import current_theme
from haradaer.gui.window import DocumentWindow


@pytest.fixture
def janela(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


def test_barra_de_menus_enxuta(janela):
    assert not janela.menuBar().isHidden()
    nomes = [a.text() for a in janela.menuBar().actions()]
    assert nomes == ["&Arquivo", "&Editar", "&Organizar", "E&xibir", "&Configurações", "Aj&uda"]
    for acao in (
        janela.action_preferences,
        janela.action_validate,
        janela.action_structure,
        janela.action_quick_edit,
    ):
        assert acao in janela.settings_menu.actions()
    nos_menus = janela.view_menu.actions() + janela.help_menu.actions()
    nos_menus += janela.edit_menu.actions()
    for acao in (janela.auto_updates_action, janela.check_updates_action):
        assert acao not in nos_menus  # só na janela Preferências
    assert janela.action_copy_image in janela.file_menu.actions()
    assert janela.action_preferences.shortcut().toString() == "Ctrl+,"
    assert janela.inspector_dock.toggleViewAction() in janela.view_menu.actions()
    assert janela.action_grid in janela.view_menu.actions()  # parte da vista (Apple)


def test_atalhos_das_opcoes_aparecem_no_f1(janela, qtbot):
    dialogo = janela.show_shortcuts()
    qtbot.addWidget(dialogo)
    linhas = dialogo.visible_rows()
    assert ("Grade", "Ctrl+'") in linhas
    assert any(acao == "Edição rápida" for acao, _tecla in linhas)


def test_preferencias_so_idioma_e_atualizacoes(janela):
    dialogo = PreferencesDialog(janela)
    assert dialogo.windowTitle() == "Preferências"
    dialogo.auto_updates_box.setChecked(False)
    assert not janela.auto_updates_action.isChecked()
    janela.auto_updates_action.setChecked(True)
    assert dialogo.auto_updates_box.isChecked()


def test_idioma_nas_preferencias(janela, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    dialogo = PreferencesDialog(janela)
    indice = dialogo.language_box.findData("es")
    dialogo.language_box.setCurrentIndex(indice)
    dialogo.language_box.activated.emit(indice)
    assert saved_language() == "es"
    assert janela.language_actions["es"].isChecked()


def test_atalho_abre_preferencias(janela, qtbot):
    dialogo = janela.show_preferences()
    qtbot.addWidget(dialogo)
    assert dialogo.isVisible()
    assert dialogo.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)


def test_caixas_de_mensagem_e_botoes_sem_desenho(qapp):
    from PySide6.QtWidgets import QStyle

    from haradaer.gui.theme import TextOnlyStyle, apply_theme

    apply_theme(current_theme(), save=False)
    estilo = qapp.style()
    assert isinstance(estilo, TextOnlyStyle)
    assert estilo.standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion).isNull()
    assert estilo.standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning).isNull()
    assert estilo.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton).isNull()
    assert estilo.standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton).isNull()
    assert not estilo.standardIcon(QStyle.StandardPixmap.SP_ArrowUp).isNull()


def test_sobre_o_haradaer(janela, qtbot):
    import haradaer

    assert janela.about_action in janela.help_menu.actions()
    caixa = janela.show_about()
    qtbot.addWidget(caixa)
    assert haradaer.__version__ in caixa.text()
    assert "GPL" in caixa.informativeText()
    assert "github.com/PedroHarada/HaradaER" in caixa.informativeText()
    assert caixa.icon() == QMessageBox.Icon.NoIcon  # só texto


def test_tela_cheia_em_exibir(janela):
    acao = janela.action_full_screen
    assert acao in janela.view_menu.actions()
    assert acao.isCheckable()
    assert not acao.shortcut().isEmpty()  # F11 onde o sistema não tem atalho padrão


def test_sem_menu_janela_e_itens_no_mesmo_lugar_em_todo_sistema(janela):
    from PySide6.QtGui import QAction

    from haradaer.gui.window import _menu_actions

    assert not hasattr(janela, "window_menu")
    for acao in _menu_actions(janela.menuBar(), todas=True):
        assert acao.menuRole() == QAction.MenuRole.NoRole  # o macOS não move nada


def test_ajuda_trocar_o_idioma_abre_as_preferencias(janela, qtbot, monkeypatch):
    abertas = []
    monkeypatch.setattr(janela, "show_preferences", lambda: abertas.append(True))
    assert janela.language_action in janela.help_menu.actions()
    janela.language_action.trigger()
    assert abertas == [True]


def test_restaurar_todos_os_padroes(janela, monkeypatch):
    from haradaer.gui.settings import saved_language

    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    janela.theme_actions["escuro"].trigger()
    janela.action_grid.setChecked(True)
    janela.action_structure.setChecked(False)
    janela.action_quick_edit.setChecked(True)
    janela.auto_updates_action.setChecked(False)
    janela._language_chosen("es")
    dialogo = PreferencesDialog(janela)
    janela.action_show_status.setChecked(False)
    assert "todos os padrões" in dialogo.restore_button.text()
    dialogo.restore_button.click()
    assert dialogo.confirm_row.isVisibleTo(dialogo)
    dialogo.confirm_button.click()
    assert current_theme().name == "claro"
    assert not janela.action_grid.isChecked()
    assert janela.action_structure.isChecked()
    assert not janela.action_quick_edit.isChecked()
    assert janela.auto_updates_action.isChecked()
    assert janela.action_show_status.isChecked()
    assert saved_language() == "es"  # o idioma não muda
    assert not dialogo.confirm_row.isVisibleTo(dialogo)


def test_cancelar_nao_restaura(janela):
    janela.action_grid.setChecked(True)
    dialogo = PreferencesDialog(janela)
    dialogo.restore_button.click()
    dialogo.cancel_button.click()
    assert janela.action_grid.isChecked()


def test_menu_configuracoes_como_no_kde(janela):
    from haradaer.gui.settings import status_bar_enabled

    acoes = janela.settings_menu.actions()
    tema = next(a.menu() for a in acoes if a.menu() is not None)
    assert janela.theme_actions["claro"] in tema.actions()
    assert janela.action_show_tools in acoes and janela.action_show_status in acoes
    assert janela.action_preferences in acoes
    janela.action_show_tools.setChecked(False)
    assert janela.tool_bar.isHidden()
    janela.action_show_status.setChecked(False)
    assert janela.statusBar().isHidden() and not status_bar_enabled()
    janela.action_show_status.setChecked(True)
    assert status_bar_enabled()
