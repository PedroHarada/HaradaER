"""Alças de redimensionar, grade, empilhamento, alinhamento e seleção por tipo (M5b)."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit, QMessageBox

from haradaer.core.geometry import node_rect
from haradaer.gui.view import GRID_SIZE, Tool, resized_rect
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.resize(1000, 700)
    j.show()
    return j


def ponto(janela, x, y) -> QPoint:
    return janela.view.mapFromScene(QPointF(x, y))


def arrastar(janela, de, para, passos=6):
    viewport = janela.view.viewport()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *de))
    for i in range(1, passos + 1):
        x = de[0] + (para[0] - de[0]) * i / passos
        y = de[1] + (para[1] - de[1]) * i / passos
        QTest.mouseMove(viewport, ponto(janela, x, y))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *para))


def centro_da_alca(janela, nome):
    return janela.view.handle_rects()[nome].center().toTuple()


# ------------------------------------------------------------- alças


def test_alcas_aparecem_so_com_um_elemento_selecionado(janela):
    a = janela.editor.create("ent", 150, 150)
    b = janela.editor.create("rel", 400, 150)
    assert janela.view.handle_rects() == {}
    janela.diagram_scene.select_only(a)
    assert set(janela.view.handle_rects()) == {"nw", "n", "ne", "e", "se", "s", "sw", "w"}
    janela.diagram_scene.item_for(b).setSelected(True)
    assert janela.view.handle_rects() == {}


def test_arrastar_a_alca_redimensiona_e_desfazer_volta_num_passo(janela):
    no = janela.editor.create("ent", 150, 150)
    janela.diagram_scene.select_only(no)
    x, y, w, h = node_rect(no)
    arrastar(janela, centro_da_alca(janela, "se"), (x + w + 60, y + h + 30))
    nx, ny, nw, nh = node_rect(no)
    assert (nx, ny) == pytest.approx((x, y))
    assert (nw, nh) == pytest.approx((w + 60, h + 30), abs=1.5)
    assert janela.editor.history.undo_label == "Redimensionar"
    janela.editor.history.undo()
    assert node_rect(no) == pytest.approx((x, y, w, h))


def test_alca_do_lado_esquerdo_mexe_so_a_borda_esquerda(janela):
    no = janela.editor.create("ent", 200, 150)
    janela.diagram_scene.select_only(no)
    x, y, w, h = node_rect(no)
    arrastar(janela, centro_da_alca(janela, "w"), (x - 50, y + 100))
    nx, ny, nw, nh = node_rect(no)
    assert nx + nw == pytest.approx(x + w)
    assert nx == pytest.approx(x - 50, abs=1.5)
    assert (ny, nh) == (y, h)


def test_caixa_redimensionada_respeita_o_minimo_e_prende_o_lado_oposto():
    original = (100.0, 100.0, 80.0, 40.0)
    assert resized_rect(original, "nw", 500, 500, (60, 20)) == (120, 120, 60, 20)
    assert resized_rect(original, "se", 0, 0, (60, 20)) == (100, 100, 60, 20)
    assert resized_rect(original, "n", 999, 50, (60, 20)) == (100, 50, 80, 90)


# ------------------------------------------------------------- grade


def na_grade(valor) -> bool:
    return abs(valor / GRID_SIZE - round(valor / GRID_SIZE)) < 1e-6


def test_grade_encaixa_criar_mover_e_redimensionar(janela):
    janela.action_grid.setChecked(True)
    assert janela.view.grid == GRID_SIZE
    janela.view.set_tool(Tool("create", "ent"))
    QTest.mouseClick(janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, 203, 147))
    campo = next(c for c in janela.view.viewport().findChildren(QLineEdit) if c.isVisible())
    QTest.keyClick(campo, Qt.Key.Key_Escape)
    no = janela.editor.document.figures[-1]
    x, y, w, h = node_rect(no)
    assert (x + w / 2, y + h / 2) == pytest.approx((200, 150))

    arrastar(janela, (x + w / 2, y + h / 2), (x + w / 2 + 33, y + h / 2 + 18))
    x, y, w, h = node_rect(no)
    assert na_grade(x) and na_grade(y)

    janela.diagram_scene.select_only(no)
    arrastar(janela, centro_da_alca(janela, "se"), (x + w + 27, y + h + 13))
    _, _, w, h = node_rect(no)
    assert na_grade(x + w) and na_grade(y + h)


def test_grade_comeca_desligada(janela):
    assert not janela.action_grid.isChecked() and janela.view.grid is None


# ------------------------------------------------------------- menus


def test_trazer_para_a_frente_e_enviar_para_tras_pelo_menu(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("ent", 120, 110)
    cena = janela.diagram_scene
    cena.select_only(a)
    janela.action_front.trigger()
    assert janela.editor.document.figures == [b, a]
    assert cena.item_for(a).zValue() > cena.item_for(b).zValue()
    janela.action_back.trigger()
    assert janela.editor.document.figures == [a, b]
    assert cena.item_for(a).zValue() < cena.item_for(b).zValue()


def test_alinhar_pelo_menu(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("atr", 260, 300)
    janela.diagram_scene.select_where(lambda f: True)
    janela.align_actions["top"].trigger()
    assert node_rect(a)[1] == node_rect(b)[1]
    assert janela.editor.history.undo_label == "Alinhar"


def test_selecionar_do_mesmo_tipo(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("ent", 300, 100)
    c = janela.editor.create("rel", 200, 300)
    janela.diagram_scene.select_only(a)
    janela.action_select_same.trigger()
    assert set(map(id, janela.diagram_scene.selected_figures())) == {id(a), id(b)}
    janela.action_select_all.trigger()
    assert len(janela.diagram_scene.selected_figures()) == 3
    assert c in janela.diagram_scene.selected_figures()
