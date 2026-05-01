#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_handoff import VERIFIED_COMPLETE_STATUS, clean_value, parse_handoff


def gate_env(run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["AGENT_LOOP_CLOSEOUT_GATE"] = "1"
    env["AGENT_LOOP_GATE_RUN_DIR"] = str(run_dir)
    return env


def handoff_digest(handoff_path: Path) -> str:
    return hashlib.sha256(handoff_path.read_bytes()).hexdigest()


def latest_receipt_path(receipts_dir: Path) -> Path | None:
    candidates = sorted(receipts_dir.glob("*.md"))
    if not candidates:
        return None
    return candidates[-1]


def persist_receipt(
    run_dir: Path,
    run_decision: str,
    body: str,
    command: list[str],
    active_delta: str | None,
    blocking_or_risk: str | None,
) -> Path:
    receipts_dir = run_dir / "closeout-receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_id = f"{timestamp}-{run_decision}"
    prev_path = latest_receipt_path(receipts_dir)
    prev_receipt_id = prev_path.stem if prev_path else "none"
    handoff_path = run_dir / "handoff.md"
    fields = parse_handoff(handoff_path)

    receipt = "\n".join(
        [
            "# Closeout Receipt",
            "",
            f"- `receipt_id`: {receipt_id}",
            f"- `prev_receipt_id`: {prev_receipt_id}",
            f"- `run_decision`: {run_decision}",
            f"- `handoff_digest`: {handoff_digest(handoff_path)}",
            f"- `closeout_round_id`: {clean_value(str(fields.get('closeout_round_id', '')))}",
            f"- `command`: {' '.join(command)}",
            f"- `stop_consensus_evidence`: {clean_value(str(fields.get('stop_consensus_evidence', '')))}",
            f"- `goal_completion_evidence`: {clean_value(str(fields.get('goal_completion_evidence', '')))}",
            f"- `turn_exit_cause`: {clean_value(str(fields.get('turn_exit_cause', '')))}",
            f"- `turn_exit_evidence`: {clean_value(str(fields.get('turn_exit_evidence', '')))}",
            f"- `active_delta`: {clean_value(active_delta or 'none')}",
            f"- `blocking_or_risk`: {clean_value(blocking_or_risk or 'none')}",
            "- `handoff_snapshot`:",
            "```md",
            handoff_path.read_text(encoding="utf-8").rstrip(),
            "```",
            "- `rendered_reply`:",
            "```text",
            body.rstrip(),
            "```",
            "",
        ]
    )

    receipt_path = receipts_dir / f"{receipt_id}.md"
    receipt_path.write_text(receipt, encoding="utf-8")
    return receipt_path


def run_command(
    command: list[str],
    run_dir: Path,
    run_decision: str,
    active_delta: str | None = None,
    blocking_or_risk: str | None = None,
) -> int:
    result = subprocess.run(command, text=True, capture_output=True, env=gate_env(run_dir))
    if result.returncode == 0 and result.stdout:
        persist_receipt(run_dir, run_decision, result.stdout, command, active_delta, blocking_or_risk)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


HARD_TURN_END_REASONS = {
    "blocked_during_attempt",
    "context_budget_exhausted",
    "host_turn_boundary_pause",
    "tool_timeout_after_batch_shrink",
    "user_interrupt",
}

FORCED_REASON_EVIDENCE_PATTERNS = {
    "blocked_during_attempt": [
        r"\bblocked\b",
        r"\bblocker\b",
        r"\berror\b",
        r"\bfailure\b",
        r"\bfailed\b",
        r"\bpermission\b",
        r"\bauth\b",
        r"\brejected\b",
        r"막",
        r"차단",
        r"오류",
        r"실패",
        r"권한",
    ],
    "context_budget_exhausted": [
        r"\bcontext\b",
        r"\btoken\b",
        r"\bbudget\b",
        r"\bwindow\b",
        r"\blimit\b",
        r"\bexhaust(?:ed|ion)\b",
        r"컨텍스트",
        r"토큰",
        r"분량",
        r"한도",
        r"제한",
        r"소진",
    ],
    "host_turn_boundary_pause": [
        r"\bhost\b",
        r"\bsame-turn\b",
        r"\bsame_turn_only\b",
        r"\bvisible turn boundary\b",
        r"\bturn boundary\b",
        r"\bforced\b",
        r"호스트",
        r"턴 경계",
        r"가시적 턴",
        r"강제",
    ],
    "tool_timeout_after_batch_shrink": [
        r"\btimeout\b",
        r"\btimed out\b",
        r"\btime limit\b",
        r"\bbatch shrink\b",
        r"\bsmaller batch\b",
        r"\breduced batch\b",
        r"타임아웃",
        r"시간 제한",
        r"배치 축소",
    ],
    "user_interrupt": [
        r"\buser interrupt\b",
        r"\buser reply\b",
        r"\bnew user message\b",
        r"\binterrupted by user\b",
        r"사용자",
        r"인터럽트",
        r"새 메시지",
    ],
}


def evidence_matches_forced_reason(reason: str, evidence: str) -> bool:
    patterns = FORCED_REASON_EVIDENCE_PATTERNS.get(reason, [])
    if not patterns:
        return False

    return any(re.search(pattern, evidence, flags=re.IGNORECASE) for pattern in patterns)


def env_value(name: str) -> str:
    return clean_value(os.environ.get(name, ""))


def contains_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def delegated_quota_pause_error(fields: dict[str, object]) -> str | None:
    run_decision = clean_value(str(fields.get("run_decision", "")))
    continuation_mode = clean_value(str(fields.get("continuation_mode", "")))
    external_basis = clean_value(str(fields.get("external_authority_basis", "")))
    continue_exit_status = clean_value(str(fields.get("continue_exit_status", "")))
    evidence = " ".join(
        clean_value(str(fields.get(name, ""))).lower()
        for name in ("continue_exit_evidence", "pause_reason", "blocking_findings")
    )

    if not (
        run_decision == "pause"
        and continuation_mode == "nonstop"
        and external_basis == "host_turn_boundary"
        and continue_exit_status == "blocked_during_attempt"
    ):
        return None

    has_delegation = contains_any_pattern(
        evidence,
        [
            r"\bspawn_agent\b",
            r"\bdelegated[- ]agent\b",
            r"\bdelegated\b",
            r"\blane\b",
            r"에이전트",
        ],
    )
    has_quota = contains_any_pattern(
        evidence,
        [
            r"\bquota\b",
            r"\busage limit\b",
            r"\brate limit\b",
            r"\bcredits?\b",
            r"\btry again\b",
            r"사용량",
            r"한도",
            r"쿼터",
            r"크레딧",
        ],
    )
    if not (has_delegation and has_quota):
        return None

    return (
        "closeout_gate.py refused delegated-agent quota as a host-boundary pause. "
        "Encode it as run_decision=continue, loop_state=reassessment_pending, "
        "stop_authorization_status=not_applicable, external_authority_basis=none, "
        "continue_exit_status=blocked_during_attempt, turn_exit_cause=host_turn_boundary_pause, "
        "and emit an auto-resume continue receipt."
    )


def hard_turn_end_confirmation_error(fields: dict[str, object]) -> str | None:
    if not truthy_env("AGENT_LOOP_CONFIRMED_HOST_TURN_END"):
        return (
            "closeout_gate.py refused a nonstop turn-ending reply without "
            "AGENT_LOOP_CONFIRMED_HOST_TURN_END=1 plus a hard forced-turn-end reason. "
            "Continue the next_mandatory_action if tool work is still available."
        )

    reason = env_value("AGENT_LOOP_FORCED_TURN_END_REASON")
    if reason not in HARD_TURN_END_REASONS:
        allowed = ", ".join(sorted(HARD_TURN_END_REASONS))
        return (
            "closeout_gate.py refused a nonstop turn-ending reply because "
            "AGENT_LOOP_CONFIRMED_HOST_TURN_END=1 alone is not proof. Set "
            "AGENT_LOOP_FORCED_TURN_END_REASON to one of "
            f"{allowed} only when that hard boundary is actually present."
        )

    evidence = env_value("AGENT_LOOP_FORCED_TURN_END_EVIDENCE")
    if not evidence:
        return (
            "closeout_gate.py refused a nonstop turn-ending reply because "
            "AGENT_LOOP_FORCED_TURN_END_EVIDENCE is required. The evidence must "
            "name the concrete blocker, exhausted resource, user interrupt, or "
            "same-turn-only visible host boundary."
        )

    if not evidence_matches_forced_reason(reason, evidence):
        return (
            "closeout_gate.py refused a nonstop turn-ending reply because "
            f"AGENT_LOOP_FORCED_TURN_END_EVIDENCE does not match reason {reason}. "
            "Name the concrete blocker, timeout, context/token budget limit, user interrupt, "
            "or same-turn-only visible host boundary."
        )

    turn_exit_cause = clean_value(str(fields.get("turn_exit_cause", "")))
    if turn_exit_cause not in {reason, "host_turn_boundary_pause"}:
        return (
            "closeout_gate.py refused a nonstop turn-ending reply because "
            f"handoff turn_exit_cause={turn_exit_cause or '<empty>'} is not aligned "
            f"with forced reason {reason}."
        )

    turn_exit_evidence = clean_value(str(fields.get("turn_exit_evidence", "")))
    if evidence.lower() not in turn_exit_evidence.lower():
        return (
            "closeout_gate.py refused a nonstop turn-ending reply because "
            "AGENT_LOOP_FORCED_TURN_END_EVIDENCE is not echoed in handoff "
            "turn_exit_evidence. Record the same concrete proof before closing."
        )

    return None


def host_boundary_pause_needs_confirmation(fields: dict[str, object]) -> bool:
    run_decision = clean_value(str(fields.get("run_decision", "")))
    continuation_mode = clean_value(str(fields.get("continuation_mode", "")))
    external_basis = clean_value(str(fields.get("external_authority_basis", "")))
    next_action = clean_value(str(fields.get("next_mandatory_action", "")))
    goal_status = clean_value(str(fields.get("goal_completion_status", "")))

    return (
        run_decision == "pause"
        and continuation_mode == "nonstop"
        and external_basis == "host_turn_boundary"
        and goal_status != VERIFIED_COMPLETE_STATUS
        and bool(next_action)
    )


def nonstop_continue_needs_confirmation(fields: dict[str, object]) -> bool:
    run_decision = clean_value(str(fields.get("run_decision", "")))
    continuation_mode = clean_value(str(fields.get("continuation_mode", "")))
    next_action = clean_value(str(fields.get("next_mandatory_action", "")))
    goal_status = clean_value(str(fields.get("goal_completion_status", "")))

    return (
        run_decision == "continue"
        and continuation_mode == "nonstop"
        and goal_status != VERIFIED_COMPLETE_STATUS
        and bool(next_action)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonical public turn-end gate for agent-loop closeout replies.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--active-delta",
        help="Concrete in-flight delta for a turn-ending continue reply. Required when handoff run_decision=continue.",
    )
    parser.add_argument(
        "--blocking-or-risk",
        help="Optional blocker or risk detail for a turn-ending continue reply.",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"handoff.md not found: {handoff_path}", file=sys.stderr)
        return 1

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    scripts_dir = Path(__file__).resolve().parent

    if run_decision == "pause":
        quota_error = delegated_quota_pause_error(fields)
        if quota_error:
            print(quota_error, file=sys.stderr)
            return 2
        if host_boundary_pause_needs_confirmation(fields):
            error = hard_turn_end_confirmation_error(fields)
            if error:
                print(error, file=sys.stderr)
                return 2
        return run_command([sys.executable, str(scripts_dir / "emit_pause_reply.py"), str(run_dir)], run_dir, run_decision)

    if run_decision == "continue":
        if nonstop_continue_needs_confirmation(fields):
            error = hard_turn_end_confirmation_error(fields)
            if error:
                print(error, file=sys.stderr)
                return 2
        if not args.active_delta or not clean_value(args.active_delta):
            print("closeout_gate.py requires --active-delta when run_decision=continue", file=sys.stderr)
            return 1
        command = [
            sys.executable,
            str(scripts_dir / "emit_continue_reply.py"),
            str(run_dir),
            "--active-delta",
            args.active_delta,
        ]
        if args.blocking_or_risk:
            command.extend(["--blocking-or-risk", args.blocking_or_risk])
        return run_command(command, run_dir, run_decision, args.active_delta, args.blocking_or_risk)

    if run_decision in {"stop", "planning_complete"}:
        return run_command([sys.executable, str(scripts_dir / "emit_terminal_reply.py"), str(run_dir)], run_dir, run_decision)

    print(
        "closeout_gate.py requires handoff.md with run_decision=continue|pause|stop|planning_complete",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
