from __future__ import annotations

import os
from pathlib import Path

STATE_DIR = Path(os.environ.get("LUMEN_STATE_DIR", "/tmp/lumen-store"))


class Config:
    SECRET_KEY = os.environ.get("LUMEN_SECRET_KEY", "lumen-store-local")
    DATABASE = str(STATE_DIR / "store.db")
    UPLOAD_DIR = str(STATE_DIR / "uploads")
    ASSET_DIR = str(STATE_DIR / "assets")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
