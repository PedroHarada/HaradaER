"""Sem conexão livre (RF-25): o HaradaER não a cria e a apaga ao abrir e ao colar."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_node_command,
    change_connection_type_command,
    connect_command,
    copy_text,
    paste_command,
    remove_free_connections,
)
from haradaer.core.figures.factory import create_connection, create_node
from haradaer.core.geometry import node_rect
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element

MEDIDOR = FixedMeasurer()


def modelo():
    doc, h = Document.new(), History()
    aluno = create_node("ent", 0, 0, MEDIDOR, "Aluno")
    curso = create_node("ent", 200, 0, MEDIDOR, "Curso")
    for no in (aluno, curso):
        h.execute(add_node_command(doc, no))
    return doc, h, aluno, curso


def livre(origem, destino):
    """Uma conexão livre como a que vem de um arquivo (os comandos não a criam mais)."""
    return create_connection("llabel", origem, destino, node_rect(origem), node_rect(destino), [])


def tags(doc):
    return [f.tag for f in doc.figures]


def test_nao_cria_nem_muda_para_conexao_livre():
    doc, h, aluno, curso = modelo()
    with pytest.raises(ValueError):
        connect_command(doc, "llabel", aluno, curso)
    h.execute(connect_command(doc, "generalizacaoLine", aluno, curso))
    with pytest.raises(ValueError):
        change_connection_type_command(doc, doc.figures[-1], "llabel")


def test_apaga_e_devolve_as_pontas():
    doc, _h, aluno, curso = modelo()
    doc.figures.append(livre(aluno, curso))
    assert remove_free_connections(doc) == [(aluno, curso)]
    assert tags(doc) == ["ent", "ent"]
    assert "llabel" not in io.dumps(doc)


def test_apaga_dentro_de_grupo():
    doc, _h, aluno, curso = modelo()
    grupo = Element("g", children=[Element("children", children=[livre(aluno, curso)])])
    doc.figures.append(grupo)
    assert remove_free_connections(doc) == [(aluno, curso)]
    assert grupo.child("children").children == []


def test_sem_conexao_livre_nada_muda():
    doc, _h, _aluno, _curso = modelo()
    antes = io.dumps(doc)
    assert remove_free_connections(doc) == []
    assert io.dumps(doc) == antes


def test_amostra_do_terraer(referencia):
    doc = io.loads((referencia / "amostra-todos-os-tipos.xml").read_bytes())
    pontas = remove_free_connections(doc)
    assert [(a.tag, b.tag) for a, b in pontas] == [("entrel", "entfraca")]
    assert "<llabel " not in io.dumps(doc)
    assert io.loads(io.dumps(doc))  # o arquivo continua válido


def test_pontas_soltas(referencia):
    doc = io.loads((referencia / "amostra-conexoes-incompletas.xml").read_bytes())
    pontas = [(a.tag if a else None, b.tag if b else None) for a, b in remove_free_connections(doc)]
    assert (None, None) in pontas and ("ent", None) in pontas
    assert "<llabel " not in io.dumps(doc)


def test_colar_descarta_a_conexao_livre():
    doc, h, aluno, curso = modelo()
    pedaco = Document.new()
    pedaco.figures.extend([aluno, curso, livre(aluno, curso)])
    texto = io.dumps(pedaco)
    assert "<llabel " in texto
    comando, novas = paste_command(doc, texto, 20, 20)
    h.execute(comando)
    assert [f.tag for f in novas] == ["ent", "ent"]
    assert "llabel" not in io.dumps(doc)
    assert copy_text(doc, list(doc.figures))  # a cópia segue funcionando


def test_marcar_modificado_sem_passo_de_desfazer():
    h = History()
    h.mark_dirty()
    assert h.is_dirty and not h.can_undo
    h.mark_clean()
    assert not h.is_dirty
