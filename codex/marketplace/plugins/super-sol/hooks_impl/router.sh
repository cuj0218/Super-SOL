#!/usr/bin/env bash
# Super SOL UserPromptSubmit router — inject a conditional procedure pack only
# when a clear task signal is present. Smallest matching pack only. Offline,
# no API, always exits 0 (fail-open).
# stdin: JSON {"prompt": "..."}; stdout: extra context when a signal matches.
set -uo pipefail

ROOT="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"
PACKS="$ROOT/packs"

prompt="$(python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("prompt",""))
except Exception: pass' 2>/dev/null || true)"
[ -z "${prompt:-}" ] && exit 0
low="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"

emit=""
add() { emit="${emit:+$emit
}$1"; }

# Debugging / root-cause → investigation protocol
case "$low" in
  *debug*|*bug*|*error*|*traceback*|*"stack trace"*|*crash*|*failing*|*"not working"*|*버그*|*오류*|*디버그*|*재현*)
    add "[Super SOL:investigation] 디버깅 신호 — $PACKS/investigation-protocol.txt 를 따르세요: 먼저 재현하고, 가설을 3개 이상 세우고, 가설별 증거를 모으고, 원인 사슬을 끝까지 추적한 뒤, 고치기 전후를 검증하고, 기각한 가설도 보고하세요." ;;
esac
# Render / executable artifacts → grounding loop
case "$low" in
  *html*|*svg*|*game*|*canvas*|*chart*|*render*|*website*|*webpage*|*그래프*|*차트*|*렌더*|*화면*)
    add "[Super SOL:grounding] 렌더/실행 산출물 신호 — $PACKS/verification-grounding-pack.txt 를 따르세요: 실제 렌더러에서 돌려 눈으로 출력을 확인하고, 관찰한 문제를 고친 뒤 다시 돌리세요. 정적 점검은 관찰이 아닙니다." ;;
esac

[ -n "$emit" ] && printf '%s\n' "$emit"
exit 0
