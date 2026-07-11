#!/usr/bin/env python3
"""PostToolUse: record this turn's evidence from the observed tool call.

Beginner-first and offline. We only look at what actually ran:
  - a file edit (apply_patch / write / edit)  → code_mutated (or docs_only)
  - a successful test/verify command          → fresh_verification
  - another code edit after a passing check    → fresh_verification reset

This is observation, not model claims. It never blocks a tool. Always exits 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from session_state import load_state, read_stdin_json, save_state

_DOC_SUFFIX = re.compile(r"\.(?:md|rst|txt|adoc)\b", re.I)
_MUTATION_TOOLS = re.compile(r"apply_patch|write_file|edit_file|str_replace|create_file", re.I)
_VERIFY_CMD = re.compile(
    r"\b(?:pytest|unittest|tox|nox|npm (?:test|run test)|yarn test|pnpm test|"
    r"go test|cargo test|jest|vitest|mvn test|gradle test|make test|"
    r"super-sol-eval|ruff check|basedpyright|mypy|tsc)\b",
    re.I,
)


def _text(data: dict[str, object], *keys: str) -> str:
    parts: list[str] = []
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            parts.append(" ".join(str(v) for v in value.values()))
    return " ".join(parts)


def _exit_ok(data: dict[str, object]) -> bool:
    """Best-effort success read across Codex payload shapes; default True."""
    for key in ("exit_code", "exitCode", "returncode", "status"):
        value = data.get(key)
        if isinstance(value, int):
            return value == 0
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value) == 0
    result = data.get("tool_result")
    if isinstance(result, dict):
        return _exit_ok(result)
    return True


def main() -> int:
    data = read_stdin_json()
    session_id = str(data.get("session_id") or "")
    tool_name = _text(data, "tool_name", "tool", "name")
    command = _text(data, "command", "tool_input", "input", "arguments", "cmd")
    blob = f"{tool_name} {command}"

    state = load_state(session_id)

    is_mutation = bool(_MUTATION_TOOLS.search(blob))
    # Shell edits (heredoc/redirect/sed) also count as mutations.
    if not is_mutation and re.search(r"\b(?:>|>>|tee|sed -i|cat >)\b", command):
        is_mutation = True

    if is_mutation:
        paths = " ".join(re.findall(r"[\w./-]+\.[A-Za-z0-9]+", command)) or command
        docs_only = bool(paths) and all(_DOC_SUFFIX.search(p) for p in paths.split()) or (
            not paths and False
        )
        state["code_mutated"] = True
        state["docs_only"] = bool(state.get("docs_only", True)) and docs_only
        state["fresh_verification"] = False  # new edit invalidates prior check

    if _VERIFY_CMD.search(command) and _exit_ok(data):
        state["fresh_verification"] = True

    save_state(session_id, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
