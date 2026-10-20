"""Gera `criados-no-haradaer/todos-os-tipos.xml`: os 13 elementos e as 9 conexões, criados
pelos comandos de edição do HaradaER.

Uso, a partir da raiz do projeto: `.venv/bin/python <este arquivo> saida.xml`.
"""

import sys

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_node_command,
    connect_command,
    move_command,
    new_node,
    rename_command,
    set_attribute_type_command,
    set_nullable_command,
)
from haradaer.core.figures.factory import KINDS
from haradaer.core.model.document import Document

MEDIDOR = FixedMeasurer(0.55, 1.36)

LIGACOES = [
    ("llabelUm", "ent", "rel"),
    ("llabelMuitos", "rel", "entfraca"),
    ("llabelDoubleUm", "relfraco", "entrel"),
    ("llabelDoubleMuitos", "relfraco", "ent"),
    ("llabel", "rel", "ent"),
    ("lcaf", "atr", "ent"),
    ("lcaf", "atrchave", "entfraca"),
    ("lcaf", "atrderivado", "ent"),
    ("lcaf", "atrmulti", "ent"),
    ("lcaf", "atrchaveparcial", "entfraca"),
    ("generalizacaoLine", "uniao", "ent"),
    ("llabelGeneralizacao", "disjuncao", "ent"),
    ("llabelDoubleGeneralizacao", "sobreposicao", "ent"),
]


def main(destino: str) -> None:
    doc, historico = Document.new(), History()
    nos = {}
    for i, tag in enumerate(KINDS):
        nos[tag] = new_node(tag, 60 + (i % 5) * 190, 60 + (i // 5) * 130, MEDIDOR)
        historico.execute(add_node_command(doc, nos[tag]))
    for tag, origem, destino_tag in LIGACOES:
        historico.execute(connect_command(doc, tag, nos[origem], nos[destino_tag]))
    historico.execute(rename_command(doc, nos["ent"], "Departamento de Pessoal", MEDIDOR))
    historico.execute(set_attribute_type_command(doc, nos["atr"], "NUMBER(9,2)"))
    historico.execute(set_nullable_command(doc, nos["atr"], True))
    historico.execute(move_command(doc, [nos["rel"]], 30, 25))
    io.save(doc, destino)
    print("ok", len(doc.figures))


if __name__ == "__main__":
    main(sys.argv[1])
