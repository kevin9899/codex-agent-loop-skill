#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from validate_handoff import (
    clean_value,
    extract_attempt_ref,
    parse_handoff,
    resolve_run_scoped_ref,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a host-turn-boundary authority receipt bound to the latest attempt receipt.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--evidence",
        required=True,
        help="Concrete forced-boundary evidence excerpt to record in the receipt",
    )
    parser.add_argument(
        "--closeout-round-id",
        help="Optional closeout round id; defaults to handoff.md closeout_round_id",
    )
    parser.add_argument(
        "--attempt-ref",
        help="Optional attempt receipt path; defaults to attempt_ref from handoff continue_exit_evidence",
    )
    parser.add_argument(
        "--event-id",
        help="Optional stable event id; defaults to a UTC timestamped host-boundary id",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    fields: dict[str, object] = {}
    if handoff_path.exists():
        fields = parse_handoff(handoff_path)

    closeout_round_id = clean_value(args.closeout_round_id or str(fields.get("closeout_round_id", "")))
    if not closeout_round_id:
        print("record_host_boundary_receipt.py requires --closeout-round-id or handoff.md closeout_round_id")
        return 1

    attempt_ref = clean_value(args.attempt_ref or extract_attempt_ref(fields.get("continue_exit_evidence", "")))
    if not attempt_ref:
        print("record_host_boundary_receipt.py requires --attempt-ref or handoff.md continue_exit_evidence with attempt_ref=<...>")
        return 1

    if resolve_run_scoped_ref(attempt_ref, run_dir) is None:
        print("record_host_boundary_receipt.py requires attempt_ref to resolve to an existing in-run artifact")
        return 1

    evidence = clean_value(args.evidence)
    if not evidence:
        print("record_host_boundary_receipt.py requires non-empty --evidence")
        return 1

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    event_id = clean_value(args.event_id) or f"{timestamp}-host-boundary"

    authority_dir = run_dir / "authority"
    authority_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = authority_dir / f"{timestamp}-host-turn-boundary.md"
    receipt_path.write_text(
        "\n".join(
            [
                "# Authority Receipt",
                "authority_receipt_version=v1",
                "authority_kind=host_turn_boundary",
                f"event_id={event_id}",
                f"closeout_round_id={closeout_round_id}",
                f"attempt_ref={attempt_ref}",
                f"excerpt={evidence}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(receipt_path.relative_to(run_dir).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
