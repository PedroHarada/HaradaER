from pathlib import Path

import pytest

REFERENCIA = Path(__file__).resolve().parents[1] / "docs" / "referencia-terraer"


@pytest.fixture(scope="session")
def referencia() -> Path:
    """Pasta com os arquivos gerados pelo próprio TerraER (golden files)."""
    assert REFERENCIA.is_dir(), f"pasta de referência não encontrada: {REFERENCIA}"
    return REFERENCIA
