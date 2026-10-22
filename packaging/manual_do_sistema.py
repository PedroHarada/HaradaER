"""Tira do manual o de um sistema só, para ir dentro do pacote dele.

    python packaging/manual_do_sistema.py linux|windows|macos SAIDA.txt [pt|en]

O idioma é `pt` (`docs/PRIMEIROS-PASSOS.md`) se não for dito; `en` usa `docs/GETTING-STARTED.md`.
Fica a introdução (com a linha da tabela só daquele sistema), a seção do sistema e "Depois de
abrir". As seções do manual são separadas por `---`; cada uma começa com `## <Sistema>`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

DOCS = Path(__file__).resolve().parent.parent / "docs"
SISTEMAS = {"linux": "Linux", "windows": "Windows", "macos": "macOS"}


class Idioma(NamedTuple):
    manual: Path
    depois: str  # título da última seção, igual em todos os sistemas
    cada_sistema: str  # trecho da introdução que vira "no <sistema>"
    no_sistema: str
    teclas: str  # trecho com as duas teclas, que fica só com a do sistema
    ctrl: str
    cmd: str


IDIOMAS = {
    "pt": Idioma(
        DOCS / "PRIMEIROS-PASSOS.md",
        "Depois de abrir",
        "abrir e instalar o HaradaER em cada sistema",
        "abrir e instalar o HaradaER no {nome}",
        "Ctrl + clique; no Mac, Cmd + clique",
        "Ctrl + clique",
        "Cmd + clique",
    ),
    "en": Idioma(
        DOCS / "GETTING-STARTED.md",
        "After opening",
        "open and install HaradaER on each system",
        "open and install HaradaER on {nome}",
        "Ctrl-click; on a Mac, Cmd-click",
        "Ctrl-click",
        "Cmd-click",
    ),
}
MANUAL = IDIOMAS["pt"].manual
DEPOIS = IDIOMAS["pt"].depois


def _titulo(secao: str) -> str:
    m = re.search(r"^## (.+)$", secao, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _sem_links(texto: str) -> str:
    """Fora do GitHub, os links viram texto (`[Linux](#linux)` -> `Linux`), e a linha que manda
    ao README sai: quem baixou o pacote pode não ter acesso ao repositório."""
    linhas = [linha for linha in texto.splitlines() if "README.md" not in linha]
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", "\n".join(linhas)).rstrip("\n")


def manual_de(sistema: str, texto: str, idioma: str = "pt") -> str:
    config = IDIOMAS[idioma]
    nome = SISTEMAS[sistema]
    secoes = [s.strip("\n") for s in re.split(r"^---$", texto, flags=re.MULTILINE)]
    introducao, resto = secoes[0], secoes[1:]
    linhas = [
        linha
        for linha in introducao.splitlines()
        if not linha.startswith("| [") or linha.startswith(f"| [{nome}]")
    ]
    introducao = "\n".join(linhas).replace(config.cada_sistema, config.no_sistema.format(nome=nome))
    proprias = [s for s in resto if _titulo(s) in (nome, config.depois)]
    if [_titulo(s) for s in proprias] != [nome, config.depois]:
        raise ValueError(f"o manual não tem as seções '{nome}' e '{config.depois}'")
    juntas = "\n\n---\n\n".join([introducao, *proprias])
    # Só a tecla do próprio sistema: Cmd no Mac, Ctrl nos outros.
    tecla = config.cmd if sistema == "macos" else config.ctrl
    return _sem_links(juntas).replace(config.teclas, tecla) + "\n"


def main(argv: list[str]) -> int:
    idioma = argv[3] if len(argv) == 4 else "pt"
    if len(argv) not in (3, 4) or argv[1] not in SISTEMAS or idioma not in IDIOMAS:
        print(__doc__, file=sys.stderr)
        return 2
    texto = IDIOMAS[idioma].manual.read_text(encoding="utf-8")
    Path(argv[2]).write_text(manual_de(argv[1], texto, idioma), "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
