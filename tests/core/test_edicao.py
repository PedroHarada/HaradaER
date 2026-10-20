"""Comandos de edição, desfazer/refazer e elementos novos (M4)."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer, FontSpec
from haradaer.core.commands import (
    History,
    add_node_command,
    connect_command,
    move_command,
    new_node,
    remove_command,
    rename_command,
    set_attribute_type_command,
    set_generalization_label_command,
    set_nullable_command,
)
from haradaer.core.figures.factory import KINDS
from haradaer.core.geometry import connection_points, node_rect
from haradaer.core.model.document import Document
from haradaer.core.rules import validate

MEDIDOR = FixedMeasurer()


def abrir(referencia, nome):
    return io.loads((referencia / nome).read_bytes())


def por_tag(doc, tag):
    return [f for f in doc.figures if f.tag == tag]


# ------------------------------------------------------------- elementos novos


@pytest.mark.parametrize("tag", sorted(KINDS))
def test_cada_elemento_novo_grava_e_relê_sem_mudar(tag):
    doc = Document.new()
    History().execute(add_node_command(doc, new_node(tag, 30, 40, MEDIDOR)))
    texto = io.dumps(doc)
    relido = io.loads(texto)
    assert io.dumps(relido) == texto
    assert relido.figures[0].tag == tag
    assert relido.figures[0].name == KINDS[tag].name


def test_atributos_novos_tem_tipo_e_anulabilidade_validos():
    for tag, esperado in (("atr", "VARCHAR2(128)"), ("atrchave", "NUMBER")):
        no = new_node(tag, 0, 0, MEDIDOR)
        assert (no.attribute_type, no.nullable) == (esperado, False)
    assert new_node("ent", 0, 0, MEDIDOR).attribute_type is None


def test_forma_cresce_para_caber_o_nome_padrao_e_o_texto_fica_centralizado():
    no = new_node("ent", 100, 50, MEDIDOR)
    x, y, w, h = node_rect(no)
    assert (x, y, h) == (100, 50, 40)
    largura_texto, altura_texto = MEDIDOR.size("Entidade", FontSpec())
    assert w == max(80, largura_texto + 20)
    texto = no.parts[-1]
    assert float(texto.attrs["x"]) == pytest.approx(x + (w - largura_texto) / 2)
    assert float(texto.attrs["y"]) == pytest.approx(y + (h - altura_texto) / 2)


def test_entidade_associativa_tem_retangulo_e_losango():
    no = new_node("entrel", 0, 0, MEDIDOR)
    assert [p.tag for p in no.parts] == ["r", "diamond", "t"]


# ------------------------------------------------------------- geometria das conexões


def test_mover_zero_reproduz_os_pontos_do_terraer(referencia):
    """As contas em ponto flutuante diferem do Java na última casa; o resto é idêntico."""
    original = (referencia / "amostra-basica.xml").read_bytes().decode("ascii")
    doc = io.loads(original)
    referencia_doc = io.loads(original)
    History().execute(move_command(doc, por_tag(doc, "ent"), 0, 0))
    pontos = [p for f in doc.figures if f.child("points") for p in f.child("points").children]
    do_terraer = [
        p for f in referencia_doc.figures if f.child("points") for p in f.child("points").children
    ]
    assert len(pontos) == len(do_terraer) == 8
    for novo, velho in zip(pontos, do_terraer, strict=True):
        for nome in ("x", "y"):
            assert float(novo.attrs[nome]) == pytest.approx(float(velho.attrs[nome]), abs=1e-9)
        novo.attrs.update(velho.attrs)
    assert io.dumps(doc) == original


def test_mover_religa_as_conexoes_as_bordas(referencia):
    doc = abrir(referencia, "amostra-basica.xml")
    aluno = por_tag(doc, "ent")[0]
    History().execute(move_command(doc, [aluno], 0, 100))
    ligacao = next(f for f in doc.figures if f.tag == "llabelUm")
    assert node_rect(aluno)[1] == 150
    esperado = connection_points(node_rect(aluno), node_rect(ligacao.end))
    obtido = [(float(p.attrs["x"]), float(p.attrs["y"])) for p in ligacao.points]
    assert obtido == pytest.approx(list(esperado))


def test_mover_e_desfazer_volta_aos_mesmos_bytes(referencia):
    original = (referencia / "amostra-todos-os-tipos.xml").read_bytes().decode("ascii")
    doc = io.loads(original)
    historico = History()
    historico.execute(move_command(doc, list(doc.figures[:3]), 13.5, -7))
    assert io.dumps(doc) != original
    historico.undo()
    assert io.dumps(doc) == original
    historico.redo()
    assert io.dumps(doc) != original


def test_conexao_nao_e_movida_sozinha(referencia):
    doc = abrir(referencia, "amostra-basica.xml")
    antes = io.dumps(doc)
    conexoes = [f for f in doc.figures if f.tag.startswith(("llabel", "lc"))]
    History().execute(move_command(doc, conexoes, 50, 50))
    assert io.dumps(doc) == antes


# ------------------------------------------------------------- conectar


def modelo_simples():
    doc = Document.new()
    h = History()
    aluno = new_node("ent", 50, 50, MEDIDOR)
    rel = new_node("rel", 250, 40, MEDIDOR)
    h.execute(add_node_command(doc, aluno))
    h.execute(add_node_command(doc, rel))
    return doc, h, aluno, rel


def test_conectar_cria_linha_ligada_as_bordas():
    doc, h, aluno, rel = modelo_simples()
    h.execute(connect_command(doc, "llabelUm", aluno, rel))
    ligacao = doc.figures[-1]
    # como o TerraER: entidade -> relacionamento é gravado do relacionamento para a entidade
    assert (ligacao.start, ligacao.end) == (rel, aluno)
    pontos = [(float(p.attrs["x"]), float(p.attrs["y"])) for p in ligacao.points]
    assert pontos == pytest.approx(list(connection_points(node_rect(rel), node_rect(aluno))))
    assert validate(doc) == []


def test_conectar_par_invalido_e_permitido_mas_aparece_na_validacao():
    doc, h, aluno, _ = modelo_simples()
    outra = new_node("ent", 400, 50, MEDIDOR)
    h.execute(add_node_command(doc, outra))
    h.execute(connect_command(doc, "lcaf", aluno, outra))
    assert len(validate(doc)) == 1


def test_ligacao_de_atributo_e_gravada_do_atributo_para_o_dono():
    doc, h, aluno, _ = modelo_simples()
    atributo = new_node("atr", 60, 200, MEDIDOR)
    h.execute(add_node_command(doc, atributo))
    h.execute(connect_command(doc, "lcaf", aluno, atributo))  # arrastado do dono ao atributo
    ligacao = doc.figures[-1]
    assert (ligacao.start, ligacao.end) == (atributo, aluno)
    assert validate(doc) == []


def test_conectar_um_elemento_a_si_mesmo_e_recusado():
    doc, _, aluno, _ = modelo_simples()
    with pytest.raises(ValueError):
        connect_command(doc, "llabelUm", aluno, aluno)


def test_conexao_nova_tem_rotulo_de_generalizacao_padrao():
    doc, h, aluno, _ = modelo_simples()
    gen = new_node("disjuncao", 100, 200, MEDIDOR)
    h.execute(add_node_command(doc, gen))
    h.execute(connect_command(doc, "llabelGeneralizacao", gen, aluno))
    assert doc.figures[-1].generalization_label == "característica"
    h.execute(set_generalization_label_command(doc, doc.figures[-1], "exclusiva"))
    assert io.loads(io.dumps(doc)).figures[-1].generalization_label == "exclusiva"


# ------------------------------------------------------------- excluir


def test_excluir_elemento_leva_as_conexoes_e_desfazer_traz_tudo_de_volta(referencia):
    original = (referencia / "amostra-basica.xml").read_bytes().decode("ascii")
    doc = io.loads(original)
    historico = History()
    rel = por_tag(doc, "rel")[0]
    historico.execute(remove_command(doc, [rel]))
    assert por_tag(doc, "rel") == []
    assert not [f for f in doc.figures if f.tag in ("llabelUm", "llabelMuitos")]
    assert len(por_tag(doc, "lcaf")) == 2  # as ligações dos atributos ficam
    assert io.loads(io.dumps(doc))  # o arquivo continua válido
    historico.undo()
    assert io.dumps(doc) == original


def test_excluir_uma_conexao_so_tira_ela(referencia):
    doc = abrir(referencia, "amostra-basica.xml")
    ligacao = por_tag(doc, "llabelUm")[0]
    total = len(doc.figures)
    History().execute(remove_command(doc, [ligacao]))
    assert len(doc.figures) == total - 1


# ------------------------------------------------------------- renomear


def test_renomear_para_nome_longo_cresce_e_para_nome_curto_nao_encolhe():
    doc, h, aluno, rel = modelo_simples()
    h.execute(connect_command(doc, "llabelUm", aluno, rel))
    larga = node_rect(aluno)[2]
    h.execute(rename_command(doc, aluno, "Departamento de Pessoal Aposentado", MEDIDOR))
    maior = node_rect(aluno)[2]
    assert maior > larga
    assert aluno.name == "Departamento de Pessoal Aposentado"
    h.execute(rename_command(doc, aluno, "A", MEDIDOR))
    assert node_rect(aluno)[2] == maior
    assert aluno.name == "A"
    ligacao = doc.figures[-1]
    esperado = connection_points(node_rect(rel), node_rect(aluno))
    obtido = [(float(p.attrs["x"]), float(p.attrs["y"])) for p in ligacao.points]
    assert obtido == pytest.approx(list(esperado))


def test_renomear_e_desfazer():
    doc, h, aluno, _ = modelo_simples()
    antes = io.dumps(doc)
    h.execute(rename_command(doc, aluno, "Departamento de Pessoal Aposentado", MEDIDOR))
    h.undo()
    assert io.dumps(doc) == antes


def test_nome_com_caracteres_especiais_sobrevive_a_gravacao():
    doc, h, aluno, _ = modelo_simples()
    h.execute(rename_command(doc, aluno, 'Ação & "Reação" <ç> 😀', MEDIDOR))
    assert io.loads(io.dumps(doc)).figures[0].name == 'Ação & "Reação" <ç> 😀'


# ------------------------------------------------------------- tipo e anulabilidade


def test_mudar_tipo_e_anulabilidade():
    doc = Document.new()
    h = History()
    atr = new_node("atr", 0, 0, MEDIDOR)
    h.execute(add_node_command(doc, atr))
    h.execute(set_attribute_type_command(doc, atr, "NUMBER(9,2)"))
    h.execute(set_nullable_command(doc, atr, True))
    relido = io.loads(io.dumps(doc)).figures[0]
    assert (relido.attribute_type, relido.nullable) == ("NUMBER(9,2)", True)


def test_tipo_fora_dos_cinco_validos_e_recusado():
    atr = new_node("atr", 0, 0, MEDIDOR)
    with pytest.raises(ValueError):
        set_attribute_type_command(Document.new(), atr, "INTEGER")
    with pytest.raises(ValueError):
        set_attribute_type_command(Document.new(), new_node("ent", 0, 0, MEDIDOR), "DATE")


# ------------------------------------------------------------- histórico


def test_historico_desfaz_e_refaz_na_ordem():
    doc, h, aluno, rel = modelo_simples()
    assert [f.tag for f in doc.figures] == ["ent", "rel"]
    h.undo()
    assert [f.tag for f in doc.figures] == ["ent"]
    h.undo()
    assert doc.figures == []
    assert not h.can_undo
    h.redo()
    h.redo()
    assert [f.tag for f in doc.figures] == ["ent", "rel"]
    assert not h.can_redo


def test_novo_comando_apaga_o_que_havia_para_refazer():
    doc, h, *_ = modelo_simples()
    h.undo()
    assert h.can_redo
    h.execute(add_node_command(doc, new_node("atr", 0, 0, MEDIDOR)))
    assert not h.can_redo


def test_modificado_depende_do_ponto_gravado():
    doc, h, *_ = modelo_simples()
    assert h.is_dirty
    h.mark_clean()
    assert not h.is_dirty
    h.undo()
    assert h.is_dirty
    h.redo()
    assert not h.is_dirty  # voltou ao estado gravado
    h.undo()
    h.execute(add_node_command(doc, new_node("atr", 0, 0, MEDIDOR)))
    assert h.is_dirty  # mesmo tamanho de pilha, mas outro estado
    h.undo()
    assert h.is_dirty  # o estado gravado se perdeu


def test_grupo_vira_um_so_passo_de_desfazer():
    doc, h, aluno, _ = modelo_simples()
    antes = io.dumps(doc)
    h.begin_macro("Mover")
    for _ in range(20):
        h.execute(move_command(doc, [aluno], 1, 2))
    h.end_macro()
    assert node_rect(aluno)[:2] == (70, 90)
    h.undo()
    assert io.dumps(doc) == antes


def test_grupo_cancelado_nao_deixa_rastro():
    doc, h, aluno, _ = modelo_simples()
    antes = io.dumps(doc)
    h.begin_macro()
    h.execute(move_command(doc, [aluno], 10, 10))
    h.cancel_macro()
    assert io.dumps(doc) == antes
    h.undo()  # desfaz a criação do segundo elemento, não um grupo fantasma
    assert [f.tag for f in doc.figures] == ["ent"]


def test_documento_avisa_o_que_mudou():
    doc = Document.new()
    eventos = []
    doc.subscribe(lambda evento, figura: eventos.append((evento, figura.tag if figura else None)))
    h = History()
    no = new_node("ent", 0, 0, MEDIDOR)
    h.execute(add_node_command(doc, no))
    h.execute(move_command(doc, [no], 5, 5))
    h.undo()
    h.undo()
    assert eventos[0] == ("added", "ent")
    assert ("changed", "ent") in eventos
    assert eventos[-1] == ("removed", "ent")
