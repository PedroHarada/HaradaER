"""Os manuais trazem a mesma lista de atalhos do programa (Ajuda › Atalhos do teclado)."""

from pathlib import Path

import pytest

from haradaer.gui.shortcuts_dialog import MANUALS, MARK_BEGIN, MARK_END, manual_block

RAIZ = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("idioma", sorted(MANUALS))
def test_manual_igual_ao_programa(qtbot, idioma):
    texto = (RAIZ / MANUALS[idioma]).read_text(encoding="utf-8")
    bloco = texto[texto.index(MARK_BEGIN) + len(MARK_BEGIN) : texto.index(MARK_END)].strip()
    assert bloco == manual_block(idioma).strip(), (
        "Manual desatualizado: rode `python -m haradaer.gui.shortcuts_dialog`."
    )
