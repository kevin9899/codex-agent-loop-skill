#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from validate_handoff import clean_value, parse_handoff


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write an explicit-user-stop authority receipt for the current turn.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--excerpt",
        required=True,
        help="Short excerpt or paraphrase of the direct user stop instruction",
    )
    parser.add_argument(
        "--closeout-round-id",
        help="Optional closeout round id; defaults to handoff.md closeout_round_id",
    )
    parser.add_argument(
        "--message-id",
        help="Optional host message id; defaults to a UTC timestamped explicit-stop id",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    fields: dict[str, object] = {}
    if handoff_path.exists():
        fields = parse_handoff(handoff_path)

    closeout_round_id = clean_value(args.closeout_round_id or str(fields.get("closeout_round_id", "")))
    if not closeout_round_id:
        print("record_user_stop_receipt.py requires --closeout-round-id or handoff.md closeout_round_id")
        return 1

    excerpt = clean_value(args.excerpt)
    if not excerpt:
        print("record_user_stop_receipt.py requires non-empty --excerpt")
        return 1

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    message_id = clean_value(args.message_id or "") or f"{timestamp}-explicit-user-stop"

    authority_dir = run_dir / "authority"
    authority_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = authority_dir / f"{timestamp}-explicit-user-stop.md"
    receipt_path.write_text(
        "\n".join(
            [
                "# Authority Receipt",
                "authority_receipt_version=v1",
                "authority_kind=explicit_user_stop",
                f"message_id={message_id}",
                f"closeout_round_id={closeout_round_id}",
                "source_ref=current_user_message",
                f"excerpt={excerpt}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(receipt_path.relative_to(run_dir).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
