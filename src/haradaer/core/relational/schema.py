"""O esquema lógico relacional: relações, colunas, chaves e atributos derivados."""

from __future__ import annotations

from dataclasses import dataclass

from haradaer.core.model.element import Element
from haradaer.core.rules.validation import Issue


@dataclass(frozen=True)
class Column:
    """Uma coluna. O tipo SQL e a anulabilidade ficam guardados para o DDL, que virá depois."""

    name: str
    origin: Element | None = None
    sql_type: str | None = None
    nullable: bool = True


@dataclass(frozen=True)
class ForeignKey:
    columns: tuple[str, ...]
    relation: str
    referenced: tuple[str, ...]


@dataclass(frozen=True)
class Relation:
    name: str
    columns: tuple[Column, ...]
    primary_key: tuple[str, ...]
    foreign_keys: tuple[ForeignKey, ...]
    origin: Element | None = None


@dataclass(frozen=True)
class Derived:
    """Atributo derivado: não vira coluna (é calculado), mas a instrução SQL dele é guardada."""

    name: str
    owner: str
    sql: str | None
    origin: Element | None = None


@dataclass(frozen=True)
class Schema:
    relations: tuple[Relation, ...]
    derived: tuple[Derived, ...]
    issues: tuple[Issue, ...]

    def relation(self, nome: str) -> Relation:
        for relacao in self.relations:
            if relacao.name == nome:
                return relacao
        raise KeyError(nome)
