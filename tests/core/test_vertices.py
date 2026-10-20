"""Editar a linha de uma conexão: vértices (dobras) e reconectar uma ponta."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_bend_command,
    add_node_command,
    connect_command,
    connection_path,
    move_bend_command,
    reconnect_command,
    remove_bend_command,
    straighten_command,
)
from haradaer.core.commands import new_node as novo
from haradaer.core.geometry import nearest_segment, node_rect, route_ends
from haradaer.core.model.document import Document
from haradaer.core.rules import validate

MEDIDOR = FixedMeasurer()


def modelo():
    doc, h = Document.new(), History()
    aluno = novo("ent", 50, 300, MEDIDOR)
    cursa = novo("rel", 50, 50, MEDIDOR)
    curso = novo("ent", 400, 300, MEDIDOR)
    for no in (aluno, cursa, curso):
        h.execute(add_node_command(doc, no))
    h.execute(connect_command(doc, "llabelUm", aluno, cursa))
    return doc, h, aluno, cursa, curso, doc.figures[-1]


def pontas_certas(conexao):
    caminho = connection_path(conexao)
    esperado = route_ends(node_rect(conexao.start), node_rect(conexao.end), caminho[1:-1])
    assert caminho[0] == pytest.approx(esperado[0])
    assert caminho[-1] == pytest.approx(esperado[1])


def test_adicionar_vertice_dobra_a_linha_e_religa_as_pontas():
    doc, h, *_, conexao = modelo()
    h.execute(add_bend_command(doc, conexao, 0, (250, 180)))
    caminho = connection_path(conexao)
    assert len(caminho) == 3 and caminho[1] == (250, 180)
    pontas_certas(conexao)
    dobra = conexao.child("points").children[1]
    assert dobra.attrs == {"colinear": "true", "x": "250", "y": "180"}  # como o TerraER grava


def test_vertices_entram_no_trecho_certo():
    doc, h, *_, conexao = modelo()
    h.execute(add_bend_command(doc, conexao, 0, (200, 100)))
    h.execute(add_bend_command(doc, conexao, 1, (220, 250)))  # entre a 1ª dobra e a ponta
    h.execute(add_bend_command(doc, conexao, 0, (150, 80)))  # antes da 1ª dobra
    assert connection_path(conexao)[1:-1] == [(150, 80), (200, 100), (220, 250)]


def test_mover_e_remover_vertice():
    doc, h, *_, conexao = modelo()
    h.execute(add_bend_command(doc, conexao, 0, (200, 100)))
    h.execute(add_bend_command(doc, conexao, 1, (220, 250)))
    h.execute(move_bend_command(doc, conexao, 0, (10, 20)))
    assert connection_path(conexao)[1:-1] == [(10, 20), (220, 250)]
    pontas_certas(conexao)
    h.execute(remove_bend_command(doc, conexao, 0))
    assert connection_path(conexao)[1:-1] == [(220, 250)]
    pontas_certas(conexao)


def test_endireitar_tira_todos_os_vertices():
    doc, h, *_, conexao = modelo()
    reta = connection_path(conexao)
    h.execute(add_bend_command(doc, conexao, 0, (200, 100)))
    h.execute(add_bend_command(doc, conexao, 0, (150, 80)))
    h.execute(straighten_command(doc, conexao))
    assert connection_path(conexao) == pytest.approx(reta)


def test_cada_edicao_se_desfaz_e_o_arquivo_volta_igual():
    doc, h, *_, conexao = modelo()
    antes = io.dumps(doc)
    h.execute(add_bend_command(doc, conexao, 0, (200, 100)))
    meio = io.dumps(doc)
    h.execute(move_bend_command(doc, conexao, 0, (90, 90)))
    h.execute(remove_bend_command(doc, conexao, 0))
    h.undo()
    h.undo()
    assert io.dumps(doc) == meio
    h.undo()
    assert io.dumps(doc) == antes


def test_vertices_gravam_e_releem():
    doc, h, *_, conexao = modelo()
    h.execute(add_bend_command(doc, conexao, 0, (200.5, 100.25)))
    texto = io.dumps(doc)
    relido = io.loads(texto)
    assert connection_path(relido.figures[-1])[1] == (200.5, 100.25)
    assert io.dumps(relido) == texto


@pytest.mark.parametrize("indice", [-1, 1])
def test_vertice_inexistente_e_recusado(indice):
    doc, h, *_, conexao = modelo()
    with pytest.raises(ValueError):
        move_bend_command(doc, conexao, indice, (0, 0))
    with pytest.raises(ValueError):
        remove_bend_command(doc, conexao, 0)
    with pytest.raises(ValueError):
        add_bend_command(doc, conexao, 2, (0, 0))


def test_trecho_mais_perto():
    caminho = [(0, 0), (100, 0), (100, 100)]
    assert nearest_segment(caminho, (50, 3)) == (0, 3)
    assert nearest_segment(caminho, (97, 60)) == (1, 3)


# ------------------------------------------------------------- reconectar ponta


def test_reconectar_a_ponta_final_a_outro_elemento():
    doc, h, aluno, cursa, curso, conexao = modelo()
    assert (conexao.start, conexao.end) == (cursa, aluno)
    antes = io.dumps(doc)
    h.execute(reconnect_command(doc, conexao, "end", curso))
    assert (conexao.start, conexao.end) == (cursa, curso)
    pontas_certas(conexao)
    relido = io.loads(io.dumps(doc))
    assert relido.figures[-1].end.tag == "ent"
    h.undo()
    assert io.dumps(doc) == antes


def test_reconectar_mantem_vertices_tipo_e_sentido():
    doc, h, aluno, cursa, curso, conexao = modelo()
    h.execute(add_bend_command(doc, conexao, 0, (200, 180)))
    h.execute(reconnect_command(doc, conexao, "start", curso))
    assert conexao.tag == "llabelUm"
    assert (conexao.start, conexao.end) == (curso, aluno)
    assert connection_path(conexao)[1] == (200, 180)
    assert len(validate(doc)) == 1  # entidade com entidade: a verificação marca


def test_reconectar_aos_dois_lados_do_mesmo_elemento_e_recusado():
    doc, h, aluno, cursa, curso, conexao = modelo()
    with pytest.raises(ValueError):
        reconnect_command(doc, conexao, "end", cursa)
    with pytest.raises(ValueError):
        reconnect_command(doc, conexao, "meio", curso)


def test_reconectar_completa_uma_conexao_solta_do_terraer(referencia):
    doc = io.loads((referencia / "amostra-conexoes-incompletas.xml").read_bytes())
    entidade = next(f for f in doc.figures if f.tag == "ent")
    solta = next(f for f in doc.figures if f.tag == "llabelUm" and f.start is None)
    outra = novo("rel", 300, 300, MEDIDOR)
    h = History()
    h.execute(add_node_command(doc, outra))
    h.execute(reconnect_command(doc, solta, "start", outra))
    h.execute(reconnect_command(doc, solta, "end", entidade))
    assert (solta.start, solta.end) == (outra, entidade)
    pontas_certas(solta)
    assert io.loads(io.dumps(doc))
