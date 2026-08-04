from __future__ import annotations

import json
from pathlib import Path

import pytest

from saads_grill_agent.contracts import AssessmentConfig, AssessmentState
from saads_grill_agent.ledger import AssessmentLedger


def initial_state() -> AssessmentState:
    return AssessmentState(
        config=AssessmentConfig(target_repo=Path("review-target")),
        snapshot_id="snapshot-1",
    )


def updated_state() -> AssessmentState:
    return initial_state().model_copy(
        update={
            "phase": "debating",
            "team_sessions": {
                "red_team": "red-session",
                "code_team": "code-session",
                "judge": "judge-session",
            },
        }
    )


def test_checkpoint_is_atomic_and_event_log_is_append_only(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    ledger.append_event("hypothesis_duplicate", hypothesis_id="hyp-1")
    ledger.checkpoint(updated_state())

    assert json.loads((tmp_path / "run_state.json").read_text("utf-8"))["phase"] == "debating"
    assert len((tmp_path / "events.jsonl").read_text("utf-8").splitlines()) == 1
    assert not list(tmp_path.glob("*.tmp"))


def test_load_restores_state_sessions_and_issued_evidence(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())
    ledger.record_issued_evidence("code-1", "graph-1", "code-1")
    ledger.checkpoint(updated_state())

    restored = AssessmentLedger.load(tmp_path, expected_snapshot_id="snapshot-1")

    assert restored.state == updated_state()
    assert restored.list_issued_evidence() == ["code-1", "graph-1"]
    assert restored.state.team_sessions == {
        "red_team": "red-session",
        "code_team": "code-session",
        "judge": "judge-session",
    }


def test_load_recovers_an_invalid_jsonl_tail(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())
    ledger.append_event("hypothesis_duplicate")
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(events_path.read_text("utf-8") + '{"sequence": 2', encoding="utf-8")

    restored = AssessmentLedger.load(tmp_path, expected_snapshot_id="snapshot-1")
    restored.append_event("missing_cost_metadata", role="judge")

    events = [
        json.loads(line)
        for line in events_path.read_text("utf-8").splitlines()
    ]
    assert [event["sequence"] for event in events] == [1, 2]
    assert [event["event"] for event in events] == [
        "hypothesis_duplicate",
        "missing_cost_metadata",
    ]


def test_load_rejects_incompatible_schema_version(tmp_path: Path) -> None:
    AssessmentLedger.create(tmp_path, initial_state())
    state_path = tmp_path / "run_state.json"
    payload = json.loads(state_path.read_text("utf-8"))
    payload["schema_version"] = 999
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="schema"):
        AssessmentLedger.load(tmp_path, expected_snapshot_id="snapshot-1")


def test_load_rejects_snapshot_mismatch(tmp_path: Path) -> None:
    AssessmentLedger.create(tmp_path, initial_state())

    with pytest.raises(ValueError, match="snapshot"):
        AssessmentLedger.load(tmp_path, expected_snapshot_id="different-snapshot")


def test_append_event_rejects_secret_bearing_detail_key(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    with pytest.raises(ValueError, match="sensitive"):
        ledger.append_event("hypothesis_duplicate", api_key="secret-value")


def test_append_event_rejects_absolute_path_detail(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    with pytest.raises(ValueError, match="absolute path"):
        ledger.append_event(
            "hypothesis_duplicate",
            working_directory=r"C:\sensitive\repo",
        )


def test_append_event_rejects_oversized_string_detail(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    with pytest.raises(ValueError, match="too large"):
        ledger.append_event("hypothesis_duplicate", error="x" * 4097)


def test_append_event_rejects_unknown_event_name(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    with pytest.raises(ValueError, match="unsupported"):
        ledger.append_event("tool_called", safe_detail="preserved")


def test_append_event_persists_allowlisted_safe_payload(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())

    ledger.append_event("forced_finalization_failed", hypothesis_id="hyp-1", error="timeout")

    assert json.loads((tmp_path / "events.jsonl").read_text("utf-8")) == {
        "sequence": 1,
        "event": "forced_finalization_failed",
        "hypothesis_id": "hyp-1",
        "error": "timeout",
    }
