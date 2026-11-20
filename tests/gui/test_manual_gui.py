"""Ajuda › Manual do HaradaER (F1): o manual instalado, numa janela do próprio programa."""

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from haradaer import selftest
from haradaer.gui.manual_dialog import (
    MANUAL_FILES,
    ManualDialog,
    heading_id,
    manual_html,
    manual_path,
)
from haradaer.gui.window import DocumentWindow
from haradaer.i18n import set_language


@pytest.fixture
def janela(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


@pytest.mark.parametrize("idioma", sorted(MANUAL_FILES))
def test_manual_de_cada_idioma_existe(idioma):
    assert manual_path(idioma) is not None


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("Depois de abrir", "depois-de-abrir"),
        ("macOS", "macos"),
        ("After opening", "after-opening"),
    ],
)
def test_ancora_igual_a_do_github(titulo, esperado):
    assert heading_id(titulo) == esperado


def test_html_tem_ancoras_tabelas_e_sem_readme():
    html = manual_html(manual_path("pt").read_text(encoding="utf-8"))
    assert '<a name="depois-de-abrir"></a>' in html
    assert "<table>" in html
    assert "README" not in html
    assert "atalhos: início" not in html  # o comentário do bloco gerado não aparece


def test_f1_abre_a_janela_no_idioma_escolhido(janela, qtbot):
    dialogo = janela.open_manual()
    qtbot.addWidget(dialogo)
    assert isinstance(dialogo, ManualDialog)
    assert dialogo.isVisible()
    assert "Primeiros passos" in dialogo.browser.toPlainText()
    assert janela.open_manual() is dialogo  # a mesma janela, trazida para a frente


def test_manual_em_espanhol(qtbot):
    set_language("es")
    dialogo = ManualDialog(None, "es")
    qtbot.addWidget(dialogo)
    assert "Primeros pasos" in dialogo.browser.toPlainText()
    assert dialogo.windowTitle() == "Manual de HaradaER"


def test_busca_acha_todas_conta_e_anda_nos_dois_sentidos(qtbot):
    dialogo = ManualDialog(None, "pt")
    qtbot.addWidget(dialogo)
    dialogo.find_field.setText("harada")  # busca enquanto digita, sem maiúsculas
    total = len(dialogo._matches)
    assert total > 3
    assert len(dialogo.browser.extraSelections()) == total  # todas destacadas
    assert dialogo.not_found.text() == f"1 de {total}"
    inicio = dialogo.browser.textCursor().position()
    dialogo.next_button.click()
    assert dialogo.not_found.text() == f"2 de {total}"
    assert dialogo.browser.textCursor().position() > inicio
    dialogo.previous_button.click()
    dialogo.previous_button.click()  # antes do primeiro, vai ao último
    assert dialogo.not_found.text() == f"{total} de {total}"
    dialogo.find_field.setText("texto que não existe no manual")
    assert dialogo.not_found.text() == "Nada encontrado"
    assert not dialogo.next_button.isEnabled()


def test_links_web_vao_ao_navegador_e_os_outros_idiomas_trocam_o_manual(qtbot, monkeypatch):
    abertos = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: abertos.append(url) or True)
    dialogo = ManualDialog(None, "pt")
    qtbot.addWidget(dialogo)
    dialogo._link(QUrl("https://example.org"))
    assert len(abertos) == 1
    dialogo._link(QUrl("GETTING-STARTED.md"))
    assert "Getting started" in dialogo.browser.toPlainText()


def test_sem_manual_abre_o_repositorio(janela, monkeypatch):
    import haradaer.gui.window as modulo

    abertos = []
    monkeypatch.setattr(modulo, "manual_path", lambda idioma: None)
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: abertos.append(url) or True)
    assert janela.open_manual() is None
    assert abertos[0].toString().endswith("/docs/PRIMEIROS-PASSOS.md")


def test_autoteste_confere_os_manuais():
    assert selftest.check_manual() == "manuais: ok"


def test_pacote_leva_os_manuais():
    from pathlib import Path

    spec = (Path(__file__).resolve().parents[2] / "packaging" / "HaradaER.spec").read_text("utf-8")
    for nome in MANUAL_FILES.values():
        assert nome in spec
    assert "haradaer/manuais" in spec


def test_enter_na_busca_procura_e_nao_fecha_a_janela(qtbot):
    from PySide6.QtCore import Qt

    dialogo = ManualDialog(None, "pt")
    qtbot.addWidget(dialogo)
    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.find_field.setFocus()
    qtbot.keyClicks(dialogo.find_field, "TerraER")
    total = len(dialogo._matches)
    assert dialogo.not_found.text() == f"1 de {total}"
    qtbot.keyClick(dialogo.find_field, Qt.Key.Key_Return)
    assert dialogo.isVisible()
    assert dialogo.not_found.text() == f"2 de {total}"
    qtbot.keyClick(dialogo.find_field, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert dialogo.isVisible()
    assert dialogo.not_found.text() == f"1 de {total}"
