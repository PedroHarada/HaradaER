"""RNF-10, RNF-14 e RNF-15: o que o leitor aceita e o que recusa, com mensagem clara."""

import pytest

from haradaer.core import io
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.xmlfmt import reader

ENT = (
    '<ent id="0"><children><r id="1" x="0" y="0" w="50" h="20"/>'
    '<t id="2" x="0" y="0"><a><text><string>E</string></text></a></t></children></ent>'
)


def _desenho(*figuras: str) -> str:
    return f"<drawing><figures>{''.join(figuras)}</figures></drawing>"


def test_tag_desconhecida_e_erro_claro_com_a_linha():
    xml = '<drawing>\n<figures>\n<foo id="9"/>\n</figures>\n</drawing>'
    with pytest.raises(ArquivoInvalidoError) as erro:
        io.loads(xml)
    assert "<foo>" in str(erro.value)
    assert "<figures>" in str(erro.value)
    assert erro.value.linha == 3


def test_tag_desconhecida_dentro_de_um_elemento():
    xml = _desenho('<ent id="0"><children><bar id="7"/></children></ent>')
    with pytest.raises(ArquivoInvalidoError, match="<bar>"):
        io.loads(xml)


def test_raiz_errada_e_sem_figures():
    with pytest.raises(ArquivoInvalidoError, match="<drawing>"):
        io.loads("<document><figures/></document>")
    with pytest.raises(ArquivoInvalidoError, match="<figures>"):
        io.loads("<drawing/>")


@pytest.mark.parametrize("conteudo", [b"", b"   ", b"<drawing><figures>"])
def test_arquivo_vazio_ou_cortado(conteudo):
    with pytest.raises(ArquivoInvalidoError):
        io.loads(conteudo)


def test_id_repetido():
    xml = _desenho(ENT, ENT)
    with pytest.raises(ArquivoInvalidoError, match='id "0"'):
        io.loads(xml)


def test_referencia_para_id_inexistente():
    xml = _desenho('<ent ref="99"/>')
    with pytest.raises(ArquivoInvalidoError, match='"99"'):
        io.loads(xml)


def test_referencia_com_outros_atributos():
    xml = _desenho(ENT, '<ent ref="0" x="1"/>')
    with pytest.raises(ArquivoInvalidoError, match="'ref'"):
        io.loads(xml)


def test_caractere_de_controle_nao_aceito_pelo_xml(referencia):
    with pytest.raises(ArquivoInvalidoError, match="caractere"):
        io.loads((referencia / "amostra-caracteres-invalidos.xml").read_bytes())


def test_doctype_com_entidades_e_recusado():
    xml = '<!DOCTYPE drawing [<!ENTITY x "y">]>' + _desenho(ENT)
    with pytest.raises(ArquivoInvalidoError, match="DOCTYPE"):
        io.loads(xml)


def test_entidade_externa_nao_e_lida(tmp_path):
    segredo = tmp_path / "segredo.txt"
    segredo.write_text("CONTEUDO SECRETO")
    xml = f'<!DOCTYPE drawing [<!ENTITY x SYSTEM "file://{segredo}">]>' + _desenho(ENT)
    with pytest.raises(ArquivoInvalidoError):
        io.loads(xml)


def test_explosao_de_entidades_e_recusada():
    entidades = "".join(f'<!ENTITY e{i} "{f"&e{i - 1};" * 10}">' for i in range(1, 8))
    xml = f'<!DOCTYPE drawing [<!ENTITY e0 "lol">{entidades}]>' + _desenho(ENT)
    with pytest.raises(ArquivoInvalidoError):
        io.loads(xml)


def test_doctype_simples_e_aceito_e_ignorado():
    xml = '<!DOCTYPE drawing SYSTEM "x.dtd">' + _desenho(ENT)
    assert io.dumps(io.loads(xml)) == _desenho(ENT)


def test_aceita_declaracao_indentacao_e_utf8_direto():
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<drawing>\n  <figures>\n'
        '    <ent id="a"><children>\n      <r id="b" x="0" y="0" w="5" h="5"/>\n'
        '      <t id="c" x="0" y="0"><a><text><string>ção</string></text></a></t>\n'
        "    </children></ent>\n  </figures>\n</drawing>\n"
    )
    doc = io.loads(xml)
    assert doc.figures[0].name == "ção"
    # regravado no formato canônico: ids sequenciais, uma linha, ASCII
    assert io.dumps(doc).startswith('<drawing><figures><ent id="0"><children><r id="1"')
    assert "\n" not in io.dumps(doc)
    assert io.dumps(doc).isascii()


def test_id_ausente_ou_nao_hexadecimal_e_aceito():
    xml = _desenho('<ent id="zz"><children><r x="0" y="0" w="1" h="1"/></children></ent>')
    assert io.loads(xml).figures[0].tag == "ent"


def test_atributo_e_estilo_desconhecidos_sao_ignorados_na_leitura():
    xml = _desenho(ENT.replace('<ent id="0">', '<ent id="0" zzz="1">'))
    assert io.loads(xml).figures[0].name == "E"


def test_limite_de_profundidade():
    fundo = "<a>" * (reader.MAX_DEPTH + 5) + "</a>" * (reader.MAX_DEPTH + 5)
    with pytest.raises(ArquivoInvalidoError, match="aninhados"):
        reader.parse_xml(fundo)


def test_limite_de_tamanho(monkeypatch):
    monkeypatch.setattr(reader, "MAX_BYTES", 100)
    with pytest.raises(ArquivoInvalidoError, match="grande demais"):
        reader.parse_xml(_desenho(ENT))


def test_texto_misturado_com_elementos_e_recusado():
    with pytest.raises(ArquivoInvalidoError, match="mistura"):
        reader.parse_xml("<a>texto<b/></a>")
