"""Vista do diagrama: zoom, rolagem, gestos de trackpad (RF-15) e as ferramentas de edição.

Gestos verificados em Linux/Wayland com Qt 6.12 (`docs/INVESTIGACOES.md`):
- pinça chega como `QNativeGestureEvent` do tipo `ZoomNativeGesture`, com o fator no `value()`;
- rolagem com dois dedos chega como `QWheelEvent` com `pixelDelta`;
- `QPinchGesture` não é usado: não dispara no Wayland.

Ferramentas: selecionar (clicar, arrastar, laço), criar elemento (um clique) e conectar (arrastar
de um elemento a outro). A vista só traduz o mouse em pedidos ao `Editor`.
"""

from __future__ import annotations

import math
from typing import NamedTuple

import shiboken6
from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QContextMenuEvent,
    QKeyEvent,
    QMouseEvent,
    QNativeGestureEvent,
    QPainter,
    QPainterPath,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QMenu,
)

from haradaer.core.appearance import FontSpec, TextOp
from haradaer.core.appearance.describe import font_of
from haradaer.core.commands import can_move, connection_path, nested_nodes
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import nearest_segment, node_rect
from haradaer.core.rules import is_valid_connection
from haradaer.gui.editor import Editor
from haradaer.gui.inline_edit import InlineEdit
from haradaer.gui.qt_utils import qfont
from haradaer.gui.scene.items import FigureItem, op_bounds

MIN_ZOOM = 0.05
MAX_ZOOM = 20.0
WHEEL_ZOOM_PER_NOTCH = 1.0015  # por unidade de angleDelta (120 por "clique" da roda)
ZOOM_STEP = 1.25
DRAG_THRESHOLD = 3.0  # pixels da tela antes de um clique virar arrasto

GENERALIZATION_LABEL_FONT = FontSpec(size=12.0, italic=True)
VALID_COLOR = QColor(0, 150, 60)
INVALID_COLOR = QColor(220, 0, 0)

GRID_SIZE = 10.0  # unidades do desenho
GRID_MIN_PX = 6.0  # abaixo disso a grade é desenhada com passo maior (só a vista)
GRID_COLOR = QColor(225, 228, 235)
HANDLE_PX = 7.0  # lado das alças de redimensionar, em pixels da tela
MID_HANDLE_PX = 5.0  # alça do meio de um trecho da linha (arrastar cria um vértice)
LINE_HIT_PX = 6.0  # distância, em pixels, para o duplo clique acertar a linha
HANDLE_COLOR = QColor(40, 120, 255)

# Alças: nome -> (lado horizontal, lado vertical) que ela mexe; -1 esquerda/cima, 1 direita/baixo.
HANDLES: dict[str, tuple[int, int]] = {
    "nw": (-1, -1),
    "n": (0, -1),
    "ne": (1, -1),
    "e": (1, 0),
    "se": (1, 1),
    "s": (0, 1),
    "sw": (-1, 1),
    "w": (-1, 0),
}
_HANDLE_CURSORS = {
    "nw": Qt.CursorShape.SizeFDiagCursor,
    "se": Qt.CursorShape.SizeFDiagCursor,
    "ne": Qt.CursorShape.SizeBDiagCursor,
    "sw": Qt.CursorShape.SizeBDiagCursor,
    "n": Qt.CursorShape.SizeVerCursor,
    "s": Qt.CursorShape.SizeVerCursor,
    "e": Qt.CursorShape.SizeHorCursor,
    "w": Qt.CursorShape.SizeHorCursor,
}


def resized_rect(
    original: tuple[float, float, float, float],
    alca: str,
    x: float,
    y: float,
    minimo: tuple[float, float],
) -> tuple[float, float, float, float]:
    """Caixa nova ao arrastar a alça até (x, y). O lado oposto fica parado; respeita o mínimo."""
    esquerda, topo, w, h = original
    direita, base = esquerda + w, topo + h
    lado_x, lado_y = HANDLES[alca]
    if lado_x < 0:
        esquerda = min(x, direita - minimo[0])
    elif lado_x > 0:
        direita = max(x, esquerda + minimo[0])
    if lado_y < 0:
        topo = min(y, base - minimo[1])
    elif lado_y > 0:
        base = max(y, topo + minimo[1])
    return (esquerda, topo, direita - esquerda, base - topo)


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
        self.grid: float | None = None
        self._drag_start: QPointF | None = None  # cena: onde o arrasto começou (para a grade)
        self._drag_anchor: tuple[NodeFigure, float, float] | None = None
        self._drag_moved = (0.0, 0.0)
        self._resizing: tuple[NodeFigure, str, tuple[float, float, float, float]] | None = None
        self._bend_drag: tuple[ConnectionFigure, int] | None = None
        self._reconnecting: tuple[ConnectionFigure, str] | None = None
        self._reconnect_preview: QGraphicsPathItem | None = None
        scene.selectionChanged.connect(self._repaint_handles)
        scene.changed.connect(self._repaint_handles)
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

    # --- grade -------------------------------------------------------------------------------

    def set_grid(self, ligada: bool) -> None:
        """Mostra a grade e faz criar, mover e redimensionar encaixarem nela."""
        self.grid = GRID_SIZE if ligada else None
        self.resetCachedContent()
        self.viewport().update()

    def snap(self, valor: float) -> float:
        return valor if self.grid is None else round(valor / self.grid) * self.grid

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)
        if self.grid is None:
            return
        passo = self.grid
        while passo * self.zoom < GRID_MIN_PX:
            passo *= 5
        pen = QPen(GRID_COLOR, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        x = math.floor(rect.left() / passo) * passo
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += passo
        y = math.floor(rect.top() / passo) * passo
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += passo

    # --- alças de redimensionar --------------------------------------------------------------

    def _repaint_handles(self, *_args) -> None:
        if shiboken6.isValid(self):
            self.viewport().update()

    def resizable(self) -> NodeFigure | None:
        """O elemento que mostra alças: só quando ele é o único selecionado."""
        if self.tool.kind != "select" or not shiboken6.isValid(self._scene):
            return None
        figuras = self._scene.selected_figures()
        if len(figuras) == 1 and isinstance(figuras[0], NodeFigure):
            if node_rect(figuras[0]) is not None:
                return figuras[0]
        return None

    def handle_rects(self) -> dict[str, QRectF]:
        """Alças do elemento selecionado, em coordenadas da cena (tamanho fixo na tela)."""
        no = self.resizable()
        if no is None:
            return {}
        x, y, w, h = node_rect(no)  # type: ignore[misc]
        lado = HANDLE_PX / self.zoom
        alcas = {}
        for nome, (lado_x, lado_y) in HANDLES.items():
            cx = x + w * (lado_x + 1) / 2
            cy = y + h * (lado_y + 1) / 2
            alcas[nome] = QRectF(cx - lado / 2, cy - lado / 2, lado, lado)
        return alcas

    def _handle_at(self, pos: QPointF) -> str | None:
        folga = 2 / self.zoom
        for nome, quadro in self.handle_rects().items():
            if quadro.adjusted(-folga, -folga, folga, folga).contains(pos):
                return nome
        return None

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)
        pen = QPen(HANDLE_COLOR, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor("white"))
        for quadro in self.handle_rects().values():
            painter.drawRect(quadro)
        for tipo, _, quadro in self.connection_handles():
            if tipo == "mid":
                painter.setBrush(HANDLE_COLOR)
                painter.drawEllipse(quadro)
            else:
                painter.setBrush(HANDLE_COLOR if tipo in ("start", "end") else QColor("white"))
                painter.drawRect(quadro)

    # --- alças da linha de uma conexão --------------------------------------------------------

    def editable_connection(self) -> ConnectionFigure | None:
        """A conexão que mostra alças de vértice: só quando ela é a única selecionada."""
        if self.tool.kind != "select" or not shiboken6.isValid(self._scene):
            return None
        figuras = self._scene.selected_figures()
        if len(figuras) == 1 and isinstance(figuras[0], ConnectionFigure):
            if len(figuras[0].points) >= 2:
                return figuras[0]
        return None

    def connection_handles(self) -> list[tuple[str, int, QRectF]]:
        """Alças da conexão selecionada: pontas ("start", "end"), vértices ("bend", índice) e
        meio de cada trecho ("mid", índice do trecho), em coordenadas da cena."""
        conexao = self.editable_connection()
        if conexao is None:
            return []
        caminho = connection_path(conexao)
        lado, meio = HANDLE_PX / self.zoom, MID_HANDLE_PX / self.zoom

        def quadro(x: float, y: float, tamanho: float) -> QRectF:
            return QRectF(x - tamanho / 2, y - tamanho / 2, tamanho, tamanho)

        alcas = [("start", 0, quadro(*caminho[0], lado)), ("end", 0, quadro(*caminho[-1], lado))]
        alcas += [("bend", i, quadro(x, y, lado)) for i, (x, y) in enumerate(caminho[1:-1])]
        for i, ((x1, y1), (x2, y2)) in enumerate(zip(caminho, caminho[1:], strict=False)):
            alcas.append(("mid", i, quadro((x1 + x2) / 2, (y1 + y2) / 2, meio)))
        return alcas

    def _connection_handle_at(self, pos: QPointF) -> tuple[str, int] | None:
        folga = 2 / self.zoom
        for tipo, indice, quadro in self.connection_handles():
            if quadro.adjusted(-folga, -folga, folga, folga).contains(pos):
                return (tipo, indice)
        return None

    def _begin_line_edit(self, alca: tuple[str, int], pos: QPointF) -> None:
        conexao = self.editable_connection()
        assert conexao is not None and self.editor is not None
        tipo, indice = alca
        if tipo in ("start", "end"):
            self._reconnecting = (conexao, tipo)
            self._reconnect_preview = QGraphicsPathItem()
            self._reconnect_preview.setZValue(1e9)
            self._scene.addItem(self._reconnect_preview)
            self._update_reconnect(pos)
            return
        self._scene.hold_extent(True)
        if tipo == "mid":
            self.editor.history.begin_macro("Adicionar vértice")
            self.editor.add_bend(conexao, indice, (self.snap(pos.x()), self.snap(pos.y())))
        else:
            self.editor.history.begin_macro("Mover vértice")
        self._bend_drag = (conexao, indice)

    def _drag_bend(self, pos: QPointF) -> None:
        assert self._bend_drag is not None and self.editor is not None
        conexao, indice = self._bend_drag
        ponto = (self.snap(pos.x()), self.snap(pos.y()))
        if connection_path(conexao)[indice + 1] != ponto:
            self.editor.move_bend(conexao, indice, ponto)

    def _end_bend_drag(self) -> None:
        if self._bend_drag is not None and self.editor is not None:
            self._bend_drag = None
            self.editor.history.end_macro()
            self._scene.hold_extent(False)

    def _update_reconnect(self, pos: QPointF) -> None:
        assert self._reconnecting is not None and self._reconnect_preview is not None
        conexao, ponta = self._reconnecting
        caminho = connection_path(conexao)
        if ponta == "start":
            caminho[0] = (pos.x(), pos.y())
        else:
            caminho[-1] = (pos.x(), pos.y())
        linha = QPainterPath(QPointF(*caminho[0]))
        for ponto in caminho[1:]:
            linha.lineTo(QPointF(*ponto))
        alvo = self._reconnect_target(pos)
        cor = QColor(80, 80, 80)
        if alvo is not None:
            inicio = alvo if ponta == "start" else conexao.start
            fim = conexao.end if ponta == "start" else alvo
            if inicio is not None and fim is not None:
                valida = is_valid_connection(conexao.tag, inicio.tag, fim.tag)
                cor = VALID_COLOR if valida else INVALID_COLOR
        pen = QPen(cor, 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        self._reconnect_preview.setPen(pen)
        self._reconnect_preview.setPath(linha)

    def _reconnect_target(self, pos: QPointF) -> NodeFigure | None:
        assert self._reconnecting is not None
        conexao, ponta = self._reconnecting
        outro = conexao.end if ponta == "start" else conexao.start
        no = self._node_at(pos)
        return None if no is None or no is outro else no

    def _finish_reconnect(self, pos: QPointF | None) -> None:
        if self._reconnecting is None:
            return
        alvo = self._reconnect_target(pos) if pos is not None else None
        conexao, ponta = self._reconnecting
        self._reconnecting = None
        if self._reconnect_preview is not None:
            self._scene.removeItem(self._reconnect_preview)
            self._reconnect_preview = None
        if alvo is not None and self.editor is not None:
            self.editor.reconnect(conexao, ponta, alvo)
            self._scene.select_only(conexao)

    def _on_line(self, conexao: ConnectionFigure, pos: QPointF) -> tuple[int, float]:
        return nearest_segment(connection_path(conexao), (pos.x(), pos.y()))

    def _label_hit(self, item: FigureItem, pos: QPointF) -> bool:
        """O clique caiu no rótulo de texto da conexão (o da generalização é editável)."""
        return any(isinstance(op, TextOp) and op_bounds(op).contains(pos) for op in item.ops)

    def connection_menu(self, conexao: ConnectionFigure, pos: QPointF) -> QMenu:
        """Menu do botão direito sobre uma conexão."""
        assert self.editor is not None
        editor = self.editor
        menu = QMenu(self)
        alca = self._connection_handle_at(pos)
        if alca is not None and alca[0] == "bend":
            menu.addAction("&Remover vértice", lambda: editor.remove_bend(conexao, alca[1]))
        else:
            trecho, _ = self._on_line(conexao, pos)
            ponto = (self.snap(pos.x()), self.snap(pos.y()))
            menu.addAction(
                "&Adicionar vértice aqui", lambda: editor.add_bend(conexao, trecho, ponto)
            )
        endireitar = menu.addAction("&Endireitar linha", lambda: editor.straighten(conexao))
        endireitar.setEnabled(len(conexao.points) > 2)
        return menu

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.tool.kind != "select" or self.editor is None:
            super().contextMenuEvent(event)
            return
        pos = self.mapToScene(event.pos())
        item = self._item_at(pos)
        conexao = self.editable_connection()
        if conexao is None or self._connection_handle_at(pos) is None:
            if item is None or not item.is_connection:
                super().contextMenuEvent(event)
                return
            assert isinstance(item.figure, ConnectionFigure)
            self._scene.select_only(item.figure)
            conexao = item.figure
        self.connection_menu(conexao, pos).exec(event.globalPos())

    def _begin_resize(self, alca: str) -> None:
        no = self.resizable()
        assert no is not None and self.editor is not None
        rect = node_rect(no)
        assert rect is not None
        self._resizing = (no, alca, rect)
        self._scene.hold_extent(True)
        self.editor.history.begin_macro("Redimensionar")

    def _resize_to(self, pos: QPointF) -> None:
        assert self._resizing is not None and self.editor is not None
        no, alca, original = self._resizing
        rect = resized_rect(
            original, alca, self.snap(pos.x()), self.snap(pos.y()), self.editor.min_size(no)
        )
        if rect != node_rect(no):
            self.editor.resize(no, rect)

    def _end_resize(self) -> None:
        if self._resizing is not None and self.editor is not None:
            self._resizing = None
            self.editor.history.end_macro()
            self._scene.hold_extent(False)

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
        self._end_resize()
        self._end_bend_drag()
        self._finish_reconnect(None)
        if self._inline is not None:
            self._inline.cancel()

    def _scene_pos(self, event: QMouseEvent) -> QPointF:
        return self.mapToScene(event.position().toPoint())

    def _node_at(self, pos: QPointF) -> NodeFigure | None:
        """O elemento sob o mouse, inclusive um que esteja dentro de um grupo."""
        item = self._item_at(pos, nodes_only=True)
        if item is None:
            return None
        if isinstance(item.figure, NodeFigure):
            return item.figure
        for no in reversed(nested_nodes(item.figure)):  # o de cima primeiro
            rect = node_rect(no)
            if rect is not None and QRectF(*rect).contains(pos):
                return no
        return None

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
            alca = self._handle_at(pos)
            if alca is not None:
                self._begin_resize(alca)
                return
            alca_linha = self._connection_handle_at(pos)
            if alca_linha is not None:
                self._begin_line_edit(alca_linha, pos)
                return
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
                self._drag_start, self._drag_moved = pos, (0.0, 0.0)
                self._drag_anchor = None
                ancora = item.figure if isinstance(item.figure, NodeFigure) else None
                rect = node_rect(ancora) if ancora is not None else None
                if ancora is not None and rect is not None:
                    self._drag_anchor = (ancora, rect[0], rect[1])

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
        if self._resizing is not None:
            self._resize_to(self._scene_pos(event))
            return
        if self._bend_drag is not None:
            self._drag_bend(self._scene_pos(event))
            return
        if self._reconnecting is not None:
            self._update_reconnect(self._scene_pos(event))
            return
        if self._drag_from is not None and self.editor is not None:
            self._drag_to(event)
            return
        if self.tool.kind == "select" and event.buttons() == Qt.MouseButton.NoButton:
            pos = self._scene_pos(event)
            alca = self._handle_at(pos)
            alca_linha = self._connection_handle_at(pos)
            if alca is not None:
                cursor = _HANDLE_CURSORS[alca]
            elif alca_linha is not None:
                pontas = alca_linha[0] in ("start", "end")
                cursor = Qt.CursorShape.CrossCursor if pontas else Qt.CursorShape.SizeAllCursor
            else:
                cursor = Qt.CursorShape.ArrowCursor
            self.viewport().setCursor(cursor)
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
        if self._resizing is not None and event.button() == Qt.MouseButton.LeftButton:
            self._end_resize()
            return
        if self._bend_drag is not None and event.button() == Qt.MouseButton.LeftButton:
            self._end_bend_drag()
            return
        if self._reconnecting is not None and event.button() == Qt.MouseButton.LeftButton:
            self._finish_reconnect(self._scene_pos(event))
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
            pos = self._scene_pos(event)
            alca = self._connection_handle_at(pos)
            conexao = self.editable_connection()
            if alca is not None and alca[0] == "bend" and conexao is not None:
                self.editor.remove_bend(conexao, alca[1])  # como o TerraER
                return
            item = self._item_at(pos)
            if item is not None and item.is_connection and not self._label_hit(item, pos):
                assert isinstance(item.figure, ConnectionFigure)
                trecho, distancia = self._on_line(item.figure, pos)
                if distancia * self.zoom <= LINE_HIT_PX:  # duplo clique na linha: novo vértice
                    ponto = (self.snap(pos.x()), self.snap(pos.y()))
                    self.editor.add_bend(item.figure, trecho, ponto)
                    self._scene.select_only(item.figure)
                    return
            if item is not None:
                no = self._node_at(pos) if item.figure.tag == "g" else None
                self._edit_text(no if no is not None else item.figure)
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
        no = self.editor.create(self.tool.tag, self.snap(pos.x()), self.snap(pos.y()))
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
        assert self._drag_start is not None
        total_x, total_y = pos.x() - self._drag_start.x(), pos.y() - self._drag_start.y()
        if self.grid is not None and self._drag_anchor is not None:
            # O canto do elemento sob o mouse cai na grade; os outros vão junto.
            _, x0, y0 = self._drag_anchor
            total_x, total_y = self.snap(x0 + total_x) - x0, self.snap(y0 + total_y) - y0
        dx, dy = total_x - self._drag_moved[0], total_y - self._drag_moved[1]
        self._drag_from = pos
        if dx or dy:
            self._drag_moved = (total_x, total_y)
            self.editor.move([f for f in self._scene.selected_figures() if can_move(f)], dx, dy)

    # --- conectar ----------------------------------------------------------------------------

    def _begin_connection(self, pos: QPointF) -> None:
        no = self._node_at(pos)
        if no is None:
            return
        self._connect_from = no
        self._preview = QGraphicsLineItem()
        self._preview.setZValue(1e9)
        self._scene.addItem(self._preview)
        self._update_connection(pos)

    def _target_at(self, pos: QPointF) -> NodeFigure | None:
        no = self._node_at(pos)
        return None if no is self._connect_from else no

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
