#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from validate_handoff import clean_value, parse_handoff

FIELD_ORDER = [
    "handoff_schema_version",
    "working_goal",
    "run_intent",
    "work_type",
    "review_kind",
    "host_resume_mode",
    "capability_mode",
    "authority_record_ref",
    "run_authority_status",
    "run_authority_revision",
    "run_authority_epoch",
    "source_digest",
    "stage_graph_digest",
    "adapter_manifest_ref",
    "adapter_conformance_status",
    "adapter_effective_config_digest",
    "resource_telemetry_ref",
    "research_cycle_ref",
    "research_cycle_status",
    "research_cycle_digest_set",
    "completion_subject_type",
    "completion_subject_ref",
    "completion_subject_digest",
    "composite_subject_digest",
    "challenge_cycle_ref",
    "challenge_cycle_status",
    "challenge_cycle_digest_set",
    "visible_output_contract",
    "current_or_next_stage",
    "stage_status",
    "current_batch",
    "risk_tier",
    "implementation_gate_status",
    "implementation_gate_evidence",
    "commit_queue_status",
    "remaining_required_stages",
    "latest_evidence_summary",
    "blocking_findings",
    "residual_risks",
    "goal_completion_status",
    "goal_completion_evidence",
    "loop_state",
    "continuation_mode",
    "closeout_round_id",
    "run_decision",
    "sequential_objectives_status",
    "stop_authorization_status",
    "stop_authorization_evidence",
    "stop_consensus_status",
    "stop_consensus_evidence",
    "external_authority_basis",
    "pause_reason",
    "next_mandatory_action",
    "continue_exit_status",
    "continue_exit_evidence",
    "turn_exit_cause",
    "turn_exit_evidence",
    "resume_instructions",
]


def resolve_handoff_path(path_arg: str) -> Path:
    path = Path(path_arg).resolve()
    if path.is_dir():
        return path / "handoff.md"
    return path


def parse_flat_handoff(text: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    current_key: str | None = None
    nested: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        key_match = re.match(r"^([a-z_]+):(?:\s*(.*))?$", line)
        if key_match:
            if current_key is not None:
                fields[current_key] = nested[:] if nested else ""
            current_key = key_match.group(1)
            remainder = (key_match.group(2) or "").strip()
            nested = []
            if remainder:
                fields[current_key] = clean_value(remainder)
                current_key = None
            continue

        if current_key is not None:
            nested_match = re.match(r"^\s+-\s+(.*)$", line)
            if nested_match:
                nested.append(clean_value(nested_match.group(1)))
                continue

            if line.strip():
                fields[current_key] = clean_value(line)
                current_key = None
                nested = []

    if current_key is not None:
        fields[current_key] = nested[:] if nested else ""

    return fields


def load_fields(handoff_path: Path) -> dict[str, object]:
    text = handoff_path.read_text(encoding="utf-8")
    flat_fields = parse_flat_handoff(text)
    bullet_fields = parse_handoff(handoff_path)
    fields = dict(flat_fields)
    fields.update(bullet_fields)
    return fields


def render_scalar(value: object) -> str:
    text = clean_value(str(value)) if value is not None else ""
    return text.replace("`", "'")


def render_list(items: list[object]) -> list[str]:
    rendered: list[str] = []
    for item in items:
        text = render_scalar(item)
        if text:
            rendered.append(f"  - {text}")
    return rendered


def canonicalize(fields: dict[str, object]) -> str:
    lines = ["# Handoff", ""]

    for key in FIELD_ORDER:
        value = fields.get(key, "")
        if isinstance(value, list):
            lines.append(f"- `{key}`:")
            list_lines = render_list(value)
            if list_lines:
                lines.extend(list_lines)
            continue

        text = render_scalar(value)
        lines.append(f"- `{key}`: {text}".rstrip())

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite a legacy or mixed agent-loop handoff into the canonical bullet-form v2 shape.",
    )
    parser.add_argument("path", help="Path to a run directory or directly to handoff.md")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite handoff.md in place. Default is to print the canonicalized result to stdout.",
    )
    args = parser.parse_args()

    handoff_path = resolve_handoff_path(args.path)
    if not handoff_path.exists():
        print(f"handoff.md not found: {handoff_path}", file=sys.stderr)
        return 1

    fields = load_fields(handoff_path)
    if not fields:
        print(f"no handoff fields found in: {handoff_path}", file=sys.stderr)
        return 1

    rendered = canonicalize(fields)
    if args.write:
        handoff_path.write_text(rendered, encoding="utf-8")
        print(f"[OK] canonicalized handoff: {handoff_path}")
        return 0

    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
