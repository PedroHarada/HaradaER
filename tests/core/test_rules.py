"""Validação e recomendação de conexões, conferidas contra o próprio TerraER."""

import re

import pytest

from haradaer.core import io
from haradaer.core.figures.tags import CONNECTION_TAGS, NODE_TAGS
from haradaer.core.rules import (
    CONNECTION_RULES,
    INCOMPLETE,
    INVALID_PAIR,
    is_valid_connection,
    recommend_connections,
    recommend_elements,
    validate,
)


def _matriz_do_terraer(referencia) -> dict[str, set[tuple[str, str]]]:
    """Pares válidos medidos com `ModelValidation` do TerraER (`harness/Matrix.java`)."""
    matriz = {}
    for linha in (referencia / "matriz-validacao.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (\S+): (.*)", linha)
        if m:
            matriz[m.group(1)] = {tuple(p.split("->")) for p in m.group(2).split()}
    return matriz


def test_tabela_confere_com_o_terraer_par_a_par(referencia):
    medida = _matriz_do_terraer(referencia)
    assert set(medida) == CONNECTION_TAGS - {"lcf"}
    for conexao, pares in medida.items():
        assert set(CONNECTION_RULES[conexao]) == pares, conexao


def test_todos_os_pares_de_todas_as_conexoes(referencia):
    medida = _matriz_do_terraer(referencia)
    for conexao, pares in medida.items():
        for origem in NODE_TAGS:
            for destino in NODE_TAGS:
                esperado = (origem, destino) in pares
                assert is_valid_connection(conexao, origem, destino) is esperado


def test_lcf_e_apelido_de_lcaf():
    assert CONNECTION_RULES["lcf"] == CONNECTION_RULES["lcaf"]


def test_conexao_livre_liga_qualquer_par():
    assert all(is_valid_connection("llabel", a, b) for a in NODE_TAGS for b in NODE_TAGS)


def test_conexao_desconhecida_nunca_e_valida():
    assert not is_valid_connection("naoexiste", "ent", "rel")


def test_generalizacao_simples_e_assimetrica():
    assert is_valid_connection("generalizacaoLine", "uniao", "ent")
    assert not is_valid_connection("generalizacaoLine", "ent", "uniao")


def _vermelhos_do_terraer(referencia):
    """(arquivo, posição na lista de figuras) -> se o TerraER pinta de vermelho."""
    resultado = {}
    for linha in (
        (referencia / "validacao-por-arquivo.txt").read_text(encoding="utf-8").splitlines()
    ):
        arquivo, posicao, tag, cor = linha.split("\t")
        resultado[(arquivo, int(posicao))] = (tag, cor == "vermelho")
    return resultado


def test_cada_conexao_dos_arquivos_de_referencia_confere_com_o_terraer(referencia):
    esperado = _vermelhos_do_terraer(referencia)
    assert len(esperado) == 22
    por_arquivo: dict[str, dict[int, bool]] = {}
    for arquivo in sorted({a for a, _ in esperado}):
        doc = io.loads((referencia / arquivo).read_bytes())
        com_problema = {doc.figures.index(i.figure) for i in validate(doc)}
        por_arquivo[arquivo] = {pos: pos in com_problema for pos in range(len(doc.figures))}
    for (arquivo, posicao), (tag, vermelho) in esperado.items():
        assert por_arquivo[arquivo][posicao] is vermelho, f"{arquivo}[{posicao}] {tag}"


def test_problemas_de_todos_os_tipos(referencia):
    doc = io.loads((referencia / "amostra-todos-os-tipos.xml").read_bytes())
    (problema,) = validate(doc)
    assert problema.code == INVALID_PAIR
    assert problema.figure.tag == "generalizacaoLine"
    assert problema.details == {
        "connection": "generalizacaoLine",
        "start": "uniao",
        "end": "entfraca",
    }


def test_amostra_sem_problemas(referencia):
    assert validate(io.loads((referencia / "amostra-basica.xml").read_bytes())) == []
    assert validate(io.loads((referencia / "amostra-ordem-empilhamento.xml").read_bytes())) == []


def test_conexoes_incompletas(referencia):
    doc = io.loads((referencia / "amostra-conexoes-incompletas.xml").read_bytes())
    problemas = validate(doc)
    # llabelUm e lcaf, cada um: sem pontas, só início, início e fim no mesmo nó.
    # A conexão livre (llabel) nunca tem problema, mesmo sem pontas.
    assert [(p.figure.tag, p.code, p.details.get("missing")) for p in problemas] == [
        ("llabelUm", INCOMPLETE, "ambas"),
        ("llabelUm", INCOMPLETE, "fim"),
        ("llabelUm", INVALID_PAIR, None),
        ("lcaf", INCOMPLETE, "ambas"),
        ("lcaf", INCOMPLETE, "fim"),
        ("lcaf", INVALID_PAIR, None),
    ]
    assert problemas[2].details == {"connection": "llabelUm", "start": "ent", "end": "ent"}


def test_recomendacao_entre_dois_elementos():
    assert recommend_connections("ent", "rel") == [
        "llabelUm",
        "llabelMuitos",
        "llabelDoubleUm",
        "llabelDoubleMuitos",
    ]
    assert recommend_connections("atrchave", "ent") == ["lcaf"]
    assert recommend_connections("ent", "disjuncao") == [
        "llabelGeneralizacao",
        "llabelDoubleGeneralizacao",
    ]
    assert recommend_connections("ent", "ent") == ["generalizacaoLine"]
    assert recommend_connections("rel", "rel") == []


def test_recomendacao_nunca_inclui_a_conexao_livre_nem_algo_invalido():
    for origem in NODE_TAGS:
        for destino in NODE_TAGS:
            for conexao in recommend_connections(origem, destino):
                assert conexao != "llabel"
                assert is_valid_connection(conexao, origem, destino)


def test_elementos_possiveis_para_uma_conexao():
    pares = recommend_elements("generalizacaoLine")
    assert pares == [
        ("ent", "ent"),
        ("uniao", "ent"),
        ("disjuncao", "ent"),
        ("sobreposicao", "ent"),
    ]
    assert recommend_elements("llabelUm")[0] == ("ent", "rel")
    assert len(recommend_elements("lcaf")) == 37


def _recomendacao_do_terraer(referencia) -> dict[str, set[tuple[str, str]]]:
    """Tabela que o TerraER usa em `ModelValidationRules` (despejada por `harness/Regras.java`)."""
    classe_para_tag = {
        "LabeledLineConnectionUm": "llabelUm",
        "LabeledLineConnectionMuitos": "llabelMuitos",
        "LabeledDoubleLineConnectionUm": "llabelDoubleUm",
        "LabeledDoubleLineConnectionMuitos": "llabelDoubleMuitos",
        "LineConnectionGeneralizacao": "llabelGeneralizacao",
        "DoubleLineConnectionGeneralizacao": "llabelDoubleGeneralizacao",
        "ConnectionAttribute": "lcaf",
        "GeneralizacaoLineConnection": "generalizacaoLine",
    }
    no_para_tag = {
        "Entidade": "ent", "EntidadeFraca": "entfraca", "Relacionamento": "rel",
        "RelacionamentoFraco": "relfraco", "EntidadeRelacionamento": "entrel",
        "Atributo": "atr", "AtributoChave": "atrchave", "AtributoChaveParcial": "atrchaveparcial",
        "AtributoDerivado": "atrderivado", "AtributoMultivalorado": "atrmulti",
        "Uniao": "uniao", "Disjuncao": "disjuncao", "Sobreposicao": "sobreposicao",
    }  # fmt: skip
    tabela: dict[str, set[tuple[str, str]]] = {}
    texto = (referencia / "regras-recomendacao-terraer.txt").read_text(encoding="utf-8")
    for linha in texto.splitlines():
        m = re.match(r"(\S+)\s+bidirecional=(\w+)\s+\| origem: (.*?) \| destino: (.*)$", linha)
        if not m:
            continue
        conexao, bidirecional = classe_para_tag[m.group(1)], m.group(2) == "true"
        for origem in m.group(3).split():
            for destino in m.group(4).split():
                par = (no_para_tag[origem], no_para_tag[destino])
                tabela.setdefault(conexao, set()).add(par)
                if bidirecional:
                    tabela[conexao].add(par[::-1])
    return tabela


def test_diferencas_conhecidas_entre_a_recomendacao_do_terraer_e_a_nossa(referencia):
    """O TerraER recomenda pares que a própria verificação pinta de vermelho; nós não."""
    terraer = _recomendacao_do_terraer(referencia)
    so_do_terraer = {c: terraer[c] - CONNECTION_RULES[c] for c in terraer}
    so_nosso = {c: CONNECTION_RULES[c] - terraer[c] for c in terraer}
    fraco = {("entfraca", "relfraco"), ("relfraco", "entfraca")}
    assert so_do_terraer == {
        "llabelUm": fraco,
        "llabelMuitos": fraco,
        "llabelDoubleUm": set(),
        "llabelDoubleMuitos": set(),
        "llabelGeneralizacao": set(),
        "llabelDoubleGeneralizacao": set(),
        "lcaf": set(),
        "generalizacaoLine": {("ent", g) for g in ("uniao", "disjuncao", "sobreposicao")},
    }
    assert so_nosso == {
        **{c: set() for c in terraer},
        "generalizacaoLine": {(g, "ent") for g in ("uniao", "disjuncao", "sobreposicao")},
    }


@pytest.mark.parametrize("conexao", sorted(CONNECTION_TAGS - {"llabel"}))
def test_recomendar_elementos_so_devolve_pares_validos(conexao):
    for origem, destino in recommend_elements(conexao):
        assert is_valid_connection(conexao, origem, destino)
