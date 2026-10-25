"""Painel Esquema lógico e o `.esquema.md` gravado ao salvar (RF-23)."""

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from haradaer.gui.schema_panel import schema_file
from haradaer.gui.settings import schema_file_enabled
from haradaer.gui.window import DocumentWindow


@pytest.fixture(autouse=True)
def sem_perguntas(monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)


@pytest.fixture
def janela(qtbot):
    j = DocumentWindow()
    qtbot.addWidget(j)
    return j


def texto(janela):
    return janela.schema.text.toPlainText()


def entidade_com_chave(janela, nome="Aluno"):
    entidade = janela.editor.create("ent", 100, 100)
    janela.editor.rename(entidade, nome)
    chave = janela.editor.create("atrchave", 100, 200)
    janela.editor.rename(chave, "mat")
    janela.editor.connect("lcaf", chave, entidade)
    return entidade


def test_painel_acompanha_o_diagrama_e_o_desfazer(janela):
    assert "## Relações\n\nNenhuma." in texto(janela)
    entidade_com_chave(janela)
    assert "ALUNO (**mat**)" in texto(janela)
    janela.action_undo.trigger()  # desfaz a ligação da chave
    assert "ALUNO ()" in texto(janela)


def test_copiar(janela):
    entidade_com_chave(janela)
    janela.schema.copy_button.click()
    assert "ALUNO (**mat**)" in QApplication.clipboard().text()


def test_painel_em_exibir(janela):
    assert janela.schema_dock.toggleViewAction().text() == "Esquema lógico"


def test_salvar_sem_a_opcao_nao_grava_o_esquema(janela, tmp_path):
    entidade_com_chave(janela)
    assert janela._write(tmp_path / "modelo.xml")
    assert not schema_file(tmp_path / "modelo.xml").exists()


def test_salvar_com_a_opcao_grava_o_esquema_ao_lado(janela, tmp_path):
    janela.action_schema_file.setChecked(True)
    entidade_com_chave(janela)
    assert janela._write(tmp_path / "modelo.xml")
    esquema = tmp_path / "modelo.esquema.md"
    conteudo = esquema.read_text("utf-8")
    assert conteudo.startswith("# Esquema lógico relacional — modelo\n")
    assert "a partir de `modelo.xml`" in conteudo and "ALUNO (**mat**)" in conteudo
    assert "esquema" not in (tmp_path / "modelo.xml").read_text("utf-8")  # nada no .xml


def test_erro_no_esquema_mantem_o_modelo_salvo(janela, tmp_path, monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda pai, titulo, txt: avisos.append(txt))
    janela.action_schema_file.setChecked(True)
    (tmp_path / "modelo.esquema.md").mkdir()  # uma pasta no lugar do arquivo
    assert janela._write(tmp_path / "modelo.xml")
    assert (tmp_path / "modelo.xml").is_file() and not janela.isWindowModified()
    assert len(avisos) == 1 and "modelo.esquema.md" in avisos[0]


def test_opcao_desligada_por_padrao_e_lembrada(qtbot, janela):
    assert not janela.action_schema_file.isChecked()
    janela.action_schema_file.setChecked(True)
    assert schema_file_enabled()
    outra = DocumentWindow()
    qtbot.addWidget(outra)
    assert outra.action_schema_file.isChecked()
