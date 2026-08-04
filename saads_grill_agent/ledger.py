"""Crash-safe, append-only persistence for adversarial assessments."""

from __future__ import annotations

import json
import math
import os
import re
import uuid
from pathlib import Path
from typing import Any

from saads_grill_agent.contracts import AssessmentState


_SCHEMA_VERSION = 1
_SENSITIVE_KEY = re.compile(
    r"(api[_-]?key|authorization|credential|env|password|secret|token|tool[_-]?(args|arguments))",
    re.IGNORECASE,
)
_ABSOLUTE_WINDOWS_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_MAX_EVENT_STRING_LENGTH = 4096
_ALLOWED_EVENTS = frozenset(
    {
        "forced_finalization_failed",
        "hypothesis_duplicate",
        "missing_cost_metadata",
        "resource_cap_reached",
    }
)
_JSONL_ARTIFACTS = (
    "code_evidence.jsonl",
    "graph_evidence.jsonl",
    "hypotheses.jsonl",
    "debate_rounds.jsonl",
    "events.jsonl",
)


class AssessmentLedger:
    """Persist validated assessment state without retaining sensitive inputs."""

    def __init__(
        self,
        run_dir: Path,
        state: AssessmentState,
        issued_evidence: list[str],
        next_sequence: int,
    ) -> None:
        self.run_dir = run_dir
        self.state = state
        self._issued_evidence = issued_evidence
        self._next_sequence = next_sequence

    @classmethod
    def create(cls, run_dir: Path, initial_state: AssessmentState) -> AssessmentLedger:
        run_dir.mkdir(parents=True, exist_ok=True)
        if any(run_dir.iterdir()):
            raise ValueError("assessment run directory must be empty")
        (run_dir / "tests").mkdir()
        for filename in _JSONL_ARTIFACTS:
            (run_dir / filename).touch(exist_ok=False)
        ledger = cls(run_dir, initial_state, [], 1)
        ledger._write_checkpoint_artifacts()
        cls._atomic_write_json(run_dir / "repository_profile.json", None)
        cls._atomic_write_json(run_dir / "findings.json", [])
        cls._atomic_write_text(run_dir / "report.md", "")
        return ledger

    @classmethod
    def load(cls, run_dir: Path, expected_snapshot_id: str) -> AssessmentLedger:
        run_state = cls._read_versioned_json(run_dir / "run_state.json")
        try:
            state = AssessmentState.model_validate(
                {key: value for key, value in run_state.items() if key != "schema_version"}
            )
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid assessment state") from exc
        if state.snapshot_id != expected_snapshot_id:
            raise ValueError("repository snapshot does not match the assessment state")

        sessions = cls._read_versioned_json(run_dir / "sessions.json")
        issued_evidence = sessions.get("issued_evidence")
        if not isinstance(issued_evidence, list) or not all(
            isinstance(evidence_id, str) for evidence_id in issued_evidence
        ):
            raise ValueError("invalid issued evidence ledger")
        if sessions.get("team_sessions") != state.team_sessions:
            raise ValueError("session metadata does not match the assessment state")

        events = cls._recover_event_tail(run_dir / "events.jsonl")
        next_sequence = events[-1]["sequence"] + 1 if events else 1
        return cls(run_dir, state, issued_evidence, next_sequence)

    def checkpoint(self, state: AssessmentState) -> None:
        self.state = state
        self._write_checkpoint_artifacts()

    def append_event(self, event: str, **details: Any) -> None:
        if event not in _ALLOWED_EVENTS:
            raise ValueError(f"unsupported ledger event: {event}")
        self._validate_event_value(details)
        payload = {
            "sequence": self._next_sequence,
            "event": event,
            **details,
        }
        self._append_jsonl(self.run_dir / "events.jsonl", payload)
        self._next_sequence += 1

    def record_issued_evidence(self, *evidence_ids: str) -> None:
        for evidence_id in evidence_ids:
            if evidence_id not in self._issued_evidence:
                self._issued_evidence.append(evidence_id)
        self._write_sessions()

    def list_issued_evidence(self) -> list[str]:
        return list(self._issued_evidence)

    def _write_checkpoint_artifacts(self) -> None:
        sanitized_state = self._sanitize(self.state.model_dump(mode="json"))
        self._atomic_write_json(
            self.run_dir / "run_state.json",
            {"schema_version": _SCHEMA_VERSION, **sanitized_state},
        )
        self._write_sessions()
        self._atomic_write_json(
            self.run_dir / "repository_profile.json",
            self._sanitize(
                self.state.profile.model_dump(mode="json") if self.state.profile else None
            ),
        )
        self._atomic_write_json(
            self.run_dir / "findings.json",
            self._sanitize([finding.model_dump(mode="json") for finding in self.state.findings]),
        )
        self._atomic_write_jsonl(
            self.run_dir / "hypotheses.jsonl",
            [
                self._sanitize(record.model_dump(mode="json"))
                for record in self.state.hypotheses.values()
            ],
        )

    def _write_sessions(self) -> None:
        self._atomic_write_json(
            self.run_dir / "sessions.json",
            {
                "schema_version": _SCHEMA_VERSION,
                "team_sessions": self._sanitize(self.state.team_sessions),
                "issued_evidence": self._issued_evidence,
            },
        )

    @staticmethod
    def _read_versioned_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid ledger file: {path.name}") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError(f"incompatible ledger schema in {path.name}")
        return payload

    @classmethod
    def _recover_event_tail(cls, path: Path) -> list[dict[str, Any]]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ValueError("unable to read event log") from exc
        events: list[dict[str, Any]] = []
        for index, line in enumerate(lines):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                if index != len(lines) - 1:
                    raise ValueError("invalid event log") from exc
                cls._atomic_write_jsonl(path, events)
                break
            if (
                not isinstance(event, dict)
                or not isinstance(event.get("sequence"), int)
                or event["sequence"] != len(events) + 1
            ):
                raise ValueError("invalid event log")
            events.append(event)
        return events

    @classmethod
    def _atomic_write_json(cls, path: Path, payload: Any) -> None:
        cls._atomic_write_text(
            path, json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )

    @classmethod
    def _atomic_write_jsonl(cls, path: Path, records: list[dict[str, Any]]) -> None:
        cls._atomic_write_text(
            path,
            "".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records
            ),
        )

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        temp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    @classmethod
    def _sanitize(cls, value: Any, key: str | None = None) -> Any:
        if key is not None and _SENSITIVE_KEY.search(key):
            return None
        if isinstance(value, Path):
            return "<redacted-path>" if value.is_absolute() else str(value)
        if isinstance(value, str):
            return "<redacted-path>" if cls._is_absolute_path(value) else value
        if isinstance(value, dict):
            return {
                item_key: cls._sanitize(item_value, item_key)
                for item_key, item_value in value.items()
                if not _SENSITIVE_KEY.search(item_key)
            }
        if isinstance(value, list):
            return [cls._sanitize(item) for item in value]
        return value

    @classmethod
    def _validate_event_value(cls, value: Any, key: str | None = None) -> None:
        if key is not None and _SENSITIVE_KEY.search(key):
            raise ValueError(f"sensitive event detail is not allowed: {key}")
        if isinstance(value, Path):
            if value.is_absolute():
                raise ValueError("absolute path event detail is not allowed")
            raise ValueError("unsupported event detail type: Path")
        if isinstance(value, str):
            if cls._is_absolute_path(value):
                raise ValueError("absolute path event detail is not allowed")
            if len(value) > _MAX_EVENT_STRING_LENGTH:
                raise ValueError("event string detail is too large")
            return
        if value is None or isinstance(value, (bool, int)):
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("event detail must be JSON-serializable")
            return
        if isinstance(value, list):
            for item in value:
                cls._validate_event_value(item)
            return
        if isinstance(value, dict):
            for item_key, item_value in value.items():
                if not isinstance(item_key, str):
                    raise ValueError("event detail keys must be strings")
                cls._validate_event_value(item_value, item_key)
            return
        raise ValueError(f"unsupported event detail type: {type(value).__name__}")

    @staticmethod
    def _is_absolute_path(value: str) -> bool:
        return Path(value).is_absolute() or bool(_ABSOLUTE_WINDOWS_PATH.match(value))
