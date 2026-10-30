"""Edição rápida: atalhos de uma tecla para as ferramentas."""

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit, QMessageBox

from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.gui.settings import quick_edit_enabled
from haradaer.gui.shortcuts import FAMILIES, next_tool
from haradaer.gui.view import SELECT, Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    j.view.setFocus()
    return j


def tecla(janela, k, shift=False):
    mod = Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    QTest.keyClick(janela.view, k, mod)


def clicar(janela, x, y):
    pos = janela.view.mapFromScene(QPointF(x, y))
    QTest.mouseClick(janela.view.viewport(), Qt.MouseButton.LeftButton, pos=pos)


def fechar_campo(janela):
    # O campo anterior só é apagado depois (`deleteLater`): o aberto é o visível.
    for campo in janela.view.viewport().findChildren(QLineEdit):
        if campo.isVisible():
            QTest.keyClick(campo, Qt.Key.Key_Return)


def nos(janela):
    return [f for f in janela._editor.document.figures if isinstance(f, NodeFigure)]


def test_cada_ferramenta_tem_uma_tecla_so():
    todas = [t for _, ferramentas in FAMILIES for t in ferramentas]
    assert len(todas) == len(set(todas)) == 22


def test_a_mesma_tecla_passa_para_o_proximo_tipo_e_o_shift_volta():
    entidade, fraca, associativa = (Tool("create", t) for t in ("ent", "entfraca", "entrel"))
    assert next_tool("e", SELECT) == entidade
    assert next_tool("E", entidade) == fraca
    assert next_tool("E", associativa) == entidade
    assert next_tool("E", entidade, voltar=True) == associativa
    assert next_tool("Q", SELECT) is None


def test_desligada_as_letras_nao_fazem_nada(janela):
    tecla(janela, Qt.Key.Key_E)
    assert janela.view.tool == SELECT


def test_ligar_e_lembrado_e_a_letra_vai_para_a_dica(janela):
    janela.action_quick_edit.setChecked(True)
    assert quick_edit_enabled()
    acao = janela._tool_actions[Tool("create", "ent")]
    assert acao.toolTip().endswith("(E)")
    janela.action_quick_edit.setChecked(False)
    assert "(E)" not in acao.toolTip()


def test_indicador_na_barra_de_status_liga_e_desliga(janela):
    botao = janela._quick_edit_button
    assert botao.isVisible() and not botao.isChecked()
    botao.click()
    assert janela.action_quick_edit.isChecked() and janela.view.quick_edit
    botao.click()
    assert not janela.view.quick_edit


def test_letra_da_familia_troca_o_tipo_do_selecionado(janela):
    janela.action_quick_edit.setChecked(True)
    atributo = janela._editor.create("atr", 200, 200)
    janela.diagram_scene.select_only(atributo)
    tecla(janela, Qt.Key.Key_A)
    assert atributo.tag == "atrchave" and janela.view.tool == SELECT
    tecla(janela, Qt.Key.Key_A, shift=True)
    assert atributo.tag == "atr"
    tecla(janela, Qt.Key.Key_E)  # outra família: escolhe a ferramenta
    assert atributo.tag == "atr" and janela.view.tool == Tool("create", "ent")


def test_com_ferramenta_de_criar_a_letra_so_troca_a_ferramenta(janela):
    janela.action_quick_edit.setChecked(True)
    entidade = janela._editor.create("ent", 200, 200)
    janela.view.set_tool(Tool("create", "ent"))
    janela.diagram_scene.select_only(entidade)
    tecla(janela, Qt.Key.Key_E)
    assert entidade.tag == "ent" and janela.view.tool == Tool("create", "entfraca")


def test_letras_escolhem_e_trocam_a_ferramenta(janela):
    janela.action_quick_edit.setChecked(True)
    tecla(janela, Qt.Key.Key_E)
    assert janela.view.tool == Tool("create", "ent")
    tecla(janela, Qt.Key.Key_E)
    assert janela.view.tool == Tool("create", "entfraca")
    tecla(janela, Qt.Key.Key_E, shift=True)
    assert janela.view.tool == Tool("create", "ent")
    tecla(janela, Qt.Key.Key_N)
    assert janela.view.tool == Tool("connect", "llabelMuitos")
    tecla(janela, Qt.Key.Key_V)
    assert janela.view.tool == SELECT


def test_ligada_a_ferramenta_continua_depois_de_criar(janela):
    janela.action_quick_edit.setChecked(True)
    tecla(janela, Qt.Key.Key_E)
    clicar(janela, 100, 100)
    fechar_campo(janela)
    clicar(janela, 300, 100)
    fechar_campo(janela)
    assert len(nos(janela)) == 2
    assert janela.view.tool == Tool("create", "ent")


def test_a_com_uma_entidade_selecionada_cria_o_atributo_ligado(janela):
    janela.action_quick_edit.setChecked(True)
    entidade = janela._editor.create("ent", 200, 200)
    janela.diagram_scene.select_only(entidade)
    for _ in range(2):
        tecla(janela, Qt.Key.Key_A)
        fechar_campo(janela)
    atributos = [n for n in nos(janela) if n.tag == "atr"]
    ligacoes = [f for f in janela._editor.document.figures if isinstance(f, ConnectionFigure)]
    assert len(atributos) == 2 and len(ligacoes) == 2
    assert all(c.tag == "lcaf" for c in ligacoes)
    assert janela.diagram_scene.selected_figures() == [entidade]
    janela._editor.history.undo()
    assert len([n for n in nos(janela) if n.tag == "atr"]) == 1  # criar e ligar: um passo


def test_tecla_de_conexao_liga_os_dois_selecionados(janela):
    janela.action_quick_edit.setChecked(True)
    entidade = janela._editor.create("ent", 100, 200)
    relacao = janela._editor.create("rel", 300, 200)
    janela.diagram_scene.select_where(lambda f: f is entidade or f is relacao)
    tecla(janela, Qt.Key.Key_N)
    ligacoes = [f for f in janela._editor.document.figures if isinstance(f, ConnectionFigure)]
    assert [c.tag for c in ligacoes] == ["llabelMuitos"]


def test_ctrl_com_letra_nao_e_atalho_da_edicao_rapida(janela):
    janela.action_quick_edit.setChecked(True)
    QTest.keyClick(janela.view, Qt.Key.Key_E, Qt.KeyboardModifier.AltModifier)
    assert janela.view.tool == SELECT


def test_atalhos_do_teclado_lista_menus_edicao_rapida_e_busca(janela):
    dialogo = janela.show_shortcuts()
    linhas = dialogo.visible_rows()
    textos = [a for a, _ in linhas]
    nativo = QKeySequence("Ctrl+Shift+E").toString(QKeySequence.SequenceFormat.NativeText)
    assert ("Edição rápida", nativo) in linhas  # ⇧⌘E no Mac
    assert any(t == "E" for _, t in linhas)
    assert "Mouse e gestos" in textos
    dialogo.search.setText("duplicar")
    assert [a for a, t in dialogo.visible_rows() if t] == ["Duplicar"]
    dialogo.close()


def test_menu_do_elemento_troca_o_tipo_com_qualquer_ferramenta(janela):
    atributo = janela._editor.create("atr", 200, 200)
    janela.view.set_tool(Tool("create", "ent"))
    menu = janela.view.node_menu(atributo)
    acoes = menu.actions()[0].menu().actions()
    assert len(acoes) == 5
    assert [a.isChecked() for a in acoes] == [True, False, False, False, False]
    acoes[1].trigger()
    assert atributo.tag == "atrchave"
    janela._editor.history.undo()
    assert atributo.tag == "atr"


def test_menu_mostra_a_letra_so_com_a_edicao_rapida(janela):
    entidade = janela._editor.create("ent", 200, 200)
    assert "\t" not in janela.view.node_menu(entidade).actions()[0].menu().actions()[0].text()
    janela.action_quick_edit.setChecked(True)
    assert janela.view.node_menu(entidade).actions()[0].menu().actions()[0].text().endswith("\tE")


def test_elemento_sem_familia_nao_tem_menu(janela):
    assert janela.view.node_menu(janela._editor.create("ent", 0, 0)) is not None
    grupo_falso = janela._editor.create("atr", 0, 0)
    grupo_falso.tag = "g"
    assert janela.view.node_menu(grupo_falso) is None


def test_trocar_para_derivado_pergunta_e_nao_troca_se_recusar(janela, monkeypatch):
    atributo = janela._editor.create("atr", 200, 200)
    perguntas = []

    def responder(*a, **k):
        perguntas.append(a)
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", responder)
    janela.view.change_type(atributo, "atrderivado")
    assert perguntas and atributo.tag == "atr"
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    janela.view.change_type(atributo, "atrderivado")
    assert atributo.tag == "atrderivado"
