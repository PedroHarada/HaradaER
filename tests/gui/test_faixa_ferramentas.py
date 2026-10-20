"""Faixa de ferramentas que rola na horizontal, em vez do menu "»" que escondia botões."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.gui.view import Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


def janela_com_largura(qtbot, largura):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.resize(largura, 700)
    j.show()
    QApplication.processEvents()
    return j


def rodar(faixa, dy=0, dx=0, pixels=False):
    viewport = faixa.scroll.viewport()
    centro = QPointF(viewport.width() / 2, viewport.height() / 2)
    evento = QWheelEvent(
        centro,
        viewport.mapToGlobal(centro),
        QPoint(dx, dy) if pixels else QPoint(),
        QPoint() if pixels else QPoint(dx, dy),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(viewport, evento)


def posicao(faixa):
    return faixa.scroll.horizontalScrollBar().value()


def test_tudo_numa_linha_so_e_a_barra_nao_sai_do_lugar(qtbot):
    j = janela_com_largura(qtbot, 900)
    assert not j.tool_bar.isMovable()
    alturas = {j.tool_strip.button_for(a).geometry().top() for a in j._tool_actions.values()}
    assert len(alturas) == 1


def test_janela_estreita_mostra_as_setas_e_rola(qtbot):
    j = janela_com_largura(qtbot, 900)
    faixa = j.tool_strip
    assert faixa.overflows()
    assert faixa.left.isVisible() and faixa.right.isVisible()
    assert not faixa.left.isEnabled()  # já está no começo
    faixa.right.click()
    assert posicao(faixa) > 0
    assert faixa.left.isEnabled()
    faixa.left.click()
    assert posicao(faixa) == 0


def test_roda_do_mouse_rola_para_os_lados(qtbot):
    j = janela_com_largura(qtbot, 900)
    faixa = j.tool_strip
    rodar(faixa, dy=-120)  # roda para baixo: anda para a direita
    assert posicao(faixa) > 0
    rodar(faixa, dy=240)
    assert posicao(faixa) == 0


def test_dois_dedos_no_trackpad_rolam_para_os_lados(qtbot):
    j = janela_com_largura(qtbot, 900)
    faixa = j.tool_strip
    rodar(faixa, dx=-80, pixels=True)
    assert posicao(faixa) == 80


def test_escolher_uma_ferramenta_escondida_rola_ate_ela(qtbot):
    j = janela_com_largura(qtbot, 900)
    faixa = j.tool_strip
    j.view.set_tool(Tool("connect", "llabel"))  # a última da faixa
    botao = faixa.button_for(j._tool_actions[Tool("connect", "llabel")])
    visivel = faixa.scroll.viewport().rect()
    canto = botao.mapTo(faixa.scroll.viewport(), botao.rect().topRight())
    assert visivel.contains(canto)


def test_quando_tudo_cabe_as_setas_somem(qtbot):
    """Só a faixa, com poucos botões: não depende do tamanho da tela do sistema."""
    from PySide6.QtGui import QAction

    from haradaer.gui.tool_strip import ToolStrip

    faixa = ToolStrip()
    qtbot.addWidget(faixa)
    for nome in ("A", "B"):
        faixa.add_action(QAction(nome, faixa))
    faixa.finish()
    faixa.resize(600, faixa.height())
    faixa.show()
    QApplication.processEvents()
    assert not faixa.overflows()
    assert not faixa.left.isVisible() and not faixa.right.isVisible()


def test_disposicao_salva_nao_mexe_na_faixa(qtbot):
    primeira = janela_com_largura(qtbot, 900)
    primeira.close()  # grava a disposição
    segunda = janela_com_largura(qtbot, 900)
    assert segunda.toolBarArea(segunda.tool_bar) == Qt.ToolBarArea.TopToolBarArea
    assert segunda.tool_bar.isVisible()
