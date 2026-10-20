"""Copiar, colar e duplicar (RF-03).

O que é copiado vira um pedaço de arquivo no formato do TerraER (`<drawing><figures>...`), e
colar lê esse pedaço: as figuras coladas são novas, sem nada em comum com as originais. Uma
conexão só vai junto se os dois elementos que ela liga forem copiados. A área de transferência
do TerraER fica fora (QA-13).
"""

from __future__ import annotations

from haradaer.core import io
from haradaer.core.commands.edit import InsertFigure, move_command, nested_nodes
from haradaer.core.commands.history import Command, Composite
from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element

PASTE_OFFSET = 20.0  # cada colagem sai deslocada, para não cair em cima da anterior


def copy_selection(documento: Document, figuras: list[Element]) -> list[Element]:
    """As figuras que vão para a cópia, na ordem de empilhamento.

    As figuras escolhidas (menos conexões soltas) e as conexões cujas duas pontas estão entre
    os elementos escolhidos, mesmo que a conexão em si não tenha sido escolhida.
    """
    escolhidas = {id(f) for f in figuras}
    nos = {id(no) for f in figuras for no in nested_nodes(f)}
    copia = []
    for figura in documento.figures:
        if isinstance(figura, ConnectionFigure):
            inicio, fim = figura.start, figura.end
            if inicio is not None and fim is not None and {id(inicio), id(fim)} <= nos:
                copia.append(figura)
        elif id(figura) in escolhidas:
            copia.append(figura)
    return copia


def copy_text(documento: Document, figuras: list[Element]) -> str | None:
    """O texto que vai para a área de transferência, ou `None` se não houver o que copiar."""
    copia = copy_selection(documento, figuras)
    if not copia:
        return None
    pedaco = Document.new()
    pedaco.figures.extend(copia)  # o pedaço só é lido para gravar; as figuras não mudam
    return io.dumps(pedaco)


def paste_command(
    documento: Document, texto: str, dx: float, dy: float
) -> tuple[Command, list[Element]]:
    """Cola o pedaço deslocado de (dx, dy). Levanta `ArquivoInvalidoError` se o texto não servir."""
    pedaco = io.loads(texto)
    figuras = list(pedaco.figures)
    if dx or dy:
        move_command(
            pedaco, [f for f in figuras if not isinstance(f, ConnectionFigure)], dx, dy
        ).apply()
    comandos: list[Command] = [InsertFigure(documento, f) for f in figuras]
    return Composite(comandos, "Colar"), figuras


def duplicate_command(
    documento: Document, figuras: list[Element]
) -> tuple[Command, list[Element]] | None:
    """Copia e cola de uma vez, deslocado. `None` se não houver o que duplicar."""
    texto = copy_text(documento, figuras)
    if texto is None:
        return None
    comando, novas = paste_command(documento, texto, PASTE_OFFSET, PASTE_OFFSET)
    comando.label = "Duplicar"
    return comando, novas
