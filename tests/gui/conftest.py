import os

# Antes de qualquer QApplication: os testes de interface rodam sem tela.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
