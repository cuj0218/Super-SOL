# Super SOL v0.2.2 — Five-Lane Independent Review

Re-review of the v0.2.2 security/reproducibility patch and the new
`super-sol-codex` plugin, across five independent lanes. Verdicts are grounded
in this session's tool results; gaps that could not be verified here are stated
as gaps, not passes.

Verified this session: `ruff format --check`, `ruff check`, `basedpyright`
(0 errors), `pytest` (135 harness tests) all green; plugin suite 11 tests green;
dry-run emits `provenance.json` + per-event effort. Not verifiable here (no
Docker/API): live reasoning-effort application, image build, and the CVE scan
result — these are wired and gated but must run in a Docker/API environment.

| Lane | Prior (v0.2.1) | Now (v0.2.2) | Residual |
| --- | --- | --- | --- |
| 1. Security / supply chain | FAIL | **Gated** | scan must run in Docker CI to prove 0C/0H |
| 2. Reproducibility | FAIL | **PASS** | live effort effect unverified offline |
| 3. Beginner UX (plugin) | n/a | **PASS** | needs a real Codex install smoke |
| 4. Code quality | PASS | **PASS** | — |
| 5. Benchmark validity | FAIL (HOLD) | **still HOLD** | N=4, ceiling effect unchanged |

## Lane 1 — Security & supply chain

**Change:** Dockerfiles take `ARG BASE_IMAGE`; `scan_images.sh` builds both
images, fails on any Critical/High CVE, and writes an SPDX SBOM per image; an
`image-scan` CI workflow runs the same gate; `SUPPLY_CHAIN.md` documents picking
a clean base and attaching SBOMs as release evidence.

**Verdict: gated, not yet proven clean.** The vulnerable state can no longer
ship silently — it is now blocked by a required gate. But this session has no
Docker, so I did **not** observe a 0-Critical/0-High result; that must come from
the `image-scan` workflow. The default base is still the historically vulnerable
slim digest by design (so the gate goes red until a clean digest is pinned).
The deeper, unchanged risk from the prior red-team analysis remains: the grader
executes model-written code (`subject_worker.py` imports `/workspace`). Base
hardening reduces but does not remove that surface.

**Action before release:** run `image-scan` on a Docker runner, pin a clean
`BASE_IMAGE` digest, attach both SBOMs.

## Lane 2 — Reproducibility

**Change:** `--product-effort` / `--reference-effort` (low/medium/high/xhigh)
recorded per model, applied live via `ModelSettings(reasoning=...)`; every shadow
event carries `effort`; a `provenance.json` pins run id → models+efforts, image
digests, arm design, retries, harness+profile version, and git commit. Effort
follows model identity, so crossover order reversal cannot swap it.

**Verdict: PASS (offline).** Verified by the dry-run (`provenance.json` written,
`gpt-5.5` effort=high / `gpt-5.6-sol` effort=xhigh in events) and two new tests.
The exact prior failure — "same run id, different conditions" — is closed.

**Residual:** whether the SDK actually applies the effort to the model call is
not observable without a live run; the wiring is type-checked but live-unverified.

## Lane 3 — Beginner UX (super-sol-codex plugin)

**Change:** automation-first Codex plugin. Drop-in: classifies each request,
injects only the minimal verified discipline, blocks premature completion once
per turn (capped, fail-open). No API calls, no `OPENAI_API_KEY` read, no model
switching, no billing. Korean beginner status messages; two free layers (base
plugin vs opt-in benchmark).

**Verdict: PASS (offline).** 11 subprocess tests drive each hook exactly as
Codex would; `setup.sh` smoke passes. The design matches the agreed constraints
(no auto-billing, beginner-first, single-retry cap).

**Residual:** not yet installed in a live Codex to confirm hook discovery and the
one-time trust approval end to end. The `PostToolUse` success/mutation detection
is best-effort across payload shapes and should be re-checked against a real
Codex `PostToolUse` schema.

## Lane 4 — Code quality

**Verdict: PASS.** New harness code holds the repo's strict bar: `ruff` (ALL
rules) clean, `basedpyright` typeCheckingMode=all 0 errors, format clean, 135
tests. Suppressions are narrow and justified (one `S603` on a fixed-argv git
call with an absolute path; the CLI I/O function's existing complexity noqa
extended by one). The plugin is correctly excluded from the package's strict
profile and carries its own tests.

## Lane 5 — Benchmark validity

**Verdict: still HOLD — unchanged and correctly so.** v0.2.2 improves plumbing
and provenance, not statistical power. The pilot is still N=4 with a 100%/100%
ceiling, so no quality effect is estimable, and the frozen historical benchmark
must not be read as current-model guidance (now stated in the README). Promotion
still requires the preregistered gate: ≥50 crossover task groups, an unpublished
versioned grader pack, frozen image digests, exactly one external defect label
per session, paired effect sizes, billed-cost accounting, and a preregistered
rerun. The new effort/provenance recording is a prerequisite for that gate, not
a substitute for it.

## Bottom line

v0.2.2 turns three of the four release blockers from "fails silently" into
"gated or fixed": reproducibility is closed, model guidance is corrected, and
the supply-chain vulnerability is now a hard gate rather than a silent pin. The
supply-chain gate still needs one Docker CI run to prove 0C/0H and pin a clean
base, and benchmark validity remains an honest HOLD. Ship the harness and plugin
as experimental tooling; do not attach model-superiority claims.
