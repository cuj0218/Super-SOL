#!/usr/bin/env python3
"""Tiny per-session evidence file for the Super SOL Codex plugin.

Tracks, for the current turn, whether the model changed code and whether a
verification/test command has since succeeded — plus how many completion
nudges we have already shown (capped so we never loop). State lives out of
band under a temp dir keyed by session id; it is never shown to the model and
never leaves the machine. All failures are swallowed so a hook can never break
a Codex turn (fail-open).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

_DEFAULT = {
    "code_mutated": False,
    "docs_only": True,
    "fresh_verification": False,
    "nudges": 0,
}


def read_stdin_json() -> dict[str, object]:
    """Parse the hook stdin JSON payload; return {} on any error."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _state_dir() -> Path:
    root = Path(os.environ.get("SUPER_SOL_STATE_DIR") or Path(tempfile.gettempdir()) / "super-sol")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_id(session_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return cleaned[:120] or "unknown"


def state_path(session_id: str) -> Path:
    return _state_dir() / f"{_safe_id(session_id)}.json"


def load_state(session_id: str) -> dict[str, object]:
    try:
        data = json.loads(state_path(session_id).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_DEFAULT, **data}
    except Exception:
        pass
    return dict(_DEFAULT)


def save_state(session_id: str, state: dict[str, object]) -> None:
    try:
        state_path(session_id).write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def reset_state(session_id: str) -> None:
    save_state(session_id, dict(_DEFAULT))
