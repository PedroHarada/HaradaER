"""Trocar o tipo de um elemento dentro da família (clique direito › Trocar tipo)."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import (
    History,
    add_node_command,
    change_node_type_command,
    connect_command,
    lost_on_type_change,
    new_node,
    node_type_family,
    rename_command,
)
from haradaer.core.figures.types import ConnectionFigure
from haradaer.core.geometry import node_rect
from haradaer.core.model.document import Document

MEDIDOR = FixedMeasurer()


def modelo():
    doc = Document.new()
    historico = History()
    entidade = new_node("ent", 100, 100, MEDIDOR)
    atributo = new_node("atr", 100, 20, MEDIDOR)
    for no in (entidade, atributo):
        historico.execute(add_node_command(doc, no))
    historico.execute(rename_command(doc, atributo, "matricula", MEDIDOR))
    historico.execute(connect_command(doc, "lcaf", atributo, entidade))
    return doc, historico, entidade, atributo


def test_familias():
    assert node_type_family("atr")[-1] == "atrderivado"
    assert node_type_family("relfraco") == ("rel", "relfraco")
    assert node_type_family("g") == ()


def test_atributo_vira_chave_com_o_mesmo_lugar_nome_tipo_e_ligacao():
    doc, historico, entidade, atributo = modelo()
    antes = node_rect(atributo)
    tipo = atributo.attribute_type
    historico.execute(change_node_type_command(doc, atributo, "atrchave", MEDIDOR))
    assert atributo.tag == "atrchave"
    assert atributo.name == "matricula"
    assert node_rect(atributo) == antes
    assert atributo.attribute_type == tipo
    ligacao = next(f for f in doc.figures if isinstance(f, ConnectionFigure))
    assert ligacao.start is atributo and ligacao.end is entidade


def test_desfazer_volta_ao_tipo_e_as_partes_de_antes():
    doc, historico, _, atributo = modelo()
    antes = io.dumps(doc)
    historico.execute(change_node_type_command(doc, atributo, "atrmulti", MEDIDOR))
    assert io.dumps(doc) != antes
    historico.undo()
    assert io.dumps(doc) == antes


def test_arquivo_igual_ao_de_um_elemento_criado_daquele_tipo():
    """As partes são as que o TerraER grava para o tipo novo (só o nome e o lugar mudam)."""
    doc, historico, _, atributo = modelo()
    historico.execute(change_node_type_command(doc, atributo, "atrchave", MEDIDOR))
    novo = new_node("atrchave", *node_rect(atributo)[:2], MEDIDOR)
    referencia = Document.new()
    History().execute(add_node_command(referencia, novo))
    History().execute(rename_command(referencia, novo, "matricula", MEDIDOR))
    assert [p.tag for p in atributo.parts] == [p.tag for p in novo.parts]
    io.loads(io.dumps(doc))  # relê sem erro


def test_derivado_nao_tem_tipo_e_quem_vira_derivado_perde_o_tipo():
    doc, historico, _, atributo = modelo()
    assert lost_on_type_change(atributo, "atrderivado") == ["tipo"]
    historico.execute(change_node_type_command(doc, atributo, "atrderivado", MEDIDOR))
    assert atributo.attribute_type is None and "nullable" not in atributo.attrs
    atributo.attrs["sql"] = "SELECT 1"
    assert lost_on_type_change(atributo, "atr") == ["sql"]


def test_circulo_troca_a_letra():
    doc = Document.new()
    circulo = new_node("disjuncao", 0, 0, MEDIDOR)
    History().execute(add_node_command(doc, circulo))
    History().execute(change_node_type_command(doc, circulo, "uniao", MEDIDOR))
    assert circulo.tag == "uniao" and circulo.name == "u"


def test_fora_da_familia_e_recusado():
    doc, _, entidade, _ = modelo()
    with pytest.raises(ValueError):
        change_node_type_command(doc, entidade, "rel", MEDIDOR)
