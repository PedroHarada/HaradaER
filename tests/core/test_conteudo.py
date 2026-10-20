"""O que as figuras lidas dizem, além de voltarem iguais."""

from haradaer.core import io
from haradaer.core.figures import ConnectionFigure, NodeFigure, SupportFigure


def _abrir(referencia, nome):
    return io.loads((referencia / nome).read_bytes())


def test_amostra_basica(referencia):
    doc = _abrir(referencia, "amostra-basica.xml")
    tags = [f.tag for f in doc.figures]
    assert tags == [
        "ent",
        "ent",
        "rel",
        "atrchave",
        "atr",
        "llabelUm",
        "llabelMuitos",
        "lcaf",
        "lcaf",
    ]
    aluno, curso, rel, chave, atr = doc.figures[:5]
    assert [aluno.name, curso.name] == ["Aluno", "Curso"]
    assert all(isinstance(f, NodeFigure) for f in doc.figures[:5])

    assert chave.attribute_type == "NUMBER"
    assert chave.nullable is False
    assert atr.attribute_type == "CHAR(128)"
    assert atr.nullable is True
    assert aluno.attribute_type is None and aluno.nullable is None

    um, muitos = doc.figures[5:7]
    assert isinstance(um, ConnectionFigure)
    assert um.start is aluno and um.end is rel
    assert muitos.start is rel and muitos.end is curso
    assert len(um.points) == 2


def test_todos_os_tipos_de_elemento(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    nos = {f.tag for f in doc.figures if isinstance(f, NodeFigure)}
    assert nos == {
        "entfraca", "relfraco", "entrel", "atrderivado", "atrmulti", "atrchaveparcial",
        "uniao", "disjuncao", "sobreposicao",
    }  # fmt: skip
    conexoes = {f.tag for f in doc.figures if isinstance(f, ConnectionFigure)}
    assert conexoes == {
        "llabelDoubleUm", "llabelDoubleMuitos", "llabel", "generalizacaoLine",
        "llabelGeneralizacao", "llabelDoubleGeneralizacao", "lcaf",
    }  # fmt: skip
    rotulos = {f.generalization_label for f in doc.figures if f.tag == "llabelGeneralizacao"}
    assert rotulos == {"characteristic"}


def test_ordem_de_empilhamento_mantem_a_identidade_dos_objetos(referencia):
    """Conexões antes dos nós: o dono vem inline na conexão e depois como `ref` no desenho."""
    doc = _abrir(referencia, "amostra-ordem-empilhamento.xml")
    assert [f.tag for f in doc.figures] == ["llabelUm", "lcaf", "ent", "rel", "atrchave"]
    um, ligacao, ent, rel, chave = doc.figures
    assert um.start is ent and um.end is rel
    assert ligacao.start is chave and ligacao.end is ent


def test_figuras_de_apoio(referencia):
    doc = _abrir(referencia, "amostra-figuras-de-apoio.xml")
    assert [f.tag for f in doc.figures] == [
        "t", "tn", "ti", "ta", "r", "e", "diamond", "circ", "l", "b", "g", "image",
    ]  # fmt: skip
    assert all(isinstance(f, SupportFigure) for f in doc.figures)
    grupo = doc.figures[10]
    assert [p.tag for p in grupo.child("children").children] == ["r", "t"]
    assert "\n" in doc.figures[11].child("imageData").text


def test_vazios(referencia):
    doc = _abrir(referencia, "amostra-vazios.xml")
    entidade, derivado_vazio, derivado_sem_sql, area = doc.figures
    assert entidade.name == ""
    assert derivado_vazio.sql == ""
    assert derivado_sem_sql.sql is None
    assert area.tag == "ta"


def test_unicode_junta_o_par_de_surrogates(referencia):
    doc = _abrir(referencia, "amostra-unicode.xml")
    nome = doc.figures[0].name
    assert nome == "ção 中 😀 a\tb & <c> \"d\" 'e'"


def test_conexoes_incompletas_tem_pontas_nulas(referencia):
    doc = _abrir(referencia, "amostra-conexoes-incompletas.xml")
    conexoes = [f for f in doc.figures if isinstance(f, ConnectionFigure)]
    assert len(conexoes) == 9
    entidade = doc.figures[0]
    pontas = [(c.start, c.end) for c in conexoes[:3]]
    assert pontas == [(None, None), (entidade, None), (entidade, entidade)]
