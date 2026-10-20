"""Redimensionar, alinhar e ordem de empilhamento (M5b)."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer, FontSpec
from haradaer.core.commands import (
    History,
    add_node_command,
    align_command,
    bring_to_front_command,
    connect_command,
    min_node_size,
    new_node,
    resize_command,
    send_to_back_command,
)
from haradaer.core.figures.types import NodeFigure
from haradaer.core.geometry import connection_points, node_rect
from haradaer.core.model.document import REORDERED, Document

MEDIDOR = FixedMeasurer()


def modelo(*nos):
    doc, historico = Document.new(), History()
    for no in nos:
        historico.execute(add_node_command(doc, no))
    return doc, historico


def pontos(conexao):
    return [(float(p.attrs["x"]), float(p.attrs["y"])) for p in conexao.points]


# ------------------------------------------------------------- redimensionar


def test_redimensionar_muda_a_forma_centraliza_o_texto_e_religa():
    ent, rel = new_node("ent", 50, 50, MEDIDOR), new_node("rel", 300, 40, MEDIDOR)
    doc, historico = modelo(ent, rel)
    historico.execute(connect_command(doc, "llabelUm", ent, rel))
    conexao = doc.figures[-1]
    historico.execute(resize_command(doc, ent, (40, 30, 200, 90), MEDIDOR))
    assert node_rect(ent) == (40, 30, 200, 90)
    largura, altura = MEDIDOR.size("Entidade", FontSpec())
    texto = ent.parts[-1]
    assert float(texto.attrs["x"]) == pytest.approx(40 + (200 - largura) / 2)
    assert float(texto.attrs["y"]) == pytest.approx(30 + (90 - altura) / 2)
    assert pontos(conexao) == pytest.approx(list(connection_points(node_rect(rel), node_rect(ent))))


def test_redimensionar_nao_fica_menor_que_o_texto():
    ent = new_node("ent", 0, 0, MEDIDOR)
    doc, historico = modelo(ent)
    minimo_w, minimo_h = min_node_size(ent, MEDIDOR)
    largura, altura = MEDIDOR.size("Entidade", FontSpec())
    assert (minimo_w, minimo_h) == (largura + 20, altura)
    historico.execute(resize_command(doc, ent, (0, 0, 5, 5), MEDIDOR))
    assert node_rect(ent) == (0, 0, minimo_w, minimo_h)


def test_losango_da_entidade_associativa_acompanha_a_forma():
    no = new_node("entrel", 0, 0, MEDIDOR)
    doc, historico = modelo(no)
    historico.execute(resize_command(doc, no, (10, 10, 250, 70), MEDIDOR))
    losango = no.parts[1]
    assert losango.tag == "diamond"
    assert [float(losango.attrs[n]) for n in "xywh"] == [12, 12, 246, 66]


def test_circulo_da_generalizacao_continua_redondo():
    no = new_node("uniao", 0, 0, MEDIDOR)
    doc, historico = modelo(no)
    historico.execute(resize_command(doc, no, (0, 0, 40, 25), MEDIDOR))
    _, _, w, h = node_rect(no)
    assert w == h == 40


def test_redimensionar_e_desfazer_volta_aos_mesmos_bytes(referencia):
    original = (referencia / "amostra-todos-os-tipos.xml").read_bytes().decode("ascii")
    doc = io.loads(original)
    historico = History()
    no = next(f for f in doc.figures if isinstance(f, NodeFigure) and node_rect(f))
    historico.execute(resize_command(doc, no, (0, 0, 300, 120), MEDIDOR))
    assert io.dumps(doc) != original
    historico.undo()
    assert io.dumps(doc) == original


# ------------------------------------------------------------- alinhar


def test_alinhar_a_esquerda_e_ao_meio_religa_entre_os_alinhados():
    a, b = new_node("ent", 50, 50, MEDIDOR), new_node("rel", 200, 200, MEDIDOR)
    doc, historico = modelo(a, b)
    historico.execute(connect_command(doc, "llabelUm", a, b))
    conexao = doc.figures[-1]

    historico.execute(align_command(doc, [a, b], "left"))
    assert node_rect(a)[0] == node_rect(b)[0] == 50
    assert pontos(conexao) == pytest.approx(list(connection_points(node_rect(b), node_rect(a))))

    historico.execute(align_command(doc, [a, b], "middle"))
    ra, rb = node_rect(a), node_rect(b)
    assert ra[1] + ra[3] / 2 == pytest.approx(rb[1] + rb[3] / 2)
    assert pontos(conexao) == pytest.approx(list(connection_points(rb, ra)))


@pytest.mark.parametrize(
    ("modo", "medida"),
    [
        ("right", lambda r: r[0] + r[2]),
        ("center", lambda r: r[0] + r[2] / 2),
        ("top", lambda r: r[1]),
        ("bottom", lambda r: r[1] + r[3]),
    ],
)
def test_cada_alinhamento_iguala_a_medida(modo, medida):
    nos = [new_node(t, x, y, MEDIDOR) for t, x, y in (("ent", 0, 0), ("atr", 90, 130))]
    doc, historico = modelo(*nos)
    historico.execute(align_command(doc, nos, modo))
    assert medida(node_rect(nos[0])) == pytest.approx(medida(node_rect(nos[1])))


def test_alinhar_um_elemento_so_nao_faz_nada():
    a = new_node("ent", 0, 0, MEDIDOR)
    doc, _ = modelo(a)
    assert align_command(doc, [a], "left").commands == []


# ------------------------------------------------------------- empilhamento


def test_trazer_para_a_frente_e_enviar_para_tras_mantem_a_ordem_entre_os_escolhidos():
    a, b, c, d = (new_node("ent", i * 100, 0, MEDIDOR) for i in range(4))
    doc, historico = modelo(a, b, c, d)
    eventos = []
    doc.subscribe(lambda evento, figura: eventos.append(evento))
    historico.execute(bring_to_front_command(doc, [c, a]))
    assert doc.figures == [b, d, a, c]
    historico.execute(send_to_back_command(doc, [d, c]))
    assert doc.figures == [d, c, b, a]
    assert eventos == [REORDERED, REORDERED]
    historico.undo()
    historico.undo()
    assert doc.figures == [a, b, c, d]


def test_conexao_enviada_para_tras_grava_o_dono_por_dentro_e_relê_igual():
    """No TerraER, a conexão antes do nó leva o nó inteiro dentro do `Owner`."""
    a, b = new_node("ent", 0, 0, MEDIDOR), new_node("rel", 200, 0, MEDIDOR)
    doc, historico = modelo(a, b)
    historico.execute(connect_command(doc, "llabelUm", a, b))
    historico.execute(send_to_back_command(doc, [doc.figures[-1]]))
    texto = io.dumps(doc)
    relido = io.loads(texto)
    assert [f.tag for f in relido.figures] == ["llabelUm", "ent", "rel"]
    assert relido.figures[0].start is relido.figures[2]  # gravada rel -> ent, como no TerraER
    assert relido.figures[0].end is relido.figures[1]
    assert io.dumps(relido) == texto
