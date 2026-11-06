"""Texto (RF-26) e a conversão dos textos soltos do TerraER (RF-27).

O Texto é a Área de Texto do TerraER (`ta`): uma caixa com texto de várias linhas, que quebra pela
largura. A largura só muda quando o usuário redimensiona; a altura cresce para caber o texto e
nunca encolhe sozinha.

O TerraER tem mais três textos soltos (`t`, `ti` Papel e `tn` negrito). O HaradaER só tem o Texto:
ao abrir ou colar, cada um deles vira um Texto no mesmo lugar, com o mesmo texto e a mesma fonte.
As partes de texto que dão nome a um elemento ER não mudam.
"""

from __future__ import annotations

from haradaer.core.appearance.describe import TEXT_AREA_INSET, font_of, text_area_layout
from haradaer.core.appearance.markdown import escape_literal
from haradaer.core.appearance.metrics import TextMeasurer
from haradaer.core.commands.edit import InsertFigure, SetAttr, SetChildren, SetText
from haradaer.core.commands.history import Command, Composite
from haradaer.core.figures.factory import TEXT_AREA, bool_entry, create_text_area
from haradaer.core.figures.types import SupportFigure
from haradaer.core.geometry import Rect, part_rect
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import format_number
from haradaer.i18n import N_

FREE_TEXT_TAGS = ("t", "tn", "ti")
TEXT_AREA_MIN_WIDTH = 4 * TEXT_AREA_INSET

# O negrito do `tn` e o itálico do Papel (`ti`) vêm da tag; no Texto eles viram estilo.
_TAG_FONT = {"tn": "fontBold", "ti": "fontItalic"}


def is_text_area(figura: Element | None) -> bool:
    return figura is not None and figura.tag == TEXT_AREA


def text_of(texto: Element) -> str:
    """O texto de um Texto (vazio se não houver)."""
    for estilo in texto.children_named("a"):
        entrada = estilo.child("text")
        valor = entrada.child("string") if entrada else None
        if valor is not None:
            return valor.text or ""
    return ""


def text_area_rect(texto: Element) -> Rect:
    return part_rect(texto)


def needed_height(texto: Element, conteudo: str, largura: float, medidor: TextMeasurer) -> float:
    """A altura que a caixa precisa, nessa largura, para mostrar todo o conteúdo."""
    return text_area_layout(conteudo, font_of(texto), largura, medidor)[1]


def min_text_area_size(texto: Element, medidor: TextMeasurer) -> tuple[float, float]:
    """Menor caixa ao redimensionar, na largura atual (a altura é refeita para a largura nova)."""
    largura = part_rect(texto)[2]
    return (TEXT_AREA_MIN_WIDTH, needed_height(texto, text_of(texto), largura, medidor))


def _grow(
    documento: Document, texto: Element, rect: Rect, conteudo: str, medidor: TextMeasurer
) -> list[Command]:
    """Dá ao Texto a caixa `rect`, com a altura crescida se o conteúdo não couber."""
    x, y, w, h = rect
    w = max(w, TEXT_AREA_MIN_WIDTH)
    h = max(h, needed_height(texto, conteudo, w, medidor))
    comandos: list[Command] = []
    for nome, valor in zip(("x", "y", "w", "h"), (x, y, w, h), strict=True):
        novo = format_number(valor)
        if texto.attrs.get(nome) != novo:
            comandos.append(SetAttr(documento, texto, texto, nome, novo))
    return comandos


def add_text_area_command(
    documento: Document, rect: Rect, conteudo: str, medidor: TextMeasurer
) -> tuple[Command, SupportFigure]:
    """Cria um Texto na caixa dada; a altura cresce se o conteúdo não couber."""
    x, y, w, h = rect
    w = max(w, TEXT_AREA_MIN_WIDTH)
    texto = create_text_area(x, y, w, h, conteudo)
    h = max(h, needed_height(texto, conteudo, w, medidor))
    texto.attrs["h"] = format_number(h)
    comando = InsertFigure(documento, texto)
    comando.label = N_("Criar texto")
    return comando, texto


def set_text_command(
    documento: Document, texto: Element, conteudo: str, medidor: TextMeasurer
) -> Command:
    """Troca o conteúdo; a altura cresce para caber, a largura fica."""
    comandos: list[Command] = []
    string = None
    for estilo in texto.children_named("a"):
        entrada = estilo.child("text")
        if entrada is not None and entrada.child("string") is not None:
            string = entrada.child("string")
            break
    if string is not None:
        comandos.append(SetText(documento, texto, string, conteudo))
    else:  # Área de Texto vazia do TerraER: ainda não tem a entrada do texto
        novo = create_text_area(0, 0, 0, 0, conteudo).children
        comandos.append(SetChildren(documento, texto, texto, [*texto.children, *novo]))
    comandos.extend(_grow(documento, texto, part_rect(texto), conteudo, medidor))
    return Composite(comandos, N_("Editar texto"))


def resize_text_area_command(
    documento: Document, texto: Element, rect: Rect, medidor: TextMeasurer
) -> Command:
    """Dá ao Texto a caixa pedida; se o texto não couber na largura nova, a altura cresce."""
    return Composite(_grow(documento, texto, rect, text_of(texto), medidor), N_("Redimensionar"))


def all_text_areas(documento: Document) -> list[Element]:
    """Os Textos do desenho, inclusive os de dentro de grupos, na ordem do desenho."""
    achados: list[Element] = []

    def visitar(figuras: list[Element]) -> None:
        for figura in figuras:
            if is_text_area(figura):
                achados.append(figura)
            elif figura.tag == "g":
                grupo = figura.child("children")
                visitar(grupo.children if grupo else [])

    visitar(documento.figures)
    return achados


def _converted(solto: Element, medidor: TextMeasurer) -> SupportFigure:
    """O Texto que substitui um texto solto, com o texto no mesmo lugar."""
    fonte = font_of(solto)
    entradas = [e for bloco in solto.children_named("a") for e in bloco.children]
    marca = _TAG_FONT.get(solto.tag)
    if marca is not None and not any(e.tag == marca for e in entradas):
        # O TerraER grava o texto por último no estilo (conferido regravando pelo TerraER).
        textos = [i for i, e in enumerate(entradas) if e.tag == "text"]
        entradas.insert(textos[0] if textos else len(entradas), bool_entry(marca))
    conteudo = original_text(solto)
    entradas = [_escaped(e) for e in entradas]
    x, y = part_rect(solto)[:2]
    linhas = conteudo.split("\n")
    largura = max(medidor.size(linha, fonte)[0] for linha in linhas) + 2 * TEXT_AREA_INSET + 1
    largura = max(largura, TEXT_AREA_MIN_WIDTH)
    texto = create_text_area(x - TEXT_AREA_INSET, y - TEXT_AREA_INSET, largura, 0, "", entradas)
    texto.attrs["h"] = format_number(needed_height(texto, text_of(texto), largura, medidor))
    return texto


def original_text(solto: Element) -> str:
    """O texto de um texto solto do TerraER, como ele o mostra."""
    return text_of(solto)


def _escaped(entrada: Element) -> Element:
    """A entrada do texto com os caracteres de Markdown escapados, só onde mudariam a aparência
    (RF-28): o Texto mostra o mesmo que o texto solto mostrava."""
    valor = entrada.child("string") if entrada.tag == "text" else None
    if valor is None or not valor.text:
        return entrada
    escapado = escape_literal(valor.text)
    if escapado == valor.text:
        return entrada
    return Element("text", children=[Element("string", text=escapado)])


def convert_free_texts(documento: Document, medidor: TextMeasurer) -> list[tuple[str, str]]:
    """RF-27: troca cada texto solto (`t`, `tn`, `ti`), também dentro de grupos, por um Texto.

    Devolve (tag original, texto) de cada um, na ordem do desenho. Os nomes dos elementos ER
    (partes de texto dentro deles) não são tocados.
    """
    convertidos: list[tuple[str, str]] = []

    def trocar(lista: list[Element]) -> None:
        for i, figura in enumerate(lista):
            if figura.tag in FREE_TEXT_TAGS:
                novo = _converted(figura, medidor)
                lista[i] = novo
                convertidos.append((figura.tag, original_text(figura)))
            elif figura.tag == "g":
                grupo = figura.child("children")
                if grupo is not None:
                    trocar(grupo.children)

    trocar(documento.figures)
    return convertidos
