#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import hashlib
import json
import os
from pathlib import Path

from validate_handoff import (
    MIN_TOP_MODEL_LANES,
    REQUIRED_DELEGATED_AGENT_COUNT,
    REQUIRED_DELEGATED_MODEL_BINDING,
    REQUIRED_DELEGATED_MODEL_POLICY,
    REQUIRED_DELEGATED_REASONING_EFFORT,
    REQUIRED_AUTHORITY_POLICY_VERSION,
    REQUIRED_AUTHORITY_PROMPT_VERSION,
    REQUIRED_AUTHORITY_SCHEMA_VERSION,
    REQUIRED_AUTHORITY_VALIDATOR_VERSION,
    REQUIRED_CHALLENGE_CYCLE_SCHEMA_VERSION,
    REQUIRED_INITIAL_RESEARCH_LANES,
    REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION,
    REQUIRED_FINAL_POLICY_COVERAGE_VERDICT,
    REQUIRED_FINAL_POLICY_ROUTE_CONTEXT,
    REQUIRED_FINAL_CHALLENGE_AGENT_ROLE,
    REQUIRED_FINAL_CHALLENGE_MODES,
    REQUIRED_STOP_LANES,
    REQUIRED_STOP_VIEWPOINTS,
    TOP_DELEGATED_MODEL_SLUG,
    TOP_DELEGATED_REASONING_EFFORT,
    VERIFIED_COMPLETE_STATUS,
    challenge_cycle_validation_errors,
    compute_subject_digest,
    compute_source_digest,
    expected_policy_ref_digests,
    file_sha256_digest,
    final_policy_route_metadata_is_valid_inline,
)


VIEWPOINTS = [
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
]

RESEARCH_LANES = [
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
]

FLOOR_REASONING_EFFORT = "high"
LOADED_POLICY_REFS = "AGENTS.md#LoopCompletionGate|SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof"

COVERAGE_BY_VIEWPOINT = {
    "architecture_dependency": ["architecture_dependency"],
    "failure_verification": ["failure_verification"],
    "goal_efficiency": ["goal_efficiency"],
    "requirement_alignment": ["requirement_alignment"],
    "implementation_quality": ["implementation_quality"],
}

LANE_MODEL_PLAN = [
    (TOP_DELEGATED_MODEL_SLUG, TOP_DELEGATED_REASONING_EFFORT),
    (TOP_DELEGATED_MODEL_SLUG, TOP_DELEGATED_REASONING_EFFORT),
    (TOP_DELEGATED_MODEL_SLUG, TOP_DELEGATED_REASONING_EFFORT),
    (TOP_DELEGATED_MODEL_SLUG, FLOOR_REASONING_EFFORT),
    (TOP_DELEGATED_MODEL_SLUG, FLOOR_REASONING_EFFORT),
]


def lane_model(index: int) -> tuple[str, str]:
    return LANE_MODEL_PLAN[index - 1]


def policy_ref_digests(run_dir: Path) -> str:
    return "|".join(expected_policy_ref_digests(run_dir))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_handoff(scripts_dir: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "validate_handoff.py"),
            str(run_dir),
            "--require-consensus",
        ],
        text=True,
        capture_output=True,
    )


def expect_validation_failure(scripts_dir: Path, run_dir: Path, label: str) -> bool:
    invalid = validate_handoff(scripts_dir, run_dir)
    if invalid.returncode == 0:
        print(f"[FAIL] {label} unexpectedly passed validation", file=sys.stderr)
        return False
    return True


def consensus_evidence(
    *,
    phase: str,
    challenge_round_id: str,
    closeout_round_id: str,
    subject_digest: str,
    source_digest: str,
    refs: list[str],
    policy_ref_digest_text: str,
    v3_bindings: dict[str, str] | None = None,
) -> str:
    challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES[phase]
    viewpoint_set = "|".join(VIEWPOINTS)
    coverage_viewpoint_set = "|".join(sorted(REQUIRED_STOP_VIEWPOINTS))
    binding_text = " ".join(f"{key}={value}" for key, value in (v3_bindings or {}).items())
    if binding_text:
        binding_text += " "
    return (
        f"allow_count={REQUIRED_DELEGATED_AGENT_COUNT} deny_count=0 ambiguous_count=0 missing_count=0 "
        f"challenge_round_id={challenge_round_id} closeout_round_id={closeout_round_id} "
        f"agent_role={REQUIRED_FINAL_CHALLENGE_AGENT_ROLE} "
        f"challenge_review_mode={challenge_mode} "
        f"subject_digest={subject_digest} viewpoint_set={viewpoint_set} "
        f"coverage_viewpoint_set={coverage_viewpoint_set} "
        f"source_ref=source.md source_digest={source_digest} "
        "context_mode=clean_source_first "
        "authority_basis=source_md_original_user_prompt "
        "source_requirements_reconstructed=yes "
        "claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff "
        "repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied "
        f"route_context={REQUIRED_FINAL_POLICY_ROUTE_CONTEXT} "
        f"loaded_policy_refs={LOADED_POLICY_REFS} "
        f"policy_ref_digests={policy_ref_digest_text} "
        f"policy_coverage_verdict={REQUIRED_FINAL_POLICY_COVERAGE_VERDICT} "
        f"model_policy={REQUIRED_DELEGATED_MODEL_POLICY} "
        f"top_model_lane_min={MIN_TOP_MODEL_LANES} "
        f"resolved_model_slug={TOP_DELEGATED_MODEL_SLUG} "
        f"resolved_reasoning_effort={REQUIRED_DELEGATED_REASONING_EFFORT} "
        f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING} "
        f"{binding_text}"
        f"refs={','.join(refs)}"
    )


def handoff_text(
    *,
    closeout_round_id: str,
    stop_evidence: str,
    goal_evidence: str,
    source_digest: str,
    stage_graph_digest: str,
    adapter_manifest_ref: str,
    adapter_effective_config_digest: str,
    research_cycle_ref: str,
    research_cycle_digest_set: str,
    completion_subject_ref: str,
    completion_subject_digest: str,
    challenge_cycle_ref: str,
    challenge_cycle_digest_set: str,
) -> str:
    return "\n".join(
        [
            "# Handoff",
            "",
            f"- `handoff_schema_version`: `{REQUIRED_AUTHORITY_SCHEMA_VERSION}`",
            "- `working_goal`: `smoke terminal stop briefing`",
            "- `run_intent`: `implementation_loop`",
            "- `work_type`: `implementation`",
            "- `review_kind`: `not_applicable`",
            "- `host_resume_mode`: `same_turn_only`",
            "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
            "- `authority_record_ref`: `run://authority/run-authority.json`",
            "- `run_authority_status`: `completed`",
            "- `run_authority_revision`: `1`",
            "- `run_authority_epoch`: `1`",
            f"- `source_digest`: `{source_digest}`",
            f"- `stage_graph_digest`: `{stage_graph_digest}`",
            f"- `adapter_manifest_ref`: `{adapter_manifest_ref}`",
            "- `adapter_conformance_status`: `compatible`",
            f"- `adapter_effective_config_digest`: `{adapter_effective_config_digest}`",
            f"- `research_cycle_ref`: `{research_cycle_ref}`",
            "- `research_cycle_status`: `allow_unanimous`",
            f"- `research_cycle_digest_set`: `{research_cycle_digest_set}`",
            "- `completion_subject_type`: `repo_diff`",
            f"- `completion_subject_ref`: `{completion_subject_ref}`",
            f"- `completion_subject_digest`: `{completion_subject_digest}`",
            "- `composite_subject_digest`: `none`",
            f"- `challenge_cycle_ref`: `{challenge_cycle_ref}`",
            "- `challenge_cycle_status`: `allow_unanimous`",
            f"- `challenge_cycle_digest_set`: `{challenge_cycle_digest_set}`",
            "- `visible_output_contract`: `terminal_completion`",
            "- `current_or_next_stage`: `terminal stop briefing`",
            "- `stage_status`: `terminal stop receipt is ready for gate rendering`",
            "- `current_batch`: `none`",
            "- `risk_tier`: `tier0_trivial`",
            "- `implementation_gate_status`: `not_applicable`",
            "- `implementation_gate_evidence`: `none`",
            "- `remaining_required_stages`:",
            "  - none",
            "- `latest_evidence_summary`:",
            "  - `terminal stop briefing fields added`",
            "  - `validate_terminal_reply.py passes canonical generated receipt`",
            "- `blocking_findings`:",
            "  - none",
            "- `residual_risks`:",
            "  - `external API behavior was not exercised`",
            f"- `goal_completion_status`: `{VERIFIED_COMPLETE_STATUS}`",
            f"- `goal_completion_evidence`: `{goal_evidence}`",
            "- `loop_state`: `stopped`",
            "- `continuation_mode`: `nonstop`",
            f"- `closeout_round_id`: `{closeout_round_id}`",
            "- `run_decision`: `stop`",
            "- `sequential_objectives_status`: `satisfied`",
            "- `stop_authorization_status`: `allow`",
            "- `stop_authorization_evidence`: `fresh autonomous halt proof recorded`",
            "- `stop_consensus_status`: `allow_unanimous`",
            f"- `stop_consensus_evidence`: `{stop_evidence}`",
            "- `external_authority_basis`: `none`",
            "- `pause_reason`: `autonomous stop authorized by fresh halt and goal proof`",
            "- `next_mandatory_action`: `none`",
            "- `continue_exit_status`: `not_applicable`",
            "- `continue_exit_evidence`: `none`",
            "- `turn_exit_cause`: `not_applicable`",
            "- `turn_exit_evidence`: `none`",
            "- `resume_instructions`:",
            "  - none",
            "",
        ]
    )


def write_lane_artifacts(
    *,
    run_dir: Path,
    phase: str,
    challenge_round_id: str,
    closeout_round_id: str,
    challenge_cycle_id: str | None = None,
    authority_record_ref: str | None = None,
    authority_revision: str = "1",
    authority_epoch: str = "1",
    subject_digest: str,
    source_digest: str,
    policy_ref_digest_text: str,
) -> list[str]:
    refs: list[str] = []
    challenge_mode = REQUIRED_FINAL_CHALLENGE_MODES[phase]
    for index, viewpoint in enumerate(VIEWPOINTS, start=1):
        if viewpoint not in REQUIRED_STOP_LANES:
            raise AssertionError(f"unexpected viewpoint in smoke fixture: {viewpoint}")
        coverage = COVERAGE_BY_VIEWPOINT[viewpoint]
        rel = f"proof/{phase}-{viewpoint}.md"
        dispatch_rel = f"dispatch/{phase}-{viewpoint}.md"
        model_slug, reasoning_effort = lane_model(index)
        refs.append(rel)
        write(
            run_dir / dispatch_rel,
            "\n".join(
                [
                    "dispatch_receipt_version=v1",
                    f"phase={phase}",
                    f"agent_role={REQUIRED_FINAL_CHALLENGE_AGENT_ROLE}",
                    f"challenge_review_mode={challenge_mode}",
                    f"agent_id={phase}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    f"coverage_viewpoints={'|'.join(coverage)}",
                    f"challenge_round_id={challenge_round_id}",
                    *( [f"challenge_cycle_id={challenge_cycle_id}"] if challenge_cycle_id else [] ),
                    f"closeout_round_id={closeout_round_id}",
                    "source_ref=source.md",
                    f"source_digest={source_digest}",
                    "context_mode=clean_source_first",
                    "authority_basis=source_md_original_user_prompt",
                    "full_history_fork=false",
                    *( [f"authority_record_ref={authority_record_ref}"] if authority_record_ref else [] ),
                    f"authority_revision_at_dispatch={authority_revision}",
                    f"authority_epoch_at_dispatch={authority_epoch}",
                    f"route_context={REQUIRED_FINAL_POLICY_ROUTE_CONTEXT}",
                    f"loaded_policy_refs={LOADED_POLICY_REFS}",
                    f"policy_ref_digests={policy_ref_digest_text}",
                    f"policy_coverage_verdict={REQUIRED_FINAL_POLICY_COVERAGE_VERDICT}",
                    f"model_policy={REQUIRED_DELEGATED_MODEL_POLICY}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    "",
                ]
            ),
        )
        phase_specific_lines = []
        if phase == "goal_completion":
            phase_specific_lines.append("source_alignment_verdict=all_source_requirements_satisfied")
        write(
            run_dir / rel,
            "\n".join(
                [
                    f"phase={phase}",
                    f"agent_role={REQUIRED_FINAL_CHALLENGE_AGENT_ROLE}",
                    f"challenge_review_mode={challenge_mode}",
                    "vote=allow",
                    f"agent_id={phase}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    f"coverage_viewpoints={'|'.join(coverage)}",
                    f"challenge_round_id={challenge_round_id}",
                    *( [f"challenge_cycle_id={challenge_cycle_id}"] if challenge_cycle_id else [] ),
                    f"closeout_round_id={closeout_round_id}",
                    f"subject_digest={subject_digest}",
                    "source_ref=source.md",
                    f"source_digest={source_digest}",
                    "context_mode=clean_source_first",
                    "authority_basis=source_md_original_user_prompt",
                    "source_requirements_reconstructed=yes",
                    "claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff",
                    "repo_inspection=fresh",
                    "audit_gap_count=0",
                    "scope_verdict=original_request_satisfied",
                    *phase_specific_lines,
                    *( [f"authority_record_ref={authority_record_ref}"] if authority_record_ref else [] ),
                    f"authority_revision_at_dispatch={authority_revision}",
                    f"authority_epoch_at_dispatch={authority_epoch}",
                    f"route_context={REQUIRED_FINAL_POLICY_ROUTE_CONTEXT}",
                    f"loaded_policy_refs={LOADED_POLICY_REFS}",
                    f"policy_ref_digests={policy_ref_digest_text}",
                    f"policy_coverage_verdict={REQUIRED_FINAL_POLICY_COVERAGE_VERDICT}",
                    f"model_policy={REQUIRED_DELEGATED_MODEL_POLICY}",
                    f"resolved_model_slug={model_slug}",
                    f"resolved_reasoning_effort={reasoning_effort}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    f"spawn_tool_call_ref=run://{dispatch_rel}",
                    "freshness_status=fresh",
                    "",
                ]
            ),
        )
    return refs


def write_research_lane_artifacts(
    *,
    run_dir: Path,
    research_cycle_id: str,
    source_digest: str,
    authority_revision: str = "1",
    authority_epoch: str = "1",
) -> None:
    if set(RESEARCH_LANES) != REQUIRED_INITIAL_RESEARCH_LANES:
        raise AssertionError("smoke research lane set drifted from validator policy")
    for index, lane in enumerate(RESEARCH_LANES, start=1):
        model_slug, reasoning_effort = lane_model(index)
        dispatch_rel = f"dispatch/initial_research-{lane}.md"
        write(
            run_dir / dispatch_rel,
            "\n".join(
                [
                    "dispatch_receipt_version=v1",
                    "phase=initial_research",
                    "agent_role=research_agent",
                    f"agent_id=research-agent-{index}",
                    f"research_lane={lane}",
                    f"research_cycle_id={research_cycle_id}",
                    "source_ref=source.md",
                    f"source_digest={source_digest}",
                    f"authority_revision_at_dispatch={authority_revision}",
                    f"authority_epoch_at_dispatch={authority_epoch}",
                    f"model_policy={REQUIRED_DELEGATED_MODEL_POLICY}",
                    f"resolved_model_slug={model_slug}",
                    f"resolved_reasoning_effort={reasoning_effort}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    "",
                ]
            ),
        )
        write(
            run_dir / "research-lanes" / f"{lane}.md",
            "\n".join(
                [
                    "phase=initial_research",
                    "agent_role=research_agent",
                    f"agent_id=research-agent-{index}",
                    f"research_lane={lane}",
                    f"research_cycle_id={research_cycle_id}",
                    "vote=allow",
                    "verdict=merged",
                    "source_ref=source.md",
                    f"source_digest={source_digest}",
                    f"authority_revision_at_dispatch={authority_revision}",
                    f"authority_epoch_at_dispatch={authority_epoch}",
                    f"model_policy={REQUIRED_DELEGATED_MODEL_POLICY}",
                    f"resolved_model_slug={model_slug}",
                    f"resolved_reasoning_effort={reasoning_effort}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    f"spawn_tool_call_ref=run://{dispatch_rel}",
                    "",
                ]
            ),
        )


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    closeout_round_id = "closeout-smoke-terminal-stop-briefing"
    stop_round_id = "challenge-smoke-terminal-stop-halt"
    goal_round_id = "challenge-smoke-terminal-stop-goal"

    with tempfile.TemporaryDirectory(prefix="agent-loop-stop-smoke-") as tmp:
        run_dir = Path(tmp)
        write(run_dir / "source.md", "# Source\n\nSmoke terminal stop briefing.\n")
        write(
            run_dir / "AGENTS.md",
            "# AGENTS\n\n## LoopCompletionGate\n\nSmoke-local policy anchor.\n",
        )
        write(
            run_dir / "ideas.md",
            "\n".join(
                [
                    "# Ideas",
                    "",
                    "## Ideation Gate",
                    "",
                    "- `ideation_status`: `not_material`",
                    "- `lane_count`: `0`",
                    "- `cap`: `timebox_minutes=1 candidate_limit=1 external_source_limit=1`",
                    "- `skip_or_reopen_reason`: `ideation_not_material`",
                    "",
                    "ideation_not_material: smoke fixture deterministic terminal validation.",
                    "",
                ]
            ),
        )
        write(run_dir / "research.md", "# Research\n\nSmoke fixture.\n")
        write(
            run_dir / "revised-plan.md",
            "\n".join(
                [
                    "# Revised Plan",
                    "",
                    "- Research terminal closeout requirements",
                    "- Add stop-only briefing fields",
                    "- Validate terminal receipt output",
                    "",
                    "## Remaining Required Stages",
                    "",
                    "- none",
                    "",
                ]
            ),
        )
        write(
            run_dir / "evidence.md",
            "\n".join(
                [
                    "# Evidence",
                    "",
                    "- Implementation:",
                    "  - terminal stop briefing fields added",
                    "- Validation:",
                    "  - validate_terminal_reply.py passed canonical generated receipt",
                    "  - closeout_gate.py emitted stop receipt",
                    "",
                ]
            ),
        )
        source_digest = compute_source_digest(run_dir)
        policy_ref_digest_text = policy_ref_digests(run_dir)
        stage_graph_digest = file_sha256_digest(run_dir / "revised-plan.md")
        adapter_manifest_ref = "run://authority/default-adapter.json"
        research_cycle_ref = "run://research-cycles/initial-research.json"
        completion_subject_ref = "run://completion-subjects/repo-diff.json"
        challenge_cycle_ref = "run://challenge-cycles/current-goal-cycle.json"
        authority_record_ref = "run://authority/run-authority.json"
        goal_digest = sha256_text("smoke terminal stop briefing")

        write_json(
            run_dir / "authority" / "default-adapter.json",
            {
                "adapter_manifest_version": "v1",
                "manifest_ref": adapter_manifest_ref,
                "adapter_manifest_mode": "default_conservative",
                "agent_loop_override_status": "none",
                "agent_loop_override": {},
                "supported_subject_types": ["repo_diff"],
            },
        )
        adapter_effective_config_digest = file_sha256_digest(run_dir / "authority" / "default-adapter.json")
        write_json(
            run_dir / "completion-subjects" / "repo-diff.json",
            {
                "completion_subject_type": "repo_diff",
                "source_digest": source_digest,
                "stage_graph_digest": stage_graph_digest,
                "summary": "smoke terminal stop briefing implementation artifacts",
            },
        )
        completion_subject_digest = file_sha256_digest(run_dir / "completion-subjects" / "repo-diff.json")
        research_cycle_id = "research-cycle-smoke-initial"
        write_research_lane_artifacts(
            run_dir=run_dir,
            research_cycle_id=research_cycle_id,
            source_digest=source_digest,
        )
        write_json(
            run_dir / "research-cycles" / "initial-research.json",
            {
                "cycle_id": research_cycle_id,
                "research_cycle_schema_version": REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION,
                "source_digest": source_digest,
                "authority_revision_at_dispatch": "1",
                "authority_epoch_at_dispatch": "1",
                "lanes": [
                    {
                        "lane": lane,
                        "verdict": "merged",
                        "artifact_ref": f"research-lanes/{lane}.md",
                    }
                    for lane in RESEARCH_LANES
                ],
                "all_lanes_merged": True,
            },
        )
        research_cycle_digest_set = file_sha256_digest(run_dir / "research-cycles" / "initial-research.json")
        authority_path = run_dir / "authority" / "run-authority.json"
        pre_authority_path = run_dir / "authority" / "pre-run-authority-active.json"
        pre_authority_payload = {
            "run_id": "smoke-terminal-stop",
            "project_root_ref": "run://.",
            "project_identity_digest": sha256_text("smoke-project"),
            "vcs_identity": "absent",
            "cwd_root_binding": str(run_dir.resolve()),
            "goal_digest": goal_digest,
            "source_digest": source_digest,
            "stage_graph_digest": stage_graph_digest,
            "adapter_manifest_ref": adapter_manifest_ref,
            "adapter_conformance_status": "compatible",
            "adapter_effective_config_digest": adapter_effective_config_digest,
            "completion_subject_type": "repo_diff",
            "completion_subject_digest": completion_subject_digest,
            "status": "active",
            "supersedes": "none",
            "superseded_by": "none",
            "schema_version": REQUIRED_AUTHORITY_SCHEMA_VERSION,
            "policy_version": REQUIRED_AUTHORITY_POLICY_VERSION,
            "prompt_version": REQUIRED_AUTHORITY_PROMPT_VERSION,
            "validator_version": REQUIRED_AUTHORITY_VALIDATOR_VERSION,
            "authority_revision": "1",
            "authority_epoch": "1",
            "last_writer_id": "smoke-controller",
        }
        write_json(pre_authority_path, pre_authority_payload)
        write_json(
            authority_path,
            {
                "run_id": "smoke-terminal-stop",
                "project_root_ref": "run://.",
                "project_identity_digest": sha256_text("smoke-project"),
                "vcs_identity": "absent",
                "cwd_root_binding": str(run_dir.resolve()),
                "goal_digest": goal_digest,
                "source_digest": source_digest,
                "stage_graph_digest": stage_graph_digest,
                "adapter_manifest_ref": adapter_manifest_ref,
                "adapter_conformance_status": "compatible",
                "adapter_effective_config_digest": adapter_effective_config_digest,
                "completion_subject_type": "repo_diff",
                "completion_subject_digest": completion_subject_digest,
                "status": "completed",
                "supersedes": "none",
                "superseded_by": "none",
                "schema_version": REQUIRED_AUTHORITY_SCHEMA_VERSION,
                "policy_version": REQUIRED_AUTHORITY_POLICY_VERSION,
                "prompt_version": REQUIRED_AUTHORITY_PROMPT_VERSION,
                "validator_version": REQUIRED_AUTHORITY_VALIDATOR_VERSION,
                "authority_revision": "1",
                "authority_epoch": "1",
                "last_writer_id": "smoke-controller",
                "cas_transition": "active_to_completed",
                "cas_result": "success",
                "cas_expected_status": "active",
                "cas_target_status": "completed",
                "cas_expected_authority_revision": "1",
                "cas_expected_authority_epoch": "1",
                "cas_transition_ref": "run://authority/cas-transition.json",
            },
        )
        write_json(
            run_dir / "authority" / "cas-transition.json",
            {
                "authority_transition_receipt_version": "v1",
                "transition": "active_to_completed",
                "result": "success",
                "pre_status": "active",
                "post_status": "completed",
                "authority_record_ref": authority_record_ref,
                "authority_revision": "1",
                "authority_epoch": "1",
                "pre_authority_ref": "run://authority/pre-run-authority-active.json",
                "pre_authority_digest": file_sha256_digest(pre_authority_path),
                "post_authority_digest": file_sha256_digest(authority_path),
            },
        )
        challenge_cycle_id = "cycle-smoke-current-goal"
        write_json(
            run_dir / "challenge-cycles" / "current-goal-cycle.json",
            {
                "cycle_id": challenge_cycle_id,
                "challenge_cycle_schema_version": REQUIRED_CHALLENGE_CYCLE_SCHEMA_VERSION,
                "authority_record_ref": authority_record_ref,
                "authority_revision_at_dispatch": "1",
                "authority_epoch_at_dispatch": "1",
                "schema_version": REQUIRED_AUTHORITY_SCHEMA_VERSION,
                "policy_version": REQUIRED_AUTHORITY_POLICY_VERSION,
                "prompt_version": REQUIRED_AUTHORITY_PROMPT_VERSION,
                "validator_version": REQUIRED_AUTHORITY_VALIDATOR_VERSION,
                "reviewed_digest_set": {
                    "source_digest": source_digest,
                    "stage_graph_digest": stage_graph_digest,
                    "adapter_manifest_ref": adapter_manifest_ref,
                    "adapter_effective_config_digest": adapter_effective_config_digest,
                    "completion_subject_type": "repo_diff",
                    "completion_subject_ref": completion_subject_ref,
                    "completion_subject_digest": completion_subject_digest,
                },
                "lanes": [
                    {
                        "lane": viewpoint,
                        "verdict": "allow",
                        "artifact_ref": f"proof/goal_completion-{viewpoint}.md",
                    }
                    for viewpoint in VIEWPOINTS
                ],
                "stop_lanes": [
                    {
                        "lane": viewpoint,
                        "verdict": "allow",
                        "artifact_ref": f"proof/stop_authorization-{viewpoint}.md",
                    }
                    for viewpoint in VIEWPOINTS
                ],
                "all_lanes_allow": True,
            },
        )
        challenge_cycle_digest_set = file_sha256_digest(run_dir / "challenge-cycles" / "current-goal-cycle.json")
        v3_bindings = {
            "authority_record_ref": authority_record_ref,
            "authority_revision": "1",
            "authority_epoch": "1",
            "adapter_manifest_ref": adapter_manifest_ref,
            "adapter_effective_config_digest": adapter_effective_config_digest,
            "completion_subject_type": "repo_diff",
            "completion_subject_digest": completion_subject_digest,
            "stage_graph_digest": stage_graph_digest,
            "challenge_cycle_ref": challenge_cycle_ref,
            "challenge_cycle_digest_set": challenge_cycle_digest_set,
        }

        placeholder_stop = consensus_evidence(
            phase="stop_authorization",
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest="placeholder",
            source_digest=source_digest,
            refs=[f"proof/stop_authorization-{viewpoint}.md" for viewpoint in VIEWPOINTS],
            policy_ref_digest_text=policy_ref_digest_text,
            v3_bindings=v3_bindings,
        )
        placeholder_goal = consensus_evidence(
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest="placeholder",
            source_digest=source_digest,
            refs=[f"proof/goal_completion-{viewpoint}.md" for viewpoint in VIEWPOINTS],
            policy_ref_digest_text=policy_ref_digest_text,
            v3_bindings=v3_bindings,
        )
        write(
            run_dir / "handoff.md",
            handoff_text(
                closeout_round_id=closeout_round_id,
                stop_evidence=placeholder_stop,
                goal_evidence=placeholder_goal,
                source_digest=source_digest,
                stage_graph_digest=stage_graph_digest,
                adapter_manifest_ref=adapter_manifest_ref,
                adapter_effective_config_digest=adapter_effective_config_digest,
                research_cycle_ref=research_cycle_ref,
                research_cycle_digest_set=research_cycle_digest_set,
                completion_subject_ref=completion_subject_ref,
                completion_subject_digest=completion_subject_digest,
                challenge_cycle_ref=challenge_cycle_ref,
                challenge_cycle_digest_set=challenge_cycle_digest_set,
            ),
        )
        subject_digest = compute_subject_digest(run_dir)
        stop_refs = [f"run://proof/stop_authorization-{viewpoint}.md" for viewpoint in VIEWPOINTS]
        goal_refs = [f"run://proof/goal_completion-{viewpoint}.md" for viewpoint in VIEWPOINTS]
        stop_evidence = consensus_evidence(
            phase="stop_authorization",
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=stop_refs,
            policy_ref_digest_text=policy_ref_digest_text,
            v3_bindings=v3_bindings,
        )
        goal_evidence = consensus_evidence(
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=goal_refs,
            policy_ref_digest_text=policy_ref_digest_text,
            v3_bindings=v3_bindings,
        )
        write(
            run_dir / "handoff.md",
            handoff_text(
                closeout_round_id=closeout_round_id,
                stop_evidence=stop_evidence,
                goal_evidence=goal_evidence,
                source_digest=source_digest,
                stage_graph_digest=stage_graph_digest,
                adapter_manifest_ref=adapter_manifest_ref,
                adapter_effective_config_digest=adapter_effective_config_digest,
                research_cycle_ref=research_cycle_ref,
                research_cycle_digest_set=research_cycle_digest_set,
                completion_subject_ref=completion_subject_ref,
                completion_subject_digest=completion_subject_digest,
                challenge_cycle_ref=challenge_cycle_ref,
                challenge_cycle_digest_set=challenge_cycle_digest_set,
            ),
        )
        if compute_subject_digest(run_dir) != subject_digest:
            print("[FAIL] smoke subject digest shifted after proof insertion", file=sys.stderr)
            return 1

        write_lane_artifacts(
            run_dir=run_dir,
            phase="stop_authorization",
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            challenge_cycle_id=challenge_cycle_id,
            authority_record_ref=authority_record_ref,
            subject_digest=subject_digest,
            source_digest=source_digest,
            policy_ref_digest_text=policy_ref_digest_text,
        )
        write_lane_artifacts(
            run_dir=run_dir,
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            challenge_cycle_id=challenge_cycle_id,
            authority_record_ref=authority_record_ref,
            subject_digest=subject_digest,
            source_digest=source_digest,
            policy_ref_digest_text=policy_ref_digest_text,
        )

        handoff_path = run_dir / "handoff.md"
        original_handoff = handoff_path.read_text(encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(
                f"- `handoff_schema_version`: `{REQUIRED_AUTHORITY_SCHEMA_VERSION}`",
                "- `handoff_schema_version`: `v2-stop-consensus`",
            ),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "terminal stop with v2 handoff schema"):
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_path = run_dir / "challenge-cycles" / "current-goal-cycle.json"
        original_cycle = cycle_path.read_text(encoding="utf-8")
        cycle_payload = json.loads(original_cycle)
        cycle_payload["reviewed_digest_set"]["source_digest"] = "0" * 64
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle with mismatched reviewed source digest"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["lanes"] = cycle_payload["lanes"][:-1]
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle with partial lane set"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["stop_lanes"] = cycle_payload["stop_lanes"][:-1]
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle with partial stop lane set"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload.pop("cycle_id", None)
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle without cycle_id"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["lanes"][0]["artifact_ref"] = f"proof/stop_authorization-{VIEWPOINTS[0]}.md"
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle refs different from goal completion aggregate refs"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        alternate_stop = run_dir / "proof" / f"alternate_stop_authorization-{VIEWPOINTS[0]}.md"
        original_stop_lane = (run_dir / "proof" / f"stop_authorization-{VIEWPOINTS[0]}.md").read_text(encoding="utf-8")
        alternate_stop.write_text(original_stop_lane, encoding="utf-8")
        mismatched_stop_refs = [f"run://proof/alternate_stop_authorization-{VIEWPOINTS[0]}.md"] + [
            f"run://proof/stop_authorization-{viewpoint}.md" for viewpoint in VIEWPOINTS[1:]
        ]
        mismatched_stop_evidence = consensus_evidence(
            phase="stop_authorization",
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=mismatched_stop_refs,
            policy_ref_digest_text=policy_ref_digest_text,
            v3_bindings=v3_bindings,
        )
        handoff_path.write_text(original_handoff.replace(stop_evidence, mismatched_stop_evidence), encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "stop consensus refs different from challenge cycle stop_lanes"):
            return 1
        alternate_stop.unlink()
        handoff_path.write_text(original_handoff, encoding="utf-8")

        duplicate_before_refs = goal_evidence.replace(" refs=", " allow_count=5 refs=")
        handoff_path.write_text(
            original_handoff.replace(goal_evidence, duplicate_before_refs),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "goal completion evidence with duplicate inline field"):
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        duplicate_binding_before_refs = goal_evidence.replace(" refs=", " authority_record_ref=run://authority/other.json refs=")
        handoff_path.write_text(
            original_handoff.replace(goal_evidence, duplicate_binding_before_refs),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "goal completion evidence with duplicate authority binding field"):
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        duplicate_viewpoint_set = goal_evidence.replace(
            "viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality",
            "viewpoint_set=architecture_dependency|architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality",
        )
        handoff_path.write_text(
            original_handoff.replace(goal_evidence, duplicate_viewpoint_set),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "goal completion evidence with duplicate viewpoint_set token"):
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        tampered_lane = run_dir / "proof" / f"goal_completion-{VIEWPOINTS[0]}.md"
        original_tampered_lane = tampered_lane.read_text(encoding="utf-8")
        tampered_lane.write_text(
            "\n".join(
                line
                for line in original_tampered_lane.splitlines()
                if not line.startswith("spawn_tool_call_ref=")
            )
            + "\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane without dispatch ref"):
            return 1
        tampered_lane.write_text(original_tampered_lane, encoding="utf-8")

        tampered_lane.write_text(
            original_tampered_lane.replace("model_resolution_basis_ref=skill:model-catalog-smoke", "model_resolution_basis_ref=none"),
            encoding="utf-8",
        )
        direct_cycle_errors = challenge_cycle_validation_errors(
            cycle_path=cycle_path,
            challenge_cycle_digest_set=challenge_cycle_digest_set,
            authority_record_ref=authority_record_ref,
            authority_path=authority_path,
            run_authority_revision="1",
            run_authority_epoch="1",
            source_digest=source_digest,
            stage_graph_digest=stage_graph_digest,
            adapter_manifest_ref=adapter_manifest_ref,
            adapter_effective_config_digest=adapter_effective_config_digest,
            completion_subject_type="repo_diff",
            completion_subject_ref=completion_subject_ref,
            completion_subject_digest=completion_subject_digest,
            composite_subject_digest="none",
            goal_completion_refs=None,
            stop_consensus_refs=None,
            run_dir=run_dir,
        )
        if not any("model_resolution_basis_ref" in error for error in direct_cycle_errors):
            print("[FAIL] challenge-cycle-only validator missed placeholder model resolution basis", file=sys.stderr)
            return 1
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane with placeholder model resolution basis"):
            return 1
        tampered_lane.write_text(original_tampered_lane, encoding="utf-8")

        goal_model_paths = [
            path
            for viewpoint in VIEWPOINTS
            for path in (
                run_dir / "proof" / f"goal_completion-{viewpoint}.md",
                run_dir / "dispatch" / f"goal_completion-{viewpoint}.md",
            )
        ]
        original_goal_model_text = {path: path.read_text(encoding="utf-8") for path in goal_model_paths}
        for path, text in original_goal_model_text.items():
            path.write_text(
                text.replace("resolved_reasoning_effort=xhigh", "resolved_reasoning_effort=high").replace(
                    "spawn_tool_args_reasoning_effort=xhigh",
                    "spawn_tool_args_reasoning_effort=high",
                ),
                encoding="utf-8",
            )
        direct_cycle_errors = challenge_cycle_validation_errors(
            cycle_path=cycle_path,
            challenge_cycle_digest_set=challenge_cycle_digest_set,
            authority_record_ref=authority_record_ref,
            authority_path=authority_path,
            run_authority_revision="1",
            run_authority_epoch="1",
            source_digest=source_digest,
            stage_graph_digest=stage_graph_digest,
            adapter_manifest_ref=adapter_manifest_ref,
            adapter_effective_config_digest=adapter_effective_config_digest,
            completion_subject_type="repo_diff",
            completion_subject_ref=completion_subject_ref,
            completion_subject_digest=completion_subject_digest,
            composite_subject_digest="none",
            goal_completion_refs=None,
            stop_consensus_refs=None,
            run_dir=run_dir,
        )
        if not any("model mix" in error for error in direct_cycle_errors):
            print("[FAIL] challenge-cycle-only validator missed invalid five-lane model mix", file=sys.stderr)
            return 1
        for path, text in original_goal_model_text.items():
            path.write_text(text, encoding="utf-8")

        duplicate_agent_paths = [
            run_dir / "proof" / f"goal_completion-{VIEWPOINTS[1]}.md",
            run_dir / "dispatch" / f"goal_completion-{VIEWPOINTS[1]}.md",
        ]
        original_duplicate_agent_text = {path: path.read_text(encoding="utf-8") for path in duplicate_agent_paths}
        for path, text in original_duplicate_agent_text.items():
            path.write_text(text.replace("agent_id=goal_completion-agent-2", "agent_id=goal_completion-agent-1"), encoding="utf-8")
        direct_cycle_errors = challenge_cycle_validation_errors(
            cycle_path=cycle_path,
            challenge_cycle_digest_set=challenge_cycle_digest_set,
            authority_record_ref=authority_record_ref,
            authority_path=authority_path,
            run_authority_revision="1",
            run_authority_epoch="1",
            source_digest=source_digest,
            stage_graph_digest=stage_graph_digest,
            adapter_manifest_ref=adapter_manifest_ref,
            adapter_effective_config_digest=adapter_effective_config_digest,
            completion_subject_type="repo_diff",
            completion_subject_ref=completion_subject_ref,
            completion_subject_digest=completion_subject_digest,
            composite_subject_digest="none",
            goal_completion_refs=None,
            stop_consensus_refs=None,
            run_dir=run_dir,
        )
        if not any("agent_id is duplicated" in error for error in direct_cycle_errors):
            print("[FAIL] challenge-cycle-only validator missed duplicate agent_id", file=sys.stderr)
            return 1
        for path, text in original_duplicate_agent_text.items():
            path.write_text(text, encoding="utf-8")

        tampered_dispatch = run_dir / "dispatch" / f"goal_completion-{VIEWPOINTS[0]}.md"
        original_tampered_dispatch = tampered_dispatch.read_text(encoding="utf-8")
        tampered_dispatch.write_text(
            original_tampered_dispatch.replace("dispatch_receipt_version=v1", "dispatch_receipt_version=legacy"),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane with malformed dispatch receipt"):
            return 1
        tampered_dispatch.write_text(original_tampered_dispatch, encoding="utf-8")

        tampered_dispatch.write_text(
            "\n".join(
                line
                for line in original_tampered_dispatch.splitlines()
                if not line.startswith("model_resolution_basis_ref=")
            )
            + "\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle dispatch without model resolution basis"):
            return 1
        tampered_dispatch.write_text(original_tampered_dispatch, encoding="utf-8")

        tampered_dispatch.write_text(
            original_tampered_dispatch + "phase=wrong_phase\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane with duplicate dispatch field"):
            return 1
        tampered_dispatch.write_text(original_tampered_dispatch, encoding="utf-8")

        original_plan = (run_dir / "revised-plan.md").read_text(encoding="utf-8")
        (run_dir / "revised-plan.md").write_text(original_plan + "\n- stale digest mutation\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "stale stage_graph_digest after revised-plan mutation"):
            return 1
        (run_dir / "revised-plan.md").write_text(original_plan, encoding="utf-8")

        research_lane_path = run_dir / "research-lanes" / f"{RESEARCH_LANES[0]}.md"
        original_research_lane = research_lane_path.read_text(encoding="utf-8")
        research_lane_path.write_text(
            original_research_lane.replace(f"source_digest={source_digest}", f"source_digest={'0' * 64}"),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research lane with stale source digest"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_lane_path.write_text(
            "\n".join(
                line
                for line in original_research_lane.splitlines()
                if not line.startswith("model_resolution_basis_ref=")
            )
            + "\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research lane without model resolution basis"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_lane_path.write_text(original_research_lane + "resolved_reasoning_effort=low\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "research lane with duplicate model effort field"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_lane_path.write_text(original_research_lane + f"viewpoint={RESEARCH_LANES[-1]}\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "research lane artifact with conflicting lane alias"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_lane_path.write_text(original_research_lane.replace("vote=allow", "vote=deny"), encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "research lane artifact with denying vote"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_lane_path.write_text(original_research_lane.replace("verdict=merged", "verdict=deny"), encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "research lane artifact with conflicting verdict alias"):
            return 1
        research_lane_path.write_text(original_research_lane, encoding="utf-8")

        research_dispatch_path = run_dir / "dispatch" / f"initial_research-{RESEARCH_LANES[0]}.md"
        original_research_dispatch = research_dispatch_path.read_text(encoding="utf-8")
        research_dispatch_path.write_text(
            original_research_dispatch.replace("phase=initial_research", "phase=wrong_phase"),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research lane with malformed dispatch receipt"):
            return 1
        research_dispatch_path.write_text(original_research_dispatch, encoding="utf-8")

        research_dispatch_path.write_text(
            original_research_dispatch + "research_lane=wrong_lane\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research lane with duplicate dispatch field"):
            return 1
        research_dispatch_path.write_text(original_research_dispatch, encoding="utf-8")

        research_dispatch_path.write_text(
            "\n".join(
                line
                for line in original_research_dispatch.splitlines()
                if not line.startswith("model_resolution_basis_ref=")
            )
            + "\n",
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research dispatch without model resolution basis"):
            return 1
        research_dispatch_path.write_text(original_research_dispatch, encoding="utf-8")

        mix_lane = run_dir / "research-lanes" / f"{RESEARCH_LANES[-1]}.md"
        original_mix_lane = mix_lane.read_text(encoding="utf-8")
        mix_dispatch = run_dir / "dispatch" / f"initial_research-{RESEARCH_LANES[-1]}.md"
        original_mix_dispatch = mix_dispatch.read_text(encoding="utf-8")
        mix_lane.write_text(original_mix_lane.replace("resolved_reasoning_effort=high", "resolved_reasoning_effort=xhigh"), encoding="utf-8")
        mix_dispatch.write_text(
            original_mix_dispatch.replace("resolved_reasoning_effort=high", "resolved_reasoning_effort=xhigh").replace(
                "spawn_tool_args_reasoning_effort=high",
                "spawn_tool_args_reasoning_effort=xhigh",
            ),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research cycle with invalid five-lane model mix"):
            return 1
        mix_lane.write_text(original_mix_lane, encoding="utf-8")
        mix_dispatch.write_text(original_mix_dispatch, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace("- `work_type`: `implementation`", "- `work_type`: `research`"),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research work_type with repo_diff completion subject"):
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        authority_path = run_dir / "authority" / "run-authority.json"
        original_authority = authority_path.read_text(encoding="utf-8")
        authority_payload = json.loads(original_authority)
        authority_payload.pop("cas_expected_status", None)
        authority_path.write_text(json.dumps(authority_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority record without CAS expected status"):
            return 1
        authority_path.write_text(original_authority, encoding="utf-8")

        authority_payload = json.loads(original_authority)
        authority_payload.pop("cas_transition_ref", None)
        authority_path.write_text(json.dumps(authority_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority record without CAS transition receipt ref"):
            return 1
        authority_path.write_text(original_authority, encoding="utf-8")

        cas_transition_path = run_dir / "authority" / "cas-transition.json"
        original_cas_transition = cas_transition_path.read_text(encoding="utf-8")
        cas_transition_payload = json.loads(original_cas_transition)
        cas_transition_payload["post_authority_digest"] = "0" * 64
        cas_transition_path.write_text(json.dumps(cas_transition_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority CAS transition receipt with stale post digest"):
            return 1
        cas_transition_path.write_text(original_cas_transition, encoding="utf-8")

        cas_transition_payload = json.loads(original_cas_transition)
        cas_transition_payload.pop("pre_authority_ref", None)
        cas_transition_path.write_text(json.dumps(cas_transition_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority CAS transition receipt without pre-state ref"):
            return 1
        cas_transition_path.write_text(original_cas_transition, encoding="utf-8")

        cas_transition_path.write_text(
            original_cas_transition.rstrip()[:-1] + ',\n  "result": "failure"\n}\n',
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority CAS transition receipt with duplicate field"):
            return 1
        cas_transition_path.write_text(original_cas_transition, encoding="utf-8")

        (run_dir / "run-authority.json").write_text("not json but still a conflicting authority file\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority with duplicate non-json authority record"):
            return 1
        (run_dir / "run-authority.json").unlink()

        authority_path.write_text(
            original_authority.rstrip()[:-1] + ',\n  "status": "active"\n}\n',
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority with duplicate JSON key"):
            return 1
        authority_path.write_text(original_authority, encoding="utf-8")

        authority_path.write_text(
            original_authority.rstrip()[:-1] + ',\n  "authorityRevision": "999"\n}\n',
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "terminal authority with duplicate JSON alias key"):
            return 1
        authority_path.write_text(original_authority, encoding="utf-8")

        cycle_path = run_dir / "challenge-cycles" / "current-goal-cycle.json"
        original_cycle = cycle_path.read_text(encoding="utf-8")
        cycle_path.write_text(
            original_cycle.rstrip()[:-1] + ',\n  "allLanesAllow": false\n}\n',
            encoding="utf-8",
        )
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle with duplicate JSON alias key"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["reviewed_digest_set"]["sourceDigest"] = "0" * 64
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle with nested duplicate JSON alias key"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["lanes"][0]["vote"] = "deny"
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane with conflicting verdict aliases"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        cycle_payload = json.loads(original_cycle)
        cycle_payload["lanes"][0]["ref"] = f"proof/stop_authorization-{VIEWPOINTS[0]}.md"
        cycle_path.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(challenge_cycle_digest_set, file_sha256_digest(cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "challenge cycle lane with conflicting artifact ref aliases"):
            return 1
        cycle_path.write_text(original_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        research_cycle_path = run_dir / "research-cycles" / "initial-research.json"
        original_research_cycle = research_cycle_path.read_text(encoding="utf-8")
        research_cycle_payload = json.loads(original_research_cycle)
        research_cycle_payload["lanes"][0]["vote"] = "deny"
        research_cycle_path.write_text(
            json.dumps(research_cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        handoff_path.write_text(
            original_handoff.replace(research_cycle_digest_set, file_sha256_digest(research_cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research cycle lane with conflicting verdict aliases"):
            return 1
        research_cycle_path.write_text(original_research_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        research_cycle_payload = json.loads(original_research_cycle)
        research_cycle_payload["lanes"][0]["viewpoint"] = RESEARCH_LANES[-1]
        research_cycle_path.write_text(
            json.dumps(research_cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        handoff_path.write_text(
            original_handoff.replace(research_cycle_digest_set, file_sha256_digest(research_cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research cycle lane with conflicting lane/viewpoint aliases"):
            return 1
        research_cycle_path.write_text(original_research_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        research_cycle_payload = json.loads(original_research_cycle)
        research_cycle_payload["lanes"][0]["ref"] = "research-lanes/not-the-lane.md"
        research_cycle_path.write_text(
            json.dumps(research_cycle_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        handoff_path.write_text(
            original_handoff.replace(research_cycle_digest_set, file_sha256_digest(research_cycle_path)),
            encoding="utf-8",
        )
        if not expect_validation_failure(scripts_dir, run_dir, "research cycle lane with conflicting artifact ref aliases"):
            return 1
        research_cycle_path.write_text(original_research_cycle, encoding="utf-8")
        handoff_path.write_text(original_handoff, encoding="utf-8")

        adapter_path = run_dir / "authority" / "default-adapter.json"
        original_adapter = adapter_path.read_text(encoding="utf-8")
        adapter_payload = json.loads(original_adapter)
        adapter_payload["agent_loop_override_status"] = "validated"
        adapter_payload["agent_loop_override"] = {"final_proof_semantics": "weakened"}
        adapter_path.write_text(json.dumps(adapter_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not expect_validation_failure(scripts_dir, run_dir, "adapter manifest with forbidden override key"):
            return 1
        adapter_path.write_text(original_adapter, encoding="utf-8")

        adapter_payload = json.loads(original_adapter)
        adapter_payload["project_policy_refs"] = ["AGENTS.md#LoopCompletionGate"]
        adapter_path.write_text(json.dumps(adapter_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        project_policy_digest_text = policy_ref_digests(run_dir)
        proof_missing_project_policy_ref = consensus_evidence(
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=goal_refs,
            policy_ref_digest_text=project_policy_digest_text,
            v3_bindings=v3_bindings,
        )
        proof_missing_project_policy_ref = proof_missing_project_policy_ref.replace(
            f"loaded_policy_refs={LOADED_POLICY_REFS}",
            "loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof",
        )
        if final_policy_route_metadata_is_valid_inline(proof_missing_project_policy_ref, run_dir):
            print("[FAIL] adapter-declared project policy ref was not required in loaded_policy_refs", file=sys.stderr)
            return 1
        proof_duplicate_policy_ref = proof_missing_project_policy_ref.replace(
            "loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof",
            (
                "loaded_policy_refs=SKILL.md#NonNegotiableInvariants|"
                "SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof"
            ),
        )
        if final_policy_route_metadata_is_valid_inline(proof_duplicate_policy_ref, run_dir):
            print("[FAIL] duplicate loaded_policy_refs token unexpectedly passed final policy metadata", file=sys.stderr)
            return 1
        adapter_payload["project_policy_refs"] = ["unsupported.md#Policy"]
        adapter_path.write_text(json.dumps(adapter_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if policy_ref_digests(run_dir):
            print("[FAIL] unsupported adapter project_policy_refs unexpectedly produced policy digests", file=sys.stderr)
            return 1
        adapter_path.write_text(original_adapter, encoding="utf-8")

        # Some negative checks rewrite handoff.md; refresh proof artifacts after
        # restoring the canonical handoff so freshness checks remain meaningful.
        write_lane_artifacts(
            run_dir=run_dir,
            phase="stop_authorization",
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            challenge_cycle_id=challenge_cycle_id,
            authority_record_ref=authority_record_ref,
            subject_digest=subject_digest,
            source_digest=source_digest,
            policy_ref_digest_text=policy_ref_digest_text,
        )
        write_lane_artifacts(
            run_dir=run_dir,
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            challenge_cycle_id=challenge_cycle_id,
            authority_record_ref=authority_record_ref,
            subject_digest=subject_digest,
            source_digest=source_digest,
            policy_ref_digest_text=policy_ref_digest_text,
        )

        tampered_lane = run_dir / "proof" / f"goal_completion-{VIEWPOINTS[0]}.md"
        original_lane = tampered_lane.read_text(encoding="utf-8")
        tampered_lane.write_text(
            "\n".join(
                line
                for line in original_lane.splitlines()
                if not line.startswith("agent_role=")
            )
            + "\n",
            encoding="utf-8",
        )
        invalid = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        tampered_lane.write_text(original_lane, encoding="utf-8")
        if invalid.returncode == 0:
            print("[FAIL] final challenge lane without agent_role unexpectedly passed validation", file=sys.stderr)
            return 1

        tampered_lane.write_text(
            "\n".join(
                line
                for line in original_lane.splitlines()
                if not line.startswith("loaded_policy_refs=")
            )
            + "\n",
            encoding="utf-8",
        )
        invalid = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        tampered_lane.write_text(original_lane, encoding="utf-8")
        if invalid.returncode == 0:
            print("[FAIL] final challenge lane without loaded_policy_refs unexpectedly passed validation", file=sys.stderr)
            return 1

        tampered_lane.write_text(
            original_lane.replace(
                "coverage_viewpoints=architecture_dependency",
                "coverage_viewpoints=failure_verification",
            ),
            encoding="utf-8",
        )
        invalid = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        tampered_lane.write_text(original_lane, encoding="utf-8")
        if invalid.returncode == 0:
            print("[FAIL] final challenge lane with swapped coverage unexpectedly passed validation", file=sys.stderr)
            return 1

        tampered_lane.write_text(
            original_lane.replace(
                "coverage_viewpoints=architecture_dependency",
                "coverage_viewpoints=architecture_dependency|architecture_dependency",
            ),
            encoding="utf-8",
        )
        invalid = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        tampered_lane.write_text(original_lane, encoding="utf-8")
        if invalid.returncode == 0:
            print("[FAIL] final challenge lane with duplicate coverage unexpectedly passed validation", file=sys.stderr)
            return 1

        tampered_lane.write_text(original_lane + "vote=deny\n", encoding="utf-8")
        invalid = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        tampered_lane.write_text(original_lane, encoding="utf-8")
        if invalid.returncode == 0:
            print("[FAIL] final challenge lane with duplicate vote unexpectedly passed validation", file=sys.stderr)
            return 1

        handoff_path = run_dir / "handoff.md"
        handoff_path.write_text(handoff_path.read_text(encoding="utf-8"), encoding="utf-8")
        refreshed_handoff_validate = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "validate_handoff.py"),
                str(run_dir),
                "--require-consensus",
            ],
            text=True,
            capture_output=True,
        )
        if refreshed_handoff_validate.returncode != 0:
            print("[FAIL] proof-only handoff refresh made final challenge artifacts appear stale", file=sys.stderr)
            print(refreshed_handoff_validate.stdout, file=sys.stderr)
            print(refreshed_handoff_validate.stderr, file=sys.stderr)
            return 1

        emit_env = {
            **os.environ,
            "AGENT_LOOP_CLOSEOUT_GATE": "1",
            "AGENT_LOOP_GATE_RUN_DIR": str(run_dir.resolve()),
        }
        emit = subprocess.run(
            [sys.executable, str(scripts_dir / "emit_terminal_reply.py"), str(run_dir)],
            text=True,
            capture_output=True,
            env=emit_env,
        )
        if emit.returncode != 0:
            sys.stderr.write(emit.stdout)
            sys.stderr.write(emit.stderr)
            return emit.returncode
        tampered_reply = emit.stdout + "freeform_wrapup=this should fail\n"
        validate = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_terminal_reply.py"), "--run-dir", str(run_dir)],
            input=tampered_reply,
            text=True,
            capture_output=True,
        )
        if validate.returncode == 0:
            print("[FAIL] tampered terminal reply unexpectedly passed validation", file=sys.stderr)
            print(validate.stdout, file=sys.stderr)
            return 1
        if "stop reply must contain exactly" not in (validate.stdout + validate.stderr):
            print("[FAIL] tampered terminal reply did not exercise reply shape validation", file=sys.stderr)
            print(validate.stdout, file=sys.stderr)
            print(validate.stderr, file=sys.stderr)
            return 1

        gate = subprocess.run(
            [sys.executable, str(scripts_dir / "closeout_gate.py"), str(run_dir)],
            text=True,
            capture_output=True,
        )
        if gate.returncode != 0:
            sys.stderr.write(gate.stdout)
            sys.stderr.write(gate.stderr)
            return gate.returncode

        required_reply_tokens = [
            "run_decision=stop",
            "work_process=",
            "work_summary=",
            "verification_summary=",
            "need_to_know=external API behavior was not exercised",
            "5-lane halt proof allow_unanimous",
            "5-lane completion proof verified",
            "source-first clean audit verified",
        ]
        missing = [token for token in required_reply_tokens if token not in gate.stdout]
        if missing:
            print(f"[FAIL] terminal stop reply missing tokens: {missing}", file=sys.stderr)
            print(gate.stdout, file=sys.stderr)
            return 1

    print("[OK] terminal stop briefing smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
