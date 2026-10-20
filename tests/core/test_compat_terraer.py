"""RNF-01: o que o HaradaER cria, o TerraER abre e regrava sem mudar o modelo.

`criados-no-haradaer/todos-os-tipos.xml` foi feito pelos comandos de edição do HaradaER
(`harness/gera_no_haradaer.py`); `regravado-pelo-terraer.xml` é o que o próprio TerraER 3.14
gravou depois de ler esse arquivo (`harness/RegravaTerra.java`).
"""

import pytest

from haradaer.core import io
from haradaer.core.appearance.style import Style
from haradaer.core.figures.types import ConnectionFigure, NodeFigure
from haradaer.core.geometry import node_rect


@pytest.fixture
def criado(referencia):
    return (referencia / "criados-no-haradaer" / "todos-os-tipos.xml").read_bytes()


@pytest.fixture
def regravado(referencia):
    return (referencia / "criados-no-haradaer" / "regravado-pelo-terraer.xml").read_bytes()


def nos_e_ligacoes(doc):
    """Elementos e conexões, sem os detalhes de gravação (ids, ordem do estilo, última casa)."""
    indice = {id(f): i for i, f in enumerate(doc.figures)}
    nos, ligacoes = [], []
    for figura in doc.figures:
        if isinstance(figura, NodeFigure):
            nos.append((figura.tag, figura.name, figura.attribute_type, figura.nullable))
            nos[-1] += (node_rect(figura),)
        elif isinstance(figura, ConnectionFigure):
            pontos = [float(p.attrs[eixo]) for p in figura.points for eixo in ("x", "y")]
            ligacoes.append(
                (
                    figura.tag,
                    indice[id(figura.start)],
                    indice[id(figura.end)],
                    figura.generalization_label,
                    pontos,
                )
            )
    return nos, ligacoes


def test_o_terraer_le_e_regrava_o_mesmo_modelo(criado, regravado):
    nossos_nos, nossas_ligacoes = nos_e_ligacoes(io.loads(criado))
    nos_dele, ligacoes_dele = nos_e_ligacoes(io.loads(regravado))

    assert len(nossos_nos) == len(nos_dele) == 13
    for nosso, dele in zip(nossos_nos, nos_dele, strict=True):
        assert nosso[:4] == dele[:4]
        assert nosso[4] == pytest.approx(dele[4], abs=1e-6)

    assert len(nossas_ligacoes) == len(ligacoes_dele) == 13
    for nossa, dela in zip(nossas_ligacoes, ligacoes_dele, strict=True):
        assert nossa[:4] == dela[:4]
        # O TerraER liga a linha à caixa que inclui o texto. Só no círculo da generalização o
        # texto (fonte 16) passa da forma, então a ponta difere em menos de 2 unidades
        # (INVESTIGACOES.md, seção 14); o TerraER recalcula as pontas ao abrir o arquivo.
        folga = (
            2.0 if nossa[0].endswith("Generalizacao") or nossa[0] == "generalizacaoLine" else 1e-6
        )
        assert nossa[4] == pytest.approx(dela[4], abs=folga)


def test_conexoes_repetidas_e_letras_sobrevivem_ao_terraer(referencia):
    """Três conexões "N" e uma "1" entre os mesmos elementos, criadas no HaradaER e regravadas
    pelo TerraER: as letras (N, M, P) e os desvios voltam iguais."""
    pasta = referencia / "criados-no-haradaer"
    nosso = io.loads((pasta / "paralelas.xml").read_bytes())
    dele = io.loads((pasta / "paralelas-regravado-pelo-terraer.xml").read_bytes())
    _, nossas = nos_e_ligacoes(nosso)
    _, delas = nos_e_ligacoes(dele)
    assert [Style.of(c).string("text") for c in nosso.figures if c.tag.startswith("llabel")] == [
        "N",
        "M",
        "P",
        None,
    ]
    assert len(nossas) == len(delas) == 4
    for nossa, dela in zip(nossas, delas, strict=True):
        assert nossa[:4] == dela[:4]
        assert nossa[4] == pytest.approx(dela[4], abs=1e-6)
    textos = [Style.of(c).string("text") for c in dele.figures if c.tag.startswith("llabel")]
    assert textos == ["N", "M", "P", None]
