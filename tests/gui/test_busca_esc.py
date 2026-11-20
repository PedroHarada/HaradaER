"""Campos de busca: além do botão de limpar, Esc apaga o que foi digitado."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.window import DocumentWindow


@pytest.fixture
def janela(qtbot, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


def test_busca_do_inspetor_esc_limpa(janela, qtbot):
    campo = janela.inspector.search
    assert campo.isClearButtonEnabled()
    campo.setText("aluno")
    qtbot.keyClick(campo, Qt.Key.Key_Escape)
    assert campo.text() == ""


def test_busca_dos_atalhos_esc_limpa_e_depois_fecha(janela, qtbot):
    dialogo = janela.show_shortcuts()
    qtbot.addWidget(dialogo)
    qtbot.waitExposed(dialogo)
    campo = dialogo.search
    assert campo.isClearButtonEnabled()
    campo.setText("grade")
    qtbot.keyClick(campo, Qt.Key.Key_Escape)
    assert campo.text() == "" and dialogo.isVisible()  # o primeiro Esc só limpa
    qtbot.keyClick(campo, Qt.Key.Key_Escape)
    assert not dialogo.isVisible()  # com o campo vazio, Esc fecha a janela
