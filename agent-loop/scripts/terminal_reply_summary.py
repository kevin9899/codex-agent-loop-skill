#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from validate_handoff import REQUIRED_DELEGATED_AGENT_COUNT, clean_value, is_noneish

STOP_REPLY_PREFIXES = [
    "loop_state=",
    "run_decision=",
    "goal_completion_status=",
    "current_or_next_stage=",
    "stop_reason=",
    "stop_authorization_status=",
    "stop_consensus_status=",
    "work_process=",
    "work_summary=",
    "verification_summary=",
    "need_to_know=",
]

PLANNING_COMPLETE_REPLY_PREFIXES = [
    "loop_state=",
    "run_decision=",
    "current_or_next_stage=",
    "stop_reason=",
    "external_authority_basis=",
    "resume_instructions=",
]

LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)$")
ANGLE_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(<[^>]+>\)")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
STATUS_PREFIX_PATTERN = re.compile(r"^(?:done|in progress|pending)\s*:\s*", re.IGNORECASE)
CHECKBOX_PREFIX_PATTERN = re.compile(
    r"^\[(?:x|X|completed|done|in progress|pending| )\]\s*",
    re.IGNORECASE,
)
WHITESPACE_PATTERN = re.compile(r"\s+")
STRUCTURED_LABEL_PREFIX_PATTERN = re.compile(r"^[a-z0-9_/-]{2,40}:\s+", re.IGNORECASE)
PROCESS_ITEM_MAX = 56
SUMMARY_ITEM_MAX = 72
NEED_TO_KNOW_ITEM_MAX = 96
PREFERRED_EVIDENCE_SECTION_PATTERNS = [
    r"implementation",
    r"validation",
    r"completion",
    r"result",
    r"summary",
    r"final",
    r"구현",
    r"검증",
    r"완료",
    r"결과",
]
POSITIVE_SUMMARY_PATTERNS = [
    r"=>\s*pass",
    r"\bpass(?:ed|ing)?\b",
    r"\badded\b",
    r"\bchanged\b",
    r"\bupdated\b",
    r"\bremoved\b",
    r"\bimplemented\b",
    r"\bemits?\b",
    r"\benforces?\b",
    r"\bvalidation\b",
    r"\bfixture\b",
    r"\bcloseout\b",
    r"통과",
    r"추가",
    r"변경",
    r"수정",
    r"검증",
]
NEGATIVE_SUMMARY_PATTERNS = [
    r"\broot[_ -]?cause\b",
    r"\bcandidate\b",
    r"\brisk\b",
    r"\bmissing\b",
    r"\binspection\b",
    r"\bdiagnos(?:is|tic)\b",
    r"\bblocker\b",
    r"\breview\b",
    r"원인",
    r"위험",
    r"누락",
    r"진단",
    r"후보",
]
VERIFICATION_SUMMARY_PATTERNS = [
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\bplaywright\b",
    r"\beslint\b",
    r"\blint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"\bverify\b",
    r"\bverified\b",
    r"\bvalidation\b",
    r"\bvalidate(?:d|s)?\b",
    r"\bpass(?:ed|ing)?\b",
    r"\bproof\b",
    r"\bconsensus\b",
    r"테스트",
    r"검증",
    r"통과",
]


def normalize_markdown_text(text: str) -> str:
    rendered = ANGLE_MARKDOWN_LINK_PATTERN.sub(r"\1", text)
    rendered = MARKDOWN_LINK_PATTERN.sub(r"\1", rendered)
    rendered = re.sub(r"\]\(<[^>]+>\)", "", rendered)
    rendered = re.sub(r"\]\([^)]+\)", "", rendered)
    rendered = rendered.replace("`", "")
    rendered = rendered.replace("[", "").replace("]", "")
    rendered = STATUS_PREFIX_PATTERN.sub("", rendered)
    rendered = CHECKBOX_PREFIX_PATTERN.sub("", rendered)
    rendered = STRUCTURED_LABEL_PREFIX_PATTERN.sub("", rendered)
    rendered = WHITESPACE_PATTERN.sub(" ", clean_value(rendered))
    return rendered.rstrip(" :;,-")


def shorten_text(text: str, max_len: int) -> str:
    normalized = normalize_markdown_text(text)
    if len(normalized) <= max_len:
        return normalized
    trimmed = normalized[: max_len - 3].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0]
    return trimmed.rstrip(" ,;:-") + "..."


def markdown_list_items(path: Path, *, skip_section_labels: bool = False) -> list[str]:
    if not path.exists():
        return []

    items: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = LIST_ITEM_PATTERN.match(raw_line)
        if not match:
            continue
        raw_item = clean_value(match.group(1))
        item = normalize_markdown_text(raw_item)
        if not item:
            continue
        if (
            skip_section_labels
            and raw_line.lstrip().startswith("- ")
            and not raw_line.startswith(" ")
            and raw_item.rstrip().endswith(":")
            and len(item.split()) <= 4
        ):
            continue
        items.append(item)
    return items


def evidence_section_items(path: Path) -> list[str]:
    if not path.exists():
        return []

    sections: list[tuple[str, list[str]]] = []
    current_section = ""
    current_items: list[str] = []

    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = LIST_ITEM_PATTERN.match(raw_line)
        if not match:
            continue

        raw_item = clean_value(match.group(1))
        is_top_level_bullet = raw_line.lstrip().startswith("- ") and not raw_line.startswith(" ")
        if is_top_level_bullet and raw_item.rstrip().endswith(":"):
            if current_items:
                sections.append((current_section, current_items[:]))
            current_section = raw_item.rstrip(":").strip().lower()
            current_items = []
            continue

        item = normalize_markdown_text(raw_item)
        if not item:
            continue
        current_items.append(item)

    if current_items:
        sections.append((current_section, current_items[:]))

    preferred: list[str] = []
    fallback: list[str] = []
    for section_name, section_items in sections:
        if any(re.search(pattern, section_name, flags=re.IGNORECASE) for pattern in PREFERRED_EVIDENCE_SECTION_PATTERNS):
            preferred.extend(section_items)
        else:
            fallback.extend(section_items)

    return preferred or fallback


def summary_item_score(text: str) -> int:
    score = 0
    for pattern in POSITIVE_SUMMARY_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            score += 2
    for pattern in NEGATIVE_SUMMARY_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            score -= 2
    if len(text) < 16:
        score -= 1
    return score


def prioritize_summary_items(items: list[str]) -> list[str]:
    if not items:
        return []

    preferred = [item for item in items if summary_item_score(item) > 0]
    if len(preferred) >= 3:
        return preferred

    if preferred:
        remaining = [item for item in items if item not in preferred]
        return preferred + remaining

    return items


def value_as_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [normalize_markdown_text(str(item)) for item in value if not is_noneish(item)]
    if is_noneish(value):
        return []
    normalized = normalize_markdown_text(str(value))
    return [normalized] if normalized else []


def compress_process(items: list[str]) -> str:
    if not items:
        return "ideation -> research -> plan -> execute -> verify -> terminal closeout"

    shortened = [shorten_text(item, PROCESS_ITEM_MAX) for item in items if item]
    if len(shortened) <= 4:
        return " -> ".join(shortened)

    visible = shortened[:2] + ["..."] + shortened[-2:]
    return f"{len(shortened)} stages: " + " -> ".join(visible)


def compress_summary(items: list[str]) -> str:
    if not items:
        return "stop receipt emitted from canonical handoff state"

    shortened = [shorten_text(item, SUMMARY_ITEM_MAX) for item in items if item]
    if len(shortened) <= 3:
        return "; ".join(shortened)

    visible = shortened[:3]
    remaining = len(shortened) - len(visible)
    return "; ".join(visible) + f"; +{remaining} more"


def compress_need_to_know(items: list[str]) -> str:
    if not items:
        return "none"

    shortened = [shorten_text(item, NEED_TO_KNOW_ITEM_MAX) for item in items if item]
    if len(shortened) <= 2:
        return "; ".join(shortened)

    visible = shortened[:2]
    remaining = len(shortened) - len(visible)
    return "; ".join(visible) + f"; +{remaining} more"


def items_matching_patterns(items: list[str], patterns: list[str]) -> list[str]:
    matched: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        if any(re.search(pattern, item, flags=re.IGNORECASE) for pattern in patterns):
            matched.append(item)
            seen.add(item)
    return matched


def proof_summary_items(fields: dict[str, object]) -> list[str]:
    items: list[str] = []
    if clean_value(str(fields.get("stop_consensus_status", ""))) == "allow_unanimous":
        items.append(f"{REQUIRED_DELEGATED_AGENT_COUNT}-lane halt proof allow_unanimous")
    if clean_value(str(fields.get("goal_completion_status", ""))).startswith("verified_complete_"):
        items.append(f"{REQUIRED_DELEGATED_AGENT_COUNT}-lane completion proof verified")
    proof_text = " ".join(
        clean_value(str(fields.get(name, ""))).lower()
        for name in ("stop_consensus_evidence", "goal_completion_evidence")
    )
    if "context_mode=clean_source_first" in proof_text and "source_ref=source.md" in proof_text:
        items.append("source-first clean audit verified")
    if clean_value(str(fields.get("stop_authorization_status", ""))) == "external_authority":
        items.append("external stop authority recorded")
    return items


def derive_stop_work_process(run_dir: Path) -> str:
    plan_items = markdown_list_items(run_dir / "revised-plan.md")
    return compress_process(plan_items)


def derive_stop_work_summary(fields: dict[str, object], run_dir: Path) -> str:
    summary_items = value_as_items(fields.get("latest_evidence_summary", ""))
    if summary_items:
        return compress_summary(summary_items)

    evidence_items = evidence_section_items(run_dir / "evidence.md")
    if not evidence_items:
        evidence_items = markdown_list_items(run_dir / "evidence.md", skip_section_labels=True)
    return compress_summary(prioritize_summary_items(evidence_items))


def derive_stop_verification_summary(fields: dict[str, object], run_dir: Path) -> str:
    evidence_items = evidence_section_items(run_dir / "evidence.md")
    if not evidence_items:
        evidence_items = markdown_list_items(run_dir / "evidence.md", skip_section_labels=True)

    verification_items = items_matching_patterns(evidence_items, VERIFICATION_SUMMARY_PATTERNS)
    verification_items = proof_summary_items(fields) + verification_items
    return compress_summary(verification_items)


def derive_stop_need_to_know(fields: dict[str, object]) -> str:
    items: list[str] = []
    for field_name in ("blocking_findings", "residual_risks"):
        for item in value_as_items(fields.get(field_name, "")):
            if item and not is_noneish(item):
                items.append(item)

    goal_status = clean_value(str(fields.get("goal_completion_status", "")))
    external_basis = clean_value(str(fields.get("external_authority_basis", "")))
    if external_basis == "explicit_user_stop" and not goal_status.startswith("verified_complete_"):
        items.append("goal completion was not verified before explicit user stop")

    return compress_need_to_know(items)


def build_stop_reply_lines(fields: dict[str, object], run_dir: Path) -> list[str]:
    return [
        f"loop_state={clean_value(str(fields.get('loop_state', '')))}",
        "run_decision=stop",
        f"goal_completion_status={clean_value(str(fields.get('goal_completion_status', '')))}",
        f"current_or_next_stage={clean_value(str(fields.get('current_or_next_stage', '')))}",
        f"stop_reason={clean_value(str(fields.get('pause_reason', '')))}",
        f"stop_authorization_status={clean_value(str(fields.get('stop_authorization_status', '')))}",
        f"stop_consensus_status={clean_value(str(fields.get('stop_consensus_status', '')))}",
        f"work_process={derive_stop_work_process(run_dir)}",
        f"work_summary={derive_stop_work_summary(fields, run_dir)}",
        f"verification_summary={derive_stop_verification_summary(fields, run_dir)}",
        f"need_to_know={derive_stop_need_to_know(fields)}",
    ]
