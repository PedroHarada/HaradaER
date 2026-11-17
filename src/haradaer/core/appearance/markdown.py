"""O Markdown do Texto (RF-28): o que o conteúdo de uma Área de Texto quer dizer.

A leitura é a do markdown-it-py, no modo CommonMark (0.31.2), com só uma parte ligada: títulos
`#`, ênfase, listas, código, links (`[texto](url)`, `<url>` e por referência) e escapes, mais as
listas de tarefas do GitHub (`- [x]`). Imagens, citações, tabelas, linha separadora, títulos
sublinhados e HTML ficam como texto literal. Desvio declarado: cada Enter é uma linha nova (a
opção `breaks`) e as linhas em branco aparecem como foram digitadas, não juntas numa só.

O resultado são blocos (título, parágrafo, código, linha em branco) com pedaços de texto e o seu
estilo; quem mede e desenha é `describe.py`.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from functools import lru_cache

from markdown_it import MarkdownIt

# Fora do HaradaER: viram texto literal (lheading é o título sublinhado com === ou ---). A
# imagem continua ligada só para não virar "!" seguido de um link: ela é mostrada como escrita.
_DESLIGADAS = ["blockquote", "hr", "lheading", "html_block", "html_inline"]

BULLETS = ("•", "◦", "▪")  # do primeiro nível em diante


@dataclass(frozen=True)
class Run:
    """Um pedaço de texto com o seu estilo; `text == "\\n"` é uma quebra de linha."""

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str | None = None  # destino do link


@dataclass
class Block:
    kind: str  # "heading", "paragraph", "code" ou "blank"
    runs: list[Run] = field(default_factory=list)
    level: int = 0  # nível do título (1 a 6)
    depth: int = 0  # em quantas listas o bloco está
    marker: str | None = None  # marcador do item ("•", "3."), só no primeiro bloco do item
    task: bool | None = None  # item de tarefa: marcado ou não (o marcador vira uma caixinha)
    line: int = 0  # linha do texto onde o item começa (para marcar a tarefa pelo desenho)


@lru_cache(maxsize=1)
def _parser() -> MarkdownIt:
    return MarkdownIt("commonmark", {"breaks": True, "tasklists": True}).disable(_DESLIGADAS)


def _image_source(token) -> str:
    """A imagem como foi escrita (o leitor já a desmontou): `![legenda](arquivo "título")`."""
    titulo = token.attrGet("title")
    extra = f' "{titulo}"' if titulo else ""
    return f"![{token.content}]({token.attrGet('src') or ''}{extra})"


def _runs(filhos) -> list[Run]:
    runs: list[Run] = []
    negrito = italico = 0
    link: str | None = None
    for token in filhos or []:
        tipo = token.type
        if tipo == "link_open":
            link = str(token.attrGet("href") or "")
        elif tipo == "link_close":
            link = None
        elif tipo == "image":
            runs.append(Run(_image_source(token), negrito > 0, italico > 0))
        elif tipo == "strong_open":
            negrito += 1
        elif tipo == "strong_close":
            negrito -= 1
        elif tipo == "em_open":
            italico += 1
        elif tipo == "em_close":
            italico -= 1
        elif tipo in ("softbreak", "hardbreak"):
            runs.append(Run("\n"))
        elif tipo == "code_inline":
            runs.append(Run(token.content, code=True, link=link))
        elif token.content:
            runs.append(Run(token.content, negrito > 0, italico > 0, link=link))
    return runs


@lru_cache(maxsize=256)
def _parse(texto: str) -> tuple[Block, ...]:
    blocos: list[Block] = []
    fontes = texto.split("\n")
    fim_anterior = 0  # linha do texto onde terminou o último bloco
    listas: list[list] = []  # pilha: [ordenada, próximo número]
    marcador: str | None = None
    tarefa: bool | None = None
    linha_do_item = 0
    titulo = 0

    def acompanhar(mapa) -> None:
        nonlocal fim_anterior
        if mapa is None:
            return
        for linha in fontes[fim_anterior : mapa[0]]:  # as linhas em branco digitadas
            if not linha.strip():  # (a definição de um link por referência some, como manda)
                blocos.append(Block("blank"))
        fim_anterior = max(fim_anterior, mapa[1])

    def novo(tipo: str, runs: list[Run], **extra) -> None:
        nonlocal marcador, tarefa
        blocos.append(
            Block(
                tipo,
                runs,
                depth=len(listas),
                marker=marcador,
                task=tarefa,
                line=linha_do_item,
                **extra,
            )
        )
        marcador = tarefa = None

    for token in _parser().parse(texto):
        tipo = token.type
        if tipo in ("bullet_list_open", "ordered_list_open"):
            inicio = int(token.attrGet("start") or 1) if tipo == "ordered_list_open" else 0
            listas.append([tipo == "ordered_list_open", inicio])
        elif tipo in ("bullet_list_close", "ordered_list_close"):
            listas.pop()
        elif tipo == "list_item_open":
            ordenada, numero = listas[-1]
            tarefa = bool(token.meta["checked"]) if token.meta and "checked" in token.meta else None
            linha_do_item = token.map[0] if token.map else 0
            if ordenada:
                marcador = f"{numero}{token.markup or '.'}"
                listas[-1][1] += 1
            else:
                marcador = BULLETS[min(len(listas), len(BULLETS)) - 1]
        elif tipo == "heading_open":
            acompanhar(token.map)
            titulo = int(token.tag[1])
        elif tipo == "paragraph_open":
            acompanhar(token.map)
        elif tipo == "inline":
            if titulo:
                novo("heading", _runs(token.children), level=titulo)
                titulo = 0
            else:
                novo("paragraph", _runs(token.children))
        elif tipo in ("fence", "code_block"):
            acompanhar(token.map)
            novo("code", [Run(token.content.removesuffix("\n"), code=True)])
    if texto:
        for linha in fontes[fim_anterior:]:
            if not linha.strip():
                blocos.append(Block("blank"))
    return tuple(blocos)


def parse(texto: str) -> list[Block]:
    """Os blocos do texto, na ordem, com as linhas em branco digitadas."""
    return list(_parse(texto))


def plain_text(texto: str) -> str:
    """O texto como aparece, sem os marcadores (para o Localizar)."""
    linhas = []
    for bloco in _parse(texto):
        linhas.append("".join(run.text for run in bloco.runs))
    return "\n".join(linhas)


def _literal(texto: str, original: str) -> bool:
    """O texto aparece exatamente como `original`, sem formatação nenhuma."""
    for bloco in _parse(texto):
        if bloco.kind in ("heading", "code") or bloco.marker is not None or bloco.depth:
            return False
        if any(run.bold or run.italic or run.code or run.link is not None for run in bloco.runs):
            return False
    return plain_text(texto) == original


_ESPECIAIS = "\\`*_#~[<"
_INICIO_DE_LINHA = "-+>"


def _escape_some(texto: str) -> str:
    """Escapa os marcadores de ênfase e código, e o que abre lista ou título no começo da linha."""
    linhas = []
    for linha in texto.split("\n"):
        saida = "".join("\\" + c if c in _ESPECIAIS else c for c in linha)
        recuo = len(saida) - len(saida.lstrip(" "))
        resto = saida[recuo:]
        if resto[:1] in _INICIO_DE_LINHA:
            resto = "\\" + resto
        else:
            digitos = len(resto) - len(resto.lstrip(string.digits))
            if digitos and resto[digitos : digitos + 1] in (".", ")"):
                resto = resto[:digitos] + "\\" + resto[digitos:]
        linhas.append(saida[:recuo] + resto)
    return "\n".join(linhas)


def escape_literal(texto: str) -> str:
    """O texto escrito de modo que o Markdown o mostre exatamente como é (RF-27 com o RF-28).

    Só escapa se for preciso, e o mínimo: um texto comum volta igual."""
    if _literal(texto, texto):
        return texto
    escapado = _escape_some(texto)
    if _literal(escapado, texto):
        return escapado
    return "".join("\\" + c if c in string.punctuation else c for c in texto)


_TAREFA = re.compile(r"^(\s*(?:[-+*]|\d{1,9}[.)])[ \t]+)\[([ xX])\]")


def toggle_task(texto: str, linha: int) -> str:
    """Marca ou desmarca a tarefa que começa nessa linha: `[ ]` vira `[x]` e o contrário."""
    linhas = texto.split("\n")
    if not 0 <= linha < len(linhas):
        return texto
    achado = _TAREFA.match(linhas[linha])
    if achado is None:
        return texto
    novo = " " if achado.group(2) in "xX" else "x"
    inicio = achado.start(2)
    linhas[linha] = linhas[linha][:inicio] + novo + linhas[linha][inicio + 1 :]
    return "\n".join(linhas)
