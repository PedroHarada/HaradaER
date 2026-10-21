"""Tira de `docs/PRIMEIROS-PASSOS.md` o manual de um sistema só, para ir dentro do pacote dele.

    python packaging/manual_do_sistema.py linux|windows|macos SAIDA.txt

Fica a introdução (com a linha da tabela só daquele sistema), a seção do sistema e "Depois de
abrir". As seções do manual são separadas por `---`; cada uma começa com `## <Sistema>`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MANUAL = Path(__file__).resolve().parent.parent / "docs" / "PRIMEIROS-PASSOS.md"
SISTEMAS = {"linux": "Linux", "windows": "Windows", "macos": "macOS"}
DEPOIS = "Depois de abrir"


def _titulo(secao: str) -> str:
    m = re.search(r"^## (.+)$", secao, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _sem_links(texto: str) -> str:
    """Fora do GitHub, os links viram texto (`[Linux](#linux)` -> `Linux`), e a linha que manda
    ao README sai: quem baixou o pacote pode não ter acesso ao repositório."""
    linhas = [linha for linha in texto.splitlines() if "README.md" not in linha]
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", "\n".join(linhas)).rstrip("\n")


def _teclas(texto: str, sistema: str) -> str:
    """Só a tecla do próprio sistema: Cmd no Mac, Ctrl nos outros."""
    tecla = "Cmd + clique" if sistema == "macos" else "Ctrl + clique"
    return texto.replace("Ctrl + clique; no Mac, Cmd + clique", tecla)


def manual_de(sistema: str, texto: str) -> str:
    nome = SISTEMAS[sistema]
    secoes = [s.strip("\n") for s in re.split(r"^---$", texto, flags=re.MULTILINE)]
    introducao, resto = secoes[0], secoes[1:]
    linhas = [
        linha
        for linha in introducao.splitlines()
        if not linha.startswith("| [") or linha.startswith(f"| [{nome}]")
    ]
    introducao = "\n".join(linhas).replace(
        "abrir e instalar o HaradaER em cada sistema", f"abrir e instalar o HaradaER no {nome}"
    )
    proprias = [s for s in resto if _titulo(s) in (nome, DEPOIS)]
    if [_titulo(s) for s in proprias] != [nome, DEPOIS]:
        raise ValueError(f"o manual não tem as seções '{nome}' e '{DEPOIS}'")
    juntas = "\n\n---\n\n".join([introducao, *proprias])
    return _teclas(_sem_links(juntas), sistema) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in SISTEMAS:
        print(__doc__, file=sys.stderr)
        return 2
    Path(argv[2]).write_text(manual_de(argv[1], MANUAL.read_text(encoding="utf-8")), "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
