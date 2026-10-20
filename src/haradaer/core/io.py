"""Abrir e salvar documentos no formato do TerraER."""

from __future__ import annotations

import os
import stat
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


def _permissoes(destino: Path) -> int:
    """As do arquivo que vai ser substituído; para um arquivo novo, as de costume (umask).

    O arquivo temporário nasce só com permissão do dono, e sem isto o arquivo salvo perderia a
    leitura para os outros usuários.
    """
    try:
        return stat.S_IMODE(destino.stat().st_mode)
    except FileNotFoundError:
        mascara = os.umask(0)
        os.umask(mascara)
        return 0o666 & ~mascara


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
        os.chmod(nome_temporario, _permissoes(destino))
        os.replace(nome_temporario, destino)
    except BaseException:
        Path(nome_temporario).unlink(missing_ok=True)
        raise
