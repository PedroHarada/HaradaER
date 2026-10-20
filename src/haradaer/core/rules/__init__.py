"""Matriz de validação de conexões e recomendação de conexão."""

from haradaer.core.rules.recommendation import recommend_connections, recommend_elements
from haradaer.core.rules.tables import CONNECTION_RULES
from haradaer.core.rules.validation import (
    INCOMPLETE,
    INVALID_PAIR,
    Issue,
    is_valid_connection,
    validate,
)

__all__ = [
    "CONNECTION_RULES",
    "INCOMPLETE",
    "INVALID_PAIR",
    "Issue",
    "is_valid_connection",
    "recommend_connections",
    "recommend_elements",
    "validate",
]
