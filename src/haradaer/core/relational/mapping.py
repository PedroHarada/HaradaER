"""Mapeamento do diagrama ER/EER para o esquema lógico relacional (RF-23).

Segue o algoritmo de Elmasri e Navathe, na ordem do livro (as regras e as escolhas onde o livro
deixa opções estão em `docs/CONCEITOS.md`):

1. entidade regular: uma relação com os atributos simples (as partes dos compostos); a chave
   vira a chave primária;
2. entidade fraca: chave estrangeira para a dona; chave primária = chave da dona + chave parcial;
3. 1:1: chave estrangeira do lado com participação total (empate: a primeira ligada);
4. 1:N: chave estrangeira do lado N;
5. N:N e 7. n-ário: relação própria, com as chaves estrangeiras como chave primária;
6. multivalorado: relação própria; chave primária = chave da dona + valor;
8. especialização: opção 8A (a subclasse recebe a chave da superclasse);
9. união (categoria): chave substituta na categoria, estrangeira nas superclasses.

A entidade associativa (que não está no livro) vira uma relação como a do N:N, com os atributos
próprios. Atributos derivados não viram colunas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from haradaer.core.commands.edit import all_nodes
from haradaer.core.erview import (
    Generalization,
    Participation,
    attribute_owners,
    generalizations,
    participants,
)
from haradaer.core.figures.factory import KINDS
from haradaer.core.figures.types import NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.relational.names import column_name, relation_name, unique
from haradaer.core.relational.schema import Column, Derived, ForeignKey, Relation, Schema
from haradaer.core.rules.structure import NO_KEY, check_structure
from haradaer.core.rules.validation import Issue
from haradaer.i18n import _

NO_PRIMARY_KEY = "schema.no_primary_key"
MISSING_REFERENCED_KEY = "schema.missing_referenced_key"
DIRECTION_ASSUMED = "schema.direction_assumed"
SCHEMA_CODES = (NO_PRIMARY_KEY, MISSING_REFERENCED_KEY, DIRECTION_ASSUMED)

_SIMPLES = ("atr", "atrchave", "atrchaveparcial")


def _name(no: NodeFigure) -> str:
    """O nome do elemento, ou o nome padrão do tipo se estiver vazio."""
    return no.name or _(KINDS[no.tag].name)


@dataclass
class _Rel:
    name: str
    origin: Element | None
    columns: list[Column] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    _usados: set[str] = field(default_factory=set)
    # coluna -> nome do atributo de onde ela veio: a estrangeira de uma estrangeira se chama
    # `<atributo>_<RELACAO>`, sem acumular sufixos (Id_maquina_PROMPT, e não
    # Id_maquina_MAQUINA_SESSAO_PROMPT)
    bases: dict[str, str] = field(default_factory=dict)

    def add(self, nome: str, origem=None, tipo=None, anulavel=True, base=None) -> str:
        final = unique(nome or "coluna", self._usados)
        self.columns.append(Column(final, origem, tipo, anulavel))
        self.bases[final] = base or nome
        return final

    def freeze(self) -> Relation:
        """As colunas da chave primária vêm primeiro, na ordem da chave; as outras, na ordem do
        desenho."""
        por_nome = {c.name: c for c in self.columns}
        chave = [por_nome[n] for n in self.primary_key]
        resto = [c for c in self.columns if c.name not in self.primary_key]
        return Relation(
            self.name,
            tuple(chave + resto),
            tuple(self.primary_key),
            tuple(self.foreign_keys),
            self.origin,
        )


class _Mapper:
    def __init__(self, documento: Document) -> None:
        self.documento = documento
        self.nos = all_nodes(documento)
        donos = attribute_owners(documento)
        self.filhos: dict[int, list[NodeFigure]] = {}
        for no in self.nos:
            if id(no) in donos:
                self.filhos.setdefault(id(donos[id(no)]), []).append(no)
        self.participacoes = participants(documento)
        self.generalizacoes = generalizations(documento)
        self.relacoes: list[_Rel] = []
        self.nomes: set[str] = set()
        self.de: dict[int, _Rel] = {}  # elemento -> relação que o representa
        self.parciais: dict[int, list[str]] = {}  # entidade fraca -> colunas da chave parcial
        self.multivalorados: list[tuple[NodeFigure, _Rel]] = []
        self.derivados: list[Derived] = []
        self.avisos: list[Issue] = []

    # --- relações e atributos ---------------------------------------------------------------

    def new(self, nome: str, origem: Element | None) -> _Rel:
        relacao = _Rel(unique(nome or "RELACAO", self.nomes), origem)
        self.relacoes.append(relacao)
        return relacao

    def attributes(self, relacao: _Rel, dono: Element, chaves: tuple[str, ...]) -> list[str]:
        """Põe na relação os atributos simples do dono; devolve as colunas das chaves `chaves`."""
        colunas_chave: list[str] = []
        for atributo in self.filhos.get(id(dono), []):
            if atributo.tag in _SIMPLES:
                colunas = self.simple(relacao, atributo)
                if atributo.tag in chaves:
                    colunas_chave += colunas
            elif atributo.tag == "atrmulti":
                self.multivalorados.append((atributo, relacao))
            elif atributo.tag == "atrderivado":
                self.derivados.append(
                    Derived(_name(atributo), relacao.name, atributo.sql, atributo)
                )
        return colunas_chave

    def simple(self, relacao: _Rel, atributo: NodeFigure) -> list[str]:
        """Um atributo simples vira uma coluna; um composto, as colunas das suas partes."""
        partes = self.filhos.get(id(atributo), [])
        simples = [p for p in partes if p.tag in _SIMPLES]
        for parte in partes:  # multivalorado ou derivado dentro de um composto
            if parte.tag == "atrmulti":
                self.multivalorados.append((parte, relacao))
            elif parte.tag == "atrderivado":
                self.derivados.append(Derived(_name(parte), relacao.name, parte.sql, parte))
        if not simples:
            nome = column_name(_name(atributo))
            anulavel = atributo.nullable is not False
            return [relacao.add(nome, atributo, atributo.attribute_type, anulavel)]
        return [c for parte in simples for c in self.simple(relacao, parte)]

    def reference(
        self, relacao: _Rel, alvo: _Rel, anulavel: bool, origem: Element, nomes=None
    ) -> list[str] | None:
        """Chave estrangeira de `relacao` para `alvo`. `None` se o alvo não tem chave primária."""
        if not alvo.primary_key:
            self.avisos.append(Issue(MISSING_REFERENCED_KEY, origem, {"relation": alvo.name}))
            return None
        colunas = []
        for coluna in alvo.primary_key:
            tipo = next((c.sql_type for c in alvo.columns if c.name == coluna), None)
            base = alvo.bases.get(coluna, coluna)
            nome = nomes(coluna) if nomes else f"{base}_{alvo.name}"
            colunas.append(relacao.add(nome, origem, tipo, anulavel, base))
        relacao.foreign_keys.append(ForeignKey(tuple(colunas), alvo.name, tuple(alvo.primary_key)))
        return colunas

    # --- etapas ---------------------------------------------------------------------------

    def run(self) -> Schema:
        for no in self.nos:  # etapas 1 e 2 (e a associativa): uma relação por entidade
            if no.tag in ("ent", "entfraca", "entrel"):
                relacao = self.new(relation_name(_name(no)), no)
                self.de[id(no)] = relacao
                if no.tag == "entfraca":
                    self.parciais[id(no)] = self.attributes(relacao, no, ("atrchaveparcial",))
                else:
                    relacao.primary_key = self.attributes(relacao, no, ("atrchave",))
        self.union()
        identificadores = self.keys()
        self.associative()
        for no in self.nos:  # etapas 3, 4, 5 e 7
            if no.tag in ("rel", "relfraco") and id(no) not in identificadores:
                self.relationship(no)
        self.multivalued()
        return self.schema()

    def union(self) -> None:
        """Etapa 9: a categoria ganha uma chave substituta (se não tiver chave própria)."""
        for g in self.generalizacoes:
            if g.kind != "uniao":
                continue
            for categoria in g.subclasses:
                relacao = self.de.get(id(categoria))
                if relacao is None or relacao.primary_key:
                    continue
                nome = relacao.add(
                    f"Id_{column_name(_name(categoria))}", categoria, "NUMBER", False
                )
                relacao.primary_key = [nome]

    def keys(self) -> set[int]:
        """Etapas 2, 8 e 9: as chaves que vêm de outra relação, até não mudar mais.

        A subclasse recebe a chave da superclasse (opção 8A), a entidade fraca a da dona, e cada
        superclasse da união a chave da categoria. Como uma pode depender da outra (subclasse
        de uma fraca, fraca de uma subclasse), repete até tudo o que dá ter chave. Devolve os
        relacionamentos identificadores já tratados aqui.
        """
        herancas = self.inheritance()
        fracas = self.identifying()
        identificadores = {id(rel) for _f, _d, rel in fracas.values()}
        feitas: set[int] = set()
        mudou = True
        while mudou:
            mudou = False
            for subclasse, superclasse, g in herancas:
                if id(subclasse) in feitas:
                    continue
                alvo, relacao = self.de.get(id(superclasse)), self.de.get(id(subclasse))
                if alvo is None or relacao is None or not alvo.primary_key:
                    continue
                propria = bool(relacao.primary_key)
                colunas = self.reference(relacao, alvo, False, g.circle, nomes=lambda c: c)
                if colunas and not propria:
                    relacao.primary_key = colunas
                feitas.add(id(subclasse))
                mudou = True
            for chave, (_fraca, donos, rel) in fracas.items():
                alvos = [self.de.get(id(d)) for d in donos]
                if chave in feitas or any(a is None or not a.primary_key for a in alvos):
                    continue
                relacao = self.de[chave]
                estrangeiras = []
                for alvo in alvos:
                    estrangeiras += self.reference(relacao, alvo, False, rel) or []
                relacao.primary_key = estrangeiras + self.parciais.get(chave, [])
                self.attributes(relacao, rel, ())  # atributos do relacionamento identificador
                feitas.add(chave)
                mudou = True
        for g in self.generalizacoes:  # etapa 9: cada superclasse aponta para a categoria
            if g.kind != "uniao":
                continue
            for categoria in g.subclasses:
                alvo = self.de.get(id(categoria))
                for superclasse in g.superclasses:
                    relacao = self.de.get(id(superclasse))
                    if alvo is not None and relacao is not None:
                        self.reference(relacao, alvo, True, g.circle, nomes=lambda c: c)
        for g in self.generalizacoes:
            if g.assumed:
                self.avisos.append(Issue(DIRECTION_ASSUMED, g.circle, {"kind": g.kind}))
        return identificadores

    def identifying(self) -> dict[int, tuple[NodeFigure, list[NodeFigure], NodeFigure]]:
        """`id(fraca)` -> (fraca, donas, relacionamento identificador).

        Com uma só entidade fraca no relacionamento identificador, é ela. Com duas (a dona também
        é fraca, o que o livro permite), a fraca é a do lado N; no empate, a dona é a que já é
        identificada por outro relacionamento. Uma fraca ligada duas vezes à mesma dona, ou um
        empate que não se resolve, fica de fora (o relacionamento vira uma relação comum).
        """
        pendentes: list[tuple[NodeFigure, list[Participation]]] = []
        for no in self.nos:
            if no.tag == "relfraco":
                ligados = self.participacoes.get(id(no), [])
                if len({id(p.entity) for p in ligados}) >= 2:
                    pendentes.append((no, ligados))
        fracas: dict[int, tuple[NodeFigure, list[NodeFigure], NodeFigure]] = {}

        def identifica(rel, ligados, fraca):
            donas = [p.entity for p in ligados if p.entity is not fraca]
            if id(fraca) not in fracas:
                fracas[id(fraca)] = (fraca, donas, rel)

        mudou = True
        while pendentes and mudou:
            mudou = False
            for rel, ligados in list(pendentes):
                candidatas = [p for p in ligados if p.entity.tag == "entfraca"]
                if len(candidatas) > 1 and {p.cardinality for p in candidatas} == {"1", "N"}:
                    candidatas = [p for p in candidatas if p.cardinality == "N"]
                if len(candidatas) > 1:  # empate: a dona é a que já é fraca de outro
                    candidatas = [p for p in candidatas if id(p.entity) not in fracas]
                if len(candidatas) == 1:
                    identifica(rel, ligados, candidatas[0].entity)
                    pendentes.remove((rel, ligados))
                    mudou = True
        return fracas

    def inheritance(self) -> list[tuple[NodeFigure, NodeFigure, Generalization]]:
        herancas = []
        vistas: set[int] = set()
        for g in self.generalizacoes:
            if g.kind == "uniao" or not g.superclasses:
                continue
            for subclasse in g.subclasses:
                if id(subclasse) not in vistas:  # herança múltipla: vale a primeira
                    vistas.add(id(subclasse))
                    herancas.append((subclasse, g.superclasses[0], g))
        return herancas

    def associative(self) -> None:
        """Entidade associativa: chaves estrangeiras para as entidades ligadas a ela; sem chave
        própria, a chave primária são as do lado N (ou todas), como no N:N."""
        for no in self.nos:
            if no.tag != "entrel":
                continue
            relacao = self.de[id(no)]
            propria = list(relacao.primary_key)
            muitos: list[str] = []
            todas: list[str] = []
            for p in self.participacoes.get(id(no), []):
                alvo = self.de.get(id(p.entity))
                if alvo is None:
                    continue
                colunas = self.reference(relacao, alvo, False, p.connection) or []
                todas += colunas
                if p.cardinality == "N":
                    muitos += colunas
            relacao.primary_key = propria or muitos or todas

    def relationship(self, no: NodeFigure) -> None:
        ligados = self.participacoes.get(id(no), [])
        if len(ligados) < 2:
            return  # o aviso de estrutura já aponta
        alvos = [self.de.get(id(p.entity)) for p in ligados]
        if any(a is None for a in alvos):
            return
        cardinalidades = sorted(p.cardinality for p in ligados)
        if cardinalidades == ["1", "N"]:  # 1:N: do lado N
            self.foreign_key_side(no, next(p for p in ligados if p.cardinality == "N"))
            return
        if cardinalidades == ["1", "1"]:  # 1:1: do lado total; empate, o primeiro ligado
            a, b = ligados
            self.foreign_key_side(no, b if b.total and not a.total else a)
            return
        relacao = self.new(relation_name(_name(no)), no)  # N:N e n-ário
        muitos: list[str] = []
        todas: list[str] = []
        for p, alvo in zip(ligados, alvos, strict=True):
            colunas = self.reference(relacao, alvo, False, p.connection) or []
            todas += colunas
            if p.cardinality == "N":
                muitos += colunas
        relacao.primary_key = (muitos if len(ligados) > 2 else todas) or todas
        self.attributes(relacao, no, ())

    def foreign_key_side(self, no: NodeFigure, lado: Participation) -> None:
        """A chave estrangeira vai para a relação do `lado`, com os atributos do relacionamento."""
        outro = next(p for p in self.participacoes[id(no)] if p is not lado)
        relacao, alvo = self.de[id(lado.entity)], self.de[id(outro.entity)]
        self.reference(relacao, alvo, not lado.total, no)
        self.attributes(relacao, no, ())

    def multivalued(self) -> None:
        """Etapa 6: cada multivalorado vira uma relação; os de dentro dele, outras."""
        while self.multivalorados:
            atributo, dona = self.multivalorados.pop(0)
            nome = f"{dona.name}_{relation_name(_name(atributo))}"
            relacao = self.new(nome, atributo)
            colunas = self.reference(relacao, dona, False, atributo)
            if colunas is None:
                continue
            valores = self.simple(relacao, atributo)
            relacao.primary_key = colunas + valores

    def schema(self) -> Schema:
        estrutura = check_structure(self.documento)
        sem_chave = {id(a.figure) for a in estrutura if a.code == NO_KEY}
        for relacao in self.relacoes:
            if not relacao.primary_key and id(relacao.origin) not in sem_chave:
                self.avisos.append(
                    Issue(NO_PRIMARY_KEY, relacao.origin, {"relation": relacao.name})
                )
        return Schema(
            tuple(r.freeze() for r in self.relacoes),
            tuple(self.derivados),
            tuple(_sem_repetir([*estrutura, *self.avisos])),
        )


def _sem_repetir(avisos: list[Issue]) -> list[Issue]:
    """O mesmo aviso para o mesmo elemento só uma vez (um N:N ligado duas vezes à mesma
    entidade sem chave daria dois iguais)."""
    vistos: set[tuple] = set()
    unicos = []
    for aviso in avisos:
        chave = (aviso.code, id(aviso.figure), tuple(sorted(aviso.details.items())))
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(aviso)
    return unicos


def map_schema(documento: Document) -> Schema:
    """O esquema lógico relacional do desenho, refeito a cada chamada (nada é gravado)."""
    return _Mapper(documento).run()
