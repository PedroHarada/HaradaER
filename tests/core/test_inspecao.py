"""M5c no núcleo: mudar o tipo de uma conexão, dono dos atributos e localizar por nome."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_node_command,
    change_connection_type_command,
    connect_command,
    new_node,
    rename_command,
)
from haradaer.core.erview import attribute_owners, find_nodes
from haradaer.core.figures.factory import is_double_style_block
from haradaer.core.model.document import Document

MEDIDOR = FixedMeasurer()


def modelo():
    doc, h = Document.new(), History()
    nos = {}
    for nome, tag, x, y in (
        ("aluno", "ent", 50, 50),
        ("cursa", "rel", 300, 40),
        ("nome", "atr", 50, 200),
        ("gen", "disjuncao", 300, 200),
        ("rua", "atr", 200, 300),
    ):
        nos[nome] = new_node(tag, x, y, MEDIDOR)
        h.execute(add_node_command(doc, nos[nome]))
    return doc, h, nos


def blocos_duplos(conexao):
    return sum(1 for f in conexao.children if is_double_style_block(f))


# ------------------------------------------------------------- mudar o tipo de conexão


def test_mudar_tipo_mantem_as_pontas_e_desfaz(referencia):
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "llabelUm", nos["aluno"], nos["cursa"]))
    conexao = doc.figures[-1]
    antes = io.dumps(doc)
    h.execute(change_connection_type_command(doc, conexao, "llabelMuitos"))
    assert conexao.tag == "llabelMuitos"
    assert (conexao.start, conexao.end) == (nos["cursa"], nos["aluno"])
    assert io.loads(io.dumps(doc)).figures[-1].tag == "llabelMuitos"
    h.undo()
    assert io.dumps(doc) == antes


@pytest.mark.parametrize(
    ("de", "para", "blocos"),
    [
        ("llabelUm", "llabelDoubleUm", 1),
        ("llabelDoubleUm", "llabelUm", 0),
        ("llabelDoubleMuitos", "llabelDoubleGeneralizacao", 2),
        ("llabelDoubleGeneralizacao", "llabelDoubleUm", 1),
    ],
)
def test_blocos_das_conexoes_duplas_seguem_o_tipo(de, para, blocos):
    doc, h, nos = modelo()
    h.execute(connect_command(doc, de, nos["aluno"], nos["cursa"]))
    conexao = doc.figures[-1]
    h.execute(change_connection_type_command(doc, conexao, para))
    assert blocos_duplos(conexao) == blocos
    # igual a criar direto com o novo tipo
    doc2, h2, nos2 = modelo()
    h2.execute(connect_command(doc2, para, nos2["aluno"], nos2["cursa"]))
    assert io.dumps(doc) == io.dumps(doc2)


def test_rotulo_da_generalizacao_entra_e_sai_com_o_tipo():
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "generalizacaoLine", nos["gen"], nos["aluno"]))
    conexao = doc.figures[-1]
    assert conexao.generalization_label is None
    h.execute(change_connection_type_command(doc, conexao, "llabelGeneralizacao"))
    assert conexao.generalization_label == "característica"
    h.execute(change_connection_type_command(doc, conexao, "llabelDoubleGeneralizacao"))
    assert conexao.generalization_label == "característica"  # mantém o que havia
    h.execute(change_connection_type_command(doc, conexao, "generalizacaoLine"))
    assert "labelGeneralizacaoText" not in conexao.attrs


def test_mudar_para_ligacao_de_atributo_grava_do_atributo_para_o_dono():
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "llabel", nos["aluno"], nos["nome"]))
    conexao = doc.figures[-1]
    pontos = [(p.attrs["x"], p.attrs["y"]) for p in conexao.points]
    h.execute(change_connection_type_command(doc, conexao, "lcaf"))
    assert (conexao.start, conexao.end) == (nos["nome"], nos["aluno"])
    assert [(p.attrs["x"], p.attrs["y"]) for p in conexao.points] == pontos[::-1]
    assert io.loads(io.dumps(doc))  # o arquivo continua válido
    h.undo()
    assert (conexao.start, conexao.end) == (nos["aluno"], nos["nome"])


def test_mesmo_tipo_nao_faz_nada():
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "llabelUm", nos["aluno"], nos["cursa"]))
    assert change_connection_type_command(doc, doc.figures[-1], "llabelUm").commands == []


def test_tipo_desconhecido_e_recusado():
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "llabelUm", nos["aluno"], nos["cursa"]))
    with pytest.raises(ValueError):
        change_connection_type_command(doc, doc.figures[-1], "ent")


# ------------------------------------------------------------- donos dos atributos


def test_dono_dos_atributos_vem_das_ligacoes(referencia):
    doc = io.loads((referencia / "amostra-basica.xml").read_bytes())
    donos = attribute_owners(doc)
    atributos = [f for f in doc.figures if f.tag in ("atr", "atrchave")]
    assert {donos[id(a)].name for a in atributos} == {"Aluno"}


def test_dono_aceita_as_duas_direcoes_e_atributo_composto():
    doc, h, nos = modelo()
    h.execute(connect_command(doc, "llabel", nos["aluno"], nos["nome"]))
    h.execute(change_connection_type_command(doc, doc.figures[-1], "lcaf"))
    h.execute(connect_command(doc, "lcaf", nos["rua"], nos["nome"]))  # atributo de atributo
    donos = attribute_owners(doc)
    assert donos[id(nos["nome"])] is nos["aluno"]
    assert donos[id(nos["rua"])] is nos["nome"]
    assert id(nos["aluno"]) not in donos


def test_multivalorado_composto_e_dono_em_qualquer_direcao():
    doc, h, nos = modelo()
    telefone = new_node("atrmulti", 400, 300, MEDIDOR)
    h.execute(add_node_command(doc, telefone))
    h.execute(connect_command(doc, "lcaf", telefone, nos["aluno"]))
    h.execute(connect_command(doc, "lcaf", telefone, nos["rua"]))  # dono -> parte
    h.execute(connect_command(doc, "lcaf", nos["nome"], telefone))  # parte -> dono
    donos = attribute_owners(doc)
    assert donos[id(telefone)] is nos["aluno"]
    assert donos[id(nos["rua"])] is telefone
    assert donos[id(nos["nome"])] is telefone


def test_dono_de_aninhamento_em_tres_niveis_vem_de_cima():
    """Contato (composto) > {Telefone} (multivalorado) > DDD: a direção das linhas não importa."""
    doc, h, nos = modelo()
    telefone = new_node("atrmulti", 400, 300, MEDIDOR)
    h.execute(add_node_command(doc, telefone))
    contato, ddd = nos["nome"], nos["rua"]
    h.execute(connect_command(doc, "lcaf", ddd, telefone))  # gravada antes das de cima
    h.execute(connect_command(doc, "lcaf", contato, telefone))  # parte desenhada como "dona"
    h.execute(connect_command(doc, "lcaf", nos["aluno"], contato))
    donos = attribute_owners(doc)
    assert donos[id(contato)] is nos["aluno"]
    assert donos[id(telefone)] is contato
    assert donos[id(ddd)] is telefone


def test_chave_composta_solta_e_a_dona_das_partes():
    doc, h, nos = modelo()
    placa = new_node("atrchave", 400, 300, MEDIDOR)
    h.execute(add_node_command(doc, placa))
    h.execute(connect_command(doc, "lcaf", placa, nos["rua"]))  # chave -> parte, sem entidade
    assert attribute_owners(doc)[id(nos["rua"])] is placa


# ------------------------------------------------------------- localizar


def test_localizar_ignora_maiusculas_e_acentos():
    doc, h, nos = modelo()
    h.execute(rename_command(doc, nos["aluno"], "Matrícula do Aluno", MEDIDOR))
    assert find_nodes(doc, "matricula") == [nos["aluno"]]
    assert find_nodes(doc, "ALUNO") == [nos["aluno"]]
    assert find_nodes(doc, "zzz") == []
    assert len(find_nodes(doc, "")) == 5
