"""O que o núcleo manda desenhar, conferido contra o que o TerraER desenha."""

import pytest

from haradaer.core import io
from haradaer.core.appearance import (
    ArcOp,
    FixedMeasurer,
    FontSpec,
    ImageOp,
    PolylineOp,
    ShapeOp,
    Style,
    TextOp,
    describe_document,
    describe_figure,
    label_position,
    parse_color,
    point_on_path,
)
from haradaer.core.model.element import Element


def _abrir(referencia, nome):
    return io.loads((referencia / nome).read_bytes())


def _ops(documento, indice):
    return describe_figure(documento.figures[indice], FixedMeasurer())


def test_cores():
    assert parse_color("#ffffebeb") == (255, 235, 235, 255)
    assert parse_color("#80fa0000") == (250, 0, 0, 128)
    assert parse_color("ff00ff") == (255, 0, 255, 255)


def test_estilos_gravados_pelo_terraer(referencia):
    doc = _abrir(referencia, "amostra-estilos.xml")
    retangulo, texto = doc.figures
    s = Style.of(retangulo)
    assert s.double("strokeWidth") == 3.0
    assert s.color("fillColor") == (250, 0, 0, 128)
    assert s.color("strokeColor") == (10, 20, 200, 255)
    assert s.doubles("strokeDashes") == (4.0, 2.0)
    t = Style.of(texto)
    assert t.boolean("fontItalic") and t.boolean("fontBold") and t.boolean("fontUnderlined")
    assert t.double("fontSize") == 20.0
    assert t.string("text") == "Estilo"
    assert t.color("textColor") == (0, 128, 0, 255)
    assert t.font_face() == ("Serif", 1, 14.0)
    assert t.double("naoexiste", 7.0) == 7.0


def test_estilo_vazio_usa_padroes():
    s = Style.of(Element("r"))
    assert s.color("fillColor") is None and s.boolean("fontBold", False) is False


def test_formas_tem_preenchimento_fixo_do_terraer(referencia):
    doc = _abrir(referencia, "amostra-basica.xml")
    (retangulo, texto) = _ops(doc, 0)
    assert isinstance(retangulo, ShapeOp) and retangulo.kind == "rect"
    assert retangulo.fill == (175, 255, 175, 255)
    assert retangulo.stroke.double is False and retangulo.stroke.width == 1.0
    assert isinstance(texto, TextOp) and texto.text == "Aluno"

    (losango, _) = _ops(doc, 2)
    assert (losango.kind, losango.fill) == ("diamond", (255, 255, 100, 255))
    (elipse, _) = _ops(doc, 4)
    assert (elipse.kind, elipse.fill) == ("ellipse", (175, 175, 255, 255))


def test_o_preenchimento_do_arquivo_e_ignorado_nas_formas_fixas(referencia):
    """O atributo derivado grava `fillColor` rosa, mas o TerraER desenha a elipse lilás."""
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    derivado = next(f for f in doc.figures if f.tag == "atrderivado")
    forma, _ = describe_figure(derivado, FixedMeasurer())
    assert forma.fill == (175, 175, 255, 255)
    assert forma.stroke.dashes == (5.0,)


def test_tracos_duplos_dos_elementos_fracos(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    fraca = next(f for f in doc.figures if f.tag == "entfraca")
    forma, _ = describe_figure(fraca, FixedMeasurer())
    assert forma.stroke.double is True and forma.stroke.factor == 3.0
    multi = next(f for f in doc.figures if f.tag == "atrmulti")
    assert describe_figure(multi, FixedMeasurer())[0].stroke.double is True


def test_entidade_associativa_tem_retangulo_losango_e_texto(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    entrel = next(f for f in doc.figures if f.tag == "entrel")
    tipos = [
        (type(o).__name__, getattr(o, "kind", None))
        for o in describe_figure(entrel, FixedMeasurer())
    ]
    assert tipos == [("ShapeOp", "rect"), ("ShapeOp", "diamond"), ("TextOp", None)]


def test_estilo_do_texto(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    chave = next(f for f in doc.figures if f.tag == "atrchaveparcial")
    forma, texto, sublinhado = describe_figure(chave, FixedMeasurer())
    assert texto.font.bold and not texto.font.underline
    assert isinstance(sublinhado, PolylineOp) and sublinhado.stroke.dashes == (3.0,)
    uniao = next(f for f in doc.figures if f.tag == "uniao")
    circulo, letra = describe_figure(uniao, FixedMeasurer())
    assert circulo.fill == (245, 242, 224, 255), "o círculo usa o fillColor do arquivo"
    assert letra.font == FontSpec(size=16.0, bold=True)


def test_negrito_e_italico_implicitos_nas_anotacoes(referencia):
    doc = _abrir(referencia, "amostra-figuras-de-apoio.xml")
    livre, negrito, italico = (
        describe_figure(doc.figures[i], FixedMeasurer())[0] for i in range(3)
    )
    assert not livre.font.bold and not livre.font.italic
    assert negrito.font.bold and not negrito.font.italic
    assert italico.font.italic and not italico.font.bold


def test_figuras_de_apoio(referencia):
    doc = _abrir(referencia, "amostra-figuras-de-apoio.xml")
    por_tag = {f.tag: describe_figure(f, FixedMeasurer()) for f in doc.figures}
    area = por_tag["ta"]
    assert [o.kind for o in area if isinstance(o, ShapeOp)] == ["rect"]
    linhas = [o for o in area if isinstance(o, TextOp)]
    assert [(o.text, o.x, o.y) for o in linhas][0] == ("Área", 15.0, 105.0)
    assert [o.text for o in linhas] == ["Área", "de texto"]
    assert linhas[1].y > linhas[0].y
    (circulo,) = por_tag["circ"]
    assert circulo.fill == (255, 255, 255, 255), "círculo livre é branco"
    (linha,) = por_tag["l"]
    assert linha.points == ((300.0, 70.0), (380.0, 100.0))
    assert len(por_tag["b"][0].points) == 3
    assert [type(o).__name__ for o in por_tag["g"]] == ["ShapeOp", "TextOp"]
    (imagem,) = por_tag["image"]
    assert isinstance(imagem, ImageOp) and imagem.data.startswith(b"\x89PNG")
    assert (imagem.x, imagem.y, imagem.w, imagem.h) == (400.0, 70.0, 32.0, 32.0)


class _MedidaDoTerraer:
    """Tamanhos de texto que o TerraER mediu (`harness/Rotulos.java`)."""

    TAMANHOS = {
        ("1", 16.0): (9.15, 21.79),
        ("N", 16.0): (13.01, 21.79),
        ("characteristic", 12.0): (71.77, 16.34),
    }

    def size(self, text, font):
        return self.TAMANHOS[(text, font.size)]


def test_rotulos_ficam_onde_o_terraer_os_coloca(referencia):
    doc = _abrir(referencia, "amostra-basica.xml")
    esperado = {"llabelUm": (154.96, 36.09), "llabelMuitos": (264.04, 27.03)}
    for figura in doc.figures:
        if figura.tag in esperado:
            *_, rotulo = describe_figure(figura, _MedidaDoTerraer())
            assert (rotulo.x, rotulo.y) == pytest.approx(esperado[figura.tag], abs=0.1)

    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    figura = next(f for f in doc.figures if f.tag == "llabelGeneralizacao")
    *_, rotulo = describe_figure(figura, _MedidaDoTerraer())
    assert rotulo.text == "characteristic"
    assert (rotulo.x, rotulo.y) == pytest.approx((54.68, 221.52), abs=0.1)
    duplo = next(f for f in doc.figures if f.tag == "llabelDoubleUm")
    *_, rotulo = describe_figure(duplo, _MedidaDoTerraer())
    assert (rotulo.x, rotulo.y) == pytest.approx((108.82, 30.72), abs=0.1)


def test_ponto_no_caminho():
    reta = [(0.0, 0.0), (10.0, 0.0)]
    assert point_on_path(reta, 0.0) == (0.0, 0.0)
    assert point_on_path(reta, 0.5) == (5.0, 0.0)
    assert point_on_path(reta, 1.0) == (10.0, 0.0)
    dobrada = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    assert point_on_path(dobrada, 0.75) == (10.0, 5.0)
    assert point_on_path([(3.0, 4.0)], 0.5) == (3.0, 4.0)


def test_posicao_do_rotulo_nos_quadrantes():
    # linha para a direita: âncora acima à direita, rótulo cresce para cima
    x, y = label_position([(0.0, 0.0), (100.0, 0.0)], 0.0, 10.0, 20.0)
    assert x == pytest.approx(5.657, abs=0.01) and y == pytest.approx(-5.657 - 20.0, abs=0.01)
    # linha para a esquerda: âncora abaixo à esquerda, rótulo cresce para a esquerda
    x, y = label_position([(100.0, 0.0), (0.0, 0.0)], 0.0, 10.0, 20.0)
    assert x == pytest.approx(100 - 5.657 - 10.0, abs=0.01) and y == pytest.approx(5.657, abs=0.01)


def test_conexoes_de_traco_duplo_e_sem_rotulo(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    por_tag = {
        f.tag: describe_figure(f, FixedMeasurer())
        for f in doc.figures
        if f.tag.startswith(("llabel", "gen", "lcaf"))
    }
    assert por_tag["llabelDoubleUm"][0].stroke.double and por_tag["llabelDoubleUm"][1].text == "1"
    assert por_tag["llabelDoubleMuitos"][1].text == "N"
    assert por_tag["llabelDoubleGeneralizacao"][0].stroke.double
    assert not por_tag["llabelGeneralizacao"][0].stroke.double
    assert len(por_tag["llabel"]) == 1 and len(por_tag["lcaf"]) == 1


def test_arco_da_generalizacao_simples():
    ligacao = Element("generalizacaoLine", children=[Element("points", children=[
        Element("p", {"x": "0", "y": "100"}), Element("p", {"x": "100", "y": "0"}),
    ])])  # fmt: skip
    linha, arco = describe_figure(ligacao, FixedMeasurer())
    assert isinstance(linha, PolylineOp) and isinstance(arco, ArcOp)
    assert (arco.cx, arco.cy, arco.radius, arco.span) == (50.0, 50.0, 10.0, 210)
    assert arco.start == 300  # começa em int(315) - 15


def test_conexao_sem_pontos_nao_desenha():
    assert describe_figure(Element("llabelUm"), FixedMeasurer()) == []


def test_documento_todo(referencia):
    doc = _abrir(referencia, "amostra-todos-os-tipos.xml")
    descricao = describe_document(doc, FixedMeasurer())
    assert [f for f, _ in descricao] == list(doc.figures)
    assert all(ops for _, ops in descricao)
