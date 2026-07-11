#!/usr/bin/env python3
"""Deterministic, dependency-free task classifier for the Super SOL Codex plugin.

Bilingual (English/Korean) regex tables. No network, no model call, no imports
beyond the standard library. Mirrors the intent of the Super SOL harness
classifier but stays self-contained so the plugin runs without installing the
Python package.
"""

from __future__ import annotations

import re

# Task modes, from most to least demanding. First table to match wins.
_MODE_TABLE: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "deep",
        (
            re.compile(r"\b(?:security|auth|crypto|migration|schema|production|prod|deploy)\b", re.I),
            re.compile(r"\b(?:architecture|end-to-end|e2e|concurren|race condition)\b", re.I),
            re.compile(r"보안|아키텍처|마이그레이션|스키마|운영|배포|엔드투엔드"),
        ),
    ),
    (
        "normal",
        (
            re.compile(r"\b(?:add|build|change|create|fix|implement|refactor|update|write|debug)\b", re.I),
            re.compile(r"구현|수정|추가|변경|작성|만들|리팩터|리팩토링|고쳐|디버그|버그"),
        ),
    ),
    (
        "quick",
        (
            re.compile(r"\b(?:explain|summarize|translate|what is|what does|list|show)\b", re.I),
            re.compile(r"뭐야|뭐지|설명|요약|번역|알려|보여"),
        ),
    ),
)

_RISK_TABLE: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("security", re.compile(r"\b(?:security|auth|password|secret|token|crypto)\b|보안|비밀번호|인증", re.I)),
    ("production", re.compile(r"\b(?:production|prod|deploy|release)\b|운영|배포|릴리스", re.I)),
    ("destructive", re.compile(r"\b(?:delete|drop|erase|remove|rm -rf)\b|삭제|지워|폐기", re.I)),
    ("data", re.compile(r"\b(?:database|db|migration|schema|sql)\b|데이터베이스|마이그레이션|스키마", re.I)),
)


def classify(prompt: str) -> tuple[str, tuple[str, ...]]:
    """Return (mode, risk_flags) for a prompt. Defaults to 'normal' mode."""
    text = prompt or ""
    mode = next(
        (name for name, patterns in _MODE_TABLE if any(p.search(text) for p in patterns)),
        "normal",
    )
    risks = tuple(flag for flag, pattern in _RISK_TABLE if pattern.search(text))
    return mode, risks
