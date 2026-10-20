# Configuração do PyInstaller: gera o HaradaER como executável para quem não tem Python.
#
#   pyinstaller packaging/HaradaER.spec
#
# Linux e Windows: um arquivo único em dist/. macOS: dist/HaradaER.app.
# Módulos do Qt que o HaradaER não usa ficam de fora, para o arquivo ficar menor.
import sys

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
    datas=[("AVISOS-DE-LICENCA.txt", ".")],
    excludes=NAO_USADOS,
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="HaradaER", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="HaradaER")
    app = BUNDLE(
        coll,
        name="HaradaER.app",
        bundle_identifier="io.github.pedroharada.haradaer",
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
    )
