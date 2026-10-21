# Configuração do PyInstaller: gera o HaradaER como executável para quem não tem Python.
#
#   pyinstaller packaging/HaradaER.spec
#
# Linux e Windows: um arquivo único em dist/. macOS: dist/HaradaER.app.
# Módulos do Qt que o HaradaER não usa ficam de fora, para o arquivo ficar menor.
# Os ícones do Windows e do macOS vêm de `python packaging/gerar_icones.py`, que roda antes.
import os
import sys

GERADO = os.path.join(SPECPATH, "gerado")
ICONE_SVG = os.path.join(SPECPATH, "..", "src", "haradaer", "resources", "haradaer.svg")

NAO_USADOS = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "tkinter",
]

a = Analysis(
    ["entrada.py"],
    datas=[("AVISOS-DE-LICENCA.txt", "."), (ICONE_SVG, "haradaer/resources")],
    excludes=NAO_USADOS,
    noarchive=False,
)
if sys.platform.startswith("linux"):
    # A biblioteca de fontes vem do sistema: a da máquina que gera o executável (Ubuntu 22.04)
    # não entende a configuração de fontes de distribuições mais novas (Arch, por exemplo).
    a.binaries = [b for b in a.binaries if not b[0].startswith(("libfontconfig", "libfreetype"))]

pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="HaradaER", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="HaradaER")
    app = BUNDLE(
        coll,
        name="HaradaER.app",
        bundle_identifier="io.github.pedroharada.haradaer",
        icon=os.path.join(GERADO, "haradaer.icns"),
        info_plist={
            "CFBundleDocumentTypes": [
                {"CFBundleTypeName": "Modelo ER", "CFBundleTypeExtensions": ["xml"],
                 "CFBundleTypeRole": "Editor"}
            ],
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        name="HaradaER",
        console=False,
        upx=False,
        icon=os.path.join(GERADO, "haradaer.ico") if sys.platform == "win32" else None,
    )
