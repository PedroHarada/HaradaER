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
    DEFAULT_GENERALIZATION_LABEL,
    KINDS,
    LABELED_GENERALIZATIONS,
    MANY_TAGS,
    TEXT_MARGIN,
    bend_point,
    create_connection,
    create_node,
    many_letter,
    restyle_connection,
    text_position,
)
from haradaer.core.figures.tags import (
    CONNECTION_TAGS,
    NODE_TAGS,
    TEXT_PART_TAGS,
    TYPED_ATTRIBUTE_TAGS,
)
from haradaer.core.figures.types import ConnectionFigure, NodeFigure, SupportFigure
from haradaer.core.geometry import (
    SHAPE_PART_TAGS,
    Rect,
    node_rect,
    parallel_bends,
    part_rect,
    route_ends,
    shape_part,
)
from haradaer.core.model.document import ADDED, CHANGED, REMOVED, REORDERED, Document
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import format_number, parse_number
from haradaer.i18n import N_, _

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


def _xy(ponto: Element) -> tuple[float, float]:
    return (parse_number(ponto.attrs.get("x", "0")), parse_number(ponto.attrs.get("y", "0")))


def _moved_point(modelo: Element, x: float, y: float) -> Element:
    ponto = Element("p", attrs=dict(modelo.attrs))
    ponto.attrs["x"], ponto.attrs["y"] = format_number(x), format_number(y)
    return ponto


def _reroute(
    documento: Document,
    nos: set[int],
    previstos: dict[int, Rect],
    deslocamentos: dict[int, tuple[float, float]] | None = None,
) -> list[Command]:
    """Comandos que religam às bordas as conexões ligadas a elementos que mudaram de lugar.

    As dobras ficam onde estão, como no TerraER; só se as duas pontas andarem juntas (mesmo
    deslocamento) a linha inteira acompanha.
    """
    deslocamentos = deslocamentos or {}
    comandos: list[Command] = []
    for conexao in connections_of(documento, nos):
        origem = _rect_of(conexao.start, previstos)
        destino = _rect_of(conexao.end, previstos)
        pontos = conexao.child("points")
        if origem is None or destino is None or pontos is None or len(pontos.children) < 2:
            continue
        internos = pontos.children[1:-1]
        dx = dy = 0.0
        de_inicio = deslocamentos.get(id(conexao.start))
        if de_inicio is not None and de_inicio == deslocamentos.get(id(conexao.end)):
            dx, dy = de_inicio
        dobras = [(x + dx, y + dy) for x, y in map(_xy, internos)]
        (x1, y1), (x2, y2) = route_ends(origem, destino, dobras)
        meio = (
            [_moved_point(p, x, y) for p, (x, y) in zip(internos, dobras, strict=True)]
            if dx or dy
            else list(internos)
        )
        novos = [
            _moved_point(pontos.children[0], x1, y1),
            *meio,
            _moved_point(pontos.children[-1], x2, y2),
        ]
        comandos.append(SetChildren(documento, conexao, pontos, novos))
    return comandos


# ---------------------------------------------------------------- comandos de edição


def add_node_command(documento: Document, no: NodeFigure) -> Command:
    comando = InsertFigure(documento, no)
    comando.label = N_("Adicionar elemento")
    return comando


def new_node(tag: str, x: float, y: float, medidor: TextMeasurer) -> NodeFigure:
    if tag not in NODE_TAGS:
        raise ValueError(f"tipo de elemento desconhecido: {tag}")
    return create_node(tag, x, y, medidor)


# O TerraER grava a participação do relacionamento para a entidade (ConnectionTool.
# numberInCorrectSideHandle): por isso o rótulo 1/N fica do lado do relacionamento.
ENTITY_SIDE = ("ent", "entfraca", "entrel")
RELATIONSHIP_SIDE = ("rel", "relfraco", "entrel")


def _between(documento: Document, a: Element, b: Element) -> list[ConnectionFigure]:
    """Conexões que já ligam esses dois elementos, em qualquer sentido."""
    par = {id(a), id(b)}
    return [
        f
        for f in documento.figures
        if isinstance(f, ConnectionFigure)
        and f.start is not None
        and f.end is not None
        and {id(f.start), id(f.end)} == par
    ]


def _many_of(documento: Document, centro: Element) -> list[ConnectionFigure]:
    """Conexões "N" ligadas ao elemento, na ordem do desenho."""
    return [c for c in connections_of(documento, {id(centro)}) if c.tag in MANY_TAGS]


def _letter_of(conexao: ConnectionFigure) -> str | None:
    for bloco in conexao.children_named("a"):
        entrada = bloco.child("text")
        valor = entrada.child("string") if entrada is not None else None
        if valor is not None:
            return valor.text or ""
    return None


def _renumber(
    documento: Document, grupo: list[ConnectionFigure], pular: ConnectionFigure | None = None
) -> list[Command]:
    """Dá a cada conexão do grupo a letra da sua posição (N, M, P...), menos a `pular`."""
    comandos: list[Command] = []
    for posicao, conexao in enumerate(grupo):
        letra = many_letter(posicao)
        if conexao is not pular and _letter_of(conexao) != letra:
            filhos = restyle_connection(conexao, conexao.tag, letra)
            comandos.append(SetChildren(documento, conexao, conexao, filhos))
    return comandos


def connect_command(documento: Document, tag: str, origem: Element, destino: Element) -> Command:
    """Liga dois elementos. Qualquer par é aceito: a validade é só avisada (RF-09).

    Como o TerraER: entidade -> relacionamento é gravado ao contrário; uma conexão "N" ganha a
    próxima letra do relacionamento (N, M, P...); e, se o par já tem conexão, a nova sai para o
    lado com duas dobras, para não ficar por cima (o desvio é do HaradaER, sem cruzar).
    """
    if tag not in CONNECTION_TAGS:
        raise ValueError(f"tipo de conexão desconhecido: {tag}")
    if origem is destino:
        raise ValueError("uma conexão precisa de dois elementos diferentes")
    if tag == "lcaf" and origem.tag not in ATTRIBUTE_TAGS and destino.tag in ATTRIBUTE_TAGS:
        origem, destino = destino, origem  # o HaradaER grava atributo -> dono (QA-03)
    elif origem.tag in ENTITY_SIDE and destino.tag in RELATIONSHIP_SIDE:
        origem, destino = destino, origem
    rect_origem, rect_destino = node_rect(origem), node_rect(destino)
    if rect_origem is None or rect_destino is None:
        raise ValueError("elemento sem forma")
    dobras = parallel_bends(rect_origem, rect_destino, len(_between(documento, origem, destino)))
    comandos: list[Command] = []
    letra = None
    if tag in MANY_TAGS:
        letra = many_letter(len(_many_of(documento, origem)))
        comandos.extend(_renumber(documento, _many_of(documento, origem)))
    conexao = create_connection(tag, origem, destino, rect_origem, rect_destino, dobras, letra)
    return Composite([InsertFigure(documento, conexao), *comandos], N_("Conectar"))


def nested_nodes(figura: Element) -> list[NodeFigure]:
    """A figura, se for um elemento, ou os elementos dentro dela, se for um grupo (`g`)."""
    if isinstance(figura, NodeFigure):
        return [figura]
    if figura.tag != "g":
        return []
    grupo = figura.child("children")
    return [no for filha in (grupo.children if grupo else []) for no in nested_nodes(filha)]


def all_nodes(documento: Document) -> list[NodeFigure]:
    """Todos os elementos do desenho, inclusive os que estão dentro de grupos."""
    return [no for figura in documento.figures for no in nested_nodes(figura)]


def remove_command(documento: Document, figuras: list[Element]) -> Command:
    """Exclui figuras e, junto, as conexões ligadas a elas (como o TerraER).

    Excluir um grupo leva as conexões ligadas aos elementos de dentro dele.
    """
    escolhidas = {id(f) for f in figuras}
    ligados = {id(no) for f in figuras for no in nested_nodes(f)}
    todas = list(figuras)
    todas += [c for c in connections_of(documento, ligados) if id(c) not in escolhidas]
    ordem = {id(f): i for i, f in enumerate(documento.figures)}
    todas = [f for f in todas if id(f) in ordem]
    todas.sort(key=lambda f: ordem[id(f)], reverse=True)
    return Composite([RemoveFigure(documento, f) for f in todas], N_("Excluir"))


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
    linha = parte.child("points") if figura is not parte else None
    for ponto in linha.children if linha is not None else []:  # linha livre dentro de um grupo
        comandos.extend(_shift(documento, figura, ponto, dx, dy))
    return comandos


def can_move(figura: Element) -> bool:
    """Elementos ER e figuras de apoio com posição. Linhas livres (`l`, `b`, `bezier`) não."""
    return not isinstance(figura, ConnectionFigure) and figura.child("points") is None


def move_command(documento: Document, figuras: list[Element], dx: float, dy: float) -> Command:
    """Move elementos (e figuras de apoio) e religa as conexões que chegam neles."""
    return _move_each(documento, [(f, dx, dy) for f in figuras], N_("Mover"))


def _move_each(
    documento: Document, deslocamentos: list[tuple[Element, float, float]], rotulo: str
) -> Command:
    """Cada figura com o seu deslocamento; as conexões são religadas uma vez, no fim."""
    comandos: list[Command] = []
    movidos: set[int] = set()
    previstos: dict[int, Rect] = {}
    deltas: dict[int, tuple[float, float]] = {}
    for figura, dx, dy in deslocamentos:
        if not can_move(figura):
            continue
        comandos.extend(_shift(documento, figura, figura, dx, dy))
        for no in nested_nodes(figura):  # o próprio elemento, ou os de dentro do grupo
            movidos.add(id(no))
            deltas[id(no)] = (dx, dy)
            rect = node_rect(no)
            if rect is not None:
                previstos[id(no)] = (rect[0] + dx, rect[1] + dy, rect[2], rect[3])
    comandos.extend(_reroute(documento, movidos, previstos, deltas))
    return Composite(comandos, rotulo)


ALIGNMENTS = ("left", "center", "right", "top", "middle", "bottom")


def align_command(documento: Document, nos: list[Element], modo: str) -> Command:
    """Alinha os elementos pela caixa da seleção (como o `AlignAction` do JHotDraw)."""
    if modo not in ALIGNMENTS:
        raise ValueError(f"alinhamento desconhecido: {modo}")
    caixas = [(no, r) for no in nos if isinstance(no, NodeFigure) and (r := node_rect(no))]
    if len(caixas) < 2:
        return Composite([], N_("Alinhar"))
    esquerda = min(r[0] for _, r in caixas)
    direita = max(r[0] + r[2] for _, r in caixas)
    topo = min(r[1] for _, r in caixas)
    base = max(r[1] + r[3] for _, r in caixas)
    deslocamentos: list[tuple[Element, float, float]] = []
    for no, (x, y, w, h) in caixas:
        dx = dy = 0.0
        if modo == "left":
            dx = esquerda - x
        elif modo == "center":
            dx = (esquerda + direita) / 2 - (x + w / 2)
        elif modo == "right":
            dx = direita - (x + w)
        elif modo == "top":
            dy = topo - y
        elif modo == "middle":
            dy = (topo + base) / 2 - (y + h / 2)
        else:
            dy = base - (y + h)
        if dx or dy:
            deslocamentos.append((no, dx, dy))
    return _move_each(documento, deslocamentos, N_("Alinhar"))


def _shapes(no: NodeFigure) -> list[Element]:
    return [p for p in no.parts if p.tag in SHAPE_PART_TAGS]


def min_node_size(no: NodeFigure, medidor: TextMeasurer) -> tuple[float, float]:
    """Menor tamanho da forma ao redimensionar: o texto mais a margem, como ao renomear."""
    texto = _name_part(no)
    if texto is None:
        return (TEXT_MARGIN, TEXT_MARGIN)
    largura, altura = medidor.size(no.name or "", font_of(texto))
    return (largura + TEXT_MARGIN, altura)


def resize_command(
    documento: Document, no: NodeFigure, rect: Rect, medidor: TextMeasurer
) -> Command:
    """Dá à forma a caixa pedida (no mínimo `min_node_size`), centraliza o texto e religa.

    O círculo da generalização continua redondo; o losango interno da entidade associativa
    acompanha a forma com 2 de recuo, como ao criar.
    """
    formas = _shapes(no)
    if not formas:
        raise ValueError("elemento sem forma")
    x, y, w, h = rect
    minimo_w, minimo_h = min_node_size(no, medidor)
    w, h = max(w, minimo_w), max(h, minimo_h)
    if formas[0].tag == "circ":
        w = h = max(w, h)
    comandos: list[Command] = []

    def definir(parte: Element, valores: Rect) -> None:
        for nome, valor in zip(("x", "y", "w", "h"), valores, strict=True):
            novo = format_number(valor)
            if parte.attrs.get(nome) != novo:
                comandos.append(SetAttr(documento, no, parte, nome, novo))

    definir(formas[0], (x, y, w, h))
    for interna in formas[1:]:
        definir(interna, (x + 2, y + 2, w - 4, h - 4))
    texto = _name_part(no)
    if texto is not None:
        tamanho = medidor.size(no.name or "", font_of(texto))
        px, py = text_position((x, y, w, h), tamanho)
        for nome, valor in (("x", px), ("y", py)):
            comandos.append(SetAttr(documento, no, texto, nome, format_number(valor)))
    comandos.extend(_reroute(documento, {id(no)}, {id(no): (x, y, w, h)}))
    return Composite(comandos, N_("Redimensionar"))


class SetOrder(Command):
    """Troca a ordem de empilhamento das figuras."""

    def __init__(self, documento: Document, ordem: list[Element]):
        self._doc, self._nova = documento, ordem
        self._antiga = list(documento.figures)

    def _definir(self, ordem: list[Element]) -> None:
        self._doc.figures[:] = ordem
        self._doc.emit(REORDERED)

    def apply(self) -> None:
        self._antiga = list(self._doc.figures)
        self._definir(self._nova)

    def revert(self) -> None:
        self._definir(self._antiga)


def bring_to_front_command(documento: Document, figuras: list[Element]) -> Command:
    """Leva as figuras para cima de todas, mantendo a ordem entre elas."""
    escolhidas = {id(f) for f in figuras}
    resto = [f for f in documento.figures if id(f) not in escolhidas]
    topo = [f for f in documento.figures if id(f) in escolhidas]
    comando = SetOrder(documento, resto + topo)
    comando.label = N_("Trazer para a frente")
    return comando


def send_to_back_command(documento: Document, figuras: list[Element]) -> Command:
    """Leva as figuras para baixo de todas, mantendo a ordem entre elas."""
    escolhidas = {id(f) for f in figuras}
    resto = [f for f in documento.figures if id(f) not in escolhidas]
    fundo = [f for f in documento.figures if id(f) in escolhidas]
    comando = SetOrder(documento, fundo + resto)
    comando.label = N_("Enviar para trás")
    return comando


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
    return Composite(comandos, N_("Renomear"))


def set_attribute_type_command(documento: Document, no: NodeFigure, tipo: str) -> Command:
    """Tipo SQL de um atributo. Só aceita os cinco valores que o TerraER sabe reler."""
    if tipo not in ATTRIBUTE_TYPES:
        raise ValueError(f"tipo de atributo inválido: {tipo}")
    if no.attribute_type is None:
        raise ValueError("este elemento não tem tipo")
    comando = SetAttr(documento, no, no, "attributeType", tipo)
    comando.label = N_("Mudar tipo")
    return comando


def set_nullable_command(documento: Document, no: NodeFigure, anulavel: bool) -> Command:
    if no.nullable is None:
        raise ValueError("este elemento não tem anulabilidade")
    comando = SetAttr(documento, no, no, "nullable", "true" if anulavel else "false")
    comando.label = N_("Mudar anulabilidade")
    return comando


class SetTag(Command):
    """Troca a tag de um elemento (o tipo de uma conexão)."""

    def __init__(self, documento: Document, figura: Element, tag: str):
        self._doc, self._figura = documento, figura
        self._nova, self._antiga = tag, figura.tag

    def _definir(self, tag: str) -> None:
        self._figura.tag = tag
        self._doc.emit(CHANGED, self._figura)

    def apply(self) -> None:
        self._antiga = self._figura.tag
        self._definir(self._nova)

    def revert(self) -> None:
        self._definir(self._antiga)


def change_connection_type_command(
    documento: Document, conexao: ConnectionFigure, tag: str
) -> Command:
    """Muda o tipo de uma conexão, mantendo as pontas e a linha.

    Acerta o que depende do tipo, como o TerraER grava: o rótulo da generalização, os blocos de
    estilo das conexões duplas e, em `lcaf`, a direção atributo -> dono.
    """
    if tag not in CONNECTION_TAGS:
        raise ValueError(f"tipo de conexão desconhecido: {tag}")
    comandos: list[Command] = []
    if tag == conexao.tag:
        return Composite(comandos, N_("Mudar tipo de conexão"))
    comandos.append(SetTag(documento, conexao, tag))

    tem_rotulo = conexao.generalization_label is not None
    if tag in LABELED_GENERALIZATIONS and not tem_rotulo:
        comandos.append(
            SetAttr(
                documento,
                conexao,
                conexao,
                "labelGeneralizacaoText",
                _(DEFAULT_GENERALIZATION_LABEL),
            )
        )
    elif tag not in LABELED_GENERALIZATIONS and tem_rotulo:
        comandos.append(SetAttr(documento, conexao, conexao, "labelGeneralizacaoText", None))

    # As conexões "N" do elemento de início, como ficarão depois da troca.
    centro = conexao.start
    grupo = [] if centro is None else [c for c in _many_of(documento, centro) if c is not conexao]
    letra = None
    if tag in MANY_TAGS and centro is not None:
        grupo.append(conexao)
        letra = many_letter(len(grupo) - 1)
    filhos = restyle_connection(conexao, tag, letra)
    if [id(f) for f in filhos] != [id(f) for f in conexao.children]:
        comandos.append(SetChildren(documento, conexao, conexao, filhos))
    comandos.extend(_renumber(documento, grupo, pular=conexao))

    inicio, fim = conexao.start, conexao.end
    if (
        tag == "lcaf"
        and inicio is not None
        and fim is not None
        and inicio.tag not in ATTRIBUTE_TAGS
        and fim.tag in ATTRIBUTE_TAGS
    ):
        comandos.extend(_swap_ends(documento, conexao))
    return Composite(comandos, N_("Mudar tipo de conexão"))


def _swap_ends(documento: Document, conexao: ConnectionFigure) -> list[Command]:
    """Inverte a conexão: troca as pontas e a ordem dos pontos da linha."""
    comecar, terminar = conexao.child("startConnector"), conexao.child("endConnector")
    pontos = conexao.child("points")
    comandos: list[Command] = []
    if comecar is not None and terminar is not None:
        comandos.append(SetChildren(documento, conexao, comecar, list(terminar.children)))
        comandos.append(SetChildren(documento, conexao, terminar, list(comecar.children)))
    if pontos is not None:
        comandos.append(SetChildren(documento, conexao, pontos, list(reversed(pontos.children))))
    return comandos


def set_generalization_label_command(
    documento: Document, conexao: ConnectionFigure, texto: str
) -> Command:
    if conexao.generalization_label is None:
        raise ValueError("esta conexão não tem rótulo")
    comando = SetAttr(documento, conexao, conexao, "labelGeneralizacaoText", texto)
    comando.label = N_("Mudar rótulo")
    return comando


# ---------------------------------------------------------------- vértices e pontas da linha


def connection_path(conexao: ConnectionFigure) -> list[tuple[float, float]]:
    """Todos os pontos da linha: ponta inicial, dobras e ponta final."""
    return [_xy(p) for p in conexao.points]


def _path_command(
    documento: Document,
    conexao: ConnectionFigure,
    dobras: list[tuple[float, float]],
    rotulo: str,
    inicio: Element | None = None,
    fim: Element | None = None,
) -> Command:
    """Troca as dobras da linha e religa as pontas às bordas (mirando a dobra mais próxima)."""
    pontos = conexao.child("points")
    if pontos is None or len(pontos.children) < 2:
        raise ValueError("conexão sem linha")
    inicio = inicio if inicio is not None else conexao.start
    fim = fim if fim is not None else conexao.end
    primeiro, ultimo = pontos.children[0], pontos.children[-1]
    rect_inicio = node_rect(inicio) if inicio is not None else None
    rect_fim = node_rect(fim) if fim is not None else None
    if rect_inicio is not None and rect_fim is not None:
        (x1, y1), (x2, y2) = route_ends(rect_inicio, rect_fim, dobras)
        primeiro, ultimo = _moved_point(primeiro, x1, y1), _moved_point(ultimo, x2, y2)
    novos = [primeiro, *(bend_point(x, y) for x, y in dobras), ultimo]
    comando = SetChildren(documento, conexao, pontos, novos)
    comando.label = rotulo
    return comando


def _bends(conexao: ConnectionFigure) -> list[tuple[float, float]]:
    return connection_path(conexao)[1:-1]


def add_bend_command(
    documento: Document, conexao: ConnectionFigure, trecho: int, ponto: tuple[float, float]
) -> Command:
    """Põe uma dobra no `trecho` (0 = da ponta inicial à 1ª dobra), no ponto dado."""
    dobras = _bends(conexao)
    if not 0 <= trecho <= len(dobras):
        raise ValueError(f"trecho inexistente: {trecho}")
    return _path_command(
        documento, conexao, [*dobras[:trecho], ponto, *dobras[trecho:]], N_("Adicionar vértice")
    )


def move_bend_command(
    documento: Document, conexao: ConnectionFigure, indice: int, ponto: tuple[float, float]
) -> Command:
    """Leva a dobra `indice` (0 = a primeira) para o ponto dado."""
    dobras = _bends(conexao)
    if not 0 <= indice < len(dobras):
        raise ValueError(f"vértice inexistente: {indice}")
    dobras[indice] = ponto
    return _path_command(documento, conexao, dobras, N_("Mover vértice"))


def remove_bend_command(documento: Document, conexao: ConnectionFigure, indice: int) -> Command:
    dobras = _bends(conexao)
    if not 0 <= indice < len(dobras):
        raise ValueError(f"vértice inexistente: {indice}")
    del dobras[indice]
    return _path_command(documento, conexao, dobras, N_("Remover vértice"))


def straighten_command(documento: Document, conexao: ConnectionFigure) -> Command:
    """Tira todas as dobras: a linha volta a ir de centro a centro."""
    return _path_command(documento, conexao, [], N_("Endireitar linha"))


def reconnect_command(
    documento: Document, conexao: ConnectionFigure, ponta: str, no: NodeFigure
) -> Command:
    """Liga a ponta `"start"` ou `"end"` da conexão a outro elemento (como arrastar a ponta no
    TerraER). As dobras ficam; o tipo, o sentido e a letra da conexão não mudam."""
    if ponta not in ("start", "end"):
        raise ValueError(f"ponta desconhecida: {ponta}")
    outro = conexao.end if ponta == "start" else conexao.start
    if no is outro:
        raise ValueError("uma conexão precisa de dois elementos diferentes")
    envoltorio = conexao.child("startConnector" if ponta == "start" else "endConnector")
    if envoltorio is None:
        raise ValueError("conexão sem conector")
    conector = Element("rConnector", children=[Element("Owner", children=[no])], has_id=True)
    comandos: list[Command] = [SetChildren(documento, conexao, envoltorio, [conector])]
    inicio, fim = (no, conexao.end) if ponta == "start" else (conexao.start, no)
    comandos.append(_path_command(documento, conexao, _bends(conexao), "", inicio, fim))
    return Composite(comandos, N_("Reconectar"))


# ---------------------------------------------------------------- tipo de atributo inválido


def invalid_attribute_types(documento: Document) -> list[NodeFigure]:
    """Atributos com `attributeType` fora dos cinco que o TerraER sabe reler (RNF-16).

    O TerraER abre um arquivo assim, mas falha ao salvar; por isso o HaradaER nunca o regrava.
    """
    return [
        f
        for f in documento.figures
        if isinstance(f, NodeFigure)
        and f.attribute_type is not None
        and f.attribute_type not in ATTRIBUTE_TYPES
    ]


def fix_attribute_types_command(documento: Document) -> Command:
    """Troca cada tipo inválido pelo tipo padrão do elemento (o mesmo de um atributo novo)."""
    comandos: list[Command] = []
    for no in invalid_attribute_types(documento):
        tipado = KINDS[no.tag].typed
        padrao = tipado[1] if tipado is not None else "VARCHAR2(128)"
        comandos.append(SetAttr(documento, no, no, "attributeType", padrao))
    return Composite(comandos, N_("Corrigir tipos de atributo"))


# ---------------------------------------------------------------- agrupar e desagrupar


def can_group(figuras: list[Element]) -> bool:
    """Agrupa-se duas ou mais figuras que não sejam conexões (as conexões ficam fora do grupo,
    ligadas aos elementos de dentro, como no TerraER)."""
    return len([f for f in figuras if not isinstance(f, ConnectionFigure)]) >= 2


def group_command(documento: Document, figuras: list[Element]) -> tuple[Command, Element]:
    """Junta as figuras num grupo `g` no topo do desenho, na ordem de empilhamento delas
    (como o `GroupAction` do JHotDraw)."""
    if not can_group(figuras):
        raise ValueError("é preciso escolher ao menos duas figuras que não sejam conexões")
    ordem = {id(f): i for i, f in enumerate(documento.figures)}
    membros = sorted(
        (f for f in figuras if not isinstance(f, ConnectionFigure) and id(f) in ordem),
        key=lambda f: ordem[id(f)],
    )
    grupo = SupportFigure("g", children=[Element("children", children=membros)], has_id=True)
    comandos: list[Command] = [RemoveFigure(documento, f) for f in reversed(membros)]
    comandos.append(InsertFigure(documento, grupo))
    return Composite(comandos, N_("Agrupar")), grupo


def ungroup_command(documento: Document, grupo: Element) -> tuple[Command, list[Element]]:
    """Devolve as figuras do grupo ao topo do desenho e apaga o grupo (como o JHotDraw)."""
    if grupo.tag != "g" or not any(f is grupo for f in documento.figures):
        raise ValueError("a figura não é um grupo do desenho")
    filhos = grupo.child("children")
    membros = list(filhos.children) if filhos is not None else []
    comandos: list[Command] = [RemoveFigure(documento, grupo)]
    comandos += [InsertFigure(documento, f) for f in membros]
    return Composite(comandos, N_("Desagrupar")), membros
