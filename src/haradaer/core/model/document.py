"""O documento: a árvore do arquivo com a lista de figuras em ordem de empilhamento."""

from __future__ import annotations

from collections.abc import Callable

from haradaer.core.model.element import Element

# Eventos emitidos a quem se inscreve (a interface se inscreve; o núcleo não depende dela).
ADDED = "added"
REMOVED = "removed"
CHANGED = "changed"
REORDERED = "reordered"

Listener = Callable[[str, Element | None], None]


class Document:
    """Raiz `<drawing>`. `figures` é a lista de `<figures>`, em ordem de empilhamento."""

    def __init__(self, root: Element):
        self.root = root
        self._listeners: list[Listener] = []

    @classmethod
    def new(cls) -> Document:
        return cls(Element("drawing", children=[Element("figures")]))

    @property
    def figures(self) -> list[Element]:
        lista = self.root.child("figures")
        assert lista is not None, "documento sem <figures>"
        return lista.children

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        self._listeners.remove(listener)

    def emit(self, evento: str, figura: Element | None = None) -> None:
        for listener in list(self._listeners):
            listener(evento, figura)
