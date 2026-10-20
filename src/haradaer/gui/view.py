"""Vista do diagrama: zoom, rolagem, gestos de trackpad (RF-15) e as ferramentas de edição.

Gestos verificados em Linux/Wayland com Qt 6.12 (`docs/INVESTIGACOES.md`):
- pinça chega como `QNativeGestureEvent` do tipo `ZoomNativeGesture`, com o fator no `value()`;
- rolagem com dois dedos chega como `QWheelEvent` com `pixelDelta`;
- `QPinchGesture` não é usado: não dispara no Wayland.

Ferramentas: selecionar (clicar, arrastar, laço), criar elemento (um clique) e conectar (arrastar
de um elemento a outro). A vista só traduz o mouse em pedidos ao `Editor`.
"""

from __future__ import annotations

from typing import NamedTuple

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QMouseEvent,
    QNativeGestureEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsScene, QGraphicsView

from haradaer.core.appearance import FontSpec
from haradaer.core.appearance.describe import font_of
from haradaer.core.commands import can_move
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import node_rect
from haradaer.core.rules import is_valid_connection
from haradaer.gui.editor import Editor
from haradaer.gui.inline_edit import InlineEdit
from haradaer.gui.qt_utils import qfont
from haradaer.gui.scene.items import FigureItem

MIN_ZOOM = 0.05
MAX_ZOOM = 20.0
WHEEL_ZOOM_PER_NOTCH = 1.0015  # por unidade de angleDelta (120 por "clique" da roda)
ZOOM_STEP = 1.25
DRAG_THRESHOLD = 3.0  # pixels da tela antes de um clique virar arrasto

GENERALIZATION_LABEL_FONT = FontSpec(size=12.0, italic=True)
VALID_COLOR = QColor(0, 150, 60)
INVALID_COLOR = QColor(220, 0, 0)


class Tool(NamedTuple):
    kind: str  # "select", "create" ou "connect"
    tag: str | None = None


SELECT = Tool("select")


class DiagramView(QGraphicsView):
    zoom_changed = Signal(float)
    tool_changed = Signal(object)
    message = Signal(str)

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self._scene = scene  # o Qt não é dono da cena; sem isto ela pode ser coletada
        self.editor: Editor | None = None
        self.tool = SELECT
        self._inline: InlineEdit | None = None
        self._drag_from: QPointF | None = None  # cena: onde o arrasto de elementos começou
        self._drag_origin_px: QPointF | None = None
        self._dragging = False
        self._creating = False
        self._pan_last: QPointF | None = None
        self._connect_from: NodeFigure | None = None
        self._preview: QGraphicsLineItem | None = None
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

    # --- zoom --------------------------------------------------------------------------------

    @property
    def zoom(self) -> float:
        return self.transform().m11()

    def set_zoom(self, valor: float) -> None:
        valor = min(max(valor, MIN_ZOOM), MAX_ZOOM)
        self.resetTransform()
        self.scale(valor, valor)
        self.zoom_changed.emit(self.zoom)

    def zoom_by(self, fator: float) -> None:
        self.set_zoom(self.zoom * fator)

    def zoom_in(self) -> None:
        self.zoom_by(ZOOM_STEP)

    def zoom_out(self) -> None:
        self.zoom_by(1 / ZOOM_STEP)

    def zoom_actual(self) -> None:
        self.set_zoom(1.0)

    def zoom_fit(self) -> None:
        area: QRectF = self.scene().itemsBoundingRect()
        if area.isEmpty():
            return
        self.fitInView(area.adjusted(-20, -20, 20, 20), Qt.AspectRatioMode.KeepAspectRatio)
        self.set_zoom(self.zoom)  # aplica os limites e avisa quem acompanha o zoom

    def viewportEvent(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture and isinstance(event, QNativeGestureEvent):
            if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                self.zoom_by(1.0 + event.value())
                event.accept()
                return True
        return super().viewportEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_by(WHEEL_ZOOM_PER_NOTCH ** event.angleDelta().y())
            event.accept()
            return
        pixels = event.pixelDelta()
        if not pixels.isNull():  # rolagem com dois dedos no trackpad
            horizontal, vertical = self.horizontalScrollBar(), self.verticalScrollBar()
            horizontal.setValue(horizontal.value() - pixels.x())
            vertical.setValue(vertical.value() - pixels.y())
            event.accept()
            return
        super().wheelEvent(event)

    # --- ferramentas -------------------------------------------------------------------------

    def set_editor(self, editor: Editor) -> None:
        self._cancel_interaction()
        self.editor = editor

    def set_tool(self, tool: Tool) -> None:
        self._cancel_interaction()
        self.tool = tool
        self.viewport().setCursor(
            Qt.CursorShape.ArrowCursor if tool.kind == "select" else Qt.CursorShape.CrossCursor
        )
        self.tool_changed.emit(tool)

    def _cancel_interaction(self) -> None:
        self._end_connection()
        if self._inline is not None:
            self._inline.cancel()

    def _scene_pos(self, event: QMouseEvent) -> QPointF:
        return self.mapToScene(event.position().toPoint())

    def _item_at(self, pos: QPointF, *, nodes_only: bool = False) -> FigureItem | None:
        for item in self._scene.items(pos):
            if isinstance(item, FigureItem) and not (nodes_only and item.is_connection):
                return item
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_last = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton and self.editor is not None:
            pos = self._scene_pos(event)
            if self.tool.kind == "create":
                self._create(
                    pos, keep_tool=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                )
                return
            if self.tool.kind == "connect":
                self._begin_connection(pos)
                return
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self.tool.kind == "select":
            pos = self._scene_pos(event)
            item = self._item_at(pos)
            if item is not None and item.isSelected():
                self._drag_from, self._drag_origin_px = pos, event.position()
                self._dragging = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_last is not None:
            delta = event.position() - self._pan_last
            self._pan_last = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - round(delta.x())
            )
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - round(delta.y()))
            return
        if self._connect_from is not None:
            self._update_connection(self._scene_pos(event))
            return
        if self._drag_from is not None and self.editor is not None:
            self._drag_to(event)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._pan_last is not None:
            self._pan_last = None
            self.viewport().setCursor(
                Qt.CursorShape.ArrowCursor
                if self.tool.kind == "select"
                else Qt.CursorShape.CrossCursor
            )
            return
        if self._connect_from is not None and event.button() == Qt.MouseButton.LeftButton:
            self._finish_connection(
                self._scene_pos(event),
                keep_tool=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier),
            )
            return
        if self._drag_from is not None:
            if self._dragging and self.editor is not None:
                self.editor.end_move()
                self._scene.hold_extent(False)
            self._drag_from = self._drag_origin_px = None
            self._dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.tool.kind == "select" and self.editor is not None:
            item = self._item_at(self._scene_pos(event))
            if item is not None:
                self._edit_text(item.figure)
                return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self.editor is not None:
            self.editor.delete(self._scene.selected_figures())
            return
        if event.key() == Qt.Key.Key_Escape:
            self.set_tool(SELECT)
            return
        super().keyPressEvent(event)

    # --- criar -------------------------------------------------------------------------------

    def _create(self, pos: QPointF, *, keep_tool: bool) -> None:
        assert self.editor is not None and self.tool.tag is not None
        self.editor.history.begin_macro("Criar")  # criar e dar nome é um passo só
        self._creating = True
        no = self.editor.create(self.tool.tag, pos.x(), pos.y())
        self._scene.select_only(no)
        if not keep_tool:
            self.set_tool(SELECT)
        self._edit_text(no)
        if self._inline is None:
            self._finish_creation()

    def _finish_creation(self) -> None:
        if self._creating and self.editor is not None:
            self._creating = False
            self.editor.history.end_macro()

    # --- mover -------------------------------------------------------------------------------

    def _drag_to(self, event: QMouseEvent) -> None:
        assert self.editor is not None and self._drag_from is not None
        if not self._dragging:
            origem = self._drag_origin_px
            assert origem is not None
            if (event.position() - origem).manhattanLength() < DRAG_THRESHOLD:
                return
            movediveis = [f for f in self._scene.selected_figures() if can_move(f)]
            if not movediveis:
                self._drag_from = None
                return
            self._dragging = True
            self._scene.hold_extent(True)
            self.editor.begin_move()
        pos = self._scene_pos(event)
        dx, dy = pos.x() - self._drag_from.x(), pos.y() - self._drag_from.y()
        self._drag_from = pos
        self.editor.move([f for f in self._scene.selected_figures() if can_move(f)], dx, dy)

    # --- conectar ----------------------------------------------------------------------------

    def _begin_connection(self, pos: QPointF) -> None:
        item = self._item_at(pos, nodes_only=True)
        if item is None or not isinstance(item.figure, NodeFigure):
            return
        self._connect_from = item.figure
        self._preview = QGraphicsLineItem()
        self._preview.setZValue(1e9)
        self._scene.addItem(self._preview)
        self._update_connection(pos)

    def _target_at(self, pos: QPointF) -> NodeFigure | None:
        item = self._item_at(pos, nodes_only=True)
        if item is None or item.figure is self._connect_from:
            return None
        return item.figure if isinstance(item.figure, NodeFigure) else None

    def _update_connection(self, pos: QPointF) -> None:
        origem, previa = self._connect_from, self._preview
        if origem is None or previa is None or self.tool.tag is None:
            return
        rect = node_rect(origem)
        if rect is None:
            return
        alvo = self._target_at(pos)
        cor = QColor(80, 80, 80)
        if alvo is not None:
            valida = is_valid_connection(self.tool.tag, origem.tag, alvo.tag)
            cor = VALID_COLOR if valida else INVALID_COLOR
            self.message.emit(
                "" if valida else "Esta conexão não é aceita entre estes elementos (será marcada)."
            )
        pen = QPen(cor, 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        previa.setPen(pen)
        previa.setLine(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2, pos.x(), pos.y())

    def _end_connection(self) -> None:
        if self._preview is not None:
            self._scene.removeItem(self._preview)
        self._preview = None
        self._connect_from = None

    def _finish_connection(self, pos: QPointF, *, keep_tool: bool) -> None:
        assert self.editor is not None and self.tool.tag is not None
        origem, alvo = self._connect_from, self._target_at(pos)
        self._end_connection()
        if origem is not None and alvo is not None:
            conexao = self.editor.connect(self.tool.tag, origem, alvo)
            self._scene.select_only(conexao)
            if not keep_tool:
                self.set_tool(SELECT)

    # --- editar texto ------------------------------------------------------------------------

    def _edit_text(self, figura) -> None:
        editor = self.editor
        if editor is None or self._inline is not None:
            return
        if isinstance(figura, NodeFigure):
            rect = node_rect(figura)
            parte = next((p for p in figura.parts if p.tag in ("t", "tn", "ti")), None)
            if rect is None or parte is None:
                return
            fonte = qfont(font_of(parte))
            area = QRectF(*rect)
            texto = figura.name or ""

            def ao_confirmar(novo: str) -> None:
                editor.rename(figura, novo)

        elif isinstance(figura, ConnectionFigure) and figura.generalization_label is not None:
            pontos = figura.points
            if len(pontos) < 2:
                return
            xs = [float(p.attrs["x"]) for p in pontos]
            ys = [float(p.attrs["y"]) for p in pontos]
            centro = QPointF(sum(xs) / len(xs), sum(ys) / len(ys))
            area = QRectF(centro.x() - 60, centro.y() - 12, 120, 24)
            fonte = qfont(GENERALIZATION_LABEL_FONT)
            texto = figura.generalization_label

            def ao_confirmar(novo: str) -> None:
                editor.set_generalization_label(figura, novo)

        else:
            return
        fonte.setPixelSize(max(6, round(fonte.pixelSize() * self.zoom)))
        quadro: QRect = self.mapFromScene(area).boundingRect()
        quadro.setWidth(max(quadro.width(), 60))
        self._inline = InlineEdit(
            self.viewport(), quadro, texto, fonte, ao_confirmar, self._inline_closed
        )

    def _inline_closed(self) -> None:
        self._inline = None
        self._finish_creation()
        self.setFocus()
