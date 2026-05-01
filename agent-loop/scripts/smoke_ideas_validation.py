#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


def not_material_ideas() -> str:
    return "\n".join(
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
            "ideation_not_material: deterministic local change.",
            "",
        ]
    )


def material_ideas(
    *,
    blocking: str = "false",
    status: str = "pending",
    refs: bool = False,
    research_ref: str = "research.md#idea-001",
    evidence_ref: str = "evidence.md#idea-001",
    extra_lines: list[str] | None = None,
    heading: str = "IDEA-001",
    idea_id: str = "IDEA-001",
    pending_reason: str = "awaiting_research",
) -> str:
    decision_fields = []
    if refs:
        decision_fields = [
            f"- `research_ref`: `{research_ref}`",
            f"- `evidence_ref`: `{evidence_ref}`",
            "- `decision_date`: `2026-05-01`",
            "- `decision_summary`: `validated by smoke fixture`",
            "- `validated_against`: `source_digest=smoke`",
        ]
    else:
        decision_fields = [
            "- `research_ref`: `none`",
            "- `evidence_ref`: `none`",
            "- `decision_date`: `none`",
            "- `decision_summary`: `none`",
            "- `validated_against`: `none`",
        ]

    return "\n".join(
        [
            "# Ideas",
            "",
            "## Ideation Gate",
            "",
            "- `ideation_status`: `completed`",
            "- `viewpoint_count`: `3`",
            "- `cap`: `timebox_minutes=5 candidate_limit=5 external_source_limit=3`",
            "- `skip_or_reopen_reason`: `none`",
            "",
            f"### {heading}",
            "",
            f"- `idea_id`: `{idea_id}`",
            "- `cycle_id`: `cycle-smoke`",
            "- `source_requirement_ref`: `source.md#goal`",
            "- `idea`: `Try a bounded external pattern comparison`",
            "- `source_or_inspiration`: `repo-local smoke fixture`",
            "- `source_type`: `source_code_or_runtime`",
            "- `source_quality`: `strong`",
            "- `provenance_ref`: `validate_handoff.py`",
            "- `accessed_at`: `2026-05-01`",
            "- `memory_only`: `false`",
            "- `why_it_might_matter`: `could change the next bounded plan action`",
            "- `existence_question`: `does the smoke fixture exist`",
            "- `applicability_question`: `does the parser handle canonical markdown fields`",
            "- `validation_required`: `runtime_evidence`",
            "- `currency_risk`: `low`",
            f"- `blocking`: `{blocking}`",
            f"- `pending_reason`: `{pending_reason}`",
            "- `last_reviewed_stage`: `ideation`",
            "- `next_review_trigger`: `none`",
            f"- `research_status`: `{status}`",
            *decision_fields,
            *(extra_lines or []),
            "",
        ]
    )


def assert_errors(name: str, errors: list[str], should_error: bool) -> None:
    if should_error and not errors:
        raise AssertionError(f"{name}: expected validation errors")
    if not should_error and errors:
        raise AssertionError(f"{name}: unexpected validation errors: {errors}")


def write_cli_fixture(run_dir: Path, ideas: str, plan_body: str, closeout_round_id: str) -> None:
    write(run_dir / "source.md", "# Source\n\nFirst implement A, then implement B.\n")
    write(run_dir / "ideas.md", ideas)
    write(run_dir / "research.md", "# Research\n\n## idea-001\n\nIDEA-001 was checked against the smoke fixture.\n")
    write(run_dir / "evidence.md", "# Evidence\n\n## idea-001\n\nIDEA-001 smoke evidence exists.\n")
    write(
        run_dir / "revised-plan.md",
        "\n".join(
            [
                "# Revised Plan",
                "",
                "## Remaining Stage Queue",
                "",
                *plan_body.splitlines(),
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
                "- `working_goal`: `smoke ideas cli validation`",
                "- `run_intent`: `implementation_loop`",
                "- `host_resume_mode`: `same_turn_only`",
                "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
                "- `current_or_next_stage`: `explicit user stop`",
                "- `stage_status`: `direct user stop requested`",
                "- `remaining_required_stages`:",
                "  - `Implement A`",
                "  - `Implement B`",
                "- `latest_evidence_summary`:",
                "  - `ideas cli validation fixture`",
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


def run_cli_validation_case(name: str, root: Path, ideas: str, plan_body: str, should_error: bool) -> None:
    scripts_dir = Path(__file__).resolve().parent
    run_dir = root / name
    closeout_round_id = f"closeout-{name}"
    write_cli_fixture(run_dir, ideas, plan_body, closeout_round_id)

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
        raise AssertionError(f"{name}: receipt failed\n{receipt.stdout}{receipt.stderr}")

    receipt_ref = receipt.stdout.strip()
    handoff = (run_dir / "handoff.md").read_text(encoding="utf-8")
    write(run_dir / "handoff.md", handoff.replace("`pending user_stop_ref`", f"`user_stop_ref={receipt_ref}`"))

    validate = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
        text=True,
        capture_output=True,
    )
    if should_error and validate.returncode == 0:
        raise AssertionError(f"{name}: expected CLI validation failure")
    if not should_error and validate.returncode != 0:
        raise AssertionError(f"{name}: unexpected CLI validation failure\n{validate.stdout}{validate.stderr}")


def main() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory(prefix="agent-loop-ideas-smoke-") as tmp:
        root = Path(tmp)
        write(root / "research.md", "# Research\n\n## idea-001\n\n- idea_id=IDEA-001\n")
        write(root / "evidence.md", "# Evidence\n\n## idea-001\n\n- idea_id=IDEA-001\n")
        write(root / "source.md", "# Source\n\n## idea-001\n\nThis is not evidence.\n")
        write(root / "evidence" / "receipt.md", "# Evidence Receipt\n\nRuntime evidence fixture.\n")

        cases = [
            ("not_material", not_material_ideas(), False),
            ("pending_nonblocking", material_ideas(), False),
            ("pending_blocking", material_ideas(blocking="true"), True),
            ("validated_missing_refs", material_ideas(status="validated", refs=False), True),
            ("validated_with_refs", material_ideas(status="validated", refs=True), False),
            ("validated_none_pending_reason", material_ideas(status="validated", refs=True, pending_reason="none"), False),
            ("pending_none_pending_reason", material_ideas(status="pending", pending_reason="none"), True),
            ("pending_empty_pending_reason", material_ideas(status="pending", pending_reason=""), True),
            (
                "validated_fake_refs",
                material_ideas(status="validated", refs=True, research_ref="banana", evidence_ref="potato"),
                True,
            ),
            (
                "validated_missing_anchors",
                material_ideas(status="validated", refs=True, research_ref="research.md#missing", evidence_ref="evidence.md#missing"),
                True,
            ),
            (
                "validated_evidence_artifact_ref",
                material_ideas(status="validated", refs=True, evidence_ref="evidence/receipt.md"),
                False,
            ),
            (
                "validated_source_artifact_not_evidence",
                material_ideas(status="validated", refs=True, evidence_ref="source.md"),
                True,
            ),
            (
                "duplicate_hides_blocking",
                material_ideas(blocking="true", extra_lines=["- `blocking`: `false`"]),
                True,
            ),
            ("heading_mismatch", material_ideas(heading="IDEA-001", idea_id="IDEA-999"), True),
            (
                "legacy_lane_count_alias",
                material_ideas().replace("- `viewpoint_count`: `3`", "- `lane_count`: `3`"),
                False,
            ),
            ("lane_five_missing_reason", material_ideas().replace("- `viewpoint_count`: `3`", "- `viewpoint_count`: `5`"), True),
            (
                "lane_five_valid_reason",
                material_ideas()
                .replace("- `viewpoint_count`: `3`", "- `viewpoint_count`: `5`")
                .replace("- `skip_or_reopen_reason`: `none`", "- `skip_or_reopen_reason`: `high_impact_ambiguous`"),
                False,
            ),
            (
                "copied_template",
                "# Ideas\n\n- `idea_id`: `<id>`\n- `research_status`: `<pending|validated|rejected|stale>`\n",
                True,
            ),
            (
                "loose_equals",
                "# Ideas\n\nideation_status = completed\nviewpoint_count = 3\ncap = timebox_minutes=5 candidate_limit=5 external_source_limit=3\nskip_or_reopen_reason = none\n",
                True,
            ),
        ]

        for name, content, should_error in cases:
            path = root / f"{name}.md"
            write(path, content)
            errors = validator.validate_ideas_artifact(path)
            assert_errors(name, errors, should_error)

        plan = root / "revised-plan.md"
        write(plan, "- `idea_ref`: `IDEA-404`\n")
        invalid_refs = validator.idea_refs_in_plan(plan) - {"IDEA-001"}
        if invalid_refs != {"IDEA-404"}:
            raise AssertionError(f"plan idea_ref check failed: {invalid_refs}")

        for header in ("## Remaining Stage Queue:", "### Remaining Stage Queue", "## Remaining Required Stages:"):
            plan = root / f"{header.replace('#', '').replace(' ', '-').replace(':', '')}.md"
            write(plan, f"# Plan\n\n{header}\n\n- Stage A\n")
            remaining = validator.extract_plan_remaining(plan)
            if remaining != ["Stage A"]:
                raise AssertionError(f"plan remaining header variant failed for {header}: {remaining}")

        run_cli_validation_case(
            "cli_validated_idea_ref",
            root,
            material_ideas(status="validated", refs=True),
            "- Complete fixture improvement\n  - `idea_ref`: `IDEA-001`",
            False,
        )
        run_cli_validation_case(
            "cli_pending_idea_ref",
            root,
            material_ideas(status="pending", refs=False),
            "- Complete fixture improvement\n  - `idea_ref`: `IDEA-001`",
            True,
        )

    print("[OK] ideas validation smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
