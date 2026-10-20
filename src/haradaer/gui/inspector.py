"""Inspetor de objetos (RF-16) com a busca por nome (RF-08).

Mostra os elementos do modelo em árvore: entidades, relacionamentos e generalizações, com os
atributos pendurados no dono, e as conexões. Escolher um item seleciona a figura no desenho;
o campo de busca filtra a árvore e Enter leva ao primeiro encontrado.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from haradaer.core.erview import ATTRIBUTE_TAGS, attribute_owners, normalize
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.gui.verification import name_of

CATEGORIES = [
    ("Entidades", ("ent", "entfraca", "entrel")),
    ("Relacionamentos", ("rel", "relfraco")),
    ("Generalizações", ("uniao", "disjuncao", "sobreposicao")),
    ("Atributos sem dono", tuple(sorted(ATTRIBUTE_TAGS))),
]
NO_NAME = "(sem nome)"


def display_name(figura: Element) -> str:
    if isinstance(figura, NodeFigure):
        return figura.name or NO_NAME
    if isinstance(figura, ConnectionFigure):
        inicio = display_name(figura.start) if figura.start is not None else "?"
        fim = display_name(figura.end) if figura.end is not None else "?"
        return f"{inicio} — {fim}"
    return figura.tag


class ObjectInspector(QWidget):
    selection_requested = Signal(list)  # figuras escolhidas na árvore
    locate_requested = Signal(object)  # figura a mostrar no desenho

    def __init__(self) -> None:
        super().__init__()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Localizar elemento...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        self.search.returnPressed.connect(self._locate_first)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nome", "Tipo"])
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.itemSelectionChanged.connect(self._tree_selection_changed)
        self.tree.itemActivated.connect(self._item_activated)
        self.status = QLabel()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.search)
        layout.addWidget(self.tree)
        layout.addWidget(self.status)
        self._items: dict[int, QTreeWidgetItem] = {}
        self._figures: dict[int, Element] = {}
        self._syncing = False

    # --- montagem ----------------------------------------------------------------------------

    def refresh(self, documento: Document) -> None:
        """Remonta a árvore (os diagramas de ER são pequenos)."""
        selecionadas = [self._figures[k] for k in self._selected_keys()]
        self._syncing = True
        self.tree.clear()
        self._items.clear()
        self._figures.clear()
        donos = attribute_owners(documento)
        filhos: dict[int, list[NodeFigure]] = {}
        for figura in documento.figures:
            if isinstance(figura, NodeFigure) and id(figura) in donos:
                filhos.setdefault(id(donos[id(figura)]), []).append(figura)

        nos = [f for f in documento.figures if isinstance(f, NodeFigure)]
        for titulo, tags in CATEGORIES:
            grupo = [f for f in nos if f.tag in tags and id(f) not in donos]
            if titulo == "Atributos sem dono":
                grupo = [f for f in grupo if f.tag in ATTRIBUTE_TAGS]
            self._add_category(titulo, grupo, filhos)
        # Atributos que só pendem uns dos outros (ciclo) não teriam onde aparecer.
        soltos = [f for f in nos if id(f) not in self._items]
        self._add_category("Outros", soltos, {})
        conexoes = [f for f in documento.figures if isinstance(f, ConnectionFigure)]
        self._add_category("Conexões", conexoes, {})
        self.tree.expandAll()
        self.tree.resizeColumnToContents(0)
        self._syncing = False
        self._apply_filter(self.search.text())
        self.select_figures(selecionadas)

    def _add_category(
        self, titulo: str, figuras: list, filhos: dict[int, list[NodeFigure]]
    ) -> None:
        if not figuras:
            return
        categoria = QTreeWidgetItem([titulo])
        categoria.setFlags(Qt.ItemFlag.ItemIsEnabled)
        fonte = categoria.font(0)
        fonte.setBold(True)
        categoria.setFont(0, fonte)
        self.tree.addTopLevelItem(categoria)
        for figura in figuras:
            self._add_figure(categoria, figura, filhos, set())

    def _add_figure(
        self, pai: QTreeWidgetItem, figura: Element, filhos: dict, caminho: set[int]
    ) -> None:
        item = QTreeWidgetItem([display_name(figura), name_of(figura.tag)])
        item.setData(0, Qt.ItemDataRole.UserRole, id(figura))
        pai.addChild(item)
        self._items[id(figura)] = item
        self._figures[id(figura)] = figura
        caminho = caminho | {id(figura)}
        for filho in filhos.get(id(figura), []):
            if id(filho) not in caminho:  # atributos em ciclo não penduram para sempre
                self._add_figure(item, filho, filhos, caminho)

    # --- seleção -----------------------------------------------------------------------------

    def _selected_keys(self) -> list[int]:
        chaves = (i.data(0, Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems())
        return [c for c in chaves if c is not None and c in self._figures]

    def select_figures(self, figuras: list[Element]) -> None:
        """Acompanha a seleção do desenho, sem devolvê-la ao desenho."""
        self._syncing = True
        self.tree.clearSelection()
        for figura in figuras:
            item = self._items.get(id(figura))
            if item is not None:
                item.setSelected(True)
                self.tree.scrollToItem(item)
        self._syncing = False

    def _tree_selection_changed(self) -> None:
        if not self._syncing:
            self.selection_requested.emit([self._figures[k] for k in self._selected_keys()])

    def _item_activated(self, item: QTreeWidgetItem) -> None:
        chave = item.data(0, Qt.ItemDataRole.UserRole)
        if chave in self._figures:
            self.locate_requested.emit(self._figures[chave])

    # --- busca -------------------------------------------------------------------------------

    def _apply_filter(self, texto: str) -> None:
        procurado = normalize(texto.strip())
        achados = 0
        for i in range(self.tree.topLevelItemCount()):
            achados += self._filter(self.tree.topLevelItem(i), procurado, categoria=True)
        if procurado:
            self.status.setText("Nada encontrado" if achados == 0 else f"{achados} encontrado(s)")
        else:
            self.status.setText("")

    def _filter(self, item: QTreeWidgetItem, procurado: str, *, categoria: bool = False) -> int:
        achados = sum(self._filter(item.child(i), procurado) for i in range(item.childCount()))
        proprio = not categoria and self._is_match(item, procurado)
        visivel = not procurado or proprio or achados > 0
        item.setHidden(not visivel)
        return achados + (1 if proprio and procurado else 0)

    def matches(self) -> list[Element]:
        """Figuras visíveis que casam com a busca, na ordem da árvore."""
        procurado = normalize(self.search.text().strip())
        if not procurado:
            return []
        saida = []
        for chave, item in self._items.items():
            if not item.isHidden() and self._is_match(item, procurado):
                saida.append(self._figures[chave])
        return saida

    def _is_match(self, item: QTreeWidgetItem, procurado: str) -> bool:
        """A busca acha elementos pelo nome; conexões não entram (RF-08)."""
        figura = self._figures.get(item.data(0, Qt.ItemDataRole.UserRole))
        return isinstance(figura, NodeFigure) and procurado in normalize(item.text(0))

    def _locate_first(self) -> None:
        achados = self.matches()
        if achados:
            self.locate_requested.emit(achados[0])

    def focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()
