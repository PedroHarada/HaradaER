"""Zoom, rolagem e gestos de trackpad (RF-15)."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QNativeGestureEvent, QPointingDevice, QWheelEvent
from PySide6.QtWidgets import QApplication

from haradaer.core import io
from haradaer.gui.scene import DiagramScene
from haradaer.gui.view import MAX_ZOOM, MIN_ZOOM, DiagramView


@pytest.fixture
def vista(qtbot, referencia):
    cena = DiagramScene()
    cena.set_document(io.load(referencia / "amostra-todos-os-tipos.xml"))
    view = DiagramView(cena)
    qtbot.addWidget(view)
    view.resize(300, 200)
    view.show()
    QApplication.processEvents()
    return view


def _gesto(tipo: Qt.NativeGestureType, valor: float) -> QNativeGestureEvent:
    posicao = QPointF(50, 50)
    dispositivo = QPointingDevice.primaryPointingDevice()
    return QNativeGestureEvent(tipo, dispositivo, 2, posicao, posicao, posicao, valor, QPointF())


def _roda(pixels: QPoint, angulo: QPoint, modificadores=Qt.KeyboardModifier.NoModifier):
    posicao = QPointF(50, 50)
    return QWheelEvent(
        posicao,
        posicao,
        pixels,
        angulo,
        Qt.MouseButton.NoButton,
        modificadores,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )


def test_zoom_comeca_em_100(vista):
    assert vista.zoom == pytest.approx(1.0)


def test_ampliar_reduzir_e_tamanho_real(vista):
    vista.zoom_in()
    assert vista.zoom == pytest.approx(1.25)
    vista.zoom_out()
    vista.zoom_out()
    assert vista.zoom == pytest.approx(0.8)
    vista.zoom_actual()
    assert vista.zoom == pytest.approx(1.0)


def test_zoom_tem_limites(vista):
    vista.set_zoom(1000)
    assert vista.zoom == pytest.approx(MAX_ZOOM)
    vista.set_zoom(0.0001)
    assert vista.zoom == pytest.approx(MIN_ZOOM)


def test_zoom_avisa_quem_acompanha(vista, qtbot):
    with qtbot.waitSignal(vista.zoom_changed) as sinal:
        vista.zoom_by(2)
    assert sinal.args == [pytest.approx(2.0)]


def test_ajustar_a_janela_cabe_o_desenho_inteiro(vista):
    vista.zoom_fit()
    assert vista.zoom < 1.0
    area = vista.mapFromScene(vista.scene().itemsBoundingRect()).boundingRect()
    assert vista.viewport().rect().contains(area)


def test_pinca_amplia_e_afasta_reduz(vista):
    """`ZoomNativeGesture` é o evento que o Qt entrega no Wayland (verificado no trackpad)."""
    QApplication.sendEvent(vista.viewport(), _gesto(Qt.NativeGestureType.ZoomNativeGesture, 0.5))
    assert vista.zoom == pytest.approx(1.5)
    QApplication.sendEvent(vista.viewport(), _gesto(Qt.NativeGestureType.ZoomNativeGesture, -0.2))
    assert vista.zoom == pytest.approx(1.2)


def test_pinca_acumula_muitos_eventos_pequenos(vista):
    for _ in range(10):
        QApplication.sendEvent(
            vista.viewport(), _gesto(Qt.NativeGestureType.ZoomNativeGesture, 0.05)
        )
    assert vista.zoom == pytest.approx(1.05**10)


@pytest.mark.parametrize(
    "tipo", [Qt.NativeGestureType.RotateNativeGesture, Qt.NativeGestureType.PanNativeGesture]
)
def test_rotacao_e_deslocamento_nativo_sao_ignorados(vista, tipo):
    QApplication.sendEvent(vista.viewport(), _gesto(tipo, 0.7))
    assert vista.zoom == pytest.approx(1.0)


def test_ctrl_mais_roda_faz_zoom(vista):
    ctrl = Qt.KeyboardModifier.ControlModifier
    QApplication.sendEvent(vista.viewport(), _roda(QPoint(), QPoint(0, 120), ctrl))
    maior = vista.zoom
    assert maior > 1.0
    QApplication.sendEvent(vista.viewport(), _roda(QPoint(), QPoint(0, -240), ctrl))
    assert vista.zoom < maior


def test_rolagem_com_dois_dedos_move_a_vista(vista):
    vista.scene().setSceneRect(0, 0, 3000, 3000)
    QApplication.processEvents()
    horizontal, vertical = vista.horizontalScrollBar(), vista.verticalScrollBar()
    assert horizontal.maximum() > 100 and vertical.maximum() > 100
    h0, v0 = horizontal.value(), vertical.value()
    QApplication.sendEvent(vista.viewport(), _roda(QPoint(-30, -40), QPoint(0, -120)))
    assert horizontal.value() == h0 + 30
    assert vertical.value() == v0 + 40
    QApplication.sendEvent(vista.viewport(), _roda(QPoint(0, 15), QPoint(0, 120)))
    assert vertical.value() == v0 + 25
    assert vista.zoom == pytest.approx(1.0), "rolar não muda o zoom"
