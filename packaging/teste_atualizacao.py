"""Teste de ponta a ponta da atualização (RF-22), rodado pelo workflow de versão em cada sistema.

Uso: python packaging/teste_atualizacao.py SISTEMA PACOTE PROGRAMA

Publica o PACOTE recém-gerado (com o SHA256SUMS) num servidor local, copia o PROGRAMA gerado
para uma pasta "instalada" e roda `HaradaER --atualizar` dessa cópia, com a versão forçada para a
do próprio código. Confere que a cópia foi trocada pelo programa do pacote (o antigo virou `.old`)
e que o programa novo passa no autoteste. É o único lugar em que a troca roda no Windows e no
macOS de verdade.
"""

from __future__ import annotations

import functools
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import haradaer
from haradaer import selfupdate


def main(sistema: str, pacote: Path, programa: Path) -> int:
    versao = haradaer.__version__
    nome = selfupdate.asset_name(versao, sistema, {"macos": "arm64"}.get(sistema, "x86_64"))
    assert nome is not None
    raiz = Path(tempfile.mkdtemp(prefix="haradaer-atualizacao-"))
    servidor = raiz / "servidor"
    servidor.mkdir()
    shutil.copyfile(pacote, servidor / nome)
    soma = hashlib.sha256((servidor / nome).read_bytes()).hexdigest()
    (servidor / selfupdate.SUMS).write_text(f"{soma}  {nome}\n", encoding="utf-8")

    http = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(servidor))
    )
    threading.Thread(target=http.serve_forever, daemon=True).start()

    instalado = raiz / "instalado" / programa.name
    instalado.parent.mkdir()
    if programa.is_dir():
        shutil.copytree(programa, instalado, symlinks=True)
    else:
        shutil.copy2(programa, instalado)
    exe = selfupdate.executable(instalado, sistema)

    ambiente = {
        **selfupdate.child_env(),
        selfupdate.BASE_ENV: f"http://127.0.0.1:{http.server_address[1]}",
        selfupdate.VERSION_ENV: versao,
        "QT_QPA_PLATFORM": "offscreen",
    }
    log = raiz / "atualizar.txt"
    with log.open("w") as saida:
        codigo = subprocess.run(
            [str(exe), "--atualizar"], env=ambiente, stdout=saida, stderr=saida, timeout=600
        ).returncode
    http.shutdown()
    print(log.read_text(errors="replace"))
    if codigo != 0:
        print(f"--atualizar terminou com {codigo}")
        return 1
    alvo = selfupdate.Target(instalado, sistema)
    falhas = []
    if not alvo.old.exists():
        falhas.append("o antigo não virou .old")
    if not instalado.exists():
        falhas.append("o programa novo não está no lugar")
    if falhas:
        print("; ".join(falhas))
        return 1
    resultado = raiz / "autoteste.txt"
    codigo = subprocess.run(
        [str(selfupdate.executable(instalado, sistema)), "--autoteste", str(resultado)],
        env=ambiente,
        timeout=300,
    ).returncode
    print(resultado.read_text("utf-8") if resultado.exists() else "(sem resultado do autoteste)")
    if codigo != 0:
        return 1
    print("troca: ok")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.exit(main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])))
