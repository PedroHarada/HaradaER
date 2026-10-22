"""Idioma da interface (RNF-06): a janela em inglês e a troca pelo menu Exibir › Idioma."""

import pytest
from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.app import choose_language, install_translator
from haradaer.gui.settings import saved_language, set_saved_language
from haradaer.gui.window import DocumentWindow
from haradaer.i18n import language, set_language


@pytest.fixture
def avisos(monkeypatch):
    capturados: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda pai, titulo, texto: capturados.append((titulo, texto))
    )
    return capturados


def _menus(janela: DocumentWindow) -> list[str]:
    return [acao.text() for acao in janela.menuBar().actions()]


def test_janela_em_portugues(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert _menus(janela) == ["&Arquivo", "&Editar", "&Organizar", "E&xibir"]


def test_janela_em_ingles(qtbot):
    set_language("en")
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert _menus(janela) == ["&File", "&Edit", "&Arrange", "&View"]
    assert janela.windowTitle() == "Untitled[*] - HaradaER"
    assert janela.action_save.text() == "&Save"
    assert janela.inspector_dock.windowTitle() == "Object inspector"
    assert janela.messages.status.text() == "No problems in the model."
    curtos = [a.text() for a in janela._tool_actions.values()]
    assert "Select" in curtos and "Weak ent." in curtos


def test_elemento_criado_em_ingles_tem_nome_em_ingles(qtbot, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    set_language("en")
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    no = janela.editor.create("ent", 0, 0)
    assert no.name == "Entity"
    assert janela.action_undo.text() == "&Undo Add element"


def test_menu_idioma_marca_o_atual(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert {c: a.isChecked() for c, a in janela.language_actions.items()} == {
        "pt": True,
        "en": False,
    }
    assert janela.language_actions["en"].text() == "English"  # cada idioma no próprio nome


def test_trocar_idioma_grava_e_avisa_no_idioma_novo(qtbot, avisos):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.language_actions["en"].trigger()
    assert saved_language() == "en"
    assert avisos == [
        ("Language", "The language changes when HaradaER is closed and opened again.")
    ]
    assert language() == "pt"  # a janela aberta continua como estava
    assert _menus(janela)[0] == "&Arquivo"
    assert janela.language_actions["en"].isChecked()


def test_escolher_o_mesmo_idioma_nao_avisa(qtbot, avisos):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.language_actions["pt"].trigger()
    assert avisos == []


def test_ao_abrir_vale_o_idioma_gravado(monkeypatch):
    monkeypatch.setattr(QLocale, "system", lambda: QLocale("pt_BR"))
    set_saved_language("en")
    assert choose_language() == "en"


def test_na_primeira_vez_vale_o_idioma_do_sistema(monkeypatch):
    monkeypatch.setattr(QLocale, "system", lambda: QLocale("en_US"))
    assert saved_language() is None
    assert choose_language() == "en"
    monkeypatch.setattr(QLocale, "system", lambda: QLocale("de_DE"))
    assert choose_language() == "pt"


def test_tradutor_do_qt_so_em_portugues(qapp):
    set_language("en")
    assert not install_translator(qapp)
