"""Verificação do modelo (RF-09): quais conexões o TerraER pintaria de vermelho."""

from __future__ import annotations

from dataclasses import dataclass, field

from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.rules.tables import CONNECTION_RULES, LINE_FREE

INVALID_PAIR = "connection.invalid_pair"
INCOMPLETE = "connection.incomplete"


@dataclass(frozen=True)
class Issue:
    """Um problema encontrado. `code` é estável; a interface o traduz para o usuário (D-09)."""

    code: str
    figure: Element
    details: dict[str, str] = field(default_factory=dict)


def is_valid_connection(connection_tag: str, start_tag: str, end_tag: str) -> bool:
    """O TerraER aceita uma conexão desse tipo entre esses dois elementos?"""
    return (start_tag, end_tag) in CONNECTION_RULES.get(connection_tag, frozenset())


def validate(document: Document) -> list[Issue]:
    """Problemas de cada conexão do desenho, na ordem de empilhamento.

    Igual ao TerraER: a conexão livre (`llabel`) nunca tem problema; as demais têm problema se
    faltar uma das pontas ou se os dois elementos ligados não combinarem com o tipo da conexão.
    """
    problemas: list[Issue] = []
    for figura in document.figures:
        if not isinstance(figura, ConnectionFigure) or figura.tag == LINE_FREE:
            continue
        inicio, fim = figura.start, figura.end
        if inicio is None or fim is None:
            faltando = (
                "ambas" if inicio is None and fim is None else "início" if inicio is None else "fim"
            )
            problemas.append(
                Issue(INCOMPLETE, figura, {"connection": figura.tag, "missing": faltando})
            )
        elif not is_valid_connection(figura.tag, inicio.tag, fim.tag):
            problemas.append(
                Issue(
                    INVALID_PAIR,
                    figura,
                    {"connection": figura.tag, "start": inicio.tag, "end": fim.tag},
                )
            )
    return problemas
