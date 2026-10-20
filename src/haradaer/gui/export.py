"""Exportar o desenho (RF-11): PNG e JPG, SVG e PDF, e copiar como imagem.

Exporta só o modelo: sem seleção, sem as marcas vermelhas da verificação e sem a grade. A área
é a do desenho mais uma margem, com fundo branco como no TerraER. GIF fica fora (D-08).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRect, QRectF, QSize, QSizeF
from PySide6.QtGui import QColor, QImage, QPageSize, QPainter, QPdfWriter
from PySide6.QtSvg import QSvgGenerator

from haradaer.gui.scene.diagram_scene import DiagramScene

EXPORT_MARGIN = 20.0
RASTER_SCALE = 2.0  # PNG e JPG com o dobro de pixels, para ficarem nítidos ao ampliar

# (extensão, nome no diálogo)
EXPORT_FORMATS = [
    ("png", "Imagem PNG"),
    ("jpg", "Imagem JPG"),
    ("svg", "Desenho vetorial SVG"),
    ("pdf", "Documento PDF"),
]


class EmptyDiagramError(ValueError):
    """Não há nada para exportar."""


def export_area(cena: DiagramScene) -> QRectF:
    area = cena.content_rect()
    if area.isEmpty():
        raise EmptyDiagramError("O desenho está vazio.")
    return area.adjusted(-EXPORT_MARGIN, -EXPORT_MARGIN, EXPORT_MARGIN, EXPORT_MARGIN)


@contextmanager
def _painting(cena: DiagramScene) -> Iterator[None]:
    anterior = cena.exporting
    cena.exporting = True
    try:
        yield
    finally:
        cena.exporting = anterior


def _render(cena: DiagramScene, painter: QPainter, destino: QRectF, area: QRectF) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    with _painting(cena):
        cena.render(painter, destino, area)


def render_image(cena: DiagramScene, escala: float = RASTER_SCALE) -> QImage:
    area = export_area(cena)
    largura, altura = round(area.width() * escala), round(area.height() * escala)
    imagem = QImage(largura, altura, QImage.Format.Format_RGB32)
    imagem.fill(QColor("white"))
    painter = QPainter(imagem)
    _render(cena, painter, QRectF(0, 0, largura, altura), area)
    painter.end()
    return imagem


def _write_svg(cena: DiagramScene, caminho: Path, titulo: str) -> None:
    area = export_area(cena)
    largura, altura = round(area.width()), round(area.height())
    gerador = QSvgGenerator()
    gerador.setFileName(str(caminho))
    gerador.setSize(QSize(largura, altura))
    gerador.setViewBox(QRect(0, 0, largura, altura))
    gerador.setTitle(titulo)
    painter = QPainter()
    if not painter.begin(gerador):
        raise OSError(f"não foi possível gravar {caminho}")
    painter.fillRect(QRectF(0, 0, largura, altura), QColor("white"))
    _render(cena, painter, QRectF(0, 0, largura, altura), area)
    painter.end()


def _write_pdf(cena: DiagramScene, caminho: Path, titulo: str) -> None:
    area = export_area(cena)
    escritor = QPdfWriter(str(caminho))
    escritor.setTitle(titulo)
    escritor.setResolution(72)  # 1 unidade do desenho = 1 ponto
    escritor.setPageSize(QPageSize(QSizeF(area.width(), area.height()), QPageSize.Unit.Point))
    escritor.setPageMargins(QMarginsF(0, 0, 0, 0))
    painter = QPainter()
    if not painter.begin(escritor):
        raise OSError(f"não foi possível gravar {caminho}")
    _render(cena, painter, QRectF(0, 0, area.width(), area.height()), area)
    painter.end()


def export_diagram(cena: DiagramScene, caminho: Path, titulo: str = "") -> None:
    """Grava o desenho no formato da extensão do arquivo."""
    formato = caminho.suffix.lower().lstrip(".")
    if formato in ("png", "jpg", "jpeg"):
        imagem = render_image(cena)
        qualidade = 95 if formato != "png" else -1
        if not imagem.save(str(caminho), None, qualidade):
            raise OSError(f"não foi possível gravar {caminho}")
    elif formato == "svg":
        _write_svg(cena, caminho, titulo)
    elif formato == "pdf":
        _write_pdf(cena, caminho, titulo)
    else:
        raise ValueError(f"formato não suportado: {caminho.suffix or '(sem extensão)'}")
