"""Painel Esquema lógico (RF-23): o esquema relacional do diagrama, refeito a cada mudança.

O mesmo texto vai para `<modelo>.esquema.md` ao salvar, se Arquivo › Gravar esquema lógico ao
salvar estiver ligado. Nada disso entra no `.xml`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from haradaer.core.model.document import Document
from haradaer.core.relational import (
    DIRECTION_ASSUMED,
    MISSING_REFERENCED_KEY,
    NO_PRIMARY_KEY,
    map_schema,
    schema_markdown,
)
from haradaer.core.rules import Issue
from haradaer.gui.inspector import display_name
from haradaer.gui.verification import message_text
from haradaer.i18n import N_, _

UNTITLED_MODEL = N_("Sem título")

_AVISOS_DO_ESQUEMA = {
    NO_PRIMARY_KEY: N_("a relação {relation} ficou sem chave primária"),
    MISSING_REFERENCED_KEY: N_(
        "a chave estrangeira para {relation} ficou de fora: {relation} não tem chave primária"
    ),
    DIRECTION_ASSUMED: N_(
        "na generalização, a superclasse foi deduzida (ligue a superclasse com uma linha de "
        "participação e as subclasses com a generalização simples)"
    ),
}


def describe(issue: Issue) -> str:
    """O aviso em palavras, com o elemento na frente."""
    modelo = _AVISOS_DO_ESQUEMA.get(issue.code)
    texto = _(modelo).format(**issue.details) if modelo else message_text(issue)
    return f"{display_name(issue.figure)}: {texto}"


def schema_file(caminho: Path) -> Path:
    """`modelo.xml` -> `modelo.esquema.md`, na mesma pasta."""
    return caminho.with_name(f"{caminho.stem}.esquema.md")


def schema_text(documento: Document, caminho: Path | None, agora: datetime | None = None) -> str:
    agora = agora or datetime.now()
    nome = caminho.stem if caminho else _(UNTITLED_MODEL)
    return schema_markdown(
        map_schema(documento),
        nome,
        caminho.name if caminho else None,
        agora.strftime("%Y-%m-%d %H:%M"),
        describe,
    )


def write_schema_file(documento: Document, caminho: Path) -> Path:
    """Grava o esquema ao lado do modelo, em UTF-8. Lança `OSError` se não conseguir."""
    destino = schema_file(caminho)
    destino.write_text(schema_text(documento, caminho), encoding="utf-8")
    return destino


class SchemaPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.text.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.copy_button = QPushButton(_("&Copiar"))
        self.copy_button.clicked.connect(self.copy)
        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(self.copy_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.text)
        layout.addLayout(botoes)

    def show_schema(self, documento: Document, caminho: Path | None) -> None:
        barra = self.text.verticalScrollBar()
        posicao = barra.value()  # o texto é refeito a cada mudança: a rolagem fica onde estava
        self.text.setPlainText(schema_text(documento, caminho))
        barra.setValue(posicao)

    def copy(self) -> None:
        QApplication.clipboard().setText(self.text.toPlainText())
