"""Atualização pelo próprio programa (RF-22, desde a 1.4.0): baixa o pacote da versão nova,
confere o SHA-256, testa o programa novo e troca o instalado por ele.

A troca só acontece quando a pessoa pede (botão Atualizar e reiniciar, ou `HaradaER --atualizar`
no terminal). O preparo fica numa pasta ao lado do programa (`.HaradaER-atualizacao`), no mesmo
disco, para a troca ser só renomear: o atual vira `.old` e o novo entra no lugar. O `.old` sai na
abertura seguinte. Sem chave de assinatura (decisão do autor, 2026-11-15): a segurança é a do
download pelo navegador (HTTPS); o SHA-256 pega download corrompido ou pela metade.

Não importa nada de Qt (RNF-08): a janela de progresso fica em `gui/updates.py`.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import haradaer
from haradaer import updates
from haradaer.feedback import REPOSITORIO
from haradaer.i18n import _

DOWNLOAD = f"{REPOSITORIO}/releases/download"
SUMS = "SHA256SUMS"
STAGING = ".HaradaER-atualizacao"
SELFTEST_TIMEOUT = 120  # segundos: o executável de arquivo único se descompacta antes de abrir

# Só para o teste de ponta a ponta do workflow de versão: baixa de outro endereço e força a versão.
BASE_ENV = "HARADAER_ATUALIZACAO_BASE"
VERSION_ENV = "HARADAER_ATUALIZACAO_VERSAO"

# Pacotes publicados: sistema -> (processadores aceitos, extensão do pacote).
PACOTES = {
    "linux": ({"x86_64", "amd64"}, "tar.gz"),
    "windows": ({"amd64", "x86_64"}, "zip"),
    "macos": ({"arm64"}, "zip"),  # só chip Apple
}

Progress = Callable[[int, int], None]  # bytes baixados, total (0 se o servidor não disser)


class UpdateError(Exception):
    """Falha com uma mensagem para mostrar a quem usa. Nada foi trocado."""


class Cancelled(UpdateError):
    pass


def system_name(plataforma: str = sys.platform) -> str:
    if plataforma.startswith("win"):
        return "windows"
    if plataforma == "darwin":
        return "macos"
    return "linux"


def asset_name(versao: str, sistema: str, maquina: str) -> str | None:
    """Nome do pacote deste sistema e processador, ou `None` se não houver pacote."""
    aceitos, extensao = PACOTES[sistema]
    if maquina.lower() not in aceitos:
        return None
    return f"HaradaER-v{versao}-{sistema}.{extensao}"


@dataclass(frozen=True)
class Target:
    """O que a atualização troca: o executável (Linux, Windows) ou o `HaradaER.app` (macOS)."""

    path: Path
    sistema: str

    @property
    def folder(self) -> Path:
        return self.path.parent

    @property
    def old(self) -> Path:
        return self.path.with_name(self.path.name + ".old")

    @property
    def staging(self) -> Path:
        return self.folder / STAGING


def install_target(
    congelado: bool | None = None, executavel: str | None = None, plataforma: str = sys.platform
) -> Target | None:
    """O programa instalado, ou `None` rodando do código-fonte (sem pacote para trocar)."""
    if not (getattr(sys, "frozen", False) if congelado is None else congelado):
        return None
    exe = Path(executavel or sys.executable)
    sistema = system_name(plataforma)
    if sistema == "macos":
        app = exe.parents[2]  # HaradaER.app/Contents/MacOS/HaradaER
        return Target(app, sistema) if app.suffix == ".app" else None
    return Target(exe, sistema)


def why_not(alvo: Target | None, maquina: str | None = None) -> str | None:
    """Por que não dá para atualizar por aqui (fica só o Baixar), ou `None` se dá."""
    if alvo is None:
        return _("A atualização automática só funciona no programa baixado em Releases.")
    maquina = maquina or platform.machine()
    if asset_name("0.0.0", alvo.sistema, maquina) is None:
        return _("Não há pacote do HaradaER para este processador ({maquina}).").format(
            maquina=maquina
        )
    if "/AppTranslocation/" in alvo.path.as_posix():
        return _("Mova o HaradaER para a pasta Aplicativos e abra de lá para poder atualizar.")
    if not os.access(alvo.folder, os.W_OK):
        return _("Sem permissão para gravar na pasta {pasta}.").format(pasta=alvo.folder)
    return None


def base_url(versao: str) -> str:
    return os.environ.get(BASE_ENV) or f"{DOWNLOAD}/v{versao}"


def download(
    url: str,
    destino: Path,
    progresso: Progress | None = None,
    cancelado: Callable[[], bool] | None = None,
) -> None:
    from urllib.request import Request, urlopen

    with urlopen(  # noqa: S310 (endereço fixo do GitHub, ou o do teste de ponta a ponta)
        Request(url), timeout=updates.TIMEOUT, context=updates.ssl_context()
    ) as resposta:
        total = int(resposta.headers.get("Content-Length") or 0)
        feito = 0
        with destino.open("wb") as arquivo:
            while bloco := resposta.read(256 * 1024):
                if cancelado and cancelado():
                    raise Cancelled(_("Atualização cancelada."))
                arquivo.write(bloco)
                feito += len(bloco)
                if progresso:
                    progresso(feito, total)


def parse_sums(texto: str) -> dict[str, str]:
    """Linhas do `sha256sum` (`hash  nome` ou `hash *nome`) -> {nome: hash}."""
    somas = {}
    for linha in texto.splitlines():
        partes = linha.strip().split(maxsplit=1)
        if len(partes) == 2 and len(partes[0]) == 64:
            somas[partes[1].lstrip("*")] = partes[0].lower()
    return somas


def sha256(arquivo: Path) -> str:
    resumo = hashlib.sha256()
    with arquivo.open("rb") as entrada:
        while bloco := entrada.read(1024 * 1024):
            resumo.update(bloco)
    return resumo.hexdigest()


def extract(pacote: Path, destino: Path, sistema: str) -> None:
    """Descompacta sem deixar nada sair de `destino`."""
    destino.mkdir(parents=True, exist_ok=True)
    try:
        if pacote.name.endswith(".tar.gz"):
            with tarfile.open(pacote, "r:gz") as tar:
                tar.extractall(destino, filter="data")  # recusa caminho absoluto, `..` e links
        elif sistema == "macos":
            # O zipfile perde os links simbólicos e as permissões de dentro do .app.
            subprocess.run(["ditto", "-x", "-k", str(pacote), str(destino)], check=True)
        else:
            with zipfile.ZipFile(pacote) as zipado:
                for nome in zipado.namelist():
                    caminho = PurePosixPath(nome.replace("\\", "/"))
                    if caminho.is_absolute() or ".." in caminho.parts or ":" in nome:
                        raise UpdateError(_("O pacote baixado tem um caminho inválido."))
                zipado.extractall(destino)
    except (tarfile.TarError, zipfile.BadZipFile, subprocess.CalledProcessError) as erro:
        raise UpdateError(_("O pacote baixado não pôde ser aberto.")) from erro


def payload(pasta: Path, sistema: str) -> Path:
    """O programa novo dentro do pacote descompactado."""
    nome = {"linux": "HaradaER", "windows": "HaradaER.exe", "macos": "HaradaER.app"}[sistema]
    caminho = pasta / nome
    if not caminho.exists():
        raise UpdateError(_("O pacote baixado não tem o programa."))
    return caminho


def executable(programa: Path, sistema: str) -> Path:
    return programa / "Contents" / "MacOS" / "HaradaER" if sistema == "macos" else programa


def child_env() -> dict[str, str]:
    """Ambiente para abrir outro executável do PyInstaller a partir deste: sem a variável, o
    filho de um executável de arquivo único usaria a pasta descompactada do pai."""
    return {**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"}


def selftest_new(programa: Path, sistema: str, versao: str) -> None:
    """Abre o programa novo no modo autoteste: ele tem de passar e dizer a versão esperada."""
    saida = programa.parent / "autoteste.txt"
    try:
        subprocess.run(
            [str(executable(programa, sistema)), "--autoteste", str(saida)],
            env=child_env(),
            timeout=SELFTEST_TIMEOUT,
            check=False,
        )
        linhas = saida.read_text("utf-8").splitlines()
    except (OSError, subprocess.SubprocessError) as erro:
        raise UpdateError(_("A versão nova não abriu neste computador.")) from erro
    if "RESULTADO: ok" not in linhas or f"versão: {versao}" not in linhas:
        raise UpdateError(_("A versão nova não abriu neste computador."))


@dataclass(frozen=True)
class Prepared:
    """Versão nova baixada, conferida e testada, pronta para `apply`."""

    versao: str
    alvo: Target
    novo: Path


def prepare(
    versao: str,
    alvo: Target,
    progresso: Progress | None = None,
    cancelado: Callable[[], bool] | None = None,
    maquina: str | None = None,
) -> Prepared:
    """Baixa, confere, descompacta e testa. Em qualquer falha apaga o preparo e lança
    `UpdateError`; o programa instalado não é tocado."""
    from urllib.error import HTTPError

    nome = asset_name(versao, alvo.sistema, maquina or platform.machine())
    if nome is None:
        raise UpdateError(_("Não há pacote do HaradaER para este processador."))
    shutil.rmtree(alvo.staging, ignore_errors=True)
    alvo.staging.mkdir()
    base = base_url(versao)
    incompleta = _("A versão {versao} ainda não está completa no GitHub. Tente mais tarde.")
    try:
        somas = alvo.staging / SUMS
        try:
            download(f"{base}/{SUMS}", somas, cancelado=cancelado)
        except HTTPError as erro:
            raise UpdateError(incompleta.format(versao=versao)) from erro
        esperado = parse_sums(somas.read_text("utf-8")).get(nome)
        if esperado is None:
            raise UpdateError(incompleta.format(versao=versao))
        pacote = alvo.staging / nome
        try:
            download(f"{base}/{nome}", pacote, progresso, cancelado)
        except HTTPError as erro:
            raise UpdateError(incompleta.format(versao=versao)) from erro
        if sha256(pacote) != esperado:
            raise UpdateError(_("O download veio corrompido. Tente de novo."))
        extraido = alvo.staging / "novo"
        extract(pacote, extraido, alvo.sistema)
        pacote.unlink()
        novo = payload(extraido, alvo.sistema)
        selftest_new(novo, alvo.sistema, versao)
        return Prepared(versao, alvo, novo)
    except UpdateError:
        shutil.rmtree(alvo.staging, ignore_errors=True)
        raise
    except OSError as erro:
        shutil.rmtree(alvo.staging, ignore_errors=True)
        raise UpdateError(
            _("Não foi possível baixar a versão nova ({erro}).").format(erro=erro)
        ) from erro


def _remove(caminho: Path) -> None:
    if caminho.is_dir() and not caminho.is_symlink():
        shutil.rmtree(caminho)
    elif caminho.exists() or caminho.is_symlink():
        caminho.unlink()


def apply(preparado: Prepared) -> None:
    """Troca o programa: o atual vira `.old` e o novo entra no lugar. Se o segundo passo
    falhar, o atual volta."""
    alvo = preparado.alvo
    try:
        _remove(alvo.old)
        os.replace(alvo.path, alvo.old)
    except OSError as erro:
        raise UpdateError(
            _("Não foi possível trocar o programa ({erro}).").format(erro=erro)
        ) from erro
    try:
        os.replace(preparado.novo, alvo.path)
    except OSError as erro:
        os.replace(alvo.old, alvo.path)
        raise UpdateError(
            _("Não foi possível trocar o programa ({erro}).").format(erro=erro)
        ) from erro


def restart(alvo: Target) -> None:
    """Abre o programa trocado, separado deste processo, que está fechando."""
    if alvo.sistema == "macos":
        comando = ["open", "-n", str(alvo.path)]
    else:
        comando = [str(alvo.path)]
    opcoes: dict = {"env": child_env()}
    if alvo.sistema == "windows":
        opcoes["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        opcoes["start_new_session"] = True
    subprocess.Popen(comando, **opcoes)  # noqa: S603


def cleanup_old(alvo: Target | None) -> None:
    """Na abertura: apaga o `.old` de uma troca anterior e um preparo que ficou pela metade.
    Se algo estiver preso (o Windows ainda fechando o antigo), fica para a próxima."""
    if alvo is None:
        return
    for caminho in (alvo.old, alvo.staging):
        try:
            _remove(caminho)
        except OSError:
            pass


def latest_version() -> str:
    """A versão publicada mais recente, ou a forçada nos testes de ponta a ponta. Lança
    `OSError` sem rede."""
    return os.environ.get(VERSION_ENV) or updates.fetch_latest()


def _target_version() -> str | None:
    """A versão para instalar, ou `None` se já é a mais recente (a forçada sempre vale)."""
    versao = latest_version()
    forcada = bool(os.environ.get(VERSION_ENV))
    return versao if forcada or updates.is_newer(versao, haradaer.__version__) else None


def main(argv: list[str]) -> int | None:
    """`HaradaER --atualizar` no terminal. `None` se não for essa opção."""
    if len(argv) != 2 or argv[1] != "--atualizar":
        return None
    alvo = install_target()
    cleanup_old(alvo)
    motivo = why_not(alvo)
    if motivo:
        print(motivo, file=sys.stderr)
        return 1
    assert alvo is not None
    try:
        versao = _target_version()
    except OSError as erro:
        print(_("Não foi possível verificar agora ({erro}).").format(erro=erro), file=sys.stderr)
        return 1
    if versao is None:
        print(_("Você já tem a versão mais recente ({atual}).").format(atual=haradaer.__version__))
        return 0
    print(_("Baixando o HaradaER {versao}…").format(versao=versao))
    try:
        apply(prepare(versao, alvo))
    except UpdateError as erro:
        print(str(erro), file=sys.stderr)
        return 1
    print(_("HaradaER atualizado para a {versao}.").format(versao=versao))
    return 0
