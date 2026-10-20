"""Transforma as figuras do arquivo em operações de desenho, como o TerraER as desenharia.

Regras levantadas no TerraER 3.14 (`docs/INVESTIGACOES.md`, seção 13):
- o preenchimento das formas é **fixo por tipo de forma** e ignora o estilo do arquivo
  (retângulo, losango e elipse); só o círculo usa `fillColor`;
- entidade/relacionamento/atributo fracos usam traço duplo;
- os rótulos `1`/`N` e o texto das generalizações ficam a 8 de distância, a -45° do início
  da linha (`BezierLabelLocator`);
- a conexão de generalização simples ganha um arco de 210° no centro da linha.
"""

from __future__ import annotations

import base64
import math

from haradaer.core.appearance.metrics import TextMeasurer
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
from haradaer.core.appearance.style import BLACK, RGBA, WHITE, Style
from haradaer.core.figures.tags import CONNECTION_TAGS, NODE_TAGS
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import parse_number

SHAPE_KINDS = {"r": "rect", "diamond": "diamond", "e": "ellipse", "circ": "ellipse"}

# Preenchimento fixo no código de desenho do TerraER (ignora o atributo do arquivo).
FIXED_FILL: dict[str, RGBA] = {
    "r": (175, 255, 175, 255),
    "diamond": (255, 255, 100, 255),
    "e": (175, 175, 255, 255),
}

DOUBLE_CONNECTIONS = frozenset(
    {"llabelDoubleUm", "llabelDoubleMuitos", "llabelDoubleGeneralizacao"}
)
CARDINALITY_LABELS = {
    "llabelUm": "1",
    "llabelDoubleUm": "1",
    "llabelMuitos": "N",
    "llabelDoubleMuitos": "N",
}
GENERALIZATION_LABELS = frozenset({"llabelGeneralizacao", "llabelDoubleGeneralizacao"})

LABEL_ANGLE = -math.pi / 4
LABEL_DISTANCE = 8.0
CARDINALITY_FONT = FontSpec(size=16.0, bold=True)
GENERALIZATION_FONT = FontSpec(size=12.0, italic=True)
TEXT_AREA_INSET = 5.0
ARC_RADIUS = 10.0

Point = tuple[float, float]


def _num(elemento: Element, nome: str, padrao: float = 0.0) -> float:
    valor = elemento.attrs.get(nome)
    return parse_number(valor) if valor is not None else padrao


def _stroke(style: Style, *, double: bool = False) -> Stroke:
    tipo = style.enum("strokeType", "DOUBLE" if double else "BASIC")
    fator_padrao = 3.0 if double else 2.0
    return Stroke(
        color=style.color("strokeColor", BLACK) or BLACK,
        width=style.double("strokeWidth", 1.0) or 1.0,
        double=tipo == "DOUBLE",
        factor=style.double("innerStrokeWidthFactor", fator_padrao) or fator_padrao,
        dashes=style.doubles("strokeDashes") or (),
    )


def _font(style: Style, tag: str) -> FontSpec:
    face = style.font_face()
    familia, estilo_java, tamanho_face = face if face else ("Dialog", 0, 12.0)
    negrito_padrao = tag == "tn" or bool(face and estilo_java & 1)
    italico_padrao = tag == "ti" or bool(face and estilo_java & 2)
    return FontSpec(
        family=familia,
        size=style.double("fontSize", tamanho_face) or tamanho_face,
        bold=bool(style.boolean("fontBold", negrito_padrao)),
        italic=bool(style.boolean("fontItalic", italico_padrao)),
        underline=bool(style.boolean("fontUnderlined", False)),
    )


def _shape(elemento: Element) -> list[DrawOp]:
    style = Style.of(elemento)
    tag = elemento.tag
    if tag in FIXED_FILL:
        fundo: RGBA | None = FIXED_FILL[tag]
    else:
        fundo = style.color("fillColor", WHITE)
    return [
        ShapeOp(
            SHAPE_KINDS[tag],
            _num(elemento, "x"),
            _num(elemento, "y"),
            _num(elemento, "w"),
            _num(elemento, "h"),
            fundo,
            _stroke(style),
        )
    ]


def _text(elemento: Element, medidor: TextMeasurer) -> list[DrawOp]:
    style = Style.of(elemento)
    fonte = _font(style, elemento.tag)
    texto = style.string("text", "") or ""
    x, y = _num(elemento, "x"), _num(elemento, "y")
    cor = style.color("textColor", BLACK) or BLACK
    ops: list[DrawOp] = [TextOp(x, y, texto, fonte, cor)]
    tracejado = style.doubles("strokeDashes")
    if tracejado:  # chave parcial: sublinhado tracejado
        largura, altura = medidor.size(texto, fonte)
        ops.append(
            PolylineOp(((x, y + altura), (x + largura, y + altura)), Stroke(dashes=tracejado))
        )
    return ops


def _text_area(elemento: Element, medidor: TextMeasurer) -> list[DrawOp]:
    style = Style.of(elemento)
    fonte = _font(style, "ta")
    x, y = _num(elemento, "x"), _num(elemento, "y")
    w, h = _num(elemento, "w"), _num(elemento, "h")
    cor = style.color("textColor", BLACK) or BLACK
    ops: list[DrawOp] = [
        ShapeOp("rect", x, y, w, h, style.color("fillColor", WHITE), _stroke(style))
    ]
    topo = y + TEXT_AREA_INSET
    for linha in (style.string("text", "") or "").split("\n"):
        ops.append(TextOp(x + TEXT_AREA_INSET, topo, linha, fonte, cor))
        topo += medidor.size(linha or " ", fonte)[1]
    return ops


def _points(elemento: Element) -> list[Point]:
    pontos = elemento.child("points")
    if pontos is None:
        return []
    return [(_num(p, "x"), _num(p, "y")) for p in pontos.children_named("p")]


def point_on_path(pontos: list[Point], relativo: float) -> Point:
    """Ponto a `relativo` (0 a 1) do comprimento de uma linha poligonal."""
    if len(pontos) == 1:
        return pontos[0]
    trechos = [math.dist(a, b) for a, b in zip(pontos, pontos[1:], strict=False)]
    total = sum(trechos)
    if total == 0:
        return pontos[0]
    alvo = min(max(relativo, 0.0), 1.0) * total
    for (a, b), comprimento in zip(zip(pontos, pontos[1:], strict=False), trechos, strict=True):
        if alvo <= comprimento or comprimento == 0:
            f = 0.0 if comprimento == 0 else alvo / comprimento
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        alvo -= comprimento
    return pontos[-1]


def label_position(pontos: list[Point], relativo: float, largura: float, altura: float) -> Point:
    """Canto superior esquerdo do rótulo, como o `BezierLabelLocator` do TerraER.

    O ponto de ancoragem fica a 8 unidades da linha, a -45° da direção dela; o rótulo ocupa o
    quadrante oposto à direção para onde a âncora aponta.
    """
    ponto = point_on_path(pontos, relativo)
    seguinte = point_on_path(pontos, relativo + 0.1 if relativo <= 0.5 else relativo - 0.1)
    angulo_linha = math.atan2(seguinte[1] - ponto[1], seguinte[0] - ponto[0])
    angulo = angulo_linha + LABEL_ANGLE
    ancora_x = ponto[0] + LABEL_DISTANCE * math.cos(angulo)
    ancora_y = ponto[1] + LABEL_DISTANCE * math.sin(angulo)
    x = ancora_x if math.cos(angulo) >= 0 else ancora_x - largura
    y = ancora_y if math.sin(angulo) >= 0 else ancora_y - altura
    return (x, y)


def _connection(elemento: Element, medidor: TextMeasurer) -> list[DrawOp]:
    pontos = _points(elemento)
    if len(pontos) < 2:
        return []
    style = Style.of(elemento)
    tag = elemento.tag
    traco = _stroke(style, double=tag in DOUBLE_CONNECTIONS)
    ops: list[DrawOp] = [PolylineOp(tuple(pontos), traco)]

    texto = CARDINALITY_LABELS.get(tag)
    fonte = CARDINALITY_FONT
    relativo = 0.0
    if tag in GENERALIZATION_LABELS:
        texto = elemento.attrs.get("labelGeneralizacaoText", "")
        fonte, relativo = GENERALIZATION_FONT, 0.25
    if texto:
        largura, altura = medidor.size(texto, fonte)
        x, y = label_position(pontos, relativo, largura, altura)
        ops.append(TextOp(x, y, texto, fonte))

    if tag == "generalizacaoLine":
        ops.append(_subset_arc(pontos))
    return ops


def _subset_arc(pontos: list[Point]) -> ArcOp:
    """Arco "subconjunto" da generalização simples (`GeneralizacaoLineConnectionFigure.draw`)."""
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    centro = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    dx, dy = pontos[0][0] - centro[0], pontos[0][1] - centro[1]
    teta = math.degrees(math.atan(abs(dy) / abs(dx))) if dx != 0 else 90.0
    if dx > 0 and dy < 0:
        angulo = (teta + 90) % 360
    elif dx > 0 and dy > 0:
        angulo = (90 - teta) % 360
    elif dx < 0 and dy > 0:
        angulo = (teta + 270) % 360
    else:
        angulo = (270 - teta) % 360
    return ArcOp(centro[0], centro[1], ARC_RADIUS, int(angulo) - 15, 210, Stroke())


def _line(elemento: Element) -> list[DrawOp]:
    pontos = _points(elemento)
    if len(pontos) < 2:
        return []
    return [PolylineOp(tuple(pontos), _stroke(Style.of(elemento)))]


def _image(elemento: Element) -> list[DrawOp]:
    dados = elemento.child("imageData")
    if dados is None or not dados.text:
        return []
    try:
        imagem = base64.b64decode("".join(dados.text.split()))
    except ValueError:
        return []
    return [
        ImageOp(
            _num(elemento, "x"),
            _num(elemento, "y"),
            _num(elemento, "w"),
            _num(elemento, "h"),
            imagem,
        )
    ]


def describe_figure(figura: Element, medidor: TextMeasurer) -> list[DrawOp]:
    """Operações de desenho de uma figura, na ordem em que devem ser pintadas."""
    tag = figura.tag
    if tag in NODE_TAGS or tag == "g":
        filhos = figura.child("children")
        ops: list[DrawOp] = []
        for parte in filhos.children if filhos else []:
            ops.extend(describe_figure(parte, medidor))
        return ops
    if tag in SHAPE_KINDS:
        return _shape(figura)
    if tag in ("t", "tn", "ti"):
        return _text(figura, medidor)
    if tag == "ta":
        return _text_area(figura, medidor)
    if tag in ("l", "b", "bezier"):
        return _line(figura)
    if tag == "image":
        return _image(figura)
    if tag in CONNECTION_TAGS:
        return _connection(figura, medidor)
    return []


def describe_document(
    documento: Document, medidor: TextMeasurer
) -> list[tuple[Element, list[DrawOp]]]:
    """Cada figura do desenho com as suas operações, em ordem de empilhamento."""
    return [(figura, describe_figure(figura, medidor)) for figura in documento.figures]


def font_of(parte: Element) -> FontSpec:
    """Fonte com que uma parte de texto é desenhada."""
    return _font(Style.of(parte), parte.tag)
