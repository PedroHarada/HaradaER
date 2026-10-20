"""Copiar, colar, duplicar, agrupar e desagrupar pela interface (RF-03)."""

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox

from haradaer.core.commands import all_nodes
from haradaer.core.geometry import node_rect
from haradaer.gui.view import Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


def nova_janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    return j


@pytest.fixture
def cena(qtbot):
    j = nova_janela(qtbot)
    ent = j.editor.create("ent", 150, 350)
    rel = j.editor.create("rel", 150, 100)
    fora = j.editor.create("ent", 450, 350)
    j.editor.connect("llabelUm", ent, rel)
    return j, ent, rel, fora


def selecionar(janela, *figuras):
    chaves = {id(f) for f in figuras}
    janela.diagram_scene.select_where(lambda f: id(f) in chaves)


def ponto(janela, x, y):
    return janela.view.mapFromScene(QPointF(x, y))


# ------------------------------------------------------------- copiar e colar


def test_copiar_e_colar_seleciona_as_copias_deslocadas(cena):
    janela, ent, rel, _ = cena
    selecionar(janela, ent, rel)
    assert janela.action_copy.isEnabled() and janela.copy()
    total = len(janela.editor.document.figures)
    assert janela.paste()
    figuras = janela.editor.document.figures
    assert len(figuras) == total + 3  # ent, rel e a conexão entre eles
    novas = janela.diagram_scene.selected_figures()
    assert [f.tag for f in novas] == ["ent", "rel", "llabelUm"]
    assert node_rect(novas[0])[0] == node_rect(ent)[0] + 20
    janela.paste()  # de novo: mais 20
    assert node_rect(janela.diagram_scene.selected_figures()[0])[0] == node_rect(ent)[0] + 40
    janela.action_undo.trigger()
    janela.action_undo.trigger()
    assert len(janela.editor.document.figures) == total


def test_colar_em_outra_janela(cena, qtbot):
    janela, ent, rel, _ = cena
    selecionar(janela, ent, rel)
    janela.action_copy.trigger()
    outra = nova_janela(qtbot)
    outra.action_paste.trigger()
    assert [f.tag for f in outra.editor.document.figures] == ["ent", "rel", "llabelUm"]
    assert outra.isWindowModified()


def test_recortar_tira_e_colar_devolve(cena):
    janela, ent, rel, fora = cena
    selecionar(janela, fora)
    janela.action_cut.trigger()
    assert fora not in janela.editor.document.figures
    janela.action_paste.trigger()
    assert [f.tag for f in janela.editor.document.figures].count("ent") == 2


def test_duplicar(cena):
    janela, ent, *_ = cena
    selecionar(janela, ent)
    janela.action_duplicate.trigger()
    copia = janela.diagram_scene.selected_figures()[0]
    assert copia is not ent and copia.name == ent.name


def test_colar_algo_que_nao_e_modelo_nao_faz_nada(cena):
    janela, *_ = cena
    dados = QMimeData()
    dados.setText("texto qualquer")
    QApplication.clipboard().setMimeData(dados)
    total = len(janela.editor.document.figures)
    assert not janela.paste()
    assert len(janela.editor.document.figures) == total


def test_ctrl_c_no_campo_de_nome_continua_copiando_texto(cena):
    janela, ent, *_ = cena
    QTest.mouseDClick(
        janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, 150, 350)
    )
    campo = next(c for c in janela.view.viewport().findChildren(QLineEdit) if c.isVisible())
    campo.selectAll()
    QTest.keyClick(campo, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert QApplication.clipboard().text() == ent.name
    total = len(janela.editor.document.figures)
    QTest.keyClick(campo, Qt.Key.Key_Escape)
    assert len(janela.editor.document.figures) == total


# ------------------------------------------------------------- agrupar


def test_agrupar_e_desagrupar_pelo_menu(cena):
    janela, ent, rel, fora = cena
    selecionar(janela, ent, rel)
    janela.action_group.trigger()
    selecionadas = janela.diagram_scene.selected_figures()
    assert [f.tag for f in selecionadas] == ["g"]
    assert len(janela.diagram_scene.figure_items()) == 3  # fora, conexão, grupo
    janela.action_ungroup.trigger()
    assert {f.tag for f in janela.diagram_scene.selected_figures()} == {"ent", "rel"}
    assert len(janela.diagram_scene.figure_items()) == 4


def test_agrupar_uma_figura_so_nao_faz_nada(cena):
    janela, ent, *_ = cena
    selecionar(janela, ent)
    janela.action_group.trigger()
    assert all(f.tag != "g" for f in janela.editor.document.figures)


def test_elementos_do_grupo_continuam_conectaveis_e_renomeaveis(cena):
    janela, ent, rel, fora = cena
    selecionar(janela, ent, rel)
    janela.action_group.trigger()
    # conectar a partir de um elemento de dentro do grupo
    janela.view.set_tool(Tool("connect", "llabelMuitos"))
    viewport = janela.view.viewport()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, 450, 350))
    QTest.mouseMove(viewport, ponto(janela, 300, 200))
    QTest.mouseMove(viewport, ponto(janela, 150, 100))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, 150, 100))
    nova = janela.editor.document.figures[-1]
    assert nova.tag == "llabelMuitos" and {nova.start, nova.end} == {rel, fora}
    # renomear com duplo clique um elemento de dentro do grupo
    QTest.mouseDClick(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, 150, 350))
    campo = next(c for c in viewport.findChildren(QLineEdit) if c.isVisible())
    campo.setText("Aluno")
    QTest.keyClick(campo, Qt.Key.Key_Return)
    assert ent.name == "Aluno"


def test_inspetor_mostra_e_localiza_elementos_dentro_do_grupo(cena):
    janela, ent, rel, _ = cena
    selecionar(janela, ent, rel)
    janela.action_group.trigger()
    janela.diagram_scene.clearSelection()
    janela.inspector.search.setText("relacion")
    assert janela.inspector.matches() == [rel]
    janela.locate(rel)
    assert [f.tag for f in janela.diagram_scene.selected_figures()] == ["g"]
    assert len(all_nodes(janela.editor.document)) == 3
