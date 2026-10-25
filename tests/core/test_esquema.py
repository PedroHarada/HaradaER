"""Esquema lógico relacional (RF-23): o mapeamento ER/EER de Elmasri e Navathe, regra a regra."""

from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import History, add_node_command, connect_command
from haradaer.core.erview import generalizations, participants
from haradaer.core.figures.factory import create_node
from haradaer.core.model.document import Document
from haradaer.core.relational import (
    DIRECTION_ASSUMED,
    MISSING_REFERENCED_KEY,
    map_schema,
    schema_markdown,
)
from haradaer.core.relational.markdown import relation_line
from haradaer.core.rules.structure import NO_KEY

MEDIDOR = FixedMeasurer()


class Modelo:
    def __init__(self):
        self.doc, self.h = Document.new(), History()

    def no(self, tag, nome):
        figura = create_node(tag, 10 * len(self.doc.figures), 10, MEDIDOR, nome)
        self.h.execute(add_node_command(self.doc, figura))
        return figura

    def liga(self, tipo, a, b):
        self.h.execute(connect_command(self.doc, tipo, a, b))

    def atr(self, dono, nome, tag="atr"):
        atributo = self.no(tag, nome)
        self.liga("lcaf", atributo, dono)
        return atributo

    def entidade(self, nome, chave="id", tag="ent"):
        entidade = self.no(tag, nome)
        if chave:
            self.atr(entidade, chave, "atrchaveparcial" if tag == "entfraca" else "atrchave")
        return entidade

    def esquema(self):
        return map_schema(self.doc)

    def linhas(self):
        esquema = self.esquema()
        return {r.name: relation_line(r) for r in esquema.relations}

    def estrangeiras(self, relacao):
        return [
            (fk.columns, fk.relation, fk.referenced)
            for fk in self.esquema().relation(relacao).foreign_keys
        ]


def test_entidade_regular_com_atributo_composto():
    m = Modelo()
    aluno = m.entidade("Aluno", "mat")
    nome = m.atr(aluno, "Nome completo")
    m.atr(nome, "Prenome")
    m.atr(nome, "Sobrenome")
    assert m.linhas() == {"ALUNO": "ALUNO (**mat**, Prenome, Sobrenome)"}


def test_chave_composta():
    m = Modelo()
    carro = m.entidade("Carro", chave=None)
    registro = m.atr(carro, "Registro", "atrchave")
    m.atr(registro, "Estado")
    m.atr(registro, "Numero")
    assert m.linhas()["CARRO"] == "CARRO (**Estado**, **Numero**)"


def test_entidade_fraca():
    m = Modelo()
    func = m.entidade("Funcionario", "cpf")
    dep = m.entidade("Dependente", "nome", tag="entfraca")
    m.atr(dep, "parentesco")
    rel = m.no("relfraco", "Dependentes de")
    m.liga("llabelUm", func, rel)
    m.liga("llabelDoubleMuitos", dep, rel)
    assert m.linhas()["DEPENDENTE"] == "DEPENDENTE (**cpf_FUNCIONARIO**, **nome**, parentesco)"
    assert m.estrangeiras("DEPENDENTE") == [(("cpf_FUNCIONARIO",), "FUNCIONARIO", ("cpf",))]
    assert "DEPENDENTES_DE" not in m.linhas()  # o identificador não vira relação


def test_um_para_um_vai_para_o_lado_total():
    m = Modelo()
    func = m.entidade("Funcionario", "cpf")
    dep = m.entidade("Departamento", "num")
    rel = m.no("rel", "Gerencia")
    m.atr(rel, "inicio")
    m.liga("llabelUm", func, rel)
    m.liga("llabelDoubleUm", dep, rel)
    assert m.linhas()["DEPARTAMENTO"] == "DEPARTAMENTO (**num**, cpf_FUNCIONARIO, inicio)"
    assert m.linhas()["FUNCIONARIO"] == "FUNCIONARIO (**cpf**)"


def test_um_para_um_sem_total_vai_para_o_primeiro_ligado():
    m = Modelo()
    a = m.entidade("A", "ida")
    b = m.entidade("B", "idb")
    rel = m.no("rel", "R")
    m.liga("llabelUm", a, rel)
    m.liga("llabelUm", b, rel)
    assert m.estrangeiras("A") == [(("idb_B",), "B", ("idb",))]
    assert m.estrangeiras("B") == []


def test_um_para_muitos_vai_para_o_lado_n():
    m = Modelo()
    dep = m.entidade("Departamento", "num")
    func = m.entidade("Funcionario", "cpf")
    rel = m.no("rel", "Trabalha para")
    m.liga("llabelUm", dep, rel)
    m.liga("llabelMuitos", func, rel)
    assert m.estrangeiras("FUNCIONARIO") == [(("num_DEPARTAMENTO",), "DEPARTAMENTO", ("num",))]
    coluna = next(
        c for c in m.esquema().relation("FUNCIONARIO").columns if c.name.startswith("num")
    )
    assert coluna.nullable  # participação parcial do lado N


def test_muitos_para_muitos_com_atributo():
    m = Modelo()
    func = m.entidade("Funcionario", "cpf")
    proj = m.entidade("Projeto", "num")
    rel = m.no("rel", "Trabalha em")
    m.atr(rel, "horas")
    m.liga("llabelMuitos", func, rel)
    m.liga("llabelMuitos", proj, rel)
    assert m.linhas()["TRABALHA_EM"] == (
        "TRABALHA_EM (**cpf_FUNCIONARIO**, **num_PROJETO**, horas)"
    )


def test_n_ario_tira_da_chave_o_lado_1():
    m = Modelo()
    forn = m.entidade("Fornecedor", "fnome")
    peca = m.entidade("Peca", "num")
    proj = m.entidade("Projeto", "pnome")
    rel = m.no("rel", "Fornecimento")
    m.liga("llabelMuitos", forn, rel)
    m.liga("llabelMuitos", peca, rel)
    m.liga("llabelUm", proj, rel)
    assert m.esquema().relation("FORNECIMENTO").primary_key == ("fnome_FORNECEDOR", "num_PECA")


def test_recursivo_numera_a_segunda_coluna():
    m = Modelo()
    func = m.entidade("Funcionario", "cpf")
    rel = m.no("rel", "Supervisao")
    m.liga("llabelMuitos", func, rel)
    m.liga("llabelMuitos", func, rel)
    assert m.linhas()["SUPERVISAO"] == ("SUPERVISAO (**cpf_FUNCIONARIO**, **cpf_FUNCIONARIO_2**)")


def test_multivalorado_e_multivalorado_composto():
    m = Modelo()
    dep = m.entidade("Departamento", "num")
    m.atr(dep, "Localizacoes", "atrmulti")
    fones = m.atr(dep, "Telefones", "atrmulti")
    m.atr(fones, "ddd")
    m.atr(fones, "numero")
    linhas = m.linhas()
    assert linhas["DEPARTAMENTO"] == "DEPARTAMENTO (**num**)"
    assert linhas["DEPARTAMENTO_LOCALIZACOES"] == (
        "DEPARTAMENTO_LOCALIZACOES (**num_DEPARTAMENTO**, **Localizacoes**)"
    )
    assert linhas["DEPARTAMENTO_TELEFONES"] == (
        "DEPARTAMENTO_TELEFONES (**num_DEPARTAMENTO**, **ddd**, **numero**)"
    )


def test_derivado_nao_vira_coluna():
    m = Modelo()
    dep = m.entidade("Departamento", "num")
    com_sql = m.atr(dep, "Total", "atrderivado")
    com_sql.attrs["sql"] = "SELECT COUNT(*) FROM FUNCIONARIO"
    m.atr(dep, "Idade", "atrderivado")
    esquema = m.esquema()
    assert relation_line(esquema.relation("DEPARTAMENTO")) == "DEPARTAMENTO (**num**)"
    assert [(d.name, d.owner, d.sql) for d in esquema.derived] == [
        ("Total", "DEPARTAMENTO", "SELECT COUNT(*) FROM FUNCIONARIO"),
        ("Idade", "DEPARTAMENTO", None),
    ]


def test_entidade_associativa():
    m = Modelo()
    aluno = m.entidade("Aluno", "mat")
    disc = m.entidade("Disciplina", "cod")
    matricula = m.no("entrel", "Matricula")
    m.atr(matricula, "nota")
    m.liga("llabelMuitos", aluno, matricula)
    m.liga("llabelMuitos", disc, matricula)
    sala = m.entidade("Sala", "num")
    usa = m.no("rel", "Usa")
    m.liga("llabelMuitos", matricula, usa)
    m.liga("llabelUm", sala, usa)
    linhas = m.linhas()
    assert linhas["MATRICULA"] == ("MATRICULA (**mat_ALUNO**, **cod_DISCIPLINA**, nota, num_SALA)")


def test_especializacao_8a():
    m = Modelo()
    pessoa = m.entidade("Pessoa", "cpf")
    aluno = m.entidade("Aluno", chave=None)
    m.atr(aluno, "curso")
    prof = m.entidade("Professor", chave=None)
    circulo = m.no("disjuncao", "d")
    m.liga("llabelDoubleGeneralizacao", pessoa, circulo)
    m.liga("generalizacaoLine", circulo, aluno)
    m.liga("generalizacaoLine", circulo, prof)
    linhas = m.linhas()
    assert linhas["ALUNO"] == "ALUNO (**cpf**, curso)"
    assert linhas["PROFESSOR"] == "PROFESSOR (**cpf**)"
    assert m.estrangeiras("ALUNO") == [(("cpf",), "PESSOA", ("cpf",))]
    (g,) = generalizations(m.doc)
    assert g.total and g.superclasses == (pessoa,) and not g.assumed


def test_especializacao_com_linhas_iguais_assume_a_superclasse_com_chave():
    m = Modelo()
    pessoa = m.entidade("Pessoa", "cpf")
    aluno = m.entidade("Aluno", chave=None)
    circulo = m.no("sobreposicao", "o")
    m.liga("llabelGeneralizacao", pessoa, circulo)
    m.liga("llabelGeneralizacao", aluno, circulo)
    esquema = m.esquema()
    assert esquema.relation("ALUNO").primary_key == ("cpf",)
    assert DIRECTION_ASSUMED in {a.code for a in esquema.issues}


def test_uniao_cria_chave_substituta():
    m = Modelo()
    pessoa = m.entidade("Pessoa", "cpf")
    banco = m.entidade("Banco", "bnome")
    dono = m.entidade("Proprietario", chave=None)
    circulo = m.no("uniao", "u")
    m.liga("llabelGeneralizacao", pessoa, circulo)
    m.liga("llabelGeneralizacao", banco, circulo)
    m.liga("generalizacaoLine", circulo, dono)
    linhas = m.linhas()
    assert linhas["PROPRIETARIO"] == "PROPRIETARIO (**Id_Proprietario**)"
    assert linhas["PESSOA"] == "PESSOA (**cpf**, Id_Proprietario)"
    assert m.estrangeiras("BANCO") == [(("Id_Proprietario",), "PROPRIETARIO", ("Id_Proprietario",))]


def test_entidade_sem_chave_avisa_uma_vez_e_nao_quebra_as_estrangeiras():
    m = Modelo()
    sem = m.entidade("Sem chave", chave=None)
    outra = m.entidade("Outra", "id")
    rel = m.no("rel", "R")
    m.liga("llabelUm", sem, rel)
    m.liga("llabelMuitos", outra, rel)
    esquema = m.esquema()
    codigos = [a.code for a in esquema.issues]
    assert codigos.count(NO_KEY) == 1 and MISSING_REFERENCED_KEY in codigos
    assert relation_line(esquema.relation("SEM_CHAVE")) == "SEM_CHAVE ()"


def test_nomes_repetidos_ganham_numero():
    m = Modelo()
    m.entidade("Aluno", "mat")
    m.entidade("aluno", "mat")
    assert sorted(m.linhas()) == ["ALUNO", "ALUNO_2"]


def test_participacoes_nos_dois_sentidos():
    m = Modelo()
    a = m.entidade("A")
    rel = m.no("rel", "R")
    m.liga("llabelDoubleMuitos", a, rel)  # gravado relacionamento -> entidade
    (p,) = participants(m.doc)[id(rel)]
    assert (p.entity, p.cardinality, p.total) == (a, "N", True)


def test_nada_vai_para_o_arquivo():
    from haradaer.core import io

    m = Modelo()
    m.entidade("Aluno", "mat")
    antes = io.dumps(m.doc)
    m.esquema()
    assert io.dumps(m.doc) == antes


def test_markdown_basico():
    m = Modelo()
    dep = m.entidade("Departamento", "num")
    func = m.entidade("Funcionario", "cpf")
    rel = m.no("rel", "Trabalha para")
    m.liga("llabelUm", dep, rel)
    m.liga("llabelMuitos", func, rel)
    derivado = m.atr(dep, "Total", "atrderivado")
    derivado.attrs["sql"] = "SELECT COUNT(*)\nFROM FUNCIONARIO"
    texto = schema_markdown(m.esquema(), "empresa", "empresa.xml", "2026-10-25 10:00", str)
    assert texto == (
        "# Esquema lógico relacional — empresa\n"
        "\n"
        "Gerado pelo HaradaER a partir de `empresa.xml` em 2026-10-25 10:00.\n"
        "Não edite este arquivo: ele é refeito a partir do diagrama.\n"
        "\n"
        "Notação de Elmasri e Navathe, *Sistemas de Banco de Dados*. Chave primária em "
        "**negrito**; chaves estrangeiras listadas abaixo de cada relação.\n"
        "\n"
        "## Relações\n"
        "\n"
        "DEPARTAMENTO (**num**)\n"
        "\n"
        "FUNCIONARIO (**cpf**, num_DEPARTAMENTO)\n"
        "\n"
        "- num_DEPARTAMENTO → DEPARTAMENTO (num)\n"
        "\n"
        "## Atributos derivados\n"
        "\n"
        "Não viram colunas: são calculados a partir das outras relações.\n"
        "\n"
        "- Total, de DEPARTAMENTO: `SELECT COUNT(*) FROM FUNCIONARIO`\n"
        "\n"
        "## Avisos\n"
        "\n"
        "Nenhum.\n"
    )


def test_markdown_escapa_formatacao():
    m = Modelo()
    m.entidade("A*B", "x`y")
    texto = schema_markdown(m.esquema(), "m", None, "agora", str)
    assert "A\\*B (**x\\`y**)" in texto
    assert "a partir de um modelo não salvo em agora" in texto


def test_exemplo_empresa_do_livro():
    """O banco EMPRESA de Elmasri e Navathe (Figuras 9.1 e 9.2), com os nomes gerados no
    lugar dos que o livro renomeou à mão (Dnr, Fcpf, Pnr...)."""
    m = Modelo()
    func = m.entidade("FUNCIONARIO", chave=None)
    dep = m.entidade("DEPARTAMENTO", chave=None)
    proj = m.entidade("PROJETO", chave=None)
    depn = m.entidade("DEPENDENTE", chave=None, tag="entfraca")
    nome = m.atr(func, "Nome")
    for parte in ("Pnome", "Minicial", "Unome"):
        m.atr(nome, parte)
    m.atr(func, "Cpf", "atrchave")
    for atributo in ("Datanasc", "Endereco", "Sexo", "Salario"):
        m.atr(func, atributo)
    m.atr(dep, "Dnome")
    m.atr(dep, "Dnumero", "atrchave")
    m.atr(dep, "Localizacoes", "atrmulti")
    m.atr(dep, "Numero_funcionarios", "atrderivado")
    m.atr(proj, "Projnome")
    m.atr(proj, "Projnumero", "atrchave")
    m.atr(proj, "Projlocal")
    m.atr(depn, "Nome_dependente", "atrchaveparcial")
    for atributo in ("Sexo", "Datanasc", "Parentesco"):
        m.atr(depn, atributo)

    def relacionamento(nome, tag, ligacoes, atributo=None):
        rel = m.no(tag, nome)
        for tipo, entidade in ligacoes:
            m.liga(tipo, entidade, rel)
        if atributo:
            m.atr(rel, atributo)

    relacionamento("TRABALHA_PARA", "rel", [("llabelUm", dep), ("llabelDoubleMuitos", func)])
    relacionamento("GERENCIA", "rel", [("llabelUm", func), ("llabelDoubleUm", dep)], "Data_inicio")
    relacionamento("CONTROLA", "rel", [("llabelUm", dep), ("llabelDoubleMuitos", proj)])
    relacionamento("SUPERVISAO", "rel", [("llabelUm", func), ("llabelMuitos", func)])
    relacionamento(
        "TRABALHA_EM",
        "rel",
        [("llabelDoubleMuitos", func), ("llabelDoubleMuitos", proj)],
        "Horas",
    )
    relacionamento("DEPENDENTES_DE", "relfraco", [("llabelUm", func), ("llabelDoubleMuitos", depn)])
    esquema = m.esquema()
    assert [relation_line(r) for r in esquema.relations] == [
        "FUNCIONARIO (**Cpf**, Pnome, Minicial, Unome, Datanasc, Endereco, Sexo, Salario, "
        "Dnumero_DEPARTAMENTO, Cpf_FUNCIONARIO)",
        "DEPARTAMENTO (**Dnumero**, Dnome, Cpf_FUNCIONARIO, Data_inicio)",
        "PROJETO (**Projnumero**, Projnome, Projlocal, Dnumero_DEPARTAMENTO)",
        "DEPENDENTE (**Cpf_FUNCIONARIO**, **Nome_dependente**, Sexo, Datanasc, Parentesco)",
        "TRABALHA_EM (**Cpf_FUNCIONARIO**, **Projnumero_PROJETO**, Horas)",
        "DEPARTAMENTO_LOCALIZACOES (**Dnumero_DEPARTAMENTO**, **Localizacoes**)",
    ]
    assert [d.name for d in esquema.derived] == ["Numero_funcionarios"]
    assert esquema.issues == ()


def test_fraca_de_fraca_e_nomes_sem_acumular_sufixos():
    """A dona também pode ser fraca (o livro permite a cadeia); a fraca é a do lado N, e no
    empate a dona é a que já é fraca de outro relacionamento."""
    m = Modelo()
    maquina = m.entidade("Maquina", "id")
    sessao = m.entidade("Sessao", "inicio", tag="entfraca")
    prompt = m.entidade("Prompt", "ordem", tag="entfraca")
    resultado = m.entidade("Resultado", chave=None, tag="entfraca")
    usa = m.no("relfraco", "Usa")
    m.liga("llabelUm", maquina, usa)
    m.liga("llabelDoubleMuitos", sessao, usa)
    contem = m.no("relfraco", "Contem")
    m.liga("llabelDoubleUm", sessao, contem)
    m.liga("llabelDoubleMuitos", prompt, contem)
    gera = m.no("relfraco", "Gera")
    m.liga("llabelDoubleUm", resultado, gera)
    m.liga("llabelDoubleUm", prompt, gera)
    linhas = m.linhas()
    assert linhas["SESSAO"] == "SESSAO (**id_MAQUINA**, **inicio**)"
    assert linhas["PROMPT"] == "PROMPT (**id_SESSAO**, **inicio_SESSAO**, **ordem**)"
    assert linhas["RESULTADO"] == ("RESULTADO (**id_PROMPT**, **inicio_PROMPT**, **ordem_PROMPT**)")
    assert m.esquema().issues == ()
