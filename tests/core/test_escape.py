import pytest

from haradaer.core.xmlfmt import escape


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Aluno", "Aluno"),
        ("A&B", "A&amp;B"),
        ("<x>", "&lt;x&gt;"),
        ("\"d\" 'e'", "&quot;d&quot; &apos;e&apos;"),
        ("linha1\nlinha2", "linha1\nlinha2"),
        ("a\tb", "a&#x9;b"),
        ("a\rb", "a&#xd;b"),
        ("ção", "&#xe7;&#xe3;o"),
        ("中", "&#x4e2d;"),
        ("~", "~"),
        ("\x7f", "&#x7f;"),
        ("😀", "&#xd83d;&#xde00;"),
    ],
)
def test_escape_como_o_terraer(texto, esperado):
    assert escape(texto) == esperado
