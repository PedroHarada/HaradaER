"""Comandos de edição do diagrama.

Cada função `*_command` só **monta** o comando; quem o executa é o `History`. Os comandos
elementares (`SetAttr`, `SetChildren`, `InsertFigure`, `RemoveFigure`) avisam o `Document` do que
mudou, para a interface se atualizar.
"""

from __future__ import annotations

from haradaer.core.appearance.describe import font_of
from haradaer.core.appearance.metrics import TextMeasurer
from haradaer.core.commands.history import Command, Composite
from haradaer.core.figures.factory import (
    ATTRIBUTE_TYPES,
    TEXT_MARGIN,
    create_connection,
    create_node,
    text_position,
)
from haradaer.core.figures.tags import (
    CONNECTION_TAGS,
    NODE_TAGS,
    TEXT_PART_TAGS,
    TYPED_ATTRIBUTE_TAGS,
)
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import Rect, connection_points, node_rect, part_rect, shape_part
from haradaer.core.model.document import ADDED, CHANGED, REMOVED, Document
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import format_number, parse_number

ATTRIBUTE_TAGS = TYPED_ATTRIBUTE_TAGS | {"atrderivado"}


class SetAttr(Command):
    """Troca (ou cria, ou apaga, se `valor` for `None`) um atributo de um elemento."""

    def __init__(self, documento: Document, figura: Element, alvo: Element, nome: str, valor):
        self._doc, self._figura, self._alvo = documento, figura, alvo
        self._nome, self._novo = nome, valor
        self._antigo: str | None = alvo.attrs.get(nome)

    def _definir(self, valor: str | None) -> None:
        if valor is None:
            self._alvo.attrs.pop(self._nome, None)
        else:
            self._alvo.attrs[self._nome] = valor
        self._doc.emit(CHANGED, self._figura)

    def apply(self) -> None:
        self._antigo = self._alvo.attrs.get(self._nome)
        self._definir(self._novo)

    def revert(self) -> None:
        self._definir(self._antigo)


class SetChildren(Command):
    """Troca a lista de filhos de um elemento (pontos de uma linha, estilo de um texto...)."""

    def __init__(self, documento: Document, figura: Element, alvo: Element, filhos: list[Element]):
        self._doc, self._figura, self._alvo = documento, figura, alvo
        self._novos = filhos
        self._antigos = list(alvo.children)

    def _definir(self, filhos: list[Element]) -> None:
        self._alvo.children[:] = filhos
        self._doc.emit(CHANGED, self._figura)

    def apply(self) -> None:
        self._antigos = list(self._alvo.children)
        self._definir(self._novos)

    def revert(self) -> None:
        self._definir(self._antigos)


class SetText(Command):
    """Troca o conteúdo de um elemento folha (`<string>`)."""

    def __init__(self, documento: Document, figura: Element, alvo: Element, texto: str):
        self._doc, self._figura, self._alvo = documento, figura, alvo
        self._novo, self._antigo = texto, alvo.text

    def _definir(self, texto: str | None) -> None:
        self._alvo.text = texto
        self._doc.emit(CHANGED, self._figura)

    def apply(self) -> None:
        self._antigo = self._alvo.text
        self._definir(self._novo)

    def revert(self) -> None:
        self._definir(self._antigo)


class InsertFigure(Command):
    def __init__(self, documento: Document, figura: Element, indice: int | None = None):
        self._doc, self._figura, self._indice = documento, figura, indice

    def apply(self) -> None:
        figuras = self._doc.figures
        figuras.insert(len(figuras) if self._indice is None else self._indice, self._figura)
        self._doc.emit(ADDED, self._figura)

    def revert(self) -> None:
        self._doc.figures.remove(self._figura)
        self._doc.emit(REMOVED, self._figura)


class RemoveFigure(Command):
    def __init__(self, documento: Document, figura: Element):
        self._doc, self._figura = documento, figura
        self._indice = 0

    def apply(self) -> None:
        figuras = self._doc.figures
        self._indice = next(i for i, f in enumerate(figuras) if f is self._figura)
        del figuras[self._indice]
        self._doc.emit(REMOVED, self._figura)

    def revert(self) -> None:
        self._doc.figures.insert(self._indice, self._figura)
        self._doc.emit(ADDED, self._figura)


# ---------------------------------------------------------------- consultas


def connections_of(documento: Document, nos: set[int]) -> list[ConnectionFigure]:
    """Conexões do desenho que têm alguma ponta em um dos elementos (identificados por `id()`)."""
    achadas = []
    for figura in documento.figures:
        if isinstance(figura, ConnectionFigure):
            inicio, fim = figura.start, figura.end
            if (inicio is not None and id(inicio) in nos) or (fim is not None and id(fim) in nos):
                achadas.append(figura)
    return achadas


def _rect_of(no: Element | None, previstos: dict[int, Rect]) -> Rect | None:
    if no is None:
        return None
    return previstos.get(id(no)) or node_rect(no)


def _reroute(documento: Document, nos: set[int], previstos: dict[int, Rect]) -> list[Command]:
    """Comandos que religam às bordas as conexões ligadas a elementos que mudaram de lugar."""
    comandos: list[Command] = []
    for conexao in connections_of(documento, nos):
        origem = _rect_of(conexao.start, previstos)
        destino = _rect_of(conexao.end, previstos)
        if origem is None or destino is None:
            continue
        (x1, y1), (x2, y2) = connection_points(origem, destino)
        pontos = conexao.child("points")
        if pontos is None or len(pontos.children) != 2:
            continue
        novos = []
        for modelo, (x, y) in zip(pontos.children, ((x1, y1), (x2, y2)), strict=True):
            ponto = Element("p", attrs=dict(modelo.attrs))
            ponto.attrs["x"], ponto.attrs["y"] = format_number(x), format_number(y)
            novos.append(ponto)
        comandos.append(SetChildren(documento, conexao, pontos, novos))
    return comandos


# ---------------------------------------------------------------- comandos de edição


def add_node_command(documento: Document, no: NodeFigure) -> Command:
    comando = InsertFigure(documento, no)
    comando.label = "Adicionar elemento"
    return comando


def new_node(tag: str, x: float, y: float, medidor: TextMeasurer) -> NodeFigure:
    if tag not in NODE_TAGS:
        raise ValueError(f"tipo de elemento desconhecido: {tag}")
    return create_node(tag, x, y, medidor)


def connect_command(documento: Document, tag: str, origem: Element, destino: Element) -> Command:
    """Liga dois elementos. Qualquer par é aceito: a validade é só avisada (RF-09)."""
    if tag not in CONNECTION_TAGS:
        raise ValueError(f"tipo de conexão desconhecido: {tag}")
    if origem is destino:
        raise ValueError("uma conexão precisa de dois elementos diferentes")
    if tag == "lcaf" and origem.tag not in ATTRIBUTE_TAGS and destino.tag in ATTRIBUTE_TAGS:
        origem, destino = destino, origem  # o HaradaER grava atributo -> dono (QA-03)
    rect_origem, rect_destino = node_rect(origem), node_rect(destino)
    if rect_origem is None or rect_destino is None:
        raise ValueError("elemento sem forma")
    conexao = create_connection(tag, origem, destino, rect_origem, rect_destino)
    comando = InsertFigure(documento, conexao)
    comando.label = "Conectar"
    return comando


def remove_command(documento: Document, figuras: list[Element]) -> Command:
    """Exclui figuras e, junto, as conexões ligadas a elas (como o TerraER)."""
    escolhidas = {id(f) for f in figuras}
    todas = list(figuras)
    todas += [c for c in connections_of(documento, escolhidas) if id(c) not in escolhidas]
    ordem = {id(f): i for i, f in enumerate(documento.figures)}
    todas = [f for f in todas if id(f) in ordem]
    todas.sort(key=lambda f: ordem[id(f)], reverse=True)
    return Composite([RemoveFigure(documento, f) for f in todas], "Excluir")


def _shift(
    documento: Document, figura: Element, parte: Element, dx: float, dy: float
) -> list[Command]:
    """Desloca uma parte e, se for um grupo, as partes de dentro."""
    comandos: list[Command] = []
    for nome, delta in (("x", dx), ("y", dy)):
        if nome in parte.attrs:
            valor = format_number(parse_number(parte.attrs[nome]) + delta)
            comandos.append(SetAttr(documento, figura, parte, nome, valor))
    grupo = parte.child("children")
    for filha in grupo.children if grupo else []:
        comandos.extend(_shift(documento, figura, filha, dx, dy))
    return comandos


def can_move(figura: Element) -> bool:
    """Elementos ER e figuras de apoio com posição. Linhas livres (`l`, `b`, `bezier`) não."""
    return not isinstance(figura, ConnectionFigure) and figura.child("points") is None


def move_command(documento: Document, figuras: list[Element], dx: float, dy: float) -> Command:
    """Move elementos (e figuras de apoio) e religa as conexões que chegam neles."""
    comandos: list[Command] = []
    movidos: set[int] = set()
    previstos: dict[int, Rect] = {}
    for figura in figuras:
        if not can_move(figura):
            continue
        movidos.add(id(figura))
        comandos.extend(_shift(documento, figura, figura, dx, dy))
        if isinstance(figura, NodeFigure):
            rect = node_rect(figura)
            if rect is not None:
                previstos[id(figura)] = (rect[0] + dx, rect[1] + dy, rect[2], rect[3])
    comandos.extend(_reroute(documento, movidos, previstos))
    return Composite(comandos, "Mover")


def name_string(no: NodeFigure) -> Element | None:
    """O elemento `<string>` com o nome do elemento, se existir."""
    for parte in no.parts:
        if parte.tag in TEXT_PART_TAGS:
            for estilo in parte.children_named("a"):
                entrada = estilo.child("text")
                if entrada is not None and entrada.child("string") is not None:
                    return entrada.child("string")
    return None


def _name_part(no: NodeFigure) -> Element | None:
    return next((p for p in no.parts if p.tag in TEXT_PART_TAGS), None)


def rename_command(
    documento: Document, no: NodeFigure, nome: str, medidor: TextMeasurer
) -> Command:
    """Muda o nome e reajusta a forma ao texto: ela cresce, nunca encolhe, e o texto centraliza."""
    texto = _name_part(no)
    forma = shape_part(no)
    string = name_string(no)
    if texto is None or forma is None or string is None:
        raise ValueError("elemento sem texto para renomear")
    comandos: list[Command] = [SetText(documento, no, string, nome)]

    x, y, w, h = part_rect(forma)
    largura_texto, altura_texto = medidor.size(nome, font_of(texto))
    nova_largura = max(w, largura_texto + TEXT_MARGIN)
    if nova_largura != w:
        comandos.append(SetAttr(documento, no, forma, "w", format_number(nova_largura)))
        outras = [p for p in no.parts if p is not forma and p.tag in ("r", "diamond", "e", "circ")]
        for outra in outras:  # losango interno da entidade associativa
            comandos.append(SetAttr(documento, no, outra, "w", format_number(nova_largura - 4)))
    px, py = text_position((x, y, nova_largura, h), (largura_texto, altura_texto))
    comandos.append(SetAttr(documento, no, texto, "x", format_number(px)))
    comandos.append(SetAttr(documento, no, texto, "y", format_number(py)))
    comandos.extend(_reroute(documento, {id(no)}, {id(no): (x, y, nova_largura, h)}))
    return Composite(comandos, "Renomear")


def set_attribute_type_command(documento: Document, no: NodeFigure, tipo: str) -> Command:
    """Tipo SQL de um atributo. Só aceita os cinco valores que o TerraER sabe reler."""
    if tipo not in ATTRIBUTE_TYPES:
        raise ValueError(f"tipo de atributo inválido: {tipo}")
    if no.attribute_type is None:
        raise ValueError("este elemento não tem tipo")
    comando = SetAttr(documento, no, no, "attributeType", tipo)
    comando.label = "Mudar tipo"
    return comando


def set_nullable_command(documento: Document, no: NodeFigure, anulavel: bool) -> Command:
    if no.nullable is None:
        raise ValueError("este elemento não tem anulabilidade")
    comando = SetAttr(documento, no, no, "nullable", "true" if anulavel else "false")
    comando.label = "Mudar anulabilidade"
    return comando


def set_generalization_label_command(
    documento: Document, conexao: ConnectionFigure, texto: str
) -> Command:
    if conexao.generalization_label is None:
        raise ValueError("esta conexão não tem rótulo")
    comando = SetAttr(documento, conexao, conexao, "labelGeneralizacaoText", texto)
    comando.label = "Mudar rótulo"
    return comando
