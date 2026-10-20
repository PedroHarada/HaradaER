"""Operações de desenho: o que mostrar, sem depender de nenhuma biblioteca gráfica."""

from __future__ import annotations

from dataclasses import dataclass

from haradaer.core.appearance.style import BLACK, RGBA


@dataclass(frozen=True)
class Stroke:
    """Traço. `double` desenha duas linhas (o TerraER usa isso para entidades e relações fracas)."""

    color: RGBA = BLACK
    width: float = 1.0
    double: bool = False
    factor: float = 3.0  # faixas de largura `width` com vão de `width * (factor - 1)`
    dashes: tuple[float, ...] = ()  # em múltiplos da espessura, como no Java


@dataclass(frozen=True)
class FontSpec:
    family: str = "Dialog"
    size: float = 12.0
    bold: bool = False
    italic: bool = False
    underline: bool = False


@dataclass(frozen=True)
class ShapeOp:
    kind: str  # "rect", "ellipse" ou "diamond"
    x: float
    y: float
    w: float
    h: float
    fill: RGBA | None
    stroke: Stroke | None


@dataclass(frozen=True)
class TextOp:
    """Texto com o canto superior esquerdo em (x, y)."""

    x: float
    y: float
    text: str
    font: FontSpec
    color: RGBA = BLACK
    dashes: tuple[float, ...] = ()


@dataclass(frozen=True)
class PolylineOp:
    points: tuple[tuple[float, float], ...]
    stroke: Stroke


@dataclass(frozen=True)
class ArcOp:
    """Arco de círculo, em graus, anti-horário a partir das 3 horas (como o `drawArc` do Java)."""

    cx: float
    cy: float
    radius: float
    start: float
    span: float
    stroke: Stroke


@dataclass(frozen=True)
class ImageOp:
    x: float
    y: float
    w: float
    h: float
    data: bytes


DrawOp = ShapeOp | TextOp | PolylineOp | ArcOp | ImageOp
