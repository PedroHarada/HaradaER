"""A cena desenha o que o núcleo descreve."""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter

from haradaer.core import io
from haradaer.gui.scene import DiagramScene


def _cena(referencia, nome) -> DiagramScene:
    cena = DiagramScene()
    cena.set_document(io.load(referencia / nome))
    return cena


def _desenhar(cena: DiagramScene, area: QRectF) -> QImage:
    imagem = QImage(int(area.width()), int(area.height()), QImage.Format.Format_RGB32)
    imagem.fill(QColor("white"))
    pintor = QPainter(imagem)
    cena.render(pintor, QRectF(imagem.rect()), area)
    pintor.end()
    return imagem


def _rgb(imagem: QImage, x: int, y: int) -> tuple[int, int, int]:
    cor = QColor(imagem.pixel(x, y))
    return (cor.red(), cor.green(), cor.blue())


def test_um_item_por_figura_na_ordem_de_empilhamento(qapp, referencia):
    cena = _cena(referencia, "amostra-basica.xml")
    itens = cena.figure_items()
    assert [i.figure.tag for i in itens] == [f.tag for f in cena.document.figures]
    assert [i.zValue() for i in itens] == sorted(i.zValue() for i in itens)


def test_cena_vazia(qapp):
    cena = DiagramScene()
    cena.set_document(None)
    assert cena.figure_items() == [] and cena.sceneRect().isEmpty()


def test_a_cena_tem_margem_em_volta_do_desenho(qapp, referencia):
    cena = _cena(referencia, "amostra-basica.xml")
    assert cena.sceneRect().width() > cena.itemsBoundingRect().width()


def test_cores_desenhadas_sao_as_do_terraer(qapp, referencia):
    cena = _cena(referencia, "amostra-basica.xml")
    imagem = _desenhar(cena, QRectF(0, 0, 600, 260))
    assert _rgb(imagem, 5, 5) == (255, 255, 255), "fundo branco"
    assert _rgb(imagem, 55, 55) == (175, 255, 175), "entidade: verde fixo do TerraER"


def test_borda_da_entidade_e_escura(qapp, referencia):
    cena = _cena(referencia, "amostra-basica.xml")
    imagem = _desenhar(cena, QRectF(0, 0, 600, 260))
    # a entidade começa em x=50; a borda de 1 px cai entre dois pixels, então fica cinza
    escuros = [x for x in range(48, 53) if sum(_rgb(imagem, x, 70)) < 450]
    assert escuros, "deveria haver uma borda escura na coluna 48..52"
    assert _rgb(imagem, 60, 85) == (175, 255, 175), "dentro da entidade, longe do texto, só o verde"


def test_losango_do_relacionamento_e_amarelo(qapp, referencia):
    cena = _cena(referencia, "amostra-figuras-de-apoio.xml")
    imagem = _desenhar(cena, QRectF(0, 0, 500, 200))
    assert _rgb(imagem, 230, 150) == (255, 255, 100)


def test_figura_de_apoio_imagem_e_vermelha(qapp, referencia):
    cena = _cena(referencia, "amostra-figuras-de-apoio.xml")
    imagem = _desenhar(cena, QRectF(0, 0, 500, 200))
    assert _rgb(imagem, 416, 86) == (255, 0, 0)


def test_elipse_do_atributo_e_lilas(qapp, referencia):
    cena = _cena(referencia, "amostra-figuras-de-apoio.xml")
    imagem = _desenhar(cena, QRectF(0, 0, 500, 200))
    assert _rgb(imagem, 230, 90) == (175, 175, 255)


@pytest.mark.parametrize(
    "nome",
    [
        "amostra-basica.xml",
        "amostra-todos-os-tipos.xml",
        "amostra-figuras-de-apoio.xml",
        "amostra-ordem-empilhamento.xml",
        "amostra-conexoes-incompletas.xml",
        "amostra-estilos.xml",
        "amostra-numeros.xml",
        "amostra-unicode.xml",
        "amostra-vazios.xml",
    ],
)
def test_todas_as_amostras_desenham_sem_erro(qapp, referencia, nome):
    cena = _cena(referencia, nome)
    area = cena.itemsBoundingRect().adjusted(-5, -5, 5, 5)
    if area.width() > 4000 or area.height() > 4000:  # amostra-numeros espalha formas muito longe
        area = QRectF(0, 0, 200, 200)
    imagem = _desenhar(cena, area)
    assert not imagem.isNull()
