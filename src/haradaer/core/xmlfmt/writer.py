"""Gravação do `.xml` no formato exato do TerraER.

Reproduz o `NanoXMLDOMOutput`: uma linha, sem declaração, sem indentação, elemento vazio como
`<tag/>`, `id` sequencial em hexadecimal na ordem em que cada objeto aparece pela primeira vez, e
`ref` nas aparições seguintes do mesmo objeto.
"""

from __future__ import annotations

from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.escape import escape


class _Escritor:
    def __init__(self) -> None:
        self._ids: dict[int, str] = {}
        self._saida: list[str] = []

    def escrever(self, elemento: Element) -> None:
        if elemento.has_id:
            existente = self._ids.get(id(elemento))
            if existente is not None:
                self._saida.append(f'<{elemento.tag} ref="{existente}"/>')
                return
            novo = format(len(self._ids), "x")
            self._ids[id(elemento)] = novo
            atributos = [f'id="{novo}"']
        else:
            atributos = []
        atributos.extend(f'{nome}="{escape(valor)}"' for nome, valor in elemento.attrs.items())
        abertura = "<" + " ".join([elemento.tag, *atributos])

        if not elemento.children and elemento.text is None:
            self._saida.append(abertura + "/>")
            return
        self._saida.append(abertura + ">")
        if elemento.text is not None:
            self._saida.append(escape(elemento.text))
        for filho in elemento.children:
            self.escrever(filho)
        self._saida.append(f"</{elemento.tag}>")

    def resultado(self) -> str:
        return "".join(self._saida)


def serialize(raiz: Element) -> str:
    """Texto do arquivo (ASCII puro, sem quebra de linha final)."""
    escritor = _Escritor()
    escritor.escrever(raiz)
    return escritor.resultado()
