"""Avisos de estrutura: o que a teoria do modelo ER pede além de cada ligação estar certa.

A verificação de conexões (`validation.py`) olha uma ligação por vez, como o TerraER. Estes
avisos olham o modelo como um todo e só apontam o que a teoria considera errado em qualquer
caso (Elmasri e Navathe, caps. 3 e 4), nunca o que é só costume:

- entidade sem atributo chave. Ficam de fora as que recebem a chave de outra: a subclasse de
  uma especialização (herda a da superclasse), a entidade ligada a uma união (categoria, cuja
  chave pode vir das superclasses) e a entidade associativa (a chave vem do relacionamento);
- entidade fraca sem relacionamento identificador;
- relacionamento identificador sem entidade fraca;
- relacionamento com menos de dois participantes (o recursivo conta duas vezes: um por papel);
- especialização (círculo) com menos de dois elementos ligados: falta a superclasse ou a
  subclasse;
- atributo sem dono.

Não há aviso para entidade fraca sem chave parcial: ela "normalmente" tem uma, mas pode não ter
(por exemplo, quando cada dono tem no máximo uma). Os elementos dentro de grupos também contam.
"""

from __future__ import annotations

from collections import defaultdict

from haradaer.core.commands.edit import all_nodes
from haradaer.core.erview import ATTRIBUTE_TAGS, attribute_owners
from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.rules.tables import GENERALIZATIONS
from haradaer.core.rules.validation import Issue

NO_KEY = "structure.no_key"
WEAK_WITHOUT_IDENTIFYING = "structure.weak_without_identifying"
IDENTIFYING_WITHOUT_WEAK = "structure.identifying_without_weak"
FEW_PARTICIPANTS = "structure.few_participants"
INCOMPLETE_SPECIALIZATION = "structure.incomplete_specialization"
ORPHAN_ATTRIBUTE = "structure.orphan_attribute"

STRUCTURE_CODES = (
    NO_KEY,
    WEAK_WITHOUT_IDENTIFYING,
    IDENTIFYING_WITHOUT_WEAK,
    FEW_PARTICIPANTS,
    INCOMPLETE_SPECIALIZATION,
    ORPHAN_ATTRIBUTE,
)

PARTICIPATION_LINKS = ("llabelUm", "llabelMuitos", "llabelDoubleUm", "llabelDoubleMuitos")
GENERALIZATION_LINKS = ("generalizacaoLine", "llabelGeneralizacao", "llabelDoubleGeneralizacao")
_ENTIDADES = ("ent", "entfraca", "entrel")
_RELACIONAMENTOS = ("rel", "relfraco")
_CHAVES = ("atrchave", "atrchaveparcial")


def check_structure(document: Document) -> list[Issue]:
    """Avisos de estrutura, um por elemento, na ordem do desenho."""
    ligacoes: dict[int, list[tuple[str, Element]]] = defaultdict(list)  # id -> (tipo, outro)
    for figura in document.figures:
        if not isinstance(figura, ConnectionFigure):
            continue
        inicio, fim = figura.start, figura.end
        if inicio is None or fim is None or inicio is fim:
            continue
        ligacoes[id(inicio)].append((figura.tag, fim))
        ligacoes[id(fim)].append((figura.tag, inicio))
    # Subclasses: a ponta de entidade da `generalizacaoLine` (o círculo fica na origem). Na
    # ligação direta entidade -> entidade, as duas pontas ficam de fora: a direção desenhada não
    # garante qual é a superclasse, e um aviso a menos é melhor que um aviso errado.
    subclasses = set()
    for figura in document.figures:
        if isinstance(figura, ConnectionFigure) and figura.tag == "generalizacaoLine":
            for ponta in (figura.start, figura.end):
                if ponta is not None and ponta.tag in _ENTIDADES:
                    subclasses.add(id(ponta))
    donos = attribute_owners(document)
    chave_de = {
        id(donos[id(n)]) for n in all_nodes(document) if n.tag in _CHAVES and id(n) in donos
    }

    avisos: list[Issue] = []
    for no in all_nodes(document):
        tag, minhas = no.tag, ligacoes.get(id(no), [])
        codigo = None
        if tag in ("ent", "entfraca"):
            herda = id(no) in subclasses or any(o.tag == "uniao" for _, o in minhas)
            if tag == "entfraca" and not any(o.tag == "relfraco" for _, o in minhas):
                codigo = WEAK_WITHOUT_IDENTIFYING
            elif tag == "ent" and not herda and id(no) not in chave_de:
                codigo = NO_KEY
        elif tag in _RELACIONAMENTOS:
            participantes = [
                o for t, o in minhas if t in PARTICIPATION_LINKS and o.tag in _ENTIDADES
            ]
            if len(participantes) < 2:
                codigo = FEW_PARTICIPANTS
            elif tag == "relfraco" and not any(o.tag == "entfraca" for o in participantes):
                codigo = IDENTIFYING_WITHOUT_WEAK
        elif tag in GENERALIZATIONS:
            if sum(1 for t, _ in minhas if t in GENERALIZATION_LINKS) < 2:
                codigo = INCOMPLETE_SPECIALIZATION
        elif tag in ATTRIBUTE_TAGS and id(no) not in donos:
            codigo = ORPHAN_ATTRIBUTE
        if codigo is not None:
            avisos.append(Issue(codigo, no, {"element": tag}))
    return avisos
