"""O núcleo não pode depender de Qt nem da interface gráfica (RNF-08)."""

import ast
import subprocess
import sys
from pathlib import Path

import haradaer.core

CORE_DIR = Path(haradaer.core.__file__).parent
PROIBIDOS = ("PySide6", "PyQt5", "PyQt6", "shiboken6", "haradaer.gui")


def _arquivos_do_nucleo() -> list[Path]:
    return sorted(CORE_DIR.rglob("*.py"))


def _modulos_importados(caminho: Path) -> list[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    nomes: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.append(no.module)
    return nomes


def test_nucleo_tem_arquivos():
    assert _arquivos_do_nucleo(), "o núcleo não pode estar vazio"


def test_codigo_do_nucleo_nao_importa_qt_nem_gui():
    violacoes = []
    for caminho in _arquivos_do_nucleo():
        for nome in _modulos_importados(caminho):
            if any(nome == p or nome.startswith(p + ".") for p in PROIBIDOS):
                violacoes.append(f"{caminho.relative_to(CORE_DIR)} importa {nome}")
    assert not violacoes, "\n".join(violacoes)


def test_importar_o_nucleo_nao_carrega_qt():
    codigo = (
        "import importlib, pkgutil, sys\n"
        "import haradaer.core as core\n"
        "for m in pkgutil.walk_packages(core.__path__, core.__name__ + '.'):\n"
        "    importlib.import_module(m.name)\n"
        "carregados = sorted(n for n in sys.modules\n"
        "                    if n.split('.')[0] in ('PySide6', 'PyQt5', 'PyQt6', 'shiboken6')\n"
        "                    or n.startswith('haradaer.gui'))\n"
        "print(','.join(carregados))\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert resultado.stdout.strip() == ""
