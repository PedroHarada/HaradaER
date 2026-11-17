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
import re
from dataclasses import dataclass, replace

from haradaer.core.appearance.markdown import Run, parse
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
NUMBERED_LABELS = frozenset({"llabelMuitos", "llabelDoubleMuitos"})
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


# --- Texto (RF-26) com Markdown (RF-28) --------------------------------------------------------

HEADING_SCALE = {1: 2.0, 2: 1.5, 3: 1.17, 4: 1.0, 5: 0.83, 6: 0.67}  # como os títulos do HTML
CODE_FAMILY = "Monospaced"  # a fonte lógica monoespaçada do Java
CODE_FILL: RGBA = (235, 235, 235, 255)
LINK_COLOR: RGBA = (0, 0, 238, 255)  # o azul dos links do HTML
CHECKBOX_SCALE = 0.8  # lado da caixinha da tarefa, em múltiplos do tamanho da fonte
LIST_STEP = 1.5  # recuo de cada nível de lista, em múltiplos do tamanho da fonte


@dataclass(frozen=True)
class TextSegment:
    """Um pedaço de uma linha do Texto, a `x` do começo da área útil da caixa."""

    x: float
    text: str
    font: FontSpec
    code: bool = False
    link: str | None = None
    checkbox: bool | None = None  # caixinha de tarefa (marcada ou não), no lugar do texto
    task_line: int = 0  # linha do item da tarefa no texto


@dataclass(frozen=True)
class TextLine:
    segments: tuple[TextSegment, ...]
    height: float
    code_block: bool = False  # fundo de código na largura toda
    indent: float = 0.0


def _run_font(base: FontSpec, run: Run, titulo: int) -> FontSpec:
    sublinhado = base.underline or run.link is not None
    if run.code:
        return replace(base, family=CODE_FAMILY, bold=False, italic=False, underline=sublinhado)
    tamanho = base.size * HEADING_SCALE[titulo] if titulo else base.size
    return replace(
        base,
        size=tamanho,
        bold=base.bold or run.bold or bool(titulo),
        italic=base.italic or run.italic,
        underline=sublinhado,
    )


def _height(segmentos: list[TextSegment], vazio: FontSpec, medidor: TextMeasurer) -> float:
    if not segmentos:
        return medidor.size(" ", vazio)[1]
    return max(medidor.size(s.text or " ", s.font)[1] for s in segmentos)


def _wrap_runs(
    runs: list[Run],
    base: FontSpec,
    titulo: int,
    largura: float,
    recuo: float,
    marcador: str | None,
    medidor: TextMeasurer,
    tarefa: bool | None = None,
    linha_da_tarefa: int = 0,
) -> list[TextLine]:
    """Quebra os pedaços pela largura, entre palavras; uma palavra mais larga que a linha é
    cortada. A palavra pode misturar fontes (`in*crí*vel`) e não quebra no meio da troca."""
    linha_vazia = _run_font(base, Run(""), titulo)
    linhas: list[TextLine] = []
    atual: list[TextSegment] = []
    x = recuo
    if tarefa is not None:  # a caixinha fica no lugar do marcador
        atual.append(
            TextSegment(
                recuo - LIST_STEP * base.size,
                "",
                linha_vazia,
                checkbox=tarefa,
                task_line=linha_da_tarefa,
            )
        )
    elif marcador is not None:
        atual.append(TextSegment(recuo - LIST_STEP * base.size, marcador, linha_vazia))

    def fechar() -> None:
        nonlocal atual, x
        linhas.append(TextLine(tuple(atual), _height(atual, linha_vazia, medidor), indent=recuo))
        atual, x = [], recuo

    def largura_de(texto: str, fonte: FontSpec) -> float:
        return medidor.size(texto, fonte)[0]

    def por(texto: str, fonte: FontSpec, codigo: bool, link: str | None) -> None:
        """Põe o texto na linha, juntando ao pedaço anterior se o estilo for o mesmo."""
        nonlocal x
        ultimo = atual[-1] if atual else None
        if (
            ultimo
            and ultimo.x >= recuo
            and (ultimo.font, ultimo.code, ultimo.link) == (fonte, codigo, link)
        ):
            atual[-1] = TextSegment(ultimo.x, ultimo.text + texto, fonte, codigo, link)
            x = ultimo.x + largura_de(atual[-1].text, fonte)
            return
        atual.append(TextSegment(x, texto, fonte, codigo, link))
        x += largura_de(texto, fonte)

    # Palavras (pedaços sem espaço, talvez de fontes diferentes) separadas por espaços.
    palavras: list[tuple[str, list[tuple[str, FontSpec, bool, str | None]]]] = []
    for run in runs:
        if run.text == "\n":
            palavras.append(("quebra", []))
            continue
        fonte = _run_font(base, run, titulo)
        for pedaco in re.split(r"( +)", run.text):
            if not pedaco:
                continue
            parte = (pedaco, fonte, run.code, run.link)
            if pedaco.startswith(" ") and not run.code:
                palavras.append(("espaco", [parte]))
            elif palavras and palavras[-1][0] == "palavra":
                palavras[-1][1].append(parte)
            else:
                palavras.append(("palavra", [parte]))

    espaco: tuple[str, FontSpec, bool, str | None] | None = None
    for tipo, partes in palavras:
        if tipo == "quebra":
            fechar()
            espaco = None
            continue
        if tipo == "espaco":
            espaco = partes[0]
            continue
        conteudo = [s for s in atual if s.x >= recuo]  # o marcador não conta
        largura_palavra = sum(largura_de(t, f) for t, f, _c, _l in partes)
        largura_espaco = largura_de(espaco[0], espaco[1]) if espaco and conteudo else 0.0
        if conteudo and x + largura_espaco + largura_palavra > largura:
            fechar()
            largura_espaco = 0.0
        if largura_espaco and espaco is not None:
            por(*espaco)
        espaco = None
        if largura_palavra <= largura - x or not partes:
            for parte in partes:
                por(*parte)
            continue
        for texto, fonte, codigo, link in partes:  # mais larga que a linha: corta
            for letra in texto:
                if x + largura_de(letra, fonte) > largura and any(s.x >= recuo for s in atual):
                    fechar()
                por(letra, fonte, codigo, link)
    fechar()
    return linhas


def _wrap_code(
    codigo: str, base: FontSpec, largura: float, recuo: float, medidor: TextMeasurer
) -> list[TextLine]:
    """Bloco de código: quebra por caractere, para nada sumir da caixa."""
    fonte = _run_font(base, Run("", code=True), 0)
    altura = medidor.size(" ", fonte)[1]
    linhas = []
    for linha in codigo.split("\n"):
        atual = ""
        for letra in linha:
            if atual and recuo + medidor.size(atual + letra, fonte)[0] > largura:
                linhas.append(TextLine((TextSegment(recuo, atual, fonte),), altura, True, recuo))
                atual = ""
            atual += letra
        segmentos = (TextSegment(recuo, atual, fonte),) if atual else ()
        linhas.append(TextLine(segmentos, altura, True, recuo))
    return linhas


def text_area_layout(
    texto: str, fonte: FontSpec, largura: float, medidor: TextMeasurer
) -> tuple[list[TextLine], float]:
    """As linhas do Texto numa caixa dessa largura e a altura de que a caixa precisa."""
    util = largura - 2 * TEXT_AREA_INSET
    linhas: list[TextLine] = []
    for bloco in parse(texto):
        recuo = bloco.depth * LIST_STEP * fonte.size
        if bloco.kind == "blank":
            linhas.append(TextLine((), medidor.size(" ", fonte)[1]))
        elif bloco.kind == "code":
            linhas.extend(_wrap_code(bloco.runs[0].text, fonte, util, recuo, medidor))
        else:
            linhas.extend(
                _wrap_runs(
                    bloco.runs,
                    fonte,
                    bloco.level,
                    util,
                    recuo,
                    bloco.marker,
                    medidor,
                    bloco.task,
                    bloco.line,
                )
            )
    return linhas, sum(linha.height for linha in linhas) + 2 * TEXT_AREA_INSET


def _text_area(elemento: Element, medidor: TextMeasurer) -> list[DrawOp]:
    style = Style.of(elemento)
    fonte = _font(style, "ta")
    x, y = _num(elemento, "x"), _num(elemento, "y")
    w, h = _num(elemento, "w"), _num(elemento, "h")
    cor = style.color("textColor", BLACK) or BLACK
    ops: list[DrawOp] = [
        ShapeOp("rect", x, y, w, h, style.color("fillColor", WHITE), _stroke(style))
    ]
    esquerda, topo = x + TEXT_AREA_INSET, y + TEXT_AREA_INSET
    linhas, _altura = text_area_layout(style.string("text", "") or "", fonte, w, medidor)
    for linha in linhas:
        if linha.code_block:
            largura = w - 2 * TEXT_AREA_INSET - linha.indent
            ops.append(
                ShapeOp(
                    "rect", esquerda + linha.indent, topo, largura, linha.height, CODE_FILL, None
                )
            )
        for pedaco in linha.segments:
            if pedaco.checkbox is not None:
                ops.extend(_checkbox(esquerda + pedaco.x, topo, linha.height, pedaco, cor))
                continue
            if pedaco.code and not linha.code_block:
                largura = medidor.size(pedaco.text, pedaco.font)[0]
                ops.append(
                    ShapeOp(
                        "rect", esquerda + pedaco.x, topo, largura, linha.height, CODE_FILL, None
                    )
                )
            tinta = LINK_COLOR if pedaco.link is not None else cor
            ops.append(
                TextOp(esquerda + pedaco.x, topo, pedaco.text, pedaco.font, tinta, link=pedaco.link)
            )
        topo += linha.height
    return ops


def _checkbox(x: float, topo: float, altura: float, pedaco: TextSegment, cor: RGBA) -> list[DrawOp]:
    """A caixinha da tarefa, centrada na linha, com um tique se estiver marcada."""
    lado = pedaco.font.size * CHECKBOX_SCALE
    y = topo + (altura - lado) / 2
    caixa = ShapeOp("rect", x, y, lado, lado, WHITE, Stroke(color=cor), task=pedaco.task_line)
    ops: list[DrawOp] = [caixa]
    if pedaco.checkbox:
        tique = ((x + lado * 0.2, y + lado * 0.5), (x + lado * 0.42, y + lado * 0.75))
        tique += ((x + lado * 0.8, y + lado * 0.25),)
        ops.append(PolylineOp(tique, Stroke(color=cor, width=1.5)))
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
    if tag in NUMBERED_LABELS:  # N, M, P...: o TerraER grava a letra no estilo da conexão
        texto = style.string("text", texto) or texto
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
