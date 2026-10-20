"""Edição pela interface: criar, mover, conectar, renomear, excluir, desfazer, salvar (M4)."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit, QMessageBox

from haradaer.core import io
from haradaer.core.geometry import node_rect
from haradaer.gui.view import SELECT, Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    """Ao fechar uma janela modificada ao fim do teste, descarta sem abrir a pergunta."""
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    return j


def ponto(janela, x, y) -> QPoint:
    """Posição na tela (viewport) de um ponto da cena."""
    return janela.view.mapFromScene(QPointF(x, y))


def clicar(janela, x, y, **kw):
    QTest.mouseClick(
        janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, x, y), **kw
    )


def arrastar(janela, de, para, passos=6):
    viewport = janela.view.viewport()
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *de))
    for i in range(1, passos + 1):
        x = de[0] + (para[0] - de[0]) * i / passos
        y = de[1] + (para[1] - de[1]) * i / passos
        QTest.mouseMove(viewport, ponto(janela, x, y))
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=ponto(janela, *para))


def campo_aberto(janela):
    """O campo de texto flutuante visível, ou `None` (o escondido só some no próximo ciclo)."""
    abertos = [c for c in janela.view.viewport().findChildren(QLineEdit) if c.isVisible()]
    return abertos[0] if abertos else None


def criar(janela, tag, x, y, nome=None):
    janela.view.set_tool(Tool("create", tag))
    clicar(janela, x, y)
    campo = campo_aberto(janela)
    assert campo is not None, "o campo do nome abre logo depois de criar"
    if nome is not None:
        campo.setText(nome)
    QTest.keyClick(campo, Qt.Key.Key_Return)
    return janela.editor.document.figures[-1]


def test_clicar_com_a_ferramenta_de_criar_cria_o_elemento_e_volta_a_selecionar(janela):
    janela.view.set_tool(Tool("create", "ent"))
    clicar(janela, 200, 150)
    QTest.keyClick(campo_aberto(janela), Qt.Key.Key_Escape)
    figuras = janela.editor.document.figures
    assert [f.tag for f in figuras] == ["ent"]
    x, y, w, h = node_rect(figuras[0])
    assert (x + w / 2, y + h / 2) == pytest.approx((200, 150), abs=1)
    assert janela.view.tool == SELECT
    assert janela.isWindowModified()
    assert len(janela.diagram_scene.figure_items()) == 1


def test_nome_digitado_ao_criar_vai_para_o_modelo(janela):
    no = criar(janela, "ent", 200, 150, "Aluno")
    assert no.name == "Aluno"
    assert campo_aberto(janela) is None


def test_esc_no_campo_do_nome_mantem_o_nome_padrao(janela):
    janela.view.set_tool(Tool("create", "atr"))
    clicar(janela, 100, 100)
    campo = campo_aberto(janela)
    campo.setText("descartado")
    QTest.keyClick(campo, Qt.Key.Key_Escape)
    assert janela.editor.document.figures[0].name == "Atributo"


def test_duplo_clique_edita_o_nome(janela):
    criar(janela, "ent", 200, 150, "Aluno")
    QTest.mouseDClick(
        janela.view.viewport(), Qt.MouseButton.LeftButton, pos=ponto(janela, 200, 150)
    )
    campo = campo_aberto(janela)
    assert campo is not None and campo.text() == "Aluno"
    campo.setText("Estudante")
    QTest.keyClick(campo, Qt.Key.Key_Return)
    assert janela.editor.document.figures[0].name == "Estudante"


def test_arrastar_move_o_elemento_e_um_desfazer_volta_tudo(janela):
    no = criar(janela, "ent", 200, 150, "Aluno")
    antes = node_rect(no)
    clicar(janela, 200, 150)
    arrastar(janela, (200, 150), (320, 230))
    depois = node_rect(no)
    assert depois[0] - antes[0] == pytest.approx(120, abs=2)
    assert depois[1] - antes[1] == pytest.approx(80, abs=2)
    janela.editor.history.undo()
    assert node_rect(no) == pytest.approx(antes)


def test_arrastar_leva_a_conexao_junto(janela):
    a = criar(janela, "ent", 100, 100, "A")
    r = criar(janela, "rel", 400, 100, "R")
    janela.view.set_tool(Tool("connect", "llabelUm"))
    arrastar(janela, (100, 100), (400, 100))
    conexao = janela.editor.document.figures[-1]
    antes = [float(p.attrs["y"]) for p in conexao.points]
    clicar(janela, 100, 100)
    arrastar(janela, (100, 100), (100, 250))
    depois = [float(p.attrs["y"]) for p in conexao.points]
    assert depois != antes
    assert (conexao.start, conexao.end) == (a, r)


def test_conectar_arrastando_de_um_elemento_a_outro(janela):
    a = criar(janela, "ent", 100, 100, "A")
    r = criar(janela, "rel", 400, 100, "R")
    janela.view.set_tool(Tool("connect", "llabelMuitos"))
    arrastar(janela, (100, 100), (400, 100))
    conexao = janela.editor.document.figures[-1]
    assert conexao.tag == "llabelMuitos"
    assert (conexao.start, conexao.end) == (a, r)
    assert janela.view.tool == SELECT
    assert janela.view._preview is None


def test_soltar_fora_de_um_elemento_cancela_a_conexao(janela):
    criar(janela, "ent", 100, 100, "A")
    janela.view.set_tool(Tool("connect", "llabelUm"))
    arrastar(janela, (100, 100), (500, 400))
    assert [f.tag for f in janela.editor.document.figures] == ["ent"]
    assert janela.view._preview is None


def test_conexao_invalida_e_criada_e_avisada_durante_o_arrasto(janela):
    criar(janela, "ent", 100, 100, "A")
    criar(janela, "ent", 400, 100, "B")
    mensagens = []
    janela.view.message.connect(mensagens.append)
    janela.view.set_tool(Tool("connect", "lcaf"))
    arrastar(janela, (100, 100), (400, 100))
    assert janela.editor.document.figures[-1].tag == "lcaf"
    assert any("não é aceita" in m for m in mensagens)


def test_excluir_elemento_leva_as_conexoes_e_desfazer_traz_de_volta(janela):
    criar(janela, "ent", 100, 100, "A")
    criar(janela, "rel", 400, 100, "R")
    janela.view.set_tool(Tool("connect", "llabelUm"))
    arrastar(janela, (100, 100), (400, 100))
    clicar(janela, 100, 100)
    QTest.keyClick(janela.view, Qt.Key.Key_Delete)
    assert [f.tag for f in janela.editor.document.figures] == ["rel"]
    janela.editor.history.undo()
    assert [f.tag for f in janela.editor.document.figures] == ["ent", "rel", "llabelUm"]
    assert len(janela.diagram_scene.figure_items()) == 3


def test_esc_volta_para_a_ferramenta_de_selecionar(janela):
    janela.view.set_tool(Tool("connect", "lcaf"))
    QTest.keyClick(janela.view, Qt.Key.Key_Escape)
    assert janela.view.tool == SELECT


def test_menu_desfazer_e_refazer_acompanham_o_historico(janela):
    assert not janela.action_undo.isEnabled()
    criar(janela, "ent", 100, 100, "A")
    assert janela.action_undo.isEnabled() and not janela.action_redo.isEnabled()
    janela.action_undo.trigger()
    assert janela.editor.document.figures == [] and janela.action_redo.isEnabled()
    janela.action_redo.trigger()
    assert len(janela.editor.document.figures) == 1
    assert len(janela.diagram_scene.figure_items()) == 1


def test_selecionar_com_clique_e_com_laco(janela):
    criar(janela, "ent", 100, 100, "A")
    criar(janela, "ent", 300, 100, "B")
    clicar(janela, 100, 100)
    assert len(janela.diagram_scene.selected_figures()) == 1
    arrastar(janela, (20, 30), (420, 200))
    assert len(janela.diagram_scene.selected_figures()) == 2


# ------------------------------------------------------------- salvar e fechar


def test_salvar_grava_um_arquivo_que_abre_de_volta_igual(janela, tmp_path, monkeypatch):
    criar(janela, "ent", 100, 100, "Aluno")
    criar(janela, "atr", 100, 250, "nome")
    janela.view.set_tool(Tool("connect", "lcaf"))
    arrastar(janela, (100, 250), (100, 100))
    destino = tmp_path / "modelo.xml"
    monkeypatch.setattr(
        "haradaer.gui.window.QFileDialog.getSaveFileName", lambda *a, **k: (str(destino), "")
    )
    assert janela.save()
    assert not janela.isWindowModified()
    relido = io.load(destino)
    assert [f.tag for f in relido.figures] == ["ent", "atr", "lcaf"]
    assert [f.name for f in relido.figures[:2]] == ["Aluno", "nome"]
    assert io.dumps(relido) == io.dumps(janela.editor.document)
    assert janela.windowTitle() == "modelo.xml[*] - HaradaER"


def test_salvar_como_acrescenta_a_extensao(janela, tmp_path, monkeypatch):
    criar(janela, "ent", 100, 100)
    monkeypatch.setattr(
        "haradaer.gui.window.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(tmp_path / "semextensao"), ""),
    )
    assert janela.save_as()
    assert (tmp_path / "semextensao.xml").exists()


def test_editar_um_arquivo_do_terraer_e_salvar_por_cima(qtbot, referencia, tmp_path):
    copia = tmp_path / "amostra.xml"
    copia.write_bytes((referencia / "amostra-basica.xml").read_bytes())
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.show()
    assert janela.load(copia)
    assert not janela.isWindowModified()
    criar(janela, "atr", 300, 300, "idade")
    assert janela.isWindowModified()
    assert janela.save()
    relido = io.load(copia)
    assert relido.figures[-1].name == "idade"
    assert len(relido.figures) == 10


def test_fechar_modificado_pergunta_e_cancelar_mantem_a_janela(janela, monkeypatch):
    criar(janela, "ent", 100, 100)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    assert not janela.close()
    assert janela.isVisible()


def test_fechar_modificado_e_descartar_fecha(janela, monkeypatch):
    criar(janela, "ent", 100, 100)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    assert janela.close()


def test_fechar_sem_modificacao_nao_pergunta(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: chamadas.append(1))
    assert janela.close()
    assert chamadas == []
