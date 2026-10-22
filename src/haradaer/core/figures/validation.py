"""Verificação da estrutura de um arquivo lido (RNF-14).

O TerraER recusa o arquivo inteiro quando encontra, no lugar de um objeto, uma tag que não
conhece. O HaradaER faz o mesmo, com uma mensagem que diz qual tag e onde.
"""

from __future__ import annotations

from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.figures.tags import CONTAINERS_OF_OBJECTS, KNOWN_OBJECT_TAGS
from haradaer.core.model.element import Element
from haradaer.i18n import _


def validate_structure(raiz: Element) -> None:
    if raiz.tag != "drawing":
        raise ArquivoInvalidoError(
            _("o elemento raiz deve ser <drawing>, mas é <{tag}>").format(tag=raiz.tag), raiz.line
        )
    if raiz.child("figures") is None:
        raise ArquivoInvalidoError(_("o desenho não tem o elemento <figures>"), raiz.line)

    for elemento in raiz.walk():
        if elemento.tag not in CONTAINERS_OF_OBJECTS:
            continue
        for filho in elemento.children:
            if filho.tag not in KNOWN_OBJECT_TAGS:
                raise ArquivoInvalidoError(
                    _(
                        "tag desconhecida <{tag}> dentro de <{pai}>: "
                        "o TerraER também não abre arquivos com essa tag"
                    ).format(tag=filho.tag, pai=elemento.tag),
                    filho.line,
                )
