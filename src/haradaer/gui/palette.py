"""Nomes (em português; traduzidos ao mostrar) dos elementos e conexões da barra de ferramentas."""

from haradaer.core.figures.factory import KINDS
from haradaer.i18n import N_

# Ordem e nomes seguem REQUISITOS.md, seções 3.1 e 3.2.
ELEMENTS: list[tuple[str, str]] = [(tag, kind.label) for tag, kind in KINDS.items()]

CONNECTIONS: list[tuple[str, str]] = [
    ("llabelUm", N_('Participação, lado "1"')),
    ("llabelMuitos", N_('Participação, lado "N"')),
    ("llabelDoubleUm", N_('Participação total, lado "1"')),
    ("llabelDoubleMuitos", N_('Participação total, lado "N"')),
    ("lcaf", N_("Ligação de atributo")),
    ("generalizacaoLine", N_("Generalização simples")),
    ("llabelGeneralizacao", N_("Participação opcional em generalização")),
    ("llabelDoubleGeneralizacao", N_("Participação obrigatória em generalização")),
    ("llabel", N_("Conexão livre")),
]
