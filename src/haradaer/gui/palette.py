"""Nomes (em português) dos elementos e conexões da barra de ferramentas."""

from haradaer.core.figures.factory import KINDS

# Ordem e nomes seguem REQUISITOS.md, seções 3.1 e 3.2.
ELEMENTS: list[tuple[str, str]] = [(tag, kind.label) for tag, kind in KINDS.items()]

CONNECTIONS: list[tuple[str, str]] = [
    ("llabelUm", 'Participação, lado "1"'),
    ("llabelMuitos", 'Participação, lado "N"'),
    ("llabelDoubleUm", 'Participação total, lado "1"'),
    ("llabelDoubleMuitos", 'Participação total, lado "N"'),
    ("lcaf", "Ligação de atributo"),
    ("generalizacaoLine", "Generalização simples"),
    ("llabelGeneralizacao", "Participação opcional em generalização"),
    ("llabelDoubleGeneralizacao", "Participação obrigatória em generalização"),
    ("llabel", "Conexão livre"),
]
