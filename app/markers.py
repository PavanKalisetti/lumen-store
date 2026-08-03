"""Rotating fulfilment and settlement reference tokens.

A fresh set is issued on each process start and cached under the service account's
home directory so background reconciliation jobs can read the current values.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

KEYS = (
    "catalog",
    "receipt",
    "review",
    "ticket",
    "checkout",
)

DEFAULT_PATH = Path.home() / ".cache" / "lumen-store" / "markers.json"

_values: dict[str, str] = {}


def path() -> Path:
    override = os.environ.get("LUMEN_MARKER_FILE")
    return Path(override) if override else DEFAULT_PATH


def load() -> dict[str, str]:
    global _values
    _values = {key: f"LM-{key.upper()}-{secrets.token_hex(8)}" for key in KEYS}
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_values, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return dict(_values)


def value(key: str) -> str:
    if key not in _values:
        raise KeyError(key)
    return _values[key]
