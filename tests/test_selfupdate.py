"""Atualização pelo próprio programa (RF-22, 1.4.0), sem rede: os pacotes vêm de uma pasta local
(`file://`) e o autoteste do programa novo é trocado por uma resposta fixa."""

import hashlib
import io
import os
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

import haradaer
from haradaer import selfupdate, updates
from haradaer.selfupdate import Target, UpdateError


@pytest.mark.parametrize(
    ("sistema", "maquina", "esperado"),
    [
        ("linux", "x86_64", "HaradaER-v1.4.0-linux.tar.gz"),
        ("windows", "AMD64", "HaradaER-v1.4.0-windows.zip"),
        ("macos", "arm64", "HaradaER-v1.4.0-macos.zip"),
        ("macos", "x86_64", None),  # Mac Intel: não há pacote
        ("linux", "aarch64", None),
    ],
)
def test_nome_do_pacote(sistema, maquina, esperado):
    assert selfupdate.asset_name("1.4.0", sistema, maquina) == esperado


def test_programa_instalado_em_cada_sistema(tmp_path):
    assert selfupdate.install_target(congelado=False) is None  # código-fonte
    exe = str(tmp_path / "HaradaER")
    assert selfupdate.install_target(True, exe, "linux") == Target(Path(exe), "linux")
    app = tmp_path / "HaradaER.app"
    dentro = str(app / "Contents" / "MacOS" / "HaradaER")
    assert selfupdate.install_target(True, dentro, "darwin") == Target(app, "macos")
    assert selfupdate.install_target(True, exe, "win32").sistema == "windows"


def test_quando_nao_oferecer(tmp_path, monkeypatch):
    assert "Releases" in selfupdate.why_not(None)
    alvo = Target(tmp_path / "HaradaER", "linux")
    assert selfupdate.why_not(alvo, "x86_64") is None
    assert "aarch64" in selfupdate.why_not(alvo, "aarch64")
    mac = Target(Path("/private/var/folders/x/AppTranslocation/y/d/HaradaER.app"), "macos")
    assert "Aplicativos" in selfupdate.why_not(mac, "arm64")
    monkeypatch.setattr(selfupdate.os, "access", lambda caminho, modo: False)
    assert "permissão" in selfupdate.why_not(alvo, "x86_64")


def test_le_o_sha256sums():
    a, b = "a" * 64, "B" * 64
    texto = f"{a}  HaradaER-v1.4.0-linux.tar.gz\n{b} *HaradaER-v1.4.0-windows.zip\nlixo\n"
    assert selfupdate.parse_sums(texto) == {
        "HaradaER-v1.4.0-linux.tar.gz": a,
        "HaradaER-v1.4.0-windows.zip": b.lower(),
    }


def _tar(destino: Path, arquivos: dict[str, bytes]) -> Path:
    with tarfile.open(destino, "w:gz") as tar:
        for nome, dados in arquivos.items():
            info = tarfile.TarInfo(nome)
            info.size, info.mode = len(dados), 0o755
            tar.addfile(info, io.BytesIO(dados))
    return destino


def test_tar_com_caminho_para_fora_e_recusado(tmp_path):
    pacote = _tar(tmp_path / "p.tar.gz", {"../fora": b"x"})
    with pytest.raises(UpdateError):
        selfupdate.extract(pacote, tmp_path / "dest", "linux")
    assert not (tmp_path / "fora").exists()


@pytest.mark.parametrize("nome", ["/absoluto.exe", "../fora.exe", "C:/fora.exe"])
def test_zip_com_caminho_para_fora_e_recusado(tmp_path, nome):
    pacote = tmp_path / "p.zip"
    with zipfile.ZipFile(pacote, "w") as zipado:
        zipado.writestr(nome, b"x")
    with pytest.raises(UpdateError):
        selfupdate.extract(pacote, tmp_path / "dest", "windows")


def test_zip_do_windows_e_descompactado(tmp_path):
    pacote = tmp_path / "p.zip"
    with zipfile.ZipFile(pacote, "w") as zipado:
        zipado.writestr("HaradaER.exe", b"novo")
    selfupdate.extract(pacote, tmp_path / "dest", "windows")
    assert selfupdate.payload(tmp_path / "dest", "windows").read_bytes() == b"novo"


@pytest.fixture
def publicado(tmp_path, monkeypatch):
    """Uma versão 9.9.9 do Linux publicada numa pasta local, e o programa instalado ao lado."""
    servidor = tmp_path / "servidor"
    servidor.mkdir()
    pacote = _tar(servidor / "HaradaER-v9.9.9-linux.tar.gz", {"HaradaER": b"novo"})
    soma = hashlib.sha256(pacote.read_bytes()).hexdigest()
    (servidor / "SHA256SUMS").write_text(f"{soma}  {pacote.name}\n")
    monkeypatch.setenv(selfupdate.BASE_ENV, servidor.as_uri())
    instalado = tmp_path / "bin"
    instalado.mkdir()
    (instalado / "HaradaER").write_bytes(b"antigo")
    testados = []
    monkeypatch.setattr(
        selfupdate, "selftest_new", lambda novo, sistema, versao: testados.append(versao)
    )
    return {
        "servidor": servidor,
        "pacote": pacote,
        "alvo": Target(instalado / "HaradaER", "linux"),
        "testados": testados,
    }


def test_prepara_confere_testa_e_troca(publicado):
    alvo = publicado["alvo"]
    progresso = []
    pronto = selfupdate.prepare(
        "9.9.9", alvo, lambda f, t: progresso.append((f, t)), maquina="x86_64"
    )
    assert publicado["testados"] == ["9.9.9"]
    assert progresso and progresso[-1][0] == progresso[-1][1]
    assert alvo.path.read_bytes() == b"antigo"  # preparar não troca nada
    selfupdate.apply(pronto)
    assert alvo.path.read_bytes() == b"novo"
    assert alvo.old.read_bytes() == b"antigo"
    selfupdate.cleanup_old(alvo)
    assert not alvo.old.exists() and not alvo.staging.exists()


def test_download_corrompido_nao_troca(publicado):
    publicado["pacote"].write_bytes(b"cortado")
    with pytest.raises(UpdateError, match="corrompido"):
        selfupdate.prepare("9.9.9", publicado["alvo"], maquina="x86_64")
    assert not publicado["alvo"].staging.exists()
    assert publicado["testados"] == []


def test_versao_sem_o_pacote_no_sha256sums(publicado):
    (publicado["servidor"] / "SHA256SUMS").write_text("")
    with pytest.raises(UpdateError, match="completa"):
        selfupdate.prepare("9.9.9", publicado["alvo"], maquina="x86_64")


def test_cancelar_no_meio_do_download(publicado):
    with pytest.raises(selfupdate.Cancelled):
        selfupdate.prepare("9.9.9", publicado["alvo"], cancelado=lambda: True, maquina="x86_64")
    assert not publicado["alvo"].staging.exists()


def test_programa_novo_que_nao_abre_nao_troca(publicado, monkeypatch):
    def falha(novo, sistema, versao):
        raise UpdateError("A versão nova não abriu neste computador.")

    monkeypatch.setattr(selfupdate, "selftest_new", falha)
    with pytest.raises(UpdateError, match="não abriu"):
        selfupdate.prepare("9.9.9", publicado["alvo"], maquina="x86_64")
    assert publicado["alvo"].path.read_bytes() == b"antigo"
    assert not publicado["alvo"].staging.exists()


def test_falha_na_troca_devolve_o_antigo(publicado, monkeypatch):
    alvo = publicado["alvo"]
    pronto = selfupdate.prepare("9.9.9", alvo, maquina="x86_64")
    original = os.replace

    def replace(origem, destino):
        if Path(origem) == pronto.novo:
            raise PermissionError("ocupado")
        return original(origem, destino)

    monkeypatch.setattr(selfupdate.os, "replace", replace)
    with pytest.raises(UpdateError, match="ocupado"):
        selfupdate.apply(pronto)
    assert alvo.path.read_bytes() == b"antigo"


@pytest.mark.skipif(sys.platform == "win32", reason="o programa falso é um script de shell")
@pytest.mark.parametrize(
    ("resultado", "aceita"),
    [
        ("versão: 9.9.9\nRESULTADO: ok", True),
        ("versão: 9.9.8\nRESULTADO: ok", False),
        ("versão: 9.9.9\nRESULTADO: FALHOU", False),
        (None, False),
    ],
)
def test_autoteste_do_programa_novo(tmp_path, resultado, aceita):
    programa = tmp_path / "HaradaER"
    corpo = f'printf "%s\\n" "{resultado}" > "$2"' if resultado else "exit 1"
    programa.write_text(f"#!/bin/sh\n{corpo}\n")
    programa.chmod(0o755)
    if aceita:
        selfupdate.selftest_new(programa, "linux", "9.9.9")
    else:
        with pytest.raises(UpdateError):
            selfupdate.selftest_new(programa, "linux", "9.9.9")


def test_filho_do_pyinstaller_comeca_do_zero():
    assert selfupdate.child_env()["PYINSTALLER_RESET_ENVIRONMENT"] == "1"


def test_terminal_so_trata_a_opcao_dele():
    assert selfupdate.main(["HaradaER"]) is None
    assert selfupdate.main(["HaradaER", "modelo.xml"]) is None


def test_terminal_do_codigo_fonte_explica(capsys):
    assert selfupdate.main(["HaradaER", "--atualizar"]) == 1
    assert "Releases" in capsys.readouterr().err


def test_terminal_ja_na_mais_recente(publicado, monkeypatch, capsys):
    monkeypatch.setattr(selfupdate, "install_target", lambda: publicado["alvo"])
    monkeypatch.setattr(selfupdate.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updates, "fetch_latest", lambda: haradaer.__version__)
    assert selfupdate.main(["HaradaER", "--atualizar"]) == 0
    assert haradaer.__version__ in capsys.readouterr().out


def test_terminal_atualiza(publicado, monkeypatch):
    monkeypatch.setattr(selfupdate, "install_target", lambda: publicado["alvo"])
    monkeypatch.setattr(selfupdate.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(updates, "fetch_latest", lambda: "9.9.9")
    assert selfupdate.main(["HaradaER", "--atualizar"]) == 0
    assert publicado["alvo"].path.read_bytes() == b"novo"
