"""Leitura do `.xml` do TerraER.

Usa o `expat` da biblioteca padrão com as proteções do RNF-10 e as regras de leitura que o
TerraER tem (RNF-14, RNF-15):

- `DOCTYPE` é aceito e ignorado, mas um com subconjunto interno (onde se declaram entidades)
  é recusado;
- não se resolvem entidades externas;
- há limite de tamanho e de profundidade;
- `id` repetido ou `ref` para id inexistente são erros, como no TerraER;
- referências a surrogates (`&#xd83d;&#xde00;`, como o TerraER grava emojis) são juntadas num único
  caractere antes do parse.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from xml.parsers import expat

from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.model.element import Element

MAX_BYTES = 64 * 1024 * 1024
MAX_DEPTH = 200

_PAR_DE_SURROGATES = re.compile(
    rb"&#[xX](d[89abAB][0-9a-fA-F]{2});&#[xX](d[c-fC-F][0-9a-fA-F]{2});"
)

_MENSAGENS = {
    expat.errors.XML_ERROR_NO_ELEMENTS: "o arquivo está vazio ou foi cortado antes do fim",
    expat.errors.XML_ERROR_UNCLOSED_TOKEN: "o arquivo foi cortado no meio de um elemento",
    expat.errors.XML_ERROR_TAG_MISMATCH: "uma tag foi aberta e fechada com nomes diferentes",
    expat.errors.XML_ERROR_JUNK_AFTER_DOC_ELEMENT: "há conteúdo depois do fim do desenho",
    expat.errors.XML_ERROR_UNDEFINED_ENTITY: "o arquivo usa uma entidade não definida",
    expat.errors.XML_ERROR_BAD_CHAR_REF: (
        "o texto contém um caractere que o XML não aceita (por exemplo um caractere de controle)"
    ),
    expat.errors.XML_ERROR_SYNTAX: "o XML tem um erro de sintaxe",
    expat.errors.XML_ERROR_INVALID_TOKEN: "o XML tem um caractere ou símbolo inválido",
}


def _juntar_surrogates(dados: bytes) -> bytes:
    def trocar(m: re.Match[bytes]) -> bytes:
        alto, baixo = int(m.group(1), 16), int(m.group(2), 16)
        codigo = 0x10000 + ((alto - 0xD800) << 10) + (baixo - 0xDC00)
        return b"&#x%x;" % codigo

    return _PAR_DE_SURROGATES.sub(trocar, dados)


class _Leitor:
    def __init__(self, classe_para_tag: Callable[[str], type[Element]]):
        self._classe_para_tag = classe_para_tag
        self._ids: dict[str, Element] = {}
        # cada item: [elemento, é_referência, pedaços_de_texto]
        self._pilha: list[list] = []
        self.raiz: Element | None = None
        self.parser = expat.ParserCreate()
        self.parser.ordered_attributes = True
        self.parser.buffer_text = True
        self.parser.StartElementHandler = self._inicio
        self.parser.EndElementHandler = self._fim
        self.parser.CharacterDataHandler = self._texto
        self.parser.StartDoctypeDeclHandler = self._doctype
        self.parser.EntityDeclHandler = self._entidade
        self.parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)

    @property
    def _linha(self) -> int:
        return self.parser.CurrentLineNumber

    def _doctype(self, nome, sistema, publico, tem_subconjunto_interno):
        if tem_subconjunto_interno:
            raise ArquivoInvalidoError(
                "o arquivo declara entidades no DOCTYPE, o que não é aceito por segurança",
                self._linha,
            )

    def _entidade(self, *_args):
        raise ArquivoInvalidoError("declaração de entidade não é aceita por segurança", self._linha)

    def _inicio(self, nome: str, lista_attrs: list[str]) -> None:
        if len(self._pilha) >= MAX_DEPTH:
            raise ArquivoInvalidoError(
                f"o arquivo tem elementos aninhados demais (limite {MAX_DEPTH})", self._linha
            )
        attrs = dict(zip(lista_attrs[::2], lista_attrs[1::2], strict=True))
        pai = self._pilha[-1][0] if self._pilha else None

        if "ref" in attrs:
            if len(attrs) > 1:
                raise ArquivoInvalidoError(
                    f"<{nome}> tem 'ref' junto com outros atributos", self._linha
                )
            alvo = self._ids.get(attrs["ref"])
            if alvo is None:
                raise ArquivoInvalidoError(
                    f'<{nome}> aponta para o id "{attrs["ref"]}", que não existe '
                    "(ou aparece só depois)",
                    self._linha,
                )
            if pai is None:
                raise ArquivoInvalidoError(
                    "o elemento raiz não pode ser uma referência", self._linha
                )
            pai.children.append(alvo)
            self._pilha.append([alvo, True, []])
            return

        identificador = attrs.pop("id", None)
        elemento = self._classe_para_tag(nome)(
            nome, attrs, has_id=identificador is not None, line=self._linha
        )
        if identificador is not None:
            if identificador in self._ids:
                raise ArquivoInvalidoError(
                    f'o id "{identificador}" aparece em mais de um elemento (<{nome}>)',
                    self._linha,
                )
            self._ids[identificador] = elemento
        if pai is not None:
            pai.children.append(elemento)
        else:
            self.raiz = elemento
        self._pilha.append([elemento, False, []])

    def _texto(self, dados: str) -> None:
        if self._pilha and not self._pilha[-1][1]:
            self._pilha[-1][2].append(dados)

    def _fim(self, nome: str) -> None:
        elemento, referencia, pedacos = self._pilha.pop()
        if referencia:
            return
        texto = "".join(pedacos)
        if elemento.children:
            if texto.strip():
                raise ArquivoInvalidoError(
                    f"<{nome}> mistura texto e elementos, o que o formato não permite", self._linha
                )
        elif texto:
            elemento.text = texto


def parse_xml(
    dados: bytes | str,
    classe_para_tag: Callable[[str], type[Element]] = lambda _tag: Element,
) -> Element:
    """Lê o XML e devolve a raiz. Levanta `ArquivoInvalidoError` se o arquivo não servir."""
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    if len(dados) > MAX_BYTES:
        raise ArquivoInvalidoError(f"o arquivo é grande demais (limite {MAX_BYTES // 2**20} MiB)")
    leitor = _Leitor(classe_para_tag)
    try:
        leitor.parser.Parse(_juntar_surrogates(dados), True)
    except expat.ExpatError as erro:
        motivo = _MENSAGENS.get(expat.ErrorString(erro.code), expat.ErrorString(erro.code))
        raise ArquivoInvalidoError(f"XML inválido: {motivo}", erro.lineno) from erro
    if leitor.raiz is None:
        raise ArquivoInvalidoError("o arquivo não tem nenhum elemento")
    return leitor.raiz
