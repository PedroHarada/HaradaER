"""Gera os arquivos de `criados-no-haradaer/` pelos comandos de edição do HaradaER.

- `todos-os-tipos.xml`: os 13 elementos e as 9 conexões;
- `paralelas.xml` (com `--paralelas`): três conexões "N" e uma "1" chegando no mesmo
  relacionamento, duas delas entre o mesmo par (desvio e letras N, M, P);
- `vertices.xml` (com `--vertices`): vértices adicionados, movidos e removidos, uma linha
  endireitada e uma ponta reconectada a outro elemento.

Uso, a partir da raiz do projeto:
`.venv/bin/python <este arquivo> [--paralelas | --vertices] saida.xml`.
"""

import sys

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_bend_command,
    add_node_command,
    connect_command,
    move_bend_command,
    move_command,
    new_node,
    reconnect_command,
    remove_bend_command,
    rename_command,
    set_attribute_type_command,
    set_nullable_command,
    straighten_command,
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


def paralelas(destino: str) -> None:
    doc, historico = Document.new(), History()
    prompt = new_node("ent", 100, 320, MEDIDOR)
    melhoria = new_node("rel", 90, 60, MEDIDOR)
    fraca = new_node("entfraca", 400, 320, MEDIDOR)
    for no in (prompt, melhoria, fraca):
        historico.execute(add_node_command(doc, no))
    historico.execute(rename_command(doc, prompt, "Prompt", MEDIDOR))
    historico.execute(rename_command(doc, melhoria, "Melhoria", MEDIDOR))
    for tag in ("llabelMuitos", "llabelDoubleMuitos", "llabelMuitos"):
        historico.execute(connect_command(doc, tag, prompt, melhoria))
    historico.execute(connect_command(doc, "llabelUm", fraca, melhoria))
    io.save(doc, destino)
    print("ok", len(doc.figures))


def vertices(destino: str) -> None:
    doc, historico = Document.new(), History()
    entidade = new_node("ent", 60, 320, MEDIDOR)
    relacao = new_node("rel", 300, 60, MEDIDOR)
    outra = new_node("ent", 520, 320, MEDIDOR)
    atributo = new_node("atr", 60, 520, MEDIDOR)
    for no in (entidade, relacao, outra, atributo):
        historico.execute(add_node_command(doc, no))
    historico.execute(connect_command(doc, "llabelMuitos", entidade, relacao))
    em_l = doc.figures[-1]
    historico.execute(add_bend_command(doc, em_l, 0, (100, 100)))
    historico.execute(add_bend_command(doc, em_l, 0, (300, 30)))
    historico.execute(move_bend_command(doc, em_l, 0, (340, 20)))
    historico.execute(add_bend_command(doc, em_l, 2, (90, 200)))
    historico.execute(remove_bend_command(doc, em_l, 2))
    historico.execute(connect_command(doc, "llabelUm", outra, relacao))
    reta = doc.figures[-1]
    historico.execute(add_bend_command(doc, reta, 0, (600, 100)))
    historico.execute(straighten_command(doc, reta))
    historico.execute(connect_command(doc, "lcaf", atributo, entidade))
    ligacao = doc.figures[-1]
    historico.execute(add_bend_command(doc, ligacao, 0, (300, 450)))
    historico.execute(reconnect_command(doc, ligacao, "end", outra))
    io.save(doc, destino)
    print("ok", len(doc.figures))


if __name__ == "__main__":
    if sys.argv[1] == "--paralelas":
        paralelas(sys.argv[2])
    elif sys.argv[1] == "--vertices":
        vertices(sys.argv[2])
    else:
        main(sys.argv[1])
