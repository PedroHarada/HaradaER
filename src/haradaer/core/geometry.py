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


def route_ends(origem: Rect, destino: Rect, dobras: list[Point]) -> tuple[Point, Point]:
    """Pontas de uma linha com dobras: cada ponta mira a dobra mais próxima dela.

    Sem dobras, é a linha de centro a centro. Com dobras, é o que o `ChopRectangleConnector` do
    JHotDraw faz: a ponta inicial mira o 2º ponto, e a final, o penúltimo.
    """
    if not dobras:
        return connection_points(origem, destino)
    return (chop(origem, dobras[0]), chop(destino, dobras[-1]))


PARALLEL_OFFSET = 70.0  # o mesmo desvio que o TerraER usa (ConnectionTool.unaryRelationshipHandle)


def parallel_bends(origem: Rect, destino: Rect, ordem: int) -> list[Point]:
    """Dobras da `ordem`-ésima conexão extra entre o mesmo par (0 = a primeira, reta).

    A linha sai para o lado em forma de colchete, com dobras a 1/3 e 2/3 do caminho. As extras
    alternam de lado e se afastam (70, -70, 140, -140...), para nunca ficarem uma sobre a outra.
    """
    if ordem <= 0:
        return []
    (x1, y1), (x2, y2) = center(origem), center(destino)
    dx, dy = x2 - x1, y2 - y1
    comprimento = (dx * dx + dy * dy) ** 0.5
    if comprimento == 0:
        return []
    lado = 1 if ordem % 2 else -1
    desvio = PARALLEL_OFFSET * ((ordem + 1) // 2) * lado
    nx, ny = -dy / comprimento * desvio, dx / comprimento * desvio
    return [(x1 + dx / 3 + nx, y1 + dy / 3 + ny), (x1 + 2 * dx / 3 + nx, y1 + 2 * dy / 3 + ny)]


def nearest_segment(caminho: list[Point], ponto: Point) -> tuple[int, float]:
    """Trecho da linha mais perto do ponto: (índice do trecho, distância).

    O trecho `i` vai do ponto `i` ao `i + 1` do caminho.
    """
    melhor, menor = 0, float("inf")
    for i, ((x1, y1), (x2, y2)) in enumerate(zip(caminho, caminho[1:], strict=False)):
        dx, dy = x2 - x1, y2 - y1
        comprimento2 = dx * dx + dy * dy
        t = (
            0.0
            if comprimento2 == 0
            else ((ponto[0] - x1) * dx + (ponto[1] - y1) * dy) / comprimento2
        )
        t = min(max(t, 0.0), 1.0)
        px, py = x1 + t * dx, y1 + t * dy
        distancia = ((ponto[0] - px) ** 2 + (ponto[1] - py) ** 2) ** 0.5
        if distancia < menor:
            melhor, menor = i, distancia
    return melhor, menor
