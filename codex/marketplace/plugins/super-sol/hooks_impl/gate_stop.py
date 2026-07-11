#!/usr/bin/env python3
"""Stop: block premature completion once, in plain language.

If this turn changed code (not docs-only) and no test/verify has since
succeeded, ask Codex to check its work — at most one nudge per turn, then it
allows so we never loop. Beginner-friendly wording. Offline, fail-open.

Codex Stop contract: print {"decision":"block","reason":"..."} to make the
model keep working; print nothing / exit 0 to allow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from session_state import load_state, read_stdin_json, save_state

_MAX_NUDGES = 1

_REASON = (
    "검증 중 — 방금 코드를 바꿨는데 아직 확인(테스트/실행)이 없습니다. "
    "관련 테스트나 명령을 한 번 실행해 결과를 확인한 뒤 마무리하세요. "
    "(You changed code but haven't verified it yet — run the relevant test/command once, then finish.)"
)


def _allow() -> int:
    return 0


def _block(session_id: str, state: dict[str, object]) -> int:
    state["nudges"] = int(state.get("nudges", 0)) + 1
    save_state(session_id, state)
    sys.stdout.write(json.dumps({"decision": "block", "reason": _REASON}) + "\n")
    return 0


def main() -> int:
    data = read_stdin_json()
    session_id = str(data.get("session_id") or "")
    state = load_state(session_id)

    code_mutated = bool(state.get("code_mutated"))
    docs_only = bool(state.get("docs_only", True))
    fresh = bool(state.get("fresh_verification"))
    nudges = int(state.get("nudges", 0))

    # Allow when: nothing changed, docs-only, already verified, or we've already
    # nudged once this turn (cap prevents an infinite loop).
    if not code_mutated or docs_only or fresh or nudges >= _MAX_NUDGES:
        return _allow()

    return _block(session_id, state)


if __name__ == "__main__":
    raise SystemExit(main())
