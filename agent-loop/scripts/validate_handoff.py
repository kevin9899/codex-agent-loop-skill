#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from urllib.parse import unquote
from pathlib import Path

SCALAR_FIELDS = [
    "handoff_schema_version",
    "working_goal",
    "run_intent",
    "host_resume_mode",
    "capability_mode",
    "current_or_next_stage",
    "stage_status",
    "current_batch",
    "risk_tier",
    "implementation_gate_status",
    "implementation_gate_evidence",
    "latest_evidence_summary",
    "blocking_findings",
    "residual_risks",
    "goal_completion_status",
    "goal_completion_evidence",
    "loop_state",
    "continuation_mode",
    "closeout_round_id",
    "run_decision",
    "sequential_objectives_status",
    "stop_authorization_status",
    "stop_authorization_evidence",
    "stop_consensus_status",
    "stop_consensus_evidence",
    "external_authority_basis",
    "pause_reason",
    "next_mandatory_action",
    "continue_exit_status",
    "continue_exit_evidence",
    "turn_exit_cause",
    "turn_exit_evidence",
    "resume_instructions",
]

OPTIONAL_SCALAR_FIELDS = [
    "work_type",
    "review_kind",
    "authority_record_ref",
    "run_authority_status",
    "run_authority_revision",
    "run_authority_epoch",
    "source_digest",
    "stage_graph_digest",
    "adapter_manifest_ref",
    "adapter_conformance_status",
    "adapter_effective_config_digest",
    "resource_telemetry_ref",
    "research_cycle_ref",
    "research_cycle_status",
    "research_cycle_digest_set",
    "commit_queue_status",
    "completion_subject_type",
    "completion_subject_ref",
    "completion_subject_digest",
    "composite_subject_digest",
    "challenge_cycle_ref",
    "challenge_cycle_status",
    "challenge_cycle_digest_set",
    "visible_output_contract",
]

LIST_OR_SCALAR_FIELDS = {
    "remaining_required_stages",
}

CANONICAL_FIELD_NAMES = set(SCALAR_FIELDS) | set(OPTIONAL_SCALAR_FIELDS) | LIST_OR_SCALAR_FIELDS

# Delegated `$loop` consensus proofs must be produced with explicit gpt-5.5/high
# or stronger model args, not inherited/default subagent settings. gpt-5.4,
# Spark, 5.3, and mini-model lanes are intentionally inadmissible for this
# process.
HARD_ADMISSIBLE_DELEGATED_MODEL_SLUGS = ("gpt-5.5",)
HARD_TOP_DELEGATED_MODEL_SLUG = "gpt-5.5"
HARD_TOP_DELEGATED_REASONING_EFFORT = "xhigh"
HARD_ALLOWED_DELEGATED_REASONING_EFFORTS = ("xhigh", "high")
HARD_DELEGATED_CAPABILITY_CLASS_BY_SLUG = {
    "gpt-5.5": "frontier_loop_authority_v1",
}
REQUIRED_DELEGATED_MODEL_POLICY = os.environ.get(
    "AGENT_LOOP_REQUIRED_MODEL_POLICY",
    "gpt_5_5_high_minimum_explicit",
).strip()
TOP_DELEGATED_MODEL_SLUG = os.environ.get(
    "AGENT_LOOP_TOP_MODEL",
    "gpt-5.5",
).strip()
TOP_DELEGATED_REASONING_EFFORT = os.environ.get(
    "AGENT_LOOP_TOP_REASONING_EFFORT",
    "xhigh",
).strip()
REQUIRED_DELEGATED_MODEL_SLUG = os.environ.get(
    "AGENT_LOOP_REQUIRED_MODEL",
    TOP_DELEGATED_MODEL_SLUG,
).strip()
REQUIRED_DELEGATED_REASONING_EFFORT = os.environ.get(
    "AGENT_LOOP_REQUIRED_REASONING_EFFORT",
    TOP_DELEGATED_REASONING_EFFORT,
).strip()
MIN_TOP_MODEL_LANES = int(os.environ.get("AGENT_LOOP_MIN_TOP_MODEL_LANES", "5").strip())
MIN_TOP_XHIGH_LANES = int(os.environ.get("AGENT_LOOP_MIN_TOP_XHIGH_LANES", "3").strip())
MINIMUM_DELEGATED_REASONING_EFFORTS = ("xhigh", "high")
ALLOWED_DELEGATED_MODEL_SLUGS = tuple(
    model.strip().lower()
    for model in os.environ.get(
        "AGENT_LOOP_ALLOWED_MODELS",
        "gpt-5.5",
    ).split(",")
    if model.strip()
)
ALLOWED_DELEGATED_REASONING_EFFORTS = tuple(
    effort.strip().lower()
    for effort in os.environ.get(
        "AGENT_LOOP_ALLOWED_REASONING_EFFORTS",
        "xhigh,high",
    ).split(",")
    if effort.strip() and effort.strip().lower() in MINIMUM_DELEGATED_REASONING_EFFORTS
)
REQUIRED_DELEGATED_CAPABILITY_CLASS = os.environ.get(
    "AGENT_LOOP_REQUIRED_CAPABILITY_CLASS",
    "frontier_loop_authority_v1",
).strip()
MODEL_CAPABILITY_CLASS_BY_SLUG = {
    pair.split("=", 1)[0].strip().lower(): pair.split("=", 1)[1].strip()
    for pair in os.environ.get(
        "AGENT_LOOP_MODEL_CAPABILITY_CLASSES",
        "gpt-5.5=frontier_loop_authority_v1",
    ).split(",")
    if "=" in pair and pair.split("=", 1)[0].strip() and pair.split("=", 1)[1].strip()
}

def _fail_if_model_floor_weakened() -> None:
    if (
        TOP_DELEGATED_MODEL_SLUG.lower() != HARD_TOP_DELEGATED_MODEL_SLUG
        or TOP_DELEGATED_REASONING_EFFORT.lower() != HARD_TOP_DELEGATED_REASONING_EFFORT
        or REQUIRED_DELEGATED_MODEL_SLUG.lower() != HARD_TOP_DELEGATED_MODEL_SLUG
    ):
        raise SystemExit(
            "invalid model floor: delegated loop strongest-model authority requires "
            f"{HARD_TOP_DELEGATED_MODEL_SLUG}/{HARD_TOP_DELEGATED_REASONING_EFFORT}"
        )
    configured_models = {
        TOP_DELEGATED_MODEL_SLUG.lower(),
        REQUIRED_DELEGATED_MODEL_SLUG.lower(),
        *ALLOWED_DELEGATED_MODEL_SLUGS,
    }
    unsupported_models = {
        model
        for model in configured_models
        if (
            model not in HARD_ADMISSIBLE_DELEGATED_MODEL_SLUGS
            or MODEL_CAPABILITY_CLASS_BY_SLUG.get(model) != HARD_DELEGATED_CAPABILITY_CLASS_BY_SLUG.get(model)
            or MODEL_CAPABILITY_CLASS_BY_SLUG.get(model) != REQUIRED_DELEGATED_CAPABILITY_CLASS
        )
    }
    if unsupported_models:
        raise SystemExit(
            "invalid model floor: delegated loop validation requires capability class "
            f"{REQUIRED_DELEGATED_CAPABILITY_CLASS}; unsupported model(s): "
            + ", ".join(sorted(unsupported_models))
        )
    configured_efforts = {
        TOP_DELEGATED_REASONING_EFFORT.lower(),
        REQUIRED_DELEGATED_REASONING_EFFORT.lower(),
        *ALLOWED_DELEGATED_REASONING_EFFORTS,
    }
    if (
        REQUIRED_DELEGATED_REASONING_EFFORT.lower() != HARD_TOP_DELEGATED_REASONING_EFFORT
        or not configured_efforts
        or not configured_efforts.issubset(set(HARD_ALLOWED_DELEGATED_REASONING_EFFORTS))
    ):
        raise SystemExit(
            "invalid reasoning floor: delegated loop strongest-model authority requires xhigh, "
            "with high allowed only for explicit lower lanes"
        )


_fail_if_model_floor_weakened()
REQUIRED_DELEGATED_MODEL_BINDING = "explicit_tool_args"
REQUIRED_DELEGATED_MODEL_MIX = {
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "xhigh"): 3,
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "high"): 2,
}
REQUIRED_IMPLEMENTATION_CHALLENGE_MODEL_MIX = {
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "xhigh"): 3,
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "high"): 2,
}
REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX = {
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "xhigh"): 1,
    (REQUIRED_DELEGATED_CAPABILITY_CLASS, "high"): 1,
}
REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS = {
    "operator_execution_fit",
    "verification_evidence_fit",
}
REQUIRED_PRE_IMPLEMENTATION_VIEWPOINTS = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}
REQUIRED_POST_IMPLEMENTATION_VIEWPOINTS = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}
REQUIRED_FINAL_POLICY_ROUTE_CONTEXT = "final_halt_completion"
REQUIRED_FINAL_POLICY_COVERAGE_VERDICT = "route_required_refs_loaded"
REQUIRED_FINAL_LOADED_POLICY_REF_TOKENS = (
    "skill.md#nonnegotiableinvariants",
    "handoff-template.md#finalproof",
)
OPTIONAL_PROJECT_POLICY_REF_TOKENS = (
    "agents.md#loopcompletiongate",
)
AGENT_LOOP_SKILL_DIR = Path(
    os.environ.get(
        "AGENT_LOOP_SKILL_DIR",
        str(Path(__file__).resolve().parents[1]),
    )
)
POLICY_REF_DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$", re.IGNORECASE)
REQUIRED_DELEGATED_AGENT_COUNT = 5
VERIFIED_COMPLETE_STATUS = "verified_complete_5lane"
REQUIRED_FINAL_CHALLENGE_AGENT_ROLE = "challenge_agent"
REQUIRED_STRATEGY_AGENT_ROLE = "strategy_agent"
REQUIRED_VERIFICATION_AGENT_ROLE = "verification_agent"
REQUIRED_VERIFICATION_AGENT_MODE = "current_stage_verification"
REQUIRED_FINAL_CHALLENGE_MODES = {
    "stop_authorization": "autonomous_stop_challenge",
    "goal_completion": "goal_completion_challenge",
}
REQUIRED_SOURCE_REF = "source.md"
REQUIRED_IDEAS_REF = "ideas.md"
REQUIRED_FINAL_AUDIT_CONTEXT_MODE = "clean_source_first"
REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS = "source_md_original_user_prompt"
REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED = "yes"
REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST = "untrusted_ideas_research_revised_plan_evidence_handoff"
REQUIRED_FINAL_AUDIT_REPO_INSPECTION = "fresh"
REQUIRED_FINAL_AUDIT_SCOPE_VERDICT = "original_request_satisfied"
REQUIRED_GOAL_COMPLETION_ALIGNMENT_VERDICT = "all_source_requirements_satisfied"
REQUIRED_AUTHORITY_SCHEMA_VERSION = "v3-worktype-authority"
REQUIRED_AUTHORITY_POLICY_VERSION = "agent-loop-v3-worktype-authority"
REQUIRED_AUTHORITY_PROMPT_VERSION = "final-5lane-v3"
REQUIRED_AUTHORITY_VALIDATOR_VERSION = "validate_handoff:v3-worktype-authority:1"
REQUIRED_CHALLENGE_CYCLE_SCHEMA_VERSION = "challenge-cycle-v1"
REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION = "research-cycle-v1"
REQUIRED_CAS_TRANSITION_RECEIPT_VERSION = "v1"
REQUIRED_RESEARCH_DISPATCH_PHASE = "initial_research"
REQUIRED_INITIAL_RESEARCH_LANES = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}
WORK_TYPE_COMPLETION_SUBJECT_TYPES = {
    "implementation": {"repo_diff", "operation_record"},
    "research": {"research_packet"},
    "docs": {"document_artifact"},
    "planning": {"plan_artifact"},
    "review": {"plan_review", "artifact_review", "completion_challenge", "audit_packet"},
    "mixed": {"composite_subject"},
}
REVIEW_KIND_COMPLETION_SUBJECT_TYPES = {
    "plan_review": "plan_review",
    "artifact_review": "artifact_review",
    "completion_challenge": "completion_challenge",
    "audit": "audit_packet",
}
ALLOWED_ADAPTER_OVERRIDE_KEYS = {
    "local_verification_command_mapping",
    "artifact_root_aliases",
    "quota_limits",
    "dev_server_policy",
    "extra_nonterminal_evidence_requirements",
    "project_specific_subject_validators",
    "stricter_output_constraints",
}
RESOURCE_TELEMETRY_REQUIRED_PATTERNS = [
    r"\btelemetry_required\b",
    r"\bresource_telemetry_required\b",
    r"\bscheduling_impact=resource\b",
    r"\bscheduling_impact=quota\b",
    r"\bscheduling_impact=tool_limit\b",
    r"\bcontroller_decision=(?:defer_specific_action|shrink_batch|retry_when_available|continue_with_smaller_local_action)\b",
    r"\btool[-\s]?limits?\b",
    r"\bquota/tool blocked\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\b(?:blocked by quota|quota blocked|usage limits?)\b",
    r"\b(?:blocked by quota|quota blocked|usage limits?)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bquota\s+limits?\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bquota\s+limits?\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bquota\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bquota\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bcredits?\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bcredits?\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\bresource[-\s]?busy\b",
    r"\brate[-\s]?limited\b",
    r"\brate[-\s]?limits?\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\b(?:reached|hit|exceeded|exhausted)\s+rate[-\s]?limits?\b",
]
RESOURCE_TELEMETRY_REAL_SCHEDULING_PATTERNS = [
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\b(?:blocked by quota|quota blocked|usage limits?)\b",
    r"\b(?:blocked by quota|quota blocked|usage limits?)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bquota\s+limits?\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bquota\s+limits?\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bquota\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bquota\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
    r"\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b.{0,80}\bcredits?\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\bcredits?\s+(?:reached|hit|exceeded|exhausted)\b.{0,80}\b(?:delegated|dispatch|spawn_agent|controller|challenge|agent|tool|process)\b",
]
RESOURCE_TELEMETRY_REAL_SCHEDULING_NEGATED_PATTERNS = [
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+quota\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?quota\s+blocked\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+usage\s+limits?\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+tool[-\s]?limits?\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+rate[-\s]?limits?\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+resource[-\s]?busy\b",
]
RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS = [
    r"\b(?:storybook|mock(?:ed)?|fixture|component)\b.{0,120}\b(?:ui|visual|copy|error state|error-state|error copy|render(?:s|ed|ing)?|display(?:s|ed|ing)?)\b",
    r"\b(?:ui|visual)\b.{0,80}\b(?:copy|error state|error-state|error copy|render(?:s|ed|ing)?|display(?:s|ed|ing)?)\b",
    r"\b(?:copy only|error copy|error-state copy)\b",
    r"\b(?:render(?:s|ed|ing)?|display(?:s|ed|ing)?)\b.{0,80}\b(?:copy|error state|error-state|error copy)\b",
    r"(?:ui|오류\s*상태|문구|표시(?:함|됨)?|렌더).{0,80}(?:에이전트|사용량|한도|쿼터)",
    r"(?:에이전트|사용량|한도|쿼터).{0,80}(?:ui|오류\s*상태|문구|표시(?:함|됨)?|렌더)",
]
RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS = [
    r"^\s*(?:dispatch\s+)?(?:blocked\s+by\s+quota|quota\s+blocked|usage\s+limits?)\s*$",
    r"^\s*quota/tool\s+blocked\s*$",
    r"^\s*tool[-\s]?limits?\s*$",
]
RESOURCE_TELEMETRY_EXPLICIT_DECISION_PATTERNS = [
    r"\btelemetry_required\b",
    r"\bresource_telemetry_required\b",
    r"\bscheduling_impact=(?:resource|quota|tool_limit)\b",
    r"\bcontroller_decision=(?:defer_specific_action|shrink_batch|retry_when_available|continue_with_smaller_local_action)\b",
]
RESOURCE_TELEMETRY_NEGATED_PATTERNS = [
    r"\bnot\s+(?:rate[-\s]?limited|resource[-\s]?busy|tool[-\s]?limited|quota[-\s]?limited)\b",
    r"\b(?:usage\s+limits?|rate[-\s]?limits?|resource[-\s]?busy|tool[-\s]?limits?|quota(?:\s+limits?)?)\s+(?:was|were)?\s*(?:ruled\s+out|not\s+present|not\s+observed|absent)\b",
    r"\bwithout\s+(?:usage\s+limits?|rate[-\s]?limits?|resource[-\s]?busy|tool[-\s]?limits?|quota(?:\s+limits?)?)\b",
    r"\bno\s+(?:usage\s+limits?|rate[-\s]?limits?|resource[-\s]?busy|tool[-\s]?limits?|quota(?:\s+limits?)?)\b",
    r"\bnot\s+blocked\s+by\s+quota\b",
    r"\bwas(?:\s+not|n't)\s+(?:actually\s+)?blocked\s+by\s+quota\b",
    r"\b(?:was(?:\s+not|n't)|not)\s+(?:actually\s+)?blocked\s+by\s+(?:usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?|resource[-\s]?busy)\b",
    r"\b(?:usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?|resource[-\s]?busy)\s+(?:was|were)\s+(?:ruled\s+out|not\s+present|not\s+observed|absent)\b",
    r"\b(?:quota(?:\s+limits?)?|usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?)\s+(?:(?:was|were|wasn't|weren't)\s+)?not\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\b(?:quota(?:\s+limits?)?|usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?)\s+(?:wasn't|weren't)\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\b(?:quota(?:\s+limits?)?|usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?)\s+(?:has|have)\s+not\s+been\s+(?:reached|hit|exceeded|exhausted)\b",
    r"\b(?:quota(?:\s+limits?)?|usage\s+limits?|tool[-\s]?limits?|rate[-\s]?limits?)\s+(?:hasn't|haven't)\s+been\s+(?:reached|hit|exceeded|exhausted)\b",
    r"리소스.{0,20}(아님|없|배제)",
    r"쿼터.{0,20}(아님|없|배제)",
    r"레이트.?리밋.{0,20}(아님|없|배제)",
]
RESOURCE_TELEMETRY_NON_SCHEDULING_CONTEXT_PATTERNS = [
    r"\bmock(?:ed)?\b.{0,80}\b(?:rate[-\s]?(?:limited|limits?)|resource[-\s]?busy|tool[-\s]?limits?|quota)\b",
    r"\b(?:rate[-\s]?(?:limited|limits?)|resource[-\s]?busy|tool[-\s]?limits?|quota)\b.{0,80}\b(?:mock(?:ed)?|fixture|copy|error state|error-state|display|visual|component|storybook)\b",
    r"\b(?:ui|copy|error state|error-state|component|storybook)\b.{0,80}\b(?:rate[-\s]?(?:limited|limits?)|resource[-\s]?busy|tool[-\s]?limits?|quota)\b",
    r"\b(?:docs?|documentation|readme|guide)\b.{0,120}\b(?:explain(?:s|ed|ing)?|describ(?:e|es|ed|ing)|document(?:s|ed|ing)?|mention(?:s|ed|ing)?|updated)\b.{0,120}\b(?:rate[-\s]?limits?|resource[-\s]?busy|tool[-\s]?limits?|usage\s+limits?|credits?|quota)\b",
    r"\b(?:rate[-\s]?limits?|resource[-\s]?busy|tool[-\s]?limits?|usage\s+limits?|credits?|quota)\b.{0,120}\b(?:explain(?:s|ed|ing)?|describ(?:e|es|ed|ing)|document(?:s|ed|ing)?|mention(?:s|ed|ing)?)\b.{0,120}\b(?:docs?|documentation|readme|guide)\b",
    r"\b(?:docs?|documentation|readme|guide)\b.{0,120}\b(?:explain(?:s|ed|ing)?|describ(?:e|es|ed|ing)|document(?:s|ed|ing)?|mention(?:s|ed|ing)?|updated)\b.{0,120}\b(?:spawn_agent|delegated|dispatch|challenge|agent)\b.{0,120}\b(?:credits?|quota|usage\s+limits?|rate[-\s]?limits?|tool[-\s]?limits?|resource[-\s]?busy)\b",
    r"\b(?:spawn_agent|delegated|dispatch|challenge|agent)\b.{0,120}\b(?:credits?|quota|usage\s+limits?|rate[-\s]?limits?|tool[-\s]?limits?|resource[-\s]?busy)\b.{0,120}\b(?:explain(?:s|ed|ing)?|describ(?:e|es|ed|ing)|document(?:s|ed|ing)?|mention(?:s|ed|ing)?)\b.{0,120}\b(?:docs?|documentation|readme|guide)\b",
    r"\b(?:smoke|test|coverage)\b.{0,120}\b(?:coverage|parsing|parser|case|smoke|test)?\b.{0,120}\b(?:tool[-\s]?limits?|resource[-\s]?busy|rate[-\s]?limits?|quota|usage\s+limits?)\b.{0,120}\b(?:passed|verified|covered|coverage|parsing)\b",
    r"모의.{0,40}(레이트.?리밋|리소스|쿼터)",
]
RESOURCE_TELEMETRY_DOC_OR_COPY_PREFIX_SEGMENT_PATTERNS = [
    r"^\s*(?:docs?|documentation|readme|guide|test|tests?|smoke|coverage)\s*$",
    r"^\s*(?:korean\s+copy|copy|ui\s+copy|ux\s+copy)\s*$",
    r"^\s*(?:한국어\s*)?(?:문구|복사문구|ui\s*문구|오류\s*문구)\s*$",
]
RESOURCE_TELEMETRY_EVENT_TYPES = {
    "quota_limit",
    "rate_limit",
    "resource_pressure",
    "tool_unavailable",
    "process_bottleneck",
    "usage_limit",
}
REQUIRED_CAPABILITY_MODE_TOKENS = (
    "delegated_agents_authorized_by_loop_tool_available",
    "delegated_agents_authorized_by_loop_tool_unavailable",
    "delegated_agents_authorized_by_loop_tool_state_unknown",
)


def delegated_model_is_allowed(model_slug: str, reasoning_effort: str) -> bool:
    model = clean_value(model_slug).lower()
    effort = clean_value(reasoning_effort).lower()
    return (
        model in HARD_ADMISSIBLE_DELEGATED_MODEL_SLUGS
        and model in ALLOWED_DELEGATED_MODEL_SLUGS
        and MODEL_CAPABILITY_CLASS_BY_SLUG.get(model) == HARD_DELEGATED_CAPABILITY_CLASS_BY_SLUG.get(model)
        and effort in ALLOWED_DELEGATED_REASONING_EFFORTS
    )


def delegated_model_is_top(model_slug: str, reasoning_effort: str) -> bool:
    return clean_value(model_slug).lower() == TOP_DELEGATED_MODEL_SLUG.lower()


def delegated_model_is_top_xhigh(model_slug: str, reasoning_effort: str) -> bool:
    return (
        clean_value(model_slug).lower() == TOP_DELEGATED_MODEL_SLUG.lower()
        and clean_value(reasoning_effort).lower() == TOP_DELEGATED_REASONING_EFFORT.lower()
    )


def delegated_lane_model_key(model_slug: str, reasoning_effort: str) -> tuple[str, str]:
    model = clean_value(model_slug).lower()
    capability_class = MODEL_CAPABILITY_CLASS_BY_SLUG.get(model, model)
    return capability_class, clean_value(reasoning_effort).lower()


def split_policy_list(value: object) -> list[str]:
    text = flatten_multivalue_text(value)
    return [clean_value(part) for part in re.split(r"[|,]", text) if clean_value(part)]


def policy_list_is_exact(value: object, expected: set[str]) -> bool:
    refs = [re.sub(r"\s+", "", ref.lower()) for ref in split_policy_list(value)]
    return len(refs) == len(expected) and len(set(refs)) == len(refs) and set(refs) == expected


def adapter_declared_policy_ref_tokens(run_dir: Path) -> set[str] | None:
    authority_path = current_v3_authority_record_path(run_dir)
    adapter_ref = record_value(authority_path, "adapter_manifest_ref")
    adapter_path = resolve_artifact_ref(adapter_ref, run_dir)
    adapter = read_record_json(adapter_path)
    project_policy_refs = record_json_get(adapter, "project_policy_refs")
    if project_policy_refs is None:
        return set()
    if not isinstance(project_policy_refs, list):
        return None
    tokens: set[str] = set()
    for ref in project_policy_refs:
        ref_token = re.sub(r"\s+", "", clean_value(str(ref)).lower())
        if ref_token not in OPTIONAL_PROJECT_POLICY_REF_TOKENS:
            return None
        repo_root = repo_root_for_run_dir(run_dir)
        if ref_token == "agents.md#loopcompletiongate":
            if repo_root is None or not (repo_root / "AGENTS.md").exists():
                return None
        tokens.add(ref_token)
    return tokens


def expected_policy_ref_tokens(run_dir: Path) -> set[str] | None:
    adapter_tokens = adapter_declared_policy_ref_tokens(run_dir)
    if adapter_tokens is None:
        return None
    tokens = set(REQUIRED_FINAL_LOADED_POLICY_REF_TOKENS) | adapter_tokens
    repo_root = repo_root_for_run_dir(run_dir)
    if repo_root is not None and (repo_root / "AGENTS.md").exists():
        tokens.add("agents.md#loopcompletiongate")
    return tokens


def policy_ref_tokens_are_complete(value: object, run_dir: Path) -> bool:
    expected = expected_policy_ref_tokens(run_dir)
    return expected is not None and policy_list_is_exact(value, expected)


def markdown_heading_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", clean_value(value).lower())


def normalized_markdown_section_text(path: Path, anchor: str) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start_index = -1
    start_level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match and markdown_heading_slug(match.group(2)) == anchor:
            start_index = index
            start_level = len(match.group(1))
            break
    if start_index < 0:
        return None
    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index])
        if match and len(match.group(1)) <= start_level:
            end_index = index
            break
    return "\n".join(lines[start_index:end_index]).rstrip() + "\n"


def repo_root_for_run_dir(run_dir: Path) -> Path | None:
    for authority_path in (run_dir / "authority" / "run-authority.json", run_dir / "run-authority.json"):
        authority = read_record_json(authority_path)
        if authority is None:
            continue
        for key in ("cwd_root_binding", "project_root_ref"):
            raw = json_value_text(authority, key)
            if not raw or raw.lower().startswith("run://"):
                continue
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = (run_dir / candidate).resolve()
            else:
                candidate = candidate.resolve()
            if (candidate / "AGENTS.md").exists():
                return candidate
        return None
    for candidate in [run_dir.resolve(), *run_dir.resolve().parents]:
        if (candidate / "AGENTS.md").exists():
            return candidate
    return None


def expected_policy_ref_digests(run_dir: Path) -> list[str]:
    refs = [
        (AGENT_LOOP_SKILL_DIR / "SKILL.md", "nonnegotiableinvariants"),
        (AGENT_LOOP_SKILL_DIR / "references" / "handoff-template.md", "finalproof"),
    ]
    project_policy_refs = adapter_declared_policy_ref_tokens(run_dir)
    if project_policy_refs is None:
        return []
    repo_root = repo_root_for_run_dir(run_dir)
    if repo_root is not None and (repo_root / "AGENTS.md").exists():
        refs.append((repo_root / "AGENTS.md", "loopcompletiongate"))
    digests: list[str] = []
    for path, anchor in refs:
        section_text = normalized_markdown_section_text(path, anchor)
        if section_text is None:
            return []
        digests.append(f"sha256:{hashlib.sha256(section_text.encode('utf-8')).hexdigest()}")
    return digests


def policy_ref_digests_are_valid(value: object, run_dir: Path) -> bool:
    digests = split_policy_list(value)
    expected = expected_policy_ref_digests(run_dir)
    expected_tokens = expected_policy_ref_tokens(run_dir)
    if expected_tokens is None:
        return False
    return (
        len(digests) == len(expected_tokens)
        and len(set(digests)) == len(digests)
        and all(POLICY_REF_DIGEST_RE.fullmatch(digest) for digest in digests)
        and len(expected) == len(expected_tokens)
        and set(digests) == set(expected)
    )


IDEATION_STATUSES = {"completed", "not_material", "reopened"}
IDEATION_LANE_COUNTS = {"0", "3", "5"}
IDEATION_SKIP_OR_REOPEN_REASONS = {
    "ideation_not_material",
    "remaining_gap",
    "new_constraint",
    "higher_leverage_candidate",
    "high_impact_ambiguous",
    "none",
}
IDEA_STATUSES = {"pending", "validated", "rejected", "stale"}
IDEA_SOURCE_TYPES = {
    "official_primary",
    "source_code_or_runtime",
    "vendor_docs",
    "paper_or_standard",
    "secondary_expert",
    "community_anecdote",
    "example_only",
    "ai_memory",
    "unverified_web_lead",
}
IDEA_SOURCE_QUALITIES = {"strong", "medium", "weak", "memory_only"}
IDEA_VALIDATION_REQUIREMENTS = {
    "official_docs",
    "primary_source",
    "runtime_evidence",
    "repo_inspection",
    "not_material",
}
IDEA_CURRENCY_RISKS = {"low", "medium", "high"}
IDEA_REQUIRED_FIELDS = {
    "idea_id",
    "cycle_id",
    "source_requirement_ref",
    "idea",
    "source_or_inspiration",
    "source_type",
    "source_quality",
    "provenance_ref",
    "accessed_at",
    "memory_only",
    "why_it_might_matter",
    "existence_question",
    "applicability_question",
    "validation_required",
    "currency_risk",
    "blocking",
    "pending_reason",
    "last_reviewed_stage",
    "next_review_trigger",
    "research_status",
}
IDEA_PENDING_REASONS = {"not_material", "deferred", "awaiting_research", "none"}
IDEA_REVIEW_STAGES = {"ideation", "research", "planning", "reassessment"}
IDEA_REQUIRED_BUT_NONE_ALLOWED_FIELDS = {"next_review_trigger", "pending_reason"}
IDEAS_GATE_FIELDS = {"ideation_status", "viewpoint_count", "lane_count", "cap", "skip_or_reopen_reason"}
IDEAS_KNOWN_FIELDS = IDEAS_GATE_FIELDS | IDEA_REQUIRED_FIELDS | {
    "research_ref",
    "evidence_ref",
    "decision_date",
    "decision_summary",
    "validated_against",
}

ENUMS = {
    "handoff_schema_version": {
        "v2-stop-consensus",
        "v3-worktype-authority",
    },
    "run_intent": {
        "implementation_oriented",
        "planning_only",
        "implementation_loop",
    },
    "loop_state": {
        "ideation",
        "research",
        "planning",
        "execution",
        "verify",
        "reassessment_pending",
        "paused",
        "stopped",
    },
    "continuation_mode": {
        "default",
        "nonstop",
    },
    "host_resume_mode": {
        "same_turn_only",
        "durable_runtime",
    },
    "run_decision": {
        "planning_complete",
        "continue",
        "pause",
        "stop",
    },
    "sequential_objectives_status": {
        "none_detected",
        "open",
        "satisfied",
    },
    "stop_authorization_status": {
        "not_applicable",
        "not_run",
        "deny",
        "allow",
        "external_authority",
    },
    "stop_consensus_status": {
        "not_applicable",
        "not_run",
        "deny",
        "allow_unanimous",
        "waived_external_authority",
    },
    "external_authority_basis": {
        "none",
        "explicit_user_pause",
        "explicit_user_stop",
        "explicit_user_redirect",
        "human_decision_required",
        "host_turn_boundary",
    },
    "continue_exit_status": {
        "not_applicable",
        "next_action_started",
        "blocked_during_attempt",
    },
    "turn_exit_cause": {
        "not_applicable",
        "context_budget_exhausted",
        "tool_timeout_after_batch_shrink",
        "blocked_during_attempt",
        "host_turn_boundary_pause",
        "user_interrupt",
    },
    "goal_completion_status": {
        "not_reached",
        "completion_candidate",
        VERIFIED_COMPLETE_STATUS,
    },
    "risk_tier": {
        "tier0_trivial",
        "tier1_local",
        "tier2_material",
        "tier3_high_risk",
        "not_classified",
    },
    "implementation_gate_status": {
        "not_applicable",
        "strategy_pending",
        "pre_challenge_pending",
        "implementation_in_progress",
        "verification_pending",
        "post_challenge_pending",
        "accepted",
        "blocked",
    },
    "work_type": {
        "implementation",
        "research",
        "docs",
        "planning",
        "review",
        "mixed",
        "not_classified",
    },
    "review_kind": {
        "not_applicable",
        "plan_review",
        "artifact_review",
        "completion_challenge",
        "audit",
    },
    "run_authority_status": {
        "active",
        "superseded",
        "completed",
        "blocked",
        "quarantined",
        "not_applicable",
    },
    "adapter_conformance_status": {
        "compatible",
        "requires_adapter",
        "requires_migration",
        "fail_closed",
        "not_applicable",
    },
    "commit_queue_status": {
        "not_applicable",
        "intent_needed",
        "ready_to_commit",
        "needs_commit_owner",
        "orphan_or_conflicted",
        "committed",
        "blocked",
    },
    "completion_subject_type": {
        "repo_diff",
        "document_artifact",
        "research_packet",
        "plan_artifact",
        "plan_review",
        "artifact_review",
        "completion_challenge",
        "audit_packet",
        "operation_record",
        "composite_subject",
        "not_classified",
    },
    "research_cycle_status": {
        "not_applicable",
        "not_run",
        "running",
        "deny",
        "allow_unanimous",
        "stale",
        "schema_invalid",
        "blocked",
    },
    "challenge_cycle_status": {
        "not_applicable",
        "not_run",
        "running",
        "deny",
        "allow_unanimous",
        "stale",
        "schema_invalid",
    },
    "visible_output_contract": {
        "live_status",
        "challenge_result",
        "forced_boundary_continue",
        "blocked_external_gate",
        "terminal_completion",
        "not_applicable",
    },
}

REQUIRED_STOP_LANES = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}

REQUIRED_STOP_VIEWPOINTS = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}

REQUIRED_STOP_LANE_COVERAGE = {
    "architecture_dependency": {"architecture_dependency"},
    "failure_verification": {"failure_verification"},
    "goal_efficiency": {"goal_efficiency"},
    "requirement_alignment": {"requirement_alignment"},
    "implementation_quality": {"implementation_quality"},
}

FRESH_PROOF_STATUSES = {
    "fresh",
    "current_pass",
    "current_cycle",
}

SUBJECT_DIGEST_REDACTED_HANDOFF_FIELDS = {
    "challenge_cycle_digest_set",
    "challenge_cycle_ref",
    "challenge_cycle_status",
    "goal_completion_evidence",
    "stop_authorization_evidence",
    "stop_consensus_evidence",
}

MAX_TURN_END_ATTEMPT_STALENESS_SECONDS = 600
MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS = 180
MAX_USER_STOP_RECEIPT_STALENESS_SECONDS = 180

IMPLEMENTATION_INTENTS = {
    "implementation_oriented",
    "implementation_loop",
}

PLANNING_ONLY_INTENTS = {
    "planning_only",
}

SEQUENTIAL_PATTERNS = [
    r"\bfirst\b",
    r"\bthen\b",
    r"\bafter that\b",
    r"\bnext\b",
    r"먼저",
    r"일단",
    r"그 다음",
    r"다음으로",
]

PLANNING_ONLY_SOURCE_PATTERNS = [
    r"\bplanning[_ -]?only\b",
    r"\bplan only\b",
    r"\bjust plan\b",
    r"\bplanning only request\b",
    r"계획만",
    r"구현하지 말",
]

PLAN_EXECUTION_SOURCE_PATTERNS = [
    r"\bproceed with (?:this|that|the) plan\b",
    r"\bexecute (?:this|that|the) plan\b",
    r"\bimplement (?:this|that|the) plan\b",
    r"\brun (?:this|that|the) roadmap\b",
    r"\bproceed with (?:this|that|the) roadmap\b",
    r"해당\s*plan\s*진행",
    r"plan\s*진행",
    r"로드맵\s*진행",
    r"계획\s*진행",
    r"계획대로\s*진행",
]

INFERRED_AUTHORITY_PATTERNS = [
    r"bounded objective",
    r"current bounded objective",
    r"goal satisfied",
    r"request complete",
    r"subgoal complete",
    r"done for now",
]

PAUSE_CLOSURE_SCENT_PATTERNS = [
    r"완료",
    r"마무리",
    r"정리",
    r"\bcomplete\b",
    r"\bcompletion\b",
    r"\b끝\b",
    r"\bdone\b",
    r"\bcompleted\b",
    r"\bfinished\b",
    r"\bfinaliz(?:e|ed)\b",
    r"\bwrap(?:ped)? up\b",
    r"\bqueued\b",
    r"\bnext loop\b",
    r"\bpick up\b",
    r"\bawaiting\b",
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"다음 루프",
    r"재개",
    r"이어서",
    r"대기",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

WEAK_PAUSE_RESUME_PATTERNS = [
    r"완료",
    r"마무리",
    r"정리",
    r"\b끝\b",
    r"\bdone\b",
    r"\bcompleted\b",
    r"\bfinished\b",
    r"\bcomplete\b",
    r"\bcompletion\b",
    r"\bcurrent batch complete\b",
    r"\bfinaliz(?:e|ed)\b",
    r"\bqueued\b",
    r"\bnext loop\b",
    r"\bpick up\b",
    r"\bif needed\b",
    r"\bif you want\b",
    r"\bcan take\b",
    r"\bcould\b",
    r"\bawaiting\b",
    r"\bwhen you are ready\b",
    r"\bif you are ready\b",
    r"\blet me know if\b",
    r"\btell me if\b",
    r"\bif i should\b",
    r"\bok(?:ay)? to\b",
    r"\btell me whether to proceed\b",
    r"\bshall i\b",
    r"\bshould i\b",
    r"\bwant me to\b",
    r"\bdo you want me to\b",
    r"continue\?",
    r"resume\?",
    r"proceed\?",
    r"\bcontinue from here\??\b",
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"다음 루프",
    r"필요하면",
    r"원하면",
    r"대기",
    r"준비되면",
    r"말해주시면",
    r"계속할까요",
    r"진행할까요",
    r"이어갈까요",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

HOST_BOUNDARY_REASON_PATTERNS = [
    r"host",
    r"same-turn",
    r"turn boundary",
    r"visible turn boundary",
    r"host boundary",
    r"same_turn_only",
    r"호스트",
    r"턴 경계",
    r"가시적 턴",
]

HOST_BOUNDARY_FORCE_PATTERNS = [
    r"\bforced\b",
    r"\bforce\b",
    r"\bceiling\b",
    r"\bcannot continue in this visible turn\b",
    r"\bturn must end now\b",
    r"\bhost ceiling\b",
    r"강제",
    r"턴 종료",
    r"더 진행할 수 없",
    r"호스트 한계",
]

CONTEXT_BUDGET_TURN_EXIT_PATTERNS = [
    r"\bcontext budget\b",
    r"\bcontext window\b",
    r"\btoken budget\b",
    r"\bresponse budget\b",
    r"\bmessage budget\b",
    r"\bcontext limit\b",
    r"\btoken limit\b",
    r"컨텍스트",
    r"토큰",
    r"응답 길이",
    r"메시지 길이",
]

TIMEOUT_BATCH_SHRINK_TURN_EXIT_PATTERNS = [
    r"\btimeout\b",
    r"\btimed out\b",
    r"\btime limit\b",
    r"\bbatch shrink\b",
    r"\bshrink(?:ing)? the batch\b",
    r"\bsmaller batch\b",
    r"\breduced batch\b",
    r"타임아웃",
    r"시간 제한",
    r"배치 축소",
    r"배치를 줄",
]

BLOCKED_DURING_ATTEMPT_TURN_EXIT_PATTERNS = [
    r"\bblocked\b",
    r"\bblocker\b",
    r"\bfailed during attempt\b",
    r"\bpermission\b",
    r"\bauth\b",
    r"\berror\b",
    r"\bfailure\b",
    r"\brejected\b",
    r"막",
    r"차단",
    r"권한",
    r"오류",
    r"실패",
]

USER_INTERRUPT_TURN_EXIT_PATTERNS = [
    r"\buser interrupt\b",
    r"\buser interrupted\b",
    r"\binterrupted by user\b",
    r"\buser reply\b",
    r"\buser redirected\b",
    r"\bnew user message\b",
    r"사용자",
    r"인터럽트",
    r"중단",
    r"새 메시지",
    r"리다이렉트",
]

NON_HOST_PAUSE_CAUSE_PATTERNS = [
    r"\bhuman approval\b",
    r"\bawaiting approval\b",
    r"\bapproval pending\b",
    r"\bconfirmation pending\b",
    r"\bawaiting confirmation\b",
    r"\buser decision\b",
    r"\bhuman decision\b",
    r"\bexplicit user\b",
    r"\bredirect\b",
    r"\bpermission\b",
    r"승인 대기",
    r"확인 대기",
    r"결정 대기",
    r"사용자 결정",
    r"사람 판단",
    r"리다이렉트",
]

APPROVAL_OR_NO_LOCAL_ACTION_CHALLENGE_PATTERNS = [
    r"\bno bounded local actions?\b",
    r"\bno local actions?\b",
    r"\bno bounded actions?\b",
    r"\bno tool-backed actions?\b",
    r"\bno safe local actions?\b",
    r"\bonly approval[- ](?:needed|required|pending)\b",
    r"\bapproval[- ](?:needed|required|pending)\b",
    r"\bawaiting approval\b",
    r"\bhuman approval\b",
    r"\bhuman decision\b",
    r"\bmanual approval\b",
    r"\bexternal authority\b",
    r"\bexternal receipt\b",
    r"\bprovider receipt\b",
    r"\bproduction authority\b",
    r"\bcommit owner\b",
    r"\bindex owner\b",
    r"\bmanual index\b",
    r"\bblocked[- ]only\b.{0,80}\b(?:approval|human decision|external authority|manual|no bounded local actions?|no local actions?)\b",
    r"\bblocker[- ]only\b.{0,80}\b(?:approval|human decision|external authority|manual|no bounded local actions?|no local actions?)\b",
    r"승인",
    r"사람 판단",
    r"외부 권한",
    r"외부 승인",
    r"수동 승인",
    r"커밋 오너",
    r"인덱스 오너",
    r"로컬 작업.*없",
    r"더 할.*없",
    r"블로커.*남",
    r"차단.*남",
]

NO_BOUNDED_LOCAL_ACTION_PATTERNS = [
    r"\bno bounded local actions?\b",
    r"\bno local actions?\b",
    r"\bno bounded actions?\b",
    r"\bno tool-backed actions?\b",
    r"\bno safe local actions?\b",
    r"\bonly approval[- ](?:needed|required|pending)\b",
    r"\bapproval[- ]only\b",
    r"\bblocked[- ]only\b.{0,80}\b(?:approval|human decision|external authority|manual|no bounded local actions?|no local actions?)\b",
    r"\bblocker[- ]only\b.{0,80}\b(?:approval|human decision|external authority|manual|no bounded local actions?|no local actions?)\b",
    r"로컬 작업.*없",
    r"더 할.*없",
]

WEAK_CONTINUE_EXIT_PATTERNS = [
    r"\binspect(?:ed|ing)?\b",
    r"\bread(?:ing)?\b",
    r"\breview(?:ed|ing)?\b",
    r"\bscope(?:d|ing)?\b",
    r"\bverify(?:ing|ied)?\b",
    r"\bcheck(?:ed|ing)?\b",
    r"\blook(?:ed|ing)? at\b",
    r"\btriag(?:e|ing)?\b",
    r"\bsweep(?:ing)?\b",
    r"\bscan(?:ning)?\b",
    r"\bexplor(?:e|ing|ation)\b",
    r"\breassess(?:ing|ment)?\b",
    r"\binventory\b",
    r"검토",
    r"읽",
    r"확인",
    r"점검",
    r"탐색",
    r"스캔",
    r"스윕",
    r"재평가",
    r"분류",
    r"판별",
    r"후보",
]

STRONG_CONTINUE_EXIT_PATTERNS = [
    r"\bspawn(?:ed|ing)?\b",
    r"\bdispatch(?:ed|ing)?\b",
    r"\bdelegat(?:e|ed|ing|ion)\b",
    r"\battempt(?:ed|ing)?\b",
    r"\bedit(?:ed|ing)?\b",
    r"\bpatch(?:ed|ing)?\b",
    r"\bupdate(?:d|ing)?\b",
    r"\bchange(?:d|ing)?\b",
    r"\bimplement(?:ed|ing)?\b",
    r"\bran\b",
    r"\brun(?:ning)?\b",
    r"\bexecute(?:d|ing)?\b",
    r"\blaunch(?:ed|ing)?\b",
    r"\bcapture(?:d|ing)?\b",
    r"\bwrite(?:s|ing|en)?\b",
    r"\bcreate(?:d|ing)?\b",
    r"\badd(?:ed|ing)?\b",
    r"\bremove(?:d|ing)?\b",
    r"\bfix(?:ed|ing)?\b",
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\beslint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"수정",
    r"패치",
    r"적용",
    r"실행",
    r"재실행",
    r"캡처",
    r"구현",
    r"작성",
    r"변경",
    r"추가",
    r"제거",
    r"테스트",
    r"검증",
]

LOCAL_EDIT_CONTINUE_PATTERNS = [
    r"\bedit(?:ed|ing)?\b",
    r"\bpatch(?:ed|ing)?\b",
    r"\bupdate(?:d|ing)?\b",
    r"\bchange(?:d|ing)?\b",
    r"\bimplement(?:ed|ing)?\b",
    r"\bwrite(?:s|ing|en)?\b",
    r"\bcreate(?:d|ing)?\b",
    r"\badd(?:ed|ing)?\b",
    r"\bremove(?:d|ing)?\b",
    r"\bfix(?:ed|ing)?\b",
    r"수정",
    r"패치",
    r"적용",
    r"구현",
    r"작성",
    r"변경",
    r"추가",
    r"제거",
]

VALIDATION_EVIDENCE_PATTERNS = [
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\beslint\b",
    r"\blint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"\bverif(?:y|ied|ying|ication)\b",
    r"\bvalidat(?:e|ed|ing|ion)\b",
    r"\bpass(?:ed|ing)?\b",
    r"\bchecks?\b",
    r"테스트",
    r"검증",
    r"린트",
    r"빌드",
    r"타입체크",
    r"통과",
]

OPEN_ENDED_CONTINUE_PATTERNS = [
    r"\btriag(?:e|ing)?\b",
    r"\bsweep(?:ing)?\b",
    r"\bscan(?:ning)?\b",
    r"\bexplor(?:e|ing|ation)\b",
    r"\breassess(?:ing|ment)?\b",
    r"\binventory\b",
    r"\bclassif(?:y|ying|ication)\b",
    r"\btaxonomy gap\b",
    r"\bgap sweep\b",
    r"탐색",
    r"스캔",
    r"스윕",
    r"재평가",
    r"분류",
    r"taxonomy gap",
    r"route inventory",
]

CANDIDATE_HUNT_PATTERNS = [
    r"\bcandidate\b",
    r"\bfind(?:ing)?\b.*\bcandidate\b",
    r"\bchoose\b.*\bcandidate\b",
    r"\bpick\b.*\bcandidate\b",
    r"판별",
    r"후보",
    r"고른다",
    r"찾는다",
    r"추린다",
]

DELEGATED_QUOTA_BLOCKER_PATTERNS = [
    r"\bspawn_agent\b",
    r"\bdelegated[- ]agent\b",
    r"\bdelegated\b",
    r"\bagent lane\b",
    r"\blane\b",
    r"\bquota\b",
    r"\busage limits?\b",
    r"\brate limits?\b",
    r"\bcredits?\b",
    r"\btry again\b",
    r"에이전트",
    r"사용량",
    r"한도",
    r"쿼터",
    r"크레딧",
]

CONSENT_SEEKING_PATTERNS = [
    r"continue\?",
    r"resume\?",
    r"proceed\?",
    r"\bopen (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\bspawn (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\blaunch (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\bmay i (?:open|spawn|launch) (?:the )?(?:agent|agents|lane|lanes)\b",
    r"\bcontinue from here\??\b",
    r"\bshall i\b",
    r"\bshould i\b",
    r"\bwant me to\b",
    r"\bdo you want me to\b",
    r"\blet me know if\b",
    r"\btell me if\b",
    r"\bif i should\b",
    r"\bok(?:ay)? to\b",
    r"\btell me whether to proceed\b",
    r"\bif you want\b",
    r"\bwhen you are ready\b",
    r"\bif you are ready\b",
    r"\bready for me to\b",
    r"계속할까요",
    r"계속해도 될까요",
    r"계속해도 됩니까",
    r"진행할까요",
    r"진행해도 될까요",
    r"진행해도 됩니까",
    r"에이전트.*열까요",
    r"에이전트.*열어도 될까요",
    r"에이전트.*사용해도 될까요",
    r"이어갈까요",
    r"이어가도 될까요",
    r"원하시면",
    r"준비되면",
    r"말해주시면",
]

REPORT_DRIVEN_PATTERNS = [
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"\bfor reporting\b",
    r"\bfor status\b",
    r"\bfor handoff\b",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

COMPLETION_GATE_PATTERNS = [
    r"\bchallenge_review_mode=goal_completion_challenge\b",
    r"\bgoal[_ -]?completion[_ -]?challenge\b",
    r"\bgoal[_ -]?completion.{0,40}\b(?:5|five)[_ -]?(?:agent|lane|codex)",
    r"\b(?:5|five)[_ -]?(?:agent|lane|codex).{0,40}\bgoal[_ -]?completion",
    r"\bcompletion[_ -]?proof.{0,40}\b(?:5|five)[_ -]?(?:agent|lane|codex)",
    r"\b(?:5|five)[_ -]?(?:agent|lane|codex).{0,40}\bcompletion[_ -]?proof",
    r"goal_completion_evidence=.*challenge_review_mode=goal_completion_challenge",
    r"5.{0,12}(에이전트|lane|codex).{0,40}(완료|goal completion)",
    r"(완료 증명|goal completion).{0,40}5.{0,12}(에이전트|lane|codex)",
]

DELEGATION_PERMISSION_CHECKPOINT_PATTERNS = [
    r"when[_ -]delegation[_ -]authorized\b",
    r"when.{0,40}\b(?:delegated[ _-])?agents?.{0,20}\b(?:are[ _-])?authori[sz]ed\b",
    r"\bdelegat(?:e|ed|ion|ing).{0,80}\bauthori[sz](?:e|ed|ation).{0,40}\b(?:pending|required|needed|waiting)\b",
    r"\bauthori[sz](?:e|ed|ation).{0,80}\bdelegat(?:e|ed|ion|ing).{0,40}\b(?:pending|required|needed|waiting)\b",
    r"\b(?:permission|approval|consent).{0,80}\b(?:open|spawn|launch|use).{0,40}\bagents?\b",
    r"\b(?:open|spawn|launch|use).{0,40}\bagents?.{0,80}\b(?:permission|approval|consent)\b",
    r"\bask(?:ing)? .{0,80}\b(?:open|spawn|launch|use).{0,40}\bagents?\b",
    r"\bagents?[_ -](?:permission|approval|consent)[_ -]pending\b",
    r"에이전트.{0,40}(허가|승인|권한).{0,20}(대기|필요)",
    r"(허가|승인|권한).{0,40}에이전트.{0,20}(대기|필요)",
    r"(위임|delegation).{0,40}(허가|승인|권한).{0,20}(대기|필요)",
]


def clean_value(value: str) -> str:
    return value.strip().strip("`").strip()


def is_noneish(value: object) -> bool:
    if isinstance(value, list):
        if not value:
            return True
        return len(value) == 1 and is_noneish(value[0])
    if value is None:
        return True
    text = clean_value(str(value)).lower()
    if not text:
        return True
    return (
        text == "none"
        or text == "n/a"
        or text == "na"
        or text.startswith("none ")
        or text.startswith("none-")
        or text.startswith("none -")
    )


def flatten_multivalue_text(value: object) -> str:
    if isinstance(value, list):
        return " | ".join(clean_value(str(item)) for item in value if clean_value(str(item)))
    return clean_value(str(value))


def iter_flattened_text_values(value: object) -> list[str]:
    if isinstance(value, list):
        return [flatten_multivalue_text(item) for item in value if flatten_multivalue_text(item)]
    return [flatten_multivalue_text(value)] if flatten_multivalue_text(value) else []


def contains_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def structured_values(text: str, key: str) -> list[str]:
    return [
        clean_value(match.group(1))
        for match in re.finditer(rf"(?:^|[\s;,`]){re.escape(key)}=([^\s;,\n]+)", text, flags=re.IGNORECASE)
    ]


def extract_structured_value(text: str, key: str) -> str | None:
    values = structured_values(text, key)
    if len(values) != 1:
        return None
    return values[0]


def extract_inline_token_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?:^|[\s;,]){re.escape(key)}=([^\s;,\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return clean_value(match.group(1))


def extract_pipe_value_set(text: str | None) -> set[str]:
    if text is None:
        return set()
    return {clean_value(part).lower() for part in text.split("|") if clean_value(part)}


def pipe_value_set_is_exact(text: str | None, expected: set[str]) -> bool:
    if text is None:
        return False
    values = [clean_value(part).lower() for part in text.split("|") if clean_value(part)]
    return len(values) == len(expected) and len(set(values)) == len(values) and set(values) == expected


def extract_coverage_viewpoint_set(text: str) -> set[str]:
    return extract_pipe_value_set(
        extract_artifact_field(text, "coverage_viewpoints")
        or extract_artifact_field(text, "covered_viewpoints")
    )


def artifact_pipe_field_is_exact(text: str, key: str, expected: set[str]) -> bool:
    return pipe_value_set_is_exact(extract_artifact_field(text, key), expected)


def normalize_artifact_value(value: str) -> str:
    normalized = clean_value(value)
    # Template values are often rendered as `<...>` inside backticks. Strip
    # one extra code fence layer after markdown key/value parsing.
    return clean_value(normalized)


def is_fast_path_authorized(evidence: object, run_dir: Path, risk_tier: str) -> bool:
    if risk_tier not in {"tier0_trivial", "tier1_local"}:
        return False
    text = clean_value(str(evidence))
    guarded_tokens = (
        "fast_path_reason",
        "minimal_plan_ref",
        "requirement_trace_ref",
        "local_verification",
        "verification_ref",
        "scoped_files",
        "external_api",
        "db_or_migration",
        "security_sensitive",
        "reversible",
        "verification_result",
    )
    if any(not inline_token_is_unique(text, key) for key in guarded_tokens):
        return False
    allowed_reasons = {"single_file_local_fix", "user_specified_exact_change", "no_behavior_change"}
    reason = clean_value(extract_inline_token_value(text, "fast_path_reason") or "").lower()
    if reason not in allowed_reasons:
        return False
    required_tokens = [
        "minimal_plan_ref",
        "requirement_trace_ref",
        "local_verification",
        "verification_ref",
        "scoped_files",
    ]
    if any(is_noneish(extract_inline_token_value(text, key) or "") for key in required_tokens):
        return False
    for key in ("external_api", "db_or_migration", "security_sensitive"):
        if clean_value(extract_inline_token_value(text, key) or "").lower() != "false":
            return False
    if clean_value(extract_inline_token_value(text, "reversible") or "").lower() != "true":
        return False
    if clean_value(extract_inline_token_value(text, "verification_result") or "").lower() not in {"pass", "passed"}:
        return False
    minimal_plan_ref = extract_inline_token_value(text, "minimal_plan_ref")
    trace_ref = extract_inline_token_value(text, "requirement_trace_ref")
    verification_ref = extract_inline_token_value(text, "verification_ref")
    return (
        resolve_artifact_ref(minimal_plan_ref, run_dir) is not None
        and resolve_artifact_ref(trace_ref, run_dir) is not None
        and resolve_artifact_ref(verification_ref, run_dir) is not None
    )


def is_tier1_self_check_authorized(evidence: object, run_dir: Path, risk_tier: str) -> bool:
    if risk_tier != "tier1_local":
        return False
    text = clean_value(str(evidence))
    guarded_tokens = (
        "tier1_self_check",
        "risk_expanded",
        "implementation_summary_ref",
        "verification_plan_ref",
        "requirement_trace_ref",
        "verification_ref",
        "local_verification",
        "scope_evidence",
        "scoped_files",
        "external_api",
        "db_or_migration",
        "security_sensitive",
        "shared_boundary",
        "verification_result",
    )
    if any(not inline_token_is_unique(text, key) for key in guarded_tokens):
        return False
    if clean_value(extract_inline_token_value(text, "tier1_self_check") or "").lower() not in {"pass", "passed"}:
        return False
    if clean_value(extract_inline_token_value(text, "risk_expanded") or "").lower() != "false":
        return False
    required_tokens = [
        "implementation_summary_ref",
        "verification_plan_ref",
        "requirement_trace_ref",
        "verification_ref",
        "local_verification",
        "scope_evidence",
        "scoped_files",
    ]
    if any(is_noneish(extract_inline_token_value(text, key) or "") for key in required_tokens):
        return False
    for key in ("external_api", "db_or_migration", "security_sensitive", "shared_boundary"):
        if clean_value(extract_inline_token_value(text, key) or "").lower() != "false":
            return False
    if clean_value(extract_inline_token_value(text, "verification_result") or "").lower() not in {"pass", "passed"}:
        return False
    for key in ("implementation_summary_ref", "verification_plan_ref", "requirement_trace_ref", "verification_ref"):
        if resolve_artifact_ref(extract_inline_token_value(text, key), run_dir) is None:
            return False
    return True


def is_research_skip_authorized(evidence: object, run_dir: Path, risk_tier: str) -> bool:
    return is_fast_path_authorized(evidence, run_dir, risk_tier) or is_tier1_self_check_authorized(
        evidence,
        run_dir,
        risk_tier,
    )


def parse_markdown_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    duplicates: list[str] = []
    malformed: list[str] = []
    pattern = r"^\s*-\s+`([A-Za-z0-9_-]+)`\s*:\s*(.+?)\s*$"
    loose_key_value = r"^\s*(?:-\s*)?`?[A-Za-z0-9_-]+`?\s*[:=]\s*.+$"

    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.match(pattern, line)
        if not match:
            loose_match = re.match(loose_key_value, line)
            if loose_match:
                loose_key = clean_value(loose_match.group(0).split("=", 1)[0].split(":", 1)[0]).strip("- ").strip("`").lower()
                if loose_key in IDEAS_KNOWN_FIELDS:
                    malformed.append(str(line_no))
            continue
        key = clean_value(match.group(1)).lower()
        value = normalize_artifact_value(match.group(2))
        if key in fields and key not in duplicates:
            duplicates.append(key)
        fields[key] = value

    if duplicates:
        fields["_duplicate_keys"] = ",".join(sorted(duplicates))
    if malformed:
        fields["_malformed_key_value_lines"] = ",".join(malformed)
    return fields


def parse_ideas_artifact(path: Path) -> tuple[dict[str, str], list[dict[str, str]], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = list(re.finditer(r"^###\s+(IDEA-[A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE))
    first_block_start = matches[0].start() if matches else len(text)
    gate = parse_markdown_key_values(text[:first_block_start])
    candidates: list[dict[str, str]] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        fields = parse_markdown_key_values(block)
        heading_id = clean_value(match.group(1))
        fields.setdefault("idea_id", heading_id)
        fields["_heading_id"] = heading_id
        candidates.append(fields)

    return gate, candidates, text


def valid_positive_int_token(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9][0-9]*", clean_value(value)))


def cap_has_required_numeric_limits(cap: str) -> bool:
    maxima = {
        "timebox_minutes": 5,
        "candidate_limit": 5,
        "external_source_limit": 3,
    }
    for key, maximum in maxima.items():
        value = clean_value(extract_inline_token_value(cap, key) or "")
        if not valid_positive_int_token(value):
            return False
        if int(value) > maximum:
            return False
    return True


def markdown_anchor_slug(text: str) -> str:
    slug = clean_value(text).strip().strip("#").strip().lower()
    slug = slug.replace("`", "")
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def markdown_heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = markdown_anchor_slug(match.group(1))
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def artifact_markdown_ref_resolves(ref: str, run_dir: Path, expected_file: str) -> bool:
    normalized = clean_value(ref)
    if is_placeholder_reference(normalized):
        return False
    if not normalized.lower().startswith(f"{expected_file.lower()}#"):
        return False
    anchor = markdown_anchor_slug(unquote(normalized.split("#", 1)[1]))
    if not anchor:
        return False
    path = run_dir / expected_file
    return path.exists() and path.is_file() and anchor in markdown_heading_anchors(path)


def idea_decision_refs_resolve(candidate: dict[str, str], run_dir: Path) -> bool:
    research_ref = clean_value(candidate.get("research_ref", ""))
    evidence_ref = clean_value(candidate.get("evidence_ref", ""))
    if not artifact_markdown_ref_resolves(research_ref, run_dir, "research.md"):
        return False
    if artifact_markdown_ref_resolves(evidence_ref, run_dir, "evidence.md"):
        return True
    evidence_path = resolve_run_scoped_ref(evidence_ref, run_dir)
    if evidence_path is None:
        return False
    try:
        relative = evidence_path.resolve().relative_to(run_dir.resolve()).as_posix().lower()
    except ValueError:
        return False
    return relative.startswith(
        (
            "evidence/",
            "receipts/",
            "authority/",
            "closeout-receipts/",
            "status-receipts/",
        )
    )


def validate_ideas_artifact(path: Path, *, allow_in_progress_ideation: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.exists() or not path.is_file():
        return ["implementation-oriented runs require ideas.md before continue/pause/stop validation"]

    run_dir = path.parent
    gate, candidates, text = parse_ideas_artifact(path)
    lower_text = text.lower()

    if gate.get("_malformed_key_value_lines"):
        errors.append("ideas.md Ideation Gate must use canonical `- `field`: `value`` lines")
    if gate.get("_duplicate_keys"):
        errors.append(f"ideas.md Ideation Gate has duplicate field(s): {gate['_duplicate_keys']}")

    ideation_status = clean_value(gate.get("ideation_status", "")).lower()
    viewpoint_count = clean_value(gate.get("viewpoint_count", "")).lower()
    legacy_lane_count = clean_value(gate.get("lane_count", "")).lower()
    if viewpoint_count and legacy_lane_count and viewpoint_count != legacy_lane_count:
        errors.append("ideas.md viewpoint_count and legacy lane_count must match when both are present")
    if not viewpoint_count and legacy_lane_count:
        viewpoint_count = legacy_lane_count
    cap = clean_value(gate.get("cap", ""))
    skip_or_reopen_reason = clean_value(gate.get("skip_or_reopen_reason", "")).lower()

    if ideation_status not in IDEATION_STATUSES:
        errors.append("ideas.md requires ideation_status=completed|not_material|reopened")
    if viewpoint_count not in IDEATION_LANE_COUNTS:
        errors.append("ideas.md requires viewpoint_count=0|3|5")
    if not cap_has_required_numeric_limits(cap):
        errors.append(
            "ideas.md cap must include positive bounded timebox_minutes<=5, candidate_limit<=5, and external_source_limit<=3"
        )
    if skip_or_reopen_reason not in IDEATION_SKIP_OR_REOPEN_REASONS:
        errors.append(
            "ideas.md requires skip_or_reopen_reason=ideation_not_material|remaining_gap|new_constraint|higher_leverage_candidate|high_impact_ambiguous|none"
        )

    if viewpoint_count == "0":
        if ideation_status != "not_material" or skip_or_reopen_reason != "ideation_not_material":
            errors.append("ideas.md viewpoint_count=0 requires ideation_status=not_material and skip_or_reopen_reason=ideation_not_material")
        has_explicit_not_material_rationale = any(
            "ideation_not_material" in line.lower()
            and not re.match(r"^\s*-\s*`?skip_or_reopen_reason`?\s*:", line, flags=re.IGNORECASE)
            for line in text.splitlines()
        )
        if not has_explicit_not_material_rationale:
            errors.append("ideas.md viewpoint_count=0 requires an explicit ideation_not_material rationale")
    elif ideation_status == "not_material":
        errors.append("ideas.md ideation_status=not_material requires viewpoint_count=0")

    if viewpoint_count == "5" and skip_or_reopen_reason != "high_impact_ambiguous":
        errors.append("ideas.md viewpoint_count=5 requires skip_or_reopen_reason=high_impact_ambiguous")

    if viewpoint_count in {"3", "5"} and not candidates and not allow_in_progress_ideation:
        errors.append("ideas.md material ideation requires at least one parsed ### IDEA-* candidate")

    seen_ids: set[str] = set()
    for candidate in candidates:
        idea_id = clean_value(candidate.get("idea_id", ""))
        heading_id = clean_value(candidate.get("_heading_id", ""))
        if candidate.get("_malformed_key_value_lines"):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} must use canonical `- `field`: `value`` lines")
        if candidate.get("_duplicate_keys"):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} has duplicate field(s): {candidate['_duplicate_keys']}")
        if idea_id and heading_id and idea_id != heading_id:
            errors.append(f"ideas.md candidate heading {heading_id} must match idea_id {idea_id}")
        if not re.fullmatch(r"IDEA-[A-Za-z0-9_-]+", idea_id):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} requires a stable idea_id like IDEA-001")
        if idea_id in seen_ids:
            errors.append(f"ideas.md duplicate idea_id: {idea_id}")
        if idea_id:
            seen_ids.add(idea_id)

        for field in sorted(IDEA_REQUIRED_FIELDS):
            if field in IDEA_REQUIRED_BUT_NONE_ALLOWED_FIELDS:
                if field not in candidate or not clean_value(candidate.get(field, "")):
                    errors.append(f"ideas.md candidate {idea_id or heading_id} requires {field}")
                continue
            if is_placeholder_reference(candidate.get(field)):
                errors.append(f"ideas.md candidate {idea_id or heading_id} requires non-placeholder {field}")

        source_type = clean_value(candidate.get("source_type", "")).lower()
        source_quality = clean_value(candidate.get("source_quality", "")).lower()
        validation_required = clean_value(candidate.get("validation_required", "")).lower()
        currency_risk = clean_value(candidate.get("currency_risk", "")).lower()
        blocking = clean_value(candidate.get("blocking", "")).lower()
        memory_only = clean_value(candidate.get("memory_only", "")).lower()
        pending_reason = clean_value(candidate.get("pending_reason", "")).lower()
        last_reviewed_stage = clean_value(candidate.get("last_reviewed_stage", "")).lower()
        status = clean_value(candidate.get("research_status", "")).lower()

        if source_type and source_type not in IDEA_SOURCE_TYPES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid source_type={source_type}")
        if source_quality and source_quality not in IDEA_SOURCE_QUALITIES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid source_quality={source_quality}")
        if validation_required and validation_required not in IDEA_VALIDATION_REQUIREMENTS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid validation_required={validation_required}")
        if currency_risk and currency_risk not in IDEA_CURRENCY_RISKS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid currency_risk={currency_risk}")
        if blocking and blocking not in {"true", "false"}:
            errors.append(f"ideas.md candidate {idea_id or heading_id} requires blocking=true|false")
        if memory_only and memory_only not in {"true", "false"}:
            errors.append(f"ideas.md candidate {idea_id or heading_id} requires memory_only=true|false")
        if pending_reason and pending_reason not in IDEA_PENDING_REASONS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid pending_reason={pending_reason}")
        if last_reviewed_stage and last_reviewed_stage not in IDEA_REVIEW_STAGES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid last_reviewed_stage={last_reviewed_stage}")
        if status and status not in IDEA_STATUSES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid research_status={status}")

        if status == "pending" and pending_reason in {"", "none"}:
            errors.append(f"ideas.md pending candidate {idea_id or heading_id} requires pending_reason other than none")
        if status == "pending" and blocking == "true" and not allow_in_progress_ideation:
            errors.append("ideas.md may not carry research_status=pending with blocking=true at continue/pause/stop validation")
        if status == "stale" and blocking == "true" and not allow_in_progress_ideation:
            errors.append("ideas.md may not carry research_status=stale with blocking=true at continue/pause/stop validation")

        if status in {"validated", "rejected", "stale"}:
            for field in ("research_ref", "evidence_ref", "decision_date", "decision_summary"):
                if is_placeholder_reference(candidate.get(field)):
                    errors.append(f"ideas.md {status} candidate {idea_id or heading_id} requires non-placeholder {field}")
            decision_date = clean_value(candidate.get("decision_date", ""))
            if decision_date and not is_placeholder_reference(decision_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", decision_date):
                errors.append(f"ideas.md {status} candidate {idea_id or heading_id} requires decision_date=YYYY-MM-DD")
            if not idea_decision_refs_resolve(candidate, run_dir):
                errors.append(
                    f"ideas.md {status} candidate {idea_id or heading_id} requires research_ref=research.md#... "
                    "and evidence_ref=evidence.md#... or an existing in-run artifact"
                )

    # Catch copied templates that include field names but no concrete gate or candidate.
    if not candidates and viewpoint_count != "0" and ("idea_id" in lower_text or "research_status" in lower_text):
        errors.append("ideas.md appears to contain a copied template without concrete ### IDEA-* candidates")

    return errors


def validated_idea_ids(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    _, candidates, _ = parse_ideas_artifact(path)
    run_dir = path.parent
    return {
        clean_value(candidate.get("idea_id", ""))
        for candidate in candidates
        if clean_value(candidate.get("research_status", "")).lower() == "validated"
        and idea_decision_refs_resolve(candidate, run_dir)
    }


def idea_refs_in_plan(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    refs: set[str] = set()
    for match in re.finditer(
        r"`?(?:idea_ref|idea_id)`?\s*[:=]\s*`?(IDEA-[A-Za-z0-9_-]+)`?",
        text,
        flags=re.IGNORECASE,
    ):
        refs.add(clean_value(match.group(1)))
    return refs


def authority_snapshot_paths(run_dir: Path) -> list[Path]:
    names = ["source.md", REQUIRED_IDEAS_REF, "research.md", "revised-plan.md", "evidence.md", "handoff.md"]
    return [path for path in (run_dir / name for name in names) if path.exists() and path.is_file()]


def authority_snapshot_bytes(path: Path) -> bytes:
    if path.name != "handoff.md":
        return path.read_bytes()

    # Proof fields carry subject_digest and refs, so including them in the
    # subject digest creates an impossible self-reference. Bind proof to the
    # live authority state by hashing handoff minus proof-evidence payloads.
    lines: list[str] = []
    redacting_field: str | None = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.lstrip()
        is_top_level_bullet = line.startswith("- ")
        if redacting_field and not is_top_level_bullet:
            if line.startswith((" ", "\t")):
                continue
            redacting_field = None
        redacting_field = None
        for field in SUBJECT_DIGEST_REDACTED_HANDOFF_FIELDS:
            if stripped.startswith(f"- `{field}`:"):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}- `{field}`: <redacted-for-subject-digest>")
                redacting_field = field
                break
        else:
            lines.append(line)
    return ("\n".join(lines) + "\n").encode("utf-8")


def compute_subject_digest(run_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in authority_snapshot_paths(run_dir):
        relative = path.relative_to(run_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(authority_snapshot_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def compute_source_digest(run_dir: Path) -> str:
    source_path = run_dir / REQUIRED_SOURCE_REF
    if not source_path.exists() or not source_path.is_file():
        return ""
    return hashlib.sha256(source_path.read_bytes()).hexdigest()


def latest_authority_mtime(run_dir: Path) -> float:
    paths = [path for path in authority_snapshot_paths(run_dir) if path.name != "handoff.md"]
    if not paths:
        return 0.0
    return max(path.stat().st_mtime for path in paths)


def is_placeholder_reference(value: str | None) -> bool:
    if value is None:
        return True
    normalized = clean_value(value)
    if is_noneish(normalized):
        return True
    lower = normalized.lower()
    if lower in {"<...>", "<ref>", "<value>", "tbd", "todo"}:
        return True
    return bool(re.fullmatch(r"<[^>]+>", normalized))


def authority_ref_is_resolved(value: str | None, run_dir: Path) -> bool:
    return resolve_run_scoped_ref(value, run_dir) is not None


def authority_receipt_is_valid(path: Path, expected_kind: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "authority_receipt_version").lower() != "v1":
        return False
    if extract_artifact_field(text, "authority_kind").lower() != expected_kind.lower():
        return False
    if not (
        extract_artifact_field(text, "message_id")
        or extract_artifact_field(text, "event_id")
        or extract_artifact_field(text, "source_ref")
        or extract_artifact_field(text, "excerpt")
    ):
        return False
    return True


HOST_BOUNDARY_EVENT_ID_SOURCES = {
    "controller_generated_same_turn_boundary",
    "provided_event_id",
    "host_event_id",
}


def normalize_ref_token(value: str | None) -> str:
    if value is None:
        return ""
    text = clean_value(value)
    if not text:
        return ""
    return Path(text).as_posix()


def artifact_is_fresh_for_closeout(path: Path, handoff_path: Path, max_gap_seconds: int) -> bool:
    if not path.exists() or not handoff_path.exists():
        return False
    gap_seconds = abs(handoff_path.stat().st_mtime - path.stat().st_mtime)
    return gap_seconds <= max_gap_seconds


def host_boundary_receipt_is_valid(path: Path, closeout_round_id: str, attempt_ref: str) -> bool:
    if not authority_receipt_is_valid(path, "host_turn_boundary"):
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if is_placeholder_reference(extract_artifact_field(text, "event_id")):
        return False
    event_id_source = extract_artifact_field(text, "event_id_source").lower()
    if event_id_source not in HOST_BOUNDARY_EVENT_ID_SOURCES:
        return False
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False

    receipt_attempt_ref = normalize_ref_token(extract_artifact_field(text, "attempt_ref"))
    if not receipt_attempt_ref:
        return False

    return receipt_attempt_ref == normalize_ref_token(attempt_ref)


def user_stop_receipt_is_valid(path: Path, closeout_round_id: str) -> bool:
    if not authority_receipt_is_valid(path, "explicit_user_stop"):
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False
    if extract_artifact_field(text, "source_ref").lower() != "current_user_message":
        return False
    if not extract_artifact_field(text, "excerpt"):
        return False
    return True


def resolve_run_scoped_ref(value: str | None, run_dir: Path) -> Path | None:
    if value is None or is_placeholder_reference(value):
        return None
    ref_path = Path(clean_value(value))
    if not ref_path.is_absolute():
        ref_path = (run_dir / ref_path).resolve()
    else:
        ref_path = ref_path.resolve()
    try:
        ref_path.relative_to(run_dir.resolve())
    except ValueError:
        return None
    if not ref_path.exists() or not ref_path.is_file():
        return None
    return ref_path


def has_actionable_resume_instructions(value: object) -> bool:
    flattened = flatten_multivalue_text(value)
    if is_noneish(flattened):
        return False
    if "?" in flattened or contains_any_pattern(flattened, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
        return False

    action_patterns = [
        r"\bopen\b",
        r"\bread\b",
        r"\brun\b",
        r"\brerun\b",
        r"\binspect\b",
        r"\breview\b",
        r"\bverify\b",
        r"\bfocus\b",
        r"열",
        r"읽",
        r"실행",
        r"재실행",
        r"확인",
        r"검토",
    ]
    has_action = contains_any_pattern(flattened, action_patterns)
    has_anchor = any(
        marker in flattened.lower()
        for marker in ("run directory", "/", ".md", ".py", ".json", ".png", ".txt", "next_mandatory_action")
    )
    has_multiple_steps = isinstance(value, list) and len([item for item in value if clean_value(str(item))]) >= 2
    return has_action and (has_anchor or has_multiple_steps)


def extract_anchor_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9_-]{4,}|[가-힣]{2,}", text.lower())
    stopwords = {
        "this",
        "that",
        "with",
        "from",
        "into",
        "after",
        "before",
        "while",
        "current",
        "next",
        "action",
        "focus",
        "open",
        "read",
        "run",
        "rerun",
        "inspect",
        "review",
        "verify",
        "directory",
        "handoff",
        "research",
        "evidence",
        "continue",
        "resume",
        "loop",
        "work",
        "again",
        "then",
        "the",
        "and",
        "for",
        "none",
        "readme",
        "openai",
        "current_or_next_stage",
        "next_mandatory_action",
    }
    return {token for token in tokens if token not in stopwords}


def has_anchor_overlap(left: object, right: object) -> bool:
    left_tokens = extract_anchor_tokens(clean_value(str(left)))
    right_tokens = extract_anchor_tokens(clean_value(str(right)))
    if not left_tokens or not right_tokens:
        return False
    return bool(left_tokens & right_tokens)


def parse_handoff(path: Path) -> dict[str, object]:
    fields: dict[str, object] = {}
    current_key: str | None = None
    nested: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^- `([^`]+)`: ?(.*)$", line)
        if match:
            if current_key is not None:
                fields[current_key] = nested[:] if nested else ""
            current_key = match.group(1)
            remainder = match.group(2).strip()
            nested = []
            if remainder:
                fields[current_key] = clean_value(remainder)
                current_key = None
            continue
        if current_key is not None:
            nested_match = re.match(r"^\s+-\s+(.*)$", line)
            if nested_match:
                nested.append(clean_value(nested_match.group(1)))
                continue
            if line.strip():
                fields[current_key] = nested[:] if nested else clean_value(line)
                current_key = None
                nested = []

    if current_key is not None:
        fields[current_key] = nested[:] if nested else ""

    return fields


def inspect_canonical_handoff(path: Path) -> tuple[list[str], list[str]]:
    duplicates: list[str] = []
    unknown_fields: list[str] = []
    seen: set[str] = set()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- `([^`]+)`: ?(.*)$", raw_line.rstrip())
        if not match:
            continue
        key = clean_value(match.group(1))
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
        if key not in CANONICAL_FIELD_NAMES and key not in unknown_fields:
            unknown_fields.append(key)

    return duplicates, unknown_fields


def has_flat_legacy_lines(path: Path) -> bool:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("- "):
            continue
        if re.match(r"^[a-z_]+:\s", line):
            return True
    return False


def extract_plan_remaining(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    inside = False
    collected: list[str] = []
    for line in lines:
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if heading:
            if inside:
                break
            title = clean_value(heading.group(1)).rstrip(":")
            inside = title in {"Remaining Required Stages", "Remaining Stage Queue"}
            continue
        if inside:
            bullet = re.match(r"^\s*-\s+(.*)$", line)
            if bullet:
                collected.append(clean_value(bullet.group(1)))
            elif line.strip():
                collected.append(clean_value(line))
    return collected if inside else None


def source_has_sequential_markers(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return any(re.search(pattern, text) for pattern in SEQUENTIAL_PATTERNS)


def source_explicit_planning_only(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return any(re.search(pattern, text) for pattern in PLANNING_ONLY_SOURCE_PATTERNS)


def source_requests_plan_execution(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return any(re.search(pattern, text) for pattern in PLAN_EXECUTION_SOURCE_PATTERNS)


def is_inspection_only_continue_exit(status: str, evidence: object) -> bool:
    if clean_value(status) != "next_action_started":
        return False

    text = clean_value(str(evidence))
    if not text:
        return False
    if has_conflicting_inline_tokens(text, CRITICAL_FINAL_INLINE_FIELDS):
        return False

    weak_hit = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in WEAK_CONTINUE_EXIT_PATTERNS)
    strong_hit = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in STRONG_CONTINUE_EXIT_PATTERNS)
    return weak_hit and not strong_hit


def is_open_ended_candidate_hunt(value: object) -> bool:
    text = clean_value(str(value))
    if not text:
        return False

    candidate_hunt_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in CANDIDATE_HUNT_PATTERNS
    )
    if candidate_hunt_hit:
        return True

    open_ended_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in OPEN_ENDED_CONTINUE_PATTERNS
    )
    if not open_ended_hit:
        return False

    closeout_ready_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in STRONG_CONTINUE_EXIT_PATTERNS
    )
    return not closeout_ready_hit


def has_unverified_local_edit_signal(value: object) -> bool:
    text = clean_value(str(value))
    if not text:
        return False

    local_edit_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in LOCAL_EDIT_CONTINUE_PATTERNS
    )
    if not local_edit_hit:
        return False

    validation_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in VALIDATION_EVIDENCE_PATTERNS
    )
    return not validation_hit


def turn_exit_evidence_matches_cause(cause: str, evidence: object) -> bool:
    text = clean_value(str(evidence))
    if not text:
        return False

    if cause == "host_turn_boundary_pause":
        return contains_any_pattern(text, HOST_BOUNDARY_REASON_PATTERNS) and contains_any_pattern(
            text, HOST_BOUNDARY_FORCE_PATTERNS
        )

    patterns_by_cause = {
        "context_budget_exhausted": CONTEXT_BUDGET_TURN_EXIT_PATTERNS,
        "tool_timeout_after_batch_shrink": TIMEOUT_BATCH_SHRINK_TURN_EXIT_PATTERNS,
        "blocked_during_attempt": BLOCKED_DURING_ATTEMPT_TURN_EXIT_PATTERNS,
        "user_interrupt": USER_INTERRUPT_TURN_EXIT_PATTERNS,
    }
    patterns = patterns_by_cause.get(cause)
    if patterns is None:
        return False
    return contains_any_pattern(text, patterns)


def is_delegated_quota_blocker(*values: object) -> bool:
    for value in values:
        for item in iter_flattened_text_values(value):
            if has_delegated_quota_blocker_signal(item.lower()):
                return True
    return False


def has_delegated_quota_blocker_signal(value: str) -> bool:
    has_ui_copy_context = contains_any_pattern(value, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS)
    segment_records = split_scheduling_signal_segment_records(value)
    segments = [segment for segment, _separator in segment_records]
    suppressed_segment_indexes = doc_or_copy_prefixed_segment_indexes(segment_records)
    actor_patterns = [
        r"\bspawn_agent\b",
        r"\bdelegated[- ]agent\b",
        r"\bdelegated\b",
        r"\bdispatch\b",
        r"\bchallenge\b",
        r"\bagent lane\b",
        r"\blane\b",
        r"\bagent\b",
        r"에이전트",
    ]
    quota_patterns = [
        r"\bquota\b",
        r"\busage limits?\b",
        r"\brate limits?\b",
        r"\bcredits?\b",
        r"사용량",
        r"한도",
        r"쿼터",
        r"크레딧",
    ]
    for index, segment in enumerate(segments):
        if index in suppressed_segment_indexes:
            continue
        if not contains_any_pattern(segment, actor_patterns):
            continue
        if not contains_any_pattern(segment, quota_patterns):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_NON_SCHEDULING_CONTEXT_PATTERNS):
            continue
        if has_ui_copy_context and contains_any_pattern(segment, RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_REAL_SCHEDULING_NEGATED_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_NEGATED_PATTERNS):
            continue
        return True
    return has_adjacent_delegated_quota_blocker_signal(
        segments,
        actor_patterns=actor_patterns,
        quota_patterns=quota_patterns,
        has_ui_copy_context=has_ui_copy_context,
        suppressed_segment_indexes=suppressed_segment_indexes,
    )


def has_adjacent_delegated_quota_blocker_signal(
    segments: list[str],
    *,
    actor_patterns: list[str],
    quota_patterns: list[str],
    has_ui_copy_context: bool,
    suppressed_segment_indexes: set[int] | None = None,
) -> bool:
    suppressed_segment_indexes = suppressed_segment_indexes or set()
    for index in range(len(segments) - 1):
        if index in suppressed_segment_indexes or index + 1 in suppressed_segment_indexes:
            continue
        current = segments[index]
        following = segments[index + 1]
        combined = f"{current} {following}"
        if contains_any_pattern(current, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS):
            continue
        if contains_any_pattern(following, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS):
            continue
        if contains_any_pattern(combined, RESOURCE_TELEMETRY_NON_SCHEDULING_CONTEXT_PATTERNS):
            continue
        if contains_any_pattern(combined, RESOURCE_TELEMETRY_REAL_SCHEDULING_NEGATED_PATTERNS):
            continue
        if contains_any_pattern(combined, RESOURCE_TELEMETRY_NEGATED_PATTERNS):
            continue
        if has_ui_copy_context and contains_any_pattern(current, RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS):
            continue
        if has_ui_copy_context and contains_any_pattern(following, RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS):
            continue
        has_actor_then_failure = contains_any_pattern(current, actor_patterns) and contains_any_pattern(
            current,
            [r"\bfailed\b", r"\bblocked\b", r"\bdeferred\b", r"\bstopped\b", r"\bpaused\b", r"\b차단\b", r"\b실패\b"],
        )
        has_quota_condition = contains_any_pattern(following, quota_patterns) and contains_any_pattern(
            following,
            [
                r"\b(?:reached|hit|exceeded|exhausted)\b",
                r"\bblocked\b",
                r"\bquota\s+blocked\b",
                r"\b사용량\b",
                r"\b한도\b",
                r"\b차단\b",
            ],
        )
        if has_actor_then_failure and has_quota_condition:
            return True
        has_quota_condition_first = contains_any_pattern(current, quota_patterns) and contains_any_pattern(
            current,
            [
                r"\b(?:reached|hit|exceeded|exhausted)\b",
                r"\bblocked\b",
                r"\bquota\s+blocked\b",
                r"\b사용량\b",
                r"\b한도\b",
                r"\b차단\b",
            ],
        )
        has_actor_failure_after = contains_any_pattern(following, actor_patterns) and contains_any_pattern(
            following,
            [r"\bfailed\b", r"\bblocked\b", r"\bdeferred\b", r"\bstopped\b", r"\bpaused\b", r"\b차단\b", r"\b실패\b"],
        )
        if has_quota_condition_first and has_actor_failure_after:
            return True
    return False


def split_scheduling_signal_segments(value: str) -> list[str]:
    return [segment for segment, _separator in split_scheduling_signal_segment_records(value)]


def split_scheduling_signal_segment_records(value: str) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for major in re.split(r"[.;|\n]+", value):
        major = clean_value(major.lower())
        if not major:
            continue
        position = 0
        for match in re.finditer(r"\s*(,|:|=|\s+-\s+|\bbut\b|\bhowever\b|\bthen\b|\band\b)\s*", major):
            segment = clean_value(major[position : match.start()])
            if segment:
                segments.append((segment, clean_value(match.group(1))))
            position = match.end()
        segment = clean_value(major[position:])
        if segment:
            segments.append((segment, ""))
    return segments


def doc_or_copy_prefixed_segment_indexes(segment_records: list[tuple[str, str]]) -> set[int]:
    suppressed: set[int] = set()
    for index, (segment, separator) in enumerate(segment_records):
        if separator in {":", "=", "-"} and contains_any_pattern(
            segment,
            RESOURCE_TELEMETRY_DOC_OR_COPY_PREFIX_SEGMENT_PATTERNS,
        ):
            suppressed.add(index)
            if index + 1 < len(segment_records):
                suppressed.add(index + 1)
    return suppressed


def extract_consensus_refs(evidence: object) -> list[str]:
    text = clean_value(str(evidence))
    match = re.search(r"(?:^|[\s;,])refs=([^\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return []
    raw_refs = match.group(1).strip()
    return [clean_value(part) for part in re.split(r"[|,]", raw_refs) if clean_value(part)]


def extract_artifact_field(text: str, key: str) -> str:
    patterns = [
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*=\s*(.+)$",
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*:\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return clean_value(match.group(1))
    return ""


def extract_artifact_field_values(text: str, key: str) -> list[str]:
    patterns = [
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*=\s*(.+)$",
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*:\s*(.+)$",
    ]
    values: list[str] = []
    for pattern in patterns:
        values.extend(
            clean_value(match.group(1))
            for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        )
    return values


def artifact_alias_values(text: str, keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        values.extend(value for value in extract_artifact_field_values(text, key) if not is_noneish(value))
    return values


def artifact_alias_values_are_allowed(text: str, keys: tuple[str, ...], allowed: set[str]) -> bool:
    values = [value.lower() for value in artifact_alias_values(text, keys)]
    if not values or not all(value in allowed for value in values):
        return False
    equivalence = {
        "allow": "positive",
        "pass": "positive",
        "approve": "positive",
        "approved": "positive",
        "merged": "positive",
        "deny": "negative",
        "fail": "negative",
        "failed": "negative",
        "reject": "negative",
        "rejected": "negative",
        "block": "negative",
        "blocked": "negative",
        "ambiguous": "ambiguous",
        "unclear": "ambiguous",
    }
    classes = {equivalence.get(value, value) for value in values}
    return len(classes) == 1


def has_duplicate_artifact_field(text: str, key: str) -> bool:
    pattern = rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*(?:=|:)\s*.+$"
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)) > 1


def has_duplicate_artifact_fields(text: str, keys: list[str] | tuple[str, ...]) -> bool:
    return any(has_duplicate_artifact_field(text, key) for key in keys)


CRITICAL_PROOF_ARTIFACT_FIELDS = (
    "phase",
    "agent_role",
    "challenge_review_mode",
    "vote",
    "agent_id",
    "viewpoint",
    "coverage_viewpoints",
    "challenge_round_id",
    "challenge_cycle_id",
    "closeout_round_id",
    "subject_digest",
    "source_ref",
    "source_digest",
    "authority_record_ref",
    "authority_revision",
    "authority_epoch",
    "adapter_manifest_ref",
    "adapter_effective_config_digest",
    "completion_subject_type",
    "completion_subject_digest",
    "stage_graph_digest",
    "challenge_cycle_ref",
    "challenge_cycle_digest_set",
    "context_mode",
    "authority_basis",
    "source_requirements_reconstructed",
    "claim_files_trust",
    "repo_inspection",
    "audit_gap_count",
    "scope_verdict",
    "route_context",
    "loaded_policy_refs",
    "policy_ref_digests",
    "policy_coverage_verdict",
    "model_policy",
    "resolved_model_slug",
    "resolved_reasoning_effort",
    "model_resolution_basis_ref",
    "spawn_model_binding",
    "spawn_tool_args_model",
    "spawn_tool_args_reasoning_effort",
    "spawn_tool_call_ref",
    "freshness_status",
)


CRITICAL_DISPATCH_ARTIFACT_FIELDS = (
    "dispatch_receipt_version",
    "phase",
    "agent_role",
    "challenge_review_mode",
    "agent_id",
    "viewpoint",
    "challenge_round_id",
    "challenge_cycle_id",
    "closeout_round_id",
    "source_ref",
    "source_digest",
    "context_mode",
    "authority_basis",
    "full_history_fork",
    "route_context",
    "loaded_policy_refs",
    "policy_ref_digests",
    "policy_coverage_verdict",
    "model_policy",
    "model_resolution_basis_ref",
    "spawn_model_binding",
    "spawn_tool_args_model",
    "spawn_tool_args_reasoning_effort",
    "authority_record_ref",
    "authority_revision_at_dispatch",
    "authority_epoch_at_dispatch",
)


CRITICAL_RESEARCH_ARTIFACT_FIELDS = (
    "phase",
    "agent_role",
    "agent_id",
    "research_lane",
    "research_cycle_id",
    "vote",
    "verdict",
    "source_ref",
    "source_digest",
    "authority_revision_at_dispatch",
    "authority_epoch_at_dispatch",
    "model_policy",
    "resolved_model_slug",
    "resolved_reasoning_effort",
    "model_resolution_basis_ref",
    "spawn_model_binding",
    "spawn_tool_args_model",
    "spawn_tool_args_reasoning_effort",
    "spawn_tool_call_ref",
)


CRITICAL_RESEARCH_DISPATCH_FIELDS = (
    "dispatch_receipt_version",
    "phase",
    "agent_role",
    "agent_id",
    "research_lane",
    "research_cycle_id",
    "source_ref",
    "source_digest",
    "authority_revision_at_dispatch",
    "authority_epoch_at_dispatch",
    "model_policy",
    "model_resolution_basis_ref",
    "spawn_model_binding",
    "spawn_tool_args_model",
    "spawn_tool_args_reasoning_effort",
)


CRITICAL_VERIFICATION_ARTIFACT_FIELDS = (
    "agent_role",
    "verification_agent_mode",
    "agent_id",
    "verification_status",
    "verification_result",
    "verification_command",
    "verification_ref",
    "evidence_ref",
    "source_digest",
    "stage_graph_digest",
    "authority_record_ref",
    "authority_revision",
    "authority_epoch",
    "adapter_manifest_ref",
    "adapter_effective_config_digest",
    "model_policy",
    "resolved_model_slug",
    "resolved_reasoning_effort",
    "spawn_model_binding",
    "spawn_tool_args_model",
    "spawn_tool_args_reasoning_effort",
    "spawn_tool_call_ref",
)


CRITICAL_FINAL_INLINE_FIELDS = (
    "allow_count",
    "deny_count",
    "ambiguous_count",
    "missing_count",
    "challenge_round_id",
    "closeout_round_id",
    "agent_role",
    "challenge_review_mode",
    "subject_digest",
    "source_ref",
    "source_digest",
    "authority_record_ref",
    "authority_revision",
    "authority_epoch",
    "adapter_manifest_ref",
    "adapter_effective_config_digest",
    "completion_subject_type",
    "completion_subject_digest",
    "stage_graph_digest",
    "challenge_cycle_ref",
    "challenge_cycle_digest_set",
    "context_mode",
    "authority_basis",
    "source_requirements_reconstructed",
    "claim_files_trust",
    "repo_inspection",
    "audit_gap_count",
    "scope_verdict",
    "route_context",
    "loaded_policy_refs",
    "policy_ref_digests",
    "policy_coverage_verdict",
    "viewpoint_set",
    "coverage_viewpoint_set",
    "model_policy",
    "resolved_model_slug",
    "resolved_reasoning_effort",
    "spawn_model_binding",
)


def inline_token_values(text: str, key: str) -> list[str]:
    return [
        clean_value(match.group(1))
        for match in re.finditer(rf"(?:^|[\s;,]){re.escape(key)}=([^\s;,\n]+)", text, flags=re.IGNORECASE)
    ]


def inline_token_is_unique(text: str, key: str) -> bool:
    return len(inline_token_values(text, key)) <= 1


def has_conflicting_inline_tokens(text: str, keys: list[str] | tuple[str, ...]) -> bool:
    for key in keys:
        values = inline_token_values(text, key)
        if len(values) > 1:
            return True
    return False


def extract_challenge_round_id(evidence: object) -> str:
    return clean_value(extract_inline_token_value(clean_value(str(evidence)), "challenge_round_id") or "")


def extract_closeout_round_id(evidence: object) -> str:
    return clean_value(extract_inline_token_value(clean_value(str(evidence)), "closeout_round_id") or "")


def extract_attempt_ref(evidence: object) -> str:
    return clean_value(extract_structured_value(clean_value(str(evidence)), "attempt_ref") or "")


def extract_inline_count(text: str, key: str) -> int | None:
    raw_value = extract_inline_token_value(text, key)
    if raw_value is None:
        return None
    try:
        return int(clean_value(raw_value))
    except ValueError:
        return None


def extract_source_digest_token(text: str) -> str:
    return clean_value(
        extract_inline_token_value(text, "source_digest")
        or extract_inline_token_value(text, "source_digest_sha256")
        or ""
    )


def final_policy_route_metadata_is_valid_inline(text: str, run_dir: Path) -> bool:
    return (
        clean_value(extract_inline_token_value(text, "route_context") or "").lower()
        == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT
        and clean_value(extract_inline_token_value(text, "policy_coverage_verdict") or "").lower()
        == REQUIRED_FINAL_POLICY_COVERAGE_VERDICT
        and policy_ref_tokens_are_complete(extract_inline_token_value(text, "loaded_policy_refs") or "", run_dir)
        and policy_ref_digests_are_valid(extract_inline_token_value(text, "policy_ref_digests") or "", run_dir)
    )


def final_policy_route_metadata_is_valid_artifact(text: str, run_dir: Path) -> bool:
    return (
        extract_artifact_field(text, "route_context").lower() == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT
        and extract_artifact_field(text, "policy_coverage_verdict").lower() == REQUIRED_FINAL_POLICY_COVERAGE_VERDICT
        and policy_ref_tokens_are_complete(extract_artifact_field(text, "loaded_policy_refs"), run_dir)
        and policy_ref_digests_are_valid(extract_artifact_field(text, "policy_ref_digests"), run_dir)
    )


def final_audit_evidence_is_valid(evidence: object, run_dir: Path) -> bool:
    text = clean_value(str(evidence)).lower()
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False
    if not final_policy_route_metadata_is_valid_inline(text, run_dir):
        return False

    required_tokens = {
        "source_ref": REQUIRED_SOURCE_REF,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
        "audit_gap_count": "0",
        "scope_verdict": REQUIRED_FINAL_AUDIT_SCOPE_VERDICT,
    }
    for key, expected in required_tokens.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected:
            return False

    return extract_source_digest_token(text).lower() == source_digest.lower()


def artifact_field_equals(text: str, key: str, expected: str) -> bool:
    return clean_value(extract_artifact_field(text, key)).lower() == expected.lower()


def final_audit_artifact_is_valid(text: str, run_dir: Path, required_phase: str) -> bool:
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False
    if not final_policy_route_metadata_is_valid_artifact(text, run_dir):
        return False

    required_fields = {
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
        "audit_gap_count": "0",
        "scope_verdict": REQUIRED_FINAL_AUDIT_SCOPE_VERDICT,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False

    if required_phase == "goal_completion" and not artifact_field_equals(
        text,
        "source_alignment_verdict",
        REQUIRED_GOAL_COMPLETION_ALIGNMENT_VERDICT,
    ):
        return False

    return True


def challenge_attempt_core_evidence_is_valid(evidence: object, run_dir: Path, required_phase: str) -> bool:
    text = clean_value(str(evidence)).lower()
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False
    if not final_policy_route_metadata_is_valid_inline(text, run_dir):
        return False

    required_tokens = {
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
    }
    for key, expected in required_tokens.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected.lower():
            return False

    required_challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES.get(required_phase)
    if not required_challenge_mode:
        return False
    required_challenge_tokens = {
        "agent_role": REQUIRED_FINAL_CHALLENGE_AGENT_ROLE,
        "challenge_review_mode": required_challenge_mode,
        "model_policy": REQUIRED_DELEGATED_MODEL_POLICY,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_challenge_tokens.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected.lower():
            return False

    return True


def challenge_attempt_core_artifact_is_valid(text: str, run_dir: Path) -> bool:
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False
    if not final_policy_route_metadata_is_valid_artifact(text, run_dir):
        return False

    required_fields = {
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False

    return True


def dispatch_receipt_is_valid(
    path: Path,
    *,
    run_dir: Path,
    required_phase: str,
    challenge_round_id: str,
    closeout_round_id: str,
    source_digest: str,
    viewpoint: str,
    agent_id: str,
    expected_model_slug: str,
    expected_reasoning_effort: str,
    expected_challenge_cycle_id: str | None = None,
    expected_authority_record_ref: str | None = None,
    expected_authority_revision: str | None = None,
    expected_authority_epoch: str | None = None,
) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if has_duplicate_artifact_fields(text, CRITICAL_DISPATCH_ARTIFACT_FIELDS):
        return False
    required_challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES.get(required_phase)
    if not required_challenge_mode:
        return False
    required_fields = {
        "dispatch_receipt_version": "v1",
        "phase": required_phase,
        "agent_role": REQUIRED_FINAL_CHALLENGE_AGENT_ROLE,
        "challenge_review_mode": required_challenge_mode,
        "agent_id": agent_id,
        "viewpoint": viewpoint,
        "challenge_round_id": challenge_round_id,
        "closeout_round_id": closeout_round_id,
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "full_history_fork": "false",
        "model_policy": REQUIRED_DELEGATED_MODEL_POLICY,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    optional_fields = {
        "challenge_cycle_id": expected_challenge_cycle_id,
        "authority_record_ref": expected_authority_record_ref,
        "authority_revision_at_dispatch": expected_authority_revision,
        "authority_epoch_at_dispatch": expected_authority_epoch,
    }
    for key, expected in optional_fields.items():
        if expected is not None and not artifact_field_equals(text, key, expected):
            return False
    if not final_policy_route_metadata_is_valid_artifact(text, run_dir):
        return False
    if is_placeholder_reference(extract_artifact_field(text, "model_resolution_basis_ref")):
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != clean_value(expected_model_slug).lower():
        return False
    if (
        clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower()
        != clean_value(expected_reasoning_effort).lower()
    ):
        return False
    return True


def challenge_round_id_seen_in_receipts(run_dir: Path, round_id: str) -> bool:
    if not round_id:
        return False
    receipts_dir = run_dir / "closeout-receipts"
    if not receipts_dir.exists():
        return False
    pattern = rf"\bchallenge_round_id={re.escape(round_id)}\b"
    for receipt_path in receipts_dir.glob("*.md"):
        text = receipt_path.read_text(encoding="utf-8", errors="ignore")
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def closeout_round_id_seen_in_receipts(run_dir: Path, round_id: str) -> bool:
    if not round_id:
        return False
    for dirname in ("closeout-receipts",):
        receipts_dir = run_dir / dirname
        if not receipts_dir.exists():
            continue
        pattern = rf"\bcloseout_round_id\b.*{re.escape(round_id)}|\bcloseout_round_id={re.escape(round_id)}\b"
        for receipt_path in receipts_dir.glob("*.md"):
            text = receipt_path.read_text(encoding="utf-8", errors="ignore")
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
    return False


def attempt_receipt_is_valid(path: Path, closeout_round_id: str, next_action: str, continue_exit_status: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "attempt_receipt_version").lower() != "v1":
        return False
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False
    if extract_artifact_field(text, "attempt_status").lower() != continue_exit_status.lower():
        return False
    if not has_anchor_overlap(extract_artifact_field(text, "next_action"), next_action):
        return False
    if not (
        extract_artifact_field(text, "command_ref")
        or extract_artifact_field(text, "artifact_ref")
        or extract_artifact_field(text, "summary")
    ):
        return False
    return True


def has_unanimous_codex_proof(
    evidence: object,
    run_dir: Path,
    required_phase: str,
    closeout_round_id: str,
) -> bool:
    text = clean_value(str(evidence)).lower()
    if not text:
        return False
    if has_conflicting_inline_tokens(text, CRITICAL_FINAL_INLINE_FIELDS):
        return False
    required_challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES.get(required_phase)
    if not required_challenge_mode:
        return False

    required_tokens = [
        f"allow_count={REQUIRED_DELEGATED_AGENT_COUNT}",
        "deny_count=0",
        "ambiguous_count=0",
        "missing_count=0",
        f"agent_role={REQUIRED_FINAL_CHALLENGE_AGENT_ROLE}",
        f"challenge_review_mode={required_challenge_mode}",
        f"top_model_lane_min={MIN_TOP_MODEL_LANES}",
    ]
    if not all(token in text for token in required_tokens):
        return False

    if not pipe_value_set_is_exact(extract_inline_token_value(text, "viewpoint_set"), REQUIRED_STOP_LANES):
        return False
    if not pipe_value_set_is_exact(extract_inline_token_value(text, "coverage_viewpoint_set"), REQUIRED_STOP_VIEWPOINTS):
        return False

    challenge_round_id = extract_inline_token_value(text, "challenge_round_id")
    if challenge_round_id is None or is_placeholder_reference(challenge_round_id):
        return False
    if extract_closeout_round_id(evidence).lower() != closeout_round_id.lower():
        return False

    subject_digest = extract_inline_token_value(text, "subject_digest")
    if subject_digest is None or is_placeholder_reference(subject_digest):
        return False
    if clean_value(subject_digest).lower() != compute_subject_digest(run_dir).lower():
        return False

    if extract_inline_token_value(text, "model_policy") != REQUIRED_DELEGATED_MODEL_POLICY:
        return False
    inline_model_slug = clean_value(extract_inline_token_value(text, "resolved_model_slug") or "")
    inline_reasoning_effort = clean_value(extract_inline_token_value(text, "resolved_reasoning_effort") or "")
    if (inline_model_slug or inline_reasoning_effort) and not delegated_model_is_allowed(
        inline_model_slug,
        inline_reasoning_effort,
    ):
        return False
    if extract_inline_token_value(text, "spawn_model_binding") != REQUIRED_DELEGATED_MODEL_BINDING:
        return False
    if not final_audit_evidence_is_valid(evidence, run_dir):
        return False

    refs = extract_consensus_refs(evidence)
    if len(refs) != REQUIRED_DELEGATED_AGENT_COUNT or len(set(refs)) != REQUIRED_DELEGATED_AGENT_COUNT:
        return False

    seen_agent_ids: set[str] = set()
    seen_viewpoints: set[str] = set()
    covered_viewpoints: set[str] = set()
    top_model_lane_count = 0
    top_xhigh_lane_count = 0
    model_mix_counts: dict[tuple[str, str], int] = {}
    current_authority_mtime = latest_authority_mtime(run_dir)
    source_digest = compute_source_digest(run_dir)

    for ref in refs:
        ref_path = resolve_artifact_ref(ref, run_dir)
        if ref_path is None:
            return False
        if current_authority_mtime and ref_path.stat().st_mtime < current_authority_mtime:
            return False

        artifact_text = ref_path.read_text(encoding="utf-8", errors="ignore")
        if has_duplicate_artifact_fields(artifact_text, CRITICAL_PROOF_ARTIFACT_FIELDS):
            return False
        if extract_artifact_field(artifact_text, "phase").lower() != required_phase:
            return False
        if extract_artifact_field(artifact_text, "agent_role").lower() != REQUIRED_FINAL_CHALLENGE_AGENT_ROLE:
            return False
        if extract_artifact_field(artifact_text, "challenge_review_mode").lower() != required_challenge_mode:
            return False
        if not artifact_alias_values_are_allowed(artifact_text, ("vote", "verdict"), {"allow"}):
            return False
        if not final_audit_artifact_is_valid(artifact_text, run_dir, required_phase):
            return False

        agent_id = extract_artifact_field(artifact_text, "agent_id").lower()
        if not agent_id or agent_id in seen_agent_ids:
            return False
        seen_agent_ids.add(agent_id)

        viewpoint = extract_artifact_field(artifact_text, "viewpoint").lower()
        if viewpoint not in REQUIRED_STOP_LANES or viewpoint in seen_viewpoints:
            return False
        seen_viewpoints.add(viewpoint)
        expected_lane_coverage = REQUIRED_STOP_LANE_COVERAGE.get(viewpoint, set())
        coverage_text = extract_artifact_field(artifact_text, "coverage_viewpoints") or extract_artifact_field(
            artifact_text,
            "covered_viewpoints",
        )
        if not pipe_value_set_is_exact(coverage_text, expected_lane_coverage):
            return False
        lane_coverage = extract_pipe_value_set(coverage_text)
        covered_viewpoints.update(lane_coverage)

        artifact_round_id = (
            extract_artifact_field(artifact_text, "challenge_round_id")
            or extract_artifact_field(artifact_text, "freshness_ref")
        )
        if clean_value(artifact_round_id).lower() != challenge_round_id.lower():
            return False
        artifact_closeout_round_id = (
            extract_artifact_field(artifact_text, "closeout_round_id")
            or extract_artifact_field(artifact_text, "closeout_ref")
            or extract_artifact_field(artifact_text, "freshness_anchor")
        )
        if clean_value(artifact_closeout_round_id).lower() != closeout_round_id.lower():
            return False
        if extract_artifact_field(artifact_text, "subject_digest").lower() != clean_value(subject_digest).lower():
            return False

        if extract_artifact_field(artifact_text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
            return False
        artifact_model_slug = clean_value(extract_artifact_field(artifact_text, "resolved_model_slug"))
        artifact_reasoning_effort = clean_value(extract_artifact_field(artifact_text, "resolved_reasoning_effort"))
        spawn_model_slug = clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_model"))
        spawn_reasoning_effort = clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_reasoning_effort"))
        if not delegated_model_is_allowed(artifact_model_slug, artifact_reasoning_effort):
            return False
        if spawn_model_slug.lower() != artifact_model_slug.lower():
            return False
        if spawn_reasoning_effort.lower() != artifact_reasoning_effort.lower():
            return False
        if delegated_model_is_top(artifact_model_slug, artifact_reasoning_effort):
            top_model_lane_count += 1
        if delegated_model_is_top_xhigh(artifact_model_slug, artifact_reasoning_effort):
            top_xhigh_lane_count += 1
        lane_model_key = delegated_lane_model_key(artifact_model_slug, artifact_reasoning_effort)
        model_mix_counts[lane_model_key] = model_mix_counts.get(lane_model_key, 0) + 1
        if is_placeholder_reference(extract_artifact_field(artifact_text, "model_resolution_basis_ref")):
            return False
        if extract_artifact_field(artifact_text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            return False
        spawn_tool_call_ref = extract_artifact_field(artifact_text, "spawn_tool_call_ref")
        if is_placeholder_reference(spawn_tool_call_ref):
            return False
        dispatch_path = resolve_artifact_ref(spawn_tool_call_ref, run_dir)
        if dispatch_path is None or not dispatch_receipt_is_valid(
            dispatch_path,
            run_dir=run_dir,
            required_phase=required_phase,
            challenge_round_id=challenge_round_id,
            closeout_round_id=closeout_round_id,
            source_digest=source_digest,
            viewpoint=viewpoint,
            agent_id=agent_id,
            expected_model_slug=artifact_model_slug,
            expected_reasoning_effort=artifact_reasoning_effort,
        ):
            return False

        freshness_status = (
            extract_artifact_field(artifact_text, "freshness_status")
            or extract_artifact_field(artifact_text, "freshness")
        ).lower()
        if freshness_status not in FRESH_PROOF_STATUSES:
            return False

    return (
        seen_viewpoints == REQUIRED_STOP_LANES
        and covered_viewpoints == REQUIRED_STOP_VIEWPOINTS
        and top_model_lane_count >= MIN_TOP_MODEL_LANES
        and top_xhigh_lane_count >= MIN_TOP_XHIGH_LANES
        and model_mix_counts == REQUIRED_DELEGATED_MODEL_MIX
    )


def has_codex_challenge_attempt(
    evidence: object,
    run_dir: Path,
    required_phase: str,
    closeout_round_id: str,
) -> bool:
    text = clean_value(str(evidence)).lower()
    if not text:
        return False
    if has_conflicting_inline_tokens(text, CRITICAL_FINAL_INLINE_FIELDS):
        return False
    required_challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES.get(required_phase)
    if not required_challenge_mode:
        return False
    if not challenge_attempt_core_evidence_is_valid(evidence, run_dir, required_phase):
        return False

    challenge_round_id = extract_inline_token_value(text, "challenge_round_id")
    if challenge_round_id is None or is_placeholder_reference(challenge_round_id):
        return False
    if extract_closeout_round_id(evidence).lower() != closeout_round_id.lower():
        return False

    if not pipe_value_set_is_exact(extract_inline_token_value(text, "viewpoint_set"), REQUIRED_STOP_LANES):
        return False
    if not pipe_value_set_is_exact(extract_inline_token_value(text, "coverage_viewpoint_set"), REQUIRED_STOP_VIEWPOINTS):
        return False

    allow_count = extract_inline_count(text, "allow_count")
    deny_count = extract_inline_count(text, "deny_count")
    ambiguous_count = extract_inline_count(text, "ambiguous_count")
    missing_count = extract_inline_count(text, "missing_count")
    if None in {allow_count, deny_count, ambiguous_count, missing_count}:
        return False
    if allow_count + deny_count + ambiguous_count + missing_count != REQUIRED_DELEGATED_AGENT_COUNT:
        return False
    if missing_count != 0:
        return False

    subject_digest = extract_inline_token_value(text, "subject_digest")
    if subject_digest is None or is_placeholder_reference(subject_digest):
        return False
    if clean_value(subject_digest).lower() != compute_subject_digest(run_dir).lower():
        return False

    inline_model_slug = clean_value(extract_inline_token_value(text, "resolved_model_slug") or "")
    inline_reasoning_effort = clean_value(extract_inline_token_value(text, "resolved_reasoning_effort") or "")
    if (inline_model_slug or inline_reasoning_effort) and not delegated_model_is_allowed(
        inline_model_slug,
        inline_reasoning_effort,
    ):
        return False

    refs = extract_consensus_refs(evidence)
    if len(refs) != REQUIRED_DELEGATED_AGENT_COUNT or len(set(refs)) != REQUIRED_DELEGATED_AGENT_COUNT:
        return False

    seen_agent_ids: set[str] = set()
    seen_viewpoints: set[str] = set()
    covered_viewpoints: set[str] = set()
    top_model_lane_count = 0
    top_xhigh_lane_count = 0
    model_mix_counts: dict[tuple[str, str], int] = {}
    artifact_vote_counts = {"allow": 0, "deny": 0, "ambiguous": 0}
    current_authority_mtime = latest_authority_mtime(run_dir)
    source_digest = compute_source_digest(run_dir)

    for ref in refs:
        ref_path = resolve_artifact_ref(ref, run_dir)
        if ref_path is None:
            return False
        if current_authority_mtime and ref_path.stat().st_mtime < current_authority_mtime:
            return False

        artifact_text = ref_path.read_text(encoding="utf-8", errors="ignore")
        if has_duplicate_artifact_fields(artifact_text, CRITICAL_PROOF_ARTIFACT_FIELDS):
            return False
        if extract_artifact_field(artifact_text, "phase").lower() != required_phase:
            return False
        if extract_artifact_field(artifact_text, "agent_role").lower() != REQUIRED_FINAL_CHALLENGE_AGENT_ROLE:
            return False
        if extract_artifact_field(artifact_text, "challenge_review_mode").lower() != required_challenge_mode:
            return False
        if not challenge_attempt_core_artifact_is_valid(artifact_text, run_dir):
            return False

        if not artifact_alias_values_are_allowed(artifact_text, ("vote", "verdict"), set(artifact_vote_counts)):
            return False
        vote = extract_artifact_field(artifact_text, "vote").lower()
        if vote not in artifact_vote_counts:
            return False
        artifact_vote_counts[vote] += 1

        agent_id = extract_artifact_field(artifact_text, "agent_id").lower()
        if not agent_id or agent_id in seen_agent_ids:
            return False
        seen_agent_ids.add(agent_id)

        viewpoint = extract_artifact_field(artifact_text, "viewpoint").lower()
        if viewpoint not in REQUIRED_STOP_LANES or viewpoint in seen_viewpoints:
            return False
        seen_viewpoints.add(viewpoint)
        expected_lane_coverage = REQUIRED_STOP_LANE_COVERAGE.get(viewpoint, set())
        coverage_text = extract_artifact_field(artifact_text, "coverage_viewpoints") or extract_artifact_field(
            artifact_text,
            "covered_viewpoints",
        )
        if not pipe_value_set_is_exact(coverage_text, expected_lane_coverage):
            return False
        lane_coverage = extract_pipe_value_set(coverage_text)
        covered_viewpoints.update(lane_coverage)

        artifact_round_id = (
            extract_artifact_field(artifact_text, "challenge_round_id")
            or extract_artifact_field(artifact_text, "freshness_ref")
        )
        if clean_value(artifact_round_id).lower() != challenge_round_id.lower():
            return False
        artifact_closeout_round_id = (
            extract_artifact_field(artifact_text, "closeout_round_id")
            or extract_artifact_field(artifact_text, "closeout_ref")
            or extract_artifact_field(artifact_text, "freshness_anchor")
        )
        if clean_value(artifact_closeout_round_id).lower() != closeout_round_id.lower():
            return False
        if extract_artifact_field(artifact_text, "subject_digest").lower() != clean_value(subject_digest).lower():
            return False

        if extract_artifact_field(artifact_text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
            return False
        artifact_model_slug = clean_value(extract_artifact_field(artifact_text, "resolved_model_slug"))
        artifact_reasoning_effort = clean_value(extract_artifact_field(artifact_text, "resolved_reasoning_effort"))
        spawn_model_slug = clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_model"))
        spawn_reasoning_effort = clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_reasoning_effort"))
        if not delegated_model_is_allowed(artifact_model_slug, artifact_reasoning_effort):
            return False
        if spawn_model_slug.lower() != artifact_model_slug.lower():
            return False
        if spawn_reasoning_effort.lower() != artifact_reasoning_effort.lower():
            return False
        if delegated_model_is_top(artifact_model_slug, artifact_reasoning_effort):
            top_model_lane_count += 1
        if delegated_model_is_top_xhigh(artifact_model_slug, artifact_reasoning_effort):
            top_xhigh_lane_count += 1
        lane_model_key = delegated_lane_model_key(artifact_model_slug, artifact_reasoning_effort)
        model_mix_counts[lane_model_key] = model_mix_counts.get(lane_model_key, 0) + 1
        if is_placeholder_reference(extract_artifact_field(artifact_text, "model_resolution_basis_ref")):
            return False
        if extract_artifact_field(artifact_text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            return False
        spawn_tool_call_ref = extract_artifact_field(artifact_text, "spawn_tool_call_ref")
        if is_placeholder_reference(spawn_tool_call_ref):
            return False
        dispatch_path = resolve_artifact_ref(spawn_tool_call_ref, run_dir)
        if dispatch_path is None or not dispatch_receipt_is_valid(
            dispatch_path,
            run_dir=run_dir,
            required_phase=required_phase,
            challenge_round_id=challenge_round_id,
            closeout_round_id=closeout_round_id,
            source_digest=source_digest,
            viewpoint=viewpoint,
            agent_id=agent_id,
            expected_model_slug=artifact_model_slug,
            expected_reasoning_effort=artifact_reasoning_effort,
        ):
            return False

        freshness_status = (
            extract_artifact_field(artifact_text, "freshness_status")
            or extract_artifact_field(artifact_text, "freshness")
        ).lower()
        if freshness_status not in FRESH_PROOF_STATUSES:
            return False

    return (
        seen_viewpoints == REQUIRED_STOP_LANES
        and covered_viewpoints == REQUIRED_STOP_VIEWPOINTS
        and top_model_lane_count >= MIN_TOP_MODEL_LANES
        and top_xhigh_lane_count >= MIN_TOP_XHIGH_LANES
        and model_mix_counts == REQUIRED_DELEGATED_MODEL_MIX
        and artifact_vote_counts["allow"] == allow_count
        and artifact_vote_counts["deny"] == deny_count
        and artifact_vote_counts["ambiguous"] == ambiguous_count
    )


def has_stop_authorization_proof(evidence: object, run_dir: Path, closeout_round_id: str) -> bool:
    return has_unanimous_codex_proof(
        evidence,
        run_dir,
        required_phase="stop_authorization",
        closeout_round_id=closeout_round_id,
    )


def has_stop_authorization_challenge_attempt(evidence: object, run_dir: Path, closeout_round_id: str) -> bool:
    return has_codex_challenge_attempt(
        evidence,
        run_dir,
        required_phase="stop_authorization",
        closeout_round_id=closeout_round_id,
    )


def has_goal_completion_proof(evidence: object, run_dir: Path, closeout_round_id: str) -> bool:
    return has_unanimous_codex_proof(
        evidence,
        run_dir,
        required_phase="goal_completion",
        closeout_round_id=closeout_round_id,
    )


def completion_candidate_points_at_challenge(*values: object) -> bool:
    combined = " ".join(clean_value(str(value)).lower() for value in values if clean_value(str(value)))
    return contains_any_pattern(combined, COMPLETION_GATE_PATTERNS)


def requires_approval_or_no_action_challenge(fields: dict[str, object]) -> bool:
    run_decision = clean_value(str(fields.get("run_decision", ""))).lower()
    external_basis = clean_value(str(fields.get("external_authority_basis", ""))).lower()
    continue_exit_status = clean_value(str(fields.get("continue_exit_status", ""))).lower()
    turn_exit_cause = clean_value(str(fields.get("turn_exit_cause", ""))).lower()
    local_action_text = " | ".join(
        [
            clean_value(str(fields.get("current_or_next_stage", ""))),
            clean_value(str(fields.get("next_mandatory_action", ""))),
            flatten_multivalue_text(fields.get("remaining_required_stages", "")),
            flatten_multivalue_text(fields.get("resume_instructions", "")),
        ]
    )
    combined = " | ".join(
        [
            clean_value(str(fields.get("current_or_next_stage", ""))),
            clean_value(str(fields.get("next_mandatory_action", ""))),
            flatten_multivalue_text(fields.get("remaining_required_stages", "")),
            flatten_multivalue_text(fields.get("blocking_findings", "")),
            clean_value(str(fields.get("pause_reason", ""))),
            clean_value(str(fields.get("continue_exit_evidence", ""))),
            clean_value(str(fields.get("turn_exit_evidence", ""))),
            flatten_multivalue_text(fields.get("resume_instructions", "")),
        ]
    )
    local_action_available = (
        not contains_any_pattern(local_action_text, NO_BOUNDED_LOCAL_ACTION_PATTERNS)
        and (
            contains_any_pattern(local_action_text, LOCAL_EDIT_CONTINUE_PATTERNS)
            or contains_any_pattern(local_action_text, VALIDATION_EVIDENCE_PATTERNS)
            or contains_any_pattern(local_action_text, STRONG_CONTINUE_EXIT_PATTERNS)
        )
    )

    if external_basis == "human_decision_required":
        return not local_action_available
    if run_decision in {"continue", "pause"} and contains_any_pattern(combined, APPROVAL_OR_NO_LOCAL_ACTION_CHALLENGE_PATTERNS):
        if local_action_available and not contains_any_pattern(combined, NO_BOUNDED_LOCAL_ACTION_PATTERNS):
            return False
        return True
    if run_decision == "continue" and continue_exit_status == "blocked_during_attempt" and turn_exit_cause == "blocked_during_attempt":
        if local_action_available and not contains_any_pattern(combined, NO_BOUNDED_LOCAL_ACTION_PATTERNS):
            return False
        return contains_any_pattern(combined, APPROVAL_OR_NO_LOCAL_ACTION_CHALLENGE_PATTERNS)
    return False


def inline_token_set(value: str | None) -> set[str]:
    return {clean_value(part).lower() for part in re.split(r"[|,]", clean_value(value or "")) if clean_value(part)}


def inline_token_set_is_exact(value: str | None, expected: set[str]) -> bool:
    return pipe_value_set_is_exact(value, expected)


def strategy_dispatch_receipt_is_valid(path: Path, run_dir: Path, authority_path: Path | None = None) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if has_duplicate_artifact_fields(text, CRITICAL_DISPATCH_ARTIFACT_FIELDS):
        return False
    if not artifact_field_equals(text, "dispatch_receipt_version", "v1"):
        return False
    if extract_artifact_field(text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
        return False
    if extract_artifact_field(text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != TOP_DELEGATED_MODEL_SLUG.lower():
        return False
    if (
        clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower()
        != TOP_DELEGATED_REASONING_EFFORT.lower()
    ):
        return False
    resolved_model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
    resolved_reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
    if resolved_model_slug and resolved_model_slug.lower() != TOP_DELEGATED_MODEL_SLUG.lower():
        return False
    if resolved_reasoning_effort and resolved_reasoning_effort.lower() != TOP_DELEGATED_REASONING_EFFORT.lower():
        return False
    if not artifact_field_equals(text, "agent_role", REQUIRED_STRATEGY_AGENT_ROLE):
        return False
    if extract_artifact_field(text, "route_context").lower() == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT:
        return False
    return artifact_binds_current_v3_snapshot(text, run_dir, authority_path=authority_path)


def strategy_artifact_has_top_model_authority(path: Path, run_dir: Path, authority_path: Path | None = None) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    dispatch_ref = extract_artifact_field(text, "dispatch_ref")
    dispatch_path = resolve_artifact_ref(dispatch_ref, run_dir)
    target_scope = record_value(authority_path, "target_scope").lower() if authority_path is not None else ""
    requires_portability = (
        artifact_field_equals(text, "global_skill_change", "true")
        or target_scope in {"global_skill", "codex_skill", "agent_loop_skill"}
    )
    if requires_portability and not artifact_field_equals(text, "portability_classification", "global_invariant"):
        return False
    return (
        artifact_field_equals(text, "agent_role", REQUIRED_STRATEGY_AGENT_ROLE)
        and
        artifact_field_equals(text, "plan_model_policy", "strongest_model_required")
        and artifact_field_equals(text, "plan_model_slug", TOP_DELEGATED_MODEL_SLUG)
        and artifact_field_equals(text, "plan_reasoning_effort", TOP_DELEGATED_REASONING_EFFORT)
        and dispatch_path is not None
        and strategy_dispatch_receipt_is_valid(dispatch_path, run_dir, authority_path=authority_path)
    )


def implementation_dispatch_receipt_is_valid(
    path: Path,
    *,
    run_dir: Path,
    challenge_review_mode: str,
    viewpoint: str,
    agent_id: str,
    expected_model_slug: str,
    expected_reasoning_effort: str,
    authority_path: Path | None = None,
) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if has_duplicate_artifact_fields(text, CRITICAL_DISPATCH_ARTIFACT_FIELDS):
        return False
    required_fields = {
        "dispatch_receipt_version": "v1",
        "agent_role": REQUIRED_FINAL_CHALLENGE_AGENT_ROLE,
        "challenge_review_mode": challenge_review_mode,
        "agent_id": agent_id,
        "viewpoint": viewpoint,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    if extract_artifact_field(text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
        return False
    if extract_artifact_field(text, "route_context").lower() == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT:
        return False
    if is_placeholder_reference(extract_artifact_field(text, "model_resolution_basis_ref")):
        return False
    if not artifact_binds_current_v3_snapshot(text, run_dir, authority_path=authority_path):
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != clean_value(expected_model_slug).lower():
        return False
    if (
        clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower()
        != clean_value(expected_reasoning_effort).lower()
    ):
        return False
    resolved_model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
    resolved_reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
    if resolved_model_slug and resolved_model_slug.lower() != clean_value(expected_model_slug).lower():
        return False
    if resolved_reasoning_effort and resolved_reasoning_effort.lower() != clean_value(expected_reasoning_effort).lower():
        return False
    return True


def verification_dispatch_receipt_is_valid(
    path: Path,
    *,
    run_dir: Path,
    agent_id: str,
    expected_model_slug: str,
    expected_reasoning_effort: str,
    authority_path: Path | None = None,
) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if has_duplicate_artifact_fields(text, CRITICAL_DISPATCH_ARTIFACT_FIELDS + ("verification_agent_mode",)):
        return False
    required_fields = {
        "dispatch_receipt_version": "v1",
        "agent_role": REQUIRED_VERIFICATION_AGENT_ROLE,
        "verification_agent_mode": REQUIRED_VERIFICATION_AGENT_MODE,
        "agent_id": agent_id,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    if extract_artifact_field(text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
        return False
    if extract_artifact_field(text, "route_context").lower() == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT:
        return False
    if not artifact_binds_current_v3_snapshot(text, run_dir, authority_path=authority_path):
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != clean_value(expected_model_slug).lower():
        return False
    if (
        clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower()
        != clean_value(expected_reasoning_effort).lower()
    ):
        return False
    resolved_model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
    resolved_reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
    if resolved_model_slug and resolved_model_slug.lower() != clean_value(expected_model_slug).lower():
        return False
    if resolved_reasoning_effort and resolved_reasoning_effort.lower() != clean_value(expected_reasoning_effort).lower():
        return False
    return True


def verification_agent_artifact_is_valid(
    path: Path | None,
    run_dir: Path,
    authority_path: Path | None = None,
) -> bool:
    if path is None:
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    if has_duplicate_artifact_fields(text, CRITICAL_VERIFICATION_ARTIFACT_FIELDS):
        return False
    if not artifact_binds_current_v3_snapshot(text, run_dir, authority_path=authority_path):
        return False
    required_fields = {
        "agent_role": REQUIRED_VERIFICATION_AGENT_ROLE,
        "verification_agent_mode": REQUIRED_VERIFICATION_AGENT_MODE,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    if extract_artifact_field(text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
        return False
    if clean_value(extract_artifact_field(text, "verification_status")).lower() not in {"pass", "passed"}:
        return False
    if clean_value(extract_artifact_field(text, "verification_result")).lower() not in {"pass", "passed"}:
        return False
    if is_noneish(extract_artifact_field(text, "verification_command")):
        return False
    verification_ref = extract_artifact_field(text, "verification_ref")
    evidence_ref = extract_artifact_field(text, "evidence_ref")
    if resolve_artifact_ref(verification_ref, run_dir) is None or resolve_artifact_ref(evidence_ref, run_dir) is None:
        return False
    agent_id = extract_artifact_field(text, "agent_id").lower()
    if not agent_id:
        return False
    model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
    reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
    if not delegated_model_is_allowed(model_slug, reasoning_effort):
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != model_slug.lower():
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower() != reasoning_effort.lower():
        return False
    if is_placeholder_reference(extract_artifact_field(text, "spawn_tool_call_ref")):
        return False
    dispatch_path = resolve_artifact_ref(extract_artifact_field(text, "spawn_tool_call_ref"), run_dir)
    if dispatch_path is None:
        return False
    return verification_dispatch_receipt_is_valid(
        dispatch_path,
        run_dir=run_dir,
        agent_id=agent_id,
        expected_model_slug=model_slug,
        expected_reasoning_effort=reasoning_effort,
        authority_path=authority_path,
    )


def implementation_challenge_artifacts_are_valid(
    refs: list[str],
    *,
    run_dir: Path,
    challenge_review_mode: str,
    required_viewpoints: set[str],
    required_model_mix: dict[tuple[str, str], int] = REQUIRED_IMPLEMENTATION_CHALLENGE_MODEL_MIX,
    authority_path: Path | None = None,
) -> bool:
    expected_count = len(required_viewpoints)
    if len(refs) != expected_count or len(set(refs)) != expected_count:
        return False
    seen_viewpoints: set[str] = set()
    model_mix_counts: dict[tuple[str, str], int] = {}
    agent_ids: set[str] = set()
    for ref in refs:
        path = resolve_artifact_ref(ref, run_dir)
        if path is None:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
        if has_duplicate_artifact_fields(text, CRITICAL_PROOF_ARTIFACT_FIELDS):
            return False
        if not artifact_binds_current_v3_snapshot(text, run_dir, authority_path=authority_path):
            return False
        if not artifact_field_equals(text, "agent_role", REQUIRED_FINAL_CHALLENGE_AGENT_ROLE):
            return False
        if not artifact_field_equals(text, "challenge_review_mode", challenge_review_mode):
            return False
        if not artifact_alias_values_are_allowed(text, ("vote", "verdict"), {"allow", "pass", "approve"}):
            return False
        verdict = (
            extract_artifact_field(text, "vote")
            or extract_artifact_field(text, "verdict")
        ).lower()
        if verdict not in {"allow", "pass", "approve"}:
            return False
        viewpoint = extract_artifact_field(text, "viewpoint").lower()
        if viewpoint not in required_viewpoints or viewpoint in seen_viewpoints:
            return False
        seen_viewpoints.add(viewpoint)
        agent_id = extract_artifact_field(text, "agent_id").lower()
        if not agent_id or agent_id in agent_ids:
            return False
        agent_ids.add(agent_id)
        if extract_artifact_field(text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
            return False
        if is_placeholder_reference(extract_artifact_field(text, "model_resolution_basis_ref")):
            return False
        model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
        reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
        if not delegated_model_is_allowed(model_slug, reasoning_effort):
            return False
        if extract_artifact_field(text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            return False
        if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != model_slug.lower():
            return False
        if clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower() != reasoning_effort.lower():
            return False
        if is_placeholder_reference(extract_artifact_field(text, "spawn_tool_call_ref")):
            return False
        dispatch_path = resolve_artifact_ref(extract_artifact_field(text, "spawn_tool_call_ref"), run_dir)
        if dispatch_path is None or not implementation_dispatch_receipt_is_valid(
            dispatch_path,
            run_dir=run_dir,
            challenge_review_mode=challenge_review_mode,
            viewpoint=viewpoint,
            agent_id=agent_id,
            expected_model_slug=model_slug,
            expected_reasoning_effort=reasoning_effort,
            authority_path=authority_path,
        ):
            return False
        freshness_status = (
            extract_artifact_field(text, "freshness_status")
            or extract_artifact_field(text, "freshness")
        ).lower()
        if freshness_status not in FRESH_PROOF_STATUSES:
            return False
        key = delegated_lane_model_key(model_slug, reasoning_effort)
        model_mix_counts[key] = model_mix_counts.get(key, 0) + 1
    return seen_viewpoints == required_viewpoints and model_mix_counts == required_model_mix


def implementation_mini_plan_validation_evidence_is_valid(
    evidence: object,
    run_dir: Path,
    authority_path: Path | None = None,
) -> bool:
    text = clean_value(str(evidence))
    if is_noneish(text):
        return False
    guarded_tokens = (
        "pre_plan_validation_lane_count",
        "post_plan_validation_lane_count",
        "pre_plan_validation_viewpoint_set",
        "post_plan_validation_viewpoint_set",
        "pre_plan_validation_verdict",
        "post_plan_validation_verdict",
        "pre_plan_validation_refs",
        "post_plan_validation_refs",
        "strategy_ref",
        "verification_agent_ref",
    )
    if any(not inline_token_is_unique(text, key) for key in guarded_tokens):
        return False
    required_pairs = {
        "pre_plan_validation_lane_count": "2",
        "post_plan_validation_lane_count": "2",
    }
    for key, expected in required_pairs.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected:
            return False
    if not inline_token_set_is_exact(
        extract_inline_token_value(text, "pre_plan_validation_viewpoint_set"),
        REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
    ):
        return False
    if not inline_token_set_is_exact(
        extract_inline_token_value(text, "post_plan_validation_viewpoint_set"),
        REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
    ):
        return False
    if clean_value(extract_inline_token_value(text, "pre_plan_validation_verdict") or "").lower() not in {
        "pass_unanimous",
        "allow_unanimous",
    }:
        return False
    if clean_value(extract_inline_token_value(text, "post_plan_validation_verdict") or "").lower() not in {
        "pass_unanimous",
        "allow_unanimous",
    }:
        return False
    strategy_refs = split_policy_list(extract_inline_token_value(text, "strategy_ref") or "")
    if len(strategy_refs) != 1:
        return False
    strategy_path = resolve_artifact_ref(strategy_refs[0], run_dir)
    if strategy_path is None or not strategy_artifact_has_top_model_authority(strategy_path, run_dir, authority_path=authority_path):
        return False
    verification_agent_refs = split_policy_list(extract_inline_token_value(text, "verification_agent_ref") or "")
    if len(verification_agent_refs) != 1:
        return False
    verification_agent_path = resolve_artifact_ref(verification_agent_refs[0], run_dir)
    if verification_agent_path is None or verification_agent_path.resolve() == strategy_path.resolve():
        return False
    if not verification_agent_artifact_is_valid(verification_agent_path, run_dir, authority_path=authority_path):
        return False
    pre_refs = split_policy_list(extract_inline_token_value(text, "pre_plan_validation_refs") or "")
    post_refs = split_policy_list(extract_inline_token_value(text, "post_plan_validation_refs") or "")
    return implementation_challenge_artifacts_are_valid(
        pre_refs,
        run_dir=run_dir,
        challenge_review_mode="pre_implementation_plan_validation",
        required_viewpoints=REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
        required_model_mix=REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
        authority_path=authority_path,
    ) and implementation_challenge_artifacts_are_valid(
        post_refs,
        run_dir=run_dir,
        challenge_review_mode="post_implementation_plan_validation",
        required_viewpoints=REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
        required_model_mix=REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
        authority_path=authority_path,
    )


def implementation_gate_mini_requirement_is_satisfied(
    evidence: object,
    run_dir: Path,
    risk_tier: str,
    authority_path: Path | None = None,
) -> bool:
    if implementation_mini_plan_validation_evidence_is_valid(evidence, run_dir, authority_path=authority_path):
        return True
    if is_tier1_self_check_authorized(evidence, run_dir, risk_tier):
        return True
    text = clean_value(str(evidence))
    if risk_tier in {"tier0_trivial", "tier1_local"}:
        guarded_tokens = (
            "mini_plan_validation_skip",
            "local_verification",
            "skip_scope_evidence",
            "external_api",
            "db_or_migration",
            "security_sensitive",
            "verification_result",
        )
        if any(not inline_token_is_unique(text, key) for key in guarded_tokens):
            return False
        skip = clean_value(extract_inline_token_value(text, "mini_plan_validation_skip") or "").lower()
        allowed_skips = {"single_file_local_fix", "user_specified_exact_change", "no_behavior_change"}
        if risk_tier == "tier0_trivial":
            allowed_skips.add("tier0_trivial")
        if skip not in allowed_skips:
            return False
        if not inline_token_is_unique(text, "mini_plan_validation_skip"):
            return False
        if is_noneish(extract_inline_token_value(text, "local_verification") or ""):
            return False
        if is_noneish(extract_inline_token_value(text, "skip_scope_evidence") or ""):
            return False
        for key in ("external_api", "db_or_migration", "security_sensitive"):
            if clean_value(extract_inline_token_value(text, key) or "").lower() != "false":
                return False
        if clean_value(extract_inline_token_value(text, "verification_result") or "").lower() not in {"pass", "passed"}:
            return False
        return True
    if risk_tier == "not_classified":
        return (
            clean_value(extract_inline_token_value(text, "file_changing_batch") or "").lower() == "false"
            and not is_noneish(extract_inline_token_value(text, "non_file_change_evidence") or "")
        )
    return False


def implementation_gate_evidence_is_valid(evidence: object, run_dir: Path, authority_path: Path | None = None) -> bool:
    text = clean_value(str(evidence))
    if is_noneish(text):
        return False
    guarded_tokens = (
        "pre_challenge_lane_count",
        "post_challenge_lane_count",
        "pre_challenge_viewpoint_set",
        "post_challenge_viewpoint_set",
        "pre_challenge_verdict",
        "post_challenge_verdict",
        "strategy_ref",
        "pre_challenge_refs",
        "post_challenge_refs",
    )
    if any(not inline_token_is_unique(text, key) for key in guarded_tokens):
        return False
    required_pairs = {
        "pre_challenge_lane_count": "5",
        "post_challenge_lane_count": "5",
    }
    for key, expected in required_pairs.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected:
            return False
    if not inline_token_set_is_exact(
        extract_inline_token_value(text, "pre_challenge_viewpoint_set"),
        REQUIRED_PRE_IMPLEMENTATION_VIEWPOINTS,
    ):
        return False
    if not inline_token_set_is_exact(
        extract_inline_token_value(text, "post_challenge_viewpoint_set"),
        REQUIRED_POST_IMPLEMENTATION_VIEWPOINTS,
    ):
        return False
    if clean_value(extract_inline_token_value(text, "pre_challenge_verdict") or "").lower() not in {
        "pass_unanimous",
        "allow_unanimous",
    }:
        return False
    if clean_value(extract_inline_token_value(text, "post_challenge_verdict") or "").lower() not in {
        "pass_unanimous",
        "allow_unanimous",
    }:
        return False
    strategy_ref = clean_value(extract_inline_token_value(text, "strategy_ref") or "")
    if is_noneish(strategy_ref):
        return False
    strategy_path = resolve_artifact_ref(strategy_ref, run_dir)
    if strategy_path is None or not strategy_artifact_has_top_model_authority(strategy_path, run_dir, authority_path=authority_path):
        return False
    pre_refs = split_policy_list(extract_inline_token_value(text, "pre_challenge_refs") or "")
    post_refs = split_policy_list(extract_inline_token_value(text, "post_challenge_refs") or "")
    return implementation_challenge_artifacts_are_valid(
        pre_refs,
        run_dir=run_dir,
        challenge_review_mode="pre_implementation_challenge",
        required_viewpoints=REQUIRED_PRE_IMPLEMENTATION_VIEWPOINTS,
        required_model_mix=REQUIRED_IMPLEMENTATION_CHALLENGE_MODEL_MIX,
        authority_path=authority_path,
    ) and implementation_challenge_artifacts_are_valid(
        post_refs,
        run_dir=run_dir,
        challenge_review_mode="post_implementation_challenge",
        required_viewpoints=REQUIRED_POST_IMPLEMENTATION_VIEWPOINTS,
        required_model_mix=REQUIRED_IMPLEMENTATION_CHALLENGE_MODEL_MIX,
        authority_path=authority_path,
    )


def implementation_gate_evidence_has_valid_waiver(evidence: object, risk_tier: str) -> bool:
    text = clean_value(str(evidence))
    if is_noneish(text):
        return False
    waiver = clean_value(extract_inline_token_value(text, "implementation_gate_waiver") or "").lower()
    if waiver not in {"delegated_tool_unavailable", "demonstrably_mechanical"}:
        return False
    if clean_value(extract_inline_token_value(text, "risk_tier") or "") != risk_tier:
        return False
    if is_noneish(extract_inline_token_value(text, "waiver_reason") or ""):
        return False
    if is_noneish(extract_inline_token_value(text, "compensating_verification") or ""):
        return False
    return True


def goal_completion_evidence_has_implementation_authority(evidence: object, run_dir: Path) -> bool:
    text = clean_value(str(evidence))
    authority_ref = extract_inline_token_value(text, "implementation_authority_ref")
    authority_path = resolve_run_scoped_ref(authority_ref, run_dir)
    if authority_path is None:
        return False
    try:
        relative = authority_path.resolve().relative_to(run_dir.resolve()).as_posix().lower()
    except ValueError:
        return False
    return relative in {"revised-plan.md", "handoff.md"} or relative.startswith("implementation-authority/")


def looks_like_sha256_digest(value: object) -> bool:
    text = clean_value(str(value)).lower()
    return bool(re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", text))


def normalize_sha256_digest(value: object) -> str:
    text = clean_value(str(value)).lower()
    if text.startswith("sha256:"):
        return text.split(":", 1)[1]
    return text


def file_sha256_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def looks_like_nonnegative_integer(value: object) -> bool:
    text = clean_value(str(value))
    return bool(re.fullmatch(r"\d+", text))


def proof_token_matches(proof_text: str, key: str, expected: str) -> bool:
    actual = extract_inline_token_value(proof_text, key)
    return actual is not None and clean_value(actual).lower() == clean_value(expected).lower()


def resolve_artifact_ref(value: str | None, run_dir: Path) -> Path | None:
    if value is None or is_placeholder_reference(value):
        return None
    text = clean_value(value)
    lowered = text.lower()
    if lowered.startswith("run://"):
        return resolve_run_scoped_ref(text[6:], run_dir)
    if lowered.startswith("file://"):
        return resolve_run_scoped_ref(text[7:], run_dir)
    if "://" in lowered:
        return None
    return resolve_run_scoped_ref(text, run_dir)


def read_record_text(path: Path | None) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def reject_json_constant(value: str) -> object:
    raise ValueError(f"invalid JSON constant: {value}")


def reject_nonfinite_json_numbers(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    if isinstance(value, dict):
        for nested in value.values():
            reject_nonfinite_json_numbers(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_nonfinite_json_numbers(nested)
    return value


def read_record_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(
            path.read_text(encoding="utf-8-sig", errors="ignore"),
            object_pairs_hook=reject_duplicate_json_pairs,
            parse_constant=reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        return None
    try:
        reject_nonfinite_json_numbers(data)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def canonical_json_alias_key(key: str) -> str:
    text = key.replace("-", "_")
    text = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", text)
    text = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_").lower()


def reject_duplicate_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    alias_seen: dict[str, str] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        alias_key = canonical_json_alias_key(key)
        if alias_key in alias_seen:
            raise ValueError(f"duplicate JSON key alias: {alias_seen[alias_key]} / {key}")
        alias_seen[alias_key] = key
        result[key] = value
    return result


def loads_strict_json_object(text: str) -> dict[str, object] | None:
    try:
        data = json.loads(
            text,
            object_pairs_hook=reject_duplicate_json_pairs,
            parse_constant=reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        return None
    try:
        reject_nonfinite_json_numbers(data)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def camelize_key(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def record_value(path: Path | None, key: str) -> str:
    data = read_record_json(path)
    if data is not None:
        candidates = [key, camelize_key(key), key.replace("_", "-")]
        for candidate in candidates:
            if candidate in data:
                value = data[candidate]
                if isinstance(value, bool):
                    return "true" if value else "false"
                return clean_value(str(value))
    return extract_artifact_field(read_record_text(path), key)


def record_value_matches(path: Path | None, key: str, expected: object) -> bool:
    return clean_value(record_value(path, key)).lower() == clean_value(str(expected)).lower()


def record_truthy(path: Path | None, key: str) -> bool:
    return clean_value(record_value(path, key)).lower() in {"true", "yes", "1", "allow", "allowed", "pass", "passed"}


def record_json_get(data: dict[str, object] | None, key: str) -> object | None:
    if data is None:
        return None
    for candidate in (key, camelize_key(key), key.replace("_", "-")):
        if candidate in data:
            return data[candidate]
    return None


def json_semantic_alias_present(data: dict[str, object], key: str) -> bool:
    return any(candidate in data for candidate in (key, camelize_key(key), key.replace("_", "-")))


def json_semantic_alias_conflict(data: dict[str, object], keys: tuple[str, ...]) -> bool:
    return sum(1 for key in keys if json_semantic_alias_present(data, key)) > 1


def json_value_text(data: dict[str, object] | None, key: str) -> str:
    value = record_json_get(data, key)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return ""
    return clean_value(str(value))


def json_value_matches(data: dict[str, object] | None, key: str, expected: object) -> bool:
    return json_value_text(data, key).lower() == clean_value(str(expected)).lower()


def json_digest_matches(data: dict[str, object] | None, key: str, expected: object) -> bool:
    actual = json_value_text(data, key)
    return looks_like_sha256_digest(actual) and normalize_sha256_digest(actual) == normalize_sha256_digest(expected)


def normalized_in_run_artifact_ref(value: str | None, run_dir: Path) -> str:
    path = resolve_artifact_ref(value, run_dir)
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(run_dir.resolve()).as_posix().lower()
    except ValueError:
        return ""


def authority_record_conflict_errors(run_dir: Path) -> list[str]:
    canonical = run_dir / "authority" / "run-authority.json"
    legacy = run_dir / "run-authority.json"
    if canonical.exists() and legacy.exists() and canonical.resolve() != legacy.resolve():
        return ["v3 authority handoff must not have conflicting authority/run-authority.json and run-authority.json"]
    return []


def current_v3_authority_record_path(run_dir: Path, selected_authority_path: Path | None = None) -> Path | None:
    if selected_authority_path is not None and read_record_json(selected_authority_path) is not None:
        return selected_authority_path
    for candidate in (run_dir / "authority" / "run-authority.json", run_dir / "run-authority.json"):
        if read_record_json(candidate) is not None:
            return candidate
    return None


def artifact_binds_current_v3_snapshot(text: str, run_dir: Path, authority_path: Path | None = None) -> bool:
    authority_path = current_v3_authority_record_path(run_dir, selected_authority_path=authority_path)
    if authority_path is None:
        return True
    required = {
        "source_digest": compute_source_digest(run_dir),
        "stage_graph_digest": file_sha256_digest(run_dir / "revised-plan.md") if (run_dir / "revised-plan.md").exists() else "",
        "authority_revision": record_value(authority_path, "authority_revision"),
        "authority_epoch": record_value(authority_path, "authority_epoch"),
    }
    for key, expected in required.items():
        if is_noneish(expected) or not artifact_field_equals(text, key, expected):
            return False
    for key in (
        "completion_subject_type",
        "completion_subject_digest",
        "authority_record_ref",
        "adapter_manifest_ref",
        "adapter_effective_config_digest",
    ):
        expected = record_value(authority_path, key)
        if expected and not artifact_field_equals(text, key, expected):
            return False
    return True


def cas_transition_receipt_is_valid(
    path: Path | None,
    *,
    run_dir: Path,
    authority_record_ref: str,
    authority_path: Path | None,
    run_authority_revision: str,
    run_authority_epoch: str,
) -> bool:
    if path is None or authority_path is None:
        return False
    text = read_record_text(path)
    if has_duplicate_artifact_fields(text, tuple([
        "authority_transition_receipt_version",
        "transition",
        "result",
        "pre_status",
        "post_status",
        "authority_record_ref",
        "authority_revision",
        "authority_epoch",
        "pre_authority_ref",
        "pre_authority_digest",
        "post_authority_digest",
    ])):
        return False
    required_fields = {
        "authority_transition_receipt_version": REQUIRED_CAS_TRANSITION_RECEIPT_VERSION,
        "transition": "active_to_completed",
        "result": "success",
        "pre_status": "active",
        "post_status": "completed",
        "authority_record_ref": authority_record_ref,
        "authority_revision": run_authority_revision,
        "authority_epoch": run_authority_epoch,
    }
    for key, expected in required_fields.items():
        if not record_value_matches(path, key, expected):
            return False
    pre_digest = record_value(path, "pre_authority_digest")
    post_digest = record_value(path, "post_authority_digest")
    pre_authority_ref = record_value(path, "pre_authority_ref")
    pre_authority_path = resolve_artifact_ref(pre_authority_ref, run_dir)
    if not looks_like_sha256_digest(pre_digest) or not looks_like_sha256_digest(post_digest):
        return False
    if pre_authority_path is None or read_record_json(pre_authority_path) is None:
        return False
    if normalize_sha256_digest(pre_digest) != file_sha256_digest(pre_authority_path):
        return False
    if not record_value_matches(pre_authority_path, "status", "active"):
        return False
    for key, expected in {
        "run_id": record_value(authority_path, "run_id"),
        "project_identity_digest": record_value(authority_path, "project_identity_digest"),
        "vcs_identity": record_value(authority_path, "vcs_identity"),
        "goal_digest": record_value(authority_path, "goal_digest"),
        "schema_version": record_value(authority_path, "schema_version"),
        "policy_version": record_value(authority_path, "policy_version"),
        "prompt_version": record_value(authority_path, "prompt_version"),
        "validator_version": record_value(authority_path, "validator_version"),
        "authority_revision": run_authority_revision,
        "authority_epoch": run_authority_epoch,
        "source_digest": record_value(authority_path, "source_digest"),
        "stage_graph_digest": record_value(authority_path, "stage_graph_digest"),
        "adapter_manifest_ref": record_value(authority_path, "adapter_manifest_ref"),
        "adapter_effective_config_digest": record_value(authority_path, "adapter_effective_config_digest"),
        "completion_subject_type": record_value(authority_path, "completion_subject_type"),
        "completion_subject_digest": record_value(authority_path, "completion_subject_digest"),
        "supersedes": record_value(authority_path, "supersedes"),
        "superseded_by": record_value(authority_path, "superseded_by"),
    }.items():
        if expected and not record_value_matches(pre_authority_path, key, expected):
            return False
    if normalize_sha256_digest(post_digest) != file_sha256_digest(authority_path):
        return False
    if normalize_sha256_digest(pre_digest) == normalize_sha256_digest(post_digest):
        return False
    return True


def adapter_manifest_validation_errors(
    *,
    manifest_path: Path | None,
    manifest_ref: str,
    expected_digest: str,
    run_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if manifest_path is None:
        return ["adapter_manifest_ref must resolve to an existing in-run adapter manifest artifact"]
    if normalize_sha256_digest(expected_digest) != file_sha256_digest(manifest_path):
        errors.append("adapter_effective_config_digest must match sha256(adapter_manifest_ref)")
    manifest = read_record_json(manifest_path)
    if manifest is None:
        errors.append("adapter_manifest_ref must be a JSON adapter manifest")
        return errors

    override = record_json_get(manifest, "agent_loop_override")
    override_status = (
        json_value_text(manifest, "agent_loop_override_status")
        or json_value_text(manifest, "override_validation_status")
        or "none"
    ).lower()
    if override is None:
        override = {}
    if not isinstance(override, dict):
        errors.append("adapter manifest agent_loop_override must be an object when present")
        return errors
    unknown = sorted(str(key) for key in override.keys() if str(key) not in ALLOWED_ADAPTER_OVERRIDE_KEYS)
    if unknown:
        errors.append(f"adapter manifest has non-allowlisted agent_loop_override keys: {', '.join(unknown)}")
    if override and override_status != "validated":
        errors.append("adapter manifest with agent_loop_override entries must record agent_loop_override_status=validated")
    if not override and override_status not in {"none", "not_present", "no_overrides", "validated"}:
        errors.append("adapter manifest override status must be none/not_present/no_overrides/validated")
    if manifest_ref.lower().startswith("run://") and json_value_text(manifest, "manifest_ref"):
        if json_value_text(manifest, "manifest_ref").lower() != manifest_ref.lower():
            errors.append("adapter manifest manifest_ref must match handoff adapter_manifest_ref")
    project_policy_refs = record_json_get(manifest, "project_policy_refs")
    if project_policy_refs is not None:
        if not isinstance(project_policy_refs, list):
            errors.append("adapter manifest project_policy_refs must be a list when present")
        else:
            repo_root = repo_root_for_run_dir(run_dir)
            for ref in project_policy_refs:
                ref_token = re.sub(r"\s+", "", clean_value(str(ref)).lower())
                if ref_token not in OPTIONAL_PROJECT_POLICY_REF_TOKENS:
                    errors.append(f"adapter manifest has unsupported project_policy_refs entry: {ref}")
                elif ref_token == "agents.md#loopcompletiongate" and (
                    repo_root is None or not (repo_root / "AGENTS.md").exists()
                ):
                    errors.append("adapter manifest project_policy_refs AGENTS.md#LoopCompletionGate must resolve under bound repo root")
    return errors


def telemetry_required_for_fields(fields: dict[str, object]) -> bool:
    values = [
        clean_value(str(fields.get("stage_status", ""))),
        clean_value(str(fields.get("current_batch", ""))),
        fields.get("latest_evidence_summary", ""),
        fields.get("blocking_findings", ""),
        clean_value(str(fields.get("continue_exit_status", ""))),
        clean_value(str(fields.get("continue_exit_evidence", ""))),
        clean_value(str(fields.get("turn_exit_cause", ""))),
        clean_value(str(fields.get("turn_exit_evidence", ""))),
        clean_value(str(fields.get("next_mandatory_action", ""))),
    ]
    for value in values:
        for item in iter_flattened_text_values(value):
            if has_resource_telemetry_required_signal(item):
                return True
    return False


def has_resource_telemetry_required_signal(value: str) -> bool:
    has_ui_copy_context = contains_any_pattern(value, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS)
    segment_records = split_scheduling_signal_segment_records(value)
    segments = [segment for segment, _separator in segment_records]
    suppressed_segment_indexes = doc_or_copy_prefixed_segment_indexes(segment_records)
    if has_adjacent_resource_telemetry_signal(
        segments,
        has_ui_copy_context=has_ui_copy_context,
        suppressed_segment_indexes=suppressed_segment_indexes,
    ):
        return True
    for index, segment in enumerate(segments):
        if index in suppressed_segment_indexes:
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_EXPLICIT_DECISION_PATTERNS):
            return True
        if resource_telemetry_segment_is_real_scheduling_signal(segment, has_ui_copy_context=has_ui_copy_context):
            return True
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS):
            continue
        if has_ui_copy_context and contains_any_pattern(segment, RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_NON_SCHEDULING_CONTEXT_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_NEGATED_PATTERNS):
            continue
        if contains_any_pattern(segment, RESOURCE_TELEMETRY_REQUIRED_PATTERNS):
            return True
    return False


def has_resource_telemetry_real_scheduling_signal(value: str) -> bool:
    has_ui_copy_context = contains_any_pattern(value, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS)
    segment_records = split_scheduling_signal_segment_records(value)
    segments = [segment for segment, _separator in segment_records]
    suppressed_segment_indexes = doc_or_copy_prefixed_segment_indexes(segment_records)
    if has_adjacent_resource_telemetry_signal(
        segments,
        has_ui_copy_context=has_ui_copy_context,
        suppressed_segment_indexes=suppressed_segment_indexes,
    ):
        return True
    for index, segment in enumerate(segments):
        if index in suppressed_segment_indexes:
            continue
        if resource_telemetry_segment_is_real_scheduling_signal(segment, has_ui_copy_context=has_ui_copy_context):
            return True
    return False


def has_adjacent_resource_telemetry_signal(
    segments: list[str],
    *,
    has_ui_copy_context: bool,
    suppressed_segment_indexes: set[int] | None = None,
) -> bool:
    actor_patterns = [
        r"\bspawn_agent\b",
        r"\bdelegated[- ]agent\b",
        r"\bdelegated\b",
        r"\bdispatch\b",
        r"\bcontroller\b",
        r"\bchallenge\b",
        r"\bagent\b",
        r"\bprocess\b",
    ]
    quota_patterns = [
        r"\bquota\b",
        r"\busage\s+limits?\b",
        r"\bcredits?\b",
        r"\brate[-\s]?limits?\b",
        r"\btool[-\s]?limits?\b",
        r"\bresource[-\s]?busy\b",
    ]
    return has_adjacent_delegated_quota_blocker_signal(
        segments,
        actor_patterns=actor_patterns,
        quota_patterns=quota_patterns,
        has_ui_copy_context=has_ui_copy_context,
        suppressed_segment_indexes=suppressed_segment_indexes,
    )


def resource_telemetry_segment_is_real_scheduling_signal(segment: str, *, has_ui_copy_context: bool) -> bool:
    if not contains_any_pattern(segment, RESOURCE_TELEMETRY_REAL_SCHEDULING_PATTERNS):
        return False
    if contains_any_pattern(segment, RESOURCE_TELEMETRY_UI_COPY_ONLY_CONTEXT_PATTERNS):
        return False
    if contains_any_pattern(segment, RESOURCE_TELEMETRY_NON_SCHEDULING_CONTEXT_PATTERNS):
        return False
    if has_ui_copy_context and contains_any_pattern(segment, RESOURCE_TELEMETRY_AMBIGUOUS_COPY_LABEL_PATTERNS):
        return False
    if contains_any_pattern(segment, RESOURCE_TELEMETRY_REAL_SCHEDULING_NEGATED_PATTERNS):
        return False
    if contains_any_pattern(segment, RESOURCE_TELEMETRY_NEGATED_PATTERNS):
        return False
    return True


def resource_telemetry_validation_errors(path: Path | None, *, required: bool, ref: str = "") -> list[str]:
    if path is None:
        return ["resource_telemetry_ref is required for resource/quota/tool-limit scheduling changes"] if required else []
    if clean_value(ref).lower() != "run://telemetry/resource-events.jsonl":
        return ["resource_telemetry_ref must use canonical run://telemetry/resource-events.jsonl"]
    if not path.exists() or not path.is_file():
        return ["resource_telemetry_ref must resolve to an existing in-run JSONL artifact"]
    errors: list[str] = []
    valid_relevant_event = False
    for index, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        event = loads_strict_json_object(line)
        if event is None:
            errors.append(f"resource telemetry line {index} must be valid JSON")
            continue
        required_fields = {
            "telemetry_schema_version": "resource-telemetry-v1",
            "event_id": None,
            "observed_at": None,
            "event_type": None,
            "affected_action": None,
            "decision_impact": None,
            "next_action": None,
        }
        for key, expected in required_fields.items():
            value = event.get(key)
            if not isinstance(value, str):
                errors.append(f"resource telemetry line {index} requires scalar string {key}")
                continue
            if expected is None:
                if is_noneish(value):
                    errors.append(f"resource telemetry line {index} requires {key}")
            elif clean_value(value).lower() != expected:
                errors.append(f"resource telemetry line {index} requires {key}={expected}")
        event_type = clean_value(event.get("event_type", "") if isinstance(event.get("event_type"), str) else "").lower()
        if event_type and event_type not in RESOURCE_TELEMETRY_EVENT_TYPES:
            errors.append(f"resource telemetry line {index} has unsupported event_type={event_type}")
        decision_impact = event.get("decision_impact")
        if event_type in RESOURCE_TELEMETRY_EVENT_TYPES and isinstance(decision_impact, str) and not is_noneish(decision_impact):
            valid_relevant_event = True
    if required and not valid_relevant_event:
        errors.append("resource_telemetry_ref must contain at least one relevant event with decision_impact")
    return errors


def research_dispatch_receipt_is_valid(
    path: Path | None,
    *,
    lane: str,
    research_cycle_id: str,
    source_digest: str,
    run_authority_revision: str,
    run_authority_epoch: str,
    agent_id: str,
    expected_model_slug: str,
    expected_reasoning_effort: str,
) -> bool:
    if path is None:
        return False
    text = read_record_text(path)
    if has_duplicate_artifact_fields(text, CRITICAL_RESEARCH_DISPATCH_FIELDS):
        return False
    required_fields = {
        "dispatch_receipt_version": "v1",
        "phase": REQUIRED_RESEARCH_DISPATCH_PHASE,
        "agent_role": "research_agent",
        "research_lane": lane,
        "research_cycle_id": research_cycle_id,
        "agent_id": agent_id,
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "authority_revision_at_dispatch": run_authority_revision,
        "authority_epoch_at_dispatch": run_authority_epoch,
        "model_policy": REQUIRED_DELEGATED_MODEL_POLICY,
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    if extract_artifact_field(text, "route_context").lower() == REQUIRED_FINAL_POLICY_ROUTE_CONTEXT:
        return False
    if is_placeholder_reference(extract_artifact_field(text, "model_resolution_basis_ref")):
        return False
    if clean_value(extract_artifact_field(text, "spawn_tool_args_model")).lower() != clean_value(expected_model_slug).lower():
        return False
    if (
        clean_value(extract_artifact_field(text, "spawn_tool_args_reasoning_effort")).lower()
        != clean_value(expected_reasoning_effort).lower()
    ):
        return False
    resolved_model_slug = clean_value(extract_artifact_field(text, "resolved_model_slug"))
    resolved_reasoning_effort = clean_value(extract_artifact_field(text, "resolved_reasoning_effort"))
    if resolved_model_slug and resolved_model_slug.lower() != clean_value(expected_model_slug).lower():
        return False
    if resolved_reasoning_effort and resolved_reasoning_effort.lower() != clean_value(expected_reasoning_effort).lower():
        return False
    return True


def challenge_cycle_lane_set_errors(
    *,
    lanes: object,
    lane_field_name: str,
    required_phase: str,
    cycle_id: str,
    source_digest: str,
    authority_record_ref: str,
    run_authority_revision: str,
    run_authority_epoch: str,
    refs_to_match: list[str] | None,
    run_dir: Path,
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    if not isinstance(lanes, list):
        return [f"challenge_cycle_ref must record {lane_field_name} as a list"], set()

    required_challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES.get(required_phase)
    if not required_challenge_mode:
        return [f"challenge_cycle_ref has unsupported phase for {lane_field_name}: {required_phase}"], set()

    seen_lanes: set[str] = set()
    cycle_artifact_refs: set[str] = set()
    agent_ids: set[str] = set()
    model_mix_counts: dict[tuple[str, str], int] = {}
    for item in lanes:
        if not isinstance(item, dict):
            errors.append(f"challenge_cycle {lane_field_name} entries must be objects")
            continue
        if json_semantic_alias_conflict(item, ("lane", "lane_name", "viewpoint")):
            errors.append(f"challenge_cycle {lane_field_name} entry has conflicting lane aliases")
            continue
        if json_semantic_alias_conflict(item, ("verdict", "vote")):
            errors.append(f"challenge_cycle {lane_field_name} entry has conflicting verdict aliases")
            continue
        if json_semantic_alias_conflict(item, ("artifact_ref", "lane_artifact_ref", "ref")):
            errors.append(f"challenge_cycle {lane_field_name} entry has conflicting artifact ref aliases")
            continue
        lane = (
            json_value_text(item, "lane")
            or json_value_text(item, "lane_name")
            or json_value_text(item, "viewpoint")
        ).lower()
        verdict = (json_value_text(item, "verdict") or json_value_text(item, "vote")).lower()
        if lane not in REQUIRED_STOP_LANES:
            errors.append(f"challenge_cycle {lane_field_name} lane has invalid or missing lane name: {lane or '<missing>'}")
            continue
        if lane in seen_lanes:
            errors.append(f"challenge_cycle {lane_field_name} lane is duplicated: {lane}")
        seen_lanes.add(lane)
        if verdict != "allow":
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must have verdict=allow")
        artifact_ref = (
            json_value_text(item, "artifact_ref")
            or json_value_text(item, "lane_artifact_ref")
            or json_value_text(item, "ref")
        )
        artifact_path = resolve_artifact_ref(artifact_ref, run_dir)
        if artifact_path is None:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must reference an existing in-run lane artifact")
            continue
        normalized_ref = normalized_in_run_artifact_ref(artifact_ref, run_dir)
        if normalized_ref:
            cycle_artifact_refs.add(normalized_ref)
        artifact_text = read_record_text(artifact_path)
        if has_duplicate_artifact_fields(artifact_text, CRITICAL_PROOF_ARTIFACT_FIELDS):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact has duplicate critical field")
            continue
        if extract_artifact_field(artifact_text, "phase").lower() != required_phase:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact phase mismatch")
        if extract_artifact_field(artifact_text, "agent_role").lower() != REQUIRED_FINAL_CHALLENGE_AGENT_ROLE:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must record agent_role={REQUIRED_FINAL_CHALLENGE_AGENT_ROLE}")
        if extract_artifact_field(artifact_text, "challenge_review_mode").lower() != required_challenge_mode:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact challenge_review_mode mismatch")
        if extract_artifact_field(artifact_text, "viewpoint").lower() != lane:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact viewpoint mismatch")
        if not artifact_alias_values_are_allowed(artifact_text, ("vote", "verdict"), {"allow"}):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must record vote=allow without conflicting verdict aliases")
        coverage_text = extract_artifact_field(artifact_text, "coverage_viewpoints") or extract_artifact_field(
            artifact_text,
            "covered_viewpoints",
        )
        if not pipe_value_set_is_exact(coverage_text, REQUIRED_STOP_LANE_COVERAGE[lane]):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact coverage_viewpoints mismatch")
        if not final_audit_artifact_is_valid(artifact_text, run_dir, required_phase):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact final audit metadata is invalid")
        if not is_placeholder_reference(cycle_id) and extract_artifact_field(artifact_text, "challenge_cycle_id").lower() != cycle_id.lower():
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must bind challenge_cycle_id={cycle_id}")
        if extract_artifact_field(artifact_text, "source_digest").lower() != source_digest.lower():
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must bind source_digest={source_digest}")

        agent_id = extract_artifact_field(artifact_text, "agent_id").lower()
        if not agent_id:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must record agent_id")
        elif agent_id in agent_ids:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact agent_id is duplicated")
        else:
            agent_ids.add(agent_id)
        model_slug = clean_value(extract_artifact_field(artifact_text, "resolved_model_slug"))
        reasoning_effort = clean_value(extract_artifact_field(artifact_text, "resolved_reasoning_effort"))
        if not delegated_model_is_allowed(model_slug, reasoning_effort):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must use allowed delegated model/effort")
        else:
            key = delegated_lane_model_key(model_slug, reasoning_effort)
            model_mix_counts[key] = model_mix_counts.get(key, 0) + 1
        if extract_artifact_field(artifact_text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must record model_policy={REQUIRED_DELEGATED_MODEL_POLICY}")
        if is_placeholder_reference(extract_artifact_field(artifact_text, "model_resolution_basis_ref")):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must record model_resolution_basis_ref")
        if extract_artifact_field(artifact_text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must record spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}")
        if clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_model")).lower() != model_slug.lower():
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} spawn_tool_args_model must match resolved_model_slug")
        if clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_reasoning_effort")).lower() != reasoning_effort.lower():
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} spawn_tool_args_reasoning_effort must match resolved_reasoning_effort")

        artifact_round_id = extract_artifact_field(artifact_text, "challenge_round_id")
        artifact_closeout_round_id = extract_artifact_field(artifact_text, "closeout_round_id")
        if is_placeholder_reference(artifact_round_id):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must record challenge_round_id")
        if is_placeholder_reference(artifact_closeout_round_id):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} artifact must record closeout_round_id")

        spawn_tool_call_ref = extract_artifact_field(artifact_text, "spawn_tool_call_ref")
        if is_placeholder_reference(spawn_tool_call_ref):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} must record spawn_tool_call_ref")
            continue
        dispatch_path = resolve_artifact_ref(spawn_tool_call_ref, run_dir)
        if dispatch_path is None:
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} spawn_tool_call_ref must resolve to an in-run dispatch receipt")
            continue
        if not dispatch_receipt_is_valid(
            dispatch_path,
            run_dir=run_dir,
            required_phase=required_phase,
            challenge_round_id=artifact_round_id,
            closeout_round_id=artifact_closeout_round_id,
            source_digest=source_digest,
            viewpoint=lane,
            agent_id=agent_id,
            expected_model_slug=model_slug,
            expected_reasoning_effort=reasoning_effort,
            expected_challenge_cycle_id=None if is_placeholder_reference(cycle_id) else cycle_id,
            expected_authority_record_ref=authority_record_ref,
            expected_authority_revision=run_authority_revision,
            expected_authority_epoch=run_authority_epoch,
        ):
            errors.append(f"challenge_cycle {lane_field_name} lane {lane} dispatch receipt is invalid or mismatched")

    if seen_lanes != REQUIRED_STOP_LANES:
        missing = ", ".join(sorted(REQUIRED_STOP_LANES - seen_lanes))
        extra = ", ".join(sorted(seen_lanes - REQUIRED_STOP_LANES))
        detail = "; ".join(part for part in (f"missing: {missing}" if missing else "", f"extra: {extra}" if extra else "") if part)
        errors.append(f"challenge_cycle {lane_field_name} must exactly cover required final lane set ({detail})")
    if model_mix_counts != REQUIRED_DELEGATED_MODEL_MIX:
        errors.append(f"challenge_cycle {lane_field_name} lanes must use the required five-lane model mix")
    if refs_to_match is not None:
        aggregate_refs = {normalized_in_run_artifact_ref(ref, run_dir) for ref in refs_to_match}
        aggregate_refs.discard("")
        if aggregate_refs != cycle_artifact_refs:
            aggregate_label = "goal_completion_evidence refs" if lane_field_name == "lanes" else "stop_consensus_evidence refs"
            errors.append(f"{aggregate_label} must exactly match challenge_cycle {lane_field_name} artifact refs")
    return errors, cycle_artifact_refs


def challenge_cycle_validation_errors(
    *,
    cycle_path: Path | None,
    challenge_cycle_digest_set: str,
    authority_record_ref: str,
    authority_path: Path | None,
    run_authority_revision: str,
    run_authority_epoch: str,
    source_digest: str,
    stage_graph_digest: str,
    adapter_manifest_ref: str,
    adapter_effective_config_digest: str,
    completion_subject_type: str,
    completion_subject_ref: str,
    completion_subject_digest: str,
    composite_subject_digest: str,
    goal_completion_refs: list[str] | None,
    stop_consensus_refs: list[str] | None,
    run_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if cycle_path is None:
        return ["challenge_cycle_ref must resolve to an existing in-run challenge cycle artifact"]
    if normalize_sha256_digest(challenge_cycle_digest_set) != file_sha256_digest(cycle_path):
        errors.append("challenge_cycle_digest_set must match sha256(challenge_cycle_ref)")
    cycle = read_record_json(cycle_path)
    if cycle is None:
        errors.append("challenge_cycle_ref must be a JSON challenge-cycle artifact")
        return errors

    required_scalar_matches = {
        "authority_record_ref": authority_record_ref,
        "authority_revision_at_dispatch": run_authority_revision,
        "authority_epoch_at_dispatch": run_authority_epoch,
    }
    for key, expected in required_scalar_matches.items():
        if not json_value_matches(cycle, key, expected):
            errors.append(f"challenge_cycle_ref must record {key}={expected}")
    if not json_value_matches(cycle, "all_lanes_allow", "true"):
        errors.append("challenge_cycle_ref must record all_lanes_allow=true")
    if json_value_text(cycle, "challenge_cycle_schema_version") != REQUIRED_CHALLENGE_CYCLE_SCHEMA_VERSION:
        errors.append(f"challenge_cycle_ref must record challenge_cycle_schema_version={REQUIRED_CHALLENGE_CYCLE_SCHEMA_VERSION}")
    cycle_id = json_value_text(cycle, "cycle_id")
    if is_placeholder_reference(cycle_id):
        errors.append("challenge_cycle_ref must record a concrete cycle_id")

    for key in ("schema_version", "policy_version", "prompt_version", "validator_version"):
        expected = record_value(authority_path, key)
        if is_noneish(expected):
            errors.append(f"authority_record_ref must record {key} for challenge-cycle version matching")
        elif not json_value_matches(cycle, key, expected):
            errors.append(f"challenge_cycle_ref must record {key} matching authority_record_ref")

    digest_set = record_json_get(cycle, "reviewed_digest_set")
    if not isinstance(digest_set, dict):
        errors.append("challenge_cycle_ref must record reviewed_digest_set object")
        digest_set = {}
    digest_matches = {
        "source_digest": source_digest,
        "stage_graph_digest": stage_graph_digest,
        "adapter_effective_config_digest": adapter_effective_config_digest,
        "completion_subject_digest": completion_subject_digest,
    }
    for key, expected in digest_matches.items():
        if not json_digest_matches(digest_set, key, expected):
            errors.append(f"challenge_cycle reviewed_digest_set must bind {key}={expected}")
    scalar_digest_set_matches = {
        "adapter_manifest_ref": adapter_manifest_ref,
        "completion_subject_type": completion_subject_type,
        "completion_subject_ref": completion_subject_ref,
    }
    for key, expected in scalar_digest_set_matches.items():
        if not json_value_matches(digest_set, key, expected):
            errors.append(f"challenge_cycle reviewed_digest_set must bind {key}={expected}")
    if looks_like_sha256_digest(composite_subject_digest):
        if not json_digest_matches(digest_set, "composite_subject_digest", composite_subject_digest):
            errors.append("challenge_cycle reviewed_digest_set must bind composite_subject_digest")

    lane_errors, _ = challenge_cycle_lane_set_errors(
        lanes=record_json_get(cycle, "lanes"),
        lane_field_name="lanes",
        required_phase="goal_completion",
        cycle_id=cycle_id,
        source_digest=source_digest,
        authority_record_ref=authority_record_ref,
        run_authority_revision=run_authority_revision,
        run_authority_epoch=run_authority_epoch,
        refs_to_match=goal_completion_refs,
        run_dir=run_dir,
    )
    errors.extend(lane_errors)
    if stop_consensus_refs is not None:
        stop_lane_errors, _ = challenge_cycle_lane_set_errors(
            lanes=record_json_get(cycle, "stop_lanes"),
            lane_field_name="stop_lanes",
            required_phase="stop_authorization",
            cycle_id=cycle_id,
            source_digest=source_digest,
            authority_record_ref=authority_record_ref,
            run_authority_revision=run_authority_revision,
            run_authority_epoch=run_authority_epoch,
            refs_to_match=stop_consensus_refs,
            run_dir=run_dir,
        )
        errors.extend(stop_lane_errors)
    return errors


def research_cycle_validation_errors(
    *,
    cycle_path: Path | None,
    research_cycle_digest_set: str,
    source_digest: str,
    run_authority_revision: str,
    run_authority_epoch: str,
    run_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if cycle_path is None:
        return ["research_cycle_ref must resolve to an existing in-run research cycle artifact"]
    if normalize_sha256_digest(research_cycle_digest_set) != file_sha256_digest(cycle_path):
        errors.append("research_cycle_digest_set must match sha256(research_cycle_ref)")
    cycle = read_record_json(cycle_path)
    if cycle is None:
        errors.append("research_cycle_ref must be a JSON research-cycle artifact")
        return errors
    cycle_id = json_value_text(cycle, "cycle_id")
    if is_placeholder_reference(cycle_id):
        errors.append("research_cycle_ref must record a concrete cycle_id")
    if json_value_text(cycle, "research_cycle_schema_version") != REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION:
        errors.append(f"research_cycle_ref must record research_cycle_schema_version={REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION}")
    if not json_value_matches(cycle, "source_digest", source_digest):
        errors.append("research_cycle_ref must record matching source_digest")
    if not json_value_matches(cycle, "authority_revision_at_dispatch", run_authority_revision):
        errors.append("research_cycle_ref must record matching authority_revision_at_dispatch")
    if not json_value_matches(cycle, "authority_epoch_at_dispatch", run_authority_epoch):
        errors.append("research_cycle_ref must record matching authority_epoch_at_dispatch")
    if not json_value_matches(cycle, "all_lanes_merged", "true"):
        errors.append("research_cycle_ref must record all_lanes_merged=true")
    lanes = record_json_get(cycle, "lanes")
    if not isinstance(lanes, list):
        errors.append("research_cycle_ref must record lanes as a list")
        return errors
    seen_lanes: set[str] = set()
    agent_ids: set[str] = set()
    model_mix_counts: dict[tuple[str, str], int] = {}
    for item in lanes:
        if not isinstance(item, dict):
            errors.append("research_cycle lanes entries must be objects")
            continue
        if json_semantic_alias_conflict(item, ("lane", "research_lane", "viewpoint")):
            errors.append("research_cycle lane entry has conflicting lane aliases")
            continue
        if json_semantic_alias_conflict(item, ("verdict", "vote")):
            errors.append("research_cycle lane entry has conflicting verdict aliases")
            continue
        if json_semantic_alias_conflict(item, ("artifact_ref", "lane_artifact_ref", "ref")):
            errors.append("research_cycle lane entry has conflicting artifact ref aliases")
            continue
        lane = (
            json_value_text(item, "lane")
            or json_value_text(item, "research_lane")
            or json_value_text(item, "viewpoint")
        ).lower()
        verdict = (json_value_text(item, "verdict") or json_value_text(item, "vote")).lower()
        if lane not in REQUIRED_INITIAL_RESEARCH_LANES:
            errors.append(f"research_cycle lane has invalid or missing lane name: {lane or '<missing>'}")
            continue
        if lane in seen_lanes:
            errors.append(f"research_cycle lane is duplicated: {lane}")
        seen_lanes.add(lane)
        if verdict not in {"allow", "pass", "merged"}:
            errors.append(f"research_cycle lane {lane} must have verdict=allow|pass|merged")
        artifact_ref = (
            json_value_text(item, "artifact_ref")
            or json_value_text(item, "lane_artifact_ref")
            or json_value_text(item, "ref")
        )
        artifact_path = resolve_artifact_ref(artifact_ref, run_dir)
        if artifact_path is None:
            errors.append(f"research_cycle lane {lane} must reference an existing in-run lane artifact")
            continue
        artifact_text = read_record_text(artifact_path)
        if has_duplicate_artifact_fields(artifact_text, CRITICAL_RESEARCH_ARTIFACT_FIELDS):
            errors.append(f"research_cycle lane {lane} artifact has duplicate critical field")
            continue
        artifact_lane_fields = [
            value
            for value in (
                extract_artifact_field(artifact_text, "research_lane"),
                extract_artifact_field(artifact_text, "viewpoint"),
            )
            if not is_noneish(value)
        ]
        if len(artifact_lane_fields) > 1:
            errors.append(f"research_cycle lane {lane} artifact has conflicting lane aliases")
            continue
        artifact_lane = (
            extract_artifact_field(artifact_text, "research_lane")
            or extract_artifact_field(artifact_text, "viewpoint")
        ).lower()
        if artifact_lane != lane:
            errors.append(f"research_cycle lane {lane} artifact lane mismatch")
        if not artifact_alias_values_are_allowed(artifact_text, ("vote", "verdict"), {"allow", "pass", "merged"}):
            errors.append(f"research_cycle lane {lane} artifact must record vote/verdict=allow|pass|merged")
        if extract_artifact_field(artifact_text, "agent_role").lower() != "research_agent":
            errors.append(f"research_cycle lane {lane} artifact must record agent_role=research_agent")
        if not is_placeholder_reference(cycle_id) and extract_artifact_field(artifact_text, "research_cycle_id").lower() != cycle_id.lower():
            errors.append(f"research_cycle lane {lane} artifact must bind research_cycle_id={cycle_id}")
        if extract_artifact_field(artifact_text, "source_digest").lower() != source_digest.lower():
            errors.append(f"research_cycle lane {lane} artifact must bind source_digest={source_digest}")
        if extract_artifact_field(artifact_text, "authority_revision_at_dispatch").lower() != run_authority_revision.lower():
            errors.append(f"research_cycle lane {lane} artifact must bind authority_revision_at_dispatch={run_authority_revision}")
        if extract_artifact_field(artifact_text, "authority_epoch_at_dispatch").lower() != run_authority_epoch.lower():
            errors.append(f"research_cycle lane {lane} artifact must bind authority_epoch_at_dispatch={run_authority_epoch}")
        agent_id = extract_artifact_field(artifact_text, "agent_id").lower()
        if not agent_id:
            errors.append(f"research_cycle lane {lane} artifact must record agent_id")
        elif agent_id in agent_ids:
            errors.append(f"research_cycle lane {lane} artifact agent_id is duplicated")
        else:
            agent_ids.add(agent_id)
        model_slug = clean_value(extract_artifact_field(artifact_text, "resolved_model_slug"))
        reasoning_effort = clean_value(extract_artifact_field(artifact_text, "resolved_reasoning_effort"))
        if not delegated_model_is_allowed(model_slug, reasoning_effort):
            errors.append(f"research_cycle lane {lane} must use allowed delegated model/effort")
        else:
            key = delegated_lane_model_key(model_slug, reasoning_effort)
            model_mix_counts[key] = model_mix_counts.get(key, 0) + 1
        if extract_artifact_field(artifact_text, "model_policy").lower() != REQUIRED_DELEGATED_MODEL_POLICY:
            errors.append(f"research_cycle lane {lane} must record model_policy={REQUIRED_DELEGATED_MODEL_POLICY}")
        if is_placeholder_reference(extract_artifact_field(artifact_text, "model_resolution_basis_ref")):
            errors.append(f"research_cycle lane {lane} must record model_resolution_basis_ref")
        if extract_artifact_field(artifact_text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            errors.append(f"research_cycle lane {lane} must record spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}")
        if clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_model")).lower() != model_slug.lower():
            errors.append(f"research_cycle lane {lane} spawn_tool_args_model must match resolved_model_slug")
        if clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_reasoning_effort")).lower() != reasoning_effort.lower():
            errors.append(f"research_cycle lane {lane} spawn_tool_args_reasoning_effort must match resolved_reasoning_effort")
        spawn_tool_call_ref = extract_artifact_field(artifact_text, "spawn_tool_call_ref")
        if is_placeholder_reference(spawn_tool_call_ref):
            errors.append(f"research_cycle lane {lane} must record spawn_tool_call_ref")
            continue
        dispatch_path = resolve_artifact_ref(spawn_tool_call_ref, run_dir)
        if not research_dispatch_receipt_is_valid(
            dispatch_path,
            lane=lane,
            research_cycle_id=cycle_id,
            source_digest=source_digest,
            run_authority_revision=run_authority_revision,
            run_authority_epoch=run_authority_epoch,
            agent_id=agent_id,
            expected_model_slug=model_slug,
            expected_reasoning_effort=reasoning_effort,
        ):
            errors.append(f"research_cycle lane {lane} dispatch receipt is invalid or mismatched")
    if seen_lanes != REQUIRED_INITIAL_RESEARCH_LANES:
        missing = ", ".join(sorted(REQUIRED_INITIAL_RESEARCH_LANES - seen_lanes))
        extra = ", ".join(sorted(seen_lanes - REQUIRED_INITIAL_RESEARCH_LANES))
        detail = "; ".join(part for part in (f"missing: {missing}" if missing else "", f"extra: {extra}" if extra else "") if part)
        errors.append(f"research_cycle lanes must exactly cover required initial research lane set ({detail})")
    if model_mix_counts != REQUIRED_DELEGATED_MODEL_MIX:
        errors.append("research_cycle lanes must use the required five-lane model mix")
    return errors


def validate_fields(
    fields: dict[str, object],
    run_dir: Path,
    require_consensus: bool,
    live_state: bool = False,
    resume_state: bool = False,
) -> list[str]:
    errors: list[str] = []

    for key in SCALAR_FIELDS:
        if key not in fields:
            errors.append(f"missing handoff field: {key}")
    for key in LIST_OR_SCALAR_FIELDS:
        if key not in fields:
            errors.append(f"missing handoff field: {key}")

    if errors:
        return errors

    for key, allowed in ENUMS.items():
        if key in OPTIONAL_SCALAR_FIELDS and key not in fields:
            continue
        value = clean_value(str(fields.get(key, "")))
        if key in OPTIONAL_SCALAR_FIELDS and is_noneish(value):
            continue
        if value not in allowed:
            errors.append(f"{key} must be one of {sorted(allowed)}, got: {value}")

    if errors:
        return errors

    run_decision = clean_value(str(fields["run_decision"]))
    loop_state = clean_value(str(fields["loop_state"]))
    continuation_mode = clean_value(str(fields["continuation_mode"]))
    closeout_round_id = clean_value(str(fields["closeout_round_id"]))
    host_resume_mode = clean_value(str(fields["host_resume_mode"]))
    sequential_status = clean_value(str(fields["sequential_objectives_status"]))
    stop_status = clean_value(str(fields["stop_authorization_status"]))
    stop_consensus_status = clean_value(str(fields["stop_consensus_status"]))
    stop_consensus_evidence_text = clean_value(str(fields["stop_consensus_evidence"]))
    external_basis = clean_value(str(fields["external_authority_basis"]))
    pause_reason = clean_value(str(fields["pause_reason"])).lower()
    stop_evidence = clean_value(str(fields["stop_authorization_evidence"])).lower()
    continue_exit_status = clean_value(str(fields["continue_exit_status"]))
    continue_exit_evidence = clean_value(str(fields["continue_exit_evidence"]))
    turn_exit_cause = clean_value(str(fields["turn_exit_cause"]))
    turn_exit_evidence = clean_value(str(fields["turn_exit_evidence"]))
    turn_exit_host_boundary_ref = extract_structured_value(turn_exit_evidence, "host_boundary_ref")
    goal_completion_status = clean_value(str(fields["goal_completion_status"]))
    goal_completion_evidence = clean_value(str(fields["goal_completion_evidence"]))
    capability_mode = clean_value(str(fields["capability_mode"]))
    stop_round_id = extract_challenge_round_id(fields["stop_consensus_evidence"])
    goal_round_id = extract_challenge_round_id(fields["goal_completion_evidence"])
    run_intent = clean_value(str(fields["run_intent"])).lower()
    host_boundary_pause = run_decision == "pause" and external_basis == "host_turn_boundary"
    host_boundary_continue = (
        run_decision == "continue"
        and host_resume_mode == "same_turn_only"
        and turn_exit_cause == "host_turn_boundary_pause"
    )
    explicit_user_stop_override = (
        run_decision == "stop"
        and stop_status == "external_authority"
        and external_basis == "explicit_user_stop"
    )
    live_continue_state = (
        live_state
        and run_decision == "continue"
        and loop_state not in {"paused", "stopped"}
        and turn_exit_cause == "not_applicable"
        and is_noneish(turn_exit_evidence)
    )
    resume_instructions_text = flatten_multivalue_text(fields["resume_instructions"]).lower()
    current_stage = clean_value(str(fields["current_or_next_stage"]))
    next_action = clean_value(str(fields["next_mandatory_action"]))
    risk_tier = clean_value(str(fields["risk_tier"]))
    implementation_gate_status = clean_value(str(fields["implementation_gate_status"]))
    implementation_gate_evidence = clean_value(str(fields["implementation_gate_evidence"]))
    handoff_path = run_dir / "handoff.md"
    remaining_required_stages = fields["remaining_required_stages"]
    blocking_findings_text = flatten_multivalue_text(fields["blocking_findings"])
    implementation_like_intent = run_intent in IMPLEMENTATION_INTENTS
    schema_version = clean_value(str(fields["handoff_schema_version"]))
    work_type = clean_value(str(fields.get("work_type", "not_classified"))).lower()
    review_kind = clean_value(str(fields.get("review_kind", "not_applicable"))).lower()
    authority_record_ref = clean_value(str(fields.get("authority_record_ref", "none")))
    run_authority_status = clean_value(str(fields.get("run_authority_status", "not_applicable"))).lower()
    run_authority_revision = clean_value(str(fields.get("run_authority_revision", "none")))
    run_authority_epoch = clean_value(str(fields.get("run_authority_epoch", "none")))
    source_digest_field = clean_value(str(fields.get("source_digest", "none")))
    stage_graph_digest = clean_value(str(fields.get("stage_graph_digest", "none")))
    adapter_manifest_ref = clean_value(str(fields.get("adapter_manifest_ref", "none")))
    adapter_conformance_status = clean_value(str(fields.get("adapter_conformance_status", "not_applicable"))).lower()
    adapter_effective_config_digest = clean_value(str(fields.get("adapter_effective_config_digest", "none")))
    resource_telemetry_ref = clean_value(str(fields.get("resource_telemetry_ref", "none")))
    research_cycle_ref = clean_value(str(fields.get("research_cycle_ref", "none")))
    research_cycle_status = clean_value(str(fields.get("research_cycle_status", "not_applicable"))).lower()
    research_cycle_digest_set = clean_value(str(fields.get("research_cycle_digest_set", "none")))
    completion_subject_type = clean_value(str(fields.get("completion_subject_type", "not_classified"))).lower()
    completion_subject_ref = clean_value(str(fields.get("completion_subject_ref", "none")))
    completion_subject_digest = clean_value(str(fields.get("completion_subject_digest", "none")))
    composite_subject_digest = clean_value(str(fields.get("composite_subject_digest", "none")))
    challenge_cycle_ref = clean_value(str(fields.get("challenge_cycle_ref", "none")))
    challenge_cycle_status = clean_value(str(fields.get("challenge_cycle_status", "not_applicable"))).lower()
    challenge_cycle_digest_set = clean_value(str(fields.get("challenge_cycle_digest_set", "none")))
    visible_output_contract = clean_value(str(fields.get("visible_output_contract", "not_applicable"))).lower()
    source_path = run_dir / "source.md"
    ideas_path = run_dir / REQUIRED_IDEAS_REF
    research_path = run_dir / "research.md"
    revised_plan_path = run_dir / "revised-plan.md"
    evidence_path = run_dir / "evidence.md"

    terminal_verified_stop = run_decision == "stop" and goal_completion_status == VERIFIED_COMPLETE_STATUS

    if terminal_verified_stop and not explicit_user_stop_override and schema_version != REQUIRED_AUTHORITY_SCHEMA_VERSION:
        errors.append(f"verified terminal stop requires handoff_schema_version={REQUIRED_AUTHORITY_SCHEMA_VERSION}")

    telemetry_required = telemetry_required_for_fields(fields)
    if telemetry_required or not is_noneish(resource_telemetry_ref):
        errors.extend(
            resource_telemetry_validation_errors(
                resolve_artifact_ref(resource_telemetry_ref, run_dir),
                required=telemetry_required,
                ref=resource_telemetry_ref,
            )
        )

    if schema_version == REQUIRED_AUTHORITY_SCHEMA_VERSION:
        required_v3_fields = [
            "work_type",
            "review_kind",
            "authority_record_ref",
            "run_authority_status",
            "run_authority_revision",
            "run_authority_epoch",
            "source_digest",
            "stage_graph_digest",
            "adapter_manifest_ref",
            "adapter_conformance_status",
            "adapter_effective_config_digest",
            "research_cycle_ref",
            "research_cycle_status",
            "research_cycle_digest_set",
            "completion_subject_type",
            "completion_subject_ref",
            "completion_subject_digest",
            "composite_subject_digest",
            "challenge_cycle_ref",
            "challenge_cycle_status",
            "challenge_cycle_digest_set",
            "visible_output_contract",
        ]
        for field in required_v3_fields:
            if field not in fields:
                errors.append(f"handoff_schema_version=v3-worktype-authority requires handoff field: {field}")
        if work_type == "not_classified":
            errors.append("handoff_schema_version=v3-worktype-authority requires a concrete work_type")
        if work_type == "review" and review_kind == "not_applicable":
            errors.append("work_type=review requires concrete review_kind")
        if work_type != "review" and review_kind != "not_applicable":
            errors.append("review_kind must be not_applicable unless work_type=review")
        if is_noneish(authority_record_ref):
            errors.append("v3 authority handoff requires authority_record_ref")
        elif authority_record_ref.lower() not in {"run://authority/run-authority.json", "run://run-authority.json"}:
            errors.append("v3 authority_record_ref must be run://authority/run-authority.json or run://run-authority.json")
        if run_authority_status == "not_applicable":
            errors.append("v3 authority handoff requires concrete run_authority_status")
        if not looks_like_nonnegative_integer(run_authority_revision):
            errors.append("v3 authority handoff requires numeric run_authority_revision")
        if not looks_like_nonnegative_integer(run_authority_epoch):
            errors.append("v3 authority handoff requires numeric run_authority_epoch")
        if not looks_like_sha256_digest(source_digest_field):
            errors.append("v3 authority handoff requires sha256 source_digest")
        if not looks_like_sha256_digest(stage_graph_digest):
            errors.append("v3 authority handoff requires sha256 stage_graph_digest")
        if revised_plan_path.exists() and looks_like_sha256_digest(stage_graph_digest):
            actual_stage_graph_digest = file_sha256_digest(revised_plan_path)
            if normalize_sha256_digest(stage_graph_digest) != actual_stage_graph_digest:
                errors.append("stage_graph_digest does not match sha256(revised-plan.md)")
        if is_noneish(adapter_manifest_ref):
            errors.append("v3 authority handoff requires adapter_manifest_ref")
        if adapter_conformance_status == "not_applicable":
            errors.append("v3 authority handoff requires concrete adapter_conformance_status")
        if not looks_like_sha256_digest(adapter_effective_config_digest):
            errors.append("v3 authority handoff requires sha256 adapter_effective_config_digest")
        if research_cycle_status == "allow_unanimous" and (
            is_noneish(research_cycle_ref) or not looks_like_sha256_digest(research_cycle_digest_set)
        ):
            errors.append("research_cycle_status=allow_unanimous requires research_cycle_ref and sha256 research_cycle_digest_set")
        if completion_subject_type == "not_classified":
            errors.append("v3 authority handoff requires concrete completion_subject_type")
        allowed_subject_types = WORK_TYPE_COMPLETION_SUBJECT_TYPES.get(work_type, set())
        if allowed_subject_types and completion_subject_type not in allowed_subject_types:
            errors.append(
                f"work_type={work_type} requires completion_subject_type in {sorted(allowed_subject_types)}"
            )
        expected_review_subject_type = REVIEW_KIND_COMPLETION_SUBJECT_TYPES.get(review_kind)
        if expected_review_subject_type and completion_subject_type != expected_review_subject_type:
            errors.append(f"review_kind={review_kind} requires completion_subject_type={expected_review_subject_type}")
        if is_noneish(completion_subject_ref):
            errors.append("v3 authority handoff requires completion_subject_ref")
        if not looks_like_sha256_digest(completion_subject_digest):
            errors.append("v3 authority handoff requires sha256 completion_subject_digest")
        if work_type == "mixed" and completion_subject_type != "composite_subject":
            errors.append("work_type=mixed requires completion_subject_type=composite_subject")
        if work_type == "mixed" and not looks_like_sha256_digest(composite_subject_digest):
            errors.append("work_type=mixed requires sha256 composite_subject_digest")
        if challenge_cycle_status == "allow_unanimous" and (
            is_noneish(challenge_cycle_ref) or not looks_like_sha256_digest(challenge_cycle_digest_set)
        ):
            errors.append("challenge_cycle_status=allow_unanimous requires challenge_cycle_ref and sha256 challenge_cycle_digest_set")
        if source_path.exists() and looks_like_sha256_digest(source_digest_field):
            actual_source_digest = compute_source_digest(run_dir)
            if normalize_sha256_digest(source_digest_field) != actual_source_digest:
                errors.append("source_digest does not match sha256(raw source.md bytes)")
        authority_path = resolve_artifact_ref(authority_record_ref, run_dir)
        errors.extend(authority_record_conflict_errors(run_dir))
        if authority_path is None:
            errors.append("authority_record_ref must resolve to an existing in-run authority artifact")
        elif read_record_json(authority_path) is None:
            errors.append("v3 authority_record_ref must be a JSON authority artifact")
        else:
            authority_expected = {
                "authority_revision": run_authority_revision,
                "authority_epoch": run_authority_epoch,
                "status": run_authority_status,
                "source_digest": source_digest_field,
                "stage_graph_digest": stage_graph_digest,
                "adapter_manifest_ref": adapter_manifest_ref,
                "adapter_conformance_status": adapter_conformance_status,
                "adapter_effective_config_digest": adapter_effective_config_digest,
            }
            for key, expected in authority_expected.items():
                if not record_value_matches(authority_path, key, expected):
                    errors.append(f"authority_record_ref must record {key}={expected}")
            for key, expected in {
                "schema_version": REQUIRED_AUTHORITY_SCHEMA_VERSION,
                "policy_version": REQUIRED_AUTHORITY_POLICY_VERSION,
                "prompt_version": REQUIRED_AUTHORITY_PROMPT_VERSION,
                "validator_version": REQUIRED_AUTHORITY_VALIDATOR_VERSION,
            }.items():
                if not record_value_matches(authority_path, key, expected):
                    errors.append(f"authority_record_ref must record {key}={expected}")
        adapter_manifest_path = resolve_artifact_ref(adapter_manifest_ref, run_dir)
        errors.extend(
            adapter_manifest_validation_errors(
                manifest_path=adapter_manifest_path,
                manifest_ref=adapter_manifest_ref,
                expected_digest=adapter_effective_config_digest,
                run_dir=run_dir,
            )
        )
        research_skip_authorized = is_research_skip_authorized(implementation_gate_evidence, run_dir, risk_tier)
        if research_cycle_status == "allow_unanimous":
            errors.extend(
                research_cycle_validation_errors(
                    cycle_path=resolve_artifact_ref(research_cycle_ref, run_dir),
                    research_cycle_digest_set=research_cycle_digest_set,
                    source_digest=source_digest_field,
                    run_authority_revision=run_authority_revision,
                    run_authority_epoch=run_authority_epoch,
                    run_dir=run_dir,
                )
            )
        elif (terminal_verified_stop or implementation_gate_status == "accepted") and not research_skip_authorized:
            errors.append("v3 terminal or accepted implementation state requires research_cycle_status=allow_unanimous")
        completion_subject_path = resolve_artifact_ref(completion_subject_ref, run_dir)
        if completion_subject_path is None:
            errors.append("completion_subject_ref must resolve to an existing in-run subject artifact")
        elif normalize_sha256_digest(completion_subject_digest) != file_sha256_digest(completion_subject_path):
            errors.append("completion_subject_digest must match sha256(completion_subject_ref)")
        if work_type == "mixed" and completion_subject_path is not None:
            if normalize_sha256_digest(composite_subject_digest) != file_sha256_digest(completion_subject_path):
                errors.append("composite_subject_digest must match sha256(completion_subject_ref) for mixed work")
        challenge_cycle_path = resolve_artifact_ref(challenge_cycle_ref, run_dir)
        if challenge_cycle_status == "allow_unanimous":
            errors.extend(
                challenge_cycle_validation_errors(
                    cycle_path=challenge_cycle_path,
                    challenge_cycle_digest_set=challenge_cycle_digest_set,
                    authority_record_ref=authority_record_ref,
                    authority_path=authority_path,
                    run_authority_revision=run_authority_revision,
                    run_authority_epoch=run_authority_epoch,
                    source_digest=source_digest_field,
                    stage_graph_digest=stage_graph_digest,
                    adapter_manifest_ref=adapter_manifest_ref,
                    adapter_effective_config_digest=adapter_effective_config_digest,
                    completion_subject_type=completion_subject_type,
                    completion_subject_ref=completion_subject_ref,
                    completion_subject_digest=completion_subject_digest,
                    composite_subject_digest=composite_subject_digest,
                    goal_completion_refs=extract_consensus_refs(goal_completion_evidence) if terminal_verified_stop else None,
                    stop_consensus_refs=extract_consensus_refs(stop_consensus_evidence_text) if terminal_verified_stop and stop_status == "allow" else None,
                    run_dir=run_dir,
                )
            )
        if run_decision == "continue" and visible_output_contract == "terminal_completion":
            errors.append("run_decision=continue may not use visible_output_contract=terminal_completion")
        if terminal_verified_stop:
            if visible_output_contract != "terminal_completion":
                errors.append("verified terminal stop requires visible_output_contract=terminal_completion")
            if adapter_conformance_status != "compatible":
                errors.append("verified terminal stop requires adapter_conformance_status=compatible")
            if run_authority_status != "completed":
                errors.append("verified terminal stop requires run_authority_status=completed after CAS completion")
            if challenge_cycle_status != "allow_unanimous":
                errors.append("verified terminal stop requires challenge_cycle_status=allow_unanimous")
            if is_noneish(challenge_cycle_ref):
                errors.append("verified terminal stop requires challenge_cycle_ref")
            if authority_path is not None:
                required_authority_identity_fields = [
                    "run_id",
                    "project_root_ref",
                    "project_identity_digest",
                    "vcs_identity",
                    "cwd_root_binding",
                    "goal_digest",
                    "source_digest",
                    "stage_graph_digest",
                    "schema_version",
                    "policy_version",
                    "prompt_version",
                    "validator_version",
                    "authority_revision",
                    "authority_epoch",
                    "last_writer_id",
                    "status",
                    "supersedes",
                    "superseded_by",
                    "cas_transition_ref",
                ]
                for key in required_authority_identity_fields:
                    value = record_value(authority_path, key)
                    if key in {"supersedes", "superseded_by"}:
                        if value == "":
                            errors.append(f"verified terminal stop authority record must have {key}")
                    elif is_noneish(value):
                        errors.append(f"verified terminal stop authority record must have {key}")
                if not record_value_matches(authority_path, "status", "completed"):
                    errors.append("verified terminal stop authority record must have status=completed")
                if not record_value_matches(authority_path, "cas_transition", "active_to_completed"):
                    errors.append("verified terminal stop authority record must record cas_transition=active_to_completed")
                if not record_value_matches(authority_path, "cas_result", "success"):
                    errors.append("verified terminal stop authority record must record cas_result=success")
                if not record_value_matches(authority_path, "cas_expected_status", "active"):
                    errors.append("verified terminal stop authority record must record cas_expected_status=active")
                if not record_value_matches(authority_path, "cas_target_status", "completed"):
                    errors.append("verified terminal stop authority record must record cas_target_status=completed")
                if not record_value_matches(authority_path, "cas_expected_authority_revision", run_authority_revision):
                    errors.append("verified terminal stop authority record must record matching cas_expected_authority_revision")
                if not record_value_matches(authority_path, "cas_expected_authority_epoch", run_authority_epoch):
                    errors.append("verified terminal stop authority record must record matching cas_expected_authority_epoch")
                cas_transition_ref = record_value(authority_path, "cas_transition_ref")
                cas_transition_path = resolve_artifact_ref(cas_transition_ref, run_dir)
                if not cas_transition_receipt_is_valid(
                    cas_transition_path,
                    run_dir=run_dir,
                    authority_record_ref=authority_record_ref,
                    authority_path=authority_path,
                    run_authority_revision=run_authority_revision,
                    run_authority_epoch=run_authority_epoch,
                ):
                    errors.append("verified terminal stop authority record must have a valid CAS transition receipt")
            for key, expected in {
                "authority_record_ref": authority_record_ref,
                "authority_revision": run_authority_revision,
                "authority_epoch": run_authority_epoch,
                "source_digest": source_digest_field,
                "adapter_manifest_ref": adapter_manifest_ref,
                "adapter_effective_config_digest": adapter_effective_config_digest,
                "completion_subject_type": completion_subject_type,
                "completion_subject_digest": completion_subject_digest,
                "stage_graph_digest": stage_graph_digest,
                "challenge_cycle_ref": challenge_cycle_ref,
                "challenge_cycle_digest_set": challenge_cycle_digest_set,
            }.items():
                if not proof_token_matches(goal_completion_evidence, key, expected):
                    errors.append(f"verified terminal stop goal_completion_evidence must bind {key}={expected}")
                if stop_status == "allow" and not proof_token_matches(stop_consensus_evidence_text, key, expected):
                    errors.append(f"verified terminal stop stop_consensus_evidence must bind {key}={expected}")
    if (
        implementation_like_intent
        and terminal_verified_stop
        and risk_tier in {"tier1_local", "tier2_material", "tier3_high_risk"}
        and implementation_gate_status != "accepted"
        and not explicit_user_stop_override
    ):
        errors.append("implementation verified terminal stops require implementation_gate_status=accepted")
    if (
        implementation_gate_status == "accepted"
        and not implementation_gate_mini_requirement_is_satisfied(
            implementation_gate_evidence,
            run_dir,
            risk_tier,
            authority_path=resolve_artifact_ref(authority_record_ref, run_dir),
        )
    ):
        errors.append(
            "accepted implementation gates require mandatory 2-lane pre/post plan validation "
            "with strategy_ref, verification_agent_ref, exact practical viewpoint sets, unanimous verdicts, and resolvable in-run artifacts; "
            "tier0_trivial/tier1_local deterministic paths may use an explicit mini_plan_validation_skip with local_verification and skip_scope_evidence, "
            "tier1 may use structured tier1_self_check evidence, "
            "while not_classified accepted gates must prove file_changing_batch=false"
        )
    if risk_tier in {"tier2_material", "tier3_high_risk"}:
        if terminal_verified_stop and implementation_gate_status != "accepted":
            errors.append("tier2/tier3 verified terminal stops require implementation_gate_status=accepted")
        if implementation_gate_status == "accepted":
            if not implementation_gate_evidence_is_valid(
                implementation_gate_evidence,
                run_dir,
                authority_path=resolve_artifact_ref(authority_record_ref, run_dir),
            ):
                errors.append(
                    "tier2/tier3 accepted implementation gates require strategy_ref, 5-lane pre/post challenge refs, "
                    "exact viewpoint sets, unanimous verdicts, and resolvable in-run artifacts"
                )
    continue_attempt_ref = extract_attempt_ref(continue_exit_evidence)

    if implementation_like_intent and continuation_mode != "nonstop":
        errors.append("implementation-oriented runs must use continuation_mode=nonstop")

    capability_mode_lower = capability_mode.lower()

    if "delegated_agents_authorized_by_loop" not in capability_mode_lower:
        errors.append(
            "agent-loop handoffs must record capability_mode with "
            "delegated_agents_authorized_by_loop; tool availability belongs in "
            "the suffix, not as a separate permission gate"
        )
    elif not any(token in capability_mode_lower for token in REQUIRED_CAPABILITY_MODE_TOKENS):
        errors.append(
            "agent-loop handoffs must record capability_mode with one of "
            "delegated_agents_authorized_by_loop_tool_available, "
            "delegated_agents_authorized_by_loop_tool_unavailable, or "
            "delegated_agents_authorized_by_loop_tool_state_unknown"
        )

    delegation_permission_checkpoint_text = " | ".join(
        [
            capability_mode,
            current_stage,
            next_action,
            flatten_multivalue_text(remaining_required_stages),
            blocking_findings_text,
            pause_reason,
            resume_instructions_text,
        ]
    )
    if (
        implementation_like_intent
        and continuation_mode == "nonstop"
        and contains_any_pattern(delegation_permission_checkpoint_text, DELEGATION_PERMISSION_CHECKPOINT_PATTERNS)
    ):
        errors.append(
            "implementation-oriented $loop runs may not make delegated-agent use a separate user-authorization checkpoint; "
            "$loop already authorizes spawn_agent lanes when available"
        )

    if run_decision in {"continue", "pause", "stop", "planning_complete"} and is_noneish(closeout_round_id):
        errors.append("turn-ending handoffs require a concrete closeout_round_id")
    elif not (resume_state and run_decision in {"continue", "pause"}) and closeout_round_id_seen_in_receipts(run_dir, closeout_round_id):
        errors.append("closeout_round_id was already used in a prior status/closeout receipt; closeout rounds must be fresh and non-reusable")

    requires_default_artifacts = run_decision in {"continue", "pause", "stop", "planning_complete"}
    requires_default_artifacts = (
        requires_default_artifacts
        or stop_consensus_status == "allow_unanimous"
        or goal_completion_status == VERIFIED_COMPLETE_STATUS
    )

    if requires_default_artifacts:
        if not source_path.exists():
            errors.append("agent-loop closeout validation requires source.md")
        if not ideas_path.exists():
            errors.append("agent-loop closeout validation requires ideas.md")
        else:
            errors.extend(
                validate_ideas_artifact(
                    ideas_path,
                    allow_in_progress_ideation=live_state and loop_state == "ideation",
                )
            )
        if not research_path.exists():
            errors.append("agent-loop closeout validation requires research.md")
        if not revised_plan_path.exists():
            errors.append("agent-loop closeout validation requires revised-plan.md")
        if not evidence_path.exists():
            errors.append("agent-loop closeout validation requires evidence.md")

        invalid_plan_idea_refs = idea_refs_in_plan(revised_plan_path) - validated_idea_ids(ideas_path)
        if invalid_plan_idea_refs:
            errors.append(
                "revised-plan.md may only cite validated ideas with research_ref/evidence_ref; invalid idea_ref(s): "
                + ", ".join(sorted(invalid_plan_idea_refs))
            )

    if stop_status == "external_authority" and external_basis == "none":
        errors.append("stop_authorization_status=external_authority requires an explicit external_authority_basis")
    if stop_status != "external_authority" and external_basis != "none":
        errors.append("external_authority_basis must be none unless stop_authorization_status=external_authority")
    if stop_status == "allow" and stop_consensus_status != "allow_unanimous":
        errors.append("stop_authorization_status=allow requires stop_consensus_status=allow_unanimous")
    if stop_status == "external_authority" and stop_consensus_status != "waived_external_authority":
        errors.append("stop_authorization_status=external_authority requires stop_consensus_status=waived_external_authority")
    if stop_status in {"not_applicable", "not_run", "deny"} and stop_consensus_status in {"allow_unanimous", "waived_external_authority"}:
        errors.append("stop_consensus_status may not claim halt proof or waiver when stop_authorization_status is not allow/external_authority")
    if stop_consensus_status == "allow_unanimous" and not has_stop_authorization_proof(
        fields["stop_consensus_evidence"], run_dir, closeout_round_id
    ):
        errors.append(
            f"stop_consensus_status=allow_unanimous requires explicit stop_authorization phase "
            f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent proof in stop_consensus_evidence"
        )
    if stop_round_id and challenge_round_id_seen_in_receipts(run_dir, stop_round_id) and not resume_state:
        errors.append("stop_consensus_evidence challenge_round_id was already used in a prior closeout receipt; challenge rounds must be fresh and non-reusable")
    if stop_consensus_status in {"allow_unanimous", "waived_external_authority"} and is_noneish(fields["stop_consensus_evidence"]):
        errors.append("stop_consensus_status requires concrete stop_consensus_evidence")

    if is_noneish(fields["goal_completion_status"]):
        errors.append("goal_completion_status must be concrete")
    if is_noneish(fields["goal_completion_evidence"]):
        errors.append("goal_completion_evidence must be concrete")
    if goal_completion_status == VERIFIED_COMPLETE_STATUS and not has_goal_completion_proof(
        fields["goal_completion_evidence"], run_dir, closeout_round_id
    ):
        errors.append(
            f"goal_completion_status={VERIFIED_COMPLETE_STATUS} requires explicit goal_completion phase "
            f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent proof in goal_completion_evidence"
        )
    if goal_round_id and challenge_round_id_seen_in_receipts(run_dir, goal_round_id) and not resume_state:
        errors.append("goal_completion_evidence challenge_round_id was already used in a prior closeout receipt; completion rounds must be fresh and non-reusable")

    if requires_approval_or_no_action_challenge(fields) and not has_stop_authorization_challenge_attempt(
        fields["stop_consensus_evidence"],
        run_dir,
        closeout_round_id,
    ):
        errors.append(
            f"approval/no-bounded-action/blocker closeouts require a fresh {REQUIRED_DELEGATED_AGENT_COUNT}-lane "
            "stop_authorization challenge attempt before yielding or treating the blocker as terminal"
        )

    if (
        run_decision == "stop"
        and implementation_like_intent
        and source_requests_plan_execution(source_path)
        and not explicit_user_stop_override
        and not goal_completion_evidence_has_implementation_authority(goal_completion_evidence, run_dir)
    ):
        errors.append(
            "roadmap-derived implementation stops require goal_completion_evidence to record "
            "implementation_authority_ref=<revised-plan.md|handoff.md|implementation-authority/...>"
        )

    if run_decision == "continue":
        if loop_state in {"paused", "stopped"}:
            errors.append("run_decision=continue cannot use loop_state paused/stopped")
        if is_noneish(current_stage):
            errors.append("run_decision=continue requires a live current_or_next_stage")
        if is_noneish(next_action):
            errors.append("run_decision=continue requires a live next_mandatory_action")
        elif is_open_ended_candidate_hunt(next_action):
            errors.append(
                "run_decision=continue may not end a turn on a pure triage/sweep/candidate-hunt next_mandatory_action; keep working until a concrete bounded patch, test batch, or blocker is actually in flight"
            )
        if is_noneish(remaining_required_stages):
            errors.append("run_decision=continue requires at least one remaining required stage")
        if continue_exit_status == "not_applicable":
            errors.append("run_decision=continue requires continue_exit_status to prove the latest next-action attempt")
        if is_noneish(continue_exit_evidence):
            errors.append("run_decision=continue requires concrete continue_exit_evidence")
        if is_inspection_only_continue_exit(continue_exit_status, continue_exit_evidence):
            errors.append("inspection-only continue_exit_evidence is illegal for continue_exit_status=next_action_started")
        if has_unverified_local_edit_signal(continue_exit_evidence):
            errors.append(
                "run_decision=continue may not close the turn on local-edit evidence without matching targeted validation; bundle apply_patch-sized edits with the smallest relevant test/lint/type/build proof first"
            )
        if not continue_attempt_ref:
            errors.append("run_decision=continue requires continue_exit_evidence to record attempt_ref=<in-run-artifact>")
        else:
            attempt_path = resolve_run_scoped_ref(continue_attempt_ref, run_dir)
            if attempt_path is None:
                errors.append("run_decision=continue requires attempt_ref to resolve to an existing in-run artifact")
            elif not attempt_receipt_is_valid(attempt_path, closeout_round_id, next_action, continue_exit_status):
                errors.append("run_decision=continue requires attempt_ref to resolve to a valid v1 attempt receipt bound to the current closeout_round_id and next_action")
            elif not artifact_is_fresh_for_closeout(
                attempt_path,
                handoff_path,
                MAX_TURN_END_ATTEMPT_STALENESS_SECONDS,
            ):
                errors.append("run_decision=continue requires attempt_ref to stay fresh relative to handoff.md; stale attempt proof suggests voluntary_turn_close")
        if extract_closeout_round_id(continue_exit_evidence).lower() != closeout_round_id.lower():
            errors.append("run_decision=continue requires continue_exit_evidence to record closeout_round_id=<current-closeout-round>")
        if not live_continue_state:
            if turn_exit_cause == "not_applicable":
                errors.append("run_decision=continue requires a concrete turn_exit_cause for any turn-ending continue state")
            if is_noneish(turn_exit_evidence):
                errors.append("run_decision=continue requires concrete turn_exit_evidence")
            elif not turn_exit_evidence_matches_cause(turn_exit_cause, turn_exit_evidence):
                errors.append(f"run_decision=continue requires turn_exit_evidence to match turn_exit_cause={turn_exit_cause}")
            if host_resume_mode == "same_turn_only" and turn_exit_cause != "host_turn_boundary_pause":
                errors.append("host_resume_mode=same_turn_only run_decision=continue requires turn_exit_cause=host_turn_boundary_pause")
            if host_resume_mode == "same_turn_only" and turn_exit_cause == "host_turn_boundary_pause":
                if turn_exit_host_boundary_ref is None:
                    errors.append(
                        "host_resume_mode=same_turn_only run_decision=continue requires turn_exit_evidence to record host_boundary_ref=<authority-receipt-path>"
                    )
                elif is_placeholder_reference(turn_exit_host_boundary_ref):
                    errors.append(
                        "host_resume_mode=same_turn_only run_decision=continue requires a concrete non-placeholder host_boundary_ref value"
                    )
                else:
                    authority_path = resolve_run_scoped_ref(turn_exit_host_boundary_ref, run_dir)
                    if authority_path is None:
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires host_boundary_ref to resolve to an existing in-run authority receipt artifact"
                        )
                    elif not host_boundary_receipt_is_valid(authority_path, closeout_round_id, continue_attempt_ref):
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires host_boundary_ref to resolve to a valid v1 authority receipt artifact bound to the current closeout_round_id and attempt_ref"
                        )
                    elif not artifact_is_fresh_for_closeout(
                        authority_path,
                        handoff_path,
                        MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS,
                    ):
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires a fresh host_boundary_ref receipt close to handoff.md; stale boundary proof suggests voluntary_turn_close"
                        )
            if continue_exit_status == "next_action_started" and turn_exit_cause == "blocked_during_attempt":
                errors.append("turn_exit_cause=blocked_during_attempt requires continue_exit_status=blocked_during_attempt")
            allowed_blocked_turn_causes = {
                "blocked_during_attempt",
                "tool_timeout_after_batch_shrink",
            }
            if host_boundary_continue:
                # The latest bounded action can be blocked while the visible
                # turn ends for the separate same-turn-only host boundary.
                allowed_blocked_turn_causes.add("host_turn_boundary_pause")
            if continue_exit_status == "blocked_during_attempt" and turn_exit_cause not in allowed_blocked_turn_causes:
                errors.append("continue_exit_status=blocked_during_attempt requires a matching blocker-style turn_exit_cause")
            if turn_exit_cause == "tool_timeout_after_batch_shrink" and continue_exit_status != "blocked_during_attempt":
                errors.append("turn_exit_cause=tool_timeout_after_batch_shrink requires continue_exit_status=blocked_during_attempt")
        if goal_completion_status == VERIFIED_COMPLETE_STATUS:
            errors.append(f"run_decision=continue may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")
        if goal_completion_status == "completion_candidate" and not completion_candidate_points_at_challenge(
            next_action,
            continue_exit_evidence,
            goal_completion_evidence,
        ):
            errors.append(
                f"goal_completion_status=completion_candidate requires the live continue state to point at the fresh "
                f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent completion challenge"
            )

    if continue_exit_status in {"next_action_started", "blocked_during_attempt"} and run_decision != "continue" and not host_boundary_pause:
        errors.append("continue_exit_status may only prove a turn-ending continue state or a host_turn_boundary pause")
    if turn_exit_cause != "not_applicable" and run_decision != "continue" and not host_boundary_pause:
        errors.append("turn_exit_cause may only be non-default for turn-ending continue states or host_turn_boundary pauses")
    if run_decision != "continue" and not host_boundary_pause and not is_noneish(turn_exit_evidence):
        errors.append("turn_exit_evidence must stay empty unless run_decision=continue or external_authority_basis=host_turn_boundary")
    if turn_exit_cause == "host_turn_boundary_pause" and not (host_boundary_pause or host_boundary_continue):
        errors.append("turn_exit_cause=host_turn_boundary_pause requires either host-boundary pause or same_turn_only continue")

    if run_decision == "planning_complete":
        if run_intent not in PLANNING_ONLY_INTENTS:
            errors.append("run_decision=planning_complete requires run_intent=planning_only")
        if not source_explicit_planning_only(source_path):
            errors.append("run_decision=planning_complete requires source.md to explicitly record a planning-only request")
        if loop_state != "planning":
            errors.append("run_decision=planning_complete requires loop_state=planning")
        if continuation_mode == "nonstop":
            errors.append("run_decision=planning_complete is illegal in continuation_mode=nonstop")
        if stop_status != "external_authority":
            errors.append("run_decision=planning_complete requires stop_authorization_status=external_authority")
        if stop_consensus_status != "waived_external_authority":
            errors.append("run_decision=planning_complete requires stop_consensus_status=waived_external_authority")
        if external_basis != "explicit_user_redirect":
            errors.append("run_decision=planning_complete requires external_authority_basis=explicit_user_redirect")
        if is_noneish(fields["stop_authorization_evidence"]):
            errors.append("run_decision=planning_complete requires stop_authorization_evidence")
        if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
            errors.append("run_decision=planning_complete may not use consent-seeking or report-driven phrasing in pause_reason")

    if run_decision in {"pause", "stop"}:
        if stop_status not in {"allow", "external_authority"}:
            errors.append(f"run_decision={run_decision} requires stop_authorization_status=allow or external_authority")
        if is_noneish(fields["stop_authorization_evidence"]):
            errors.append(f"run_decision={run_decision} requires stop_authorization_evidence")
        if is_noneish(fields["pause_reason"]):
            errors.append(f"run_decision={run_decision} requires a concrete pause_reason")
        if run_decision == "pause" and loop_state != "paused":
            errors.append("run_decision=pause requires loop_state=paused")
        if run_decision == "stop" and loop_state != "stopped":
            errors.append("run_decision=stop requires loop_state=stopped")
        if run_decision == "stop" and not is_noneish(remaining_required_stages) and not explicit_user_stop_override:
            errors.append("run_decision=stop is illegal while remaining_required_stages is non-empty")
        if run_decision == "stop" and sequential_status == "open" and not explicit_user_stop_override:
            errors.append("run_decision=stop is illegal while sequential_objectives_status=open")
        if require_consensus and stop_status == "not_run":
            errors.append("consensus-required mode forbids stop_authorization_status=not_run")
        if run_decision == "pause" and is_noneish(next_action):
            errors.append("run_decision=pause requires an explicit next_mandatory_action")
        if run_decision == "pause" and is_noneish(remaining_required_stages):
            errors.append("run_decision=pause requires live remaining_required_stages; do not pause in a semantically finished state")

        if run_decision == "pause":
            if goal_completion_status == VERIFIED_COMPLETE_STATUS:
                errors.append(f"run_decision=pause may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")
            if contains_any_pattern(pause_reason, PAUSE_CLOSURE_SCENT_PATTERNS):
                errors.append("run_decision=pause may not use completion-scent phrasing in pause_reason")
            if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("run_decision=pause may not use consent-seeking or report-driven phrasing in pause_reason")
            if contains_any_pattern(current_stage.lower(), PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("run_decision=pause current_or_next_stage must stay live and non-closure-scented")
            if contains_any_pattern(next_action.lower(), PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("run_decision=pause next_mandatory_action must stay live and non-closure-scented")
            if contains_any_pattern(resume_instructions_text, WEAK_PAUSE_RESUME_PATTERNS):
                errors.append("run_decision=pause may not use vague, consent-seeking, or closure-scent phrasing in resume_instructions")
            if not has_actionable_resume_instructions(fields["resume_instructions"]):
                errors.append("run_decision=pause requires actionable resume_instructions anchored to concrete restart steps")
            else:
                next_action_tokens = extract_anchor_tokens(next_action)
                resume_tokens = extract_anchor_tokens(resume_instructions_text)
                if next_action_tokens:
                    if not (next_action_tokens & resume_tokens):
                        errors.append("run_decision=pause requires resume_instructions to stay aligned with next_mandatory_action")
                elif "next_mandatory_action" not in resume_instructions_text and "current_or_next_stage" not in resume_instructions_text:
                    errors.append("run_decision=pause requires resume_instructions to reference the paused work when next_mandatory_action lacks stable anchor tokens")

            if goal_completion_status == "completion_candidate" and not completion_candidate_points_at_challenge(
                next_action,
                resume_instructions_text,
                goal_completion_evidence,
            ):
                errors.append(
                    f"goal_completion_status=completion_candidate requires next_mandatory_action or resume_instructions "
                    f"to point at the fresh {REQUIRED_DELEGATED_AGENT_COUNT}-agent completion challenge"
                )

            if external_basis == "host_turn_boundary":
                if is_delegated_quota_blocker(continue_exit_evidence, pause_reason, blocking_findings_text):
                    errors.append(
                        "delegated-agent quota blockers must use run_decision=continue with "
                        "continue_exit_status=blocked_during_attempt and auto-resume; they are not host-boundary pause authority"
                    )
                if turn_exit_cause != "host_turn_boundary_pause":
                    errors.append("host_turn_boundary pauses require turn_exit_cause=host_turn_boundary_pause")
                if is_noneish(turn_exit_evidence):
                    errors.append("host_turn_boundary pauses require concrete turn_exit_evidence")
                elif not turn_exit_evidence_matches_cause(turn_exit_cause, turn_exit_evidence):
                    errors.append(f"host_turn_boundary pause turn_exit_evidence must match turn_exit_cause={turn_exit_cause}")
                if continue_exit_status == "not_applicable":
                    errors.append("host_turn_boundary pauses require continue_exit_status to prove the latest next-action attempt")
                if is_noneish(continue_exit_evidence):
                    errors.append("host_turn_boundary pauses require concrete continue_exit_evidence")
                elif is_inspection_only_continue_exit(continue_exit_status, continue_exit_evidence):
                    errors.append("host_turn_boundary pauses may not use inspection-only continue_exit_evidence for continue_exit_status=next_action_started")
                elif has_unverified_local_edit_signal(continue_exit_evidence):
                    errors.append(
                        "host_turn_boundary pauses may not close on local-edit evidence without matching targeted validation; finish the smallest relevant verification batch before yielding the visible turn"
                    )
                elif not has_anchor_overlap(next_action, continue_exit_evidence):
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to stay anchored to next_mandatory_action")
                host_attempt_ref = extract_attempt_ref(continue_exit_evidence)
                if not host_attempt_ref:
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to record attempt_ref=<in-run-artifact>")
                else:
                    attempt_path = resolve_run_scoped_ref(host_attempt_ref, run_dir)
                    if attempt_path is None:
                        errors.append("host_turn_boundary pauses require attempt_ref to resolve to an existing in-run artifact")
                    elif not attempt_receipt_is_valid(attempt_path, closeout_round_id, next_action, continue_exit_status):
                        errors.append("host_turn_boundary pauses require attempt_ref to resolve to a valid v1 attempt receipt bound to the current closeout_round_id and next_action")
                    elif not artifact_is_fresh_for_closeout(
                        attempt_path,
                        handoff_path,
                        MAX_TURN_END_ATTEMPT_STALENESS_SECONDS,
                    ):
                        errors.append("host_turn_boundary pauses require attempt_ref to stay fresh relative to handoff.md; stale attempt proof suggests voluntary_turn_close")
                if extract_closeout_round_id(continue_exit_evidence).lower() != closeout_round_id.lower():
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to record closeout_round_id=<current-closeout-round>")

        if run_decision == "stop":
            if contains_any_pattern(pause_reason, PAUSE_CLOSURE_SCENT_PATTERNS):
                errors.append("run_decision=stop may not use soft-close or queued-for-later phrasing in pause_reason")
            if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("run_decision=stop may not use consent-seeking or report-driven phrasing in pause_reason")
            if external_basis == "explicit_user_stop":
                if goal_completion_status == "completion_candidate":
                    errors.append("explicit_user_stop may not leave goal_completion_status=completion_candidate")
            elif goal_completion_status != VERIFIED_COMPLETE_STATUS:
                errors.append(
                    f"run_decision=stop requires goal_completion_status={VERIFIED_COMPLETE_STATUS} unless the basis is a direct explicit user stop"
                )
            if stop_status == "allow":
                stop_round_id = extract_challenge_round_id(fields["stop_consensus_evidence"])
                goal_round_id = extract_challenge_round_id(fields["goal_completion_evidence"])
                if not stop_round_id or not goal_round_id:
                    errors.append("autonomous stop requires explicit challenge_round_id in both stop_consensus_evidence and goal_completion_evidence")
                elif stop_round_id == goal_round_id:
                    errors.append(
                        f"autonomous stop requires distinct fresh {REQUIRED_DELEGATED_AGENT_COUNT}-agent rounds for halt proof and goal-completion proof"
                    )

        if host_resume_mode == "same_turn_only" and run_decision == "pause":
            if stop_status != "external_authority":
                errors.append("host_resume_mode=same_turn_only requires run_decision=pause to use stop_authorization_status=external_authority")
            if external_basis not in {
                "explicit_user_pause",
                "explicit_user_redirect",
                "human_decision_required",
                "host_turn_boundary",
            }:
                errors.append("host_resume_mode=same_turn_only requires run_decision=pause to use a truthful external authority basis")

    if stop_status == "external_authority":
        if external_basis in {"explicit_user_pause", "human_decision_required"} or (
            external_basis == "explicit_user_redirect" and run_decision != "planning_complete"
        ):
            errors.append(
                "explicit_user_pause, explicit_user_redirect, and human_decision_required require host-produced "
                "immutable authority and are unsupported in the default local file-backed profile"
            )
        if run_decision == "pause" and external_basis not in {
            "explicit_user_pause",
            "explicit_user_redirect",
            "human_decision_required",
            "host_turn_boundary",
        }:
            errors.append("run_decision=pause with external_authority requires pause/redirect/decision basis")
        if run_decision == "stop" and external_basis != "explicit_user_stop":
            errors.append("run_decision=stop with external_authority requires external_authority_basis=explicit_user_stop")
        if any(re.search(pattern, pause_reason) for pattern in INFERRED_AUTHORITY_PATTERNS):
            errors.append("external_authority may not be justified by inferred closure phrasing in pause_reason")
        if any(re.search(pattern, stop_evidence) for pattern in INFERRED_AUTHORITY_PATTERNS):
            errors.append("external_authority may not be justified by inferred closure phrasing in stop_authorization_evidence")
        if external_basis == "human_decision_required" and "human_decision_gate=unresolved_after_3_codex" not in stop_evidence:
            errors.append("human_decision_required requires stop_authorization_evidence to record human_decision_gate=unresolved_after_3_codex")
        if external_basis == "host_turn_boundary" and host_resume_mode != "same_turn_only":
            errors.append("external_authority_basis=host_turn_boundary requires host_resume_mode=same_turn_only")
        if external_basis == "explicit_user_pause":
            user_pause_ref = extract_structured_value(stop_evidence, "user_pause_ref")
            if user_pause_ref is None:
                errors.append("explicit_user_pause requires stop_authorization_evidence to record user_pause_ref=<...>")
            elif is_placeholder_reference(user_pause_ref):
                errors.append("explicit_user_pause requires a concrete non-placeholder user_pause_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_pause_ref, run_dir)
                if authority_path is None or not authority_receipt_is_valid(authority_path, "explicit_user_pause"):
                    errors.append("explicit_user_pause requires user_pause_ref to resolve to a valid v1 authority receipt artifact")
        if external_basis == "explicit_user_redirect":
            user_redirect_ref = extract_structured_value(stop_evidence, "user_redirect_ref")
            if user_redirect_ref is None:
                errors.append("explicit_user_redirect requires stop_authorization_evidence to record user_redirect_ref=<...>")
            elif is_placeholder_reference(user_redirect_ref):
                errors.append("explicit_user_redirect requires a concrete non-placeholder user_redirect_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_redirect_ref, run_dir)
                if authority_path is None or not authority_receipt_is_valid(authority_path, "explicit_user_redirect"):
                    errors.append("explicit_user_redirect requires user_redirect_ref to resolve to a valid v1 authority receipt artifact")
        if external_basis == "host_turn_boundary":
            host_boundary_ref = extract_structured_value(stop_evidence, "host_boundary_ref")
            if host_boundary_ref is None:
                errors.append("host_turn_boundary requires stop_authorization_evidence to record host_boundary_ref=<...>")
            elif is_placeholder_reference(host_boundary_ref):
                errors.append("host_turn_boundary requires stop_authorization_evidence to carry a concrete non-placeholder host_boundary_ref value")
            else:
                authority_path = resolve_run_scoped_ref(host_boundary_ref, run_dir)
                if authority_path is None:
                    errors.append("host_turn_boundary requires host_boundary_ref to resolve to an existing in-run authority receipt artifact")
                elif not host_boundary_receipt_is_valid(authority_path, closeout_round_id, continue_attempt_ref):
                    errors.append("host_turn_boundary requires host_boundary_ref to resolve to a valid v1 authority receipt artifact bound to the current closeout_round_id and attempt_ref")
                elif not artifact_is_fresh_for_closeout(
                    authority_path,
                    handoff_path,
                    MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS,
                ):
                    errors.append("host_turn_boundary requires a fresh host_boundary_ref receipt close to handoff.md; stale boundary proof suggests voluntary_turn_close")
            if not contains_any_pattern(pause_reason, HOST_BOUNDARY_REASON_PATTERNS) or not contains_any_pattern(
                pause_reason, HOST_BOUNDARY_FORCE_PATTERNS
            ):
                errors.append("host_turn_boundary pauses must describe a forced visible turn boundary in pause_reason")
            if contains_any_pattern(pause_reason, NON_HOST_PAUSE_CAUSE_PATTERNS):
                errors.append("host_turn_boundary pauses may not mix in non-host pause causes inside pause_reason")
        if external_basis == "explicit_user_stop":
            user_stop_ref = extract_structured_value(stop_evidence, "user_stop_ref")
            if user_stop_ref is None:
                errors.append("explicit_user_stop requires stop_authorization_evidence to record user_stop_ref=<...>")
            elif is_placeholder_reference(user_stop_ref):
                errors.append("explicit_user_stop requires a concrete non-placeholder user_stop_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_stop_ref, run_dir)
                if authority_path is None:
                    errors.append("explicit_user_stop requires user_stop_ref to resolve to an existing in-run authority receipt artifact")
                elif not user_stop_receipt_is_valid(authority_path, closeout_round_id):
                    errors.append(
                        "explicit_user_stop requires user_stop_ref to resolve to a valid v1 authority receipt "
                        "artifact bound to the current closeout_round_id and current_user_message source"
                    )
                elif not artifact_is_fresh_for_closeout(
                    authority_path,
                    handoff_path,
                    MAX_USER_STOP_RECEIPT_STALENESS_SECONDS,
                ):
                    errors.append("explicit_user_stop requires a fresh user_stop_ref receipt close to handoff.md")

    if continuation_mode == "nonstop" and run_decision == "pause" and stop_status == "allow":
        if is_noneish(blocking_findings_text):
            errors.append("continuation_mode=nonstop only allows autonomous pause with concrete blocking_findings")
        elif not has_anchor_overlap(blocking_findings_text, next_action):
            errors.append("blocking_findings must stay anchored to the paused next_mandatory_action for a nonstop autonomous pause")
        if not has_anchor_overlap(blocking_findings_text, pause_reason):
            errors.append("continuation_mode=nonstop autonomous pause requires pause_reason to stay anchored to blocking_findings")

    if continuation_mode == "nonstop" and run_decision == "pause" and external_basis == "host_turn_boundary" and goal_completion_status == VERIFIED_COMPLETE_STATUS:
        errors.append("host_turn_boundary pauses in continuation_mode=nonstop may not claim a fully verified completed goal")

    plan_remaining = extract_plan_remaining(run_dir / "revised-plan.md")
    if plan_remaining is not None:
        if run_decision == "continue" and is_noneish(plan_remaining):
            errors.append("revised-plan.md has no remaining required stages but handoff says continue")
        if run_decision == "pause" and is_noneish(plan_remaining):
            errors.append("revised-plan.md has no remaining required stages but handoff says pause")
        if run_decision == "stop" and not is_noneish(plan_remaining) and not explicit_user_stop_override:
            errors.append("revised-plan.md still has remaining required stages but handoff says stop")

    if source_has_sequential_markers(run_dir / "source.md"):
        if sequential_status == "none_detected":
            errors.append("source.md contains sequential markers but sequential_objectives_status=none_detected")
        if run_decision == "stop" and sequential_status != "satisfied" and not explicit_user_stop_override:
            errors.append("source.md contains sequential markers, so stop requires sequential_objectives_status=satisfied")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate agent-loop handoff closeout invariants.")
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--require-consensus",
        action="store_true",
        help="Reject autonomous halt states that lack recorded halt authorization",
    )
    parser.add_argument(
        "--live-state",
        action="store_true",
        help="Validate an in-progress handoff without requiring turn-ending continue evidence",
    )
    parser.add_argument(
        "--resume-state",
        action="store_true",
        help="Validate an already-emitted continue/pause handoff during resume without treating its own closeout receipt as stale replay authority",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"[FAIL] handoff.md not found: {handoff_path}")
        return 1

    if has_flat_legacy_lines(handoff_path):
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print("- mixed-format legacy handoff detected; refresh it with scripts/refresh_legacy_handoffs.py and keep only canonical v2 fields")
        return 1

    duplicate_fields, unknown_fields = inspect_canonical_handoff(handoff_path)
    if duplicate_fields:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print(f"- duplicate canonical handoff fields are illegal: {', '.join(duplicate_fields)}")
        return 1
    if unknown_fields:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print(f"- unknown canonical handoff fields are illegal: {', '.join(unknown_fields)}")
        return 1

    fields = parse_handoff(handoff_path)
    errors = validate_fields(
        fields,
        run_dir,
        require_consensus=args.require_consensus,
        live_state=args.live_state,
        resume_state=args.resume_state,
    )
    if errors:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[OK] Handoff validation passed: {run_dir}")
    print(f"run_decision={clean_value(str(fields['run_decision']))}")
    print(f"loop_state={clean_value(str(fields['loop_state']))}")
    print(f"stop_authorization_status={clean_value(str(fields['stop_authorization_status']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
