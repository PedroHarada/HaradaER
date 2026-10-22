"""Ícones da barra de ferramentas, desenhados com as mesmas regras do diagrama.

Cada ícone é um pedacinho de diagrama de verdade (um elemento recém-criado, ou duas formas
ligadas pela conexão), reduzido para caber no botão. Nada vem das imagens do TerraER (RNF-13).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from haradaer.core.appearance import describe_figure
from haradaer.core.appearance.describe import font_of
from haradaer.core.appearance.ops import DrawOp
from haradaer.core.appearance.style import Style
from haradaer.core.figures.factory import create_connection, create_node, text_position
from haradaer.core.geometry import node_rect
from haradaer.core.model.element import Element
from haradaer.core.xmlfmt.numbers import format_number
from haradaer.gui.qt_utils import QtMeasurer
from haradaer.gui.scene.items import ink_op, op_bounds, paint_op
from haradaer.gui.theme import current_theme
from haradaer.i18n import N_

ICON_SIZE = QSize(40, 26)
_ESCALA_TELA = 2  # desenha com o dobro de pixels, para ficar nítido em telas de alta densidade

# Nome curto que aparece embaixo do ícone (o nome completo fica na dica).
SHORT_NAMES = {
    "ent": N_("Entidade"),
    "entfraca": N_("Ent. fraca"),
    "rel": N_("Relacion."),
    "relfraco": N_("Rel. fraco"),
    "entrel": N_("Ent. assoc."),
    "atr": N_("Atributo"),
    "atrchave": N_("Chave"),
    "atrchaveparcial": N_("Ch. parcial"),
    "atrderivado": N_("Derivado"),
    "atrmulti": N_("Multival."),
    "uniao": N_("União"),
    "disjuncao": N_("Disjunção"),
    "sobreposicao": N_("Sobrepos."),
    "llabelUm": N_("Lado 1"),
    "llabelMuitos": N_("Lado N"),
    "llabelDoubleUm": N_("Total 1"),
    "llabelDoubleMuitos": N_("Total N"),
    "lcaf": N_("Lig. atrib."),
    "generalizacaoLine": N_("General."),
    "llabelGeneralizacao": N_("Gen. opc."),
    "llabelDoubleGeneralizacao": N_("Gen. obrig."),
    "llabel": N_("Livre"),
}

_ATRIBUTOS = ("atr", "atrchave", "atrchaveparcial", "atrderivado", "atrmulti")
_CIRCULOS = ("uniao", "disjuncao", "sobreposicao")

# De que forma sai e onde chega cada conexão no ícone: mostra para que ela serve.
_PONTAS = {
    "lcaf": ("atr", "ent"),
    "generalizacaoLine": ("uniao", "ent"),
    "llabelGeneralizacao": ("disjuncao", "ent"),
    "llabelDoubleGeneralizacao": ("sobreposicao", "ent"),
    "llabel": ("ent", "ent"),
}

_medidor = QtMeasurer()


def _blank() -> QPixmap:
    imagem = QPixmap(ICON_SIZE.width() * _ESCALA_TELA, ICON_SIZE.height() * _ESCALA_TELA)
    imagem.setDevicePixelRatio(_ESCALA_TELA)
    imagem.fill(Qt.GlobalColor.transparent)
    return imagem


def _render(ops: list[DrawOp]) -> QIcon:
    """Desenha as operações centralizadas e reduzidas para caber no ícone. As linhas e os textos
    soltos seguem o tema (no escuro, ficam claros para aparecer sobre a barra)."""
    tinta = current_theme().ink
    largura, altura = ICON_SIZE.width(), ICON_SIZE.height()
    imagem = _blank()
    area = QRectF()
    for op in ops:
        area = area.united(op_bounds(op))
    if area.isEmpty():
        return QIcon(imagem)
    margem = 1.5
    escala = min((largura - 2 * margem) / area.width(), (altura - 2 * margem) / area.height())
    painter = QPainter(imagem)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.translate(largura / 2, altura / 2)
    painter.scale(escala, escala)
    painter.translate(-area.center())
    for op in ops:
        paint_op(painter, ink_op(op, tinta, textos=False))
    painter.end()
    return QIcon(imagem)


def _reshape(no: Element, x: float, y: float, largura: float, altura: float) -> None:
    """Põe as formas do elemento no retângulo dado (só para o ícone) e recentraliza o texto."""
    grupo = no.child("children")
    for parte in grupo.children if grupo else []:
        if parte.tag in ("r", "diamond", "e", "circ"):
            parte.attrs.update(
                x=format_number(x),
                y=format_number(y),
                w=format_number(largura),
                h=format_number(altura),
            )
        elif parte.tag in ("t", "tn"):
            texto = Style.of(parte).string("text", "") or ""
            medida = _medidor.size(texto, font_of(parte))
            px, py = text_position((x, y, largura, altura), medida)
            parte.attrs.update(x=format_number(px), y=format_number(py))


def element_icon(tag: str) -> QIcon:
    """O elemento como aparece ao ser criado. Atributos ganham um nome curto ("id") e uma elipse
    menos achatada, para o sublinhado da chave aparecer."""
    nome = None if tag in _CIRCULOS else ("id" if tag in _ATRIBUTOS else "")
    no = create_node(tag, 0, 0, _medidor, nome)
    if tag in _ATRIBUTOS:
        _reshape(no, 0, 0, 56, 30)
    return _render(describe_figure(no, _medidor))


def connection_icon(tag: str) -> QIcon:
    """A conexão entre duas formas pequenas, com a linha longa para o 1/N aparecer. O rótulo da
    generalização ("característica") não cabe e fica de fora."""
    origem_tag, destino_tag = _PONTAS.get(tag, ("rel", "ent"))
    origem = create_node(origem_tag, 0, 0, _medidor, "")
    destino = create_node(destino_tag, 0, 0, _medidor, "")
    if origem_tag in _CIRCULOS:
        _reshape(origem, 0, 0, 10, 10)
    else:
        _reshape(origem, 0, 0, 14, 9)
    _reshape(destino, 40, 10, 14, 9)
    rect_o, rect_d = node_rect(origem), node_rect(destino)
    assert rect_o is not None and rect_d is not None
    conexao = create_connection(tag, origem, destino, rect_o, rect_d)
    conexao.attrs.pop("labelGeneralizacaoText", None)
    ops: list[DrawOp] = []
    for figura in (origem, destino):
        ops.extend(describe_figure(figura, _medidor))
    tinta = current_theme().ink  # o rótulo 1/N fica sobre a barra: segue o tema
    ops.extend(ink_op(op, tinta) for op in describe_figure(conexao, _medidor))
    return _render(ops)


def select_icon() -> QIcon:
    """Seta do mouse."""
    imagem = _blank()
    painter = QPainter(imagem)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    seta = QPainterPath(QPointF(15, 2))
    for x, y in ((15, 21), (19.5, 16.5), (23, 24), (26, 22.5), (22.5, 15.5), (28.5, 15.5)):
        seta.lineTo(x, y)
    seta.closeSubpath()
    painter.setPen(QPen(QColor("black"), 1.2))
    painter.setBrush(QColor("white"))
    painter.drawPath(seta)
    painter.end()
    return QIcon(imagem)
