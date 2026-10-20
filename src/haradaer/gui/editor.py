"""O editor de um documento: junta o `Document`, o `History` e as operações que a tela pede.

A tela nunca altera o modelo: ela chama o editor, que monta o comando e o executa no histórico.
Depois disso o `Document` avisa o que mudou e a cena se atualiza.
"""

from __future__ import annotations

from haradaer.core.commands import (
    History,
    add_node_command,
    align_command,
    bring_to_front_command,
    connect_command,
    min_node_size,
    move_command,
    new_node,
    remove_command,
    rename_command,
    resize_command,
    send_to_back_command,
    set_generalization_label_command,
)
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import node_rect
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.gui.qt_utils import QtMeasurer


class Editor:
    def __init__(self, document: Document):
        self.document = document
        self.history = History()
        self.measurer = QtMeasurer()

    def create(self, tag: str, centro_x: float, centro_y: float) -> NodeFigure:
        """Cria um elemento com o centro no ponto dado."""
        provisorio = new_node(tag, 0, 0, self.measurer)
        rect = node_rect(provisorio)
        assert rect is not None
        no = new_node(tag, centro_x - rect[2] / 2, centro_y - rect[3] / 2, self.measurer)
        self.history.execute(add_node_command(self.document, no))
        return no

    def connect(self, tag: str, origem: Element, destino: Element) -> ConnectionFigure:
        comando = connect_command(self.document, tag, origem, destino)
        self.history.execute(comando)
        conexao = self.document.figures[-1]
        assert isinstance(conexao, ConnectionFigure)
        return conexao

    def delete(self, figuras: list[Element]) -> None:
        if figuras:
            self.history.execute(remove_command(self.document, figuras))

    def begin_move(self) -> None:
        self.history.begin_macro("Mover")

    def move(self, figuras: list[Element], dx: float, dy: float) -> None:
        self.history.execute(move_command(self.document, figuras, dx, dy))

    def end_move(self) -> None:
        self.history.end_macro()

    def min_size(self, no: NodeFigure) -> tuple[float, float]:
        return min_node_size(no, self.measurer)

    def resize(self, no: NodeFigure, rect: tuple[float, float, float, float]) -> None:
        self.history.execute(resize_command(self.document, no, rect, self.measurer))

    def align(self, figuras: list[Element], modo: str) -> None:
        comando = align_command(self.document, figuras, modo)
        if comando.commands:
            self.history.execute(comando)

    def bring_to_front(self, figuras: list[Element]) -> None:
        if figuras:
            self.history.execute(bring_to_front_command(self.document, figuras))

    def send_to_back(self, figuras: list[Element]) -> None:
        if figuras:
            self.history.execute(send_to_back_command(self.document, figuras))

    def rename(self, no: NodeFigure, nome: str) -> None:
        if nome != no.name:
            self.history.execute(rename_command(self.document, no, nome, self.measurer))

    def set_generalization_label(self, conexao: ConnectionFigure, texto: str) -> None:
        if texto != conexao.generalization_label:
            self.history.execute(set_generalization_label_command(self.document, conexao, texto))
