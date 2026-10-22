"""Autoteste do executável (`--autoteste`), rodado aqui fora do pacote."""

import re
from pathlib import Path

from haradaer import selftest, updates

RAIZ = Path(__file__).resolve().parents[1]


def test_lista_igual_a_do_spec():
    spec = (RAIZ / "packaging" / "HaradaER.spec").read_text("utf-8")
    bloco = re.search(r"FORA_DO_PACOTE = \(([^)]*)\)", spec)
    assert bloco is not None
    assert tuple(re.findall(r'"([^"]+)"', bloco[1])) == selftest.PROIBIDOS


def test_acha_arquivos_que_deviam_ficar_de_fora(tmp_path):
    (tmp_path / "PySide6" / "Qt" / "plugins").mkdir(parents=True)
    (tmp_path / "PySide6" / "Qt" / "plugins" / "libqtvirtualkeyboardplugin.so").write_text("")
    (tmp_path / "libQt6Widgets.so.6").write_text("")
    assert selftest.bundled_forbidden(tmp_path) == [
        str(Path("PySide6/Qt/plugins/libqtvirtualkeyboardplugin.so"))
    ]


def test_sem_autoteste_o_programa_abre_normalmente():
    assert selftest.main(["HaradaER"]) is None
    assert selftest.main(["HaradaER", "modelo.xml"]) is None


def test_autoteste_grava_o_resultado(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(updates, "fetch_latest", lambda: "9.9.9")
    saida = tmp_path / "resultado.txt"
    assert selftest.main(["HaradaER", "--autoteste", str(saida)]) == 0
    texto = saida.read_text("utf-8")
    assert "janela: ok" in texto and "9.9.9" in texto and texto.endswith("RESULTADO: ok\n")


def test_resposta_http_prova_a_conexao_segura(monkeypatch):
    from urllib.error import HTTPError

    def nao_achou():
        raise HTTPError(updates.API, 404, "Not Found", {}, None)

    monkeypatch.setattr(updates, "fetch_latest", nao_achou)
    assert "404" in selftest.check_tls()


def test_falha_de_certificado_reprova(qtbot, tmp_path, monkeypatch):
    def sem_certificado():
        raise OSError("CERTIFICATE_VERIFY_FAILED")

    monkeypatch.setattr(updates, "fetch_latest", sem_certificado)
    saida = tmp_path / "resultado.txt"
    assert selftest.run(saida) == 1
    texto = saida.read_text("utf-8")
    assert "CERTIFICATE_VERIFY_FAILED" in texto and "RESULTADO: FALHOU" in texto
