import os
import tempfile

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
