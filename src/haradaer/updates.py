"""Aviso de versão nova (RF-22): consulta no GitHub a versão mais recente e compara.

Só lê a página pública de versões; não envia nada sobre quem usa. Sem internet, ou se o GitHub
falhar, `fetch_latest` lança `OSError` e quem chamou não mostra nada.
"""

from __future__ import annotations

import json
import re
from datetime import date

from haradaer.feedback import REPOSITORIO

API = "https://api.github.com/repos/PedroHarada/HaradaER/releases/latest"  # sem pré-versões
RELEASES = f"{REPOSITORIO}/releases/latest"
TIMEOUT = 5  # segundos

_VERSAO = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(-\S+)?$")


def parse_version(texto: str) -> tuple[int, int, int, bool] | None:
    """`v1.2.0` vira (1, 2, 0, True); o último valor é False numa pré-versão (`1.2.0-rc1`),
    que vem antes da versão final de mesmo número."""
    m = _VERSAO.match(texto.strip())
    if not m:
        return None
    return int(m[1]), int(m[2]), int(m[3]), m[4] is None


def is_newer(mais_recente: str, atual: str) -> bool:
    nova, instalada = parse_version(mais_recente), parse_version(atual)
    return nova is not None and instalada is not None and nova > instalada


def latest_from_json(dados: bytes) -> str:
    """A etiqueta (`tag_name`) da resposta do GitHub, sem o `v`."""
    try:
        etiqueta = json.loads(dados)["tag_name"]
    except (ValueError, KeyError, TypeError) as erro:
        raise OSError(f"resposta inesperada do GitHub: {erro}") from erro
    if not isinstance(etiqueta, str) or parse_version(etiqueta) is None:
        raise OSError(f"etiqueta inesperada: {etiqueta!r}")
    return etiqueta.removeprefix("v")


def fetch_latest() -> str:
    """Versão mais recente publicada. Lança `OSError` sem rede ou com resposta estranha."""
    from urllib.request import Request, urlopen

    pedido = Request(API, headers={"Accept": "application/vnd.github+json"})
    with urlopen(pedido, timeout=TIMEOUT) as resposta:  # noqa: S310 (endereço fixo, https)
        return latest_from_json(resposta.read(64 * 1024))


def due_today(ultima: str | None, hoje: date) -> bool:
    """A verificação automática roda no máximo uma vez por dia."""
    return ultima != hoje.isoformat()
