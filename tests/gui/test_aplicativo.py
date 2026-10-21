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


def test_icone_da_janela_vem_do_svg_em_varios_tamanhos(qapp):
    from haradaer.gui.app import ICON_PATH, ICON_SIZES, app_icon

    assert ICON_PATH.is_file()
    icone = app_icon()
    assert {s.width() for s in icone.availableSizes()} == set(ICON_SIZES)


def test_gerador_de_icones_do_windows_e_do_macos(tmp_path, monkeypatch, qapp):
    import importlib.util
    import struct
    from pathlib import Path

    from PySide6.QtGui import QImage, QImageReader

    caminho = Path(__file__).parents[2] / "packaging" / "gerar_icones.py"
    especificacao = importlib.util.spec_from_file_location("gerar_icones", caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "SAIDA", tmp_path)
    assert modulo.main() == 0

    leitor = QImageReader(str(tmp_path / "haradaer.ico"))
    lados = []
    for i in range(leitor.imageCount()):
        leitor.jumpToImage(i)
        lados.append(leitor.read().width())
    assert lados == list(modulo.TAMANHOS_ICO)

    dados = (tmp_path / "haradaer.icns").read_bytes()
    assert dados[:4] == b"icns" and struct.unpack(">I", dados[4:8])[0] == len(dados)
    i, blocos = 8, {}
    while i < len(dados):
        tipo, tamanho = dados[i : i + 4], struct.unpack(">I", dados[i + 4 : i + 8])[0]
        blocos[tipo] = QImage.fromData(dados[i + 8 : i + tamanho]).width()
        i += tamanho
    assert blocos == modulo.BLOCOS_ICNS
