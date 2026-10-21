"""Visão ER derivada do desenho: a quem pertence cada atributo e a busca por nome.

Nada aqui é gravado; é calculado a partir das conexões `lcaf` (ARQUITETURA.md, seção 4.1).
"""

from __future__ import annotations

import unicodedata

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
