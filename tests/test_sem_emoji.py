"""O programa não usa emoji nos textos (decisão do autor,
2026-11-18). Setas e marcadores tipográficos (→, ↔, •) continuam valendo."""

import re
from pathlib import Path

FONTE = Path(__file__).resolve().parents[1] / "src" / "haradaer"

# Emoji e símbolos do Unicode (não as setas nem a pontuação).
_EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿⬀-⯿⌚-⏿️‍⌀⌘]")


def test_nenhum_emoji_no_codigo_do_programa():
    achados = [
        f"{arquivo.relative_to(FONTE)}:{numero}: {linha.strip()}"
        for arquivo in sorted(FONTE.rglob("*.py"))
        for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1)
        if _EMOJI.search(linha)
    ]
    assert achados == []
