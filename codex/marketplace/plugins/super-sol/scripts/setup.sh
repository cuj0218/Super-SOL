#!/usr/bin/env bash
# Super SOL for Codex — one-time local setup. Offline only: no API key, no
# Docker, no billing. It just self-checks the hook scripts so a beginner can
# confirm the plugin is wired correctly before trusting the hooks in Codex.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required (it ships with macOS and most Linux)." >&2
  exit 1
fi

echo "==> Checking hook scripts compile"
python3 -c "import py_compile,glob,sys; [py_compile.compile(f, doraise=True) for f in glob.glob('hooks_impl/*.py')]; print('  ok: hooks_impl/*.py')"

echo "==> Smoke: classify a sample request (no network)"
python3 - <<'PY'
import sys
sys.path.insert(0, "hooks_impl")
from classify import classify
mode, risks = classify("데이터베이스 마이그레이션을 운영에 배포해줘")
assert mode == "deep", mode
assert "production" in risks and "data" in risks, risks
print(f"  ok: mode={mode} risks={risks}")
PY

echo "==> Smoke: stop-gate blocks unverified code change, then allows"
python3 - <<'PY'
import json, os, subprocess, sys, tempfile
d = tempfile.mkdtemp()
env = {**os.environ, "SUPER_SOL_STATE_DIR": d}
sid = "setup-smoke"

def run(script, payload):
    return subprocess.run(
        ["python3", f"hooks_impl/{script}"],
        input=json.dumps(payload), text=True, capture_output=True, env=env,
    )

run("gate_prompt.py", {"session_id": sid, "prompt": "fix the parser bug"})
run("gate_post_tool.py", {"session_id": sid, "tool_name": "apply_patch", "command": "apply_patch parser.py"})
first = run("gate_stop.py", {"session_id": sid})
assert '"block"' in first.stdout, first.stdout
second = run("gate_stop.py", {"session_id": sid})
assert second.stdout.strip() == "", second.stdout  # capped at one nudge
print("  ok: blocks once, then allows")
PY

echo "==> Super SOL for Codex is ready."
echo "    Install it in Codex, approve the hooks once, and just work as usual."
