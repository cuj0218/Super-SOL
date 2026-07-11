#!/usr/bin/env python3
"""UserPromptSubmit: classify the request and inject only the minimal discipline.

Automation-first and beginner-first: the user types normally, and this hook
quietly (1) resets this turn's evidence tracker and (2) injects a short,
plain-language operating rule sized to the task. It never calls an API, never
reads OPENAI_API_KEY, never switches models. Always exits 0 (fail-open).

Output on stdout becomes extra context Codex sees for this turn.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify import classify
from session_state import read_stdin_json, reset_state

# Minimal always-on rule — the two procedures Super SOL measured as worth their
# tokens: run what you build, and verify before claiming done.
_ALWAYS_ON = (
    "[Super SOL] 실행성과 검증만 최소로 지킵니다. "
    "코드를 바꾸면 관련 테스트/실행으로 확인한 뒤 완료라고 말하고, "
    "확인 없이 완료를 선언하지 마세요. (Run what you change; verify before claiming done.)"
)

_DEEP = (
    "[Super SOL] 이 작업은 신중 모드입니다. 계획 → 구현 → 검증 순서로 진행하고, "
    "파일을 바꾼 뒤에는 반드시 관련 테스트나 실행으로 결과를 확인하세요."
)

_RISK_NOTE = {
    "security": "보안 관련 작업입니다. 비밀값을 출력하지 말고 입력 검증을 우선하세요.",
    "production": "운영/배포 영향이 있는 작업입니다. 되돌리기 어려운 동작은 먼저 확인을 받으세요.",
    "destructive": "삭제/파괴적 동작이 감지됐습니다. 대상을 먼저 확인하고, 지우기 전에 사용자 확인을 받으세요.",
    "data": "데이터/스키마 변경입니다. 마이그레이션은 되돌릴 방법을 함께 준비하세요.",
}


def main() -> int:
    data = read_stdin_json()
    prompt = str(data.get("prompt") or "")
    session_id = str(data.get("session_id") or "")

    # New user turn → clear this turn's evidence so the stop gate judges fresh.
    reset_state(session_id)

    if not prompt.strip():
        return 0

    mode, risks = classify(prompt)

    lines: list[str] = [_ALWAYS_ON]
    if mode == "deep":
        lines.append(_DEEP)
    for risk in risks:
        note = _RISK_NOTE.get(risk)
        if note:
            lines.append(f"[Super SOL] {note}")

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
