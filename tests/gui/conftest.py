import os
import tempfile
from pathlib import Path

import pytest

# Antes de qualquer QApplication: os testes de interface rodam sem tela.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Configurações (recentes, disposição da janela) numa pasta só dos testes, nunca a do usuário.
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="haradaer-testes-")


@pytest.fixture(autouse=True)
def configuracoes_limpas():
    from haradaer.gui.settings import settings

    settings().clear()
    yield
    settings().clear()


AMOSTRA = "docs/referencia-terraer/amostra-basica.xml"  # um gabarito do TerraER


@pytest.fixture(autouse=True)
def caixas_nunca_travam(monkeypatch):
    """Uma caixa de diálogo que o teste não esperava esperaria um clique para sempre. Sem os
    gabaritos do TerraER (fora do GitHub), é a caixa de erro ao abrir uma amostra: o teste é
    pulado. Fora isso, o teste falha dizendo qual caixa apareceu. Testes que esperam a caixa
    trocam esta por outra com o seu próprio `monkeypatch`."""
    from PySide6.QtWidgets import QMessageBox

    def inesperada(*argumentos, **_):
        texto = " | ".join(str(a) for a in argumentos[1:3])
        if not (Path(__file__).resolve().parents[2] / AMOSTRA).exists():
            pytest.skip(f"gabarito do TerraER ausente ({texto})")
        raise AssertionError(f"caixa de diálogo inesperada no teste: {texto}")

    for nome in ("critical", "warning", "information"):
        monkeypatch.setattr(QMessageBox, nome, inesperada)
