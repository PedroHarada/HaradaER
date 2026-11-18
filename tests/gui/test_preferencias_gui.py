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


@pytest.mark.skipif(sys.platform == "darwin", reason="no macOS a barra de menus é a do sistema")
def test_barra_de_menus_escondida_e_botao_menu(janela):
    assert janela.menuBar().isHidden()
    assert janela.menu_button.menu() is None  # sem a setinha de menu
    janela.menu_button.click()
    assert janela.main_menu.isVisible()
    janela.main_menu.hide()
    submenus = [a.menu() for a in janela.main_menu.actions() if a.menu() is not None]
    for menu in (janela.edit_menu, janela.arrange_menu, janela.view_menu, janela.help_menu):
        assert menu in submenus


def test_barra_de_comandos_tem_as_acoes_do_dia_a_dia(janela):
    acoes = janela.command_bar.actions()
    for acao in (janela.action_new, janela.action_open, janela.action_save):
        assert acao in acoes
    for acao in (janela.action_undo, janela.action_zoom_in, janela.action_preferences):
        assert acao not in acoes  # ficam no Menu e no teclado
    assert janela.action_preferences.shortcut().toString() == "Ctrl+,"


def test_atalhos_valem_com_a_barra_escondida(janela):
    acoes = janela.actions()
    for acao in (janela.action_save, janela.action_grid, janela.action_preferences):
        assert acao in acoes


def test_opcoes_saem_dos_menus(janela):
    textos = [a.text() for a in janela.view_menu.actions() + janela.help_menu.actions()]
    assert janela.action_grid.text() in textos  # a grade continua em Exibir, com o atalho
    for acao in (janela.action_validate, janela.action_structure, janela.auto_updates_action):
        assert acao.text() not in textos


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


def test_barra_de_comandos_fica_acima_da_faixa_mesmo_com_disposicao_antiga(qtbot):
    from haradaer.gui.settings import save_window_layout

    antiga = DocumentWindow()
    qtbot.addWidget(antiga)
    antiga.removeToolBar(antiga.command_bar)  # como numa disposição salva antes da barra nova
    antiga.addToolBar(Qt.ToolBarArea.TopToolBarArea, antiga.command_bar)
    antiga.command_bar.show()
    assert not antiga.toolBarBreak(antiga.tool_bar)
    save_window_layout(antiga.saveGeometry(), antiga.saveState())

    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.show()
    qtbot.waitExposed(janela)
    assert janela.toolBarBreak(janela.tool_bar)
    assert janela.command_bar.geometry().bottom() < janela.tool_bar.geometry().top()


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


@pytest.mark.skipif(sys.platform == "darwin", reason="no macOS a barra de menus é a do sistema")
def test_alt_sozinho_e_f10_abrem_o_menu(janela, qtbot, monkeypatch):
    abertos = []
    monkeypatch.setattr(janela, "_show_main_menu", lambda: abertos.append(True))
    qtbot.keyPress(janela.view, Qt.Key.Key_Alt)
    qtbot.keyRelease(janela.view, Qt.Key.Key_Alt)
    assert abertos == [True]
    qtbot.keyPress(janela.view, Qt.Key.Key_Alt)  # Alt com outra tecla não abre
    qtbot.keyPress(janela.view, Qt.Key.Key_S, Qt.KeyboardModifier.AltModifier)
    qtbot.keyRelease(janela.view, Qt.Key.Key_Alt)
    assert abertos == [True]
    assert janela.action_main_menu.shortcut().toString() == "F10"
    assert janela.action_main_menu in janela.actions()


def test_menu_principal_sem_letra_de_acesso_repetida(qtbot):
    from haradaer.i18n import set_language

    for idioma in ("pt", "en", "es"):
        set_language(idioma)
        janela = DocumentWindow()
        qtbot.addWidget(janela)
        letras = [
            a.text()[a.text().index("&") + 1].lower()
            for a in janela.main_menu.actions()
            if "&" in a.text()
        ]
        assert len(letras) == len(set(letras)), idioma
