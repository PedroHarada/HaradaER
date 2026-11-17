"""Avisos de estrutura: o que a teoria do modelo ER pede além de cada ligação."""

from haradaer.core.appearance import FixedMeasurer
from haradaer.core.commands import History, add_node_command, connect_command, new_node
from haradaer.core.model.document import Document
from haradaer.core.rules import check_structure
from haradaer.core.rules.structure import (
    FEW_PARTICIPANTS,
    IDENTIFYING_WITHOUT_WEAK,
    INCOMPLETE_SPECIALIZATION,
    NO_KEY,
    ORPHAN_ATTRIBUTE,
    WEAK_WITHOUT_IDENTIFYING,
)

MEDIDOR = FixedMeasurer()


class Modelo:
    def __init__(self):
        self.doc, self.h = Document.new(), History()

    def no(self, tag):
        figura = new_node(tag, 50 * len(self.doc.figures), 50, MEDIDOR)
        self.h.execute(add_node_command(self.doc, figura))
        return figura

    def liga(self, tipo, a, b):
        self.h.execute(connect_command(self.doc, tipo, a, b))

    def entidade(self, tag="ent"):
        """Entidade com chave (ou chave parcial, se fraca)."""
        figura = self.no(tag)
        self.liga("lcaf", self.no("atrchaveparcial" if tag == "entfraca" else "atrchave"), figura)
        return figura

    def avisos(self):
        return {(a.figure.tag, a.code) for a in check_structure(self.doc)}


def test_modelo_completo_nao_tem_aviso():
    m = Modelo()
    aluno, curso = m.entidade(), m.entidade()
    cursa = m.no("rel")
    m.liga("llabelMuitos", cursa, aluno)
    m.liga("llabelMuitos", cursa, curso)
    m.liga("lcaf", m.no("atr"), cursa)  # atributo do relacionamento
    dependente, tem = m.entidade("entfraca"), m.no("relfraco")
    m.liga("llabelUm", tem, aluno)
    m.liga("llabelDoubleMuitos", tem, dependente)
    assert m.avisos() == set()


def test_entidade_sem_chave():
    m = Modelo()
    aluno = m.no("ent")
    m.liga("lcaf", m.no("atr"), aluno)
    assert m.avisos() == {("ent", NO_KEY)}


def test_chave_composta_conta_como_chave():
    m = Modelo()
    carro, placa = m.no("ent"), m.no("atrchave")
    m.liga("lcaf", placa, carro)
    m.liga("lcaf", m.no("atr"), placa)
    m.liga("lcaf", m.no("atr"), placa)
    assert m.avisos() == set()


def test_quem_recebe_a_chave_de_outra_entidade_nao_tem_aviso():
    m = Modelo()
    pessoa, circulo = m.entidade(), m.no("disjuncao")
    aluno, professor = m.no("ent"), m.no("ent")  # subclasses: herdam a chave
    m.liga("llabelDoubleGeneralizacao", pessoa, circulo)
    m.liga("generalizacaoLine", circulo, aluno)
    m.liga("generalizacaoLine", circulo, professor)
    gerente = m.no("ent")
    m.liga("generalizacaoLine", pessoa, gerente)  # subclasse direta, sem círculo
    dono, uniao = m.no("ent"), m.no("uniao")  # categoria
    m.liga("llabelGeneralizacao", m.entidade(), uniao)
    m.liga("llabelGeneralizacao", m.entidade(), uniao)
    m.liga("generalizacaoLine", uniao, dono)
    associativa = m.no("entrel")  # a chave vem do relacionamento
    m.liga("llabelMuitos", associativa, m.no("rel"))
    assert NO_KEY not in {codigo for _, codigo in m.avisos()}


def test_entidade_fraca_sem_relacionamento_identificador():
    m = Modelo()
    dependente, rel = m.entidade("entfraca"), m.no("rel")
    m.liga("llabelMuitos", rel, dependente)
    m.liga("llabelUm", rel, m.entidade())
    assert m.avisos() == {("entfraca", WEAK_WITHOUT_IDENTIFYING)}


def test_relacionamento_identificador_sem_entidade_fraca():
    m = Modelo()
    tem = m.no("relfraco")
    m.liga("llabelUm", tem, m.entidade())
    m.liga("llabelMuitos", tem, m.entidade())
    assert m.avisos() == {("relfraco", IDENTIFYING_WITHOUT_WEAK)}


def test_relacionamento_precisa_de_dois_participantes_e_o_recursivo_conta_duas_vezes():
    m = Modelo()
    pessoa, sozinho, recursivo = m.entidade(), m.no("rel"), m.no("rel")
    m.liga("llabelUm", sozinho, pessoa)
    m.liga("llabelUm", recursivo, pessoa)  # supervisor
    m.liga("llabelMuitos", recursivo, pessoa)  # supervisionado
    vazio = m.no("rel")
    m.liga("lcaf", m.no("atr"), vazio)  # atributo não é participante
    avisos = [(a.figure, a.code) for a in check_structure(m.doc)]
    assert avisos == [(sozinho, FEW_PARTICIPANTS), (vazio, FEW_PARTICIPANTS)]


def test_especializacao_sem_superclasse_ou_sem_subclasse():
    m = Modelo()
    sem_sub = m.no("sobreposicao")
    m.no("uniao")  # sem nada ligado
    m.liga("llabelGeneralizacao", m.entidade(), sem_sub)
    assert m.avisos() == {
        ("sobreposicao", INCOMPLETE_SPECIALIZATION),
        ("uniao", INCOMPLETE_SPECIALIZATION),
    }


def test_atributo_sem_dono_e_parte_de_composto_tem_dono():
    m = Modelo()
    aluno, endereco = m.entidade(), m.no("atr")
    m.liga("lcaf", endereco, aluno)
    m.liga("lcaf", m.no("atr"), endereco)  # rua: dono é o endereço
    m.no("atrderivado")  # solto
    m.liga("llabelUm", m.no("atrmulti"), aluno)  # participação não é ligação de atributo
    assert m.avisos() == {("atrderivado", ORPHAN_ATTRIBUTE), ("atrmulti", ORPHAN_ATTRIBUTE)}
