"""Tipos de figura: elementos do arquivo com acessores para o que o programa precisa ler.

São subclasses de `Element`, então continuam sendo a própria árvore do arquivo; as propriedades
só olham para ela. Nada aqui altera o arquivo.
"""

from __future__ import annotations

from haradaer.core.figures.tags import (
    CONNECTION_TAGS,
    NODE_TAGS,
    SUPPORT_TAGS,
    TEXT_PART_TAGS,
    TYPED_ATTRIBUTE_TAGS,
)
from haradaer.core.model.element import Element


def style_text(parte: Element) -> str | None:
    """Texto gravado no estilo (`<a><text><string>..`) de uma parte, ou `None` se não houver."""
    for estilo in parte.children_named("a"):
        entrada = estilo.child("text")
        valor = entrada.child("string") if entrada else None
        if valor is not None:
            return valor.text or ""
    return None


class Figure(Element):
    __slots__ = ()


class NodeFigure(Figure):
    """Elemento do modelo ER: entidade, relacionamento, atributo ou generalização."""

    __slots__ = ()

    @property
    def parts(self) -> list[Element]:
        grupo = self.child("children")
        return list(grupo.children) if grupo else []

    @property
    def name(self) -> str | None:
        """Nome do elemento: o texto da primeira parte de texto."""
        for parte in self.parts:
            if parte.tag in TEXT_PART_TAGS:
                return style_text(parte)
        return None

    @property
    def attribute_type(self) -> str | None:
        """Tipo SQL gravado (`CHAR(128)`, `NUMBER`, ...) nos atributos que têm tipo."""
        return self.attrs.get("attributeType") if self.tag in TYPED_ATTRIBUTE_TAGS else None

    @property
    def nullable(self) -> bool | None:
        if self.tag not in TYPED_ATTRIBUTE_TAGS:
            return None
        return self.attrs.get("nullable") == "true"

    @property
    def sql(self) -> str | None:
        """Instrução SQL do atributo derivado."""
        return self.attrs.get("sql") if self.tag == "atrderivado" else None


class ConnectionFigure(Figure):
    """Linha entre dois elementos."""

    __slots__ = ()

    @property
    def points(self) -> list[Element]:
        pontos = self.child("points")
        return list(pontos.children) if pontos else []

    def _owner(self, nome: str) -> Element | None:
        envoltorio = self.child(nome)
        conector = envoltorio.children[0] if envoltorio and envoltorio.children else None
        dono = conector.child("Owner") if conector else None
        return dono.children[0] if dono and dono.children else None

    @property
    def start(self) -> Element | None:
        return self._owner("startConnector")

    @property
    def end(self) -> Element | None:
        return self._owner("endConnector")

    @property
    def generalization_label(self) -> str | None:
        return self.attrs.get("labelGeneralizacaoText")


class SupportFigure(Figure):
    """Texto, forma, linha, imagem ou grupo.

    Aparece como parte de um elemento ER (o retângulo e o texto de uma entidade) ou solto no
    desenho (anotações). Fora do ER, é preservado e regravado sem alteração (RF-12).
    """

    __slots__ = ()


def class_for_tag(tag: str) -> type[Element]:
    if tag in NODE_TAGS:
        return NodeFigure
    if tag in CONNECTION_TAGS:
        return ConnectionFigure
    if tag in SUPPORT_TAGS:
        return SupportFigure
    return Element
