"""Elemento genérico do arquivo do TerraER, com identidade.

O arquivo é uma árvore de elementos. Alguns têm `id` e podem ser referenciados por outros
(`<ent ref="0"/>`). Na leitura, cada referência é trocada pelo próprio objeto referenciado, de modo
que o mesmo `Element` aparece em mais de um lugar da árvore. Na gravação, a segunda aparição vira
`ref` de novo (veja `xmlfmt.writer`).
"""

from __future__ import annotations

from collections.abc import Iterator


class Element:
    """Um elemento XML.

    - `attrs` guarda os atributos como texto, na ordem do arquivo, **sem** o `id`.
    - `has_id` diz se o elemento é um objeto identificável (recebe `id` ao gravar).
    - `text` é o conteúdo de um elemento folha; `None` quando vazio ou quando há filhos.
    - `line` é a linha do arquivo de onde veio (só para mensagens de erro).
    """

    __slots__ = ("attrs", "children", "has_id", "line", "tag", "text")

    def __init__(
        self,
        tag: str,
        attrs: dict[str, str] | None = None,
        children: list[Element] | None = None,
        text: str | None = None,
        *,
        has_id: bool = False,
        line: int | None = None,
    ):
        self.tag = tag
        self.attrs: dict[str, str] = attrs if attrs is not None else {}
        self.children: list[Element] = children if children is not None else []
        self.text = text
        self.has_id = has_id
        self.line = line

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.tag} filhos={len(self.children)}>"

    def child(self, tag: str) -> Element | None:
        """Primeiro filho com essa tag, ou `None`."""
        for filho in self.children:
            if filho.tag == tag:
                return filho
        return None

    def children_named(self, tag: str) -> list[Element]:
        return [filho for filho in self.children if filho.tag == tag]

    def walk(self) -> Iterator[Element]:
        """Percorre a árvore em profundidade, visitando cada objeto uma única vez."""
        vistos: set[int] = set()
        pilha = [self]
        while pilha:
            atual = pilha.pop()
            if id(atual) in vistos:
                continue
            vistos.add(id(atual))
            yield atual
            pilha.extend(reversed(atual.children))
