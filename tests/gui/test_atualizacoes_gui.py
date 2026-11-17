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
    assert "testes sem rede" in avisos[0]  # o motivo técnico vai junto


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


# Atualizar e reiniciar (1.4.0)


def _botoes(monkeypatch):
    """Guarda os botões de cada aviso e aperta o primeiro da lista `apertar` que existir."""
    estado = {"botoes": [], "apertar": []}

    def exec_(self):
        nomes = [b.text() for b in self.buttons()]
        estado["botoes"].append(nomes)
        for botao in self.buttons():
            if botao.text() in estado["apertar"]:
                self._clicado = botao
                break
        return 0

    monkeypatch.setattr(QMessageBox, "exec", exec_)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: getattr(self, "_clicado", None))
    return estado


@pytest.fixture
def instalador(monkeypatch):
    from haradaer.gui import updates as gui_updates

    novo = gui_updates.UpdateInstaller()
    monkeypatch.setattr(gui_updates, "_installer", novo)
    return novo


def test_do_codigo_fonte_so_baixar(qtbot, janela, monkeypatch):
    estado = _botoes(monkeypatch)
    _resposta(monkeypatch, "99.0.0")
    janela.check_updates_action.trigger()
    _espera(qtbot, janela)
    assert "Atualizar e &reiniciar" not in estado["botoes"][0]
    assert "&Baixar" in estado["botoes"][0]


def test_atualizar_prepara_e_troca_ao_fechar(qtbot, janela, monkeypatch, tmp_path, instalador):
    from haradaer import selfupdate

    alvo = selfupdate.Target(tmp_path / "HaradaER", "linux")
    pronto = selfupdate.Prepared("99.0.0", alvo, tmp_path / "novo")
    monkeypatch.setattr(selfupdate, "install_target", lambda: alvo)
    monkeypatch.setattr(selfupdate, "why_not", lambda a: None)
    monkeypatch.setattr(selfupdate, "prepare", lambda versao, a, progresso, cancelado: pronto)
    aplicados, reabertos = [], []
    monkeypatch.setattr(selfupdate, "apply", aplicados.append)
    monkeypatch.setattr(selfupdate, "restart", reabertos.append)
    estado = _botoes(monkeypatch)
    estado["apertar"] = ["Atualizar e &reiniciar", "Ao &fechar"]
    _resposta(monkeypatch, "99.0.0")
    janela.check_updates_action.trigger()
    _espera(qtbot, janela)
    qtbot.waitUntil(lambda: instalador.prepared is pronto, timeout=2000)
    assert "&Reiniciar agora" in estado["botoes"][-1]
    assert aplicados == []  # nada trocado com o programa aberto
    instalador.apply_on_quit()
    assert aplicados == [pronto] and reabertos == []
    instalador.apply_on_quit()  # só uma vez
    assert aplicados == [pronto]


def test_reiniciar_agora_troca_e_reabre(monkeypatch, tmp_path, instalador):
    from haradaer import selfupdate

    alvo = selfupdate.Target(tmp_path / "HaradaER", "linux")
    instalador.prepared = selfupdate.Prepared("99.0.0", alvo, tmp_path / "novo")
    reabertos = []
    monkeypatch.setattr(selfupdate, "apply", lambda p: None)
    monkeypatch.setattr(selfupdate, "restart", reabertos.append)
    instalador.restart_now()
    instalador.apply_on_quit()
    assert reabertos == [alvo]


def test_falha_no_preparo_avisa(qtbot, monkeypatch, tmp_path, instalador, avisos):
    from haradaer import selfupdate

    def falha(versao, alvo, progresso, cancelado):
        raise selfupdate.UpdateError("O download veio corrompido. Tente de novo.")

    monkeypatch.setattr(selfupdate, "prepare", falha)
    monkeypatch.setattr(QMessageBox, "warning", lambda pai, titulo, texto: avisos.append(texto))
    alvo = selfupdate.Target(tmp_path / "HaradaER", "linux")
    assert instalador.start("99.0.0", alvo)
    qtbot.waitUntil(lambda: not instalador._running, timeout=2000)
    assert avisos == ["O download veio corrompido. Tente de novo."]
    assert instalador.prepared is None
