#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


def write_default_artifacts(run_dir: Path, *, source_text: str, plan_remaining: str = "- none") -> None:
    write(run_dir / "source.md", f"# Source\n\n{source_text}\n")
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
                "ideation_not_material: deterministic validator guard smoke.",
                "",
            ]
        ),
    )
    write(run_dir / "research.md", "# Research\n\nNo external research needed for validator smoke.\n")
    write(run_dir / "evidence.md", "# Evidence\n\nValidator smoke fixture.\n")
    write(
        run_dir / "revised-plan.md",
        "\n".join(
            [
                "# Revised Plan",
                "",
                "## Remaining Stage Queue",
                "",
                plan_remaining,
                "",
            ]
        ),
    )


def base_fields(**overrides):
    fields = {
        "handoff_schema_version": "v2-stop-consensus",
        "working_goal": "plan execution stop guard smoke",
        "run_intent": "implementation_loop",
        "host_resume_mode": "same_turn_only",
        "capability_mode": "delegated_agents_authorized_by_loop_tool_available_smoke",
        "current_or_next_stage": "final stop validation",
        "stage_status": "candidate stop",
        "current_batch": "none",
        "risk_tier": "tier1_local",
        "implementation_gate_status": "not_applicable",
        "implementation_gate_evidence": "none",
        "remaining_required_stages": ["none"],
        "latest_evidence_summary": ["smoke fixture"],
        "blocking_findings": ["none"],
        "residual_risks": ["none"],
        "goal_completion_status": "verified_complete_5lane",
        "goal_completion_evidence": "challenge_round_id=goal-smoke refs=proof/goal.md",
        "loop_state": "stopped",
        "continuation_mode": "nonstop",
        "closeout_round_id": "closeout-smoke",
        "run_decision": "stop",
        "sequential_objectives_status": "satisfied",
        "stop_authorization_status": "allow",
        "stop_authorization_evidence": "fresh halt proof",
        "stop_consensus_status": "allow_unanimous",
        "stop_consensus_evidence": "challenge_round_id=halt-smoke refs=proof/halt.md",
        "external_authority_basis": "none",
        "pause_reason": "autonomous stop authorized by fresh halt and goal proof",
        "next_mandatory_action": "none",
        "continue_exit_status": "not_applicable",
        "continue_exit_evidence": "none",
        "turn_exit_cause": "not_applicable",
        "turn_exit_evidence": "none",
        "resume_instructions": ["none"],
    }
    fields.update(overrides)
    return fields


def assert_contains(errors: list[str], expected: str, name: str) -> None:
    if not any(expected in error for error in errors):
        raise AssertionError(f"{name}: expected {expected!r} in errors, got: {errors}")


def assert_not_contains(errors: list[str], unexpected: str, name: str) -> None:
    if any(unexpected in error for error in errors):
        raise AssertionError(f"{name}: unexpected {unexpected!r} in errors: {errors}")


def main() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        remaining_run = root / "stop-with-remaining"
        write_default_artifacts(remaining_run, source_text="Implement the bounded fix.")
        errors = validator.validate_fields(
            base_fields(remaining_required_stages=["ENG-LEARN-01 review processor split remains"]),
            remaining_run,
            require_consensus=True,
        )
        assert_contains(errors, "run_decision=stop is illegal while remaining_required_stages is non-empty", "remaining")

        roadmap_run = root / "roadmap-derived-without-authority"
        write_default_artifacts(roadmap_run, source_text="$loop로 해당 plan 진행해")
        errors = validator.validate_fields(base_fields(), roadmap_run, require_consensus=True)
        assert_contains(errors, "roadmap-derived implementation stops require goal_completion_evidence", "roadmap authority")

        roadmap_with_authority_run = root / "roadmap-derived-with-authority"
        write_default_artifacts(roadmap_with_authority_run, source_text="$loop로 해당 plan 진행해")
        errors = validator.validate_fields(
            base_fields(
                goal_completion_evidence=(
                    "challenge_round_id=goal-smoke implementation_authority_ref=revised-plan.md "
                    "refs=proof/goal.md"
                )
            ),
            roadmap_with_authority_run,
            require_consensus=True,
        )
        assert_not_contains(
            errors,
            "roadmap-derived implementation stops require goal_completion_evidence",
            "roadmap authority accepted",
        )

        high_risk_run = root / "high-risk-without-gate"
        write_default_artifacts(high_risk_run, source_text="Implement a core write-path change.")
        errors = validator.validate_fields(
            base_fields(
                risk_tier="tier2_material",
                implementation_gate_status="accepted",
                implementation_gate_evidence="none",
            ),
            high_risk_run,
            require_consensus=True,
        )
        assert_contains(errors, "tier2/tier3 accepted implementation gates require", "high risk gate")

        high_risk_waiver_run = root / "high-risk-with-waiver"
        write_default_artifacts(high_risk_waiver_run, source_text="Implement a mechanical shared workflow change.")
        errors = validator.validate_fields(
            base_fields(
                risk_tier="tier2_material",
                implementation_gate_status="accepted",
                implementation_gate_evidence=(
                    "implementation_gate_waiver=demonstrably_mechanical risk_tier=tier2_material "
                    "waiver_reason=comment_only_guard compensating_verification=validator_smoke"
                ),
            ),
            high_risk_waiver_run,
            require_consensus=True,
        )
        assert_contains(errors, "tier2/tier3 accepted implementation gates require", "high risk waiver rejected")

        blocked_without_challenge_run = root / "blocked-no-action-without-challenge"
        write_default_artifacts(
            blocked_without_challenge_run,
            source_text="$loop로 production hardening plan 진행해",
            plan_remaining="- external production approval remains",
        )
        write(
            blocked_without_challenge_run / "attempts" / "no-bounded.md",
            "\n".join(
                [
                    "# Attempt Receipt",
                    "",
                    "- `attempt_receipt_version`: `v1`",
                    "- `closeout_round_id`: `closeout-smoke`",
                    "- `attempt_status`: `blocked_during_attempt`",
                    "- `next_action`: `retry fresh 5-lane stop_authorization challenge for approval-only blocker`",
                    "- `summary`: `blocked: no bounded local actions remain awaiting approval`",
                    "",
                ]
            ),
        )
        errors = validator.validate_fields(
            base_fields(
                host_resume_mode="durable_runtime",
                current_or_next_stage="blocked approval gate",
                stage_status="blocked pending challenge",
                remaining_required_stages=["external production approval remains"],
                blocking_findings=["blocked: no bounded local actions remain awaiting approval"],
                goal_completion_status="not_reached",
                goal_completion_evidence="fresh 5-lane completion challenge not available",
                loop_state="reassessment_pending",
                run_decision="continue",
                sequential_objectives_status="open",
                stop_authorization_status="not_applicable",
                stop_authorization_evidence="none",
                stop_consensus_status="not_applicable",
                stop_consensus_evidence="none",
                external_authority_basis="none",
                pause_reason="none",
                next_mandatory_action="retry fresh 5-lane stop_authorization challenge for approval-only blocker",
                continue_exit_status="blocked_during_attempt",
                continue_exit_evidence=(
                    "attempt_ref=attempts/no-bounded.md closeout_round_id=closeout-smoke "
                    "summary=blocked no bounded local actions remain awaiting approval"
                ),
                turn_exit_cause="blocked_during_attempt",
                turn_exit_evidence="blocked: no bounded local actions remain awaiting approval",
                resume_instructions=["retry fresh 5-lane stop_authorization challenge for approval-only blocker"],
            ),
            blocked_without_challenge_run,
            require_consensus=True,
        )
        assert_contains(
            errors,
            "approval/no-bounded-action/blocker closeouts require a fresh 5-lane stop_authorization challenge",
            "blocked no-action challenge",
        )

        local_blocked_run = root / "blocked-local-fix-available"
        write_default_artifacts(
            local_blocked_run,
            source_text="$loop로 local typecheck fix 진행해",
            plan_remaining="- fix typecheck error",
        )
        write(
            local_blocked_run / "attempts" / "local-blocked.md",
            "\n".join(
                [
                    "# Attempt Receipt",
                    "",
                    "- `attempt_receipt_version`: `v1`",
                    "- `closeout_round_id`: `closeout-smoke`",
                    "- `attempt_status`: `blocked_during_attempt`",
                    "- `next_action`: `fix the local typecheck error`",
                    "- `summary`: `blocked because typecheck failed; local fix remains available`",
                    "",
                ]
            ),
        )
        errors = validator.validate_fields(
            base_fields(
                host_resume_mode="durable_runtime",
                current_or_next_stage="fix local typecheck error",
                stage_status="continue with local repair",
                remaining_required_stages=["fix typecheck error"],
                blocking_findings=["blocked because typecheck failed; local fix remains available"],
                goal_completion_status="not_reached",
                goal_completion_evidence="fresh 5-lane completion challenge not available",
                loop_state="execution",
                run_decision="continue",
                sequential_objectives_status="open",
                stop_authorization_status="not_applicable",
                stop_authorization_evidence="none",
                stop_consensus_status="not_applicable",
                stop_consensus_evidence="none",
                external_authority_basis="none",
                pause_reason="none",
                next_mandatory_action="fix the local typecheck error",
                continue_exit_status="blocked_during_attempt",
                continue_exit_evidence=(
                    "attempt_ref=attempts/local-blocked.md closeout_round_id=closeout-smoke "
                    "summary=blocked because typecheck failed; local fix remains available"
                ),
                turn_exit_cause="blocked_during_attempt",
                turn_exit_evidence="blocked because typecheck failed; local fix remains available",
                resume_instructions=["fix the local typecheck error"],
            ),
            local_blocked_run,
            require_consensus=True,
        )
        if any("approval/no-bounded-action/blocker closeouts require" in error for error in errors):
            raise AssertionError(f"local repair blocker incorrectly required stop_authorization challenge: {errors}")

        approval_pending_local_action_run = root / "approval-pending-local-verification"
        write_default_artifacts(
            approval_pending_local_action_run,
            source_text="$loop로 local verification repair 진행해",
            plan_remaining="- run local verification and artifact repair",
        )
        errors = validator.validate_fields(
            base_fields(
                host_resume_mode="durable_runtime",
                current_or_next_stage="run local verification",
                stage_status="approval pending but local action remains",
                remaining_required_stages=["run local verification and artifact repair"],
                blocking_findings=["approval pending, but bounded local verification remains available"],
                goal_completion_status="not_reached",
                goal_completion_evidence="fresh 5-lane completion challenge not available",
                loop_state="execution",
                run_decision="continue",
                sequential_objectives_status="open",
                stop_authorization_status="not_applicable",
                stop_authorization_evidence="none",
                stop_consensus_status="not_applicable",
                stop_consensus_evidence="none",
                external_authority_basis="none",
                pause_reason="none",
                next_mandatory_action="run local verification and patch artifact repair",
                continue_exit_status="blocked_during_attempt",
                continue_exit_evidence=(
                    "attempt_ref=attempts/local-blocked.md closeout_round_id=closeout-smoke "
                    "summary=approval pending but local verification remains"
                ),
                turn_exit_cause="blocked_during_attempt",
                turn_exit_evidence="approval pending but local verification remains",
                resume_instructions=["run local verification and patch artifact repair"],
            ),
            approval_pending_local_action_run,
            require_consensus=True,
        )
        if any("approval/no-bounded-action/blocker closeouts require" in error for error in errors):
            raise AssertionError(f"approval wording with local action incorrectly required challenge: {errors}")

    print("[OK] plan execution stop guard smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
