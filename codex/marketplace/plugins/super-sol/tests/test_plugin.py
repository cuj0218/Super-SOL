"""Offline tests for the Super SOL Codex plugin hooks.

Run: python3 -m pytest codex/marketplace/plugins/super-sol/tests -q
No network, no Docker, no API key. Each test drives a hook as a subprocess with
an isolated state dir, exactly as Codex would invoke it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
IMPL = PLUGIN / "hooks_impl"
sys.path.insert(0, str(IMPL))

from classify import classify  # noqa: E402


def _run(script: str, payload: dict[str, object], state_dir: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "SUPER_SOL_STATE_DIR": str(state_dir)}
    return subprocess.run(
        [sys.executable, str(IMPL / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


# ---- classifier -----------------------------------------------------------


def test_classify_deep_and_risks() -> None:
    mode, risks = classify("데이터베이스 스키마 마이그레이션을 운영에 배포")
    assert mode == "deep"
    assert "production" in risks
    assert "data" in risks


def test_classify_quick() -> None:
    mode, _ = classify("이 함수가 뭐 하는지 설명해줘")
    assert mode == "quick"


def test_classify_defaults_to_normal() -> None:
    mode, risks = classify("hello there")
    assert mode == "normal"
    assert risks == ()


# ---- prompt hook ----------------------------------------------------------


def test_prompt_injects_always_on(tmp_path: Path) -> None:
    out = _run("gate_prompt.py", {"session_id": "s1", "prompt": "fix the bug"}, tmp_path)
    assert out.returncode == 0
    assert "Super SOL" in out.stdout
    assert "검증" in out.stdout


def test_prompt_deep_adds_plan_implement_verify(tmp_path: Path) -> None:
    out = _run("gate_prompt.py", {"session_id": "s2", "prompt": "보안 인증 아키텍처 설계"}, tmp_path)
    assert "신중 모드" in out.stdout


def test_prompt_empty_is_silent(tmp_path: Path) -> None:
    out = _run("gate_prompt.py", {"session_id": "s3", "prompt": "   "}, tmp_path)
    assert out.stdout.strip() == ""


# ---- stop gate end-to-end -------------------------------------------------


def test_stop_blocks_unverified_code_then_allows(tmp_path: Path) -> None:
    sid = "flow1"
    _run("gate_prompt.py", {"session_id": sid, "prompt": "fix the parser"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "tool_name": "apply_patch", "command": "apply_patch parser.py"}, tmp_path)
    first = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert '"block"' in first.stdout
    # Second stop in the same turn is capped → allow (empty output).
    second = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert second.stdout.strip() == ""


def test_stop_allows_after_verification(tmp_path: Path) -> None:
    sid = "flow2"
    _run("gate_prompt.py", {"session_id": sid, "prompt": "fix the parser"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "tool_name": "apply_patch", "command": "apply_patch parser.py"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "command": "pytest -q", "exit_code": 0}, tmp_path)
    out = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert out.stdout.strip() == ""


def test_stop_allows_docs_only_change(tmp_path: Path) -> None:
    sid = "flow3"
    _run("gate_prompt.py", {"session_id": sid, "prompt": "update the readme"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "tool_name": "apply_patch", "command": "apply_patch README.md"}, tmp_path)
    out = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert out.stdout.strip() == ""


def test_stop_allows_when_nothing_changed(tmp_path: Path) -> None:
    sid = "flow4"
    _run("gate_prompt.py", {"session_id": sid, "prompt": "what does this do"}, tmp_path)
    out = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert out.stdout.strip() == ""


def test_failed_verification_does_not_count(tmp_path: Path) -> None:
    sid = "flow5"
    _run("gate_prompt.py", {"session_id": sid, "prompt": "fix the parser"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "tool_name": "apply_patch", "command": "apply_patch parser.py"}, tmp_path)
    _run("gate_post_tool.py", {"session_id": sid, "command": "pytest -q", "exit_code": 1}, tmp_path)
    out = _run("gate_stop.py", {"session_id": sid}, tmp_path)
    assert '"block"' in out.stdout
