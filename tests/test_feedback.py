"""Endereço da issue para relatar um problema ou sugerir uma melhoria (RF-21)."""

import getpass
from urllib.parse import parse_qs, urlsplit

from haradaer import feedback


def _campos(url: str) -> dict[str, str]:
    partes = urlsplit(url)
    assert f"{partes.scheme}://{partes.netloc}{partes.path}" == (
        f"{feedback.REPOSITORIO}/issues/new"
    )
    return {chave: valor[0] for chave, valor in parse_qs(partes.query).items()}


def test_bug_leva_versao_sistema_e_idioma():
    url = feedback.issue_url("bug", "1.1.0", "Linux 6.18 (Wayland)", "pt")
    assert _campos(url) == {
        "template": "bug.yml",
        "versao": "1.1.0",
        "sistema": "Linux 6.18 (Wayland)",
        "idioma": "pt",
    }
    assert " " not in url  # espaços e parênteses codificados


def test_melhoria_nao_pergunta_o_sistema():
    url = feedback.issue_url("melhoria", "1.1.0", "Windows 11", "en")
    assert _campos(url) == {"template": "melhoria.yml", "versao": "1.1.0", "idioma": "en"}


def test_sistema_sem_dados_pessoais():
    texto = feedback.system_description()
    assert texto
    assert getpass.getuser() not in texto


def test_sessao_do_linux(monkeypatch):
    monkeypatch.setattr(feedback.platform, "system", lambda: "Linux")
    monkeypatch.setattr(feedback.platform, "release", lambda: "6.18")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert feedback.system_description() == "Linux 6.18 (Wayland)"
    monkeypatch.delenv("XDG_SESSION_TYPE")
    assert feedback.system_description() == "Linux 6.18"


def test_formularios_tem_os_campos_preenchidos():
    from pathlib import Path

    pasta = Path(__file__).resolve().parents[1] / ".github" / "ISSUE_TEMPLATE"
    bug = (pasta / "bug.yml").read_text("utf-8")
    melhoria = (pasta / "melhoria.yml").read_text("utf-8")
    for campo in ("versao", "sistema", "idioma"):
        assert f"id: {campo}\n" in bug
    for campo in ("versao", "idioma"):
        assert f"id: {campo}\n" in melhoria
