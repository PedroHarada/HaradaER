"""Menu Ajuda: relatar um problema e sugerir uma melhoria (RF-21)."""

import pytest
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

import haradaer
from haradaer.gui.window import DocumentWindow


@pytest.fixture
def abertos(monkeypatch):
    urls: list[str] = []

    def abrir(url):
        urls.append(url.toString())
        return True

    monkeypatch.setattr(QDesktopServices, "openUrl", abrir)
    return urls


@pytest.mark.parametrize(
    ("acao", "modelo"), [("report_action", "bug.yml"), ("suggest_action", "melhoria.yml")]
)
def test_abre_a_issue_preenchida(qtbot, abertos, acao, modelo):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    getattr(janela, acao).trigger()
    assert len(abertos) == 1
    assert "/issues/new?" in abertos[0]
    assert f"template={modelo}" in abertos[0]
    assert f"versao={haradaer.__version__}" in abertos[0]


def test_sem_navegador_mostra_o_endereco(qtbot, monkeypatch):
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
    avisos: list[str] = []
    monkeypatch.setattr(QMessageBox, "information", lambda pai, titulo, texto: avisos.append(texto))
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.report_action.trigger()
    assert len(avisos) == 1 and "/issues/new?" in avisos[0]
