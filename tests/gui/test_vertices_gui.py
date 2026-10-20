"""Editar a linha das conexões pela interface: vértices, menu do botão direito e reconectar."""

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from haradaer.core.commands import connection_path
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def cena(qtbot):
    """Entidade embaixo, relacionamento em cima, outra entidade à direita; uma conexão "1"."""
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    aluno = j.editor.create("ent", 150, 350)
    cursa = j.editor.create("rel", 150, 100)
    curso = j.editor.create("ent", 450, 350)
    conexao = j.editor.connect("llabelUm", aluno, cursa)
    j.diagram_scene.select_only(conexao)
    return j, aluno, cursa, curso, conexao


def ponto(janela, x, y):
    return janela.view.mapFromScene(QPointF(x, y))


def arrastar(janela, de, para, passos=5):
    viewport = janela.view.viewport()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *de))
    for i in range(1, passos + 1):
        x = de[0] + (para[0] - de[0]) * i / passos
        y = de[1] + (para[1] - de[1]) * i / passos
        QTest.mouseMove(viewport, ponto(janela, x, y))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *para))


def alca(janela, tipo, indice=0):
    for t, i, quadro in janela.view.connection_handles():
        if (t, i) == (tipo, indice):
            return (quadro.center().x(), quadro.center().y())
    raise AssertionError(f"sem alça {tipo} {indice}")


def test_conexao_selecionada_mostra_pontas_e_meio(cena):
    janela, *_ = cena
    tipos = sorted(t for t, _, _ in janela.view.connection_handles())
    assert tipos == ["end", "mid", "start"]


def test_arrastar_o_meio_cria_um_vertice_num_passo_so(cena):
    janela, *_, conexao = cena
    arrastar(janela, alca(janela, "mid"), (300, 220))
    caminho = connection_path(conexao)
    assert len(caminho) == 3
    assert caminho[1] == pytest.approx((300, 220), abs=1)
    janela.action_undo.trigger()
    assert len(connection_path(conexao)) == 2


def test_arrastar_um_vertice_move_e_duplo_clique_remove(cena):
    janela, *_, conexao = cena
    janela.editor.add_bend(conexao, 0, (300, 220))
    arrastar(janela, (300, 220), (320, 260))
    assert connection_path(conexao)[1] == pytest.approx((320, 260), abs=1)
    QTest.mouseDClick(
        janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, 320, 260)
    )
    assert len(connection_path(conexao)) == 2


def test_duplo_clique_na_linha_cria_vertice_como_no_terraer(cena):
    janela, *_, conexao = cena
    (x1, y1), (x2, y2) = connection_path(conexao)
    meio_de_cima = (x1 + (x2 - x1) * 0.25, y1 + (y2 - y1) * 0.25)
    QTest.mouseDClick(
        janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, *meio_de_cima)
    )
    assert len(connection_path(conexao)) == 3


def test_grade_encaixa_o_vertice(cena):
    janela, *_, conexao = cena
    janela.action_grid.setChecked(True)
    arrastar(janela, alca(janela, "mid"), (303, 217))
    assert connection_path(conexao)[1] == (300, 220)


def test_menu_do_botao_direito(cena):
    janela, *_, conexao = cena
    (x1, y1), (x2, y2) = connection_path(conexao)
    sobre_a_linha = QPointF((x1 + x2) / 2 + 0.5, (y1 + y2) / 2 + 30)
    menu = janela.view.connection_menu(conexao, sobre_a_linha)
    textos = [a.text() for a in menu.actions()]
    assert textos == ["&Adicionar vértice aqui", "&Endireitar linha"]
    assert not menu.actions()[1].isEnabled()
    menu.actions()[0].trigger()
    assert len(connection_path(conexao)) == 3
    vertice = QPointF(*connection_path(conexao)[1])
    menu = janela.view.connection_menu(conexao, vertice)
    assert [a.text() for a in menu.actions()] == ["&Remover vértice", "&Endireitar linha"]
    janela.editor.add_bend(conexao, 0, (40, 200))
    janela.view.connection_menu(conexao, vertice).actions()[1].trigger()
    assert len(connection_path(conexao)) == 2


def test_arrastar_a_ponta_para_outro_elemento_reconecta(cena):
    janela, aluno, cursa, curso, conexao = cena
    assert conexao.end is aluno
    arrastar(janela, alca(janela, "end"), (450, 350))
    assert conexao.end is curso
    assert janela.view._reconnect_preview is None
    janela.action_undo.trigger()
    assert conexao.end is aluno


def test_soltar_a_ponta_no_vazio_nao_muda_nada(cena):
    janela, aluno, *_, conexao = cena
    antes = connection_path(conexao)
    arrastar(janela, alca(janela, "end"), (700, 500))
    assert conexao.end is aluno
    assert connection_path(conexao) == antes
    assert not janela.editor.history.undo_label.startswith("Reconectar")


def test_ponta_nao_vai_para_o_elemento_da_outra_ponta(cena):
    janela, aluno, cursa, _, conexao = cena
    arrastar(janela, alca(janela, "end"), (150, 100))
    assert (conexao.start, conexao.end) == (cursa, aluno)


def test_rotulo_da_generalizacao_continua_editavel_no_duplo_clique(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    ent = j.editor.create("ent", 150, 100)
    gen = j.editor.create("disjuncao", 150, 350)
    conexao = j.editor.connect("llabelGeneralizacao", gen, ent)
    item = j.diagram_scene.item_for(conexao)
    rotulo = next(op for op in item.ops if type(op).__name__ == "TextOp")
    QTest.mouseDClick(
        j.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(j, rotulo.x + 3, rotulo.y + 5)
    )
    assert len(connection_path(conexao)) == 2  # não criou vértice
    assert j.view._inline is not None  # abriu o campo do rótulo
