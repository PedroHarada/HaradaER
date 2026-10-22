"""Versão nova (RF-22): comparação de versões e leitura da resposta do GitHub, sem rede."""

import json
from datetime import date

import pytest

from haradaer import updates


@pytest.mark.parametrize(
    ("nova", "atual", "esperado"),
    [
        ("1.1.0", "1.0.1", True),
        ("v1.0.2", "1.0.1", True),
        ("2.0.0", "1.9.9", True),
        ("1.10.0", "1.9.0", True),  # número, não texto
        ("1.1.0", "1.1.0", False),
        ("1.0.9", "1.1.0", False),
        ("1.1.0", "1.1.0-rc1", True),  # a final vem depois da pré-versão
        ("1.1.0-rc2", "1.1.0", False),
        ("lixo", "1.1.0", False),
    ],
)
def test_compara_versoes(nova, atual, esperado):
    assert updates.is_newer(nova, atual) is esperado


def test_le_a_etiqueta_do_github():
    assert updates.latest_from_json(json.dumps({"tag_name": "v1.2.0"}).encode()) == "1.2.0"


@pytest.mark.parametrize("dados", [b"<html>", b"{}", b'{"tag_name": 3}', b'{"tag_name": "x"}'])
def test_resposta_estranha_e_falha_de_rede(dados):
    with pytest.raises(OSError):
        updates.latest_from_json(dados)


def test_uma_vez_por_dia():
    hoje = date(2026, 10, 22)
    assert updates.due_today(None, hoje)
    assert updates.due_today("2026-10-21", hoje)
    assert not updates.due_today("2026-10-22", hoje)


def test_contexto_carrega_os_certificados_do_sistema(tmp_path, monkeypatch):
    carregados = []
    original = updates.ssl.SSLContext.load_verify_locations

    def carregar(self, cafile=None, capath=None, cadata=None):
        if cafile is None:  # no Windows, os certificados do sistema chegam por `cadata`
            return original(self, cafile, capath, cadata)
        carregados.append(cafile)
        return None

    monkeypatch.setattr(updates.ssl.SSLContext, "load_verify_locations", carregar)
    existe = tmp_path / "ca.pem"
    existe.write_text("x")
    updates.ssl_context((str(tmp_path / "nao-existe.pem"), str(existe), str(existe)))
    assert carregados == [str(existe)]  # só o primeiro que existe


def test_contexto_sem_arquivo_do_sistema_fica_o_padrao(tmp_path):
    contexto = updates.ssl_context((str(tmp_path / "nao-existe.pem"),))
    assert contexto.verify_mode == updates.ssl.CERT_REQUIRED
