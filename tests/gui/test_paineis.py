"""M5c na interface: inspetor de objetos, localizar e painel de propriedades."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot, referencia):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    assert j.load(referencia / "amostra-basica.xml")
    return j


def figura(janela, nome):
    return next(f for f in janela.editor.document.figures if getattr(f, "name", None) == nome)


def categorias(janela):
    arvore = janela.inspector.tree
    return {
        arvore.topLevelItem(i).text(0): arvore.topLevelItem(i)
        for i in range(arvore.topLevelItemCount())
    }


def textos_filhos(item):
    return [item.child(i).text(0) for i in range(item.childCount())]


# ------------------------------------------------------------- inspetor


def test_inspetor_agrupa_e_pendura_os_atributos_no_dono(janela):
    grupos = categorias(janela)
    assert set(grupos) == {"Entidades", "Relacionamentos", "Conexões"}
    entidades = grupos["Entidades"]
    assert textos_filhos(entidades) == ["Aluno", "Curso"]
    assert sorted(textos_filhos(entidades.child(0))) == ["att.0", "key att. 0"]
    assert grupos["Conexões"].childCount() == 4
    assert "Aluno — rel. 0" in textos_filhos(grupos["Conexões"])


def test_escolher_na_arvore_seleciona_no_desenho_e_vice_versa(janela):
    curso = categorias(janela)["Entidades"].child(1)
    curso.setSelected(True)
    assert [f.name for f in janela.diagram_scene.selected_figures()] == ["Curso"]
    janela.diagram_scene.select_only(figura(janela, "Aluno"))
    selecionados = janela.inspector.tree.selectedItems()
    assert [i.text(0) for i in selecionados] == ["Aluno"]


def test_inspetor_acompanha_criar_e_excluir(janela):
    janela.editor.create("ent", 600, 300)
    assert "Entidade" in textos_filhos(categorias(janela)["Entidades"])
    janela.editor.delete([figura(janela, "Curso")])
    assert "Curso" not in textos_filhos(categorias(janela)["Entidades"])
    janela.editor.history.undo()
    assert "Curso" in textos_filhos(categorias(janela)["Entidades"])


# ------------------------------------------------------------- localizar


def test_localizar_filtra_ignorando_acentos_e_enter_leva_ao_elemento(janela):
    janela.action_find.trigger()
    assert janela.inspector_dock.isVisible()
    busca = janela.inspector.search
    busca.setText("ALU")
    assert [f.name for f in janela.inspector.matches()] == ["Aluno"]
    assert "1 encontrado" in janela.inspector.status.text()
    assert categorias(janela)["Relacionamentos"].isHidden()
    QTest.keyClick(busca, Qt.Key.Key_Return)
    assert [f.name for f in janela.diagram_scene.selected_figures()] == ["Aluno"]


def test_localizar_sem_resultado(janela):
    janela.inspector.search.setText("inexistente")
    assert janela.inspector.matches() == []
    assert janela.inspector.status.text() == "Nada encontrado"
    janela.inspector.search.clear()
    assert not categorias(janela)["Entidades"].isHidden()


# ------------------------------------------------------------- propriedades


def test_propriedades_de_um_atributo_mudam_tipo_e_anulabilidade(janela):
    atributo = figura(janela, "att.0")
    painel = janela.properties
    janela.diagram_scene.select_only(atributo)
    assert painel.attribute_type.isVisible() and painel.nullable.isVisible()
    assert painel.attribute_type.currentData() == "CHAR(128)"
    assert painel.nullable.isChecked()

    indice = painel.attribute_type.findData("NUMBER(9,2)")
    painel.attribute_type.activated.emit(indice)
    assert atributo.attribute_type == "NUMBER(9,2)"
    painel.nullable.click()
    assert atributo.nullable is False
    assert janela.isWindowModified()

    janela.action_undo.trigger()
    janela.action_undo.trigger()
    assert atributo.attribute_type == "CHAR(128)" and atributo.nullable is True
    assert painel.attribute_type.currentData() == "CHAR(128)"
    assert painel.nullable.isChecked()


def test_propriedades_renomeiam_o_elemento(janela):
    aluno = figura(janela, "Aluno")
    janela.diagram_scene.select_only(aluno)
    janela.properties.name.setText("Estudante")
    janela.properties.name.editingFinished.emit()
    assert aluno.name == "Estudante"
    assert "Estudante" in textos_filhos(categorias(janela)["Entidades"])


def test_entidade_nao_mostra_tipo_sql(janela):
    janela.diagram_scene.select_only(figura(janela, "Aluno"))
    assert janela.properties.name.isVisible()
    assert not janela.properties.attribute_type.isVisible()
    assert not janela.properties.connection_type.isVisible()


def test_atributo_derivado_avisa_que_nao_tem_tipo(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    no = j.editor.create("atrderivado", 100, 100)
    j.diagram_scene.select_only(no)
    assert not j.properties.attribute_type.isVisible()
    assert "não tem tipo" in j.properties.note.text()


def test_mudar_o_tipo_de_uma_conexao(janela):
    ligacao = next(f for f in janela.editor.document.figures if f.tag == "llabelUm")
    janela.diagram_scene.select_only(ligacao)
    painel = janela.properties
    assert painel.connection_type.isVisible()
    assert painel.connection_type.currentData() == "llabelUm"
    assert painel.ends.text() == "Aluno → rel. 0"
    painel.connection_type.activated.emit(painel.connection_type.findData("llabelDoubleMuitos"))
    assert ligacao.tag == "llabelDoubleMuitos"
    item = janela.diagram_scene.item_for(ligacao)
    assert any(getattr(op, "stroke", None) and op.stroke.double for op in item.ops)
    janela.action_undo.trigger()
    assert ligacao.tag == "llabelUm"
    assert painel.connection_type.currentData() == "llabelUm"


def test_rotulo_da_generalizacao_no_painel(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    ent = j.editor.create("ent", 100, 100)
    gen = j.editor.create("disjuncao", 100, 300)
    conexao = j.editor.connect("llabelGeneralizacao", gen, ent)
    j.diagram_scene.select_only(conexao)
    assert j.properties.label.isVisible()
    assert j.properties.label.text() == "característica"
    j.properties.label.setText("exclusiva")
    j.properties.label.editingFinished.emit()
    assert conexao.generalization_label == "exclusiva"


def test_varias_figuras_selecionadas(janela):
    janela.action_select_all.trigger()
    assert not janela.properties.name.isVisible()
    assert "selecionadas" in janela.properties.note.text()


def test_paineis_podem_ser_escondidos_pelo_menu_exibir(janela):
    acao = janela.properties_dock.toggleViewAction()
    acao.trigger()
    assert not janela.properties_dock.isVisible()
    acao.trigger()
    assert janela.properties_dock.isVisible()
