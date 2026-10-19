"""Abrir e salvar documentos no formato do TerraER."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from haradaer.core.figures import class_for_tag, validate_structure
from haradaer.core.model.document import Document
from haradaer.core.xmlfmt import parse_xml, serialize


def loads(dados: bytes | str) -> Document:
    """Lê um documento. Levanta `ArquivoInvalidoError` se o arquivo não servir."""
    raiz = parse_xml(dados, class_for_tag)
    validate_structure(raiz)
    return Document(raiz)


def dumps(documento: Document) -> str:
    """Texto do arquivo, no formato do TerraER (ASCII puro)."""
    return serialize(documento.root)


def load(caminho: str | os.PathLike[str]) -> Document:
    return loads(Path(caminho).read_bytes())


def save(documento: Document, caminho: str | os.PathLike[str]) -> None:
    """Grava num arquivo temporário e só então substitui o destino (RNF-11)."""
    destino = Path(caminho)
    dados = dumps(documento).encode("ascii")
    descritor, nome_temporario = tempfile.mkstemp(
        dir=destino.parent, prefix=f".{destino.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descritor, "wb") as arquivo:
            arquivo.write(dados)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(nome_temporario, destino)
    except BaseException:
        Path(nome_temporario).unlink(missing_ok=True)
        raise
