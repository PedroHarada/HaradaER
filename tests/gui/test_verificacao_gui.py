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


def destacada(janela, tag) -> bool:
    return janela.tool_strip.is_highlighted(janela._tool_actions[Tool("connect", tag)])


def apagada(janela, tag) -> bool:
    return janela.tool_strip.is_dimmed(janela._tool_actions[Tool("connect", tag)])


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


def test_avisos_de_estrutura_aparecem_e_podem_ser_desligados(janela, qtbot):
    from haradaer.core.commands import add_node_command, new_node
    from haradaer.gui.settings import structure_warnings_enabled

    documento = janela._editor.document
    entidade = new_node("ent", 50, 50, janela.diagram_scene._medidor)
    janela._editor.history.execute(add_node_command(documento, entidade))
    item = janela.diagram_scene.item_for(entidade)
    assert janela.action_structure.isChecked()
    assert item.warning == "Aviso: entidade sem atributo chave"
    assert item.toolTip() == item.warning
    janela.action_structure.setChecked(False)
    assert item.warning is None and item.toolTip() == ""
    assert not structure_warnings_enabled()  # lembrado para as próximas janelas
    outra = DocumentWindow()
    qtbot.addWidget(outra)
    assert not outra.action_structure.isChecked()
    janela.action_structure.setChecked(True)
    assert item.warning
    janela.action_validate.setChecked(False)  # desligar a verificação desliga os avisos também
    assert item.warning is None


def _cor_mais_vermelha(janela, de, para) -> tuple[int, int, int]:
    janela.action_structure.setChecked(False)  # só o vermelho: o laranja dos avisos atrapalha
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


def test_dois_elementos_selecionados_destacam_as_aceitas_e_apagam_as_outras(qtbot, janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    assert not apagada(janela, "lcaf") and not destacada(janela, "llabelUm")
    selecionar(qtbot, janela, a, b)
    for tag in ("llabelUm", "llabelDoubleMuitos"):
        assert destacada(janela, tag) and not apagada(janela, tag)
    for tag in ("lcaf", "llabel"):
        assert apagada(janela, tag) and not destacada(janela, tag)
    assert not janela.tool_strip.is_dimmed(janela._tool_actions[Tool("create", "ent")])
    rotulo = janela._recommendation_label
    assert rotulo.isVisible()
    assert rotulo.text().startswith("Conexões aceitas entre Entidade e Relacionamento: Lado 1")
    janela.statusBar().showMessage("outra mensagem")  # não apaga a recomendação
    assert rotulo.isVisible() and rotulo.text().startswith("Conexões aceitas")
    selecionar(qtbot, janela, a)
    assert not destacada(janela, "llabelUm") and not apagada(janela, "lcaf")
    assert not rotulo.isVisible()


def test_a_faixa_rola_ate_a_primeira_conexao_aceita(qtbot, janela):
    janela.resize(500, 400)
    QApplication.processEvents()
    if not janela.tool_strip.overflows():
        pytest.skip("a faixa coube inteira nesta tela")
    janela.tool_strip.scroll.horizontalScrollBar().setValue(0)
    a = janela.editor.create("atr", 100, 100)
    b = janela.editor.create("ent", 300, 100)
    selecionar(qtbot, janela, a, b)
    assert janela.tool_strip.scroll.horizontalScrollBar().value() > 0


def test_par_sem_conexao_aceita_avisa(qtbot, janela):
    a = janela.editor.create("rel", 100, 100)
    b = janela.editor.create("rel", 300, 100)
    selecionar(qtbot, janela, a, b)
    assert janela._recommendation_label.text() == (
        "Nenhuma conexão aceita entre Relacionamento e Relacionamento"
    )
    assert apagada(janela, "llabelUm") and apagada(janela, "llabel")


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


# --- painel Mensagens e resumo na barra de status ----------------------------------------------


def _duas_entidades_sem_chave(janela):
    a = janela.editor.create("ent", 100, 100)
    b = janela.editor.create("ent", 400, 100)
    janela.editor.rename(a, "Entidade1")
    janela.editor.rename(b, "Entidade2")
    return a, b


def test_resumo_na_barra_diz_quais_elementos_tem_aviso(janela):
    _duas_entidades_sem_chave(janela)
    rotulo = janela._verification_label
    assert rotulo.isVisible()
    assert rotulo.text() == (
        "2 avisos de estrutura: Entidade1 e Entidade2 (entidade sem atributo chave)"
    )
    janela.action_structure.setChecked(False)
    assert not rotulo.isVisible()


def test_resumo_com_erros_e_avisos_conta_e_manda_ao_painel(janela, referencia):
    janela.load(referencia / "amostra-conexoes-incompletas.xml")
    texto = janela._verification_label.text()
    assert texto.startswith("6 erros de conexão e ")
    assert texto.endswith("(veja o painel Mensagens)")


def test_painel_mensagens_lista_e_leva_ao_elemento(janela):
    a, b = _duas_entidades_sem_chave(janela)
    painel = janela.messages
    assert painel.rows() == [
        ("Aviso", "Entidade1 (Entidade)", "entidade sem atributo chave"),
        ("Aviso", "Entidade2 (Entidade)", "entidade sem atributo chave"),
    ]
    painel.tree.itemClicked.emit(painel.tree.topLevelItem(1), 0)
    assert janela.diagram_scene.selected_figures() == [b]
    janela.action_validate.setChecked(False)
    assert painel.rows() == [] and "desligada" in painel.status.text()


def test_painel_mensagens_sem_problemas(janela):
    assert janela.messages.rows() == []
    assert janela.messages.status.text() == "Nenhum problema no modelo."
    assert not janela._verification_label.isVisible()


def test_paineis_comecam_em_abas_com_o_inspetor_a_frente(janela):
    from PySide6.QtWidgets import QTabBar

    abas = [
        [b.tabText(i) for i in range(b.count())]
        for b in janela.findChildren(QTabBar)
        if b.count() and b.isVisible()
    ]
    assert abas == [["Propriedades", "Mensagens", "Inspetor de objetos"]]
    assert not janela.inspector_dock.visibleRegion().isEmpty()
    assert janela.messages_dock.visibleRegion().isEmpty()  # atrás, na sua aba
