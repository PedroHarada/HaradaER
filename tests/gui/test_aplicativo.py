"""Teste de fumaça: o aplicativo sobe de verdade, abre um arquivo e fica rodando."""

import os
import subprocess
import sys


def test_aplicativo_inicia_e_fica_aberto(referencia):
    ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    comando = [sys.executable, "-m", "haradaer", str(referencia / "amostra-basica.xml")]
    try:
        resultado = subprocess.run(comando, env=ambiente, capture_output=True, timeout=3)
    except subprocess.TimeoutExpired as erro:
        # ficar rodando até o tempo acabar é o esperado: a janela está aberta
        saida = (erro.stderr or b"").decode(errors="replace")
        assert "Traceback" not in saida, saida
    else:  # terminou sozinho: só pode ser erro
        raise AssertionError(resultado.stderr.decode(errors="replace"))
