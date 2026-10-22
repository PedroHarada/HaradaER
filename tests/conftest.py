from pathlib import Path

import pytest

REFERENCIA = Path(__file__).resolve().parents[1] / "docs" / "referencia-terraer"


@pytest.fixture(scope="session")
def referencia() -> Path:
    """Pasta com os arquivos gerados pelo próprio TerraER (golden files)."""
    assert REFERENCIA.is_dir(), f"pasta de referência não encontrada: {REFERENCIA}"
    return REFERENCIA


@pytest.fixture(autouse=True)
def idioma_portugues():
    """Todo teste começa e termina em português, o padrão, qualquer que seja o do sistema."""
    from haradaer.i18n import set_language

    set_language("pt")
    yield
    set_language("pt")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Sem os gabaritos do TerraER, os testes que os usam são pulados em vez de falhar (na
    preparação ou no corpo do teste)."""
    resultado = yield
    relatorio = resultado.get_result()
    erro = call.excinfo.value if call.excinfo else None
    if (
        relatorio.failed
        and isinstance(erro, FileNotFoundError)
        and str(REFERENCIA) in str(erro.filename or "")
    ):
        relatorio.outcome = "skipped"
        relatorio.longrepr = (str(item.path), 0, f"gabarito do TerraER ausente: {erro.filename}")
