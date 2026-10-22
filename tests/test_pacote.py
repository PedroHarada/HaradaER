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
