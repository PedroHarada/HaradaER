import haradaer


def test_pacote_tem_versao():
    assert haradaer.__version__


def test_versao_igual_no_pyproject():
    import tomllib
    from pathlib import Path

    projeto = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert tomllib.loads(projeto.read_text("utf-8"))["project"]["version"] == haradaer.__version__
