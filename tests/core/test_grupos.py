"""Agrupar e desagrupar, e elementos dentro de grupos (RF-03).

Referência: `amostra-grupo.xml`, gravada pelo TerraER (`harness/Grupo.java`): uma entidade e um
relacionamento agrupados, com conexões que continuam ligadas a eles.
"""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_node_command,
    all_nodes,
    can_group,
    connect_command,
    connection_path,
    group_command,
    move_command,
    new_node,
    remove_command,
    ungroup_command,
)
from haradaer.core.geometry import node_rect, route_ends
from haradaer.core.model.document import Document
from haradaer.core.rules import validate

MEDIDOR = FixedMeasurer()


def modelo():
    doc, h = Document.new(), History()
    ent = new_node("ent", 50, 300, MEDIDOR)
    rel = new_node("rel", 50, 50, MEDIDOR)
    fora = new_node("ent", 400, 300, MEDIDOR)
    for no in (ent, rel, fora):
        h.execute(add_node_command(doc, no))
    h.execute(connect_command(doc, "llabelUm", ent, rel))
    h.execute(connect_command(doc, "llabelMuitos", fora, rel))
    return doc, h, ent, rel, fora


def pontas_certas(conexao):
    caminho = connection_path(conexao)
    esperado = route_ends(node_rect(conexao.start), node_rect(conexao.end), caminho[1:-1])
    assert caminho[0] == pytest.approx(esperado[0])
    assert caminho[-1] == pytest.approx(esperado[1])


def test_agrupar_poe_o_grupo_no_topo_e_as_conexoes_continuam_ligadas():
    doc, h, ent, rel, fora = modelo()
    comando, grupo = group_command(doc, [rel, ent])
    h.execute(comando)
    assert [f.tag for f in doc.figures] == ["ent", "llabelUm", "llabelMuitos", "g"]
    assert grupo.child("children").children == [ent, rel]  # na ordem de empilhamento
    assert {f.name for f in all_nodes(doc)} == {"Entidade", "Relacionamento"}
    assert len(all_nodes(doc)) == 3
    assert validate(doc) == []
    texto = io.dumps(doc)
    relido = io.loads(texto)
    assert io.dumps(relido) == texto
    assert relido.figures[-1].tag == "g"
    assert relido.figures[1].start in all_nodes(relido)


def test_formato_do_grupo_igual_ao_do_terraer(referencia):
    doc = io.loads((referencia / "amostra-grupo.xml").read_bytes())
    grupo = doc.figures[-1]
    assert grupo.tag == "g" and [f.tag for f in grupo.child("children").children] == ["ent", "rel"]
    nosso, h, ent, rel, _ = modelo()
    h.execute(group_command(nosso, [ent, rel])[0])
    assert [f.tag for f in nosso.figures] == [f.tag for f in doc.figures]


def test_mover_o_grupo_leva_as_conexoes_dos_elementos_de_dentro():
    doc, h, ent, rel, fora = modelo()
    comando, grupo = group_command(doc, [ent, rel])
    h.execute(comando)
    interna, externa = doc.figures[1], doc.figures[2]
    antes = connection_path(interna)
    h.execute(move_command(doc, [grupo], 100, 40))
    assert node_rect(ent)[:2] == (50 + 100, 300 + 40)
    assert connection_path(interna) == pytest.approx([(x + 100, y + 40) for x, y in antes])
    pontas_certas(externa)


def test_mover_o_grupo_da_amostra_do_terraer_como_o_terraer(referencia):
    doc = io.loads((referencia / "amostra-grupo.xml").read_bytes())
    grupo = doc.figures[-1]
    History().execute(move_command(doc, [grupo], 100, 0))
    for conexao in doc.figures[1:3]:
        pontas_certas(conexao)


def test_desagrupar_devolve_as_figuras_ao_topo():
    doc, h, ent, rel, fora = modelo()
    comando, grupo = group_command(doc, [ent, rel])
    h.execute(comando)
    agrupado = io.dumps(doc)
    comando, membros = ungroup_command(doc, grupo)
    h.execute(comando)
    assert membros == [ent, rel]
    assert [f.tag for f in doc.figures] == ["ent", "llabelUm", "llabelMuitos", "ent", "rel"]
    h.undo()
    assert io.dumps(doc) == agrupado
    h.undo()
    assert [f.tag for f in doc.figures] == ["ent", "rel", "ent", "llabelUm", "llabelMuitos"]


def test_excluir_o_grupo_leva_as_conexoes_dos_elementos_de_dentro():
    doc, h, ent, rel, fora = modelo()
    comando, grupo = group_command(doc, [ent, rel])
    h.execute(comando)
    antes = io.dumps(doc)
    h.execute(remove_command(doc, [grupo]))
    assert [f.tag for f in doc.figures] == ["ent"]
    assert io.loads(io.dumps(doc))
    h.undo()
    assert io.dumps(doc) == antes


def test_so_agrupa_duas_ou_mais_figuras_que_nao_sejam_conexoes():
    doc, h, ent, rel, fora = modelo()
    conexao = doc.figures[-1]
    assert not can_group([ent])
    assert not can_group([ent, conexao])
    assert can_group([ent, rel, conexao])
    with pytest.raises(ValueError):
        group_command(doc, [ent, conexao])
    comando, grupo = group_command(doc, [ent, rel, conexao])
    h.execute(comando)
    assert conexao in doc.figures  # a conexão fica fora do grupo
    with pytest.raises(ValueError):
        ungroup_command(doc, ent)


def test_grupo_dentro_de_grupo():
    doc, h, ent, rel, fora = modelo()
    comando, interno = group_command(doc, [ent, rel])
    h.execute(comando)
    comando, externo = group_command(doc, [interno, fora])
    h.execute(comando)
    assert len(all_nodes(doc)) == 3
    h.execute(move_command(doc, [externo], 10, 10))
    for conexao in doc.figures[:2]:
        pontas_certas(conexao)
    texto = io.dumps(doc)
    assert io.dumps(io.loads(texto)) == texto
