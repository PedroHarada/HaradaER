"""M5d: exportar o desenho, copiar como imagem, arquivos recentes e disposição da janela."""

import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.gui.app import WindowManager
from haradaer.gui.export import (
    EXPORT_MARGIN,
    RASTER_SCALE,
    EmptyDiagramError,
    export_diagram,
    render_image,
)
from haradaer.gui.settings import MAX_RECENT, RecentFiles
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def mensagens(monkeypatch):
    vistas = []
    for tipo in ("critical", "information"):
        monkeypatch.setattr(
            QMessageBox, tipo, lambda pai, titulo, texto, *a, t=tipo: vistas.append((t, texto))
        )
    return vistas


@pytest.fixture
def janela(qtbot, referencia):
    j = DocumentWindow()
    qtbot.addWidget(j)
    j.show()
    assert j.load(referencia / "amostra-basica.xml")
    return j


def escolher_arquivo(monkeypatch, caminho, filtro=""):
    monkeypatch.setattr(
        "haradaer.gui.window.QFileDialog.getSaveFileName", lambda *a, **k: (str(caminho), filtro)
    )


# ------------------------------------------------------------- exportar


@pytest.mark.parametrize("extensao", ["png", "jpg", "svg", "pdf"])
def test_exportar_em_cada_formato(janela, tmp_path, extensao):
    destino = tmp_path / f"modelo.{extensao}"
    export_diagram(janela.diagram_scene, destino, "modelo")
    dados = destino.read_bytes()
    assert len(dados) > 500
    inicio = {"png": b"\x89PNG", "jpg": b"\xff\xd8", "svg": b"<?xml", "pdf": b"%PDF"}[extensao]
    assert dados.startswith(inicio)


def test_imagem_tem_o_tamanho_do_desenho_com_margem_e_fundo_branco(janela):
    area = janela.diagram_scene.content_rect()
    imagem = render_image(janela.diagram_scene)
    largura = round((area.width() + 2 * EXPORT_MARGIN) * RASTER_SCALE)
    assert imagem.width() == largura
    assert QColor(imagem.pixel(2, 2)) == QColor("white")


def test_exportar_nao_leva_selecao_nem_marcas_vermelhas(janela):
    limpa = render_image(janela.diagram_scene)
    ligacao = next(f for f in janela.editor.document.figures if f.tag == "llabelUm")
    janela.editor.change_connection_type(ligacao, "lcaf")  # par inválido: fica vermelha na tela
    assert janela.diagram_scene.item_for(ligacao).problem
    janela.editor.change_connection_type(ligacao, "llabelUm")
    janela.action_select_all.trigger()
    assert render_image(janela.diagram_scene) == limpa

    janela.editor.change_connection_type(ligacao, "lcaf")
    imagem = render_image(janela.diagram_scene).convertToFormat(QImage.Format.Format_RGB32)
    vermelhos = sum(
        1
        for x in range(0, imagem.width(), 2)
        for y in range(0, imagem.height(), 2)
        if QColor(imagem.pixel(x, y)).red() > 200 and QColor(imagem.pixel(x, y)).green() < 60
    )
    assert vermelhos == 0


def test_desenho_vazio_nao_exporta(qtbot, tmp_path, monkeypatch, mensagens):
    j = DocumentWindow()
    qtbot.addWidget(j)
    with pytest.raises(EmptyDiagramError):
        render_image(j.diagram_scene)
    escolher_arquivo(monkeypatch, tmp_path / "vazio.png")
    assert not j.export()
    assert mensagens == [("information", "O desenho está vazio.")]
    assert not (tmp_path / "vazio.png").exists()


def test_exportar_pelo_menu_acrescenta_a_extensao_do_filtro(janela, tmp_path, monkeypatch):
    escolher_arquivo(monkeypatch, tmp_path / "diagrama", "Documento PDF (*.pdf)")
    assert janela.export()
    assert (tmp_path / "diagrama.pdf").read_bytes().startswith(b"%PDF")


def test_exportar_numa_pasta_que_nao_existe_avisa(janela, tmp_path, monkeypatch, mensagens):
    escolher_arquivo(monkeypatch, tmp_path / "nao" / "existe.png")
    assert not janela.export()
    assert mensagens and mensagens[0][0] == "critical"


def test_exportar_nao_muda_o_modelo(janela, tmp_path, monkeypatch):
    escolher_arquivo(monkeypatch, tmp_path / "x.svg")
    assert janela.export()
    assert not janela.isWindowModified()


def test_copiar_como_imagem(janela):
    assert janela.copy_image()
    imagem = QApplication.clipboard().image()
    assert not imagem.isNull()
    assert imagem.size() == render_image(janela.diagram_scene).size()


# ------------------------------------------------------------- recentes


@pytest.fixture
def gerenciador(qtbot):
    ger = WindowManager()
    yield ger
    for janela in list(ger.windows):
        janela.close()


def textos_do_menu(janela):
    janela._fill_recent_menu()
    return [a.text() for a in janela.recent_menu.actions() if not a.isSeparator()]


def test_abrir_e_salvar_entram_nos_recentes(gerenciador, referencia, tmp_path, monkeypatch):
    janela = gerenciador.open_path(referencia / "amostra-basica.xml")
    assert gerenciador.recent.paths() == [(referencia / "amostra-basica.xml").resolve()]
    escolher_arquivo(monkeypatch, tmp_path / "copia.xml")
    assert janela.save_as()
    assert gerenciador.recent.paths()[0] == (tmp_path / "copia.xml").resolve()
    menu = textos_do_menu(janela)
    assert menu[0].startswith("&1 copia.xml")
    assert menu[1].startswith("&2 amostra-basica.xml")
    assert menu[-1] == "&Limpar lista"


def test_clicar_num_recente_abre_em_outra_janela(gerenciador, referencia):
    primeira = gerenciador.open_path(referencia / "amostra-basica.xml")
    gerenciador.recent.add(referencia / "amostra-estilos.xml")
    primeira.open_recent((referencia / "amostra-estilos.xml").resolve())
    assert len(gerenciador.windows) == 2
    assert gerenciador.windows[1].path.name == "amostra-estilos.xml"


def test_recente_que_sumiu_e_tirado_da_lista(gerenciador, tmp_path, mensagens, referencia):
    some = tmp_path / "some.xml"
    some.write_bytes((referencia / "amostra-basica.xml").read_bytes())
    janela = gerenciador.open_path(some)
    some.unlink()
    janela.open_recent(some.resolve())
    assert mensagens and "não existe mais" in mensagens[0][1]
    assert textos_do_menu(janela) == ["Nenhum arquivo recente"]


def test_limpar_lista_e_limite_de_recentes(tmp_path):
    recentes = RecentFiles()
    for i in range(MAX_RECENT + 3):
        arquivo = tmp_path / f"m{i}.xml"
        arquivo.write_text("<drawing><figures/></drawing>")
        recentes.add(arquivo)
    assert len(recentes.paths()) == MAX_RECENT
    assert recentes.paths()[0].name == f"m{MAX_RECENT + 2}.xml"
    recentes.add(tmp_path / "m5.xml")  # repetido sobe para o topo, sem duplicar
    assert recentes.paths()[0].name == "m5.xml"
    assert len(recentes.paths()) == MAX_RECENT
    recentes.clear()
    assert recentes.paths() == []


# ------------------------------------------------------------- disposição da janela


def test_disposicao_dos_paineis_e_lembrada(qtbot):
    primeira = DocumentWindow()
    qtbot.addWidget(primeira)
    primeira.show()
    primeira.properties_dock.toggleViewAction().trigger()
    assert not primeira.properties_dock.isVisible()
    primeira.close()

    segunda = DocumentWindow()
    qtbot.addWidget(segunda)
    segunda.show()
    assert not segunda.properties_dock.isVisible()
    assert segunda.inspector_dock.isVisible()
