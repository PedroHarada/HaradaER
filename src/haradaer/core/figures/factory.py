"""Criação de elementos novos, com a estrutura e o estilo padrão do TerraER.

Estilos e tamanhos vêm de `docs/INVESTIGACOES.md`, seção 5. Os elementos criados aqui têm a mesma
forma dos que o TerraER grava, para que ele os abra sem diferença.
"""

from __future__ import annotations

from dataclasses import dataclass

from haradaer.core.appearance.metrics import TextMeasurer
from haradaer.core.appearance.ops import FontSpec
from haradaer.core.figures.tags import CONNECTION_TAGS, NODE_TAGS
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import Rect, connection_points
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import format_number

# Margem em volta do texto ao ajustar a forma (10 de cada lado), como no TerraER.
TEXT_MARGIN = 20.0
DEFAULT_FONT = FontSpec()
GENERALIZATION_FONT = FontSpec(size=16.0, bold=True)
DEFAULT_GENERALIZATION_LABEL = "característica"

ATTRIBUTE_TYPES = ("CHAR(128)", "VARCHAR2(128)", "NUMBER", "NUMBER(9,2)", "DATE")

GENERALIZATION_TAGS = ("uniao", "disjuncao", "sobreposicao")

DOUBLE_STYLE_BLOCKS = {
    "llabelDoubleUm": 1,
    "llabelDoubleMuitos": 1,
    "llabelDoubleGeneralizacao": 2,
}

_PINK = "#ffffebeb"
_CIRCLE_FILL = "#fff5f2e0"


@dataclass(frozen=True)
class ElementKind:
    """O que um tipo de elemento tem ao ser criado."""

    tag: str
    name: str  # nome padrão mostrado ao criar
    shape: str  # tag da forma principal
    size: tuple[float, float]
    label: str  # nome na interface
    associative: bool = False  # losango interno dentro do retângulo (entidade associativa)
    typed: tuple[bool, str] | None = None  # (anulável, tipo SQL) dos atributos com tipo


KINDS: dict[str, ElementKind] = {
    kind.tag: kind
    for kind in (
        ElementKind("ent", "Entidade", "r", (80, 40), "Entidade"),
        ElementKind("entfraca", "Entidade fraca", "r", (80, 40), "Entidade fraca"),
        ElementKind("rel", "Relacionamento", "diamond", (97, 50), "Relacionamento"),
        ElementKind(
            "relfraco", "Relacionamento fraco", "diamond", (97, 50), "Relacionamento fraco"
        ),
        ElementKind(
            "entrel",
            "Entidade associativa",
            "r",
            (80, 40),
            "Entidade associativa",
            associative=True,
        ),
        ElementKind("atr", "Atributo", "e", (125, 27), "Atributo", typed=(False, "VARCHAR2(128)")),
        ElementKind(
            "atrchave", "Atributo chave", "e", (125, 27), "Atributo chave", typed=(False, "NUMBER")
        ),
        ElementKind(
            "atrchaveparcial",
            "Chave parcial",
            "e",
            (125, 27),
            "Atributo chave parcial",
            typed=(False, "NUMBER"),
        ),
        ElementKind("atrderivado", "Atributo derivado", "e", (125, 27), "Atributo derivado"),
        ElementKind(
            "atrmulti",
            "Atributo multivalorado",
            "e",
            (125, 27),
            "Atributo multivalorado",
            typed=(False, "VARCHAR2(128)"),
        ),
        ElementKind("uniao", "u", "circ", (20, 20), "União"),
        ElementKind("disjuncao", "d", "circ", (20, 20), "Disjunção"),
        ElementKind("sobreposicao", "o", "circ", (20, 20), "Sobreposição"),
    )
}
assert set(KINDS) == NODE_TAGS


def _value(tag: str, texto: str | None = None, attrs: dict[str, str] | None = None) -> Element:
    return Element(tag, attrs=attrs, text=texto)


def _entry(nome: str, valor: Element) -> Element:
    return Element(nome, children=[valor])


def _style(*entradas: Element) -> Element:
    return Element("a", children=list(entradas))


def _double_stroke() -> list[Element]:
    return [
        _entry("strokeType", _value("enum", "DOUBLE", {"type": "strokeType"})),
        _entry("innerStrokeWidthFactor", _value("double", "3")),
    ]


def _fill(cor: str) -> Element:
    return _entry("fillColor", _value("color", None, {"rgba": cor}))


def _bool(nome: str) -> Element:
    return _entry(nome, _value("boolean", "true"))


def _text_entry(texto: str) -> Element:
    return _entry("text", _value("string", texto))


def _shape_style(tag: str) -> list[Element]:
    """Entradas de estilo da forma, além das padrão."""
    if tag in ("entfraca", "relfraco"):
        return _double_stroke()
    if tag == "atrderivado":
        return [_fill(_PINK), _entry("strokeDashes", _doubles(5))]
    if tag == "atrmulti":
        return [_fill(_PINK), *_double_stroke()]
    if tag in GENERALIZATION_TAGS:
        return [_fill(_CIRCLE_FILL)]
    return []


def _doubles(*valores: float) -> Element:
    return Element("doubleArray", children=[_value("double", format_number(v)) for v in valores])


def _text_style(tag: str) -> list[Element]:
    if tag == "atrchave":
        return [_bool("fontUnderlined"), _bool("fontBold")]
    if tag == "atrchaveparcial":
        return [_entry("strokeDashes", _doubles(3)), _bool("fontBold")]
    if tag in GENERALIZATION_TAGS:
        return [_bool("fontBold"), _entry("fontSize", _value("double", "16"))]
    return []


def text_font(tag: str) -> FontSpec:
    """Fonte do nome de um elemento recém-criado, para medir o texto."""
    if tag in GENERALIZATION_TAGS:
        return GENERALIZATION_FONT
    if tag in ("atrchave", "atrchaveparcial"):
        return FontSpec(bold=True, underline=tag == "atrchave")
    return DEFAULT_FONT


def _part(
    tag: str, x: float, y: float, tamanho: tuple[float, float] | None, entradas: list[Element]
) -> Element:
    """Parte de um elemento: forma (com tamanho) ou texto (sem tamanho)."""
    attrs = {"x": format_number(x), "y": format_number(y)}
    if tamanho is not None:
        attrs |= {"w": format_number(tamanho[0]), "h": format_number(tamanho[1])}
    parte = Element(tag, attrs=attrs, has_id=True)
    if entradas:
        parte.children.append(_style(*entradas))
    return parte


def text_position(forma: Rect, texto: tuple[float, float]) -> tuple[float, float]:
    """Canto do texto para ele ficar centralizado na forma."""
    return (forma[0] + (forma[2] - texto[0]) / 2, forma[1] + (forma[3] - texto[1]) / 2)


def create_node(
    tag: str, x: float, y: float, medidor: TextMeasurer, nome: str | None = None
) -> NodeFigure:
    """Elemento novo com o canto superior esquerdo em (x, y)."""
    tipo = KINDS[tag]
    nome = tipo.name if nome is None else nome
    largura_texto, altura_texto = medidor.size(nome, text_font(tag))
    largura = max(tipo.size[0], largura_texto + TEXT_MARGIN)
    altura = tipo.size[1]
    forma = (x, y, largura, altura)

    partes = [_part(tipo.shape, x, y, (largura, altura), _shape_style(tag))]
    if tipo.associative:
        partes.append(_part("diamond", x + 2, y + 2, (largura - 4, altura - 4), []))
    px, py = text_position(forma, (largura_texto, altura_texto))
    tag_texto = "tn" if tag in GENERALIZATION_TAGS else "t"
    partes.append(_part(tag_texto, px, py, None, [*_text_style(tag), _text_entry(nome)]))

    atributos: dict[str, str] = {}
    if tipo.typed is not None:
        atributos = {
            "nullable": "true" if tipo.typed[0] else "false",
            "attributeType": tipo.typed[1],
        }
    return NodeFigure(
        tag, attrs=atributos, children=[Element("children", children=partes)], has_id=True
    )


def _connector(no: Element) -> Element:
    return Element("rConnector", children=[Element("Owner", children=[no])], has_id=True)


def _point(x: float, y: float) -> Element:
    attrs = {"colinear": "true", "x": format_number(x), "y": format_number(y)}
    attrs |= {"c1x": "0", "c1y": "0", "c2x": "0", "c2y": "0"}
    return Element("p", attrs=attrs)


def create_connection(
    tag: str, origem: Element, destino: Element, rect_origem: Rect, rect_destino: Rect
) -> ConnectionFigure:
    """Conexão entre dois elementos, com a linha já ligada às bordas."""
    if tag not in CONNECTION_TAGS:
        raise ValueError(f"tipo de conexão desconhecido: {tag}")
    (x1, y1), (x2, y2) = connection_points(rect_origem, rect_destino)
    atributos: dict[str, str] = {}
    if tag in ("llabelGeneralizacao", "llabelDoubleGeneralizacao"):
        atributos["labelGeneralizacaoText"] = DEFAULT_GENERALIZATION_LABEL
    filhos = [
        Element("points", children=[_point(x1, y1), _point(x2, y2)]),
        Element("startConnector", children=[_connector(origem)]),
        Element("endConnector", children=[_connector(destino)]),
    ]
    # O TerraER grava esse bloco nas conexões duplas (dois, na generalização dupla).
    for _ in range(DOUBLE_STYLE_BLOCKS.get(tag, 0)):
        filhos.append(_style(_entry("innerStrokeWidthFactor", _value("double", "3"))))
    return ConnectionFigure(tag, attrs=atributos, children=filhos, has_id=True)
