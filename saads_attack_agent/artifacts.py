"""Validate and atomically publish attack case artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from saads_attack_agent.contracts import (
    ArtifactPaths,
    GeneratedAttackPackage,
)


class ArtifactValidationError(RuntimeError):
    """A generated script failed the offline publication preflight."""


def _validate_script(
    source: str,
    script: Path,
    *,
    expected_case_id: str,
    expected_family: str,
) -> None:
    try:
        compile(source, "attack.py", "exec")
    except SyntaxError as exc:
        raise ArtifactValidationError(
            "attack.py failed compilation preflight"
        ) from exc

    try:
        with tempfile.TemporaryDirectory(prefix="saads-attack-run-") as run_dir:
            working_directory = Path(run_dir)
            completed = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=working_directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=5,
                env={
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONUTF8": "1",
                },
            )
            if list(working_directory.iterdir()):
                raise ArtifactValidationError(
                    "attack.py created files during preflight"
                )
    except subprocess.TimeoutExpired as exc:
        raise ArtifactValidationError(
            "attack.py exceeded the preflight timeout"
        ) from exc

    if completed.returncode != 0:
        raise ArtifactValidationError(
            "attack.py failed execution preflight"
        )
    try:
        result: Any = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ArtifactValidationError(
            "attack.py preflight output is not one JSON object"
        ) from exc
    if not isinstance(result, dict):
        raise ArtifactValidationError(
            "attack.py preflight output must be a JSON object"
        )
    if (
        result.get("case_id") != expected_case_id
        or result.get("family") != expected_family
        or result.get("offline_only") is not True
    ):
        raise ArtifactValidationError(
            "attack.py preflight output does not match the attack case"
        )


def write_attack_package(
    package: GeneratedAttackPackage,
    output_root: Path,
) -> ArtifactPaths:
    """Publish validated JSON and Python artifacts without overwriting."""
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    final_directory = root / package.case.case_id
    if final_directory.exists():
        raise FileExistsError(
            f"Attack case directory already exists: {final_directory}"
        )

    staging_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{package.case.case_id}-",
            dir=root,
        )
    )
    case_json = staging_directory / "attack_case.json"
    script = staging_directory / "attack.py"
    try:
        case_json.write_text(
            json.dumps(
                package.case.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        script.write_text(package.script_source, encoding="utf-8")
        _validate_script(
            package.script_source,
            script,
            expected_case_id=package.case.case_id,
            expected_family=package.case.family,
        )
        staging_directory.rename(final_directory)
    except Exception:
        if staging_directory.exists():
            shutil.rmtree(staging_directory)
        raise

    return ArtifactPaths(
        directory=final_directory,
        case_json=final_directory / "attack_case.json",
        script=final_directory / "attack.py",
    )
