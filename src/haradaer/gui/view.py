"""Vista do diagrama: zoom, rolagem e gestos de trackpad (RF-15).

Gestos verificados em Linux/Wayland com Qt 6.12 (`docs/INVESTIGACOES.md`):
- pinça chega como `QNativeGestureEvent` do tipo `ZoomNativeGesture`, com o fator no `value()`;
- rolagem com dois dedos chega como `QWheelEvent` com `pixelDelta`;
- `QPinchGesture` não é usado: não dispara no Wayland.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QRectF, Qt, Signal
from PySide6.QtGui import QNativeGestureEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

MIN_ZOOM = 0.05
MAX_ZOOM = 20.0
WHEEL_ZOOM_PER_NOTCH = 1.0015  # por unidade de angleDelta (120 por "clique" da roda)
ZOOM_STEP = 1.25


class DiagramView(QGraphicsView):
    zoom_changed = Signal(float)

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self._scene = scene  # o Qt não é dono da cena; sem isto ela pode ser coletada
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

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
