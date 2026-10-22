import haradaer


def test_pacote_tem_versao():
    assert haradaer.__version__


def test_versao_igual_no_pyproject():
    import tomllib
    from pathlib import Path

    projeto = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert tomllib.loads(projeto.read_text("utf-8"))["project"]["version"] == haradaer.__version__


def test_app_do_macos_leva_a_versao():
    from pathlib import Path

    spec = (Path(__file__).resolve().parents[1] / "packaging" / "HaradaER.spec").read_text("utf-8")
    assert "version=VERSAO" in spec and "__version__" in spec


def test_zip_do_macos_sem_a_pasta_pacote():
    from pathlib import Path

    fluxo = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "versao.yml"
    assert "--keepParent" not in fluxo.read_text("utf-8")


def test_avisos_de_licenca_com_os_textos_completos():
    from pathlib import Path

    avisos = Path(__file__).resolve().parents[1] / "packaging" / "AVISOS-DE-LICENCA.txt"
    texto = avisos.read_text("utf-8")
    for trecho in (
        "GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3",  # a LGPL pede o texto junto do programa
        "GNU GENERAL PUBLIC LICENSE",
        "Version 2.1",
        "Apache License",  # OpenSSL
        "PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2",
        "OpenSSL",
        "zstd",
    ):
        assert trecho in texto, trecho


def test_licenca_gplv3():
    import tomllib
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    assert "GNU GENERAL PUBLIC LICENSE" in (raiz / "LICENSE").read_text("utf-8")
    projeto = tomllib.loads((raiz / "pyproject.toml").read_text("utf-8"))["project"]
    assert projeto["license"] == "GPL-3.0-only"


def test_pacote_sem_o_teclado_virtual():
    from pathlib import Path

    spec = (Path(__file__).resolve().parents[1] / "packaging" / "HaradaER.spec").read_text("utf-8")
    assert '"virtualkeyboard"' in spec and "_usado" in spec
