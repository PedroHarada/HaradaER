"""Cópias de recuperação: o modelo não salvo, gravado de tempos em tempos fora do arquivo dele.

O arquivo do usuário só muda quando ele salva. A cópia fica na pasta de dados do programa (no
Linux, `~/.local/share/HaradaER/recuperacao/`) e some ao salvar ou ao fechar a janela; só sobra
quando o programa fechou de repente, e então é oferecida na próxima abertura (como no Kate e no
LibreOffice).

Cada janela segura um `QLockFile` ao lado da cópia enquanto está aberta. Uma cópia cujo trava
se consegue pegar é de uma janela que não existe mais; a de outro HaradaER aberto fica com ele.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths

from haradaer.core import io
from haradaer.core.model import Document


def recovery_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)
    return Path(base) / "HaradaER" / "recuperacao"


@dataclass(frozen=True)
class Leftover:
    """Uma cópia que sobrou de uma janela que fechou sem salvar nem descartar."""

    copy: Path
    original: Path | None
    when: datetime

    def discard(self) -> None:
        _remove(self.copy)


def _meta(copia: Path) -> Path:
    return copia.with_suffix(".json")


def _lock(copia: Path) -> Path:
    return copia.with_suffix(".lock")


def _remove(copia: Path) -> None:
    for arquivo in (copia, _meta(copia), _lock(copia)):
        arquivo.unlink(missing_ok=True)


class RecoveryCopy:
    """A cópia de recuperação de uma janela. Só cria arquivos na primeira gravação."""

    def __init__(self) -> None:
        self.path = recovery_dir() / f"{uuid.uuid4().hex}.xml"
        self._trava: QLockFile | None = None

    @property
    def exists(self) -> bool:
        return self.path.exists()

    def write(self, documento: Document, original: Path | None) -> None:
        """Grava o modelo e de onde ele é. Pode lançar `OSError`."""
        if self._trava is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            trava = QLockFile(str(_lock(self.path)))
            trava.setStaleLockTime(0)  # só o processo morto libera a trava, nunca o tempo
            if not trava.tryLock(0):
                raise OSError(f"cópia de recuperação em uso: {self.path}")
            self._trava = trava
        io.save(documento, self.path)
        dados = {
            "original": str(original) if original else None,
            "hora": datetime.now().isoformat(timespec="seconds"),
        }
        _meta(self.path).write_text(json.dumps(dados), encoding="utf-8")

    def remove(self) -> None:
        """Apaga a cópia (ao salvar, descartar ou fechar a janela)."""
        if self._trava is not None:
            self._trava.unlock()
            self._trava = None
        _remove(self.path)


def leftovers() -> list[Leftover]:
    """As cópias que sobraram, da mais nova à mais antiga; as de janelas abertas ficam de fora."""
    pasta = recovery_dir()
    if not pasta.is_dir():
        return []
    achadas: list[Leftover] = []
    for copia in pasta.glob("*.xml"):
        trava = QLockFile(str(_lock(copia)))
        trava.setStaleLockTime(0)
        if not trava.tryLock(0):
            continue  # de uma janela aberta, neste ou em outro HaradaER
        trava.unlock()
        try:
            dados = json.loads(_meta(copia).read_text(encoding="utf-8"))
            original = Path(dados["original"]) if dados.get("original") else None
            hora = datetime.fromisoformat(dados["hora"])
        except OSError, ValueError, KeyError, TypeError:
            original = None
            hora = datetime.fromtimestamp(copia.stat().st_mtime)
        achadas.append(Leftover(copia, original, hora))
    return sorted(achadas, key=lambda s: s.when, reverse=True)
