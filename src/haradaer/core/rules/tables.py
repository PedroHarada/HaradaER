"""Regras de conexão do TerraER, em dados.

Medidas no TerraER 3.14 com `ModelValidation` (a validação em vermelho). Os pares são
(tag de uma ponta, tag da outra ponta). Cada conjunto foi conferido par a par contra a saída do
próprio TerraER (`docs/referencia-terraer/matriz-validacao.txt`), menos as diferenças de
`BEYOND_TERRAER`.
"""

from __future__ import annotations

from haradaer.core.figures.tags import NODE_TAGS

Pair = tuple[str, str]

ENT, ENTFRACA, REL, RELFRACO, ENTREL = "ent", "entfraca", "rel", "relfraco", "entrel"
GENERALIZATIONS = ("uniao", "disjuncao", "sobreposicao")
LINE_FREE = "llabel"


def _symmetric(pares: set[Pair]) -> frozenset[Pair]:
    return frozenset(pares | {(b, a) for a, b in pares})


_PARTICIPATION = _symmetric(
    {
        (ENT, REL),
        (ENT, RELFRACO),
        (ENT, ENTREL),
        (ENTFRACA, REL),
        (ENTFRACA, ENTREL),
        (REL, ENTREL),
        (RELFRACO, ENTREL),
    }
)
# A participação total (linha dupla) também liga entidade fraca e relacionamento fraco.
_TOTAL_PARTICIPATION = _PARTICIPATION | _symmetric({(ENTFRACA, RELFRACO)})

# Quem pode ter quais atributos (a validação do TerraER vale nas duas direções).
_ATTRIBUTES_OF = {
    ENT: ("atr", "atrchave", "atrderivado", "atrmulti"),
    ENTFRACA: ("atr", "atrchaveparcial", "atrderivado", "atrmulti"),
    REL: ("atr", "atrderivado", "atrmulti"),
    RELFRACO: ("atr", "atrderivado", "atrmulti"),
    ENTREL: ("atr", "atrchave", "atrderivado", "atrmulti"),
    "atr": ("atr", "atrmulti"),  # atributo composto
    # Só no HaradaER (BEYOND_TERRAER): chave composta e os aninhamentos com multivalorado.
    "atrchave": ("atr",),
    "atrchaveparcial": ("atr",),
    "atrmulti": ("atr", "atrmulti"),
}
_ATTRIBUTE_LINK = _symmetric(
    {(dono, a) for dono, atributos in _ATTRIBUTES_OF.items() for a in atributos}
)

_GENERALIZATION_LINK = _symmetric(
    {(e, g) for e in (ENT, ENTFRACA, ENTREL) for g in GENERALIZATIONS}
)

# `generalizacaoLine` é a única conexão assimétrica: o círculo fica na origem.
_SIMPLE_GENERALIZATION = frozenset({(ENT, ENT), *((g, ENT) for g in GENERALIZATIONS)})

# Pares que o HaradaER aceita e o TerraER pinta de vermelho, válidos no modelo ER (Elmasri e
# Navathe, cap. 3). O TerraER só aceita sub-atributo simples em atributo simples. O arquivo não
# muda: só a verificação.
# - chave composta: `Registration(State, Number)` é a chave de CARRO; vale também para a chave
#   parcial da entidade fraca;
# - multivalorado composto: `{PreviousDegrees (College, Year, Degree, Field)}`, ou o telefone
#   com DDD e número;
# - aninhamento em qualquer nível: um composto com parte multivalorada, e um multivalorado
#   composto com parte multivalorada (`{AddressPhone({Phone(AreaCode, Number)}, Address)}`).
_ATRIBUTOS_ANINHADOS = _symmetric(
    {
        ("atrchave", "atr"),
        ("atrchaveparcial", "atr"),
        ("atrmulti", "atr"),
        ("atrmulti", "atrmulti"),
    }
)
BEYOND_TERRAER: dict[str, frozenset[Pair]] = {
    "lcaf": _ATRIBUTOS_ANINHADOS,
    "lcf": _ATRIBUTOS_ANINHADOS,
}

CONNECTION_RULES: dict[str, frozenset[Pair]] = {
    LINE_FREE: frozenset((a, b) for a in NODE_TAGS for b in NODE_TAGS),
    "llabelUm": _PARTICIPATION,
    "llabelMuitos": _PARTICIPATION,
    "llabelDoubleUm": _TOTAL_PARTICIPATION,
    "llabelDoubleMuitos": _TOTAL_PARTICIPATION,
    "lcaf": _ATTRIBUTE_LINK,
    "lcf": _ATTRIBUTE_LINK,
    "generalizacaoLine": _SIMPLE_GENERALIZATION,
    "llabelGeneralizacao": _GENERALIZATION_LINK,
    "llabelDoubleGeneralizacao": _GENERALIZATION_LINK,
}

# Ordem em que as conexões são oferecidas na recomendação (a das regras do TerraER).
# A conexão livre fica de fora: serve para qualquer par e não é uma "recomendação".
RECOMMENDATION_ORDER = (
    "llabelUm",
    "llabelMuitos",
    "llabelDoubleUm",
    "llabelDoubleMuitos",
    "llabelGeneralizacao",
    "llabelDoubleGeneralizacao",
    "lcaf",
    "generalizacaoLine",
)

# Ordem dos elementos nas listas devolvidas (a da paleta do TerraER).
NODE_ORDER = (
    "ent",
    "entfraca",
    "rel",
    "relfraco",
    "entrel",
    "atr",
    "atrchave",
    "atrchaveparcial",
    "atrderivado",
    "atrmulti",
    "uniao",
    "disjuncao",
    "sobreposicao",
)
