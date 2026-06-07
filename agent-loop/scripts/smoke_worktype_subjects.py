#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_handoff.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("agent_loop_validate_handoff", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def prepare_run(run_dir: Path, validator, *, work_type: str, review_kind: str, subject_type: str) -> dict[str, object]:
    write(run_dir / "source.md", f"# Source\n\nSmoke {work_type} subject typing.\n")
    write(
        run_dir / "ideas.md",
        "\n".join(
            [
                "# Ideas",
                "",
                "## Ideation Gate",
                "",
                "- `ideation_status`: `not_material`",
                "- `viewpoint_count`: `0`",
                "- `cap`: `timebox_minutes=1 candidate_limit=1 external_source_limit=1`",
                "- `skip_or_reopen_reason`: `ideation_not_material`",
                "",
                "ideation_not_material: work-type subject smoke.",
                "",
            ]
        ),
    )
    write(run_dir / "research.md", "# Research\n\nSubject typing smoke.\n")
    write(run_dir / "revised-plan.md", "# Revised Plan\n\n## Remaining Required Stages\n\n- Finish subject smoke\n")
    write(run_dir / "evidence.md", "# Evidence\n\nSubject smoke fixture.\n")
    write(run_dir / "verification.md", "# Verification\n\nSmoke verification result: pass.\n")
    closeout_round_id = f"closeout-{work_type}-{subject_type}"
    write(
        run_dir / "receipts" / "live-attempt.md",
        "\n".join(
            [
                "attempt_receipt_version=v1",
                f"closeout_round_id={closeout_round_id}",
                "attempt_status=next_action_started",
                "next_action=Finish subject smoke",
                "summary=subject typing smoke live attempt",
                "",
            ]
        ),
    )
    source_digest = validator.compute_source_digest(run_dir)
    stage_graph_digest = validator.file_sha256_digest(run_dir / "revised-plan.md")
    adapter_ref = "run://authority/default-adapter.json"
    write_json(
        run_dir / "authority" / "default-adapter.json",
        {
            "adapter_manifest_version": "v1",
            "manifest_ref": adapter_ref,
            "agent_loop_override_status": "none",
            "agent_loop_override": {},
            "supported_subject_types": [subject_type],
        },
    )
    adapter_digest = validator.file_sha256_digest(run_dir / "authority" / "default-adapter.json")
    subject_ref = f"run://completion-subjects/{subject_type}.json"
    write_json(
        run_dir / "completion-subjects" / f"{subject_type}.json",
        {
            "completion_subject_type": subject_type,
            "source_digest": source_digest,
            "stage_graph_digest": stage_graph_digest,
            "summary": f"{work_type} subject smoke",
        },
    )
    subject_digest = validator.file_sha256_digest(run_dir / "completion-subjects" / f"{subject_type}.json")
    write_json(
        run_dir / "authority" / "run-authority.json",
        {
            "run_id": f"smoke-{work_type}-{subject_type}",
            "project_root_ref": "run://.",
            "project_identity_digest": "0" * 64,
            "vcs_identity": "absent",
            "cwd_root_binding": str(run_dir.resolve()),
            "goal_digest": "1" * 64,
            "source_digest": source_digest,
            "stage_graph_digest": stage_graph_digest,
            "adapter_manifest_ref": adapter_ref,
            "adapter_conformance_status": "compatible",
            "adapter_effective_config_digest": adapter_digest,
            "status": "active",
            "supersedes": "none",
            "superseded_by": "none",
            "schema_version": validator.REQUIRED_AUTHORITY_SCHEMA_VERSION,
            "policy_version": validator.REQUIRED_AUTHORITY_POLICY_VERSION,
            "prompt_version": validator.REQUIRED_AUTHORITY_PROMPT_VERSION,
            "validator_version": validator.REQUIRED_AUTHORITY_VALIDATOR_VERSION,
            "authority_revision": "1",
            "authority_epoch": "1",
            "last_writer_id": "smoke-controller",
        },
    )
    write(run_dir / "handoff.md", "# Handoff\n\nSubject typing smoke placeholder.\n")
    return {
        "handoff_schema_version": validator.REQUIRED_AUTHORITY_SCHEMA_VERSION,
        "working_goal": f"smoke {work_type} subject typing",
        "run_intent": "planning_only",
        "work_type": work_type,
        "review_kind": review_kind,
        "host_resume_mode": "same_turn_only",
        "capability_mode": "delegated_agents_authorized_by_loop_tool_available_smoke",
        "authority_record_ref": "run://authority/run-authority.json",
        "run_authority_status": "active",
        "run_authority_revision": "1",
        "run_authority_epoch": "1",
        "source_digest": source_digest,
        "stage_graph_digest": stage_graph_digest,
        "adapter_manifest_ref": adapter_ref,
        "adapter_conformance_status": "compatible",
        "adapter_effective_config_digest": adapter_digest,
        "resource_telemetry_ref": "none",
        "research_cycle_ref": "none",
        "research_cycle_status": "not_applicable",
        "research_cycle_digest_set": "none",
        "completion_subject_type": subject_type,
        "completion_subject_ref": subject_ref,
        "completion_subject_digest": subject_digest,
        "composite_subject_digest": subject_digest if subject_type == "composite_subject" else "none",
        "challenge_cycle_ref": "none",
        "challenge_cycle_status": "not_applicable",
        "challenge_cycle_digest_set": "none",
        "visible_output_contract": "live_status",
        "current_or_next_stage": "subject typing smoke",
        "stage_status": "live validation",
        "current_batch": "none",
        "risk_tier": "tier0_trivial",
        "implementation_gate_status": "not_applicable",
        "implementation_gate_evidence": "none",
        "remaining_required_stages": ["Finish subject smoke"],
        "latest_evidence_summary": ["subject typing smoke"],
        "blocking_findings": ["none"],
        "residual_risks": ["none"],
        "goal_completion_status": "not_reached",
        "goal_completion_evidence": "subject smoke still live",
        "loop_state": "execution",
        "continuation_mode": "nonstop",
        "closeout_round_id": closeout_round_id,
        "run_decision": "continue",
        "sequential_objectives_status": "open",
        "stop_authorization_status": "not_applicable",
        "stop_authorization_evidence": "none",
        "stop_consensus_status": "not_applicable",
        "stop_consensus_evidence": "none",
        "external_authority_basis": "none",
        "pause_reason": "none",
        "next_mandatory_action": "Finish subject smoke",
        "continue_exit_status": "next_action_started",
        "continue_exit_evidence": f"attempt_ref=receipts/live-attempt.md; closeout_round_id={closeout_round_id}",
        "turn_exit_cause": "not_applicable",
        "turn_exit_evidence": "none",
        "resume_instructions": ["none"],
    }


def write_implementation_challenge_fixture(
    run_dir: Path,
    validator,
    fields: dict[str, object],
    *,
    mode: str,
    viewpoints: list[str],
) -> list[str]:
    refs: list[str] = []
    if len(viewpoints) == 2:
        model_plan = [
            (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
            (validator.TOP_DELEGATED_MODEL_SLUG, "high"),
        ]
    else:
        model_plan = [
            (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
            (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
            (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
            (validator.TOP_DELEGATED_MODEL_SLUG, "high"),
            (validator.TOP_DELEGATED_MODEL_SLUG, "high"),
        ]
    for index, viewpoint in enumerate(viewpoints, start=1):
        model_slug, reasoning_effort = model_plan[index - 1]
        rel = f"implementation-proof/{mode}-{viewpoint}.md"
        dispatch_rel = f"implementation-dispatch/{mode}-{viewpoint}.md"
        refs.append(f"run://{rel}")
        common = [
            f"source_digest={fields['source_digest']}",
            f"stage_graph_digest={fields['stage_graph_digest']}",
            f"authority_record_ref={fields['authority_record_ref']}",
            f"authority_revision={fields['run_authority_revision']}",
            f"authority_epoch={fields['run_authority_epoch']}",
            f"adapter_manifest_ref={fields['adapter_manifest_ref']}",
            f"adapter_effective_config_digest={fields['adapter_effective_config_digest']}",
        ]
        write(
            run_dir / dispatch_rel,
            "\n".join(
                [
                    "dispatch_receipt_version=v1",
                    "agent_role=challenge_agent",
                    f"challenge_review_mode={mode}",
                    f"agent_id={mode}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    *common,
                    f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
                    f"resolved_model_slug={model_slug}",
                    f"resolved_reasoning_effort={reasoning_effort}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    "",
                ]
            ),
        )
        write(
            run_dir / rel,
            "\n".join(
                [
                    "agent_role=challenge_agent",
                    f"challenge_review_mode={mode}",
                    "vote=allow",
                    f"agent_id={mode}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    *common,
                    f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
                    f"resolved_model_slug={model_slug}",
                    f"resolved_reasoning_effort={reasoning_effort}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={model_slug}",
                    f"spawn_tool_args_reasoning_effort={reasoning_effort}",
                    f"spawn_tool_call_ref=run://{dispatch_rel}",
                    "freshness_status=fresh",
                    "",
                ]
            ),
        )
    return refs


def write_research_cycle_fixture(run_dir: Path, validator, fields: dict[str, object]) -> tuple[str, str]:
    cycle_id = "research-cycle-worktype-smoke"
    lanes = sorted(validator.REQUIRED_INITIAL_RESEARCH_LANES)
    model_plan = [
        (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
        (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
        (validator.TOP_DELEGATED_MODEL_SLUG, validator.TOP_DELEGATED_REASONING_EFFORT),
        (validator.TOP_DELEGATED_MODEL_SLUG, "high"),
        (validator.TOP_DELEGATED_MODEL_SLUG, "high"),
    ]
    for index, lane in enumerate(lanes, start=1):
        model_slug, reasoning_effort = model_plan[index - 1]
        dispatch_rel = f"research-dispatch/{lane}.md"
        lane_rel = f"research-lanes/{lane}.md"
        common = [
            "phase=initial_research",
            "agent_role=research_agent",
            f"agent_id=research-agent-{index}",
            f"research_lane={lane}",
            f"research_cycle_id={cycle_id}",
            "source_ref=source.md",
            f"source_digest={fields['source_digest']}",
            f"authority_revision_at_dispatch={fields['run_authority_revision']}",
            f"authority_epoch_at_dispatch={fields['run_authority_epoch']}",
            f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
            f"resolved_model_slug={model_slug}",
            f"resolved_reasoning_effort={reasoning_effort}",
            "model_resolution_basis_ref=skill:model-catalog-smoke",
            f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
            f"spawn_tool_args_model={model_slug}",
            f"spawn_tool_args_reasoning_effort={reasoning_effort}",
        ]
        write(run_dir / dispatch_rel, "\n".join(["dispatch_receipt_version=v1", *common, ""]))
        write(
            run_dir / lane_rel,
            "\n".join([*common, "vote=allow", "verdict=merged", f"spawn_tool_call_ref=run://{dispatch_rel}", ""]),
        )
    cycle_ref = "run://research-cycles/initial-research.json"
    write_json(
        run_dir / "research-cycles" / "initial-research.json",
        {
            "cycle_id": cycle_id,
            "research_cycle_schema_version": validator.REQUIRED_RESEARCH_CYCLE_SCHEMA_VERSION,
            "source_digest": fields["source_digest"],
            "authority_revision_at_dispatch": fields["run_authority_revision"],
            "authority_epoch_at_dispatch": fields["run_authority_epoch"],
            "lanes": [
                {
                    "lane": lane,
                    "verdict": "merged",
                    "artifact_ref": f"research-lanes/{lane}.md",
                }
                for lane in lanes
            ],
            "all_lanes_merged": True,
        },
    )
    return cycle_ref, validator.file_sha256_digest(run_dir / "research-cycles" / "initial-research.json")


def common_authority_lines(fields: dict[str, object]) -> list[str]:
    return [
        f"source_digest={fields['source_digest']}",
        f"stage_graph_digest={fields['stage_graph_digest']}",
        f"authority_record_ref={fields['authority_record_ref']}",
        f"authority_revision={fields['run_authority_revision']}",
        f"authority_epoch={fields['run_authority_epoch']}",
        f"adapter_manifest_ref={fields['adapter_manifest_ref']}",
        f"adapter_effective_config_digest={fields['adapter_effective_config_digest']}",
    ]


def write_strategy_fixture(run_dir: Path, validator, fields: dict[str, object]) -> str:
    dispatch_rel = "implementation-dispatch/strategy.md"
    strategy_rel = "implementation-strategy/strategy.md"
    write(
        run_dir / dispatch_rel,
        "\n".join(
            [
                "dispatch_receipt_version=v1",
                "agent_role=strategy_agent",
                *common_authority_lines(fields),
                f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
                f"resolved_model_slug={validator.TOP_DELEGATED_MODEL_SLUG}",
                f"resolved_reasoning_effort={validator.TOP_DELEGATED_REASONING_EFFORT}",
                f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
                f"spawn_tool_args_model={validator.TOP_DELEGATED_MODEL_SLUG}",
                f"spawn_tool_args_reasoning_effort={validator.TOP_DELEGATED_REASONING_EFFORT}",
                "",
            ]
        ),
    )
    write(
        run_dir / strategy_rel,
        "\n".join(
            [
                "agent_role=strategy_agent",
                "plan_model_policy=strongest_model_required",
                f"plan_model_slug={validator.TOP_DELEGATED_MODEL_SLUG}",
                f"plan_reasoning_effort={validator.TOP_DELEGATED_REASONING_EFFORT}",
                f"dispatch_ref=run://{dispatch_rel}",
                "",
            ]
        ),
    )
    return f"run://{strategy_rel}"


def write_verification_agent_fixture(run_dir: Path, validator, fields: dict[str, object]) -> str:
    dispatch_rel = "verification/verification-agent-dispatch.md"
    artifact_rel = "verification/verification-agent.md"
    write(
        run_dir / dispatch_rel,
        "\n".join(
            [
                "dispatch_receipt_version=v1",
                f"agent_role={validator.REQUIRED_VERIFICATION_AGENT_ROLE}",
                f"verification_agent_mode={validator.REQUIRED_VERIFICATION_AGENT_MODE}",
                "agent_id=verification-agent-1",
                *common_authority_lines(fields),
                f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
                f"resolved_model_slug={validator.TOP_DELEGATED_MODEL_SLUG}",
                "resolved_reasoning_effort=high",
                f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
                f"spawn_tool_args_model={validator.TOP_DELEGATED_MODEL_SLUG}",
                "spawn_tool_args_reasoning_effort=high",
                "",
            ]
        ),
    )
    write(
        run_dir / artifact_rel,
        "\n".join(
            [
                f"agent_role={validator.REQUIRED_VERIFICATION_AGENT_ROLE}",
                f"verification_agent_mode={validator.REQUIRED_VERIFICATION_AGENT_MODE}",
                "agent_id=verification-agent-1",
                "verification_status=pass",
                "verification_result=pass",
                "verification_command=python -B smoke_worktype_subjects.py",
                "verification_ref=verification.md",
                "evidence_ref=evidence.md",
                *common_authority_lines(fields),
                f"model_policy={validator.REQUIRED_DELEGATED_MODEL_POLICY}",
                f"resolved_model_slug={validator.TOP_DELEGATED_MODEL_SLUG}",
                "resolved_reasoning_effort=high",
                f"spawn_model_binding={validator.REQUIRED_DELEGATED_MODEL_BINDING}",
                f"spawn_tool_args_model={validator.TOP_DELEGATED_MODEL_SLUG}",
                "spawn_tool_args_reasoning_effort=high",
                f"spawn_tool_call_ref=run://{dispatch_rel}",
                "",
            ]
        ),
    )
    return f"run://{artifact_rel}"


def main() -> int:
    bad_model_env = {
        **os.environ,
        "AGENT_LOOP_TOP_MODEL": "gpt-5.4",
        "AGENT_LOOP_REQUIRED_MODEL": "gpt-5.4",
        "AGENT_LOOP_ALLOWED_MODELS": "gpt-5.4",
        "AGENT_LOOP_MODEL_CAPABILITY_CLASSES": "gpt-5.4=frontier_loop_authority_v1",
    }
    bad_model = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0,{str((ROOT / 'scripts')).__repr__()}); "
                "import validate_handoff"
            ),
        ],
        text=True,
        capture_output=True,
        env=bad_model_env,
    )
    if bad_model.returncode == 0:
        raise AssertionError("weakened delegated model floor unexpectedly imported")
    bad_effort_env = {
        **os.environ,
        "AGENT_LOOP_TOP_REASONING_EFFORT": "high",
    }
    bad_effort = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0,{str((ROOT / 'scripts')).__repr__()}); "
                "import validate_handoff"
            ),
        ],
        text=True,
        capture_output=True,
        env=bad_effort_env,
    )
    if bad_effort.returncode == 0:
        raise AssertionError("weakened top reasoning effort unexpectedly imported")
    validator = load_validator()
    if validator.artifact_alias_values_are_allowed(
        "vote=allow\nverdict=deny\n",
        ("vote", "verdict"),
        {"allow", "deny", "ambiguous"},
    ):
        raise AssertionError("conflicting vote/verdict aliases unexpectedly passed")
    if not validator.artifact_alias_values_are_allowed(
        "vote=allow\nverdict=merged\n",
        ("vote", "verdict"),
        {"allow", "pass", "merged"},
    ):
        raise AssertionError("positive equivalent vote/verdict aliases unexpectedly failed")
    cases = [
        ("research", "not_applicable", "research_packet"),
        ("docs", "not_applicable", "document_artifact"),
        ("planning", "not_applicable", "plan_artifact"),
        ("review", "plan_review", "plan_review"),
        ("review", "artifact_review", "artifact_review"),
        ("mixed", "not_applicable", "composite_subject"),
    ]
    with tempfile.TemporaryDirectory(prefix="agent-loop-worktype-smoke-") as tmp:
        root = Path(tmp)
        for work_type, review_kind, subject_type in cases:
            run_dir = root / f"{work_type}-{subject_type}"
            fields = prepare_run(run_dir, validator, work_type=work_type, review_kind=review_kind, subject_type=subject_type)
            errors = validator.validate_fields(fields, run_dir, require_consensus=False, live_state=True)
            if errors:
                raise AssertionError(f"{work_type}/{subject_type} unexpectedly failed: {errors}")

            invalid = dict(fields)
            invalid["completion_subject_type"] = "repo_diff"
            invalid_errors = validator.validate_fields(invalid, run_dir, require_consensus=False, live_state=True)
            if not any("requires completion_subject_type" in error for error in invalid_errors):
                raise AssertionError(f"{work_type}/{subject_type} wrong subject type was not rejected: {invalid_errors}")

            if work_type == "research":
                adapter_path = run_dir / "authority" / "default-adapter.json"
                authority_path = run_dir / "authority" / "run-authority.json"
                adapter_payload = json.loads(adapter_path.read_text(encoding="utf-8"))
                authority_payload = json.loads(authority_path.read_text(encoding="utf-8"))
                adapter_payload["project_policy_refs"] = ["unsupported.md#Policy"]
                write_json(adapter_path, adapter_payload)
                updated_adapter_digest = validator.file_sha256_digest(adapter_path)
                authority_payload["adapter_effective_config_digest"] = updated_adapter_digest
                write_json(authority_path, authority_payload)
                unsupported_policy = dict(fields)
                unsupported_policy["adapter_effective_config_digest"] = updated_adapter_digest
                unsupported_errors = validator.validate_fields(
                    unsupported_policy,
                    run_dir,
                    require_consensus=False,
                    live_state=True,
                )
                if not any("unsupported project_policy_refs" in error for error in unsupported_errors):
                    raise AssertionError(f"unsupported project_policy_refs was not rejected: {unsupported_errors}")

        digest_run = root / "subject-digest-proof-field-redaction"
        write(
            digest_run / "source.md",
            "# Source\n\nProof reference fields should not alter subject digest.\n",
        )
        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `challenge_cycle_ref`: `none`",
                    "- `challenge_cycle_status`: `not_applicable`",
                    "- `challenge_cycle_digest_set`: `none`",
                    "",
                ]
            ),
        )
        digest_before = validator.compute_subject_digest(digest_run)
        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `challenge_cycle_ref`: `run://challenge-cycles/current-goal-cycle.json`",
                    "- `challenge_cycle_status`: `allow_unanimous`",
                    "- `challenge_cycle_digest_set`: `sha256:" + "a" * 64 + "`",
                    "",
                ]
            ),
        )
        digest_after = validator.compute_subject_digest(digest_run)
        if digest_after != digest_before:
            raise AssertionError("challenge_cycle proof-ref fields unexpectedly changed subject digest")

        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `goal_completion_evidence`:",
                    "  - `subject_digest=OLD`",
                    "  - `proof_ref=run://challenge-cycles/current-goal-cycle.json`",
                    "",
                ]
            ),
        )
        nested_proof_digest_before = validator.compute_subject_digest(digest_run)
        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `goal_completion_evidence`:",
                    "  - `subject_digest=NEW`",
                    "  - `proof_ref=run://challenge-cycles/current-goal-cycle.json`",
                    "",
                ]
            ),
        )
        nested_proof_digest_after = validator.compute_subject_digest(digest_run)
        if nested_proof_digest_after != nested_proof_digest_before:
            raise AssertionError("nested proof-evidence payload unexpectedly changed subject digest")

        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `goal_completion_evidence`:",
                    "  - `subject_digest=OLD`",
                    "unrelated authority text before the next bullet: OLD",
                    "- `run_decision`: `continue`",
                    "",
                ]
            ),
        )
        unrelated_text_digest_before = validator.compute_subject_digest(digest_run)
        write(
            digest_run / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `goal_completion_evidence`:",
                    "  - `subject_digest=NEW`",
                    "unrelated authority text before the next bullet: NEW",
                    "- `run_decision`: `continue`",
                    "",
                ]
            ),
        )
        unrelated_text_digest_after = validator.compute_subject_digest(digest_run)
        if unrelated_text_digest_after == unrelated_text_digest_before:
            raise AssertionError("unindented text after proof-evidence payload was over-redacted from subject digest")

        fast_run = root / "implementation-fast-path"
        fast_fields = prepare_run(
            fast_run,
            validator,
            work_type="implementation",
            review_kind="not_applicable",
            subject_type="repo_diff",
        )
        fast_fields.update(
            {
                "run_intent": "implementation_loop",
                "risk_tier": "tier1_local",
                "implementation_gate_status": "accepted",
                "implementation_gate_evidence": (
                    "fast_path_reason=single_file_local_fix "
                    "minimal_plan_ref=revised-plan.md "
                    "requirement_trace_ref=evidence.md "
                    "local_verification=smoke_validation "
                    "verification_ref=verification.md "
                    "verification_result=pass "
                    "scoped_files=single_fixture "
                    "external_api=false "
                    "db_or_migration=false "
                    "security_sensitive=false "
                    "reversible=true "
                    "mini_plan_validation_skip=single_file_local_fix "
                    "skip_scope_evidence=single_file_local_change"
                ),
                "research_cycle_status": "not_applicable",
            }
        )
        fast_errors = validator.validate_fields(fast_fields, fast_run, require_consensus=False, live_state=True)
        if fast_errors:
            raise AssertionError(f"implementation fast path unexpectedly failed: {fast_errors}")
        missing_fast = dict(fast_fields)
        missing_fast["implementation_gate_evidence"] = (
            "mini_plan_validation_skip=single_file_local_fix "
            "local_verification=smoke_validation "
            "external_api=false "
            "db_or_migration=false "
            "security_sensitive=false "
            "verification_result=pass "
            "skip_scope_evidence=single_file_local_change"
        )
        missing_fast_errors = validator.validate_fields(missing_fast, fast_run, require_consensus=False, live_state=True)
        if not any("requires research_cycle_status=allow_unanimous" in error for error in missing_fast_errors):
            raise AssertionError(f"missing fast_path_reason did not require research cycle: {missing_fast_errors}")

        tier1_self_check = dict(fast_fields)
        tier1_self_check["implementation_gate_evidence"] = (
            "tier1_self_check=pass "
            "risk_expanded=false "
            "implementation_summary_ref=evidence.md "
            "verification_plan_ref=revised-plan.md "
            "requirement_trace_ref=evidence.md "
            "verification_ref=verification.md "
            "local_verification=smoke_validation "
            "verification_result=pass "
            "scope_evidence=bounded_local_change "
            "scoped_files=single_fixture "
            "external_api=false "
            "db_or_migration=false "
            "security_sensitive=false "
            "shared_boundary=false"
        )
        tier1_self_check_errors = validator.validate_fields(
            tier1_self_check,
            fast_run,
            require_consensus=False,
            live_state=True,
        )
        if tier1_self_check_errors:
            raise AssertionError(f"tier1 self-check path unexpectedly failed: {tier1_self_check_errors}")

        tier1_negative_cases = [
            (
                "risk_expanded=true",
                tier1_self_check["implementation_gate_evidence"].replace("risk_expanded=false", "risk_expanded=true"),
            ),
            (
                "external_api=true",
                tier1_self_check["implementation_gate_evidence"].replace("external_api=false", "external_api=true"),
            ),
            (
                "shared_boundary=true",
                tier1_self_check["implementation_gate_evidence"].replace("shared_boundary=false", "shared_boundary=true"),
            ),
            (
                "missing verification_ref",
                tier1_self_check["implementation_gate_evidence"].replace("verification_ref=verification.md ", ""),
            ),
        ]
        tier2_self_check = dict(tier1_self_check)
        tier2_self_check["risk_tier"] = "tier2_material"
        tier1_negative_cases.append(("non-tier1 risk", tier2_self_check["implementation_gate_evidence"]))
        for label, evidence in tier1_negative_cases:
            invalid_fields = dict(tier1_self_check)
            invalid_fields["implementation_gate_evidence"] = evidence
            if label == "non-tier1 risk":
                invalid_fields["risk_tier"] = "tier2_material"
            errors = validator.validate_fields(invalid_fields, fast_run, require_consensus=False, live_state=True)
            if not errors:
                raise AssertionError(f"unsafe tier1 self-check unexpectedly passed: {label}")

        tier0_fields = dict(fast_fields)
        tier0_fields["risk_tier"] = "tier0_trivial"
        tier0_fields["implementation_gate_evidence"] = (
            "fast_path_reason=no_behavior_change "
            "minimal_plan_ref=revised-plan.md "
            "requirement_trace_ref=evidence.md "
            "local_verification=smoke_validation "
            "verification_ref=verification.md "
            "verification_result=pass "
            "scoped_files=single_fixture "
            "external_api=false "
            "db_or_migration=false "
            "security_sensitive=false "
            "reversible=true "
            "mini_plan_validation_skip=tier0_trivial "
            "skip_scope_evidence=mechanical_no_behavior_change"
        )
        tier0_errors = validator.validate_fields(tier0_fields, fast_run, require_consensus=False, live_state=True)
        if tier0_errors:
            raise AssertionError(f"tier0 file-changing fast path unexpectedly failed: {tier0_errors}")
        tier0_duplicate_safety = dict(tier0_fields)
        tier0_duplicate_safety["implementation_gate_evidence"] = tier0_fields["implementation_gate_evidence"].replace(
            "external_api=false ",
            "external_api=false external_api=true ",
            1,
        )
        tier0_duplicate_errors = validator.validate_fields(
            tier0_duplicate_safety,
            fast_run,
            require_consensus=False,
            live_state=True,
        )
        if not any("accepted implementation gates require mandatory" in error for error in tier0_duplicate_errors):
            raise AssertionError(f"duplicate tier0 safety token was not rejected: {tier0_duplicate_errors}")

        implementation_viewpoints = sorted(validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS)
        pre_implementation_refs = write_implementation_challenge_fixture(
            fast_run,
            validator,
            fast_fields,
            mode="pre_implementation_plan_validation",
            viewpoints=implementation_viewpoints,
        )
        post_implementation_refs = write_implementation_challenge_fixture(
            fast_run,
            validator,
            fast_fields,
            mode="post_implementation_plan_validation",
            viewpoints=implementation_viewpoints,
        )
        strategy_ref = write_strategy_fixture(fast_run, validator, fast_fields)
        verification_agent_ref = write_verification_agent_fixture(fast_run, validator, fast_fields)
        if not validator.implementation_challenge_artifacts_are_valid(
            pre_implementation_refs,
            run_dir=fast_run,
            challenge_review_mode="pre_implementation_plan_validation",
            required_viewpoints=validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
            required_model_mix=validator.REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation challenge fixture unexpectedly failed")
        mini_evidence = (
            "pre_plan_validation_lane_count=2 "
            f"pre_plan_validation_viewpoint_set={'|'.join(implementation_viewpoints)} "
            "pre_plan_validation_verdict=pass_unanimous "
            f"pre_plan_validation_refs={'|'.join(pre_implementation_refs)} "
            "post_plan_validation_lane_count=2 "
            f"post_plan_validation_viewpoint_set={'|'.join(implementation_viewpoints)} "
            "post_plan_validation_verdict=pass_unanimous "
            f"post_plan_validation_refs={'|'.join(post_implementation_refs)} "
            f"strategy_ref={strategy_ref} "
            f"verification_agent_ref={verification_agent_ref}"
        )
        if not validator.implementation_mini_plan_validation_evidence_is_valid(
            mini_evidence,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation mini validation with verification_agent_ref unexpectedly failed")

        full_pre_viewpoints = sorted(validator.REQUIRED_PRE_IMPLEMENTATION_VIEWPOINTS)
        full_post_viewpoints = sorted(validator.REQUIRED_POST_IMPLEMENTATION_VIEWPOINTS)
        full_pre_refs = write_implementation_challenge_fixture(
            fast_run,
            validator,
            fast_fields,
            mode="pre_implementation_challenge",
            viewpoints=full_pre_viewpoints,
        )
        full_post_refs = write_implementation_challenge_fixture(
            fast_run,
            validator,
            fast_fields,
            mode="post_implementation_challenge",
            viewpoints=full_post_viewpoints,
        )
        full_gate_evidence = (
            f"{mini_evidence} "
            "pre_challenge_lane_count=5 "
            f"pre_challenge_viewpoint_set={'|'.join(full_pre_viewpoints)} "
            "pre_challenge_verdict=pass_unanimous "
            f"pre_challenge_refs={'|'.join(full_pre_refs)} "
            "post_challenge_lane_count=5 "
            f"post_challenge_viewpoint_set={'|'.join(full_post_viewpoints)} "
            "post_challenge_verdict=pass_unanimous "
            f"post_challenge_refs={'|'.join(full_post_refs)}"
        )
        if not validator.implementation_gate_evidence_is_valid(
            full_gate_evidence,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("tier2/tier3 5-lane implementation challenge evidence unexpectedly failed")
        tier2_full_gate = dict(fast_fields)
        tier2_full_gate["risk_tier"] = "tier2_material"
        tier2_full_gate["implementation_gate_evidence"] = full_gate_evidence
        research_cycle_ref, research_cycle_digest = write_research_cycle_fixture(fast_run, validator, tier2_full_gate)
        tier2_full_gate["research_cycle_status"] = "allow_unanimous"
        tier2_full_gate["research_cycle_ref"] = research_cycle_ref
        tier2_full_gate["research_cycle_digest_set"] = research_cycle_digest
        tier2_full_errors = validator.validate_fields(
            tier2_full_gate,
            fast_run,
            require_consensus=False,
            live_state=True,
        )
        if tier2_full_errors:
            raise AssertionError(f"tier2 full 5-lane gate unexpectedly failed: {tier2_full_errors}")

        duplicate_viewpoint_evidence = mini_evidence.replace(
            "pre_plan_validation_viewpoint_set=operator_execution_fit|verification_evidence_fit",
            "pre_plan_validation_viewpoint_set=operator_execution_fit|operator_execution_fit|verification_evidence_fit",
        )
        if validator.implementation_mini_plan_validation_evidence_is_valid(
            duplicate_viewpoint_evidence,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation mini validation with duplicate viewpoint token unexpectedly passed")
        no_verification_agent = mini_evidence.replace(f" verification_agent_ref={verification_agent_ref}", "")
        if validator.implementation_mini_plan_validation_evidence_is_valid(
            no_verification_agent,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation mini validation without verification_agent_ref unexpectedly passed")
        same_strategy_and_verification = mini_evidence.replace(
            f"verification_agent_ref={verification_agent_ref}",
            f"verification_agent_ref={strategy_ref}",
        )
        if validator.implementation_mini_plan_validation_evidence_is_valid(
            same_strategy_and_verification,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation mini validation with same strategy and verification ref unexpectedly passed")

        verification_agent_path = fast_run / verification_agent_ref.replace("run://", "")
        original_verification_agent = verification_agent_path.read_text(encoding="utf-8")
        verification_agent_path.write_text(
            original_verification_agent.replace("agent_role=verification_agent", "agent_role=challenge_agent"),
            encoding="utf-8",
        )
        if validator.implementation_mini_plan_validation_evidence_is_valid(
            mini_evidence,
            fast_run,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation mini validation with challenge_agent verification artifact unexpectedly passed")
        verification_agent_path.write_text(original_verification_agent, encoding="utf-8")

        implementation_lane = fast_run / pre_implementation_refs[0].replace("run://", "")
        original_lane = implementation_lane.read_text(encoding="utf-8")
        implementation_lane.write_text(original_lane + "vote=deny\n", encoding="utf-8")
        if validator.implementation_challenge_artifacts_are_valid(
            pre_implementation_refs,
            run_dir=fast_run,
            challenge_review_mode="pre_implementation_plan_validation",
            required_viewpoints=validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
            required_model_mix=validator.REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation challenge duplicate vote unexpectedly passed")
        implementation_lane.write_text(original_lane, encoding="utf-8")

        implementation_lane.write_text(
            "\n".join(line for line in original_lane.splitlines() if not line.startswith("model_resolution_basis_ref="))
            + "\n",
            encoding="utf-8",
        )
        if validator.implementation_challenge_artifacts_are_valid(
            pre_implementation_refs,
            run_dir=fast_run,
            challenge_review_mode="pre_implementation_plan_validation",
            required_viewpoints=validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
            required_model_mix=validator.REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation challenge without model resolution basis unexpectedly passed")
        implementation_lane.write_text(original_lane, encoding="utf-8")

        dispatch_path = fast_run / "implementation-dispatch" / (
            f"pre_implementation_plan_validation-{implementation_viewpoints[0]}.md"
        )
        original_dispatch = dispatch_path.read_text(encoding="utf-8")
        dispatch_path.write_text(original_dispatch + "viewpoint=conflicting_viewpoint\n", encoding="utf-8")
        if validator.implementation_challenge_artifacts_are_valid(
            pre_implementation_refs,
            run_dir=fast_run,
            challenge_review_mode="pre_implementation_plan_validation",
            required_viewpoints=validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
            required_model_mix=validator.REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation dispatch duplicate viewpoint unexpectedly passed")
        dispatch_path.write_text(original_dispatch, encoding="utf-8")

        dispatch_path.write_text(
            "\n".join(line for line in original_dispatch.splitlines() if not line.startswith("model_resolution_basis_ref="))
            + "\n",
            encoding="utf-8",
        )
        if validator.implementation_challenge_artifacts_are_valid(
            pre_implementation_refs,
            run_dir=fast_run,
            challenge_review_mode="pre_implementation_plan_validation",
            required_viewpoints=validator.REQUIRED_IMPLEMENTATION_MINI_PLAN_VIEWPOINTS,
            required_model_mix=validator.REQUIRED_IMPLEMENTATION_MINI_MODEL_MIX,
            authority_path=fast_run / "authority" / "run-authority.json",
        ):
            raise AssertionError("implementation dispatch without model resolution basis unexpectedly passed")
        dispatch_path.write_text(original_dispatch, encoding="utf-8")

    print("[OK] worktype subject smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
