"""Janelas: uma por documento (RF-19), abertura de arquivos e mensagens de erro (RNF-14)."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.app import WindowManager
from haradaer.gui.window import DocumentWindow


@pytest.fixture
def mensagens(monkeypatch):
    """Captura as caixas de erro em vez de abri-las."""
    capturadas: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda pai, titulo, texto: capturadas.append((titulo, texto))
    )
    return capturadas


@pytest.fixture
def gerenciador(qtbot):
    ger = WindowManager()
    yield ger
    for janela in list(ger.windows):
        janela.close()


def test_janela_vazia(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert janela.is_empty and janela.windowTitle() == "Sem título[*] - HaradaER"


def test_abrir_arquivo_mostra_o_diagrama(qtbot, referencia):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert janela.load(referencia / "amostra-basica.xml")
    assert janela.windowTitle() == "amostra-basica.xml[*] - HaradaER"
    assert len(janela.diagram_scene.figure_items()) == 9
    assert janela.view.zoom == pytest.approx(1.0)
    assert not janela.is_empty


def test_arquivo_invalido_mostra_erro_claro_e_nao_abre(qtbot, tmp_path, mensagens):
    ruim = tmp_path / "ruim.xml"
    ruim.write_text('<drawing>\n<figures>\n<foo id="0"/>\n</figures>\n</drawing>')
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert not janela.load(ruim)
    assert janela.is_empty
    (titulo, texto) = mensagens[0]
    assert "Não foi possível" in titulo
    assert "ruim.xml" in texto and "<foo>" in texto and "linha 3" in texto


def test_arquivo_inexistente(qtbot, tmp_path, mensagens):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert not janela.load(tmp_path / "nao-existe.xml")
    assert len(mensagens) == 1 and janela.is_empty


def test_zoom_aparece_na_barra_de_status(qtbot, referencia):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.load(referencia / "amostra-basica.xml")
    janela.action_zoom_in.trigger()
    assert janela._zoom_label.text() == "125%"
    janela.action_zoom_actual.trigger()
    assert janela._zoom_label.text() == "100%"
    janela.action_zoom_out.trigger()
    assert janela._zoom_label.text() == "80%"


def test_uma_janela_por_documento(gerenciador, referencia):
    a = gerenciador.open_path(referencia / "amostra-basica.xml")
    b = gerenciador.open_path(referencia / "amostra-estilos.xml")
    assert a is not b and len(gerenciador.windows) == 2
    assert a.path.name == "amostra-basica.xml" and b.path.name == "amostra-estilos.xml"


def test_abrir_de_novo_o_mesmo_arquivo_traz_a_janela_existente(gerenciador, referencia):
    a = gerenciador.open_path(referencia / "amostra-basica.xml")
    de_novo = gerenciador.open_path(Path(str(referencia / "amostra-basica.xml")))
    assert de_novo is a and len(gerenciador.windows) == 1


def test_janela_vazia_e_reaproveitada(gerenciador, referencia):
    vazia = gerenciador.new_window()
    janela = gerenciador.open_path(referencia / "amostra-basica.xml")
    assert janela is vazia and len(gerenciador.windows) == 1


def test_falha_ao_abrir_nao_deixa_janela_sobrando(gerenciador, tmp_path, mensagens):
    ruim = tmp_path / "ruim.xml"
    ruim.write_text("não é xml")
    assert gerenciador.open_path(ruim) is None
    assert gerenciador.windows == []
    assert len(mensagens) == 1


def test_fechar_remove_a_janela_do_gerenciador(gerenciador, referencia):
    a = gerenciador.open_path(referencia / "amostra-basica.xml")
    gerenciador.open_path(referencia / "amostra-estilos.xml")
    a.close()
    assert [j.path.name for j in gerenciador.windows] == ["amostra-estilos.xml"]


def test_tipo_de_atributo_invalido_avisa_e_usa_o_padrao(qtbot, referencia, monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda pai, titulo, texto: avisos.append(texto))
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert janela.load(referencia / "leitura-casos" / "tipo_FOO_.xml")
    assert len(avisos) == 1 and "FOO" in avisos[0]
    assert janela.editor.document.figures[0].attribute_type == "VARCHAR2(128)"
    assert janela.isWindowModified()  # a troca precisa ser salva


def test_barras_de_ferramentas_no_alto_com_icone_nome_curto_e_dica(qtbot):
    from PySide6.QtCore import Qt

    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert janela.toolBarArea(janela.tool_bar) == Qt.ToolBarArea.TopToolBarArea
    assert len(janela._tool_actions) == 1 + 13 + 8
    for acao in janela._tool_actions.values():
        assert not acao.icon().isNull()
        assert acao.text()  # nome curto embaixo do ícone
        assert len(acao.toolTip()) >= len(acao.text())  # nome completo na dica
    entidade = next(a for t, a in janela._tool_actions.items() if t.tag == "ent")
    assert entidade.text() == "Entidade"
    lado_n = next(a for t, a in janela._tool_actions.items() if t.tag == "llabelMuitos")
    assert (lado_n.text(), lado_n.toolTip()) == ("Lado N", 'Participação, lado "N"')


def test_paineis_tem_largura_minima_para_nao_cortar_os_nomes(qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    assert janela.inspector_dock.minimumWidth() >= 230
    assert janela.properties_dock.minimumWidth() >= 230
