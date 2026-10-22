"""O que o programa lembra entre sessões: arquivos recentes, a disposição da janela e os avisos.

Fica nas configurações do usuário (`QSettings`; no Linux, em `~/.config/HaradaER/`).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings

MAX_RECENT = 10
RECENT_KEY = "arquivos/recentes"
STATE_KEY = "janela/estado"
GEOMETRY_KEY = "janela/geometria"
STRUCTURE_KEY = "verificacao/avisos-de-estrutura"
LANGUAGE_KEY = "aparencia/idioma"
UPDATES_KEY = "atualizacoes/verificar"
LAST_CHECK_KEY = "atualizacoes/ultima-verificacao"


def settings() -> QSettings:
    return QSettings("HaradaER", "HaradaER")


def _as_list(valor) -> list[str]:
    if valor is None:
        return []
    if isinstance(valor, str):  # o QSettings devolve um texto só quando a lista tem um item
        return [valor] if valor else []
    return [str(v) for v in valor]


class RecentFiles:
    """Lista de arquivos abertos ou salvos por último, compartilhada entre as janelas (RF-01)."""

    def paths(self) -> list[Path]:
        """Os recentes que ainda existem, do mais novo ao mais antigo."""
        return [Path(p) for p in _as_list(settings().value(RECENT_KEY)) if Path(p).is_file()]

    def add(self, caminho: Path) -> None:
        texto = str(caminho.resolve())
        lista = [p for p in _as_list(settings().value(RECENT_KEY)) if p != texto]
        self._store([texto, *lista][:MAX_RECENT])

    def remove(self, caminho: Path) -> None:
        texto = str(caminho)
        self._store([p for p in _as_list(settings().value(RECENT_KEY)) if p != texto])

    def clear(self) -> None:
        self._store([])

    @staticmethod
    def _store(lista: list[str]) -> None:
        config = settings()
        config.setValue(RECENT_KEY, lista)
        config.sync()


def save_window_layout(geometria: QByteArray, estado: QByteArray) -> None:
    config = settings()
    config.setValue(GEOMETRY_KEY, geometria)
    config.setValue(STATE_KEY, estado)
    config.sync()


def window_layout() -> tuple[QByteArray | None, QByteArray | None]:
    config = settings()
    return config.value(GEOMETRY_KEY), config.value(STATE_KEY)


def structure_warnings_enabled() -> bool:
    """Os avisos de estrutura (Exibir › Avisos de estrutura) começam ligados."""
    return str(settings().value(STRUCTURE_KEY, "true")).lower() == "true"


def set_structure_warnings_enabled(ligado: bool) -> None:
    config = settings()
    config.setValue(STRUCTURE_KEY, "true" if ligado else "false")
    config.sync()


def saved_language() -> str | None:
    """O idioma escolhido em Exibir › Idioma (RNF-06); `None` se nunca foi escolhido."""
    valor = settings().value(LANGUAGE_KEY)
    return str(valor) if valor else None


def set_saved_language(codigo: str) -> None:
    config = settings()
    config.setValue(LANGUAGE_KEY, codigo)
    config.sync()


def update_check_enabled() -> bool:
    """Verificar ao abrir se há versão nova (RF-22); ligado se nunca foi mudado."""
    return str(settings().value(UPDATES_KEY, "true")).lower() == "true"


def set_update_check_enabled(ligado: bool) -> None:
    config = settings()
    config.setValue(UPDATES_KEY, "true" if ligado else "false")
    config.sync()


def last_update_check() -> str | None:
    valor = settings().value(LAST_CHECK_KEY)
    return str(valor) if valor else None


def set_last_update_check(dia: str) -> None:
    config = settings()
    config.setValue(LAST_CHECK_KEY, dia)
    config.sync()
