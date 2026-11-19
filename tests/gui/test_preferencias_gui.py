"""Barra de comandos no lugar da barra de menus, e a janela Preferências."""

import sys

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
    assert nomes == ["&Arquivo", "&Editar", "&Organizar", "E&xibir", "Aj&uda"]
    nos_menus = janela.view_menu.actions() + janela.help_menu.actions()
    nos_menus += janela.edit_menu.actions()
    for acao in (
        janela.action_validate,
        janela.action_structure,
        janela.auto_updates_action,
        janela.check_updates_action,
        janela.action_quick_edit,
        janela.action_preferences,
        janela.action_copy_image,
    ):
        assert acao not in nos_menus
    assert janela.action_preferences in janela.file_menu.actions()
    assert janela.action_copy_image in janela.file_menu.actions()
    assert janela.action_preferences.shortcut().toString() == "Ctrl+,"
    assert janela.inspector_dock.toggleViewAction() in janela.view_menu.actions()
    assert janela.action_grid in janela.view_menu.actions()  # parte da vista (Apple)


def test_atalhos_das_opcoes_continuam_e_aparecem_no_f1(janela, qtbot):
    assert janela.action_quick_edit in janela.actions()
    dialogo = janela.show_shortcuts()
    qtbot.addWidget(dialogo)
    linhas = dialogo.visible_rows()
    assert ("Grade", "Ctrl+'") in linhas
    assert any(acao == "Edição rápida" for acao, _tecla in linhas)


def test_paineis_nas_preferencias(janela):
    dialogo = PreferencesDialog(janela)
    caixa = dialogo.panel_boxes[0]
    caixa.setChecked(False)
    assert not janela.inspector_dock.toggleViewAction().isChecked()
    caixa.setChecked(True)
    assert janela.inspector_dock.toggleViewAction().isChecked()


def test_preferencias_seguem_as_acoes_nos_dois_sentidos(janela):
    dialogo = PreferencesDialog(janela)
    assert dialogo.grid_box.isChecked() == janela.action_grid.isChecked()
    dialogo.grid_box.setChecked(True)
    assert janela.action_grid.isChecked()
    janela.action_grid.setChecked(False)
    assert not dialogo.grid_box.isChecked()
    dialogo.structure_box.setChecked(False)
    assert not janela.action_structure.isChecked()
    dialogo.validate_box.setChecked(False)
    assert not janela.action_validate.isChecked()
    dialogo.quick_edit_box.setChecked(True)
    assert janela.action_quick_edit.isChecked()
    dialogo.auto_updates_box.setChecked(False)
    assert not janela.auto_updates_action.isChecked()


def test_tema_nas_preferencias(janela):
    dialogo = PreferencesDialog(janela)
    assert dialogo.theme_buttons[current_theme().name].isChecked()
    dialogo.theme_buttons["escuro"].click()
    assert current_theme().name == "escuro"
    janela.theme_actions["claro"].trigger()
    assert dialogo.theme_buttons["claro"].isChecked()


def test_idioma_nas_preferencias(janela, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    dialogo = PreferencesDialog(janela)
    indice = dialogo.language_box.findData("es")
    dialogo.language_box.setCurrentIndex(indice)
    dialogo.language_box.activated.emit(indice)
    assert saved_language() == "es"
    assert janela.language_actions["es"].isChecked()


def test_limpar_recentes(janela, tmp_path):
    arquivo = tmp_path / "m.xml"
    arquivo.write_text("x")
    janela.recent.add(arquivo)
    PreferencesDialog(janela).clear_recent_button.click()
    assert janela.recent.paths() == []


def test_atalho_abre_preferencias(janela, qtbot):
    dialogo = janela.show_preferences()
    qtbot.addWidget(dialogo)
    assert dialogo.isVisible()
    assert dialogo.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    assert [dialogo.tabs.tabText(i) for i in range(dialogo.tabs.count())] == [
        "Aparência",
        "Verificação",
        "Edição",
        "Arquivos",
        "Atualizações",
    ]


def test_caixas_de_mensagem_e_botoes_sem_desenho(qapp):
    from PySide6.QtWidgets import QStyle

    from haradaer.gui.theme import TextOnlyStyle, apply_theme, current_theme

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


@pytest.mark.skipif(sys.platform == "darwin", reason="no macOS o menu Janela existe")
def test_menu_janela_so_no_macos(janela):
    assert not hasattr(janela, "window_menu")


def test_menu_janela_do_macos(janela):
    janela._build_window_menu()
    acoes = janela.window_menu.actions()
    assert janela.action_minimize in acoes and janela.action_zoom_window in acoes
    assert janela.action_minimize.shortcut().toString() == "Ctrl+M"


def test_restaurar_padroes_de_todas_as_abas(janela, monkeypatch):
    from haradaer.gui.settings import saved_language
    from haradaer.gui.theme import current_theme

    monkeypatch.setattr(QMessageBox, "information", lambda *a: None)
    janela.theme_actions["escuro"].trigger()
    janela.action_grid.setChecked(True)
    janela.action_structure.setChecked(False)
    janela.action_quick_edit.setChecked(True)
    janela.auto_updates_action.setChecked(False)
    janela._language_chosen("es")
    dialogo = PreferencesDialog(janela)
    assert "todas as abas" in dialogo.restore_button.text()
    dialogo.restore_button.click()
    assert dialogo.confirm_row.isVisibleTo(dialogo)
    dialogo.confirm_button.click()
    assert current_theme().name == "claro"
    assert not janela.action_grid.isChecked()
    assert janela.action_structure.isChecked()
    assert not janela.action_quick_edit.isChecked()
    assert janela.auto_updates_action.isChecked()
    assert saved_language() == "es"  # o idioma não muda
    assert not dialogo.confirm_row.isVisibleTo(dialogo)


def test_cancelar_nao_restaura(janela):
    janela.action_grid.setChecked(True)
    dialogo = PreferencesDialog(janela)
    dialogo.restore_button.click()
    dialogo.cancel_button.click()
    assert janela.action_grid.isChecked()


def test_preferencias_reabrem_na_ultima_aba_com_o_nome_no_titulo(janela):
    dialogo = PreferencesDialog(janela)
    dialogo.tabs.setCurrentIndex(2)
    assert dialogo.windowTitle() == "Preferências › Edição"
    outro = PreferencesDialog(janela)
    assert outro.tabs.currentIndex() == 2
    outro.tabs.setCurrentIndex(0)
