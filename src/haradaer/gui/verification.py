"""Textos da verificação e da recomendação (RF-09, RF-10).

O núcleo dá códigos estáveis; quem os põe em português é a interface (D-09).
"""

from __future__ import annotations

from haradaer.core.rules import INCOMPLETE, INVALID_PAIR, Issue
from haradaer.gui.palette import CONNECTIONS, ELEMENTS

_NOMES = dict(ELEMENTS) | dict(CONNECTIONS) | {"g": "Grupo", "lcf": "Ligação de atributo"}

_FALTANDO = {
    "ambas": "as duas pontas estão soltas",
    "início": "a ponta de início está solta",
    "fim": "a ponta de fim está solta",
}


def name_of(tag: str) -> str:
    return _NOMES.get(tag, tag)


def issue_text(issue: Issue) -> str:
    detalhes = issue.details
    conexao = name_of(detalhes.get("connection", issue.figure.tag))
    if issue.code == INCOMPLETE:
        return f"{conexao}: {_FALTANDO.get(detalhes.get('missing', ''), 'ponta solta')}"
    if issue.code == INVALID_PAIR:
        inicio, fim = name_of(detalhes["start"]), name_of(detalhes["end"])
        return f"{conexao} não é aceita entre {inicio} e {fim}"
    return conexao


def pairs_text(pares: list[tuple[str, str]]) -> str:
    return ", ".join(f"{name_of(a)} → {name_of(b)}" for a, b in pares)
