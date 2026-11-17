"""Markdown do Texto (RF-28): CommonMark pelo markdown-it-py, com Enter = linha nova, e as listas
de tarefas do GitHub."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.appearance.describe import (
    CODE_FAMILY,
    LINK_COLOR,
    LIST_STEP,
    TEXT_AREA_INSET,
    describe_figure,
    font_of,
    text_area_layout,
)
from haradaer.core.appearance.markdown import escape_literal, parse, plain_text, toggle_task
from haradaer.core.appearance.ops import PolylineOp, ShapeOp, TextOp
from haradaer.core.commands import convert_free_texts, text_of
from haradaer.core.erview import find_texts
from haradaer.core.figures.factory import bool_entry, create_text_area
from haradaer.core.model.document import Document

MEDIDOR = FixedMeasurer()
FONTE = font_of(create_text_area(0, 0, 0, 0, ""))


def desenho(texto: str, largura: float = 300.0):
    return text_area_layout(texto, FONTE, largura, MEDIDOR)[0]


def pedacos(texto: str, largura: float = 300.0):
    """(texto, negrito, itálico, código) de cada pedaço, linha a linha."""
    return [
        [(s.text, s.font.bold, s.font.italic, s.font.family == CODE_FAMILY) for s in linha.segments]
        for linha in desenho(texto, largura)
    ]


def tipos(texto: str) -> list[str]:
    return [bloco.kind for bloco in parse(texto)]


# --- títulos ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nivel", "escala"), [(1, 2.0), (2, 1.5), (3, 1.17), (4, 1.0), (5, 0.83), (6, 0.67)]
)
def test_titulos_de_um_a_seis_em_negrito_e_maiores(nivel, escala):
    (linha,) = desenho("#" * nivel + " Regras")
    (pedaco,) = linha.segments
    assert pedaco.text == "Regras" and pedaco.font.bold
    assert pedaco.font.size == pytest.approx(12 * escala)


@pytest.mark.parametrize(
    "texto", ["#1 sem espaço", "####### sete", "\\# escapado", "    # recuado demais"]
)
def test_o_que_nao_e_titulo(texto):
    assert "heading" not in tipos(texto)


def test_titulo_com_fechamento_e_enfase():
    assert pedacos("## Nota *opcional* ##") == [
        [("Nota ", True, False, False), ("opcional", True, True, False)]
    ]


def test_titulo_sublinhado_fica_literal():
    assert tipos("Regras\n===") == ["paragraph"]
    assert plain_text("Regras\n===") == "Regras\n==="


# --- ênfase ----------------------------------------------------------------------------------


def test_negrito_italico_e_os_dois():
    assert pedacos("*a* _b_ **c** __d__ ***e***") == [
        [
            ("a", False, True, False),
            (" ", False, False, False),
            ("b", False, True, False),
            (" ", False, False, False),
            ("c", True, False, False),
            (" ", False, False, False),
            ("d", True, False, False),
            (" ", False, False, False),
            ("e", True, True, False),
        ]
    ]


def test_sublinhado_dentro_da_palavra_nao_vale_e_asterisco_vale():
    assert pedacos("id_cliente_ativo") == [[("id_cliente_ativo", False, False, False)]]
    assert pedacos("in*crí*vel") == [
        [("in", False, False, False), ("crí", False, True, False), ("vel", False, False, False)]
    ]


def test_aninhado_e_asterisco_sozinho():
    assert pedacos("*a **b** c*")[0][1] == ("b", True, True, False)
    assert plain_text("*opcional") == "*opcional"


def test_palavra_com_troca_de_fonte_nao_quebra_no_meio():
    largura = 10 * 7.2 + 2 * TEXT_AREA_INSET
    linhas = pedacos("aaaa in**crí**vel", largura)
    assert ["".join(p[0] for p in linha) for linha in linhas] == ["aaaa", "incrível"]


def test_negrito_da_caixa_inteira_continua_valendo():
    negrito = create_text_area(0, 0, 200, 60, "texto *it*", [bool_entry("fontBold")])
    textos = [op for op in describe_figure(negrito, MEDIDOR) if isinstance(op, TextOp)]
    assert all(op.font.bold for op in textos)
    assert textos[-1].font.italic


# --- listas ----------------------------------------------------------------------------------


def test_listas_com_marcador_recuo_e_sublista():
    linhas = desenho("- um\n  - dois\n    - tres\n      - quatro\n+ cinco")
    marcadores = [linha.segments[0].text for linha in linhas]
    assert marcadores == ["•", "◦", "▪", "▪", "•"]
    passo = LIST_STEP * 12
    assert [linha.indent for linha in linhas] == [passo, 2 * passo, 3 * passo, 4 * passo, passo]


def test_lista_numerada_comeca_onde_o_texto_manda():
    linhas = desenho("3. a\n4. b\n9) c")
    assert [linha.segments[0].text for linha in linhas] == ["3.", "4.", "9)"]


def test_continuacao_do_item_alinha_com_o_texto():
    largura = 12 * 7.2 + 2 * TEXT_AREA_INSET + LIST_STEP * 12
    primeira, segunda = desenho("- palavra outra", largura)
    assert primeira.segments[0].text == "•"
    assert segunda.segments[0].x == primeira.segments[1].x == LIST_STEP * 12


# --- código ----------------------------------------------------------------------------------


def test_codigo_em_linha_monoespacado_com_fundo():
    figura = create_text_area(0, 0, 200, 60, "use `SELECT` aqui")
    ops = describe_figure(figura, MEDIDOR)
    codigo = next(op for op in ops if isinstance(op, TextOp) and op.text == "SELECT")
    assert codigo.font.family == CODE_FAMILY
    fundos = [op for op in ops if isinstance(op, ShapeOp) and op.stroke is None]
    assert len(fundos) == 1 and fundos[0].x == codigo.x


@pytest.mark.parametrize("texto", ["```\nx = *1*\n```", "~~~\nx = *1*\n~~~", "    x = *1*"])
def test_bloco_de_codigo_literal_e_monoespacado(texto):
    (linha,) = desenho(texto)
    assert linha.code_block
    (pedaco,) = linha.segments
    assert pedaco.text == "x = *1*" and pedaco.font.family == CODE_FAMILY


def test_bloco_de_codigo_quebra_por_caractere():
    largura = 10 * 7.2 + 2 * TEXT_AREA_INSET
    linhas = desenho("```\n" + "x" * 25 + "\n```", largura)
    assert ["".join(s.text for s in linha.segments) for linha in linhas] == [
        "x" * 10,
        "x" * 10,
        "x" * 5,
    ]


# --- escapes, linhas e o que fica literal ----------------------------------------------------


def test_escape_de_qualquer_pontuacao():
    assert plain_text("\\*a\\* \\_b\\_ \\# \\`c\\`") == "*a* _b_ # `c`"


def test_enter_e_linha_nova_e_linhas_em_branco_aparecem():
    assert tipos("a\nb") == ["paragraph"]
    assert ["".join(p[0] for p in linha) for linha in pedacos("a\nb\n\n\nc")] == [
        "a",
        "b",
        "",
        "",
        "c",
    ]


@pytest.mark.parametrize(
    "texto",
    [
        "![foto](a.png)",
        "> citação",
        "| a | b |\n|---|---|",
        "---",
        "<b>html</b>",
        "www.sem-sinal.com",
    ],
)
def test_imagens_citacoes_tabelas_e_html_ficam_literais(texto):
    assert plain_text(texto) == texto
    assert all(not s.font.bold for linha in desenho(texto) for s in linha.segments)


def test_altura_soma_linhas_de_tamanhos_diferentes():
    _linhas, altura = text_area_layout("# T\nnormal", FONTE, 300, MEDIDOR)
    assert altura == pytest.approx(24 * 1.36 + 12 * 1.36 + 2 * TEXT_AREA_INSET)


# --- localizar e conversão -------------------------------------------------------------------


def test_localizar_ignora_os_marcadores():
    doc = Document.new()
    texto = create_text_area(0, 0, 120, 60, "## Regra\n**cliente** *ativo*")
    doc.figures.append(texto)
    assert find_texts(doc, "cliente ativo") == [texto]
    assert find_texts(doc, "**") == []


@pytest.mark.parametrize(
    "original",
    [
        "normal",
        "*opcional",
        "a *b* c",
        "1. item",
        "# tag",
        "- traço",
        "x_y_z",
        "`código`",
        "&amp;",
        "\\barra",
        "[a](b)",
        "veja <http://x>",
        "- [ ] t",
    ],
)
def test_texto_convertido_aparece_igual(original):
    escapado = escape_literal(original)
    assert plain_text(escapado) == original
    assert tipos(escapado) == ["paragraph"]
    assert not any(
        s.font.bold or s.font.italic for linha in desenho(escapado) for s in linha.segments
    )


def test_texto_comum_nao_ganha_barra():
    for original in ("normal", "*opcional", "x_y_z", "nota: 1 de 2"):
        assert escape_literal(original) == original


def test_conversao_escapa_so_o_necessario():
    doc = io.loads(
        '<drawing><figures><t id="0" x="5" y="5"><a><text><string>1. *opcional* item</string>'
        "</text></a></t></figures></drawing>"
    )
    assert convert_free_texts(doc, MEDIDOR) == [("t", "1. *opcional* item")]
    assert text_of(doc.figures[0]) == "1\\. \\*opcional\\* item"
    assert plain_text(text_of(doc.figures[0])) == "1. *opcional* item"


# --- links -----------------------------------------------------------------------------------


def links(texto: str) -> list[tuple[str, str | None]]:
    figura = create_text_area(0, 0, 400, 60, texto)
    return [(op.text, op.link) for op in describe_figure(figura, MEDIDOR) if isinstance(op, TextOp)]


def test_link_em_linha_automatico_e_por_referencia():
    texto = '[site](http://a.com) <http://b.com> [ref]\n\n[ref]: http://c.com "título"'
    assert links(texto) == [
        ("site", "http://a.com"),
        (" ", None),
        ("http://b.com", "http://b.com"),
        (" ", None),
        ("ref", "http://c.com"),
    ]
    assert plain_text(texto) == "site http://b.com ref\n"  # a definição some, como manda


def test_link_azul_sublinhado():
    figura = create_text_area(0, 0, 400, 60, "veja [o *site*](http://a.com)")
    ops = [op for op in describe_figure(figura, MEDIDOR) if isinstance(op, TextOp) and op.link]
    assert [op.text for op in ops] == ["o ", "site"]
    assert all(op.color == LINK_COLOR and op.font.underline for op in ops)
    assert ops[1].font.italic


def test_imagem_fica_como_escrita_e_nao_vira_link():
    assert links('![foto](a.png "t")') == [('![foto](a.png "t")', None)]


# --- listas de tarefas -----------------------------------------------------------------------


def test_tarefas_marcadas_e_por_marcar():
    linhas = desenho("- [x] feito\n- [ ] falta\n- [X] também\n- normal")
    assert [linha.segments[0].checkbox for linha in linhas] == [True, False, True, None]
    assert [s.text for s in linhas[0].segments] == ["", "feito"]
    assert linhas[3].segments[0].text == "•"


def test_caixinha_desenhada_com_tique_so_se_marcada():
    figura = create_text_area(0, 0, 200, 60, "- [x] a\n- [ ] b")
    ops = describe_figure(figura, MEDIDOR)
    caixas = [op for op in ops[1:] if isinstance(op, ShapeOp)]
    assert len(caixas) == 2 and caixas[0].w == caixas[0].h == 12 * 0.8
    assert len([op for op in ops if isinstance(op, PolylineOp)]) == 1


def test_colchete_sem_espaco_nao_e_tarefa():
    assert desenho("- [x]feito")[0].segments[0].checkbox is None


def test_marcar_e_desmarcar_a_tarefa_pela_linha():
    texto = "- [x] a\n- [ ] b\n  - [X] c\n1. [ ] d\nnão é tarefa"
    assert toggle_task(texto, 0).split("\n")[0] == "- [ ] a"
    assert toggle_task(texto, 1).split("\n")[1] == "- [x] b"
    assert toggle_task(texto, 2).split("\n")[2] == "  - [ ] c"
    assert toggle_task(texto, 3).split("\n")[3] == "1. [x] d"
    assert toggle_task(texto, 4) == texto and toggle_task(texto, 99) == texto


def test_caixinha_sabe_a_linha_da_sua_tarefa():
    figura = create_text_area(0, 0, 200, 60, "# T\n- [ ] a\n\n- [x] b")
    caixas = [
        op.task
        for op in describe_figure(figura, MEDIDOR)
        if isinstance(op, ShapeOp) and op.task is not None
    ]
    assert caixas == [1, 3]
