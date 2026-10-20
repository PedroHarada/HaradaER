"""O que desenhar: estilo, operações de desenho e a descrição das figuras, sem Qt."""

from haradaer.core.appearance.describe import (
    describe_document,
    describe_figure,
    label_position,
    point_on_path,
)
from haradaer.core.appearance.metrics import FixedMeasurer, TextMeasurer
from haradaer.core.appearance.ops import (
    ArcOp,
    DrawOp,
    FontSpec,
    ImageOp,
    PolylineOp,
    ShapeOp,
    Stroke,
    TextOp,
)
from haradaer.core.appearance.style import Style, parse_color

__all__ = [
    "ArcOp",
    "DrawOp",
    "FixedMeasurer",
    "FontSpec",
    "ImageOp",
    "PolylineOp",
    "ShapeOp",
    "Stroke",
    "Style",
    "TextMeasurer",
    "TextOp",
    "describe_document",
    "describe_figure",
    "label_position",
    "parse_color",
    "point_on_path",
]
