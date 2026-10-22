"""Textos da verificação e da recomendação (RF-09, RF-10).

O núcleo dá códigos estáveis; quem os põe em palavras, no idioma escolhido, é a interface (D-09).
"""

from __future__ import annotations

from haradaer.core.rules import INCOMPLETE, INVALID_PAIR, Issue
from haradaer.core.rules.structure import (
    FEW_PARTICIPANTS,
    IDENTIFYING_WITHOUT_WEAK,
    INCOMPLETE_SPECIALIZATION,
    NO_KEY,
    ORPHAN_ATTRIBUTE,
    WEAK_WITHOUT_IDENTIFYING,
)
from haradaer.gui.palette import CONNECTIONS, ELEMENTS
from haradaer.i18n import N_, _

_NOMES = dict(ELEMENTS) | dict(CONNECTIONS) | {"g": N_("Grupo"), "lcf": N_("Ligação de atributo")}

_FALTANDO = {
    "ambas": N_("as duas pontas estão soltas"),
    "início": N_("a ponta de início está solta"),
    "fim": N_("a ponta de fim está solta"),
}


_AVISOS = {
    NO_KEY: N_("entidade sem atributo chave"),
    WEAK_WITHOUT_IDENTIFYING: N_("entidade fraca sem relacionamento identificador"),
    IDENTIFYING_WITHOUT_WEAK: N_("relacionamento identificador sem entidade fraca"),
    FEW_PARTICIPANTS: N_(
        "relacionamento com menos de dois participantes (no recursivo, ligue a entidade duas vezes)"
    ),
    INCOMPLETE_SPECIALIZATION: N_("especialização sem superclasse ou sem subclasse"),
    ORPHAN_ATTRIBUTE: N_("atributo sem ligação de atributo com um dono"),
}


def name_of(tag: str) -> str:
    return _(_NOMES.get(tag, tag))


def is_warning(issue: Issue) -> bool:
    """Aviso de estrutura (laranja), e não erro de conexão (vermelho)."""
    return issue.code in _AVISOS


def issue_text(issue: Issue) -> str:
    """O texto da dica no desenho."""
    if is_warning(issue):
        return _("Aviso: {aviso}").format(aviso=_(_AVISOS[issue.code]))
    return message_text(issue)


def message_text(issue: Issue) -> str:
    """O texto sem o "Aviso:" (no painel Mensagens, o tipo fica numa coluna própria)."""
    detalhes = issue.details
    conexao = name_of(detalhes.get("connection", issue.figure.tag))
    if issue.code == INCOMPLETE:
        falta = _FALTANDO.get(detalhes.get("missing", ""), N_("ponta solta"))
        return f"{conexao}: {_(falta)}"
    if issue.code == INVALID_PAIR:
        inicio, fim = name_of(detalhes["start"]), name_of(detalhes["end"])
        return _("{conexao} não é aceita entre {inicio} e {fim}").format(
            conexao=conexao, inicio=inicio, fim=fim
        )
    if is_warning(issue):
        return _(_AVISOS[issue.code])
    return conexao


def _contagem(n: int, singular: str, plural: str) -> str:
    return f"{n} {_(singular) if n == 1 else _(plural)}"


def _lista(nomes: list[str]) -> str:
    if len(nomes) == 1:
        return nomes[0]
    return _("{primeiros} e {ultimo}").format(primeiros=", ".join(nomes[:-1]), ultimo=nomes[-1])


def summary_text(problemas: list[Issue], avisos: list[Issue], nome) -> str:
    """Resumo da verificação para a barra de status; vazio se o modelo não tem nada.

    `nome(figura)` dá o nome de um elemento. Com até três avisos do mesmo tipo e nenhum erro,
    diz quais são ("2 avisos de estrutura: Entidade1 e Entidade2 (entidade sem atributo chave)").
    """
    if not problemas and not avisos:
        return ""
    if not problemas and len(avisos) <= 3 and len({a.code for a in avisos}) == 1:
        nomes = _lista([nome(a.figure) for a in avisos])
        contagem = _contagem(len(avisos), N_("aviso de estrutura"), N_("avisos de estrutura"))
        return f"{contagem}: {nomes} ({_(_AVISOS[avisos[0].code])})"
    partes = []
    if problemas:
        partes.append(_contagem(len(problemas), N_("erro de conexão"), N_("erros de conexão")))
    if avisos:
        partes.append(_contagem(len(avisos), N_("aviso de estrutura"), N_("avisos de estrutura")))
    return _("{partes} (veja o painel Mensagens)").format(partes=_(" e ").join(partes))


def pairs_text(pares: list[tuple[str, str]]) -> str:
    return ", ".join(f"{name_of(a)} → {name_of(b)}" for a, b in pares)
