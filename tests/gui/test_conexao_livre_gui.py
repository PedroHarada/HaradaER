"""Sem conexão livre na interface (RF-25): sem ferramenta, e apagada ao abrir com aviso."""

import pytest
from PySide6.QtWidgets import QMessageBox

from haradaer.gui.shortcuts import FAMILIES
from haradaer.gui.view import Tool
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    """O modelo abre modificado: fechar a janela no fim do teste não pode esperar resposta."""
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def avisos(monkeypatch):
    capturados: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda pai, titulo, texto: capturados.append((titulo, texto))
    )
    return capturados


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    return j


def tags(janela):
    return [f.tag for f in janela.editor.document.figures]


def test_nao_ha_ferramenta_de_conexao_livre(janela):
    assert Tool("connect", "llabel") not in janela._tool_actions
    assert all(Tool("connect", "llabel") not in ferramentas for _, ferramentas in FAMILIES)
    assert "C" not in dict(FAMILIES)
    combo = janela.properties.connection_type
    assert "llabel" not in [combo.itemData(i) for i in range(combo.count())]


def test_abrir_apaga_avisa_e_so_muda_o_disco_ao_salvar(janela, avisos, referencia, tmp_path):
    arquivo = tmp_path / "modelo.xml"
    original = (referencia / "amostra-todos-os-tipos.xml").read_bytes()
    arquivo.write_bytes(original)
    assert janela.load(arquivo)
    assert "llabel" not in tags(janela)
    assert len(avisos) == 1
    titulo, texto = avisos[0]
    assert titulo == "Conexões livres apagadas"
    assert "Foi apagada 1 deste arquivo" in texto
    assert "ENT. REL. 0 (Entidade associativa) ↔ W. ENT. 0 (Entidade fraca)" in texto
    assert janela.isWindowModified() and not janela.editor.history.can_undo
    assert arquivo.read_bytes() == original
    assert janela.save()
    assert "<llabel " not in arquivo.read_text("ascii")
    assert not janela.isWindowModified()


def test_pontas_soltas_no_aviso(janela, avisos, referencia, tmp_path):
    arquivo = tmp_path / "incompletas.xml"
    arquivo.write_bytes((referencia / "amostra-conexoes-incompletas.xml").read_bytes())
    assert janela.load(arquivo)
    texto = avisos[0][1]
    assert "Foram apagadas 3 deste arquivo" in texto
    assert "• ponta solta ↔ ponta solta" in texto
    assert "(Entidade) ↔ ponta solta" in texto


def test_arquivo_sem_conexao_livre_abre_sem_aviso(janela, avisos, referencia):
    assert janela.load(referencia / "amostra-basica.xml")
    assert avisos == [] and not janela.isWindowModified()
