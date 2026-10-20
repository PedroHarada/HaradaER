"""Critério 1 de REQUISITOS.md (seção 7): ler e regravar os arquivos do TerraER sem mudar nada."""

import pytest

from haradaer.core import io

GOLDEN = [
    "amostra-basica.xml",
    "amostra-todos-os-tipos.xml",
    "amostra-escapes-e-numeros.xml",
    "amostra-ordem-empilhamento.xml",
    "amostra-figuras-de-apoio.xml",
    "amostra-numeros.xml",
    "amostra-unicode.xml",
    "amostra-vazios.xml",
    "amostra-conexoes-incompletas.xml",
]


@pytest.mark.parametrize("nome", GOLDEN)
def test_ida_e_volta_identica_ao_terraer(referencia, nome):
    original = (referencia / nome).read_bytes()
    regravado = io.dumps(io.loads(original)).encode("ascii")
    assert regravado == original


@pytest.mark.parametrize("nome", GOLDEN)
def test_regravar_duas_vezes_da_o_mesmo(referencia, nome):
    primeiro = io.dumps(io.loads((referencia / nome).read_bytes()))
    assert io.dumps(io.loads(primeiro)) == primeiro


def test_salvar_e_abrir_arquivo(referencia, tmp_path):
    original = (referencia / "amostra-todos-os-tipos.xml").read_bytes()
    destino = tmp_path / "modelo.xml"
    io.save(io.loads(original), destino)
    assert destino.read_bytes() == original
    assert [p.name for p in tmp_path.iterdir()] == ["modelo.xml"], "sem arquivo temporário sobrando"


def test_salvar_nao_corrompe_o_original_se_falhar(referencia, tmp_path, monkeypatch):
    destino = tmp_path / "modelo.xml"
    destino.write_bytes(b"conteudo antigo")
    documento = io.loads((referencia / "amostra-basica.xml").read_bytes())

    def falhar(*_args):
        raise OSError("disco cheio")

    monkeypatch.setattr(io.os, "replace", falhar)
    with pytest.raises(OSError, match="disco cheio"):
        io.save(documento, destino)
    assert destino.read_bytes() == b"conteudo antigo"
    assert [p.name for p in tmp_path.iterdir()] == ["modelo.xml"]
