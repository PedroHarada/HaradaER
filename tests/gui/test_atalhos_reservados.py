"""Nenhum atalho do HaradaER cai num atalho reservado pela Apple ou pelo KDE (2026-11-19).

Os atalhos são os mesmos nos três sistemas, e no macOS o Qt troca Ctrl por Cmd e Alt por
Option. Por isso, as duas listas estão na notação do Qt: "Ctrl" vale como Cmd no Mac, "Alt"
como Option e "Meta" como a tecla Control do Mac.

- Apple: tabela de atalhos padrão do guia de interface (Keyboards).
- KDE: atalhos padrão do KStandardShortcut que conferimos (Desmarcar, Ir para a linha,
  Buscar o próximo).

Um atalho reservado só pode ser usado com a mesma função (`MESMA_FUNCAO`) ou quando a ação
reservada não existe no HaradaER, como o próprio guia da Apple permite (`REAPROVEITADOS`).
"""

import pytest
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.window import DocumentWindow

APPLE = {
    "Ctrl+Space": "Spotlight",
    "Ctrl+Tab": "trocar de app",
    "Ctrl+`": "próxima janela do app",
    "Ctrl+?": "menu Ajuda",
    "Ctrl+;": "palavras com erro",
    "Ctrl+:": "janela de ortografia",
    "Ctrl+,": "configurações do app",
    "Ctrl+.": "cancelar a operação",
    "Ctrl+B": "negrito",
    "Ctrl+I": "itálico",
    "Ctrl+U": "sublinhado",
    "Ctrl+T": "janela de fontes",
    "Ctrl+Alt+T": "mostrar ou ocultar a barra de ferramentas",
    "Ctrl+H": "ocultar o app",
    "Ctrl+Alt+H": "ocultar os outros apps",
    "Ctrl+M": "minimizar",
    "Ctrl+Alt+M": "minimizar todas as janelas",
    "Ctrl+G": "buscar o próximo",
    "Ctrl+Shift+G": "buscar o anterior",
    "Ctrl+Shift+A": "desmarcar tudo",
    "Ctrl+E": "usar a seleção para buscar",
    "Ctrl+Alt+F": "ir ao campo de busca",
    "Ctrl+Meta+F": "tela cheia",
    "Ctrl+J": "rolar até a seleção",
    "Ctrl+P": "imprimir",
    "Ctrl+Shift+P": "configurar a página",
    "Ctrl+Shift+C": "janela de cores",
    "Ctrl+Alt+C": "copiar o estilo",
    "Ctrl+Shift+V": "colar como",
    "Ctrl+Alt+V": "aplicar o estilo",
    "Ctrl+Alt+D": "mostrar ou ocultar o Dock",
    "Ctrl+[": "alinhar à esquerda",
    "Ctrl+]": "alinhar à direita",
    "Ctrl+|": "centralizar",
    "Ctrl+Shift+Q": "encerrar a sessão",
    "F11": "mostrar a mesa",
    "F12": "Dashboard",
}
KDE = {
    "Ctrl+Shift+A": "desmarcar",
    "Ctrl+G": "ir para a linha",
    "F3": "buscar o próximo",
}

# Mesma função que a reservada: não é colisão.
MESMA_FUNCAO = {
    ("Ctrl+,", "Preferências"),
    ("Ctrl+Shift+A", "Desmarcar tudo"),
}
# A ação reservada não existe no HaradaER; o guia da Apple permite reaproveitar o atalho.
REAPROVEITADOS = {
    ("Ctrl+E", "Exportar desenho"),  # o Localizar não busca pela seleção
    ("Ctrl+Shift+C", "Copiar como imagem"),  # não há janela de cores
    ("F11", "Tela cheia"),  # só no Linux e no Windows; no Mac a tela cheia é Ctrl+Cmd+F
}


@pytest.fixture
def janela(qtbot, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    return janela


def _nome(acao: QAction) -> str:
    return acao.text().replace("&", "").replace("…", "").replace("...", "").strip()


def test_nenhum_atalho_colide_com_os_reservados(janela):
    colisoes = []
    for acao in janela.findChildren(QAction):
        for tecla in acao.shortcuts():
            texto = tecla.toString(QKeySequence.SequenceFormat.PortableText)
            reservado = APPLE.get(texto) or KDE.get(texto)
            if reservado is None:
                continue
            par = (texto, _nome(acao))
            if par in MESMA_FUNCAO or par in REAPROVEITADOS:
                continue
            colisoes.append(f"{texto} ({_nome(acao)}) é {reservado}")
    assert colisoes == []


def test_atalhos_novos(janela):
    def teclas(acao):
        return [t.toString() for t in acao.shortcuts()]

    assert teclas(janela.action_group) == ["Ctrl+Alt+G"]
    assert teclas(janela.action_ungroup) == ["Ctrl+Alt+Shift+G"]
    assert teclas(janela.action_select_same) == ["Ctrl+Alt+A"]
    assert teclas(janela.action_deselect) == ["Ctrl+Shift+A"]
    assert teclas(janela.action_front) == ["Home", "Ctrl+Alt+Shift+F"]
    assert teclas(janela.action_back) == ["End", "Ctrl+Alt+Shift+B"]


def test_desmarcar_tudo(janela):
    janela.editor.create("ent", 0, 0)
    janela._select_all()
    assert janela.diagram_scene.selected_figures()
    janela.action_deselect.trigger()
    assert janela.diagram_scene.selected_figures() == []


def test_home_e_end_mudam_a_ordem_so_no_desenho(janela, qtbot):
    from PySide6.QtCore import Qt

    janela.show()
    janela.activateWindow()  # o atalho só vale na janela ativa
    qtbot.waitUntil(janela.isActiveWindow)
    a = janela.editor.create("ent", 0, 0)
    janela.editor.create("ent", 10, 10)
    janela.view.setFocus()
    janela.diagram_scene.select_only(a)
    qtbot.keyClick(janela.view, Qt.Key.Key_Home)
    assert janela.editor.document.figures[-1] is a  # foi para a frente
    janela.diagram_scene.select_only(a)
    qtbot.keyClick(janela.view, Qt.Key.Key_End)
    assert janela.editor.document.figures[0] is a  # voltou para trás
    assert janela.action_front.shortcutContext() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_lista_do_f1_mostra_os_dois_atalhos_da_ordem(janela, qtbot):
    dialogo = janela.show_shortcuts()
    qtbot.addWidget(dialogo)
    linhas = dict(dialogo.visible_rows())
    assert linhas["Trazer para a frente"].startswith("Home")
    assert "F" in linhas["Trazer para a frente"].split(", ")[1]
