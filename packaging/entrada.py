"""Ponto de entrada do executável gerado pelo PyInstaller."""

import sys

from haradaer import selftest

codigo = selftest.main(sys.argv)  # `--autoteste SAIDA.txt`, só para o workflow de versão
if codigo is not None:
    sys.exit(codigo)

from haradaer.gui.app import main  # noqa: E402

sys.exit(main())
