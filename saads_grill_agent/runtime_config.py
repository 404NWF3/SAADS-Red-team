"""Human-editable red-team run configuration (YAML)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator, model_validator

from saads_grill_agent.contracts import AssessmentConfig, ContractModel, SdkLimits


class RedTeamConfig(ContractModel):
    """All operator-tunable parameters for one grill assessment."""

    # Kept as str until CLI validation so Windows Path does not mangle URLs.
    target_repo: str | None = None
    authorization_ref: str | None = None
    goal: str = "审查该 LLM 应用的代码级安全漏洞"
    output_root: Path = Path("artifacts/grill_runs")

    supplied_model_provider: str | None = None
    supplied_model_name: str | None = None
    supplied_agent_framework: str | None = None
    supplied_frontend_roots: list[str] = Field(default_factory=list)
    supplied_backend_roots: list[str] = Field(default_factory=list)
    scope_includes: list[str] = Field(default_factory=list)
    scope_excludes: list[str] = Field(default_factory=list)

    max_rounds_per_hypothesis: int = Field(default=4, ge=1, le=12)
    max_threat_surfaces: int = Field(default=20, ge=1, le=100)
    max_hypotheses: int = Field(default=40, ge=1, le=200)
    max_agent_calls: int | None = Field(default=100, ge=5, le=10000)
    max_cost_usd: float | None = Field(default=25.0, gt=0, le=500)

    sdk: SdkLimits = Field(default_factory=SdkLimits)

    @field_validator("authorization_ref")
    @classmethod
    def strip_auth(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @model_validator(mode="before")
    @classmethod
    def promote_flat_sdk_keys(cls, data: Any) -> Any:
        """Allow flat YAML keys or a nested ``sdk:`` block."""
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        sdk = dict(payload.get("sdk") or {})
        flat_keys = (
            "team_max_turns",
            "discovery_max_turns",
            "debate_max_turns",
            "judge_max_turns",
            "team_budget_usd",
            "judge_budget_usd",
            "enable_subagents_profiling",
            "enable_subagents_discovery",
            "enable_subagents_debate",
        )
        for key in flat_keys:
            if key in payload and key not in sdk:
                sdk[key] = payload.pop(key)
        if sdk:
            payload["sdk"] = sdk
        return payload

    def to_assessment_config(self, target_repo: Path) -> AssessmentConfig:
        return AssessmentConfig(
            target_repo=target_repo,
            goal=self.goal,
            supplied_model_provider=self.supplied_model_provider,
            supplied_model_name=self.supplied_model_name,
            supplied_agent_framework=self.supplied_agent_framework,
            supplied_frontend_roots=list(self.supplied_frontend_roots),
            supplied_backend_roots=list(self.supplied_backend_roots),
            scope_includes=list(self.scope_includes),
            scope_excludes=list(self.scope_excludes),
            max_rounds_per_hypothesis=self.max_rounds_per_hypothesis,
            max_threat_surfaces=self.max_threat_surfaces,
            max_hypotheses=self.max_hypotheses,
            max_agent_calls=self.max_agent_calls,
            max_cost_usd=self.max_cost_usd,
            sdk=self.sdk,
        )


def default_red_team_config() -> RedTeamConfig:
    return RedTeamConfig()


def load_red_team_config(path: Path | None) -> RedTeamConfig:
    """Load YAML config; missing path yields defaults."""
    if path is None:
        return default_red_team_config()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read config: {path}") from exc
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in config: {path}") from exc
    if payload is None:
        return default_red_team_config()
    if not isinstance(payload, dict):
        raise ValueError("red-team config YAML must be a mapping")
    return RedTeamConfig.model_validate(payload)


def merge_cli_over_config(
    config: RedTeamConfig,
    *,
    target_repo: str | None,
    authorization_ref: str | None,
    goal: str | None,
    output_root: Path | None,
    max_rounds: int | None,
    max_cost_usd: float | None,
    profile_overrides: dict[str, Any] | None = None,
) -> RedTeamConfig:
    """CLI / profile values win when explicitly provided."""
    updates: dict[str, Any] = dict(profile_overrides or {})
    if target_repo:
        updates["target_repo"] = target_repo
    if authorization_ref is not None and authorization_ref.strip():
        updates["authorization_ref"] = authorization_ref.strip()
    if goal is not None:
        updates["goal"] = goal
    if output_root is not None:
        updates["output_root"] = output_root
    if max_rounds is not None:
        updates["max_rounds_per_hypothesis"] = max_rounds
    if max_cost_usd is not None:
        updates["max_cost_usd"] = max_cost_usd
    return config.model_copy(update=updates) if updates else config
