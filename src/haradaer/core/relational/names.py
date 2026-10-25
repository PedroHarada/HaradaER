"""Nomes do esquema: os do TerraER (maiúsculas e `_` no lugar de espaço nas relações)."""

from __future__ import annotations


def relation_name(texto: str | None) -> str:
    return "_".join((texto or "").split()).upper()


def column_name(texto: str | None) -> str:
    return "_".join((texto or "").split())


def unique(nome: str, usados: set[str]) -> str:
    """O nome, ou `nome_2`, `nome_3`... se já estiver em uso (sem diferenciar maiúsculas)."""
    candidato, n = nome, 1
    while candidato.casefold() in usados:
        n += 1
        candidato = f"{nome}_{n}"
    usados.add(candidato.casefold())
    return candidato
