"""Cópia de recuperação: fora do arquivo, apagada ao salvar ou fechar, oferecida ao abrir."""

import shutil

import pytest
from PySide6.QtWidgets import QMessageBox

from haradaer.core import io
from haradaer.gui import app as aplicativo
from haradaer.gui.preferences_dialog import PreferencesDialog
from haradaer.gui.recovery import RecoveryCopy, leftovers, recovery_dir
from haradaer.gui.settings import recovery_interval, set_recovery_interval
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def fechar_descarta(monkeypatch):
    """As janelas alteradas fecham no fim do teste sem perguntar se salva."""
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture(autouse=True)
def pasta_limpa():
    shutil.rmtree(recovery_dir(), ignore_errors=True)
    yield
    shutil.rmtree(recovery_dir(), ignore_errors=True)


def _janela_alterada(qtbot) -> DocumentWindow:
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.editor.create("ent", 50, 50)
    assert janela.editor.history.is_dirty
    return janela


def _fecha_sem_apagar(janela: DocumentWindow) -> None:
    """Simula o fechamento repentino: a trava é solta, os arquivos ficam."""
    janela.recovery._trava.unlock()
    janela.recovery._trava = None


def test_padrao_e_um_minuto_e_zero_desliga(qtbot):
    assert recovery_interval() == 1
    janela = _janela_alterada(qtbot)
    assert janela._recovery_timer.isActive()
    assert janela._recovery_timer.interval() == 60_000
    set_recovery_interval(0)
    janela.save_recovery()
    assert not janela._recovery_timer.isActive()
    assert not janela.recovery.exists


def test_grava_so_com_alteracao(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.save_recovery()
    assert not janela.recovery.exists
    janela.editor.create("ent", 50, 50)
    janela.save_recovery()
    assert janela.recovery.exists
    assert janela.recovery.path.parent == recovery_dir()
    assert len(io.load(janela.recovery.path).figures) == len(janela.editor.document.figures)


def test_salvar_apaga_a_copia_e_nao_mexe_no_original_antes(qtbot, tmp_path):
    janela = _janela_alterada(qtbot)
    destino = tmp_path / "modelo.xml"
    assert janela._write(destino)
    janela.editor.create("ent", 200, 50)
    antes = destino.read_bytes()
    janela.save_recovery()
    assert janela.recovery.exists
    assert destino.read_bytes() == antes  # a cópia nunca grava no arquivo do usuário
    assert janela.save()
    assert not janela.recovery.exists


def test_fechar_descartando_apaga_a_copia(qtbot, monkeypatch):
    janela = _janela_alterada(qtbot)
    janela.save_recovery()
    monkeypatch.setattr(janela, "_confirm_discard", lambda: True)
    janela.close()
    assert not janela.recovery.exists
    assert leftovers() == []


def test_copia_de_janela_aberta_nao_e_oferecida(qtbot):
    janela = _janela_alterada(qtbot)
    janela.save_recovery()
    assert leftovers() == []


def test_sobra_de_fechamento_repentino_e_recuperada(qtbot, tmp_path):
    janela = _janela_alterada(qtbot)
    original = tmp_path / "modelo.xml"
    janela.path = original
    janela.save_recovery()
    _fecha_sem_apagar(janela)
    sobras = leftovers()
    assert [s.original for s in sobras] == [original]

    nova = DocumentWindow()
    qtbot.addWidget(nova)
    assert nova.restore(sobras[0])
    assert nova.path == original
    assert nova.editor.history.is_dirty
    assert not original.exists()  # o original só muda ao salvar
    assert not sobras[0].copy.exists()  # a cópia antiga virou a da janela nova
    assert nova.recovery.exists
    assert leftovers() == []


def test_pergunta_ao_abrir(qtbot, monkeypatch):
    janela = _janela_alterada(qtbot)
    janela.save_recovery()
    _fecha_sem_apagar(janela)
    gerenciador = aplicativo.WindowManager()
    gerenciador.new_window()
    qtbot.addWidget(gerenciador.windows[0])

    monkeypatch.setattr(aplicativo, "recovery_question", lambda sobras: "depois")
    aplicativo.offer_recovery(gerenciador)
    assert len(leftovers()) == 1  # Esc ou Decidir depois não apaga nada

    monkeypatch.setattr(aplicativo, "recovery_question", lambda sobras: "recuperar")
    aplicativo.offer_recovery(gerenciador)
    assert len(gerenciador.windows) == 1  # usou a janela vazia
    assert gerenciador.windows[0].editor.history.is_dirty
    assert leftovers() == []


def test_descartar_ao_abrir_apaga(qtbot, monkeypatch):
    copia = RecoveryCopy()
    janela = _janela_alterada(qtbot)
    copia.write(janela.editor.document, None)
    copia._trava.unlock()
    monkeypatch.setattr(aplicativo, "recovery_question", lambda sobras: "descartar")
    aplicativo.offer_recovery(aplicativo.WindowManager())
    assert leftovers() == []
    assert not copia.path.exists()


def test_preferencias_mudam_o_intervalo_e_restaurar_volta_a_um(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    dialogo = PreferencesDialog(janela)
    qtbot.addWidget(dialogo)
    dialogo.recovery_box.setValue(5)
    assert recovery_interval() == 5
    assert janela._recovery_timer.interval() == 5 * 60_000
    dialogo.recovery_box.setValue(0)
    assert dialogo.recovery_box.text() == "Desligada"
    assert not janela._recovery_timer.isActive()
    dialogo.restore_defaults()
    assert recovery_interval() == 1
