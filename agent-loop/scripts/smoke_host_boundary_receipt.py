#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from refresh_legacy_handoffs import (
    is_prewrite_only_validation_error,
    write_handoff_or_rollback_receipt,
    write_host_boundary_authority_receipt,
)
from validate_handoff import host_boundary_receipt_is_valid


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    closeout_round_id = "host-boundary-recorder-smoke"
    attempt_ref = "attempts/latest.md"
    evidence = "same_turn_only host visible turn boundary forced during smoke"

    with tempfile.TemporaryDirectory(prefix="agent-loop-host-boundary-") as tmp:
        run_dir = Path(tmp)
        write(
            run_dir / attempt_ref,
            "\n".join(
                [
                    "# Attempt Receipt",
                    "",
                    f"- `closeout_round_id`: `{closeout_round_id}`",
                    "- `attempt_status`: `next_action_started`",
                    "- `summary`: `smoke latest attempt`",
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
                    f"- `closeout_round_id`: `{closeout_round_id}`",
                    f"- `continue_exit_evidence`: `attempt_ref={attempt_ref}; closeout_round_id={closeout_round_id}; smoke action started`",
                    "",
                ]
            ),
        )

        result = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "record_host_boundary_receipt.py"),
                str(run_dir),
                "--evidence",
                evidence,
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode

        receipt_ref = result.stdout.strip()
        receipt_path = run_dir / receipt_ref
        if not receipt_path.exists():
            print(f"[FAIL] receipt was not created: {receipt_ref}", file=sys.stderr)
            return 1

        receipt_text = receipt_path.read_text(encoding="utf-8")
        required = [
            "authority_receipt_version=v1",
            "authority_kind=host_turn_boundary",
            "event_id=",
            "event_id_source=controller_generated_same_turn_boundary",
            f"closeout_round_id={closeout_round_id}",
            f"attempt_ref={attempt_ref}",
            f"excerpt={evidence}",
        ]
        missing = [token for token in required if token not in receipt_text]
        if missing:
            print(f"[FAIL] receipt missing tokens: {missing}", file=sys.stderr)
            print(receipt_text, file=sys.stderr)
            return 1

        missing_attempt = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "record_host_boundary_receipt.py"),
                str(run_dir),
                "--evidence",
                evidence,
                "--closeout-round-id",
                closeout_round_id,
                "--attempt-ref",
                "attempts/missing.md",
            ],
            text=True,
            capture_output=True,
        )
        if missing_attempt.returncode != 1:
            print(
                f"[FAIL] missing attempt ref should exit 1, got {missing_attempt.returncode}",
                file=sys.stderr,
            )
            print(missing_attempt.stdout, file=sys.stderr)
            print(missing_attempt.stderr, file=sys.stderr)
            return 1
        if "requires attempt_ref to resolve" not in missing_attempt.stdout:
            print("[FAIL] missing attempt ref did not explain the resolver failure", file=sys.stderr)
            print(missing_attempt.stdout, file=sys.stderr)
            return 1

        legacy_ref = write_host_boundary_authority_receipt(
            run_dir,
            "legacy-boundary-smoke",
            evidence,
            closeout_round_id,
            f"attempt_ref={attempt_ref}; closeout_round_id={closeout_round_id}; legacy refresh",
        )
        legacy_path = run_dir / legacy_ref
        if not host_boundary_receipt_is_valid(legacy_path, closeout_round_id, attempt_ref):
            print("[FAIL] legacy refresh host-boundary receipt is not validator-compatible", file=sys.stderr)
            print(legacy_path.read_text(encoding="utf-8"), file=sys.stderr)
            return 1

        missing_legacy = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "refresh_legacy_handoffs.py"),
                str(run_dir),
                "--write",
                "--force-nonlegacy",
                "--turn-exit-evidence",
                evidence,
                "--continue-exit-status",
                "next_action_started",
                "--continue-exit-evidence",
                "started without attempt ref",
            ],
            text=True,
            capture_output=True,
        )
        if missing_legacy.returncode != 1:
            print(f"[FAIL] legacy refresh without attempt_ref should exit 1, got {missing_legacy.returncode}", file=sys.stderr)
            print(missing_legacy.stdout, file=sys.stderr)
            print(missing_legacy.stderr, file=sys.stderr)
            return 1
        if "requires continue_exit_evidence with resolvable attempt_ref" not in missing_legacy.stdout:
            print("[FAIL] legacy refresh without attempt_ref did not explain the resolver failure", file=sys.stderr)
            print(missing_legacy.stdout, file=sys.stderr)
            return 1
        empty_legacy_run = run_dir / "empty-legacy-refresh"
        empty_legacy_run.mkdir()
        write(empty_legacy_run / "handoff.md", "# Handoff\n\nlegacy_field=value\n")
        missing_empty = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "refresh_legacy_handoffs.py"),
                str(empty_legacy_run),
                "--write",
                "--force-nonlegacy",
                "--turn-exit-evidence",
                evidence,
                "--continue-exit-status",
                "next_action_started",
                "--continue-exit-evidence",
                "started without attempt ref",
            ],
            text=True,
            capture_output=True,
        )
        if missing_empty.returncode != 1:
            print(f"[FAIL] empty legacy refresh without attempt_ref should exit 1, got {missing_empty.returncode}", file=sys.stderr)
            return 1
        if (empty_legacy_run / "authority").exists():
            print("[FAIL] legacy refresh without attempt_ref created authority directory before failing", file=sys.stderr)
            return 1

        escape_run = run_dir / "escape-legacy-refresh"
        escape_run.mkdir()
        write(run_dir / "outside-attempt.md", "# Outside Attempt\n")
        try:
            write_host_boundary_authority_receipt(
                escape_run,
                "legacy-boundary-escape-smoke",
                evidence,
                closeout_round_id,
                f"attempt_ref=../outside-attempt.md; closeout_round_id={closeout_round_id}; escape attempt",
            )
        except ValueError as exc:
            if "inside the run directory" not in str(exc):
                print(f"[FAIL] path escape failure used unexpected message: {exc}", file=sys.stderr)
                return 1
        else:
            print("[FAIL] legacy refresh accepted attempt_ref outside the run directory", file=sys.stderr)
            return 1
        if (escape_run / "authority").exists():
            print("[FAIL] path escape created authority directory before failing", file=sys.stderr)
            return 1

        partial_run = run_dir / "partial-write-refresh"
        partial_attempt_ref = "attempts/a.md"
        write(partial_run / partial_attempt_ref, "# Attempt\n\nattempt_status=next_action_started\n")
        write(partial_run / "handoff.md", "# Handoff\n\nlegacy_field=value\n")
        partial_failure = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "refresh_legacy_handoffs.py"),
                str(partial_run),
                "--write",
                "--force-nonlegacy",
                "--turn-exit-evidence",
                "bad",
                "--continue-exit-status",
                "next_action_started",
                "--continue-exit-evidence",
                f"attempt_ref={partial_attempt_ref}; closeout_round_id=wrong",
            ],
            text=True,
            capture_output=True,
        )
        if partial_failure.returncode != 1:
            print(
                f"[FAIL] invalid legacy refresh should exit 1, got {partial_failure.returncode}",
                file=sys.stderr,
            )
            print(partial_failure.stdout, file=sys.stderr)
            print(partial_failure.stderr, file=sys.stderr)
            return 1
        if (partial_run / "authority" / "host-turn-boundary.md").exists():
            print("[FAIL] invalid legacy refresh left a partial host-boundary receipt", file=sys.stderr)
            return 1

        stale_handoff_errors = [
            "host_turn_boundary pauses require attempt_ref to stay fresh relative to handoff.md; stale attempt proof suggests voluntary_turn_close",
            "host_turn_boundary requires a fresh host_boundary_ref receipt close to handoff.md; stale boundary proof suggests voluntary_turn_close",
        ]
        for stale_error in stale_handoff_errors:
            if not is_prewrite_only_validation_error(stale_error):
                print(f"[FAIL] stale prewrite handoff error was not recognized: {stale_error}", file=sys.stderr)
                return 1

        rollback_run = run_dir / "handoff-write-failure"
        receipt_path = rollback_run / "authority" / "host-turn-boundary.md"
        previous_receipt = "authority_receipt_version=v1\nprevious=true\n"
        write(receipt_path, previous_receipt)
        bad_handoff_path = rollback_run / "handoff.md"
        bad_handoff_path.mkdir(parents=True)
        try:
            write_handoff_or_rollback_receipt(
                bad_handoff_path,
                "# Handoff\n",
                receipt_path,
                previous_receipt,
                True,
            )
        except OSError:
            pass
        else:
            print("[FAIL] handoff write failure smoke did not raise OSError", file=sys.stderr)
            return 1
        if receipt_path.read_text(encoding="utf-8") != previous_receipt:
            print("[FAIL] handoff write failure did not roll back host-boundary receipt", file=sys.stderr)
            return 1

    print("[OK] host-boundary receipt recorder smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
