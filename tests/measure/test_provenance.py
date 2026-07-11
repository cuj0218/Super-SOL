"""Provenance recording makes a run id pin its exact conditions."""

from __future__ import annotations

import json
from pathlib import Path

import anyio

from fablized_sol.engine.models import ReasoningEffort
from fablized_sol.eval.day0_ab import run_evaluation
from fablized_sol.eval.manifest import EvalOptions
from fablized_sol.measure.provenance import RunProvenance, write_provenance

_MANIFEST = Path("eval/tasks.example.json").resolve()


def test_provenance_round_trips(tmp_path: Path) -> None:
    provenance = RunProvenance(
        run_id="r1",
        harness_version="9.9.9",
        profile="super-sol",
        profile_version="test",
        product_model="gpt-5.5",
        product_effort="high",
        reference_model="gpt-5.6-sol",
        reference_effort="xhigh",
        arm_design="holdout",
        max_gate_retries=2,
        dry_run=True,
        verification_image=None,
        grader_image=None,
        git_commit="deadbeef",
    )
    path = tmp_path / "provenance.json"
    write_provenance(path, provenance)
    loaded = RunProvenance.model_validate_json(path.read_text(encoding="utf-8"))
    assert loaded == provenance


def test_dry_run_records_provenance_and_effort(tmp_path: Path) -> None:
    options = EvalOptions(
        tasks=_MANIFEST,
        output_dir=tmp_path,
        run_id="dryrun",
        models=("gpt-5.5", "gpt-5.6-sol"),
        product_effort=ReasoningEffort.HIGH,
        reference_effort=ReasoningEffort.XHIGH,
        max_gate_retries=2,
        dry_run=True,
    )
    exit_code = anyio.run(run_evaluation, options)
    assert exit_code == 0

    provenance = json.loads((tmp_path / "dryrun" / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["product_effort"] == "high"
    assert provenance["reference_effort"] == "xhigh"
    assert provenance["git_commit"] is None or isinstance(provenance["git_commit"], str)

    events = (tmp_path / "dryrun" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    efforts = {json.loads(line)["model"]: json.loads(line)["effort"] for line in events}
    assert efforts["gpt-5.5"] == "high"
    assert efforts["gpt-5.6-sol"] == "xhigh"
