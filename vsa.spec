# PyInstaller one-folder build for the Windows portfolio application.

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("vsa")
binaries = []
# vsa.resources is only reached through importlib.resources, so PyInstaller cannot
# see it by following imports.
hiddenimports = collect_submodules("vsa") + [
    "dash",
    "dash.dcc",
    "dash.html",
    "plotly",
    "plotly.colors.qualitative",
]

analysis = Analysis(
    ["src/vsa/__main__.py"],
    pathex=["src"],
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
