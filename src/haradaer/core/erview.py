"""Visão ER derivada do desenho: a quem pertence cada atributo e a busca por nome.

Nada aqui é gravado; é calculado a partir das conexões `lcaf` (ARQUITETURA.md, seção 4.1).
"""

from __future__ import annotations

import unicodedata

from haradaer.core.figures.tags import TYPED_ATTRIBUTE_TAGS
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element

ATTRIBUTE_TAGS = TYPED_ATTRIBUTE_TAGS | {"atrderivado"}
ATTRIBUTE_LINKS = ("lcaf", "lcf")


def attribute_owners(documento: Document) -> dict[int, Element]:
    """`id(atributo)` -> dono (entidade, relacionamento ou outro atributo, se composto).

    Em cada ligação de atributo, o atributo é a ponta que é atributo; se as duas forem, é a de
    início (o HaradaER grava atributo -> dono). Vale a primeira ligação encontrada.
    """
    donos: dict[int, Element] = {}
    for figura in documento.figures:
        if not isinstance(figura, ConnectionFigure) or figura.tag not in ATTRIBUTE_LINKS:
            continue
        inicio, fim = figura.start, figura.end
        if inicio is None or fim is None:
            continue
        if inicio.tag in ATTRIBUTE_TAGS:
            atributo, dono = inicio, fim
        elif fim.tag in ATTRIBUTE_TAGS:
            atributo, dono = fim, inicio
        else:
            continue
        donos.setdefault(id(atributo), dono)
    return donos


def normalize(texto: str) -> str:
    """Para comparar nomes sem diferenciar maiúsculas nem acentos."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).casefold()


def find_nodes(documento: Document, texto: str) -> list[NodeFigure]:
    """Elementos cujo nome contém o texto, na ordem do desenho (RF-08)."""
    procurado = normalize(texto.strip())
    return [
        f
        for f in documento.figures
        if isinstance(f, NodeFigure) and procurado in normalize(f.name or "")
    ]
