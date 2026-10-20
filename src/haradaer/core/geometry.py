"""Geometria do desenho: caixa dos elementos e pontos das conexões.

O TerraER liga as conexões ao elemento por um conector retangular (`rConnector`): a linha vai do
centro de um elemento ao centro do outro e termina onde cruza a borda da forma principal do
elemento (conferido numericamente nas amostras gravadas pelo TerraER).
"""

from __future__ import annotations

from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import parse_number

SHAPE_PART_TAGS = ("r", "diamond", "e", "circ")

Rect = tuple[float, float, float, float]  # x, y, largura, altura
Point = tuple[float, float]


def shape_part(no: Element) -> Element | None:
    """Forma principal do elemento: a primeira parte que não é texto."""
    grupo = no.child("children")
    for parte in grupo.children if grupo else []:
        if parte.tag in SHAPE_PART_TAGS:
            return parte
    return None


def part_rect(parte: Element) -> Rect:
    def numero(nome: str) -> float:
        valor = parte.attrs.get(nome)
        return parse_number(valor) if valor is not None else 0.0

    return (numero("x"), numero("y"), numero("w"), numero("h"))


def node_rect(no: Element) -> Rect | None:
    forma = shape_part(no)
    return part_rect(forma) if forma is not None else None


def center(rect: Rect) -> Point:
    return (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)


def chop(rect: Rect, alvo: Point) -> Point:
    """Ponto em que a reta do centro de `rect` até `alvo` cruza a borda de `rect`."""
    x, y, w, h = rect
    cx, cy = center(rect)
    dx, dy = alvo[0] - cx, alvo[1] - cy
    if dx == 0 and dy == 0 or w == 0 or h == 0:
        return (cx, cy)
    inf = float("inf")
    horizontal = (w / 2) / abs(dx) if dx else inf  # escala até a borda esquerda/direita
    vertical = (h / 2) / abs(dy) if dy else inf  # escala até a borda de cima/baixo
    if horizontal <= vertical:  # a coordenada da borda é usada tal qual, sem conta
        return (x + w if dx > 0 else x, cy + dy * horizontal)
    return (cx + dx * vertical, y + h if dy > 0 else y)


def connection_points(origem: Rect, destino: Rect) -> tuple[Point, Point]:
    """Pontos inicial e final da linha entre dois elementos."""
    return (chop(origem, center(destino)), chop(destino, center(origem)))
