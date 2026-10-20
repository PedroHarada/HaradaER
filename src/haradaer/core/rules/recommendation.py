"""Recomendação de conexão (RF-10).

Usa a mesma tabela da validação. O TerraER tem uma segunda tabela para recomendar, e ela discorda
da validação em dois pontos (`docs/INVESTIGACOES.md` seção 12); aqui nunca se recomenda uma
conexão que a verificação do modelo pintaria de vermelho.
"""

from __future__ import annotations

from haradaer.core.rules.tables import CONNECTION_RULES, NODE_ORDER, RECOMMENDATION_ORDER


def recommend_connections(start_tag: str, end_tag: str) -> list[str]:
    """Tipos de conexão válidos de `start_tag` para `end_tag`, sem a conexão livre."""
    return [c for c in RECOMMENDATION_ORDER if (start_tag, end_tag) in CONNECTION_RULES[c]]


def recommend_elements(connection_tag: str) -> list[tuple[str, str]]:
    """Pares (origem, destino) em que esse tipo de conexão é válido."""
    ordem = {tag: i for i, tag in enumerate(NODE_ORDER)}
    return sorted(CONNECTION_RULES[connection_tag], key=lambda par: (ordem[par[0]], ordem[par[1]]))
