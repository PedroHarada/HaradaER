"""Comandos e o histórico de desfazer/refazer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class Command(ABC):
    """Uma alteração do documento que sabe se desfazer."""

    label: str = ""

    @abstractmethod
    def apply(self) -> None: ...

    @abstractmethod
    def revert(self) -> None: ...


class Composite(Command):
    """Vários comandos tratados como um só: aplicados em ordem e desfeitos na ordem inversa."""

    def __init__(self, commands: list[Command], label: str = ""):
        self.commands = commands
        self.label = label

    def apply(self) -> None:
        for comando in self.commands:
            comando.apply()

    def revert(self) -> None:
        for comando in reversed(self.commands):
            comando.revert()


class History:
    """Duas pilhas (desfazer e refazer) e a noção de "modificado desde a última gravação"."""

    def __init__(self) -> None:
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self._clean: int | None = 0  # tamanho da pilha de desfazer quando foi gravado
        self._macro: list[Command] | None = None
        self._macro_label = ""
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo) and self._macro is None

    @property
    def can_redo(self) -> bool:
        return bool(self._redo) and self._macro is None

    @property
    def undo_label(self) -> str:
        return self._undo[-1].label if self._undo else ""

    @property
    def redo_label(self) -> str:
        return self._redo[-1].label if self._redo else ""

    @property
    def is_dirty(self) -> bool:
        return self._clean != len(self._undo)

    def mark_clean(self) -> None:
        self._clean = len(self._undo)
        self._notify()

    def mark_dirty(self) -> None:
        """Modificado em relação ao arquivo, sem passo de desfazer (RF-25: o documento aberto já
        difere do que está em disco). Só salvar volta a deixá-lo limpo."""
        self._clean = None
        self._notify()

    def execute(self, comando: Command) -> None:
        """Aplica o comando e o guarda para desfazer. Apaga o que havia para refazer."""
        comando.apply()
        if self._macro is not None:
            self._macro.append(comando)
            return
        self._push(comando)

    def _push(self, comando: Command) -> None:
        self._undo.append(comando)
        if self._clean is not None and self._clean >= len(self._undo):
            self._clean = None  # o ponto gravado estava no futuro apagado
        self._redo.clear()
        self._notify()

    def begin_macro(self, label: str = "") -> None:
        """Junta os comandos seguintes num só passo de desfazer (por exemplo, um arrasto)."""
        if self._macro is not None:
            raise RuntimeError("já há um grupo aberto")
        self._macro, self._macro_label = [], label

    def end_macro(self) -> None:
        macro, self._macro = self._macro, None
        if macro:
            self._push(Composite(macro, self._macro_label))

    def cancel_macro(self) -> None:
        """Desfaz o que o grupo aberto já fez e o descarta."""
        macro, self._macro = self._macro, None
        for comando in reversed(macro or []):
            comando.revert()

    def undo(self) -> None:
        if not self.can_undo:
            return
        comando = self._undo.pop()
        comando.revert()
        self._redo.append(comando)
        self._notify()

    def redo(self) -> None:
        if not self.can_redo:
            return
        comando = self._redo.pop()
        comando.apply()
        self._undo.append(comando)
        self._notify()
