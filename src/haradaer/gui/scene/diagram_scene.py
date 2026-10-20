"""Cena do diagrama: um item por figura, na ordem de empilhamento do arquivo."""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene

from haradaer.core.appearance import describe_document
from haradaer.core.model.document import Document
from haradaer.gui.qt_utils import QtMeasurer
from haradaer.gui.scene.items import FigureItem

MARGIN = 40.0


class DiagramScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.setBackgroundBrush(QColor("white"))
        self._medidor = QtMeasurer()
        self.document: Document | None = None

    def set_document(self, documento: Document | None) -> None:
        self.clear()
        self.document = documento
        if documento is None:
            self.setSceneRect(QRectF())
            return
        for ordem, (figura, ops) in enumerate(describe_document(documento, self._medidor)):
            if not ops:
                continue
            item = FigureItem(figura, ops)
            item.setZValue(ordem)
            self.addItem(item)
        self.setSceneRect(self.itemsBoundingRect().adjusted(-MARGIN, -MARGIN, MARGIN, MARGIN))

    def figure_items(self) -> list[FigureItem]:
        return sorted(
            (i for i in self.items() if isinstance(i, FigureItem)), key=lambda i: i.zValue()
        )
