"""Idioma da interface (RNF-06): o catálogo em inglês cobre todos os textos do programa."""

import ast
import re
import string
from pathlib import Path

import pytest

from haradaer.i18n import (
    DEFAULT,
    N_,
    _,
    language,
    language_for_locale,
    set_language,
    translate,
)
from haradaer.i18n.en import EN

FONTE = Path(__file__).resolve().parents[1] / "src" / "haradaer"

# Chamadas que põem texto na tela. Um texto literal nelas, sem `_()`, escapou da tradução;
# só conta se tiver palavras fora dos campos `{...}` (nomes de arquivo e números não se traduzem).
_TELA = re.compile(
    r"\b(?:addMenu|QAction|setText|setToolTip|setStatusTip|setPlaceholderText|showMessage|addRow"
    r"|QCheckBox|QDockWidget|QToolBar|addAction|setHeaderLabels|QLabel|setWindowTitle"
    r"|critical|warning|information|question)\(\s*\[?\s*f?([\"'])(.*?)\1"
)


def _textos_marcados() -> dict[str, Path]:
    textos: dict[str, Path] = {}
    for arquivo in sorted(FONTE.rglob("*.py")):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Name)
                and no.func.id in ("_", "N_")
                and no.args
                and isinstance(no.args[0], ast.Constant)
                and isinstance(no.args[0].value, str)
            ):
                textos.setdefault(no.args[0].value, arquivo)
    return textos


def _campos(texto: str) -> set[str]:
    return {nome for _, nome, _, _ in string.Formatter().parse(texto) if nome}


def test_todo_texto_marcado_tem_traducao():
    faltando = {t: str(a.relative_to(FONTE)) for t, a in _textos_marcados().items() if t not in EN}
    assert faltando == {}


def test_catalogo_sem_texto_que_o_programa_nao_usa():
    assert set(EN) - set(_textos_marcados()) == set()


@pytest.mark.parametrize("texto", sorted(EN))
def test_traducao_tem_os_mesmos_campos(texto):
    assert _campos(EN[texto]) == _campos(texto)
    assert EN[texto].count("&") == texto.count("&")  # letra de atalho nos menus
    assert EN[texto].strip()


def test_nenhum_texto_da_tela_sem_traducao():
    escapados = []
    for arquivo in sorted((FONTE / "gui").rglob("*.py")):
        for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
            achado = _TELA.search(linha)
            if achado and re.search(r"[^\W\d_]{3}", re.sub(r"\{[^}]*\}", "", achado.group(2))):
                escapados.append(f"{arquivo.name}:{numero}: {linha.strip()}")
    assert escapados == []


def test_portugues_e_o_padrao_e_nao_traduz():
    assert language() == DEFAULT == "pt"
    assert _("&Arquivo") == "&Arquivo"
    assert N_("&Arquivo") == "&Arquivo"


def test_ingles_traduz_e_texto_desconhecido_fica_como_esta():
    set_language("en")
    assert _("&Arquivo") == "&File"
    assert _("texto que ninguém traduziu") == "texto que ninguém traduziu"
    assert _("Salvo em {caminho}").format(caminho="/tmp/a.xml") == "Saved to /tmp/a.xml"


def test_idioma_desconhecido_vira_o_padrao():
    set_language("fr")
    assert language() == "pt"


def test_traduzir_para_outro_idioma_sem_trocar_o_escolhido():
    assert translate("Idioma", "en") == "Language"
    assert translate("Idioma", "pt") == "Idioma"
    assert language() == "pt"


@pytest.mark.parametrize(
    ("local", "idioma"),
    [("en_US", "en"), ("en-GB", "en"), ("pt_BR", "pt"), ("de_DE", "pt"), ("C", "pt"), ("", "pt")],
)
def test_idioma_do_sistema(local, idioma):
    assert language_for_locale(local) == idioma


def test_nome_padrao_do_elemento_segue_o_idioma():
    from haradaer.core.appearance.metrics import FixedMeasurer
    from haradaer.core.commands.edit import new_node

    assert new_node("ent", 0, 0, FixedMeasurer()).name == "Entidade"
    set_language("en")
    assert new_node("ent", 0, 0, FixedMeasurer()).name == "Entity"
    assert new_node("uniao", 0, 0, FixedMeasurer()).name == "u"  # letra do círculo, igual


def test_erro_ao_abrir_no_idioma_escolhido():
    from haradaer.core import io
    from haradaer.core.errors import ArquivoInvalidoError

    set_language("en")
    with pytest.raises(ArquivoInvalidoError, match="the file has no elements|Invalid XML"):
        io.loads("")
