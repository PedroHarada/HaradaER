"""Autoteste do executável (`HaradaER --autoteste SAIDA.txt`), rodado pelo workflow de versão.

Confere o que só aparece no programa empacotado e escapou dos testes comuns: o Qt abre uma
janela, nada que ficou de fora do pacote voltou (o teclado virtual é só GPLv3) e a conexão segura
com o GitHub funciona com o OpenSSL empacotado (na 1.1.1 ela falhava fora do Ubuntu). O
resultado vai para um arquivo, porque o executável do Windows não tem console.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Igual a FORA_DO_PACOTE em packaging/HaradaER.spec (um teste confere).
PROIBIDOS = (
    "virtualkeyboard",
    "qtquick",
    "qt6quick",
    "qtqml",
    "qt6qml",
    "qtpdf",
    "qt6pdf",
    "qpdf",
)


def bundled_forbidden(pasta: Path) -> list[str]:
    """Arquivos do pacote cujo nome tem algo de `PROIBIDOS`."""
    return sorted(
        str(caminho.relative_to(pasta))
        for caminho in pasta.rglob("*")
        if any(nome in caminho.name.lower() for nome in PROIBIDOS)
    )


def check_window() -> str:
    from PySide6.QtWidgets import QApplication

    from haradaer.gui.window import DocumentWindow

    app = QApplication.instance() or QApplication(["HaradaER"])
    janela = DocumentWindow()
    janela.show()
    app.processEvents()
    janela.close()
    return "janela: ok"


def check_tls() -> str:
    """Só a conexão segura importa: qualquer resposta HTTP (até 404 ou limite de consultas)
    prova que o certificado do GitHub foi aceito."""
    from urllib.error import HTTPError

    from haradaer import updates

    try:
        return f"conexão segura: ok (versão publicada {updates.fetch_latest()})"
    except HTTPError as resposta:
        return f"conexão segura: ok (GitHub respondeu {resposta.code})"


def run(saida: Path) -> int:
    linhas: list[str] = []
    falhou = False
    pasta = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else None  # dentro do pacote
    verificacoes = [check_window, check_tls]
    for verificar in verificacoes:
        try:
            linhas.append(verificar())
        except Exception as erro:  # noqa: BLE001 (o autoteste relata qualquer falha)
            falhou = True
            linhas.append(f"{verificar.__name__}: FALHOU: {type(erro).__name__}: {erro}")
    if pasta is not None:
        achados = bundled_forbidden(pasta)
        if achados:
            falhou = True
            linhas.append("arquivos que deviam ficar de fora: " + ", ".join(achados))
        else:
            linhas.append("arquivos de fora do pacote: nenhum")
    linhas.append("RESULTADO: FALHOU" if falhou else "RESULTADO: ok")
    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return 1 if falhou else 0


def main(argv: list[str]) -> int | None:
    """`None` se não for o autoteste (o programa abre normalmente)."""
    if len(argv) != 3 or argv[1] != "--autoteste":
        return None
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return run(Path(argv[2]))
