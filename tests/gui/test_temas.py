"""Temas claro e escuro."""

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.core.appearance import PolylineOp, ShapeOp, TextOp
from haradaer.core.appearance.style import BLACK
from haradaer.gui.export import render_image
from haradaer.gui.theme import DARK, LIGHT, apply_theme, current_theme, saved_theme
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    ent = j.editor.create("ent", 100, 300)
    rel = j.editor.create("rel", 100, 80)
    j.editor.connect("llabelMuitos", ent, rel)
    return j


def item(janela, tag):
    figura = next(f for f in janela.editor.document.figures if f.tag == tag)
    return janela.diagram_scene.item_for(figura)


def test_escuro_pelo_menu_muda_paleta_fundo_e_menu(janela):
    janela.theme_actions["escuro"].trigger()
    assert current_theme() is DARK
    assert QApplication.palette().window().color().lightness() < 80
    assert janela.diagram_scene.backgroundBrush().color() == DARK.canvas
    assert janela.theme_actions["escuro"].isChecked()
    janela.theme_actions["claro"].trigger()
    assert QApplication.palette().window().color().lightness() > 200
    assert janela.diagram_scene.backgroundBrush().color() == LIGHT.canvas


def test_no_escuro_linhas_e_rotulos_clareiam_e_o_texto_das_formas_fica_preto(janela):
    apply_theme(DARK, save=False)
    conexao = item(janela, "llabelMuitos")._themed_ops(DARK)
    assert {op.stroke.color for op in conexao if isinstance(op, PolylineOp)} == {DARK.ink}
    assert {op.color for op in conexao if isinstance(op, TextOp)} == {DARK.ink}  # o "N"
    entidade = item(janela, "ent")._themed_ops(DARK)
    assert {op.color for op in entidade if isinstance(op, TextOp)} == {BLACK}
    assert any(isinstance(op, ShapeOp) for op in entidade)


def test_exportar_no_escuro_sai_no_claro(janela):
    claro = render_image(janela.diagram_scene)
    apply_theme(DARK, save=False)
    escuro = render_image(janela.diagram_scene)
    assert QColor(escuro.pixel(2, 2)) == QColor("white")
    assert escuro == claro


def test_icones_da_faixa_seguem_o_tema(janela):
    acao = next(a for t, a in janela._tool_actions.items() if t.tag == "llabelMuitos")
    antes = acao.icon().cacheKey()
    apply_theme(DARK, save=False)
    assert acao.icon().cacheKey() != antes


def test_tema_escolhido_e_lembrado(janela, qtbot):
    janela.theme_actions["escuro"].trigger()
    assert saved_theme() is DARK
    outra = DocumentWindow()
    qtbot.addWidget(outra)
    assert outra.theme_actions["escuro"].isChecked()


def test_ferramenta_escolhida_nao_fica_clara_no_escuro(janela):
    """Os destaques da faixa seguem o tema (o Qt não refaz as cores da folha de estilo sozinho)."""
    botao = janela.tool_strip.button_for(next(iter(janela._tool_actions.values())))

    def fundo():
        QApplication.processEvents()
        return QColor(botao.grab().toImage().pixel(3, botao.height() // 2)).lightness()

    claro = fundo()
    apply_theme(DARK, save=False)
    assert fundo() < 110
    apply_theme(LIGHT, save=False)
    assert fundo() == claro
