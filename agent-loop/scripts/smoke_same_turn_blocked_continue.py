#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    closeout_round_id = "closeout-smoke-same-turn-blocked-continue"
    next_action = "Run gpt-5.5 challenge dispatch"
    turn_exit_evidence = (
        "same_turn_only host visible turn boundary forced after delegated quota blocked the latest action"
    )

    with tempfile.TemporaryDirectory(prefix="agent-loop-smoke-") as tmp:
        run_dir = Path(tmp)
        write(run_dir / "source.md", "# Source\n\nSmoke blocked continue.\n")
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
                    "ideation_not_material: smoke fixture deterministic blocked-continue validation.",
                    "",
                ]
            ),
        )
        write(run_dir / "research.md", "# Research\n\nSmoke fixture.\n")
        write(
            run_dir / "revised-plan.md",
            "# Revised Plan\n\n## Remaining Required Stages\n\n- Stage smoke blocked continue\n",
        )
        write(run_dir / "evidence.md", "# Evidence\n\nSmoke fixture.\n")
        write(
            run_dir / "receipts" / "blocked-attempt.md",
            "\n".join(
                [
                    "attempt_receipt_version=v1",
                    f"closeout_round_id={closeout_round_id}",
                    "attempt_status=blocked_during_attempt",
                    f"next_action={next_action}",
                    "summary=spawn_agent delegated gpt-5.5 lanes blocked by usage limit during challenge dispatch",
                    "command_ref=spawn_agent model=gpt-5.5 reasoning_effort=xhigh",
                    "",
                ]
            ),
        )
        write(
            run_dir / "authority" / "host-turn-boundary.md",
            "\n".join(
                [
                    "# Authority Receipt",
                    "authority_receipt_version=v1",
                    "authority_kind=host_turn_boundary",
                    "event_id=smoke-host-boundary",
                    f"closeout_round_id={closeout_round_id}",
                    "attempt_ref=receipts/blocked-attempt.md",
                    f"excerpt={turn_exit_evidence}",
                    "",
                ]
            ),
        )
        write(
            run_dir / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `handoff_schema_version`: `v2-stop-consensus`",
                    "- `working_goal`: `smoke same-turn blocked continue`",
                    "- `run_intent`: `implementation_loop`",
                    "- `host_resume_mode`: `same_turn_only`",
                    "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
                    "- `current_or_next_stage`: `Stage smoke blocked continue`",
                    "- `stage_status`: `delegated dispatch blocked by quota; auto-resume continue should validate`",
                    "- `remaining_required_stages`:",
                    "  - `Stage smoke blocked continue`",
                    "- `latest_evidence_summary`:",
                    "  - `spawn_agent delegated gpt-5.5 lanes blocked by usage limit`",
                    "- `blocking_findings`:",
                    "  - `delegated quota blocked challenge dispatch`",
                    "- `residual_risks`:",
                    "  - none",
                    "- `goal_completion_status`: `not_reached`",
                    "- `goal_completion_evidence`: `fresh 5-agent completion challenge not available`",
                    "- `loop_state`: `reassessment_pending`",
                    "- `continuation_mode`: `nonstop`",
                    f"- `closeout_round_id`: `{closeout_round_id}`",
                    "- `run_decision`: `continue`",
                    "- `sequential_objectives_status`: `open`",
                    "- `stop_authorization_status`: `not_applicable`",
                    "- `stop_authorization_evidence`: `none`",
                    "- `stop_consensus_status`: `not_applicable`",
                    "- `stop_consensus_evidence`: `fresh 5-agent completion challenge pending`",
                    "- `external_authority_basis`: `none`",
                    "- `pause_reason`: `none`",
                    f"- `next_mandatory_action`: `{next_action}`",
                    "- `continue_exit_status`: `blocked_during_attempt`",
                    f"- `continue_exit_evidence`: `spawn_agent delegated gpt-5.5 lanes blocked by usage limit during challenge dispatch; attempt_ref=receipts/blocked-attempt.md; closeout_round_id={closeout_round_id}`",
                    "- `turn_exit_cause`: `host_turn_boundary_pause`",
                    f"- `turn_exit_evidence`: `{turn_exit_evidence}; host_boundary_ref=authority/host-turn-boundary.md`",
                    "- `resume_instructions`:",
                    f"  - `$loop {run_dir}`",
                    f"  - `{next_action}`",
                    "",
                ]
            ),
        )

        validate = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if validate.returncode != 0:
            sys.stderr.write(validate.stdout)
            sys.stderr.write(validate.stderr)
            return validate.returncode

        env = os.environ.copy()
        env["AGENT_LOOP_CONFIRMED_HOST_TURN_END"] = "1"
        env["AGENT_LOOP_FORCED_TURN_END_REASON"] = "host_turn_boundary_pause"
        env["AGENT_LOOP_FORCED_TURN_END_EVIDENCE"] = turn_exit_evidence
        gate = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "closeout_gate.py"),
                str(run_dir),
                "--active-delta",
                "dispatching gpt-5.5 challenge lanes",
                "--blocking-or-risk",
                "spawn_agent delegated gpt-5.5 lanes blocked by usage limit",
            ],
            text=True,
            capture_output=True,
            env=env,
        )
        if gate.returncode != 0:
            sys.stderr.write(gate.stdout)
            sys.stderr.write(gate.stderr)
            return gate.returncode

        required_reply_tokens = [
            "run_decision=continue",
            "semantic_state=incomplete_forced_boundary",
            "continuation_authority=standing",
            "turn_exit_cause=host_turn_boundary_pause",
            "followup_resume_policy=auto_resume_any_followup",
            "resume_command=$loop",
            "blocking_or_risk=",
        ]
        missing = [token for token in required_reply_tokens if token not in gate.stdout]
        if missing:
            print(f"[FAIL] closeout reply missing tokens: {missing}", file=sys.stderr)
            print(gate.stdout, file=sys.stderr)
            return 1

    print("[OK] same-turn blocked continue smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
