#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    closeout_round_id = "closeout-smoke-explicit-user-stop"

    with tempfile.TemporaryDirectory(prefix="agent-loop-user-stop-smoke-") as tmp:
        run_dir = Path(tmp)
        write(run_dir / "source.md", "# Source\n\nFirst implement A, then implement B.\n")
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
                    "ideation_not_material: smoke fixture deterministic user-stop validation.",
                    "",
                ]
            ),
        )
        write(run_dir / "research.md", "# Research\n\nSmoke fixture.\n")
        write(
            run_dir / "revised-plan.md",
            "# Revised Plan\n\n## Remaining Required Stages\n\n- Implement A\n- Implement B\n",
        )
        write(run_dir / "evidence.md", "# Evidence\n\nUser stopped before completion.\n")
        write(
            run_dir / "handoff.md",
            "\n".join(
                [
                    "# Handoff",
                    "",
                    "- `handoff_schema_version`: `v2-stop-consensus`",
                    "- `working_goal`: `smoke explicit user stop`",
                    "- `run_intent`: `implementation_loop`",
                    "- `host_resume_mode`: `same_turn_only`",
                    "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
                    "- `current_or_next_stage`: `explicit user stop`",
                    "- `stage_status`: `direct user stop requested`",
                    "- `current_batch`: `explicit-user-stop-smoke`",
                    "- `risk_tier`: `tier1_local`",
                    "- `implementation_gate_status`: `not_applicable`",
                    "- `implementation_gate_evidence`: `smoke fixture validates explicit user stop closeout only`",
                    "- `remaining_required_stages`:",
                    "  - `Implement A`",
                    "  - `Implement B`",
                    "- `latest_evidence_summary`:",
                    "  - `direct user stop requested before completion`",
                    "- `blocking_findings`:",
                    "  - none",
                    "- `residual_risks`:",
                    "  - `goal completion was not verified before explicit user stop`",
                    "- `goal_completion_status`: `not_reached`",
                    "- `goal_completion_evidence`: `explicit user stop before completion proof`",
                    "- `loop_state`: `stopped`",
                    "- `continuation_mode`: `nonstop`",
                    f"- `closeout_round_id`: `{closeout_round_id}`",
                    "- `run_decision`: `stop`",
                    "- `sequential_objectives_status`: `open`",
                    "- `stop_authorization_status`: `external_authority`",
                    "- `stop_authorization_evidence`: `pending user_stop_ref`",
                    "- `stop_consensus_status`: `waived_external_authority`",
                    "- `stop_consensus_evidence`: `direct explicit user stop waiver`",
                    "- `external_authority_basis`: `explicit_user_stop`",
                    "- `pause_reason`: `direct explicit user stop`",
                    "- `next_mandatory_action`: `none`",
                    "- `continue_exit_status`: `not_applicable`",
                    "- `continue_exit_evidence`: `none`",
                    "- `turn_exit_cause`: `not_applicable`",
                    "- `turn_exit_evidence`: `none`",
                    "- `resume_instructions`:",
                    "  - none",
                    "",
                ]
            ),
        )

        receipt = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "record_user_stop_receipt.py"),
                str(run_dir),
                "--excerpt",
                "direct explicit user stop",
                "--closeout-round-id",
                closeout_round_id,
            ],
            text=True,
            capture_output=True,
        )
        if receipt.returncode != 0:
            sys.stderr.write(receipt.stdout)
            sys.stderr.write(receipt.stderr)
            return receipt.returncode

        receipt_ref = receipt.stdout.strip()
        handoff = (run_dir / "handoff.md").read_text(encoding="utf-8")
        handoff = handoff.replace(
            "`pending user_stop_ref`",
            f"`user_stop_ref={receipt_ref}`",
        )
        write(run_dir / "handoff.md", handoff)

        validate = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if validate.returncode != 0:
            sys.stderr.write(validate.stdout)
            sys.stderr.write(validate.stderr)
            return validate.returncode

    print("[OK] explicit user stop smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
