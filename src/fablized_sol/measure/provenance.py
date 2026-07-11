"""Run-wide provenance so a benchmark name always pins its exact conditions.

Written once per run as `provenance.json` in the run root. It is out-of-band
metadata (never model-visible) that records the model/effort pair, the
digest-pinned images, the harness version, and the source commit — so the same
run id can never silently mean different conditions.
"""

from __future__ import annotations

import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from fablized_sol.measure.super_sol import SUPER_SOL_PROFILE

if TYPE_CHECKING:
    from pathlib import Path


def harness_version() -> str:
    """Return the installed harness version, or 'unknown' if unavailable."""
    try:
        resolved = version("super-sol-harness")
    except PackageNotFoundError:
        return "unknown"
    return resolved


def git_commit() -> str | None:
    """Return the current commit via an absolute git path, or None."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, absolute git path, no user input
            (git, "rev-parse", "HEAD"),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    if result.returncode == 0 and commit:
        return commit
    return None


class RunProvenance(BaseModel):
    """Immutable record of the exact conditions behind one run id."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)

    run_id: str = Field(min_length=1)
    harness_version: str
    profile: str
    profile_version: str
    product_model: str
    product_effort: str
    reference_model: str
    reference_effort: str
    arm_design: str
    max_gate_retries: int = Field(ge=0)
    dry_run: bool
    verification_image: str | None
    grader_image: str | None
    git_commit: str | None

    @classmethod
    def default_profile(cls) -> tuple[str, str]:
        """Return the active profile name and version for provenance."""
        return SUPER_SOL_PROFILE.name, SUPER_SOL_PROFILE.version


def write_provenance(path: Path, provenance: RunProvenance) -> None:
    """Write provenance as one pretty JSON document in the run root."""
    _ = path.write_text(provenance.model_dump_json(indent=2) + "\n", encoding="utf-8")
