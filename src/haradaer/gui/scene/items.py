"""Item gráfico de uma figura do desenho."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QGraphicsItem

from haradaer.core.appearance import (
    ArcOp,
    DrawOp,
    ImageOp,
    PolylineOp,
    ShapeOp,
    Stroke,
    TextOp,
)
from haradaer.core.appearance.style import RGBA
from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.model.element import Element
from haradaer.gui.qt_utils import QtMeasurer, qcolor, qfont

_MEDIDOR = QtMeasurer()


def shape_path(op: ShapeOp) -> QPainterPath:
    caminho = QPainterPath()
    retangulo = QRectF(op.x, op.y, op.w, op.h)
    if op.kind == "ellipse":
        caminho.addEllipse(retangulo)
    elif op.kind == "diamond":
        caminho.addPolygon(
            QPolygonF(
                [
                    QPointF(op.x + op.w / 2, op.y),
                    QPointF(op.x + op.w, op.y + op.h / 2),
                    QPointF(op.x + op.w / 2, op.y + op.h),
                    QPointF(op.x, op.y + op.h / 2),
                ]
            )
        )
        caminho.closeSubpath()
    else:
        caminho.addRect(retangulo)
    return caminho


def _even(tracejado) -> list[float]:
    """O Qt exige um número par de valores; o Java repete o padrão ímpar."""
    lista = list(tracejado)
    return lista * 2 if len(lista) % 2 else lista


def _pen(traco: Stroke, largura: float | None = None) -> QPen:
    pen = QPen(qcolor(traco.color), traco.width if largura is None else largura)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    if traco.dashes:
        pen.setDashPattern(_even(traco.dashes))
    return pen


def draw_stroke(painter: QPainter, caminho: QPainterPath, traco: Stroke) -> None:
    """Desenha o traço de um caminho.

    O traço duplo do TerraER (`DoubleStroke`) são duas faixas de largura `w` com um vão de
    `w * (fator - 1)`: um traço de largura `w * (fator + 1)` menos um de `w * (fator - 1)`.
    """
    if traco.double:
        externo = QPainterPathStroker()
        externo.setWidth(traco.width * (traco.factor + 1))
        interno = QPainterPathStroker()
        interno.setWidth(traco.width * (traco.factor - 1))
        for pincel in (externo, interno):
            pincel.setCapStyle(Qt.PenCapStyle.FlatCap)
            pincel.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        forma = externo.createStroke(caminho).subtracted(interno.createStroke(caminho))
        painter.fillPath(forma, QBrush(qcolor(traco.color)))
    else:
        painter.setPen(_pen(traco))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(caminho)


def polyline_path(pontos) -> QPainterPath:
    caminho = QPainterPath()
    caminho.moveTo(*pontos[0])
    for ponto in pontos[1:]:
        caminho.lineTo(*ponto)
    return caminho


def paint_op(painter: QPainter, op: DrawOp) -> None:
    if isinstance(op, ShapeOp):
        caminho = shape_path(op)
        if op.fill is not None:
            painter.fillPath(caminho, QBrush(qcolor(op.fill)))
        if op.stroke is not None:
            draw_stroke(painter, caminho, op.stroke)
    elif isinstance(op, TextOp):
        fonte = qfont(op.font)
        painter.setFont(fonte)
        painter.setPen(qcolor(op.color))
        painter.drawText(QPointF(op.x, op.y + QFontMetricsF(fonte).ascent()), op.text)
    elif isinstance(op, PolylineOp):
        draw_stroke(painter, polyline_path(op.points), op.stroke)
    elif isinstance(op, ArcOp):
        painter.setPen(_pen(op.stroke))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        quadro = QRectF(op.cx - op.radius, op.cy - op.radius, 2 * op.radius, 2 * op.radius)
        painter.drawArc(quadro, round(op.start * 16), round(op.span * 16))
    elif isinstance(op, ImageOp):
        imagem = QImage.fromData(op.data)
        if not imagem.isNull():
            painter.drawImage(QRectF(op.x, op.y, op.w, op.h), imagem)


def op_bounds(op: DrawOp) -> QRectF:
    if isinstance(op, ShapeOp):
        folga = 0.0
        if op.stroke is not None:
            folga = op.stroke.width * (op.stroke.factor + 1 if op.stroke.double else 1.0) / 2
        return QRectF(op.x, op.y, op.w, op.h).adjusted(-folga, -folga, folga, folga)
    if isinstance(op, TextOp):
        largura, altura = _MEDIDOR.size(op.text, op.font)
        return QRectF(op.x, op.y, largura, altura)
    if isinstance(op, PolylineOp):
        folga = op.stroke.width * (op.stroke.factor + 1 if op.stroke.double else 1.0) / 2
        return polyline_path(op.points).boundingRect().adjusted(-folga, -folga, folga, folga)
    if isinstance(op, ArcOp):
        r = op.radius + op.stroke.width
        return QRectF(op.cx - r, op.cy - r, 2 * r, 2 * r)
    return QRectF(op.x, op.y, op.w, op.h)


HIT_WIDTH = 10.0  # largura da área de clique de uma linha
SELECTION_COLOR = QColor(40, 120, 255)
PROBLEM_COLOR: RGBA = (220, 0, 0, 255)  # a mesma da prévia de conexão inválida


class FigureItem(QGraphicsItem):
    """Uma figura do arquivo, desenhada a partir das suas operações de desenho.

    O item só mostra: quem muda o modelo é o `Editor`, e o item é atualizado quando o `Document`
    avisa (`set_ops`).
    """

    def __init__(self, figure: Element, ops: list[DrawOp]):
        super().__init__()
        self.figure = figure
        self.is_connection = isinstance(figure, ConnectionFigure)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.ops = ops
        self.problem: str | None = None
        self._limites = QRectF()
        self._area = QPainterPath()
        self._calcular()

    def _calcular(self) -> None:
        self._limites = QRectF()
        for op in self.ops:
            self._limites = self._limites.united(op_bounds(op))
        self._area = self._calcular_area()

    def _calcular_area(self) -> QPainterPath:
        """Onde o clique acerta: a forma do elemento, ou uma faixa em volta da linha."""
        area = QPainterPath()
        area.setFillRule(Qt.FillRule.WindingFill)  # forma e texto se somam, sem "buracos"
        if self.is_connection:
            for op in self.ops:
                if isinstance(op, PolylineOp):
                    faixa = QPainterPathStroker()
                    faixa.setWidth(HIT_WIDTH)
                    area.addPath(faixa.createStroke(polyline_path(op.points)))
            return area
        for op in self.ops:
            if isinstance(op, ShapeOp):
                area.addPath(shape_path(op))
            elif isinstance(op, TextOp):
                area.addRect(op_bounds(op))
        if area.isEmpty():
            area.addRect(self._limites)
        return area

    def set_ops(self, ops: list[DrawOp]) -> None:
        self.prepareGeometryChange()
        self.ops = ops
        self._calcular()
        self.update()

    def shape(self) -> QPainterPath:
        return self._area

    def content_rect(self) -> QRectF:
        """O que o item desenha, sem a folga para o clique."""
        return QRectF(self._limites)

    def boundingRect(self) -> QRectF:
        return self._limites.adjusted(-HIT_WIDTH, -HIT_WIDTH, HIT_WIDTH, HIT_WIDTH)

    def set_problem(self, texto: str | None) -> None:
        """Marca a conexão com problema (RF-09). Fica no item: as `ops` mudam a cada edição."""
        if texto == self.problem:
            return
        self.problem = texto
        self.setToolTip(texto or "")
        self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        exportando = getattr(self.scene(), "exporting", False)
        for op in self.ops:
            if self.problem and not exportando and isinstance(op, (PolylineOp, ArcOp)):
                op = replace(op, stroke=replace(op.stroke, color=PROBLEM_COLOR))
            paint_op(painter, op)
        if self.isSelected() and not exportando:
            self._paint_selection(painter)

    def _paint_selection(self, painter: QPainter) -> None:
        if self.is_connection:
            cor = QColor(SELECTION_COLOR)
            cor.setAlpha(110)
            painter.setPen(QPen(cor, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for op in self.ops:
                if isinstance(op, PolylineOp):
                    painter.drawPath(polyline_path(op.points))
            return
        pen = QPen(SELECTION_COLOR, 1, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._limites.adjusted(-3, -3, 3, 3))
