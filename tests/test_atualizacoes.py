"""Versão nova (RF-22): comparação de versões e leitura da resposta do GitHub, sem rede."""

import json
from datetime import date

import pytest

from haradaer import updates

# A real: o `sem_rede` do conftest troca `updates.fetch_latest` em cada teste.
FETCH_LATEST = updates.fetch_latest


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


def test_le_a_versao_do_redirecionamento():
    url = "https://github.com/PedroHarada/HaradaER/releases/tag/v1.3.0"
    assert updates.latest_from_url(url) == "1.3.0"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/PedroHarada/HaradaER/releases",  # nenhuma versão publicada
        "https://github.com/PedroHarada/HaradaER/releases/tag/nightly",
    ],
)
def test_redirecionamento_estranho_e_falha(url):
    with pytest.raises(OSError):
        updates.latest_from_url(url)


class _Resposta:
    def __init__(self, url):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url


@pytest.mark.parametrize("codigo", [403, 429])
def test_limite_da_api_usa_a_pagina_de_versoes(monkeypatch, codigo):
    from urllib import request
    from urllib.error import HTTPError

    pedidos = []

    def abrir(pedido, timeout, context):
        pedidos.append(pedido.full_url)
        if pedido.full_url == updates.API:
            raise HTTPError(updates.API, codigo, "rate limit exceeded", {}, None)
        return _Resposta("https://github.com/PedroHarada/HaradaER/releases/tag/v9.9.9")

    monkeypatch.setattr(request, "urlopen", abrir)
    assert FETCH_LATEST() == "9.9.9"
    assert pedidos == [updates.API, updates.RELEASES]


def test_outro_erro_da_api_nao_tenta_a_pagina(monkeypatch):
    from urllib import request
    from urllib.error import HTTPError

    def abrir(pedido, timeout, context):
        raise HTTPError(pedido.full_url, 500, "Server Error", {}, None)

    monkeypatch.setattr(request, "urlopen", abrir)
    with pytest.raises(HTTPError):
        FETCH_LATEST()


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
