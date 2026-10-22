"""Endereço para relatar um problema ou sugerir uma melhoria no GitHub (RF-21).

O programa só abre a página da issue já preenchida no navegador; nada é enviado sem que a
pessoa veja e confirme. Os campos são os `id` dos formulários em `.github/ISSUE_TEMPLATE/`.
"""

from __future__ import annotations

import os
import platform
from typing import Literal
from urllib.parse import urlencode

REPOSITORIO = "https://github.com/PedroHarada/HaradaER"

Tipo = Literal["bug", "melhoria"]


def issue_url(tipo: Tipo, versao: str, sistema: str, idioma: str) -> str:
    campos = {"template": f"{tipo}.yml", "versao": versao, "idioma": idioma}
    if tipo == "bug":
        campos["sistema"] = sistema  # o formulário de melhoria não pergunta o sistema
    return f"{REPOSITORIO}/issues/new?{urlencode(campos)}"


def system_description() -> str:
    """Sistema e versão, sem nada pessoal (nome de usuário, pastas ou arquivos abertos)."""
    sistema = platform.system()
    if sistema == "Darwin":
        return f"macOS {platform.mac_ver()[0]}".strip()
    if sistema == "Windows":
        return f"Windows {platform.release()} ({platform.version()})"
    texto = f"{sistema} {platform.release()}".strip()
    sessao = os.environ.get("XDG_SESSION_TYPE")
    return f"{texto} ({sessao.capitalize()})" if sessao else texto
