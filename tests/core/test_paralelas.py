"""Várias conexões entre o mesmo par e a numeração N, M, P... das conexões "N".

Referência: `amostra-paralelas.xml` e `amostra-paralelas-dupla.xml`, gravadas pela ferramenta de
conexão do próprio TerraER (`harness/Paralelas.java`): três conexões "N" de uma entidade para
um relacionamento.
"""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer, TextOp, describe_figure
from haradaer.core.appearance.style import Style
from haradaer.core.commands import (
    History,
    add_node_command,
    change_connection_type_command,
    connect_command,
    move_command,
    new_node,
    remove_command,
)
from haradaer.core.geometry import PARALLEL_OFFSET, center, node_rect, route_ends
from haradaer.core.model.document import Document

MEDIDOR = FixedMeasurer()


def letras(doc):
    saida = []
    for figura in doc.figures:
        if figura.tag in ("llabelMuitos", "llabelDoubleMuitos", "llabelUm"):
            rotulo = [op for op in describe_figure(figura, MEDIDOR) if isinstance(op, TextOp)]
            saida.append(rotulo[0].text)
    return saida


def pontos(conexao):
    return [(float(p.attrs["x"]), float(p.attrs["y"])) for p in conexao.points]


def desvio(ponto, de, para):
    """Distância com sinal do ponto até a linha de centro a centro (positiva à esquerda)."""
    (x1, y1), (x2, y2) = center(node_rect(de)), center(node_rect(para))
    dx, dy = x2 - x1, y2 - y1
    return ((ponto[0] - x1) * -dy + (ponto[1] - y1) * dx) / (dx * dx + dy * dy) ** 0.5


def modelo():
    doc, h = Document.new(), History()
    ent = new_node("ent", 100, 300, MEDIDOR)
    rel = new_node("rel", 100, 80, MEDIDOR)
    for no in (ent, rel):
        h.execute(add_node_command(doc, no))
    return doc, h, ent, rel


# ------------------------------------------------------------- arquivos do TerraER


@pytest.mark.parametrize("nome", ["amostra-paralelas.xml", "amostra-paralelas-dupla.xml"])
def test_le_e_mostra_as_letras_gravadas_pelo_terraer(referencia, nome):
    original = (referencia / nome).read_bytes()
    doc = io.loads(original)
    assert letras(doc) == ["N", "M", "P"]
    assert io.dumps(doc).encode("ascii") == original  # dobras sem c1x/c2x continuam iguais


def test_mover_mantem_as_dobras_e_mira_as_pontas_nelas(referencia):
    doc = io.loads((referencia / "amostra-paralelas.xml").read_bytes())
    entidade = next(f for f in doc.figures if f.tag == "ent")
    segunda = [f for f in doc.figures if f.tag == "llabelMuitos"][1]
    dobras = pontos(segunda)[1:-1]
    History().execute(move_command(doc, [entidade], 30, 40))
    depois = pontos(segunda)
    assert depois[1:-1] == dobras  # as dobras ficam, como no TerraER
    inicio, fim = route_ends(node_rect(segunda.start), node_rect(segunda.end), dobras)
    assert depois[0] == pytest.approx(inicio)
    assert depois[-1] == pytest.approx(fim)


def test_mover_os_dois_elementos_leva_as_dobras_junto(referencia):
    doc = io.loads((referencia / "amostra-paralelas.xml").read_bytes())
    nos = [f for f in doc.figures if f.tag in ("ent", "rel")]
    segunda = [f for f in doc.figures if f.tag == "llabelMuitos"][1]
    antes = pontos(segunda)
    History().execute(move_command(doc, nos, 10, 20))
    assert pontos(segunda) == pytest.approx([(x + 10, y + 20) for x, y in antes])


# ------------------------------------------------------------- criar no HaradaER


def test_entidade_para_relacionamento_e_gravada_ao_contrario_como_no_terraer():
    doc, h, ent, rel = modelo()
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    conexao = doc.figures[-1]
    assert (conexao.start, conexao.end) == (rel, ent)


def test_conexoes_n_do_mesmo_relacionamento_recebem_n_m_p():
    doc, h, ent, rel = modelo()
    for _ in range(3):
        h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    assert letras(doc) == ["N", "M", "P"]
    texto = io.dumps(doc)
    assert "<string>M</string>" in texto and "<string>P</string>" in texto
    assert letras(io.loads(texto)) == ["N", "M", "P"]


def test_letras_passam_de_um_relacionamento_para_outro_sem_misturar():
    doc, h, ent, rel = modelo()
    outro = new_node("rel", 400, 80, MEDIDOR)
    h.execute(add_node_command(doc, outro))
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    h.execute(connect_command(doc, "llabelMuitos", ent, outro))
    h.execute(connect_command(doc, "llabelUm", ent, rel))
    h.execute(connect_command(doc, "llabelDoubleMuitos", ent, rel))
    assert letras(doc) == ["N", "N", "1", "M"]


def test_depois_da_sexta_volta_a_ser_n():
    doc, h, ent, rel = modelo()
    for _ in range(7):
        h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    assert letras(doc) == ["N", "M", "P", "Q", "R", "S", "N"]


def test_conexao_dupla_grava_a_letra_no_mesmo_bloco_do_fator_como_o_terraer(referencia):
    doc, h, ent, rel = modelo()
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    h.execute(connect_command(doc, "llabelDoubleMuitos", ent, rel))
    dupla = doc.figures[-1]
    blocos = dupla.children_named("a")
    assert len(blocos) == 1
    assert [e.tag for e in blocos[0].children] == ["innerStrokeWidthFactor", "text"]
    dele = io.loads((referencia / "amostra-paralelas-dupla.xml").read_bytes()).figures[-1]
    assert [[e.tag for e in b.children] for b in dele.children_named("a")] == [
        ["innerStrokeWidthFactor", "text"]
    ]


def test_desfazer_a_conexao_devolve_as_letras():
    doc, h, ent, rel = modelo()
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    antes = io.dumps(doc)
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    h.undo()
    assert io.dumps(doc) == antes


def test_excluir_nao_renumera_mas_a_proxima_conexao_sim():
    doc, h, ent, rel = modelo()
    for _ in range(3):
        h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    primeira = doc.figures[2]
    h.execute(remove_command(doc, [primeira]))
    assert letras(doc) == ["M", "P"]  # o TerraER só numera ao criar
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    assert letras(doc) == ["N", "M", "P"]


def test_mudar_o_tipo_renumera():
    doc, h, ent, rel = modelo()
    for _ in range(3):
        h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    meio = doc.figures[3]
    h.execute(change_connection_type_command(doc, meio, "llabelUm"))
    assert letras(doc) == ["N", "1", "M"]
    assert Style.of(meio).string("text") is None
    h.execute(change_connection_type_command(doc, meio, "llabelDoubleMuitos"))
    assert letras(doc) == ["N", "P", "M"]
    h.undo()
    h.undo()
    assert letras(doc) == ["N", "M", "P"]


# ------------------------------------------------------------- desvio das conexões repetidas


def test_segunda_conexao_entre_o_mesmo_par_sai_para_o_lado_sem_cruzar():
    doc, h, ent, rel = modelo()
    h.execute(connect_command(doc, "llabelUm", ent, rel))
    h.execute(connect_command(doc, "llabelMuitos", ent, rel))
    reta, desviada = doc.figures[2], doc.figures[3]
    assert len(reta.points) == 2
    caminho = pontos(desviada)
    assert len(caminho) == 4
    # as duas dobras ficam do mesmo lado, a 70 da linha reta, a 1/3 e 2/3 do caminho
    assert desvio(caminho[1], rel, ent) == pytest.approx(PARALLEL_OFFSET)
    assert desvio(caminho[2], rel, ent) == pytest.approx(PARALLEL_OFFSET)
    assert caminho[0][1] < caminho[1][1] < caminho[2][1] < caminho[3][1]  # desce sem voltar
    assert 'colinear="true" x=' in io.dumps(doc)
    dobra = desviada.child("points").children[1]
    assert "c1x" not in dobra.attrs  # como o TerraER grava as dobras


def test_conexoes_extras_alternam_de_lado_e_nao_se_sobrepoem():
    doc, h, ent, rel = modelo()
    for _ in range(5):
        h.execute(connect_command(doc, "generalizacaoLine", ent, rel))
    caminhos = [tuple(map(tuple, pontos(c))) for c in doc.figures[2:]]
    assert len(set(caminhos)) == 5
    desvios = [round(desvio(c[1], rel, ent)) for c in caminhos[1:]]
    assert desvios == [70, -70, 140, -140]


def test_conexao_em_sentido_contrario_tambem_conta_como_do_mesmo_par():
    doc, h, ent, rel = modelo()
    h.execute(connect_command(doc, "generalizacaoLine", rel, ent))
    h.execute(connect_command(doc, "generalizacaoLine", ent, rel))
    assert len(doc.figures[-1].points) == 4
