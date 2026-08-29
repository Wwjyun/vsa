# PyInstaller one-folder build for the Windows portfolio application.

import os

# Everything here is resolved from the spec directory rather than through the
# PyInstaller collect_* hooks. Those hooks import the package at build time, so
# they silently return nothing in an environment where vsa is not installed
# (CI builds straight from the checkout) and the bundle ships without its
# resources.
SOURCE_ROOT = os.path.join(SPECPATH, "src")
RESOURCE_DIR = os.path.join(SOURCE_ROOT, "vsa", "resources")

datas = [
    (os.path.join(RESOURCE_DIR, "button_names.json"), os.path.join("vsa", "resources")),
    (os.path.join(RESOURCE_DIR, "rule.json"), os.path.join("vsa", "resources")),
]
binaries = []
# vsa.resources is reached only through importlib.resources, so no import chain
# leads PyInstaller to it.
hiddenimports = [
    "vsa.resources",
    "dash",
    "dash.dcc",
    "dash.html",
    "plotly",
    "plotly.colors.qualitative",
]

analysis = Analysis(
    ["src/vsa/__main__.py"],
    pathex=[SOURCE_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="VSA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name="VSA",
)
