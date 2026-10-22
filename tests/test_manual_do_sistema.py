"""Cada pacote leva só o manual do próprio sistema, em português e em inglês
(packaging/manual_do_sistema.py)."""

import importlib.util
from pathlib import Path

import pytest

CAMINHO = Path(__file__).parents[1] / "packaging" / "manual_do_sistema.py"
_spec = importlib.util.spec_from_file_location("manual_do_sistema", CAMINHO)
modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(modulo)
TEXTO = modulo.MANUAL.read_text(encoding="utf-8")

OUTROS = {
    "linux": ("Windows", "macOS", "Mac", ".exe", "Cmd"),
    "windows": ("Linux", "macOS", "Mac", "instalar.sh", "Cmd"),
    "macos": ("Linux", "Windows", ".exe", "instalar.sh", "Ctrl"),
}


@pytest.mark.parametrize("idioma", sorted(modulo.IDIOMAS))
@pytest.mark.parametrize("sistema", sorted(modulo.SISTEMAS))
def test_manual_so_tem_o_proprio_sistema(sistema, idioma):
    config = modulo.IDIOMAS[idioma]
    manual = modulo.manual_de(sistema, config.manual.read_text(encoding="utf-8"), idioma)
    nome = modulo.SISTEMAS[sistema]
    assert f"## {nome}" in manual and f"## {config.depois}" in manual
    assert config.no_sistema.format(nome=nome) in manual
    for palavra in OUTROS[sistema]:
        assert palavra not in manual, palavra
    assert "README" not in manual and "](" not in manual  # sem links que não abririam


def test_manuais_com_as_mesmas_secoes():
    secoes = {
        idioma: [
            modulo._titulo(s)
            for s in config.manual.read_text(encoding="utf-8").split("\n---\n")[1:]
        ]
        for idioma, config in modulo.IDIOMAS.items()
    }
    assert secoes["pt"] == ["Linux", "Windows", "macOS", "Depois de abrir"]
    assert secoes["en"] == ["Linux", "Windows", "macOS", "After opening"]


def test_grava_o_manual_em_ingles(tmp_path):
    saida = tmp_path / "GETTING-STARTED.txt"
    assert modulo.main(["x", "linux", str(saida), "en"]) == 0
    assert saida.read_text(encoding="utf-8").startswith("# Getting started")


def test_sem_idioma_e_portugues(tmp_path):
    saida = tmp_path / "PRIMEIROS-PASSOS.txt"
    assert modulo.main(["x", "linux", str(saida)]) == 0
    assert saida.read_text(encoding="utf-8").startswith("# Primeiros passos")


def test_sistema_ou_idioma_desconhecido_mostra_o_uso(tmp_path):
    assert modulo.main(["x", "amiga", str(tmp_path / "m.txt")]) == 2
    assert modulo.main(["x", "linux", str(tmp_path / "m.txt"), "fr"]) == 2


def test_texto_do_manual_em_portugues():
    assert TEXTO.startswith("# Primeiros passos")
