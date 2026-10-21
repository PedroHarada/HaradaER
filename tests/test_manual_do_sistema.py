"""Cada pacote leva só o manual do próprio sistema (packaging/manual_do_sistema.py)."""

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


@pytest.mark.parametrize("sistema", sorted(modulo.SISTEMAS))
def test_manual_so_tem_o_proprio_sistema(sistema):
    manual = modulo.manual_de(sistema, TEXTO)
    nome = modulo.SISTEMAS[sistema]
    assert f"## {nome}" in manual and "## Depois de abrir" in manual
    for palavra in OUTROS[sistema]:
        assert palavra not in manual, palavra
    assert "README" not in manual and "](" not in manual  # sem links que não abririam


def test_sistema_desconhecido_mostra_o_uso(tmp_path):
    assert modulo.main(["x", "amiga", str(tmp_path / "m.txt")]) == 2
