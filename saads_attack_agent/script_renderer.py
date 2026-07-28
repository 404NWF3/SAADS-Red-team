"""Render validated plans as deterministic, offline-only Python scripts."""

from __future__ import annotations

import json

from saads_attack_agent.contracts import (
    AttackCase,
    LongHorizonDialogueScriptPlan,
    PromptInjectionScriptPlan,
    ToolHijackScriptPlan,
)


def _preamble(case: AttackCase) -> str:
    plan_json = json.dumps(
        case.script_plan.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
    )
    return f'''"""Offline simulation generated from a validated attack case."""

import json

OFFLINE_ONLY = True
CASE_ID = {json.dumps(case.case_id, ensure_ascii=False)}
ATTACK_FAMILY = {json.dumps(case.family)}
PLAN = json.loads({plan_json!r})

'''


def _render_prompt_injection(case: AttackCase) -> str:
    if not isinstance(case.script_plan, PromptInjectionScriptPlan):
        raise TypeError("prompt injection case requires its matching script plan")
    return _preamble(case) + '''
class MockTarget:
    """Simulate incorrect instruction priority without external calls."""

    def respond(self, context):
        if context == PLAN["injected_context"]:
            return PLAN["expected_attack_delta"]
        return PLAN["expected_baseline"]


def run_case():
    """Return a baseline-versus-attack simulation result."""
    target = MockTarget()
    baseline = target.respond(PLAN["trusted_context"])
    attack = target.respond(PLAN["injected_context"])
    return {
        "case_id": CASE_ID,
        "family": ATTACK_FAMILY,
        "offline_only": OFFLINE_ONLY,
        "baseline": baseline,
        "attack": attack,
        "changed": baseline != attack,
    }


def main():
    """Print the simulation result as JSON."""
    print(json.dumps(run_case(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def _render_long_dialogue(case: AttackCase) -> str:
    if not isinstance(case.script_plan, LongHorizonDialogueScriptPlan):
        raise TypeError("long dialogue case requires its matching script plan")
    return _preamble(case) + '''
class MockTarget:
    """Simulate state drift across synthetic dialogue turns."""

    def __init__(self):
        self.safety_score = 100

    def apply_turn(self, turn):
        self.safety_score -= 10 * turn["turn"]
        return {
            "turn": turn["turn"],
            "stage": turn["escalation_stage"],
            "safety_score": self.safety_score,
        }


def run_case():
    """Return a baseline-versus-attack simulation result."""
    baseline = {
        "safety_score": 100,
        "system_rule": PLAN["system_rule"],
    }
    target = MockTarget()
    trace = [target.apply_turn(turn) for turn in PLAN["turns"]]
    attack = {
        "safety_score": target.safety_score,
        "trace": trace,
        "expected_state_delta": PLAN["expected_state_delta"],
    }
    return {
        "case_id": CASE_ID,
        "family": ATTACK_FAMILY,
        "offline_only": OFFLINE_ONLY,
        "baseline": baseline,
        "attack": attack,
        "changed": baseline["safety_score"] != attack["safety_score"],
    }


def main():
    """Print the simulation result as JSON."""
    print(json.dumps(run_case(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def _render_tool_hijack(case: AttackCase) -> str:
    if not isinstance(case.script_plan, ToolHijackScriptPlan):
        raise TypeError("tool hijack case requires its matching script plan")
    return _preamble(case) + '''
class MockTarget:
    """Plan mock tool calls while preventing all execution."""

    def plan_baseline(self):
        return {
            "tool": PLAN["allowed_tool"],
            "arguments": PLAN["requested_arguments"],
        }

    def plan_attack(self):
        return PLAN["expected_planned_call"]


def run_case():
    """Return a baseline-versus-attack simulation result."""
    target = MockTarget()
    baseline = target.plan_baseline()
    attack = target.plan_attack()
    return {
        "case_id": CASE_ID,
        "family": ATTACK_FAMILY,
        "offline_only": OFFLINE_ONLY,
        "baseline": baseline,
        "attack": attack,
        "changed": baseline != attack,
        "executed": False,
    }


def main():
    """Print the simulation result as JSON."""
    print(json.dumps(run_case(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def render_attack_script(case: AttackCase) -> str:
    """Render an offline Python simulation for a validated attack case."""
    if case.family == "prompt_injection":
        return _render_prompt_injection(case)
    if case.family == "long_horizon_dialogue":
        return _render_long_dialogue(case)
    return _render_tool_hijack(case)
