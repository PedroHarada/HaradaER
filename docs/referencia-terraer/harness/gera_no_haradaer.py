"""Gera os arquivos de `criados-no-haradaer/` pelos comandos de edição do HaradaER.

- `todos-os-tipos.xml`: os 13 elementos e as 9 conexões;
- `paralelas.xml` (com `--paralelas`): três conexões "N" e uma "1" chegando no mesmo
  relacionamento, duas delas entre o mesmo par (desvio e letras N, M, P);
- `vertices.xml` (com `--vertices`): vértices adicionados, movidos e removidos, uma linha
  endireitada e uma ponta reconectada a outro elemento;
- `todas-validas.xml` (com `--todas-validas`): uma conexão para cada par aceito da tabela de
  validação (343 trios tipo/início/fim), cada uma entre dois elementos novos (critério 4);
- `grupos.xml` (com `--grupos`): grupo com conexões, grupo dentro de grupo, figuras coladas e
  duplicadas (RF-03).

Uso, a partir da raiz do projeto:
`.venv/bin/python <este arquivo> [--paralelas | --vertices | --todas-validas | --grupos]
saida.xml`.
"""

import sys

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_bend_command,
    add_node_command,
    connect_command,
    copy_text,
    duplicate_command,
    group_command,
    move_bend_command,
    move_command,
    new_node,
    paste_command,
    reconnect_command,
    remove_bend_command,
    rename_command,
    set_attribute_type_command,
    set_nullable_command,
    straighten_command,
)
from haradaer.core.figures.factory import KINDS
from haradaer.core.model.document import Document
from haradaer.core.rules import CONNECTION_RULES

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


def todas_validas(destino: str) -> None:
    doc, historico = Document.new(), History()
    trios = sorted((tag, a, b) for tag, pares in CONNECTION_RULES.items() for a, b in pares)
    for i, (tag, inicio, fim) in enumerate(trios):
        x, y = 60 + (i % 12) * 260, 60 + (i // 12) * 200
        origem, destino_no = (
            new_node(inicio, x, y, MEDIDOR),
            new_node(fim, x + 130, y + 110, MEDIDOR),
        )
        historico.execute(add_node_command(doc, origem))
        historico.execute(add_node_command(doc, destino_no))
        historico.execute(connect_command(doc, tag, origem, destino_no))
    io.save(doc, destino)
    print("ok", len(trios), "conexões")


def grupos(destino: str) -> None:
    doc, historico = Document.new(), History()
    aluno = new_node("ent", 60, 320, MEDIDOR)
    cursa = new_node("rel", 60, 60, MEDIDOR)
    curso = new_node("ent", 420, 320, MEDIDOR)
    nome = new_node("atr", 60, 480, MEDIDOR)
    for no in (aluno, cursa, curso, nome):
        historico.execute(add_node_command(doc, no))
    historico.execute(connect_command(doc, "llabelUm", aluno, cursa))
    historico.execute(connect_command(doc, "llabelMuitos", curso, cursa))
    historico.execute(connect_command(doc, "lcaf", nome, aluno))
    comando, grupo = group_command(doc, [aluno, cursa])
    historico.execute(comando)
    comando, _externo = group_command(doc, [grupo, nome])
    historico.execute(comando)
    historico.execute(move_command(doc, [_externo], 20, 10))
    comando, _ = paste_command(doc, copy_text(doc, [curso]), 300, 0)
    historico.execute(comando)
    duplicado = duplicate_command(doc, [_externo])
    assert duplicado is not None
    historico.execute(duplicado[0])
    io.save(doc, destino)
    print("ok", len(doc.figures))


if __name__ == "__main__":
    if sys.argv[1] == "--paralelas":
        paralelas(sys.argv[2])
    elif sys.argv[1] == "--vertices":
        vertices(sys.argv[2])
    elif sys.argv[1] == "--todas-validas":
        todas_validas(sys.argv[2])
    elif sys.argv[1] == "--grupos":
        grupos(sys.argv[2])
    else:
        main(sys.argv[1])
