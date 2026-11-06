"""Texto na interface (RF-26) e o aviso dos textos convertidos ao abrir (RF-27)."""

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import QMessageBox

from haradaer.core.appearance.ops import ShapeOp, TextOp
from haradaer.core.commands import all_text_areas, text_area_rect, text_of
from haradaer.gui.inline_edit import InlineTextEdit
from haradaer.gui.scene.items import op_bounds
from haradaer.gui.shortcuts import FAMILIES, next_tool
from haradaer.gui.view import SELECT, Tool
from haradaer.gui.window import DocumentWindow

TEXTO = Tool("create", "ta")


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    """O modelo convertido abre modificado: fechar a janela no fim não pode esperar resposta."""
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def avisos(monkeypatch):
    capturados: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda pai, titulo, texto: capturados.append((titulo, texto))
    )
    return capturados


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    return j


def digitar_e_confirmar(qtbot, janela, conteudo: str) -> None:
    """Ctrl+Enter confirma. Só o "apertar": o editor fecha nele, e soltar a tecla num campo já
    fechado derruba o QTest."""
    editor = janela.view._inline
    assert isinstance(editor, InlineTextEdit)
    editor.setPlainText(conteudo)
    qtbot.keyPress(editor, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
    assert janela.view._inline is None


def test_ferramenta_texto_no_fim_da_faixa_e_na_tecla_t(janela):
    assert list(janela._tool_actions)[-1] == TEXTO
    acao = janela._tool_actions[TEXTO]
    assert (acao.text(), acao.toolTip()) == ("Texto", "Texto")
    assert dict(FAMILIES)["T"] == [TEXTO]
    assert next_tool("t", SELECT) == TEXTO and next_tool("T", TEXTO) == TEXTO


def test_clicar_cria_caixa_padrao_e_enter_quebra_linha(qtbot, janela):
    janela.view.set_tool(TEXTO)
    janela.view._new_text((100, 100, 120, 60), keep_tool=False)
    assert janela.view.tool == SELECT
    editor = janela.view._inline
    assert isinstance(editor, InlineTextEdit)
    qtbot.keyClicks(editor, "Regra")
    qtbot.keyClick(editor, Qt.Key.Key_Return)  # Enter quebra a linha, não confirma
    assert janela.view._inline is editor
    editor.insertPlainText("de negócio")  # o QTest só digita ASCII
    qtbot.keyPress(editor, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
    (texto,) = all_text_areas(janela.editor.document)
    assert text_of(texto) == "Regra\nde negócio"
    assert text_area_rect(texto) == (100, 100, 120, 60)
    assert janela.diagram_scene.selected_figures() == [texto]
    janela.editor.history.undo()  # criar com o texto é um passo só
    assert all_text_areas(janela.editor.document) == []


def test_sair_sem_digitar_ou_com_esc_nao_cria(qtbot, janela):
    janela.view._new_text((0, 0, 120, 60), keep_tool=True)
    digitar_e_confirmar(qtbot, janela, "   ")
    janela.view._new_text((0, 0, 120, 60), keep_tool=True)
    editor = janela.view._inline
    editor.setPlainText("descartado")
    qtbot.keyPress(editor, Qt.Key.Key_Escape)
    assert all_text_areas(janela.editor.document) == []
    assert not janela.editor.history.can_undo


def test_duplo_clique_edita_e_apagar_tudo_exclui(qtbot, janela):
    texto = janela.editor.add_text((0, 0, 120, 60), "antes")
    janela.view._edit_text_area(texto)
    assert janela.view._inline.toPlainText() == "antes"
    digitar_e_confirmar(qtbot, janela, "depois " * 30)
    assert text_of(texto) == "depois " * 30
    x, y, w, h = text_area_rect(texto)
    assert w == 120 and h > 60  # a largura fica, a altura cresce
    janela.view._edit_text_area(texto)
    digitar_e_confirmar(qtbot, janela, "")
    assert all_text_areas(janela.editor.document) == []
    janela.editor.history.undo()
    assert all_text_areas(janela.editor.document) == [texto]


def test_texto_selecionado_tem_alcas_e_redimensiona(janela):
    texto = janela.editor.add_text((0, 0, 120, 60), "um dois tres quatro cinco")
    janela.diagram_scene.select_only(texto)
    assert janela.view.resizable() is texto
    assert set(janela.view.handle_rects()) == {"nw", "n", "ne", "e", "se", "s", "sw", "w"}
    janela.editor.resize(texto, (0, 0, 50, 10))
    _x, _y, w, h = text_area_rect(texto)
    assert w == 50 and h > 10  # estreito demais: a altura cresce para caber


def test_localizar_acha_texto_pelo_conteudo(janela):
    texto = janela.editor.add_text((0, 0, 120, 60), "Regra de negócio:\ncliente ativo")
    janela.inspector.search.setText("negocio cliente")
    assert janela.inspector.matches() == []  # a quebra de linha conta como texto
    janela.inspector.search.setText("CLIENTE ATIVO")
    assert janela.inspector.matches() == [texto]


def test_abrir_converte_avisa_e_so_muda_o_disco_ao_salvar(janela, avisos, referencia, tmp_path):
    arquivo = tmp_path / "apoio.xml"
    original = (referencia / "amostra-figuras-de-apoio.xml").read_bytes()
    arquivo.write_bytes(original)
    assert janela.load(arquivo)
    assert len(avisos) == 1
    titulo, texto = avisos[0]
    assert titulo == "Textos convertidos"
    assert "4 textos deste arquivo viraram Texto" in texto
    assert "• “Itálico” (papel)" in texto and "• “Negrito” (texto em negrito)" in texto
    assert janela.isWindowModified() and not janela.editor.history.can_undo
    assert arquivo.read_bytes() == original
    assert janela.save()
    gravado = arquivo.read_text("ascii")
    assert "<tn " not in gravado and "<ti " not in gravado
    assert not janela.isWindowModified()


def test_arquivo_sem_texto_solto_abre_sem_aviso(janela, avisos, referencia):
    assert janela.load(referencia / "amostra-basica.xml")
    assert avisos == [] and not janela.isWindowModified()


def test_ctrl_b_e_ctrl_i_poem_os_marcadores_do_markdown(qtbot, janela):
    janela.view._new_text((0, 0, 200, 60), keep_tool=False)
    editor = janela.view._inline
    editor.setPlainText("regra importante")
    cursor = editor.textCursor()
    cursor.setPosition(6)
    cursor.setPosition(16, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    qtbot.keyPress(editor, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    assert editor.toPlainText() == "regra **importante**"
    editor.moveCursor(QTextCursor.MoveOperation.End)
    qtbot.keyPress(editor, Qt.Key.Key_I, Qt.KeyboardModifier.ControlModifier)
    qtbot.keyClicks(editor, "sim")  # sem seleção, o cursor fica entre os marcadores
    assert editor.toPlainText() == "regra **importante***sim*"
    digitar_e_confirmar(qtbot, janela, "## Regra\n- **cliente** ativo")
    (texto,) = all_text_areas(janela.editor.document)
    assert text_of(texto) == "## Regra\n- **cliente** ativo"  # o arquivo guarda os marcadores
    janela.inspector.search.setText("cliente ativo")  # o Localizar não vê os marcadores
    assert janela.inspector.matches() == [texto]


def test_ctrl_clique_abre_so_links_da_web_e_de_email(qtbot, janela, monkeypatch):
    abertos = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: abertos.append(url.toString()))
    texto = janela.editor.add_text(
        (0, 0, 400, 60), "[site](https://a.com) [mail](mailto:a@b.com) [ftp](ftp://c.com)"
    )
    item = janela.diagram_scene.item_containing(texto)
    site, mail, ftp = (op for op in item.ops if isinstance(op, TextOp) and op.link)
    assert janela.view.link_at(op_bounds(site).center()) == "https://a.com"
    assert janela.view.link_at(QPointF(-50, -50)) is None
    for op in (site, mail, ftp):
        janela.view.open_link(op.link)
    assert abertos == ["https://a.com", "mailto:a@b.com"]  # ftp não abre


def test_link_perigoso_nem_vira_link():
    from haradaer.core.appearance.markdown import parse

    (bloco,) = parse("[x](javascript:alert(1)) [y](file:///etc/passwd)")
    assert all(run.link is None for run in bloco.runs)


def test_ctrl_clique_na_caixinha_marca_a_tarefa_e_desfaz(qtbot, janela):
    texto = janela.editor.add_text((0, 0, 300, 60), "### Pendências\n- [ ] revisar\n- [x] feito")
    item = janela.diagram_scene.item_containing(texto)
    revisar, feito = (op for op in item.ops if isinstance(op, ShapeOp) and op.task is not None)
    centro = QPointF(revisar.x + revisar.w / 2, revisar.y + revisar.h / 2)
    assert janela.view.task_at(centro) == (texto, 1)
    qtbot.mouseClick(
        janela.view.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        janela.view.mapFromScene(centro),
    )
    assert text_of(texto) == "### Pendências\n- [x] revisar\n- [x] feito"
    janela.editor.history.undo()
    assert text_of(texto) == "### Pendências\n- [ ] revisar\n- [x] feito"


def test_tique_continua_preto_no_tema_escuro(janela):
    from haradaer.core.appearance.ops import PolylineOp
    from haradaer.core.appearance.style import BLACK
    from haradaer.gui.theme import theme_named

    texto = janela.editor.add_text((0, 0, 300, 60), "- [x] feito")
    item = janela.diagram_scene.item_containing(texto)
    escuro = theme_named("escuro")
    (tique,) = [op for op in item._themed_ops(escuro) if isinstance(op, PolylineOp)]
    assert escuro.is_dark and tique.stroke.color == BLACK
