"""Gera os ícones do Windows (.ico) e do macOS (.icns) a partir do ícone do HaradaER (SVG).

    python packaging/gerar_icones.py   # grava em packaging/gerado/

Roda antes do PyInstaller (a versão no GitHub Actions faz isso), e só precisa do PySide6. Os
dois formatos guardam vários tamanhos em PNG num arquivo só; são gravados aqui à mão, sem
programas de fora.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

RAIZ = Path(__file__).resolve().parent.parent
ICONE = RAIZ / "src" / "haradaer" / "resources" / "haradaer.svg"
SAIDA = Path(__file__).resolve().parent / "gerado"

TAMANHOS_ICO = (16, 24, 32, 48, 64, 128, 256)
# tipo do bloco no .icns -> lado em pixels (os "@2x" são para telas Retina)
BLOCOS_ICNS = {
    b"icp4": 16,
    b"icp5": 32,
    b"ic11": 32,  # 16@2x
    b"ic12": 64,  # 32@2x
    b"ic07": 128,
    b"ic13": 256,  # 128@2x
    b"ic08": 256,
    b"ic14": 512,  # 256@2x
    b"ic09": 512,
    b"ic10": 1024,  # 512@2x
}


def png(renderizador: QSvgRenderer, lado: int) -> bytes:
    imagem = QImage(lado, lado, QImage.Format.Format_ARGB32)
    imagem.fill(0)
    pintor = QPainter(imagem)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderizador.render(pintor, QRectF(0, 0, lado, lado))
    pintor.end()
    dados = QByteArray()
    buffer = QBuffer(dados)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    imagem.save(buffer, "PNG")
    return bytes(dados.data())


def ico(imagens: dict[int, bytes]) -> bytes:
    """ICONDIR + uma entrada por tamanho, com o PNG de cada um (Windows Vista em diante)."""
    cabecalho = struct.pack("<HHH", 0, 1, len(imagens))
    entradas, corpo = b"", b""
    deslocamento = 6 + 16 * len(imagens)
    for lado, dados in sorted(imagens.items()):
        medida = 0 if lado >= 256 else lado  # 0 quer dizer 256
        entradas += struct.pack(
            "<BBBBHHII", medida, medida, 0, 0, 1, 32, len(dados), deslocamento + len(corpo)
        )
        corpo += dados
    return cabecalho + entradas + corpo


def icns(blocos: dict[bytes, bytes]) -> bytes:
    corpo = b"".join(tipo + struct.pack(">I", 8 + len(d)) + d for tipo, d in blocos.items())
    return b"icns" + struct.pack(">I", 8 + len(corpo)) + corpo


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    renderizador = QSvgRenderer(str(ICONE))
    if not renderizador.isValid():
        print(f"ícone inválido: {ICONE}", file=sys.stderr)
        return 1
    lados = {*TAMANHOS_ICO, *BLOCOS_ICNS.values()}
    imagens = {lado: png(renderizador, lado) for lado in lados}
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / "haradaer.ico").write_bytes(ico({t: imagens[t] for t in TAMANHOS_ICO}))
    (SAIDA / "haradaer.icns").write_bytes(icns({b: imagens[t] for b, t in BLOCOS_ICNS.items()}))
    print(f"ícones gravados em {SAIDA}")
    del app
    return 0


if __name__ == "__main__":
    sys.exit(main())
