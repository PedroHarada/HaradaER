"""Esquema lógico relacional calculado do diagrama ER (RF-23).

Regras de Elmasri e Navathe (mapeamento ER/EER para relacional), descritas em
`docs/CONCEITOS.md`. Nada aqui é gravado no `.xml`: o esquema é sempre refeito do desenho.
"""

from haradaer.core.relational.mapping import (
    DIRECTION_ASSUMED,
    MISSING_REFERENCED_KEY,
    NO_PRIMARY_KEY,
    SCHEMA_CODES,
    map_schema,
)
from haradaer.core.relational.markdown import schema_markdown
from haradaer.core.relational.schema import Column, Derived, ForeignKey, Relation, Schema

__all__ = [
    "DIRECTION_ASSUMED",
    "MISSING_REFERENCED_KEY",
    "NO_PRIMARY_KEY",
    "SCHEMA_CODES",
    "Column",
    "Derived",
    "ForeignKey",
    "Relation",
    "Schema",
    "map_schema",
    "schema_markdown",
]
