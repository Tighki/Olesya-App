# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

icon = "olesya/assets/logo.ico" if sys.platform == "win32" else None
binaries = []
datas = [("olesya/assets/logo.png", "assets")]
hiddenimports = [
    "olesya",
    "olesya.db",
    "olesya.mariadb_conn",
    "olesya.matching",
    "olesya.ui",
    "pymysql",
]
runtime_hooks = []

if sys.platform == "win32":
    prefix = Path(os.environ.get("UCRT64_PREFIX", r"C:\msys64\ucrt64"))
    binaries += [(str(path), ".") for path in (prefix / "bin").glob("*.dll")]
    datas += [
        (str(prefix / "lib" / "girepository-1.0"), os.path.join("lib", "girepository-1.0")),
        (str(prefix / "lib" / "gdk-pixbuf-2.0"), os.path.join("lib", "gdk-pixbuf-2.0")),
        (str(prefix / "share" / "glib-2.0" / "schemas"), os.path.join("share", "glib-2.0", "schemas")),
        (str(prefix / "share" / "icons"), os.path.join("share", "icons")),
    ]
    hiddenimports += [
        "gi",
        "gi.repository.Gtk",
        "gi.repository.Adw",
        "gi.repository.Gdk",
        "gi.repository.GdkPixbuf",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Pango",
        "gi.repository.cairo",
        "cairo",
    ]
    runtime_hooks.append("olesya/windows_runtime.py")
else:
    hiddenimports += [
        "gi",
        "gi.repository.Gtk",
        "gi.repository.Adw",
        "gi.repository.Gdk",
        "gi.repository.GdkPixbuf",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Pango",
        "gi.repository.cairo",
        "cairo",
    ]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={
        "gi": {
            "module-versions": {
                "Gtk": "4.0",
                "Gdk": "4.0",
            },
        },
    },
    runtime_hooks=runtime_hooks,
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="olesya",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="olesya",
)
