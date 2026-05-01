#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from canonicalize_handoff import canonicalize, load_fields
from validate_handoff import (
    clean_value,
    extract_attempt_ref,
    extract_plan_remaining,
    flatten_multivalue_text,
    has_flat_legacy_lines,
    is_noneish,
    validate_fields,
)


def resolve_run_dir(path_arg: str) -> Path:
    path = Path(path_arg).resolve()
    if path.is_file():
        if path.name != "handoff.md":
            raise ValueError(f"expected handoff.md or run dir, got file: {path}")
        return path.parent
    return path


def infer_continuation_mode(fields: dict[str, object]) -> str:
    existing = clean_value(str(fields.get("continuation_mode", "")))
    if existing:
        return existing
    run_intent = clean_value(str(fields.get("run_intent", ""))).lower()
    if "implementation" in run_intent:
        return "nonstop"
    return "default"


def infer_sequential_status(fields: dict[str, object]) -> str:
    existing = clean_value(str(fields.get("sequential_objectives_status", "")))
    if existing in {"none_detected", "open", "satisfied"}:
        return existing

    remaining = fields.get("remaining_required_stages", "")
    if is_noneish(remaining):
        return "satisfied"
    return "open"


def infer_current_stage(fields: dict[str, object], run_dir: Path) -> str:
    existing = clean_value(str(fields.get("current_or_next_stage", "")))
    if existing:
        return existing
    return f"reassess paused legacy run from {run_dir.name}"


def infer_stage_status(fields: dict[str, object]) -> str:
    existing = clean_value(str(fields.get("stage_status", "")))
    if existing:
        return existing
    return "legacy handoff refreshed into canonical paused state"


def infer_next_action(fields: dict[str, object], run_dir: Path) -> str:
    existing = clean_value(str(fields.get("next_mandatory_action", "")))
    weak_patterns = [
        r"^none(?:[_\s-]|$)",
        r"\bnone_required\b",
        r"\bawait explicit user\b",
        r"\bawait user\b",
        r"\bwhen the user asks\b",
        r"\botherwise\b",
        r"\boptional hardening\b",
        r"\bif resumed\b",
        r"\bif a new\b",
        r"\bresume when\b",
        r"사용자.*대기",
        r"사용자.*요청",
    ]
    if existing and not is_noneish(existing) and not any(
        re.search(pattern, existing, flags=re.IGNORECASE) for pattern in weak_patterns
    ):
        return existing

    return (
        "open revised-plan.md in this run directory, inspect current_or_next_stage in "
        "handoff.md, and write the first concrete restart action before any new execution"
    )


def infer_resume_instructions(run_dir: Path, next_action: str) -> list[str]:
    run_path = run_dir.as_posix()
    if "write the first concrete restart action before any new execution" in next_action:
        return [
            f"run $loop {run_path} to reopen this paused run",
            f"open {run_path}/revised-plan.md",
            f"inspect {run_path}/handoff.md for current_or_next_stage and next_mandatory_action",
            "write the first concrete restart action into handoff.md before any new execution",
        ]

    return [
        f"run $loop {run_path} to reopen this paused run",
        f"open {run_path}/revised-plan.md",
        f"inspect {run_path}/handoff.md for current_or_next_stage and next_mandatory_action",
        f"run next_mandatory_action: {next_action}",
    ]


def infer_remaining_required_stages(fields: dict[str, object], run_dir: Path, next_action: str) -> list[str]:
    existing = fields.get("remaining_required_stages", "")
    if isinstance(existing, list):
        concrete = [clean_value(str(item)) for item in existing if clean_value(str(item)) and not is_noneish(item)]
        if concrete:
            return concrete
    elif not is_noneish(existing):
        return [clean_value(str(existing))]

    from_plan = extract_plan_remaining(run_dir / "revised-plan.md")
    if from_plan:
        concrete = [clean_value(stage) for stage in from_plan if clean_value(stage) and not is_noneish(stage)]
        if concrete:
            return concrete

    return [f"resume execution from paused state by performing next_mandatory_action: {next_action}"]


def derive_closeout_round_id(boundary_token: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", clean_value(boundary_token)).strip("-")
    return f"legacy-refresh-{normalized or 'host-boundary'}"


def write_host_boundary_authority_receipt(
    run_dir: Path,
    boundary_token: str,
    turn_exit_evidence: str,
    closeout_round_id: str,
    continue_exit_evidence: str,
) -> str:
    authority_dir = run_dir / "authority"
    authority_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = authority_dir / "host-turn-boundary.md"
    attempt_ref = extract_attempt_ref(continue_exit_evidence) or "none"
    receipt = "\n".join(
        [
            "# Authority Receipt",
            "authority_receipt_version=v1",
            "authority_kind=host_turn_boundary",
            f"event_id={boundary_token}",
            f"closeout_round_id={closeout_round_id}",
            f"attempt_ref={attempt_ref}",
            f"excerpt={turn_exit_evidence}",
            "",
        ]
    )
    receipt_path.write_text(receipt, encoding="utf-8")
    return receipt_path.relative_to(run_dir).as_posix()


def refresh_fields(
    fields: dict[str, object],
    run_dir: Path,
    closeout_round_id: str,
    host_boundary_ref: str,
    continue_exit_status: str,
    continue_exit_evidence: str,
    turn_exit_evidence: str,
) -> dict[str, object]:
    refreshed = dict(fields)

    next_action = infer_next_action(refreshed, run_dir)
    refreshed["handoff_schema_version"] = "v2-stop-consensus"
    refreshed["host_resume_mode"] = "same_turn_only"
    capability_mode = clean_value(str(refreshed.get("capability_mode", "")))
    if not capability_mode:
        capability_mode = "delegated_agents_authorized_by_loop_tool_state_unknown_legacy_refresh"
    elif "delegated_agents_authorized_by_loop" not in capability_mode.lower():
        capability_mode = (
            "delegated_agents_authorized_by_loop_tool_state_unknown_legacy_refresh__"
            + capability_mode
        )
    refreshed["capability_mode"] = capability_mode
    refreshed["current_or_next_stage"] = infer_current_stage(refreshed, run_dir)
    refreshed["stage_status"] = infer_stage_status(refreshed)
    refreshed["goal_completion_status"] = "not_reached"
    refreshed["goal_completion_evidence"] = "legacy_refresh_before_goal_completion"
    refreshed["loop_state"] = "paused"
    refreshed["continuation_mode"] = infer_continuation_mode(refreshed)
    refreshed["closeout_round_id"] = closeout_round_id
    refreshed["run_decision"] = "pause"
    refreshed["remaining_required_stages"] = infer_remaining_required_stages(refreshed, run_dir, next_action)
    refreshed["sequential_objectives_status"] = infer_sequential_status(refreshed)
    refreshed["stop_authorization_status"] = "external_authority"
    refreshed["stop_authorization_evidence"] = f"host_boundary_ref={host_boundary_ref}"
    refreshed["stop_consensus_status"] = "waived_external_authority"
    refreshed["stop_consensus_evidence"] = f"host_turn_boundary host_boundary_ref={host_boundary_ref}"
    refreshed["external_authority_basis"] = "host_turn_boundary"
    refreshed["pause_reason"] = "same_turn_only visible turn boundary forced this paused handoff during legacy handoff refresh"
    refreshed["next_mandatory_action"] = next_action
    refreshed["continue_exit_status"] = continue_exit_status
    refreshed["continue_exit_evidence"] = continue_exit_evidence
    refreshed["turn_exit_cause"] = "host_turn_boundary_pause"
    refreshed["turn_exit_evidence"] = turn_exit_evidence
    refreshed["resume_instructions"] = infer_resume_instructions(run_dir, next_action)

    if "latest_evidence_summary" not in refreshed:
        refreshed["latest_evidence_summary"] = "legacy handoff refreshed into canonical paused state"
    if "blocking_findings" not in refreshed:
        refreshed["blocking_findings"] = "none"
    if "residual_risks" not in refreshed:
        refreshed["residual_risks"] = "none"
    if "pause_reason" in refreshed and is_noneish(refreshed["pause_reason"]):
        refreshed["pause_reason"] = "same_turn_only visible turn boundary forced this paused handoff during legacy handoff refresh"

    return refreshed


def collect_run_dirs(args: argparse.Namespace) -> list[Path]:
    run_dirs: list[Path] = []
    if args.runs_root:
        root = resolve_run_dir(args.runs_root)
        run_dirs.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    for path_arg in args.paths:
        run_dirs.append(resolve_run_dir(path_arg))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for run_dir in run_dirs:
        if run_dir in seen:
            continue
        deduped.append(run_dir)
        seen.add(run_dir)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh agent-loop run handoffs into a canonical same-turn paused state for safe resume.",
    )
    parser.add_argument("paths", nargs="*", help="Run directories (or handoff.md paths) to refresh")
    parser.add_argument("--runs-root", help="Refresh every run directory under this root")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite each run's handoff.md in place. Default is dry-run summary only.",
    )
    parser.add_argument(
        "--host-boundary-ref",
        default="legacy_handoff_refresh_2026-04-23",
        help="Structured host boundary reference to record in stop_authorization_evidence.",
    )
    parser.add_argument(
        "--turn-exit-cause",
        help="Deprecated compatibility arg. Refresh writes turn_exit_cause=host_turn_boundary_pause.",
    )
    parser.add_argument(
        "--turn-exit-evidence",
        help="Concrete forced-boundary evidence to persist for host_turn_boundary handoffs.",
    )
    parser.add_argument(
        "--continue-exit-status",
        choices=["next_action_started", "blocked_during_attempt"],
        help="Concrete latest-attempt status to persist for host_turn_boundary pauses.",
    )
    parser.add_argument(
        "--continue-exit-evidence",
        help="Concrete latest-attempt evidence to persist for host_turn_boundary pauses.",
    )
    parser.add_argument(
        "--force-nonlegacy",
        action="store_true",
        help="Allow overwriting a non-legacy handoff. Rejected by default.",
    )
    args = parser.parse_args()

    run_dirs = collect_run_dirs(args)
    if not run_dirs:
        parser.error("provide at least one run path or --runs-root")
    if args.write and (not args.turn_exit_evidence or not args.continue_exit_status or not args.continue_exit_evidence):
        parser.error("--write requires --turn-exit-evidence, --continue-exit-status, and --continue-exit-evidence")

    for run_dir in run_dirs:
        handoff_path = run_dir / "handoff.md"
        if not handoff_path.exists():
            print(f"[SKIP] {run_dir} (no handoff.md)")
            continue
        if args.write and not args.force_nonlegacy and not has_flat_legacy_lines(handoff_path):
            print(f"[FAIL] {run_dir} is not a legacy or mixed-format handoff; refuse refresh without --force-nonlegacy")
            return 1

        closeout_round_id = derive_closeout_round_id(args.host_boundary_ref)
        host_boundary_ref = args.host_boundary_ref
        if args.write:
            host_boundary_ref = write_host_boundary_authority_receipt(
                run_dir,
                args.host_boundary_ref,
                args.turn_exit_evidence or "forced_host_boundary_legacy_refresh",
                closeout_round_id,
                args.continue_exit_evidence or "none",
            )

        fields = load_fields(handoff_path)
        refreshed = refresh_fields(
            fields,
            run_dir,
            closeout_round_id,
            host_boundary_ref,
            args.continue_exit_status or "not_applicable",
            args.continue_exit_evidence or "none",
            args.turn_exit_evidence or "none",
        )
        rendered = canonicalize(refreshed)
        if args.write:
            validation_errors = validate_fields(refreshed, run_dir, require_consensus=True)
            if validation_errors:
                print(f"[FAIL] {run_dir} failed validation before legacy refresh write")
                for error in validation_errors:
                    print(f"- {error}")
                return 1
            handoff_path.write_text(rendered, encoding="utf-8")
            print(f"[OK] refreshed {handoff_path}")
        else:
            summary = flatten_multivalue_text(refreshed.get("next_mandatory_action", ""))
            print(f"[DRYRUN] {run_dir} -> pause / next_mandatory_action={summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
