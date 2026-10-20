"""Painel de propriedades da figura selecionada.

Nome dos elementos, tipo SQL e anulabilidade dos atributos (RF-05), tipo de uma conexão e o
rótulo das generalizações. Cada alteração vira um comando, então pode ser desfeita.
"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLabel, QLineEdit, QWidget

from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.model.element import Element
from haradaer.gui.editor import Editor
from haradaer.gui.inspector import display_name
from haradaer.gui.palette import CONNECTIONS
from haradaer.gui.verification import name_of

# (nome no TerraER, valor gravado) - REQUISITOS.md, seção 3.3.
ATTRIBUTE_TYPE_CHOICES = [
    ("CHAR", "CHAR(128)"),
    ("TEXT", "VARCHAR2(128)"),
    ("INTEGER", "NUMBER"),
    ("NUMBER", "NUMBER(9,2)"),
    ("DATE", "DATE"),
]
CONNECTION_ALIASES = {"lcf": "lcaf"}  # `lcf` é outro nome de `lcaf` no TerraER


class PropertiesPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.editor: Editor | None = None
        self._figura: Element | None = None
        self._updating = False

        self.kind = QLabel()
        self.name = QLineEdit()
        self.name.editingFinished.connect(self._name_edited)
        self.attribute_type = QComboBox()
        for nome, valor in ATTRIBUTE_TYPE_CHOICES:
            self.attribute_type.addItem(f"{nome}  ({valor})", valor)
        self.attribute_type.activated.connect(self._type_chosen)
        self.nullable = QCheckBox("Pode ser nulo")
        self.nullable.clicked.connect(self._nullable_clicked)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.connection_type = QComboBox()
        for tag, nome in CONNECTIONS:
            self.connection_type.addItem(nome, tag)
        self.connection_type.activated.connect(self._connection_type_chosen)
        self.ends = QLabel()
        self.label = QLineEdit()
        self.label.editingFinished.connect(self._label_edited)

        self.form = QFormLayout(self)
        self.form.addRow("Tipo:", self.kind)
        self.form.addRow("Nome:", self.name)
        self.form.addRow("Tipo SQL:", self.attribute_type)
        self.form.addRow("", self.nullable)
        self.form.addRow("Conexão:", self.connection_type)
        self.form.addRow("Liga:", self.ends)
        self.form.addRow("Rótulo:", self.label)
        self.form.addRow(self.note)
        self.show_figures([])

    def set_editor(self, editor: Editor) -> None:
        self.editor = editor
        self.show_figures([])

    def _row(self, campo: QWidget, visivel: bool) -> None:
        self.form.setRowVisible(campo, visivel)

    def show_figures(self, figuras: list[Element]) -> None:
        """Mostra a figura, se houver exatamente uma selecionada."""
        self._updating = True
        figura = figuras[0] if len(figuras) == 1 else None
        self._figura = figura
        no = figura if isinstance(figura, NodeFigure) else None
        conexao = figura if isinstance(figura, ConnectionFigure) else None

        self.kind.setText(name_of(figura.tag) if figura is not None else "")
        self._row(self.kind, figura is not None)
        self._row(self.name, no is not None)
        if no is not None:
            self.name.setText(no.name or "")
        tipado = no is not None and no.attribute_type is not None
        self._row(self.attribute_type, tipado)
        self._row(self.nullable, tipado)
        if tipado:
            self.attribute_type.setCurrentIndex(self.attribute_type.findData(no.attribute_type))
            self.nullable.setChecked(bool(no.nullable))

        self._row(self.connection_type, conexao is not None)
        self._row(self.ends, conexao is not None)
        if conexao is not None:
            tag = CONNECTION_ALIASES.get(conexao.tag, conexao.tag)
            self.connection_type.setCurrentIndex(self.connection_type.findData(tag))
            self.ends.setText(display_name(conexao).replace(" — ", " → "))
        com_rotulo = conexao is not None and conexao.generalization_label is not None
        self._row(self.label, com_rotulo)
        if com_rotulo:
            self.label.setText(conexao.generalization_label)

        if figura is None:
            nota = "Nada selecionado." if not figuras else f"{len(figuras)} figuras selecionadas."
        elif no is not None and no.tag == "atrderivado":
            nota = "Atributo derivado não tem tipo."
        else:
            nota = ""
        self.note.setText(nota)
        self.note.setVisible(bool(nota))
        self._updating = False

    def refresh(self) -> None:
        """Depois de desfazer, por exemplo, os valores mostrados mudam."""
        self.show_figures([self._figura] if self._figura is not None else [])

    # --- alterações --------------------------------------------------------------------------

    def _name_edited(self) -> None:
        if self._updating or self.editor is None or not isinstance(self._figura, NodeFigure):
            return
        if self.name.text() != (self._figura.name or ""):
            self.editor.rename(self._figura, self.name.text())

    def _type_chosen(self, indice: int) -> None:
        if self.editor is not None and isinstance(self._figura, NodeFigure):
            self.editor.set_attribute_type(self._figura, self.attribute_type.itemData(indice))

    def _nullable_clicked(self, marcado: bool) -> None:
        if self.editor is not None and isinstance(self._figura, NodeFigure):
            self.editor.set_nullable(self._figura, marcado)

    def _connection_type_chosen(self, indice: int) -> None:
        if self.editor is not None and isinstance(self._figura, ConnectionFigure):
            self.editor.change_connection_type(self._figura, self.connection_type.itemData(indice))

    def _label_edited(self) -> None:
        if self._updating or self.editor is None:
            return
        if isinstance(self._figura, ConnectionFigure):
            self.editor.set_generalization_label(self._figura, self.label.text())
