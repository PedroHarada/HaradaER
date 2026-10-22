"""Idioma da interface (RNF-06): português, o padrão, ou inglês.

O texto em português é a própria chave, como no gettext: `_("Salvar")` devolve "Salvar" em
português e "Save" em inglês. As traduções ficam em `en.py`. Um texto sem tradução sai em
português; o teste `test_idioma.py` confere que todos os `_("...")` do código têm uma.

O idioma é escolhido uma vez, ao abrir o programa (`set_language`), antes de criar as janelas;
trocar no menu só vale ao reabrir. Não importa nada de Qt: o núcleo também usa (RNF-08).
"""

from __future__ import annotations

from haradaer.i18n.en import EN

DEFAULT = "pt"
LANGUAGES = {"pt": "Português", "en": "English"}
_CATALOGS = {"en": EN}

_language = DEFAULT


def language_for_locale(nome: str) -> str:
    """O idioma para um local do sistema ("en_US" -> "en"); o padrão para os outros."""
    codigo = nome.split("_")[0].split("-")[0].lower()
    return codigo if codigo in LANGUAGES else DEFAULT


def set_language(codigo: str) -> None:
    """Escolhe o idioma; um código desconhecido vira o padrão."""
    global _language
    _language = codigo if codigo in LANGUAGES else DEFAULT


def language() -> str:
    return _language


def translate(texto: str, codigo: str) -> str:
    """O texto num idioma dado, que pode não ser o escolhido (o aviso ao trocar de idioma)."""
    return _CATALOGS.get(codigo, {}).get(texto, texto)


def _(texto: str) -> str:
    """O texto no idioma escolhido."""
    return translate(texto, _language)


def N_(texto: str) -> str:
    """Marca um texto para tradução sem traduzir agora (tabelas criadas ao importar)."""
    return texto
