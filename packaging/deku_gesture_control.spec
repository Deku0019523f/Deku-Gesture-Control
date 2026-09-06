# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller pour Deku Gesture Control (spec section 31).

Utilisation (depuis la racine du projet, avec l'environnement virtuel
activé et pyinstaller installé) :

    pyinstaller packaging/deku_gesture_control.spec --noconfirm

Résultat : dist/DekuGestureControl/DekuGestureControl.exe (sur Windows).
PyInstaller construit toujours pour la plateforme sur laquelle il
s'exécute : pour produire le .exe Windows, cette commande doit être
lancée sur une machine Windows (voir packaging/build_windows.bat).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent  # noqa: F821 (SPECPATH est injecté par PyInstaller)

hiddenimports = ["mediapipe"]
if sys.platform == "win32":
    hiddenimports += ["pynput.keyboard._win32", "pynput.mouse._win32"]
elif sys.platform == "darwin":
    hiddenimports += ["pynput.keyboard._darwin", "pynput.mouse._darwin"]
else:
    hiddenimports += ["pynput.keyboard._xorg", "pynput.mouse._xorg"]

a = Analysis(  # noqa: F821
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "assets"), "assets"),
        (str(PROJECT_ROOT / "config"), "config"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DekuGestureControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(PROJECT_ROOT / "assets" / "icon.ico"),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DekuGestureControl",
)
