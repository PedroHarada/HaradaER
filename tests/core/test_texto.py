"""Texto (RF-26), a conversão dos textos soltos do TerraER (RF-27) e o Markdown (RF-28)."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import FixedMeasurer
from haradaer.core.appearance.describe import TEXT_AREA_INSET, font_of, text_area_layout
from haradaer.core.commands import (
    History,
    add_text_area_command,
    all_text_areas,
    convert_free_texts,
    paste_command,
    resize_text_area_command,
    set_text_command,
    text_area_rect,
    text_of,
)
from haradaer.core.erview import find_texts
from haradaer.core.figures.factory import TEXT_AREA_SIZE, create_text_area
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import parse_number

MEDIDOR = FixedMeasurer()  # 12 de fonte: 7,2 de largura por caractere e 16,32 de altura por linha
LINHA = 12 * 1.36


def novo_texto(conteudo="Observação", caixa=(10, 20, *TEXT_AREA_SIZE)):
    doc, h = Document.new(), History()
    comando, texto = add_text_area_command(doc, caixa, conteudo, MEDIDOR)
    h.execute(comando)
    return doc, h, texto


def linhas(texto: str, largura: float = 120.0) -> list[str]:
    """O texto de cada linha desenhada numa caixa dessa largura."""
    fonte = font_of(create_text_area(0, 0, 0, 0, ""))
    desenho, _altura = text_area_layout(texto, fonte, largura, MEDIDOR)
    return ["".join(s.text for s in linha.segments) for linha in desenho]


def estilo(figura: Element) -> dict[str, str | None]:
    return {
        e.tag: (e.children[0].text if e.children else None)
        for bloco in figura.children_named("a")
        for e in bloco.children
    }


# --- quebra de linha -------------------------------------------------------------------------


def test_quebra_entre_palavras_no_enter_e_corta_palavra_longa():
    largura = 10 * 7.2 + 2 * TEXT_AREA_INSET  # cabem 10 caracteres
    assert linhas("um dois tres quatro", largura) == ["um dois", "tres", "quatro"]
    assert linhas("a\n\nb", largura) == ["a", "", "b"]
    assert linhas("x" * 25, largura) == ["x" * 10, "x" * 10, "x" * 5]


# --- criar, editar, redimensionar ------------------------------------------------------------


def test_criar_grava_a_area_de_texto_do_terraer():
    doc, h, texto = novo_texto()
    assert texto.tag == "ta" and texto.has_id
    assert text_area_rect(texto) == (10, 20, 120, 60)
    assert text_of(texto) == "Observação"
    gravado = io.dumps(doc)
    assert "<ta " in gravado and 'w="120" h="60"' in gravado
    assert text_of(io.loads(gravado).figures[0]) == "Observação"
    h.undo()
    assert doc.figures == []


def test_criar_com_texto_longo_cresce_so_a_altura():
    _doc, _h, texto = novo_texto("palavra " * 20)
    x, y, w, h = text_area_rect(texto)
    assert (x, y, w) == (10, 20, 120)
    assert h > 60


def test_editar_cresce_a_altura_nunca_encolhe_e_desfaz():
    doc, h, texto = novo_texto()
    h.execute(set_text_command(doc, texto, "linha\n" * 6, MEDIDOR))
    alta = text_area_rect(texto)
    assert alta[2] == 120 and alta[3] == pytest.approx(7 * LINHA + 2 * TEXT_AREA_INSET)
    h.execute(set_text_command(doc, texto, "curto", MEDIDOR))
    assert text_area_rect(texto) == alta  # não encolhe sozinho
    h.undo()
    h.undo()
    assert text_of(texto) == "Observação" and text_area_rect(texto) == (10, 20, 120, 60)


def test_area_de_texto_vazia_do_terraer_ganha_o_texto():
    doc, h = Document.new(), History()
    vazio = Element("ta", attrs={"x": "0", "y": "0", "w": "120", "h": "60"}, has_id=True)
    doc.figures.append(vazio)
    h.execute(set_text_command(doc, vazio, "agora tem", MEDIDOR))
    assert text_of(vazio) == "agora tem"
    h.undo()
    assert vazio.children == []


def test_redimensionar_estreito_aumenta_a_altura_para_caber():
    doc, h, texto = novo_texto("um dois tres quatro")
    h.execute(resize_text_area_command(doc, texto, (10, 20, 60, 20), MEDIDOR))
    x, y, w, altura = text_area_rect(texto)
    assert (x, y, w) == (10, 20, 60)
    assert altura == pytest.approx(len(linhas(text_of(texto), 60)) * LINHA + 2 * TEXT_AREA_INSET)
    h.execute(resize_text_area_command(doc, texto, (10, 20, 300, 200), MEDIDOR))
    assert text_area_rect(texto) == (10, 20, 300, 200)  # maior que o texto pede: fica


# --- conversão dos textos soltos (RF-27) -----------------------------------------------------


def test_converte_texto_negrito_papel_e_o_de_dentro_do_grupo(referencia):
    doc = io.loads((referencia / "amostra-figuras-de-apoio.xml").read_bytes())
    solto = doc.figures[0]
    antes = (parse_number(solto.attrs["x"]), parse_number(solto.attrs["y"]))
    convertidos = convert_free_texts(doc, MEDIDOR)
    assert convertidos == [
        ("t", "Anotação livre"),
        ("tn", "Negrito"),
        ("ti", "Itálico"),
        ("t", "no grupo"),
    ]
    assert not any(f.tag in ("t", "tn", "ti") for f in doc.figures)
    textos = all_text_areas(doc)
    assert [text_of(t) for t in textos] == [
        "Anotação livre",
        "Negrito",
        "Itálico",
        "Área\nde texto",
        "no grupo",
    ]
    negrito, papel = textos[1], textos[2]
    assert estilo(negrito)["fontBold"] == "true" and font_of(negrito).bold
    assert estilo(papel)["fontItalic"] == "true" and font_of(papel).italic
    x, y, _w, _h = text_area_rect(textos[0])
    assert (x + TEXT_AREA_INSET, y + TEXT_AREA_INSET) == antes  # o texto fica no lugar
    assert io.loads(io.dumps(doc))  # o arquivo continua válido


def test_texto_convertido_cabe_numa_linha():
    doc = Document.new()
    doc.figures.append(
        io.loads(
            '<drawing><figures><t id="0" x="0" y="0"><a><text><string>uma frase longa de anotação'
            "</string></text></a></t></figures></drawing>"
        ).figures[0]
    )
    convert_free_texts(doc, MEDIDOR)
    texto = doc.figures[0]
    assert len(linhas(text_of(texto), text_area_rect(texto)[2])) == 1


def test_nomes_dos_elementos_nao_mudam(referencia):
    doc = io.loads((referencia / "amostra-basica.xml").read_bytes())
    antes = io.dumps(doc)
    assert convert_free_texts(doc, MEDIDOR) == []
    assert io.dumps(doc) == antes


def test_colar_converte_os_textos_soltos():
    pedaco = (
        '<drawing><figures><ti id="0" x="5" y="5"><a><text><string>gerente</string></text></a>'
        "</ti></figures></drawing>"
    )
    doc = Document.new()
    _comando, novas = paste_command(doc, pedaco, 0, 0, MEDIDOR)
    assert [f.tag for f in novas] == ["ta"] and text_of(novas[0]) == "gerente"
    assert font_of(novas[0]).italic


def test_localizar_acha_pelo_conteudo_sem_acento():
    doc, _h, texto = novo_texto("Regra de negócio:\ncliente ativo")
    assert find_texts(doc, "NEGOCIO") == [texto]
    assert find_texts(doc, "cliente at") == [texto]
    assert find_texts(doc, "fornecedor") == []
