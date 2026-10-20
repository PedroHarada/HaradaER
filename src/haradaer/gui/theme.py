"""Temas claro e escuro da interface.

O Qt desta máquina (Linux/Wayland, sem tema de plataforma) não sabe se o sistema está claro ou
escuro e não troca a paleta sozinho; por isso o HaradaER tem paletas próprias sobre o estilo
Fusion, escolhidas em Exibir › Tema e lembradas entre sessões.

No diagrama, as formas mantêm as cores do TerraER (são claras nos dois temas, e o texto dentro
delas continua preto). No escuro mudam só o fundo, a grade e o que fica direto sobre o fundo:
linhas das conexões, rótulos 1/N, rótulo da generalização e texto livre. O arquivo `.xml` não
muda, e a exportação sai sempre no tema claro.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from haradaer.core.appearance.style import BLACK, RGBA
from haradaer.gui.settings import settings

THEME_KEY = "aparencia/tema"


@dataclass(frozen=True)
class Theme:
    name: str  # "claro" ou "escuro"
    label: str
    canvas: QColor  # fundo do diagrama
    ink: RGBA  # cor que substitui o preto do que fica direto sobre o fundo
    grid: QColor

    @property
    def is_dark(self) -> bool:
        return self.name == "escuro"


LIGHT = Theme("claro", "&Claro", QColor("white"), BLACK, QColor(225, 228, 235))
DARK = Theme("escuro", "&Escuro", QColor(43, 45, 48), (220, 220, 220, 255), QColor(62, 65, 70))
THEMES = {tema.name: tema for tema in (LIGHT, DARK)}


def _palette(tema: Theme) -> QPalette:
    if not tema.is_dark:
        return QApplication.style().standardPalette()
    p = QPalette()
    grupo, papel = QPalette.ColorGroup, QPalette.ColorRole
    cores = {
        papel.Window: "#2b2d30",
        papel.WindowText: "#e6e6e6",
        papel.Base: "#1f2023",
        papel.AlternateBase: "#2b2d30",
        papel.ToolTipBase: "#3a3d41",
        papel.ToolTipText: "#e6e6e6",
        papel.PlaceholderText: "#8a8d91",
        papel.Text: "#e6e6e6",
        papel.Button: "#36393d",
        papel.ButtonText: "#e6e6e6",
        papel.BrightText: "#ff6b6b",
        papel.Light: "#4a4d52",
        papel.Midlight: "#404347",
        papel.Mid: "#2f3134",
        papel.Dark: "#1b1c1e",
        papel.Shadow: "#000000",
        papel.Highlight: "#2f6fc4",
        papel.HighlightedText: "#ffffff",
        papel.Link: "#6aa6ff",
    }
    for nome, cor in cores.items():
        p.setColor(nome, QColor(cor))
    for nome in (papel.WindowText, papel.Text, papel.ButtonText):
        p.setColor(grupo.Disabled, nome, QColor("#7d8085"))
    return p


class _ThemeManager(QObject):
    changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.current = LIGHT


_manager: _ThemeManager | None = None


def manager() -> _ThemeManager:
    global _manager
    if _manager is None:
        _manager = _ThemeManager()
    return _manager


def current_theme() -> Theme:
    return manager().current


def saved_theme() -> Theme:
    return THEMES.get(str(settings().value(THEME_KEY, LIGHT.name)), LIGHT)


def apply_theme(tema: Theme, *, save: bool = True) -> None:
    """Troca o tema do programa inteiro (todas as janelas) e, se pedido, guarda a escolha."""
    app = QApplication.instance()
    if isinstance(app, QApplication):
        if app.style().name().lower() != "fusion":  # trocar o estilo é caro: só se preciso
            estilo = QStyleFactory.create("Fusion")
            if estilo is not None:
                app.setStyle(estilo)
        paleta = _palette(tema)
        if app.palette() != paleta:
            app.setPalette(paleta)
    mudou = manager().current is not tema
    manager().current = tema
    if save:
        config = settings()
        config.setValue(THEME_KEY, tema.name)
        config.sync()
    if mudou:
        manager().changed.emit(tema)
