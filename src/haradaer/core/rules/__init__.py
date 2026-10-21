"""Matriz de validação de conexões e recomendação de conexão."""

from haradaer.core.rules.recommendation import recommend_connections, recommend_elements
from haradaer.core.rules.structure import STRUCTURE_CODES, check_structure
from haradaer.core.rules.tables import BEYOND_TERRAER, CONNECTION_RULES
from haradaer.core.rules.validation import (
    INCOMPLETE,
    INVALID_PAIR,
    Issue,
    is_valid_connection,
    validate,
)

__all__ = [
    "BEYOND_TERRAER",
    "CONNECTION_RULES",
    "INCOMPLETE",
    "INVALID_PAIR",
    "Issue",
    "STRUCTURE_CODES",
    "check_structure",
    "is_valid_connection",
    "recommend_connections",
    "recommend_elements",
    "validate",
]
