"""Temas: claro, escuro e o do sistema (qt6ct).

O PySide6 traz um Qt próprio, sem o plugin do qt6ct que o sistema usa para dar o tema aos
programas Qt (o `QT_QPA_PLATFORMTHEME=qt6ct` não faz efeito nele). Por isso o HaradaER lê a
configuração do qt6ct por conta própria (`~/.config/qt6ct/qt6ct.conf` e o arquivo de cores para
onde ela aponta) e acompanha as trocas de tema enquanto está aberto. Os temas claro e escuro
são paletas próprias sobre o estilo Fusion. A escolha fica em Exibir › Tema e é lembrada.

No diagrama, as formas mantêm as cores do TerraER (claras, com texto preto dentro) em qualquer
tema. Mudam o fundo, a grade, o destaque da seleção e o que fica direto sobre o fundo: linhas
das conexões, rótulos 1/N, rótulo da generalização e texto livre. O arquivo `.xml` não muda, e
a exportação sai sempre no tema claro.
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from haradaer.core.appearance.style import BLACK, RGBA
from haradaer.gui.settings import settings
from haradaer.i18n import N_

THEME_KEY = "aparencia/tema"
SYSTEM = "sistema"


@dataclass(frozen=True)
class Theme:
    name: str  # "claro", "escuro" ou "sistema"
    label: str
    canvas: QColor  # fundo do diagrama
    ink: RGBA  # cor que substitui o preto do que fica direto sobre o fundo
    grid: QColor
    accent: QColor  # seleção e alças
    dark: bool
    palette: QPalette | None = field(default=None, compare=False)  # a do sistema, já pronta

    @property
    def is_dark(self) -> bool:
        return self.dark


_AZUL = QColor(40, 120, 255)
LIGHT = Theme("claro", N_("&Claro"), QColor("white"), BLACK, QColor(225, 228, 235), _AZUL, False)
DARK = Theme(
    "escuro",
    N_("&Escuro"),
    QColor(43, 45, 48),
    (220, 220, 220, 255),
    QColor(62, 65, 70),
    _AZUL,
    True,
)


# --------------------------------------------------------------------------- tema do sistema


def _qt6ct_config() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "qt6ct" / "qt6ct.conf"


def _ler_ini(caminho: Path) -> configparser.ConfigParser:
    """Lê um .ini do qt6ct. Um arquivo ilegível (codificação estranha, sintaxe quebrada) vale
    como vazio: o tema do sistema some, mas o HaradaER abre normalmente."""
    leitor = configparser.ConfigParser(interpolation=None, strict=False)
    leitor.optionxform = str  # type: ignore[assignment,method-assign]  # mantém maiúsculas
    try:
        leitor.read(caminho, encoding="utf-8")
    except UnicodeDecodeError, configparser.Error, OSError:
        return configparser.ConfigParser(interpolation=None)
    return leitor


def qt6ct_colors_file() -> Path | None:
    """O arquivo de cores que o qt6ct está usando, ou `None` se não houver paleta própria."""
    config = _qt6ct_config()
    if not config.is_file():
        return None
    leitor = _ler_ini(config)
    if not leitor.has_section("Appearance"):
        return None
    aparencia = leitor["Appearance"]
    if aparencia.get("custom_palette", "false").strip().lower() != "true":
        return None
    caminho = aparencia.get("color_scheme_path", "").strip()
    if not caminho:
        return None
    arquivo = Path(os.path.expanduser(caminho))
    return arquivo if arquivo.is_file() else None


def _cores(texto: str) -> list[QColor]:
    return [QColor(c.strip()) for c in texto.split(",") if c.strip()]


def parse_qt6ct_palette(arquivo: Path) -> QPalette | None:
    """Paleta de um arquivo de cores do qt6ct (uma cor por papel, na ordem de `ColorRole`)."""
    leitor = _ler_ini(arquivo)
    if not leitor.has_section("ColorScheme"):
        return None
    secao = leitor["ColorScheme"]
    grupos = {
        "active_colors": QPalette.ColorGroup.Active,
        "inactive_colors": QPalette.ColorGroup.Inactive,
        "disabled_colors": QPalette.ColorGroup.Disabled,
    }
    paleta = QPalette()
    achou = False
    for chave, grupo in grupos.items():
        cores = _cores(secao.get(chave, ""))
        if not cores or not all(c.isValid() for c in cores):
            continue
        achou = True
        for indice, cor in enumerate(cores[: QPalette.ColorRole.NColorRoles.value]):
            papel = QPalette.ColorRole(indice)
            if papel != QPalette.ColorRole.NoRole:
                paleta.setColor(grupo, papel, cor)
    return paleta if achou else None


def _misturar(a: QColor, b: QColor, quanto: float) -> QColor:
    return QColor(
        round(a.red() + (b.red() - a.red()) * quanto),
        round(a.green() + (b.green() - a.green()) * quanto),
        round(a.blue() + (b.blue() - a.blue()) * quanto),
    )


def system_theme() -> Theme | None:
    """O tema do qt6ct, se houver um configurado com paleta própria."""
    arquivo = qt6ct_colors_file()
    paleta = parse_qt6ct_palette(arquivo) if arquivo is not None else None
    if paleta is None:
        return None
    fundo = paleta.color(QPalette.ColorRole.Base)
    texto = paleta.color(QPalette.ColorRole.Text)
    escuro = paleta.color(QPalette.ColorRole.Window).lightness() < 128
    return Theme(
        SYSTEM,
        N_("Do &sistema (qt6ct)"),
        fundo,
        (texto.red(), texto.green(), texto.blue(), 255) if escuro else BLACK,
        _misturar(fundo, texto, 0.12),
        paleta.color(QPalette.ColorRole.Highlight),
        escuro,
        paleta,
    )


def available_themes() -> list[Theme]:
    sistema = system_theme()
    return [LIGHT, DARK] + ([sistema] if sistema is not None else [])


# --------------------------------------------------------------------------- aplicar


def _palette(tema: Theme) -> QPalette:
    if tema.palette is not None:
        return QPalette(tema.palette)
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
        self._vigia: QFileSystemWatcher | None = None

    def watch_system(self) -> None:
        """Acompanha a configuração do qt6ct: ao trocar de tema no sistema (o link `active`
        muda), o HaradaER se atualiza, se estiver usando o tema do sistema."""
        if self._vigia is None:
            self._vigia = QFileSystemWatcher(self)
            self._vigia.fileChanged.connect(self._system_changed)
            self._vigia.directoryChanged.connect(self._system_changed)
        self._rewatch()

    def _rewatch(self) -> None:
        if self._vigia is None:  # só se acompanha o sistema depois de `watch_system`
            return
        caminhos = [str(_qt6ct_config())]
        arquivo = qt6ct_colors_file()
        if arquivo is not None:
            # o arquivo de verdade e a pasta do link: trocar o tema troca o alvo do link
            caminhos += [str(arquivo.resolve()), str(arquivo.parent.parent)]
        existentes = [c for c in caminhos if Path(c).exists()]
        antigos = self._vigia.files() + self._vigia.directories()
        if antigos:
            self._vigia.removePaths(antigos)
        if existentes:
            self._vigia.addPaths(existentes)

    def _system_changed(self, *_args) -> None:
        self._rewatch()
        if self.current.name == SYSTEM:
            novo = system_theme()
            apply_theme(novo if novo is not None else LIGHT, save=False)


_manager: _ThemeManager | None = None


def manager() -> _ThemeManager:
    global _manager
    if _manager is None:
        _manager = _ThemeManager()
    return _manager


def current_theme() -> Theme:
    return manager().current


def theme_named(nome: str) -> Theme | None:
    return next((t for t in available_themes() if t.name == nome), None)


def saved_theme() -> Theme:
    return theme_named(str(settings().value(THEME_KEY, LIGHT.name))) or LIGHT


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
    anterior = manager().current
    mudou = anterior is not tema and (
        anterior != tema or anterior.palette != tema.palette or tema.name == SYSTEM
    )
    manager().current = tema
    if save:
        config = settings()
        config.setValue(THEME_KEY, tema.name)
        config.sync()
    if mudou:
        manager().changed.emit(tema)
