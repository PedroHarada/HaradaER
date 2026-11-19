"""Botão direito no desenho: as ações sobre a seleção (o antigo menu Organizar e a edição)."""

import pytest
from PySide6.QtGui import QContextMenuEvent, QKeySequence
from PySide6.QtWidgets import QMenu

from haradaer.gui.view import figure_box
from haradaer.gui.window import DocumentWindow


@pytest.fixture
def janela(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


def _textos(menu: QMenu) -> dict[str, bool]:
    """Texto (sem o atalho) -> ligado, de cada item."""
    return {a.text().split("\t")[0]: a.isEnabled() for a in menu.actions() if not a.isSeparator()}


def _menu(janela) -> QMenu:
    menu = QMenu()
    janela._fill_context_menu(menu)
    return menu


def test_sem_selecao_so_colar_e_selecionar_tudo(janela):
    itens = _textos(_menu(janela))
    assert itens["C&olar"] and itens["Selecionar &tudo"]
    assert not itens["&Copiar"] and not itens["E&xcluir"]
    assert "&Alinhar" not in itens


def test_um_elemento_ordem_ligada_alinhar_e_agrupar_cinza(janela):
    no = janela._editor.create("ent", 0, 0)
    janela.diagram_scene.select_only(no)
    itens = _textos(_menu(janela))
    assert itens["&Copiar"] and itens["E&xcluir"] and itens["&Trazer para a frente"]
    assert not itens["A&grupar"] and not itens["&Desagrupar"]
    assert not itens["&Alinhar"]


def test_varios_elementos_alinhar_funciona(janela):
    a = janela._editor.create("ent", 0, 0)
    b = janela._editor.create("ent", 200, 80)
    janela._select_all()
    menu = _menu(janela)
    itens = _textos(menu)
    assert itens["A&grupar"] and itens["&Alinhar"]
    alinhar = next(x.menu() for x in menu.actions() if x.menu() is not None)
    assert "\t" not in alinhar.actions()[0].text()  # alinhar não tem atalho
    alinhar.actions()[0].trigger()  # À esquerda
    assert figure_box(a)[0] == figure_box(b)[0]


def test_atalho_escrito_ao_lado(janela):
    no = janela._editor.create("ent", 0, 0)
    janela.diagram_scene.select_only(no)
    menu = _menu(janela)
    copiar = next(a for a in menu.actions() if a.text().startswith("&Copiar"))
    tecla = QKeySequence("Ctrl+C").toString(QKeySequence.SequenceFormat.NativeText)
    assert copiar.text().endswith(f"\t{tecla}")  # "Ctrl+C", ou "⌘C" no macOS


def test_acao_do_menu_age_na_selecao(janela):
    no = janela._editor.create("ent", 0, 0)
    janela.diagram_scene.select_only(no)
    menu = _menu(janela)
    excluir = next(a for a in menu.actions() if a.text().startswith("E&xcluir"))
    excluir.trigger()
    assert janela._editor.document.figures == []


def test_botao_direito_num_elemento_da_selecao_mantem_a_selecao(janela, monkeypatch):
    a = janela._editor.create("ent", 0, 0)
    janela._editor.create("ent", 300, 0)
    janela._select_all()
    abertos = []
    monkeypatch.setattr(janela.view, "show_menu", lambda menu, onde: abertos.append(_textos(menu)))
    janela.show()
    caixa = janela.diagram_scene.item_for(a).sceneBoundingRect()
    centro = janela.view.mapFromScene(caixa.center())
    global_ = janela.view.mapToGlobal(centro)
    evento = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, centro, global_)
    janela.view.contextMenuEvent(evento)
    assert len(janela.diagram_scene.selected_figures()) == 2
    assert abertos and abertos[0]["&Alinhar"]


def test_organizar_na_barra_e_no_botao_direito(janela):
    assert janela.arrange_menu.menuAction() in janela.menuBar().actions()
    no = janela._editor.create("ent", 0, 0)
    janela.diagram_scene.select_only(no)
    assert "A&grupar" in _textos(_menu(janela))
