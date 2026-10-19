"""Formato genérico do .xml do TerraER: ids, referências, escape e números."""

from haradaer.core.xmlfmt.escape import escape
from haradaer.core.xmlfmt.numbers import format_number, java_double_str, parse_number
from haradaer.core.xmlfmt.reader import parse_xml
from haradaer.core.xmlfmt.writer import serialize

__all__ = [
    "escape",
    "format_number",
    "java_double_str",
    "parse_number",
    "parse_xml",
    "serialize",
]
