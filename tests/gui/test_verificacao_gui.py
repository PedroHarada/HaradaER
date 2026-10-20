"""Verificação em vermelho (RF-09), recomendação na barra (RF-10) e falhas ao gravar (RF-17)."""

import errno

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.core import io
from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.geometry import node_rect
from haradaer.gui.app import install_translator
from haradaer.gui.view import SELECT, Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def mensagens(monkeypatch):
    capturadas: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda pai, titulo, texto: capturadas.append((titulo, texto))
    )
    return capturadas


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    return j


def itens_de_conexao(janela):
    return [i for i in janela.diagram_scene.figure_items() if i.is_connection]


def centro(figura):
    x, y, w, h = node_rect(figura)
    return x + w / 2, y + h / 2


def selecionar(qtbot, janela, *figuras):
    cena = janela.diagram_scene
    cena.clearSelection()
    for figura in figuras:
        cena.item_for(figura).setSelected(True)
    QApplication.processEvents()


def negrito(janela, tag) -> bool:
    return janela._tool_actions[Tool("connect", tag)].font().bold()


# --- verificação ---------------------------------------------------------------------------


def test_arquivo_com_conexoes_soltas_mostra_os_problemas_menos_na_conexao_livre(janela, referencia):
    assert janela.load(referencia / "amostra-conexoes-incompletas.xml")
    assert janela.action_validate.isChecked()
    livres = [i for i in itens_de_conexao(janela) if i.figure.tag == "llabel"]
    assert livres and all(i.problem is None and i.toolTip() == "" for i in livres)
    assert all(i.problem for i in itens_de_conexao(janela) if i.figure.tag != "llabel")
    # Na ordem do arquivo: sem pontas, sem a ponta de fim, de uma entidade a ela mesma.
    sem_pontas, sem_fim, mesma = [i for i in itens_de_conexao(janela) if i.figure.tag == "llabelUm"]
    assert sem_pontas.problem.endswith("as duas pontas estão soltas")
    assert sem_fim.problem.endswith("a ponta de fim está solta")
    assert mesma.problem.endswith("não é aceita entre Entidade e Entidade")
    assert mesma.toolTip() == mesma.problem


def test_desligar_a_verificacao_limpa_o_vermelho(janela, referencia):
    janela.load(referencia / "amostra-conexoes-incompletas.xml")
    janela.action_validate.setChecked(False)
    assert all(i.problem is None for i in itens_de_conexao(janela))
    janela.action_validate.setChecked(True)
    assert any(i.problem for i in itens_de_conexao(janela))


def _cor_mais_vermelha(janela, de, para) -> tuple[int, int, int]:
    area = janela.diagram_scene.sceneRect()
    imagem = QImage(int(area.width()), int(area.height()), QImage.Format.Format_RGB32)
    imagem.fill(QColor("white"))
    pintor = QPainter(imagem)
    janela.diagram_scene.clearSelection()
    janela.diagram_scene.render(pintor, QRectF(imagem.rect()), area)
    pintor.end()
    x = round((de[0] + para[0]) / 2 - area.x())
    y = round((de[1] + para[1]) / 2 - area.y())
    cores = []
    for dy in range(-2, 3):
        cor = QColor(imagem.pixel(x, y + dy))
        cores.append((cor.red(), cor.green(), cor.blue()))
    return max(cores, key=lambda c: c[0] - c[1])


def test_conexao_invalida_criada_fica_vermelha_e_desfazer_limpa(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("ent", 300, 100)
    conexao = janela.editor.connect("lcaf", a, b)
    item = janela.diagram_scene.item_for(conexao)
    assert item.problem == "Ligação de atributo não é aceita entre Entidade e Entidade"
    r, g, b_ = _cor_mais_vermelha(janela, centro(a), centro(b))
    assert r - g > 80 and r - b_ > 80  # linha fina com antialiasing: vermelho claro
    janela.editor.history.undo()
    assert janela.diagram_scene.item_for(conexao) is None
    assert all(i.problem is None for i in janela.diagram_scene.figure_items())


def test_conexao_valida_nao_fica_vermelha(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    conexao = janela.editor.connect("llabelUm", a, b)
    assert janela.diagram_scene.item_for(conexao).problem is None
    r, g, _ = _cor_mais_vermelha(janela, centro(a), centro(b))
    assert r - g < 50


# --- recomendação --------------------------------------------------------------------------


def test_dois_elementos_selecionados_poem_em_negrito_as_conexoes_aceitas(qtbot, janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    selecionar(qtbot, janela, a, b)
    assert negrito(janela, "llabelUm") and negrito(janela, "llabelDoubleMuitos")
    assert not negrito(janela, "lcaf") and not negrito(janela, "llabel")
    assert (
        janela.statusBar()
        .currentMessage()
        .startswith("Conexões aceitas entre Entidade e Relacionamento")
    )
    selecionar(qtbot, janela, a)
    assert not negrito(janela, "llabelUm")


def test_par_sem_conexao_aceita_avisa(qtbot, janela):
    a = janela.editor.create("rel", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    selecionar(qtbot, janela, a, b)
    assert janela.statusBar().currentMessage() == (
        "Nenhuma conexão aceita entre Relacionamento e Relacionamento"
    )


def test_clicar_no_tipo_aceito_liga_os_dois_selecionados(qtbot, janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    selecionar(qtbot, janela, a, b)
    janela._tool_actions[Tool("connect", "llabelUm")].trigger()
    conexao = janela.editor.document.figures[-1]
    assert isinstance(conexao, ConnectionFigure) and conexao.tag == "llabelUm"
    assert {conexao.start, conexao.end} == {a, b}
    assert janela.view.tool == SELECT
    assert janela._tool_actions[SELECT].isChecked()
    assert janela.diagram_scene.selected_figures() == [conexao]


@pytest.mark.parametrize("ordem", ["circulo_primeiro", "entidade_primeiro"])
def test_generalizacao_pela_barra_sai_do_circulo_para_a_entidade(qtbot, janela, ordem):
    circulo = janela.editor.create("uniao", 100, 100)
    entidade = janela.editor.create("ent", 300, 100)
    par = (circulo, entidade) if ordem == "circulo_primeiro" else (entidade, circulo)
    selecionar(qtbot, janela, *par)
    janela._tool_actions[Tool("connect", "generalizacaoLine")].trigger()
    conexao = janela.editor.document.figures[-1]
    assert (conexao.start, conexao.end) == (circulo, entidade)


def test_tipo_nao_aceito_com_par_selecionado_so_escolhe_a_ferramenta(qtbot, janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    selecionar(qtbot, janela, a, b)
    janela._tool_actions[Tool("connect", "lcaf")].trigger()
    assert len(janela.editor.document.figures) == 2
    assert janela.view.tool == Tool("connect", "lcaf")


def test_escolher_ferramenta_de_conexao_mostra_os_pares_aceitos(janela):
    janela.view.set_tool(Tool("connect", "generalizacaoLine"))
    assert janela.statusBar().currentMessage().startswith("Liga: Entidade → Entidade")
    janela.view.set_tool(Tool("connect", "llabel"))
    assert janela.statusBar().currentMessage() == ""


# --- gravação ------------------------------------------------------------------------------


def _salvar_com_erro(monkeypatch, janela, tmp_path, erro):
    janela.editor.create("ent", 100, 100)
    janela.path = tmp_path / "modelo.xml"

    def falha(*a, **k):
        raise erro

    monkeypatch.setattr(io, "save", falha)
    return janela.save()


def test_sem_permissao_explica_e_mantem_o_documento_modificado(
    monkeypatch, janela, tmp_path, mensagens
):
    erro = PermissionError(errno.EACCES, "Permission denied")
    assert not _salvar_com_erro(monkeypatch, janela, tmp_path, erro)
    titulo, texto = mensagens[0]
    assert titulo == "Não foi possível salvar o arquivo"
    assert "Sem permissão para gravar neste local." in texto
    assert janela.isWindowModified()


def test_disco_cheio_explica(monkeypatch, janela, tmp_path, mensagens):
    erro = OSError(errno.ENOSPC, "No space left on device")
    _salvar_com_erro(monkeypatch, janela, tmp_path, erro)
    assert "Não há espaço livre no disco." in mensagens[0][1]


def test_tradutor_do_qt_em_portugues_e_instalado(qapp):
    assert install_translator(qapp)
    assert QApplication.translate("QPlatformTheme", "Save") == "Salvar"
