"""Copiar, colar e duplicar (RF-03)."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    PASTE_OFFSET,
    History,
    add_node_command,
    all_nodes,
    connect_command,
    connection_path,
    copy_selection,
    copy_text,
    duplicate_command,
    group_command,
    new_node,
    paste_command,
)
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.geometry import node_rect
from haradaer.core.model.document import Document
from haradaer.core.rules import validate


def achatado(pontos):
    """[(x, y), ...] -> [x, y, ...]: o pytest.approx (9.2+) não compara listas de pontos."""
    return [c for ponto in pontos for c in ponto]


MEDIDOR = FixedMeasurer()


def modelo():
    doc, h = Document.new(), History()
    ent = new_node("ent", 50, 300, MEDIDOR)
    rel = new_node("rel", 50, 50, MEDIDOR)
    atr = new_node("atr", 300, 400, MEDIDOR)
    for no in (ent, rel, atr):
        h.execute(add_node_command(doc, no))
    h.execute(connect_command(doc, "llabelUm", ent, rel))
    h.execute(connect_command(doc, "lcaf", atr, ent))
    return doc, h, ent, rel, atr


def test_conexao_vai_junto_so_se_as_duas_pontas_forem_copiadas():
    doc, h, ent, rel, atr = modelo()
    um, ligacao = doc.figures[3], doc.figures[4]
    assert copy_selection(doc, [ent, rel]) == [ent, rel, um]
    assert copy_selection(doc, [ent]) == [ent]
    assert copy_selection(doc, [um]) == []  # conexão sozinha não tem onde se ligar
    assert copy_selection(doc, [ent, rel, atr]) == [ent, rel, atr, um, ligacao]
    assert copy_text(doc, [um]) is None


def test_o_texto_copiado_e_um_arquivo_do_terraer_valido():
    doc, h, ent, rel, atr = modelo()
    texto = copy_text(doc, [ent, rel])
    pedaco = io.loads(texto)
    assert [f.tag for f in pedaco.figures] == ["ent", "rel", "llabelUm"]
    assert io.dumps(pedaco) == texto


def test_colar_cria_figuras_novas_deslocadas_e_ligadas_entre_si():
    doc, h, ent, rel, atr = modelo()
    texto = copy_text(doc, [ent, rel])
    antes = len(doc.figures)
    comando, novas = paste_command(doc, texto, 20, 20)
    h.execute(comando)
    assert len(doc.figures) == antes + 3
    nova_ent, nova_rel, nova_conexao = novas
    assert nova_ent is not ent and nova_ent.name == ent.name
    assert node_rect(nova_ent)[:2] == (node_rect(ent)[0] + 20, node_rect(ent)[1] + 20)
    assert (nova_conexao.start, nova_conexao.end) == (nova_rel, nova_ent)
    original = doc.figures[3]
    assert achatado(connection_path(nova_conexao)) == pytest.approx(
        achatado([(x + 20, y + 20) for x, y in connection_path(original)])
    )
    assert validate(doc) == []
    assert io.loads(io.dumps(doc))


def test_colar_nao_mexe_no_original_e_desfaz():
    doc, h, ent, rel, atr = modelo()
    antes = io.dumps(doc)
    comando, _ = paste_command(doc, copy_text(doc, [ent, rel, atr]), 20, 20)
    h.execute(comando)
    h.undo()
    assert io.dumps(doc) == antes


def test_colar_em_outro_documento():
    doc, h, ent, rel, atr = modelo()
    texto = copy_text(doc, [ent, atr])
    outro = Document.new()
    comando, novas = paste_command(outro, texto, 0, 0)
    History().execute(comando)
    assert [f.tag for f in outro.figures] == ["ent", "atr", "lcaf"]


def test_duplicar_desloca_e_mantem_os_nomes():
    doc, h, ent, rel, atr = modelo()
    comando, novas = duplicate_command(doc, [rel])
    h.execute(comando)
    assert novas[0].name == rel.name
    assert node_rect(novas[0])[0] == node_rect(rel)[0] + PASTE_OFFSET
    assert duplicate_command(doc, [doc.figures[3]]) is None


def test_copiar_um_grupo_leva_as_conexoes_dos_elementos_de_dentro():
    doc, h, ent, rel, atr = modelo()
    comando, grupo = group_command(doc, [ent, rel])
    h.execute(comando)
    texto = copy_text(doc, [grupo])
    comando, novas = paste_command(doc, texto, 30, 0)
    h.execute(comando)
    assert [f.tag for f in novas] == ["llabelUm", "g"]
    assert len(all_nodes(doc)) == 5
    assert validate(doc) == []


def test_texto_que_nao_e_do_haradaer_e_recusado():
    with pytest.raises(ArquivoInvalidoError):
        paste_command(Document.new(), "qualquer coisa", 0, 0)
