#!/usr/bin/env python3
"""Запуск настольного приложения студии «Олеся»."""

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
for _scripts in (_APP_DIR / "scripts", _APP_DIR.parent / "scripts"):
    if (_scripts / "ensure_requirements.py").is_file():
        sys.path.insert(0, str(_scripts))
        break
else:
    print("Не найден scripts/ensure_requirements.py", file=sys.stderr)
    raise SystemExit(1)

from ensure_requirements import ensure_app_requirements

ensure_app_requirements(_APP_DIR, Path(__file__).resolve())

import olesya.windows_runtime
from olesya.ui import main

if __name__ == "__main__":
    raise SystemExit(main())
