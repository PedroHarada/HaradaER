"""Cena do diagrama: um item por figura, na ordem de empilhamento do arquivo.

A cena acompanha o `Document` pelos eventos que ele emite (figura criada, removida, alterada);
quem edita é o `Editor`, nunca a cena.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsScene

from haradaer.core.appearance import describe_figure
from haradaer.core.model.document import ADDED, CHANGED, REMOVED, REORDERED, Document
from haradaer.core.model.element import Element
from haradaer.core.rules import Issue
from haradaer.gui.qt_utils import QtMeasurer
from haradaer.gui.scene.items import FigureItem
from haradaer.gui.verification import issue_text

MARGIN = 40.0
MIN_AREA = QRectF(0, 0, 1600, 1200)  # espaço para desenhar num modelo novo


class DiagramScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.setBackgroundBrush(QColor("white"))
        # Diagramas de ER são pequenos; sem índice, a busca por posição vale logo após criar.
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self._medidor = QtMeasurer()
        self._itens: dict[int, FigureItem] = {}
        self.document: Document | None = None
        self._extent_held = False

    def set_document(self, documento: Document | None) -> None:
        if self.document is not None:
            self.document.unsubscribe(self._document_event)
        self.clear()
        self._itens.clear()
        self.document = documento
        if documento is None:
            self.setSceneRect(QRectF())
            return
        for figura in documento.figures:
            self._add_item(figura)
        self._restack()
        documento.subscribe(self._document_event)
        self._extent_held = False
        self.setSceneRect(self._wanted_extent())

    def hold_extent(self, segurar: bool) -> None:
        """Durante um arrasto a área não muda (senão o desenho pula sob o mouse)."""
        self._extent_held = segurar
        if not segurar:
            self._grow()

    # --- itens -------------------------------------------------------------------------------

    def item_for(self, figura: Element) -> FigureItem | None:
        return self._itens.get(id(figura))

    def figure_items(self) -> list[FigureItem]:
        return sorted(self._itens.values(), key=lambda i: i.zValue())

    def selected_figures(self) -> list[Element]:
        itens = [i for i in self.selectedItems() if isinstance(i, FigureItem)]
        return [i.figure for i in sorted(itens, key=lambda i: i.zValue())]

    def select_where(self, aceita: Callable[[Element], bool]) -> None:
        """Seleciona exatamente as figuras aceitas (RF-07: selecionar todos do mesmo tipo)."""
        for item in self._itens.values():
            item.setSelected(aceita(item.figure))

    def select_only(self, figura: Element) -> None:
        self.clearSelection()
        item = self.item_for(figura)
        if item is not None:
            item.setSelected(True)

    def show_issues(self, problemas: list[Issue]) -> None:
        """Pinta de vermelho as conexões com problema e limpa as demais (RF-09)."""
        textos = {id(p.figure): issue_text(p) for p in problemas}
        for chave, item in self._itens.items():
            item.set_problem(textos.get(chave))

    def _add_item(self, figura: Element) -> FigureItem | None:
        ops = describe_figure(figura, self._medidor)
        if not ops:
            return None
        item = FigureItem(figura, ops)
        self._itens[id(figura)] = item
        self.addItem(item)
        return item

    def _restack(self) -> None:
        if self.document is None:
            return
        for ordem, figura in enumerate(self.document.figures):
            item = self._itens.get(id(figura))
            if item is not None:
                item.setZValue(ordem)

    def _grow(self) -> None:
        """A área da cena só cresce durante a edição, para a rolagem não pular."""
        if not self._extent_held:
            self.setSceneRect(self.sceneRect().united(self._wanted_extent()))

    def _wanted_extent(self) -> QRectF:
        itens = self.itemsBoundingRect().adjusted(-MARGIN, -MARGIN, MARGIN, MARGIN)
        return itens.united(MIN_AREA)

    def _document_event(self, evento: str, figura: Element | None) -> None:
        if evento == REORDERED:
            self._restack()
            return
        if figura is None:
            return
        if evento == ADDED:
            self._add_item(figura)
            self._restack()
        elif evento == REMOVED:
            item = self._itens.pop(id(figura), None)
            if item is not None:
                self.removeItem(item)
            self._restack()
        elif evento == CHANGED:
            item = self._itens.get(id(figura))
            ops = describe_figure(figura, self._medidor)
            if item is not None:
                item.set_ops(ops)
            elif ops:
                self._add_item(figura)
                self._restack()
        self._grow()
