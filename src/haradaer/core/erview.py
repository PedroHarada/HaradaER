"""Visão ER derivada do desenho: a quem pertence cada atributo e a busca por nome.

Nada aqui é gravado; é calculado a partir das conexões `lcaf` (ARQUITETURA.md, seção 4.1).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from haradaer.core.commands.edit import all_nodes
from haradaer.core.figures.tags import TYPED_ATTRIBUTE_TAGS
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element

ATTRIBUTE_TAGS = TYPED_ATTRIBUTE_TAGS | {"atrderivado"}
ATTRIBUTE_LINKS = ("lcaf", "lcf")
_CHAVES = ("atrchave", "atrchaveparcial")


def attribute_owners(documento: Document) -> dict[int, Element]:
    """`id(atributo)` -> dono (entidade, relacionamento ou outro atributo, se composto).

    Ligação entre um atributo e um elemento que não é atributo: o atributo é a ponta que é
    atributo. Entre dois atributos, a direção não basta, porque o composto e o multivalorado
    podem ser dono um do outro (`atr` com parte `atrmulti` e `atrmulti` com parte `atr`). Vale,
    em ordem: a ponta que já tem dono é a dona; uma chave é sempre a dona (as partes de uma
    chave são simples); senão, a de início é o atributo (o HaradaER grava atributo -> dono).
    Vale a primeira ligação encontrada para cada atributo.
    """
    donos: dict[int, Element] = {}
    entre_atributos: list[tuple[Element, Element]] = []
    for figura in documento.figures:
        if not isinstance(figura, ConnectionFigure) or figura.tag not in ATTRIBUTE_LINKS:
            continue
        inicio, fim = figura.start, figura.end
        if inicio is None or fim is None:
            continue
        if inicio.tag in ATTRIBUTE_TAGS and fim.tag in ATTRIBUTE_TAGS:
            entre_atributos.append((inicio, fim))
        elif inicio.tag in ATTRIBUTE_TAGS:
            donos.setdefault(id(inicio), fim)
        elif fim.tag in ATTRIBUTE_TAGS:
            donos.setdefault(id(fim), inicio)
    # de cima para baixo: cada volta liga as partes dos atributos que já têm dono
    pendentes = entre_atributos
    while pendentes:
        restantes = []
        for inicio, fim in pendentes:
            com_inicio, com_fim = id(inicio) in donos, id(fim) in donos
            if com_inicio and not com_fim:
                donos[id(fim)] = inicio
            elif com_fim and not com_inicio:
                donos[id(inicio)] = fim
            elif not com_inicio:
                restantes.append((inicio, fim))
        if len(restantes) == len(pendentes):
            break
        pendentes = restantes
    for inicio, fim in pendentes:  # partes de atributos soltos: a chave e a direção decidem
        if id(inicio) in donos or id(fim) in donos:
            continue
        if inicio.tag in _CHAVES and fim.tag not in _CHAVES:
            donos[id(fim)] = inicio
        else:
            donos[id(inicio)] = fim
    return donos


def normalize(texto: str) -> str:
    """Para comparar nomes sem diferenciar maiúsculas nem acentos."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).casefold()


def find_nodes(documento: Document, texto: str) -> list[NodeFigure]:
    """Elementos cujo nome contém o texto, na ordem do desenho (RF-08)."""
    procurado = normalize(texto.strip())
    return [f for f in all_nodes(documento) if procurado in normalize(f.name or "")]


# ------------------------------------------------------------- relacionamentos e generalizações

PARTICIPATION_LINKS = ("llabelUm", "llabelMuitos", "llabelDoubleUm", "llabelDoubleMuitos")
RELATIONSHIP_TAGS = ("rel", "relfraco", "entrel")
ENTITY_TAGS = ("ent", "entfraca", "entrel")
GENERALIZATION_CIRCLES = ("uniao", "disjuncao", "sobreposicao")
_LADO_SUPERCLASSE = ("llabelGeneralizacao", "llabelDoubleGeneralizacao")


@dataclass(frozen=True)
class Participation:
    """Uma entidade num relacionamento: razão de cardinalidade ("1" ou "N") e se é total."""

    entity: NodeFigure
    cardinality: str
    total: bool
    connection: ConnectionFigure


def participants(documento: Document) -> dict[int, list[Participation]]:
    """`id(relacionamento)` -> participações, na ordem do desenho.

    A cardinalidade e a participação estão na tag da conexão (`Um`/`Muitos`, `Double` = total).
    As duas pontas são testadas: arquivos antigos podem vir em qualquer sentido. A entidade
    associativa é relacionamento das entidades ligadas a ela e entidade dos relacionamentos a
    que ela se liga. O recursivo aparece duas vezes, uma por papel.
    """
    resultado: dict[int, list[Participation]] = {}
    for figura in documento.figures:
        if not isinstance(figura, ConnectionFigure) or figura.tag not in PARTICIPATION_LINKS:
            continue
        inicio, fim = figura.start, figura.end
        if not isinstance(inicio, NodeFigure) or not isinstance(fim, NodeFigure):
            continue
        relacionamento, entidade = _relationship_and_entity(inicio, fim)
        if relacionamento is None or entidade is None:
            continue
        cardinalidade = "N" if "Muitos" in figura.tag else "1"
        total = "Double" in figura.tag
        resultado.setdefault(id(relacionamento), []).append(
            Participation(entidade, cardinalidade, total, figura)
        )
    return resultado


def _relationship_and_entity(a: NodeFigure, b: NodeFigure):
    for rel, ent in ((a, b), (b, a)):
        if rel.tag in ("rel", "relfraco") and ent.tag in ENTITY_TAGS:
            return rel, ent
    for rel, ent in ((a, b), (b, a)):  # associativa como relacionamento das entidades
        if rel.tag == "entrel" and ent.tag in ("ent", "entfraca"):
            return rel, ent
    return None, None


@dataclass(frozen=True)
class Generalization:
    """Um círculo (ou uma ligação direta) de especialização/generalização.

    `superclasses` tem uma entidade na especialização e as definidoras na união (categoria);
    `subclasses` tem as subclasses, ou a categoria na união. `assumed` diz que a direção não
    estava clara no desenho e foi deduzida.
    """

    circle: Element
    kind: str  # "disjuncao", "sobreposicao", "uniao" ou "direta"
    superclasses: tuple[NodeFigure, ...]
    subclasses: tuple[NodeFigure, ...]
    total: bool
    assumed: bool = False


def generalizations(documento: Document) -> list[Generalization]:
    """Especializações do desenho, na ordem do desenho.

    Ligam a superclasse ao círculo as linhas de participação em generalização (opcional ou
    obrigatória, que diz se a especialização é total); a `generalizacaoLine` liga o círculo à
    subclasse. Na ligação direta entre duas entidades (uma subclasse só), a origem é a
    superclasse, como o círculo é a origem nas outras. Se todas as ligações de um círculo forem do
    mesmo tipo, a superclasse é a única entidade com atributo chave; sem isso, fica de fora.
    """
    lados: dict[int, list[tuple[str, NodeFigure]]] = {}
    circulos: dict[int, Element] = {}
    diretas: list[Generalization] = []
    for figura in documento.figures:
        if not isinstance(figura, ConnectionFigure):
            continue
        inicio, fim = figura.start, figura.end
        if not isinstance(inicio, NodeFigure) or not isinstance(fim, NodeFigure):
            continue
        if (
            figura.tag == "generalizacaoLine"
            and inicio.tag in ENTITY_TAGS
            and fim.tag in ENTITY_TAGS
        ):
            diretas.append(Generalization(figura, "direta", (inicio,), (fim,), False, True))
            continue
        if figura.tag not in ("generalizacaoLine", *_LADO_SUPERCLASSE):
            continue
        for circulo, entidade in ((inicio, fim), (fim, inicio)):
            if circulo.tag in GENERALIZATION_CIRCLES and entidade.tag in ENTITY_TAGS:
                circulos[id(circulo)] = circulo
                lados.setdefault(id(circulo), []).append((figura.tag, entidade))
                break
    chaves = {id(dono) for no, dono in _key_owners(documento)}
    resultado: list[Generalization] = []
    for chave, circulo in circulos.items():
        ligacoes = lados[chave]
        de_cima = [e for t, e in ligacoes if t in _LADO_SUPERCLASSE]
        de_baixo = [e for t, e in ligacoes if t == "generalizacaoLine"]
        total = any(t == "llabelDoubleGeneralizacao" for t, _e in ligacoes)
        assumida = False
        if not de_cima or not de_baixo:  # todas do mesmo tipo: a superclasse é quem tem chave
            todas = de_cima or de_baixo
            com_chave = [e for e in todas if id(e) in chaves]
            if len(com_chave) != 1 or len(todas) < 2:
                continue
            de_cima = com_chave
            de_baixo = [e for e in todas if e is not com_chave[0]]
            assumida = True
        resultado.append(
            Generalization(circulo, circulo.tag, tuple(de_cima), tuple(de_baixo), total, assumida)
        )
    return resultado + diretas


def _key_owners(documento: Document):
    donos = attribute_owners(documento)
    for no in all_nodes(documento):
        if no.tag in _CHAVES and id(no) in donos:
            yield no, donos[id(no)]
