"""O documento: a árvore do arquivo com a lista de figuras em ordem de empilhamento."""

from __future__ import annotations

from haradaer.core.model.element import Element


class Document:
    """Raiz `<drawing>`. `figures` é a lista de `<figures>`, em ordem de empilhamento."""

    def __init__(self, root: Element):
        self.root = root

    @classmethod
    def new(cls) -> Document:
        return cls(Element("drawing", children=[Element("figures")]))

    @property
    def figures(self) -> list[Element]:
        lista = self.root.child("figures")
        assert lista is not None, "documento sem <figures>"
        return lista.children
