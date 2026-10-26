"""Atalhos de uma tecla da Edição rápida.

Uma letra por família de ferramentas. Apertar a mesma letra de novo passa para o próximo tipo
da família, e Shift + a letra volta. As teclas são as mesmas em português e em inglês. Só valem
com a Edição rápida ligada e com o foco no desenho (um campo de texto recebe a letra como texto).
"""

from __future__ import annotations

from haradaer.gui.view import SELECT, Tool

_C, _L = "create", "connect"

FAMILIES: list[tuple[str, list[Tool]]] = [
    ("V", [SELECT]),
    ("E", [Tool(_C, "ent"), Tool(_C, "entfraca"), Tool(_C, "entrel")]),
    ("R", [Tool(_C, "rel"), Tool(_C, "relfraco")]),
    (
        "A",
        [
            Tool(_C, "atr"),
            Tool(_C, "atrchave"),
            Tool(_C, "atrchaveparcial"),
            Tool(_C, "atrmulti"),
            Tool(_C, "atrderivado"),
        ],
    ),
    ("G", [Tool(_C, "disjuncao"), Tool(_C, "sobreposicao"), Tool(_C, "uniao")]),
    ("1", [Tool(_L, "llabelUm"), Tool(_L, "llabelDoubleUm")]),
    ("N", [Tool(_L, "llabelMuitos"), Tool(_L, "llabelDoubleMuitos")]),
    ("L", [Tool(_L, "lcaf")]),
    (
        "H",
        [
            Tool(_L, "generalizacaoLine"),
            Tool(_L, "llabelGeneralizacao"),
            Tool(_L, "llabelDoubleGeneralizacao"),
        ],
    ),
    ("C", [Tool(_L, "llabel")]),
]

_BY_KEY = dict(FAMILIES)


def key_of(tool: Tool) -> str | None:
    """A letra da família da ferramenta."""
    for tecla, ferramentas in FAMILIES:
        if tool in ferramentas:
            return tecla
    return None


def position(tool: Tool) -> tuple[int, int]:
    """(posição na família, a partir de 1; tamanho da família)."""
    tecla = key_of(tool)
    if tecla is None:
        return (0, 0)
    ferramentas = _BY_KEY[tecla]
    return (ferramentas.index(tool) + 1, len(ferramentas))


def next_tool(tecla: str, atual: Tool, *, voltar: bool = False) -> Tool | None:
    """A ferramenta que a tecla escolhe: a primeira da família, ou a seguinte (a anterior, com
    `voltar`) se a ferramenta atual já é dessa família. `None` se a tecla não é um atalho."""
    ferramentas = _BY_KEY.get(tecla.upper())
    if ferramentas is None:
        return None
    if atual not in ferramentas:
        return ferramentas[-1] if voltar else ferramentas[0]
    passo = -1 if voltar else 1
    return ferramentas[(ferramentas.index(atual) + passo) % len(ferramentas)]
