"""Tema do sistema lido do qt6ct (o Qt do PySide6 não tem o plugin do qt6ct).

Os testes usam um qt6ct falso, na pasta de configuração temporária dos testes.
"""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.gui.theme import (
    LIGHT,
    SYSTEM,
    apply_theme,
    available_themes,
    current_theme,
    manager,
    saved_theme,
    system_theme,
)
from haradaer.gui.window import DocumentWindow

# 21 cores, na ordem de QPalette.ColorRole (WindowText, Button, Light, ..., PlaceholderText)
ROXO = (
    "#ffecdfc4, #ff2a1a33, #ff3a2350, #ff2a1a33, #ff140b1a, #ff1c1024, #ffecdfc4, #ffecdfc4,"
    " #ffecdfc4, #ff1c1024, #ff1c1024, #ff140b1a, #ffd4af37, #ff1c1024, #ffb06fd1, #ff8a7fc9,"
    " #ff2a1a33, #ff2a1a33, #ffecdfc4, #ff6b5578, #ffd4af37"
)
VERDE = ROXO.replace("#ff1c1024", "#ff0f2a1a")  # outro tema: muda o fundo (Base e Window)


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def qt6ct():
    """Cria `qt6ct/qt6ct.conf` apontando para um arquivo de cores, como no sistema do autor."""
    pasta = Path(os.environ["XDG_CONFIG_HOME"]) / "qt6ct"
    pasta.mkdir(parents=True, exist_ok=True)
    cores = pasta / "cores.conf"

    def escrever(paleta: str, *, propria: bool = True) -> Path:
        cores.write_text(
            f"[ColorScheme]\nactive_colors={paleta}\ninactive_colors={paleta}\n"
            f"disabled_colors={paleta}\n"
        )
        (pasta / "qt6ct.conf").write_text(
            "# comentário como no arquivo do autor\n[Appearance]\n"
            f"color_scheme_path={cores}\ncustom_palette={'true' if propria else 'false'}\n"
            "style=Fusion\n"
        )
        return cores

    escrever(ROXO)
    yield escrever
    for arquivo in pasta.iterdir():
        arquivo.unlink()
    pasta.rmdir()


def test_le_as_cores_do_qt6ct(qt6ct):
    tema = system_theme()
    assert tema is not None and tema.name == SYSTEM and tema.is_dark
    assert tema.canvas.name() == "#1c1024"  # Base
    assert tema.ink == (0xEC, 0xDF, 0xC4, 255)  # Text: linhas e rótulos soltos
    assert tema.accent.name() == "#d4af37"  # Highlight: seleção e alças
    assert tema.palette.color(QPalette.ColorRole.Window).name() == "#1c1024"
    assert [t.name for t in available_themes()] == ["claro", "escuro", SYSTEM]


def test_sem_qt6ct_ou_sem_paleta_propria_nao_ha_tema_do_sistema(qt6ct):
    qt6ct(ROXO, propria=False)
    assert system_theme() is None
    assert [t.name for t in available_themes()] == ["claro", "escuro"]


def test_escolher_pelo_menu_aplica_e_e_lembrado(qt6ct, qtbot):
    janela = DocumentWindow()
    qtbot.addWidget(janela)
    janela.theme_actions[SYSTEM].trigger()
    assert current_theme().name == SYSTEM
    assert QApplication.palette().window().color().name() == "#1c1024"
    assert janela.diagram_scene.backgroundBrush().color().name() == "#1c1024"
    assert saved_theme().name == SYSTEM


def test_trocar_o_tema_do_sistema_atualiza_o_haradaer(qt6ct):
    apply_theme(system_theme(), save=False)
    qt6ct(VERDE)
    manager()._system_changed()  # o que o vigia de arquivos chama quando o tema muda
    assert QApplication.palette().window().color().name() == "#0f2a1a"
    assert current_theme().canvas.name() == "#0f2a1a"


def test_tema_do_sistema_que_sumiu_volta_ao_claro(qt6ct):
    apply_theme(system_theme(), save=False)
    qt6ct(ROXO, propria=False)
    manager()._system_changed()
    assert current_theme() is LIGHT
