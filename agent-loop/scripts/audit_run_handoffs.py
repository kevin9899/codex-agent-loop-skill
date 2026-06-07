#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from validate_handoff import ENUMS, clean_value, parse_handoff

LEGACY_ENUM_ALIASES = {
    "loop_state": {
        "stop_authorized",
    },
    "run_decision": {
        "allow_stop",
    },
    "external_authority_basis": {
        "user_explicit_claude_omission",
    },
}

LEGACY_REQUIRED_FIELDS = {
    "handoff_schema_version",
    "stop_consensus_status",
    "stop_consensus_evidence",
}


def classify_legacy_handoff(run_dir: Path) -> tuple[bool, str | None]:
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        return False, None

    raw_lines = handoff_path.read_text(encoding="utf-8").splitlines()
    first_non_empty = next((line.strip() for line in raw_lines if line.strip()), "")

    fields = parse_handoff(handoff_path)
    legacy_hits: list[str] = []

    if first_non_empty != "# Handoff" and re.match(r"^[a-z_]+:\s", first_non_empty):
        legacy_hits.append("flat_key_value_schema")
    elif any(
        line.strip()
        and not line.strip().startswith("#")
        and not line.strip().startswith("- ")
        and re.match(r"^[a-z_]+:\s", line.strip())
        for line in raw_lines
    ):
        legacy_hits.append("mixed_flat_key_value_schema")

    for field, aliases in LEGACY_ENUM_ALIASES.items():
        if field not in fields:
            continue
        value = clean_value(str(fields[field]))
        if value in aliases:
            legacy_hits.append(f"{field}={value}")

    for field in sorted(LEGACY_REQUIRED_FIELDS):
        if field not in fields:
            legacy_hits.append(f"missing_{field}")

    if not legacy_hits:
        return False, None

    joined = ", ".join(legacy_hits)
    return True, (
        "legacy handoff schema detected; refresh this run before trusting or resuming it "
        f"({joined}). Suggested repair: python <skill-dir>/scripts/refresh_legacy_handoffs.py {run_dir} --write --turn-exit-cause <cause> --turn-exit-evidence \"<forced-boundary-proof>\""
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate every agent-loop run handoff under a runs directory.",
    )
    parser.add_argument("runs_root", help="Path to .agents/agent-loop/runs")
    parser.add_argument(
        "--require-consensus",
        action="store_true",
        help="Pass --require-consensus through to validate_handoff.py",
    )
    parser.add_argument(
        "--only-failing",
        action="store_true",
        help="Print only failing runs",
    )
    parser.add_argument(
        "--fail-legacy",
        action="store_true",
        help="Treat legacy-schema runs as failures instead of informational migration targets.",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve().with_name("validate_handoff.py")
    runs_root = Path(args.runs_root).resolve()
    if not runs_root.exists():
        print(f"[FAIL] runs root not found: {runs_root}")
        return 1

    run_dirs = sorted(path for path in runs_root.iterdir() if path.is_dir())
    if not run_dirs:
        print(f"[FAIL] no run directories found under: {runs_root}")
        return 1

    failures = 0
    for run_dir in run_dirs:
        command = [sys.executable, str(script_path), str(run_dir)]
        if args.require_consensus:
            command.append("--require-consensus")
        result = subprocess.run(command, capture_output=True, text=True)
        passed = result.returncode == 0
        legacy, legacy_note = classify_legacy_handoff(run_dir)
        fail_legacy = args.fail_legacy or args.require_consensus
        effective_pass = passed and not (legacy and fail_legacy)
        if legacy and not fail_legacy:
            status = "LEGACY"
        else:
            status = "OK" if effective_pass else "FAIL"
        if args.only_failing and effective_pass:
            continue
        print(f"## {run_dir.name} [{status}]")
        output = (result.stdout + result.stderr).strip()
        if output:
            print(output)
        if legacy_note:
            print(legacy_note)
        print()

        if not effective_pass:
            failures += 1

    if failures:
        print(f"[FAIL] {failures} run(s) failed handoff validation.")
        return 1

    print("[OK] All run handoffs passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
