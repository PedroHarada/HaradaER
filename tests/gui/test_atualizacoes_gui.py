"""Aviso de versão nova (RF-22) na janela, com a consulta ao GitHub trocada por uma resposta
fixa."""

from datetime import date

import pytest
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

import haradaer
from haradaer import updates
from haradaer.gui.settings import last_update_check, set_update_check_enabled
from haradaer.gui.window import DocumentWindow


@pytest.fixture
def janela(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


@pytest.fixture
def avisos(monkeypatch):
    textos: list[str] = []
    monkeypatch.setattr(QMessageBox, "information", lambda pai, titulo, texto: textos.append(texto))
    return textos


@pytest.fixture
def caixa(monkeypatch):
    """O aviso de versão nova: guarda o texto e aperta o botão pedido (ou nenhum)."""
    estado = {"texto": None, "botao": None}

    def exec_(self):
        estado["texto"] = self.text()
        for botao in self.buttons():
            if botao.text() == estado["botao"]:
                self._clicado = botao
        return 0

    monkeypatch.setattr(QMessageBox, "exec", exec_)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: getattr(self, "_clicado", None))
    return estado


def _resposta(monkeypatch, versao):
    monkeypatch.setattr(updates, "fetch_latest", lambda: versao)


def _espera(qtbot, janela):
    qtbot.waitUntil(lambda: not janela.update_checker._running, timeout=2000)


def test_versao_nova_e_baixar_abre_releases(qtbot, janela, caixa, monkeypatch):
    _resposta(monkeypatch, "99.0.0")
    abertos = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: abertos.append(url.toString()))
    caixa["botao"] = "&Baixar"
    janela.check_updates_action.trigger()
    _espera(qtbot, janela)
    assert "99.0.0" in caixa["texto"] and haradaer.__version__ in caixa["texto"]
    assert abertos == [updates.RELEASES]


def test_agora_nao_nao_abre_nada(qtbot, janela, caixa, monkeypatch):
    _resposta(monkeypatch, "99.0.0")
    abertos = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: abertos.append(url))
    caixa["botao"] = "Agora &não"
    janela.check_updates_action.trigger()
    _espera(qtbot, janela)
    assert caixa["texto"] and abertos == []


def test_pedido_manual_sem_novidade_avisa(qtbot, janela, avisos, monkeypatch):
    _resposta(monkeypatch, haradaer.__version__)
    janela.check_updates_action.trigger()
    _espera(qtbot, janela)
    assert len(avisos) == 1 and haradaer.__version__ in avisos[0]


def test_pedido_manual_sem_rede_avisa(qtbot, janela, avisos):
    janela.check_updates_action.trigger()  # o conftest deixa os testes sem rede
    _espera(qtbot, janela)
    assert len(avisos) == 1 and "GitHub" in avisos[0]


def test_ao_abrir_sem_rede_fica_quieto(qtbot, janela, avisos, caixa):
    assert janela.update_checker.check_if_due(date(2026, 10, 22))
    _espera(qtbot, janela)
    assert avisos == [] and caixa["texto"] is None
    assert last_update_check() == "2026-10-22"


def test_ao_abrir_uma_vez_por_dia(qtbot, janela):
    assert janela.update_checker.check_if_due(date(2026, 10, 22))
    _espera(qtbot, janela)
    assert not janela.update_checker.check_if_due(date(2026, 10, 22))
    assert janela.update_checker.check_if_due(date(2026, 10, 23))
    _espera(qtbot, janela)


def test_desligado_nao_verifica(qtbot, janela):
    janela.auto_updates_action.setChecked(False)
    assert not janela.update_checker.check_if_due(date(2026, 10, 22))
    set_update_check_enabled(True)
    assert janela.update_checker.check_if_due(date(2026, 10, 22))
    _espera(qtbot, janela)


def test_opcao_ligada_por_padrao(janela):
    assert janela.auto_updates_action.isChecked()
