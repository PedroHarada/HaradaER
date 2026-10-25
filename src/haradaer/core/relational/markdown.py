"""O esquema lógico em Markdown básico, que o GitHub e o GitLab mostram igual (RF-23).

Notação de Elmasri e Navathe: `RELACAO (chave, atributo, ...)`, com a chave primária em negrito
(o Markdown básico não tem sublinhado) e as chaves estrangeiras listadas abaixo da relação.
"""

from __future__ import annotations

from collections.abc import Callable

from haradaer.core.relational.schema import Relation, Schema
from haradaer.core.rules.validation import Issue
from haradaer.i18n import _


def _escape(texto: str) -> str:
    """Sem os caracteres que o Markdown leria como formatação (o `_` no meio da palavra não
    vira itálico no GitHub nem no GitLab, e fica)."""
    for caractere in ("\\", "*", "`"):
        texto = texto.replace(caractere, "\\" + caractere)
    return texto


def _code(texto: str) -> str:
    texto = " ".join(texto.split())
    marca = "``" if "`" in texto else "`"
    return f"{marca} {texto} {marca}" if marca == "``" else f"`{texto}`"


def relation_line(relacao: Relation) -> str:
    colunas = [
        f"**{_escape(c.name)}**" if c.name in relacao.primary_key else _escape(c.name)
        for c in relacao.columns
    ]
    return f"{_escape(relacao.name)} ({', '.join(colunas)})"


def schema_markdown(
    schema: Schema,
    modelo: str,
    arquivo: str | None,
    gerado_em: str,
    descrever: Callable[[Issue], str],
) -> str:
    """O texto do `.esquema.md` (e do painel). `descrever` põe um aviso em palavras: a
    interface faz isso, porque o núcleo só dá códigos (D-09)."""
    linhas = [f"# {_('Esquema lógico relacional')} — {_escape(modelo)}", ""]
    if arquivo:
        linhas.append(
            _("Gerado pelo HaradaER a partir de `{arquivo}` em {quando}.").format(
                arquivo=arquivo, quando=gerado_em
            )
        )
    else:
        linhas.append(
            _("Gerado pelo HaradaER a partir de um modelo não salvo em {quando}.").format(
                quando=gerado_em
            )
        )
    linhas += [
        _("Não edite este arquivo: ele é refeito a partir do diagrama."),
        "",
        _(
            "Notação de Elmasri e Navathe, *Sistemas de Banco de Dados*. Chave primária em "
            "**negrito**; chaves estrangeiras listadas abaixo de cada relação."
        ),
        "",
        f"## {_('Relações')}",
        "",
    ]
    if not schema.relations:
        linhas += [_("Nenhuma."), ""]
    for relacao in schema.relations:
        linhas.append(relation_line(relacao))
        if relacao.foreign_keys:
            linhas.append("")
        for estrangeira in relacao.foreign_keys:
            de = ", ".join(_escape(c) for c in estrangeira.columns)
            para = ", ".join(_escape(c) for c in estrangeira.referenced)
            linhas.append(f"- {de} → {_escape(estrangeira.relation)} ({para})")
        linhas.append("")
    linhas += [f"## {_('Atributos derivados')}", ""]
    if schema.derived:
        linhas += [_("Não viram colunas: são calculados a partir das outras relações."), ""]
        for derivado in schema.derived:
            instrucao = _code(derivado.sql) if derivado.sql else _("sem instrução SQL")
            linhas.append(
                _("- {atributo}, de {dono}: {sql}").format(
                    atributo=_escape(derivado.name), dono=_escape(derivado.owner), sql=instrucao
                )
            )
    else:
        linhas.append(_("Nenhum."))
    linhas += ["", f"## {_('Avisos')}", ""]
    if schema.issues:
        linhas += [f"- {_escape(descrever(aviso))}" for aviso in schema.issues]
    else:
        linhas.append(_("Nenhum."))
    return "\n".join(linhas) + "\n"
