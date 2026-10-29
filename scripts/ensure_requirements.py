"""Venv + PyMySQL перед запуском GTK-приложений (PEP 668 / Omarchy)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _venv_python(app_dir: Path) -> Path:
    if sys.platform == "win32":
        return app_dir / ".venv" / "Scripts" / "python.exe"
    return app_dir / ".venv" / "bin" / "python"


def _in_project_venv(app_dir: Path) -> bool:
    return Path(sys.prefix).resolve() == (app_dir / ".venv").resolve()


def ensure_app_requirements(app_dir: Path, main_file: Path) -> None:
    """Создаёт .venv при необходимости, ставит requirements, перезапускает в venv."""
    app_dir = app_dir.resolve()
    main_file = main_file.resolve()
    venv_dir = app_dir / ".venv"
    venv_py = _venv_python(app_dir)
    req = app_dir / "requirements.txt"

    if not req.is_file():
        print(f"Не найден {req}", file=sys.stderr)
        raise SystemExit(1)

    if venv_py.is_file() and not _in_project_venv(app_dir):
        os.execv(str(venv_py), [str(venv_py), str(main_file), *sys.argv[1:]])

    try:
        import pymysql  # noqa: F401
        return
    except ImportError:
        pass

    if not venv_py.is_file():
        print(f"Создаю {venv_dir} (GTK из системы через --system-site-packages) …", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)],
        )

    print(f"Ставлю зависимости из {req.name} …", file=sys.stderr)
    subprocess.check_call(
        [str(venv_py), "-m", "pip", "install", "-r", str(req)],
    )

    if not _in_project_venv(app_dir):
        os.execv(str(venv_py), [str(venv_py), str(main_file), *sys.argv[1:]])

    try:
        import pymysql  # noqa: F401
    except ImportError as exc:
        print(
            "PyMySQL не установился. Вручную:\n"
            f"  cd {app_dir}\n"
            "  python -m venv --system-site-packages .venv\n"
            "  source .venv/bin/activate\n"
            "  pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
