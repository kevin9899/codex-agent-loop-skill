#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from validate_handoff import (
    REQUIRED_DELEGATED_AGENT_COUNT,
    REQUIRED_DELEGATED_MODEL_BINDING,
    REQUIRED_DELEGATED_MODEL_SLUG,
    REQUIRED_DELEGATED_REASONING_EFFORT,
    REQUIRED_STOP_VIEWPOINTS,
    compute_subject_digest,
    compute_source_digest,
)


VIEWPOINTS = [
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def consensus_evidence(
    *,
    challenge_round_id: str,
    closeout_round_id: str,
    subject_digest: str,
    source_digest: str,
    refs: list[str],
) -> str:
    viewpoint_set = "|".join(VIEWPOINTS)
    return (
        f"allow_count={REQUIRED_DELEGATED_AGENT_COUNT} deny_count=0 ambiguous_count=0 missing_count=0 "
        f"challenge_round_id={challenge_round_id} closeout_round_id={closeout_round_id} "
        f"subject_digest={subject_digest} viewpoint_set={viewpoint_set} "
        f"source_ref=source.md source_digest={source_digest} "
        "context_mode=clean_source_first "
        "authority_basis=source_md_original_user_prompt "
        "source_requirements_reconstructed=yes "
        "claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff "
        "repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied "
        "model_policy=resolved_strongest_hard_pin "
        f"resolved_model_slug={REQUIRED_DELEGATED_MODEL_SLUG} "
        f"resolved_reasoning_effort={REQUIRED_DELEGATED_REASONING_EFFORT} "
        f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING} "
        f"refs={','.join(refs)}"
    )


def handoff_text(
    *,
    closeout_round_id: str,
    stop_evidence: str,
    goal_evidence: str,
) -> str:
    return "\n".join(
        [
            "# Handoff",
            "",
            "- `handoff_schema_version`: `v2-stop-consensus`",
            "- `working_goal`: `smoke terminal stop briefing`",
            "- `run_intent`: `implementation_loop`",
            "- `host_resume_mode`: `same_turn_only`",
            "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
            "- `current_or_next_stage`: `terminal stop briefing`",
            "- `stage_status`: `terminal stop receipt is ready for gate rendering`",
            "- `remaining_required_stages`:",
            "  - none",
            "- `latest_evidence_summary`:",
            "  - `terminal stop briefing fields added`",
            "  - `validate_terminal_reply.py passes canonical generated receipt`",
            "- `blocking_findings`:",
            "  - none",
            "- `residual_risks`:",
            "  - `external API behavior was not exercised`",
            f"- `goal_completion_status`: `verified_complete_{REQUIRED_DELEGATED_AGENT_COUNT}agent`",
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
    subject_digest: str,
    source_digest: str,
) -> list[str]:
    refs: list[str] = []
    for index, viewpoint in enumerate(VIEWPOINTS, start=1):
        if viewpoint not in REQUIRED_STOP_VIEWPOINTS:
            raise AssertionError(f"unexpected viewpoint in smoke fixture: {viewpoint}")
        rel = f"proof/{phase}-{viewpoint}.md"
        dispatch_rel = f"dispatch/{phase}-{viewpoint}.md"
        refs.append(rel)
        write(
            run_dir / dispatch_rel,
            "\n".join(
                [
                    "dispatch_receipt_version=v1",
                    f"phase={phase}",
                    f"agent_id={phase}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    f"challenge_round_id={challenge_round_id}",
                    f"closeout_round_id={closeout_round_id}",
                    "source_ref=source.md",
                    f"source_digest={source_digest}",
                    "context_mode=clean_source_first",
                    "authority_basis=source_md_original_user_prompt",
                    "full_history_fork=false",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={REQUIRED_DELEGATED_MODEL_SLUG}",
                    f"spawn_tool_args_reasoning_effort={REQUIRED_DELEGATED_REASONING_EFFORT}",
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
                    "vote=allow",
                    f"agent_id={phase}-agent-{index}",
                    f"viewpoint={viewpoint}",
                    f"challenge_round_id={challenge_round_id}",
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
                    "model_policy=resolved_strongest_hard_pin",
                    f"resolved_model_slug={REQUIRED_DELEGATED_MODEL_SLUG}",
                    f"resolved_reasoning_effort={REQUIRED_DELEGATED_REASONING_EFFORT}",
                    "model_resolution_basis_ref=skill:model-catalog-smoke",
                    f"spawn_model_binding={REQUIRED_DELEGATED_MODEL_BINDING}",
                    f"spawn_tool_args_model={REQUIRED_DELEGATED_MODEL_SLUG}",
                    f"spawn_tool_args_reasoning_effort={REQUIRED_DELEGATED_REASONING_EFFORT}",
                    f"spawn_tool_call_ref={dispatch_rel}",
                    "freshness_status=fresh",
                    "",
                ]
            ),
        )
    return refs


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    closeout_round_id = "closeout-smoke-terminal-stop-briefing"
    stop_round_id = "challenge-smoke-terminal-stop-halt"
    goal_round_id = "challenge-smoke-terminal-stop-goal"

    with tempfile.TemporaryDirectory(prefix="agent-loop-stop-smoke-") as tmp:
        run_dir = Path(tmp)
        write(run_dir / "source.md", "# Source\n\nSmoke terminal stop briefing.\n")
        source_digest = compute_source_digest(run_dir)
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

        placeholder_stop = consensus_evidence(
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest="placeholder",
            source_digest=source_digest,
            refs=[f"proof/stop_authorization-{viewpoint}.md" for viewpoint in VIEWPOINTS],
        )
        placeholder_goal = consensus_evidence(
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest="placeholder",
            source_digest=source_digest,
            refs=[f"proof/goal_completion-{viewpoint}.md" for viewpoint in VIEWPOINTS],
        )
        write(
            run_dir / "handoff.md",
            handoff_text(
                closeout_round_id=closeout_round_id,
                stop_evidence=placeholder_stop,
                goal_evidence=placeholder_goal,
            ),
        )
        subject_digest = compute_subject_digest(run_dir)
        stop_refs = [f"proof/stop_authorization-{viewpoint}.md" for viewpoint in VIEWPOINTS]
        goal_refs = [f"proof/goal_completion-{viewpoint}.md" for viewpoint in VIEWPOINTS]
        stop_evidence = consensus_evidence(
            challenge_round_id=stop_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=stop_refs,
        )
        goal_evidence = consensus_evidence(
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
            refs=goal_refs,
        )
        write(
            run_dir / "handoff.md",
            handoff_text(
                closeout_round_id=closeout_round_id,
                stop_evidence=stop_evidence,
                goal_evidence=goal_evidence,
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
            subject_digest=subject_digest,
            source_digest=source_digest,
        )
        write_lane_artifacts(
            run_dir=run_dir,
            phase="goal_completion",
            challenge_round_id=goal_round_id,
            closeout_round_id=closeout_round_id,
            subject_digest=subject_digest,
            source_digest=source_digest,
        )

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
            "5-agent halt proof allow_unanimous",
            "5-agent completion proof verified",
            "source-first clean audit verified",
        ]
        missing = [token for token in required_reply_tokens if token not in gate.stdout]
        if missing:
            print(f"[FAIL] terminal stop reply missing tokens: {missing}", file=sys.stderr)
            print(gate.stdout, file=sys.stderr)
            return 1

        tampered_reply = gate.stdout + "freeform_wrapup=this should fail\n"
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

    print("[OK] terminal stop briefing smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
