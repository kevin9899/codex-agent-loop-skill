#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from urllib.parse import unquote
from pathlib import Path

SCALAR_FIELDS = [
    "handoff_schema_version",
    "working_goal",
    "run_intent",
    "host_resume_mode",
    "capability_mode",
    "current_or_next_stage",
    "stage_status",
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

LIST_OR_SCALAR_FIELDS = {
    "remaining_required_stages",
}

CANONICAL_FIELD_NAMES = set(SCALAR_FIELDS) | LIST_OR_SCALAR_FIELDS

# Delegated `$loop` consensus proofs must be produced with the resolved
# strongest hard pin, not inherited/default subagent settings. Operators may
# update these environment variables only when the local model catalog changes.
REQUIRED_DELEGATED_MODEL_SLUG = os.environ.get("AGENT_LOOP_REQUIRED_MODEL", "gpt-5.5").strip()
REQUIRED_DELEGATED_REASONING_EFFORT = os.environ.get(
    "AGENT_LOOP_REQUIRED_REASONING_EFFORT",
    "xhigh",
).strip()
REQUIRED_DELEGATED_MODEL_BINDING = "explicit_tool_args"
REQUIRED_DELEGATED_AGENT_COUNT = 5
VERIFIED_COMPLETE_STATUS = f"verified_complete_{REQUIRED_DELEGATED_AGENT_COUNT}agent"
REQUIRED_SOURCE_REF = "source.md"
REQUIRED_IDEAS_REF = "ideas.md"
REQUIRED_FINAL_AUDIT_CONTEXT_MODE = "clean_source_first"
REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS = "source_md_original_user_prompt"
REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED = "yes"
REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST = "untrusted_ideas_research_revised_plan_evidence_handoff"
REQUIRED_FINAL_AUDIT_REPO_INSPECTION = "fresh"
REQUIRED_FINAL_AUDIT_SCOPE_VERDICT = "original_request_satisfied"
REQUIRED_GOAL_COMPLETION_ALIGNMENT_VERDICT = "all_source_requirements_satisfied"
REQUIRED_CAPABILITY_MODE_TOKENS = (
    "delegated_agents_authorized_by_loop_tool_available",
    "delegated_agents_authorized_by_loop_tool_unavailable",
    "delegated_agents_authorized_by_loop_tool_state_unknown",
)
IDEATION_STATUSES = {"completed", "not_material", "reopened"}
IDEATION_LANE_COUNTS = {"0", "3", "5"}
IDEATION_SKIP_OR_REOPEN_REASONS = {
    "ideation_not_material",
    "remaining_gap",
    "new_constraint",
    "higher_leverage_candidate",
    "high_impact_ambiguous",
    "none",
}
IDEA_STATUSES = {"pending", "validated", "rejected", "stale"}
IDEA_SOURCE_TYPES = {
    "official_primary",
    "source_code_or_runtime",
    "vendor_docs",
    "paper_or_standard",
    "secondary_expert",
    "community_anecdote",
    "example_only",
    "ai_memory",
    "unverified_web_lead",
}
IDEA_SOURCE_QUALITIES = {"strong", "medium", "weak", "memory_only"}
IDEA_VALIDATION_REQUIREMENTS = {
    "official_docs",
    "primary_source",
    "runtime_evidence",
    "repo_inspection",
    "not_material",
}
IDEA_CURRENCY_RISKS = {"low", "medium", "high"}
IDEA_REQUIRED_FIELDS = {
    "idea_id",
    "cycle_id",
    "source_requirement_ref",
    "idea",
    "source_or_inspiration",
    "source_type",
    "source_quality",
    "provenance_ref",
    "accessed_at",
    "memory_only",
    "why_it_might_matter",
    "existence_question",
    "applicability_question",
    "validation_required",
    "currency_risk",
    "blocking",
    "pending_reason",
    "last_reviewed_stage",
    "next_review_trigger",
    "research_status",
}
IDEA_PENDING_REASONS = {"not_material", "deferred", "awaiting_research", "none"}
IDEA_REVIEW_STAGES = {"ideation", "research", "planning", "reassessment"}
IDEA_REQUIRED_BUT_NONE_ALLOWED_FIELDS = {"next_review_trigger", "pending_reason"}
IDEAS_GATE_FIELDS = {"ideation_status", "viewpoint_count", "lane_count", "cap", "skip_or_reopen_reason"}
IDEAS_KNOWN_FIELDS = IDEAS_GATE_FIELDS | IDEA_REQUIRED_FIELDS | {
    "research_ref",
    "evidence_ref",
    "decision_date",
    "decision_summary",
    "validated_against",
}

ENUMS = {
    "handoff_schema_version": {
        "v2-stop-consensus",
    },
    "run_intent": {
        "implementation_oriented",
        "planning_only",
        "implementation_loop",
    },
    "loop_state": {
        "ideation",
        "research",
        "planning",
        "execution",
        "verify",
        "reassessment_pending",
        "paused",
        "stopped",
    },
    "continuation_mode": {
        "default",
        "nonstop",
    },
    "host_resume_mode": {
        "same_turn_only",
        "durable_runtime",
    },
    "run_decision": {
        "planning_complete",
        "continue",
        "pause",
        "stop",
    },
    "sequential_objectives_status": {
        "none_detected",
        "open",
        "satisfied",
    },
    "stop_authorization_status": {
        "not_applicable",
        "not_run",
        "deny",
        "allow",
        "external_authority",
    },
    "stop_consensus_status": {
        "not_applicable",
        "not_run",
        "deny",
        "allow_unanimous",
        "waived_external_authority",
    },
    "external_authority_basis": {
        "none",
        "explicit_user_pause",
        "explicit_user_stop",
        "explicit_user_redirect",
        "human_decision_required",
        "host_turn_boundary",
    },
    "continue_exit_status": {
        "not_applicable",
        "next_action_started",
        "blocked_during_attempt",
    },
    "turn_exit_cause": {
        "not_applicable",
        "context_budget_exhausted",
        "tool_timeout_after_batch_shrink",
        "blocked_during_attempt",
        "host_turn_boundary_pause",
        "user_interrupt",
    },
    "goal_completion_status": {
        "not_reached",
        "completion_candidate",
        VERIFIED_COMPLETE_STATUS,
    },
}

REQUIRED_STOP_VIEWPOINTS = {
    "architecture_dependency",
    "failure_verification",
    "goal_efficiency",
    "requirement_alignment",
    "implementation_quality",
}

FRESH_PROOF_STATUSES = {
    "fresh",
    "current_pass",
    "current_cycle",
}

SUBJECT_DIGEST_REDACTED_HANDOFF_FIELDS = {
    "goal_completion_evidence",
    "stop_authorization_evidence",
    "stop_consensus_evidence",
}

MAX_TURN_END_ATTEMPT_STALENESS_SECONDS = 600
MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS = 180
MAX_USER_STOP_RECEIPT_STALENESS_SECONDS = 180

IMPLEMENTATION_INTENTS = {
    "implementation_oriented",
    "implementation_loop",
}

PLANNING_ONLY_INTENTS = {
    "planning_only",
}

SEQUENTIAL_PATTERNS = [
    r"\bfirst\b",
    r"\bthen\b",
    r"\bafter that\b",
    r"\bnext\b",
    r"먼저",
    r"일단",
    r"그 다음",
    r"다음으로",
]

PLANNING_ONLY_SOURCE_PATTERNS = [
    r"\bplanning[_ -]?only\b",
    r"\bplan only\b",
    r"\bjust plan\b",
    r"\bplanning only request\b",
    r"계획만",
    r"구현하지 말",
]

INFERRED_AUTHORITY_PATTERNS = [
    r"bounded objective",
    r"current bounded objective",
    r"goal satisfied",
    r"request complete",
    r"subgoal complete",
    r"done for now",
]

PAUSE_CLOSURE_SCENT_PATTERNS = [
    r"완료",
    r"마무리",
    r"정리",
    r"\bcomplete\b",
    r"\bcompletion\b",
    r"\b끝\b",
    r"\bdone\b",
    r"\bcompleted\b",
    r"\bfinished\b",
    r"\bfinaliz(?:e|ed)\b",
    r"\bwrap(?:ped)? up\b",
    r"\bqueued\b",
    r"\bnext loop\b",
    r"\bpick up\b",
    r"\bawaiting\b",
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"다음 루프",
    r"재개",
    r"이어서",
    r"대기",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

WEAK_PAUSE_RESUME_PATTERNS = [
    r"완료",
    r"마무리",
    r"정리",
    r"\b끝\b",
    r"\bdone\b",
    r"\bcompleted\b",
    r"\bfinished\b",
    r"\bcomplete\b",
    r"\bcompletion\b",
    r"\bcurrent batch complete\b",
    r"\bfinaliz(?:e|ed)\b",
    r"\bqueued\b",
    r"\bnext loop\b",
    r"\bpick up\b",
    r"\bif needed\b",
    r"\bif you want\b",
    r"\bcan take\b",
    r"\bcould\b",
    r"\bawaiting\b",
    r"\bwhen you are ready\b",
    r"\bif you are ready\b",
    r"\blet me know if\b",
    r"\btell me if\b",
    r"\bif i should\b",
    r"\bok(?:ay)? to\b",
    r"\btell me whether to proceed\b",
    r"\bshall i\b",
    r"\bshould i\b",
    r"\bwant me to\b",
    r"\bdo you want me to\b",
    r"continue\?",
    r"resume\?",
    r"proceed\?",
    r"\bcontinue from here\??\b",
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"다음 루프",
    r"필요하면",
    r"원하면",
    r"대기",
    r"준비되면",
    r"말해주시면",
    r"계속할까요",
    r"진행할까요",
    r"이어갈까요",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

HOST_BOUNDARY_REASON_PATTERNS = [
    r"host",
    r"same-turn",
    r"turn boundary",
    r"visible turn boundary",
    r"host boundary",
    r"same_turn_only",
    r"호스트",
    r"턴 경계",
    r"가시적 턴",
]

HOST_BOUNDARY_FORCE_PATTERNS = [
    r"\bforced\b",
    r"\bforce\b",
    r"\bceiling\b",
    r"\bcannot continue in this visible turn\b",
    r"\bturn must end now\b",
    r"\bhost ceiling\b",
    r"강제",
    r"턴 종료",
    r"더 진행할 수 없",
    r"호스트 한계",
]

CONTEXT_BUDGET_TURN_EXIT_PATTERNS = [
    r"\bcontext budget\b",
    r"\bcontext window\b",
    r"\btoken budget\b",
    r"\bresponse budget\b",
    r"\bmessage budget\b",
    r"\bcontext limit\b",
    r"\btoken limit\b",
    r"컨텍스트",
    r"토큰",
    r"응답 길이",
    r"메시지 길이",
]

TIMEOUT_BATCH_SHRINK_TURN_EXIT_PATTERNS = [
    r"\btimeout\b",
    r"\btimed out\b",
    r"\btime limit\b",
    r"\bbatch shrink\b",
    r"\bshrink(?:ing)? the batch\b",
    r"\bsmaller batch\b",
    r"\breduced batch\b",
    r"타임아웃",
    r"시간 제한",
    r"배치 축소",
    r"배치를 줄",
]

BLOCKED_DURING_ATTEMPT_TURN_EXIT_PATTERNS = [
    r"\bblocked\b",
    r"\bblocker\b",
    r"\bfailed during attempt\b",
    r"\bpermission\b",
    r"\bauth\b",
    r"\berror\b",
    r"\bfailure\b",
    r"\brejected\b",
    r"막",
    r"차단",
    r"권한",
    r"오류",
    r"실패",
]

USER_INTERRUPT_TURN_EXIT_PATTERNS = [
    r"\buser interrupt\b",
    r"\buser interrupted\b",
    r"\binterrupted by user\b",
    r"\buser reply\b",
    r"\buser redirected\b",
    r"\bnew user message\b",
    r"사용자",
    r"인터럽트",
    r"중단",
    r"새 메시지",
    r"리다이렉트",
]

NON_HOST_PAUSE_CAUSE_PATTERNS = [
    r"\bhuman approval\b",
    r"\bawaiting approval\b",
    r"\bapproval pending\b",
    r"\bconfirmation pending\b",
    r"\bawaiting confirmation\b",
    r"\buser decision\b",
    r"\bhuman decision\b",
    r"\bexplicit user\b",
    r"\bredirect\b",
    r"\bpermission\b",
    r"승인 대기",
    r"확인 대기",
    r"결정 대기",
    r"사용자 결정",
    r"사람 판단",
    r"리다이렉트",
]

WEAK_CONTINUE_EXIT_PATTERNS = [
    r"\binspect(?:ed|ing)?\b",
    r"\bread(?:ing)?\b",
    r"\breview(?:ed|ing)?\b",
    r"\bscope(?:d|ing)?\b",
    r"\bverify(?:ing|ied)?\b",
    r"\bcheck(?:ed|ing)?\b",
    r"\blook(?:ed|ing)? at\b",
    r"\btriag(?:e|ing)?\b",
    r"\bsweep(?:ing)?\b",
    r"\bscan(?:ning)?\b",
    r"\bexplor(?:e|ing|ation)\b",
    r"\breassess(?:ing|ment)?\b",
    r"\binventory\b",
    r"검토",
    r"읽",
    r"확인",
    r"점검",
    r"탐색",
    r"스캔",
    r"스윕",
    r"재평가",
    r"분류",
    r"판별",
    r"후보",
]

STRONG_CONTINUE_EXIT_PATTERNS = [
    r"\bspawn(?:ed|ing)?\b",
    r"\bdispatch(?:ed|ing)?\b",
    r"\bdelegat(?:e|ed|ing|ion)\b",
    r"\battempt(?:ed|ing)?\b",
    r"\bedit(?:ed|ing)?\b",
    r"\bpatch(?:ed|ing)?\b",
    r"\bupdate(?:d|ing)?\b",
    r"\bchange(?:d|ing)?\b",
    r"\bimplement(?:ed|ing)?\b",
    r"\bran\b",
    r"\brun(?:ning)?\b",
    r"\bexecute(?:d|ing)?\b",
    r"\blaunch(?:ed|ing)?\b",
    r"\bcapture(?:d|ing)?\b",
    r"\bwrite(?:s|ing|en)?\b",
    r"\bcreate(?:d|ing)?\b",
    r"\badd(?:ed|ing)?\b",
    r"\bremove(?:d|ing)?\b",
    r"\bfix(?:ed|ing)?\b",
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\beslint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"수정",
    r"패치",
    r"적용",
    r"실행",
    r"재실행",
    r"캡처",
    r"구현",
    r"작성",
    r"변경",
    r"추가",
    r"제거",
    r"테스트",
    r"검증",
]

LOCAL_EDIT_CONTINUE_PATTERNS = [
    r"\bedit(?:ed|ing)?\b",
    r"\bpatch(?:ed|ing)?\b",
    r"\bupdate(?:d|ing)?\b",
    r"\bchange(?:d|ing)?\b",
    r"\bimplement(?:ed|ing)?\b",
    r"\bwrite(?:s|ing|en)?\b",
    r"\bcreate(?:d|ing)?\b",
    r"\badd(?:ed|ing)?\b",
    r"\bremove(?:d|ing)?\b",
    r"\bfix(?:ed|ing)?\b",
    r"수정",
    r"패치",
    r"적용",
    r"구현",
    r"작성",
    r"변경",
    r"추가",
    r"제거",
]

VALIDATION_EVIDENCE_PATTERNS = [
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\beslint\b",
    r"\blint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"\bverif(?:y|ied|ying|ication)\b",
    r"\bvalidat(?:e|ed|ing|ion)\b",
    r"\bpass(?:ed|ing)?\b",
    r"\bchecks?\b",
    r"테스트",
    r"검증",
    r"린트",
    r"빌드",
    r"타입체크",
    r"통과",
]

OPEN_ENDED_CONTINUE_PATTERNS = [
    r"\btriag(?:e|ing)?\b",
    r"\bsweep(?:ing)?\b",
    r"\bscan(?:ning)?\b",
    r"\bexplor(?:e|ing|ation)\b",
    r"\breassess(?:ing|ment)?\b",
    r"\binventory\b",
    r"\bclassif(?:y|ying|ication)\b",
    r"\btaxonomy gap\b",
    r"\bgap sweep\b",
    r"탐색",
    r"스캔",
    r"스윕",
    r"재평가",
    r"분류",
    r"taxonomy gap",
    r"route inventory",
]

CANDIDATE_HUNT_PATTERNS = [
    r"\bcandidate\b",
    r"\bfind(?:ing)?\b.*\bcandidate\b",
    r"\bchoose\b.*\bcandidate\b",
    r"\bpick\b.*\bcandidate\b",
    r"판별",
    r"후보",
    r"고른다",
    r"찾는다",
    r"추린다",
]

DELEGATED_QUOTA_BLOCKER_PATTERNS = [
    r"\bspawn_agent\b",
    r"\bdelegated[- ]agent\b",
    r"\bdelegated\b",
    r"\bagent lane\b",
    r"\blane\b",
    r"\bquota\b",
    r"\busage limit\b",
    r"\brate limit\b",
    r"\bcredits?\b",
    r"\btry again\b",
    r"에이전트",
    r"사용량",
    r"한도",
    r"쿼터",
    r"크레딧",
]

CONSENT_SEEKING_PATTERNS = [
    r"continue\?",
    r"resume\?",
    r"proceed\?",
    r"\bopen (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\bspawn (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\blaunch (?:the )?(?:next )?(?:agent|agents|lane|lanes)\??\b",
    r"\bmay i (?:open|spawn|launch) (?:the )?(?:agent|agents|lane|lanes)\b",
    r"\bcontinue from here\??\b",
    r"\bshall i\b",
    r"\bshould i\b",
    r"\bwant me to\b",
    r"\bdo you want me to\b",
    r"\blet me know if\b",
    r"\btell me if\b",
    r"\bif i should\b",
    r"\bok(?:ay)? to\b",
    r"\btell me whether to proceed\b",
    r"\bif you want\b",
    r"\bwhen you are ready\b",
    r"\bif you are ready\b",
    r"\bready for me to\b",
    r"계속할까요",
    r"계속해도 될까요",
    r"계속해도 됩니까",
    r"진행할까요",
    r"진행해도 될까요",
    r"진행해도 됩니까",
    r"에이전트.*열까요",
    r"에이전트.*열어도 될까요",
    r"에이전트.*사용해도 될까요",
    r"이어갈까요",
    r"이어가도 될까요",
    r"원하시면",
    r"준비되면",
    r"말해주시면",
]

REPORT_DRIVEN_PATTERNS = [
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"\bfor reporting\b",
    r"\bfor status\b",
    r"\bfor handoff\b",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
]

COMPLETION_GATE_PATTERNS = [
    r"\b3\b",
    r"\bagent\b",
    r"\bcodex\b",
    r"\bchallenge\b",
    r"\bverify\b",
    r"\bverification\b",
    r"\bcompletion proof\b",
    r"\bgoal completion\b",
    r"에이전트",
    r"챌린지",
    r"검증",
    r"완료 증명",
]

DELEGATION_PERMISSION_CHECKPOINT_PATTERNS = [
    r"when[_ -]delegation[_ -]authorized\b",
    r"when.{0,40}\b(?:delegated[ _-])?agents?.{0,20}\b(?:are[ _-])?authori[sz]ed\b",
    r"\bdelegat(?:e|ed|ion|ing).{0,80}\bauthori[sz](?:e|ed|ation).{0,40}\b(?:pending|required|needed|waiting)\b",
    r"\bauthori[sz](?:e|ed|ation).{0,80}\bdelegat(?:e|ed|ion|ing).{0,40}\b(?:pending|required|needed|waiting)\b",
    r"\b(?:permission|approval|consent).{0,80}\b(?:open|spawn|launch|use).{0,40}\bagents?\b",
    r"\b(?:open|spawn|launch|use).{0,40}\bagents?.{0,80}\b(?:permission|approval|consent)\b",
    r"\bask(?:ing)? .{0,80}\b(?:open|spawn|launch|use).{0,40}\bagents?\b",
    r"\bagents?[_ -](?:permission|approval|consent)[_ -]pending\b",
    r"에이전트.{0,40}(허가|승인|권한).{0,20}(대기|필요)",
    r"(허가|승인|권한).{0,40}에이전트.{0,20}(대기|필요)",
    r"(위임|delegation).{0,40}(허가|승인|권한).{0,20}(대기|필요)",
]


def clean_value(value: str) -> str:
    return value.strip().strip("`").strip()


def is_noneish(value: object) -> bool:
    if isinstance(value, list):
        if not value:
            return True
        return len(value) == 1 and is_noneish(value[0])
    if value is None:
        return True
    text = clean_value(str(value)).lower()
    if not text:
        return True
    return (
        text == "none"
        or text == "n/a"
        or text == "na"
        or text.startswith("none ")
        or text.startswith("none-")
        or text.startswith("none -")
    )


def flatten_multivalue_text(value: object) -> str:
    if isinstance(value, list):
        return " | ".join(clean_value(str(item)) for item in value if clean_value(str(item)))
    return clean_value(str(value))


def contains_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def extract_structured_value(text: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}=([^;\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return clean_value(match.group(1))


def extract_inline_token_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?:^|[\s;,]){re.escape(key)}=([^\s;,\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return clean_value(match.group(1))


def extract_pipe_value_set(text: str | None) -> set[str]:
    if text is None:
        return set()
    return {clean_value(part).lower() for part in text.split("|") if clean_value(part)}


def normalize_artifact_value(value: str) -> str:
    normalized = clean_value(value)
    # Template values are often rendered as `<...>` inside backticks. Strip
    # one extra code fence layer after markdown key/value parsing.
    return clean_value(normalized)


def parse_markdown_key_values(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    duplicates: list[str] = []
    malformed: list[str] = []
    pattern = r"^\s*-\s+`([A-Za-z0-9_-]+)`\s*:\s*(.+?)\s*$"
    loose_key_value = r"^\s*(?:-\s*)?`?[A-Za-z0-9_-]+`?\s*[:=]\s*.+$"

    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.match(pattern, line)
        if not match:
            loose_match = re.match(loose_key_value, line)
            if loose_match:
                loose_key = clean_value(loose_match.group(0).split("=", 1)[0].split(":", 1)[0]).strip("- ").strip("`").lower()
                if loose_key in IDEAS_KNOWN_FIELDS:
                    malformed.append(str(line_no))
            continue
        key = clean_value(match.group(1)).lower()
        value = normalize_artifact_value(match.group(2))
        if key in fields and key not in duplicates:
            duplicates.append(key)
        fields[key] = value

    if duplicates:
        fields["_duplicate_keys"] = ",".join(sorted(duplicates))
    if malformed:
        fields["_malformed_key_value_lines"] = ",".join(malformed)
    return fields


def parse_ideas_artifact(path: Path) -> tuple[dict[str, str], list[dict[str, str]], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = list(re.finditer(r"^###\s+(IDEA-[A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE))
    first_block_start = matches[0].start() if matches else len(text)
    gate = parse_markdown_key_values(text[:first_block_start])
    candidates: list[dict[str, str]] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        fields = parse_markdown_key_values(block)
        heading_id = clean_value(match.group(1))
        fields.setdefault("idea_id", heading_id)
        fields["_heading_id"] = heading_id
        candidates.append(fields)

    return gate, candidates, text


def valid_positive_int_token(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9][0-9]*", clean_value(value)))


def cap_has_required_numeric_limits(cap: str) -> bool:
    maxima = {
        "timebox_minutes": 5,
        "candidate_limit": 5,
        "external_source_limit": 3,
    }
    for key, maximum in maxima.items():
        value = clean_value(extract_inline_token_value(cap, key) or "")
        if not valid_positive_int_token(value):
            return False
        if int(value) > maximum:
            return False
    return True


def markdown_anchor_slug(text: str) -> str:
    slug = clean_value(text).strip().strip("#").strip().lower()
    slug = slug.replace("`", "")
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def markdown_heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = markdown_anchor_slug(match.group(1))
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def artifact_markdown_ref_resolves(ref: str, run_dir: Path, expected_file: str) -> bool:
    normalized = clean_value(ref)
    if is_placeholder_reference(normalized):
        return False
    if not normalized.lower().startswith(f"{expected_file.lower()}#"):
        return False
    anchor = markdown_anchor_slug(unquote(normalized.split("#", 1)[1]))
    if not anchor:
        return False
    path = run_dir / expected_file
    return path.exists() and path.is_file() and anchor in markdown_heading_anchors(path)


def idea_decision_refs_resolve(candidate: dict[str, str], run_dir: Path) -> bool:
    research_ref = clean_value(candidate.get("research_ref", ""))
    evidence_ref = clean_value(candidate.get("evidence_ref", ""))
    if not artifact_markdown_ref_resolves(research_ref, run_dir, "research.md"):
        return False
    if artifact_markdown_ref_resolves(evidence_ref, run_dir, "evidence.md"):
        return True
    evidence_path = resolve_run_scoped_ref(evidence_ref, run_dir)
    if evidence_path is None:
        return False
    try:
        relative = evidence_path.resolve().relative_to(run_dir.resolve()).as_posix().lower()
    except ValueError:
        return False
    return relative.startswith(
        (
            "evidence/",
            "receipts/",
            "authority/",
            "closeout-receipts/",
            "status-receipts/",
        )
    )


def validate_ideas_artifact(path: Path, *, allow_in_progress_ideation: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.exists() or not path.is_file():
        return ["implementation-oriented runs require ideas.md before continue/pause/stop validation"]

    run_dir = path.parent
    gate, candidates, text = parse_ideas_artifact(path)
    lower_text = text.lower()

    if gate.get("_malformed_key_value_lines"):
        errors.append("ideas.md Ideation Gate must use canonical `- `field`: `value`` lines")
    if gate.get("_duplicate_keys"):
        errors.append(f"ideas.md Ideation Gate has duplicate field(s): {gate['_duplicate_keys']}")

    ideation_status = clean_value(gate.get("ideation_status", "")).lower()
    viewpoint_count = clean_value(gate.get("viewpoint_count", "")).lower()
    legacy_lane_count = clean_value(gate.get("lane_count", "")).lower()
    if viewpoint_count and legacy_lane_count and viewpoint_count != legacy_lane_count:
        errors.append("ideas.md viewpoint_count and legacy lane_count must match when both are present")
    if not viewpoint_count and legacy_lane_count:
        viewpoint_count = legacy_lane_count
    cap = clean_value(gate.get("cap", ""))
    skip_or_reopen_reason = clean_value(gate.get("skip_or_reopen_reason", "")).lower()

    if ideation_status not in IDEATION_STATUSES:
        errors.append("ideas.md requires ideation_status=completed|not_material|reopened")
    if viewpoint_count not in IDEATION_LANE_COUNTS:
        errors.append("ideas.md requires viewpoint_count=0|3|5")
    if not cap_has_required_numeric_limits(cap):
        errors.append(
            "ideas.md cap must include positive bounded timebox_minutes<=5, candidate_limit<=5, and external_source_limit<=3"
        )
    if skip_or_reopen_reason not in IDEATION_SKIP_OR_REOPEN_REASONS:
        errors.append(
            "ideas.md requires skip_or_reopen_reason=ideation_not_material|remaining_gap|new_constraint|higher_leverage_candidate|high_impact_ambiguous|none"
        )

    if viewpoint_count == "0":
        if ideation_status != "not_material" or skip_or_reopen_reason != "ideation_not_material":
            errors.append("ideas.md viewpoint_count=0 requires ideation_status=not_material and skip_or_reopen_reason=ideation_not_material")
        if "ideation_not_material" not in lower_text:
            errors.append("ideas.md viewpoint_count=0 requires an explicit ideation_not_material rationale")
    elif ideation_status == "not_material":
        errors.append("ideas.md ideation_status=not_material requires viewpoint_count=0")

    if viewpoint_count == "5" and skip_or_reopen_reason != "high_impact_ambiguous":
        errors.append("ideas.md viewpoint_count=5 requires skip_or_reopen_reason=high_impact_ambiguous")

    if viewpoint_count in {"3", "5"} and not candidates and not allow_in_progress_ideation:
        errors.append("ideas.md material ideation requires at least one parsed ### IDEA-* candidate")

    seen_ids: set[str] = set()
    for candidate in candidates:
        idea_id = clean_value(candidate.get("idea_id", ""))
        heading_id = clean_value(candidate.get("_heading_id", ""))
        if candidate.get("_malformed_key_value_lines"):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} must use canonical `- `field`: `value`` lines")
        if candidate.get("_duplicate_keys"):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} has duplicate field(s): {candidate['_duplicate_keys']}")
        if idea_id and heading_id and idea_id != heading_id:
            errors.append(f"ideas.md candidate heading {heading_id} must match idea_id {idea_id}")
        if not re.fullmatch(r"IDEA-[A-Za-z0-9_-]+", idea_id):
            errors.append(f"ideas.md candidate {heading_id or '<missing>'} requires a stable idea_id like IDEA-001")
        if idea_id in seen_ids:
            errors.append(f"ideas.md duplicate idea_id: {idea_id}")
        if idea_id:
            seen_ids.add(idea_id)

        for field in sorted(IDEA_REQUIRED_FIELDS):
            if field in IDEA_REQUIRED_BUT_NONE_ALLOWED_FIELDS:
                if field not in candidate or not clean_value(candidate.get(field, "")):
                    errors.append(f"ideas.md candidate {idea_id or heading_id} requires {field}")
                continue
            if is_placeholder_reference(candidate.get(field)):
                errors.append(f"ideas.md candidate {idea_id or heading_id} requires non-placeholder {field}")

        source_type = clean_value(candidate.get("source_type", "")).lower()
        source_quality = clean_value(candidate.get("source_quality", "")).lower()
        validation_required = clean_value(candidate.get("validation_required", "")).lower()
        currency_risk = clean_value(candidate.get("currency_risk", "")).lower()
        blocking = clean_value(candidate.get("blocking", "")).lower()
        memory_only = clean_value(candidate.get("memory_only", "")).lower()
        pending_reason = clean_value(candidate.get("pending_reason", "")).lower()
        last_reviewed_stage = clean_value(candidate.get("last_reviewed_stage", "")).lower()
        status = clean_value(candidate.get("research_status", "")).lower()

        if source_type and source_type not in IDEA_SOURCE_TYPES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid source_type={source_type}")
        if source_quality and source_quality not in IDEA_SOURCE_QUALITIES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid source_quality={source_quality}")
        if validation_required and validation_required not in IDEA_VALIDATION_REQUIREMENTS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid validation_required={validation_required}")
        if currency_risk and currency_risk not in IDEA_CURRENCY_RISKS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid currency_risk={currency_risk}")
        if blocking and blocking not in {"true", "false"}:
            errors.append(f"ideas.md candidate {idea_id or heading_id} requires blocking=true|false")
        if memory_only and memory_only not in {"true", "false"}:
            errors.append(f"ideas.md candidate {idea_id or heading_id} requires memory_only=true|false")
        if pending_reason and pending_reason not in IDEA_PENDING_REASONS:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid pending_reason={pending_reason}")
        if last_reviewed_stage and last_reviewed_stage not in IDEA_REVIEW_STAGES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid last_reviewed_stage={last_reviewed_stage}")
        if status and status not in IDEA_STATUSES:
            errors.append(f"ideas.md candidate {idea_id or heading_id} has invalid research_status={status}")

        if status == "pending" and pending_reason in {"", "none"}:
            errors.append(f"ideas.md pending candidate {idea_id or heading_id} requires pending_reason other than none")
        if status == "pending" and blocking == "true" and not allow_in_progress_ideation:
            errors.append("ideas.md may not carry research_status=pending with blocking=true at continue/pause/stop validation")
        if status == "stale" and blocking == "true" and not allow_in_progress_ideation:
            errors.append("ideas.md may not carry research_status=stale with blocking=true at continue/pause/stop validation")

        if status in {"validated", "rejected", "stale"}:
            for field in ("research_ref", "evidence_ref", "decision_date", "decision_summary"):
                if is_placeholder_reference(candidate.get(field)):
                    errors.append(f"ideas.md {status} candidate {idea_id or heading_id} requires non-placeholder {field}")
            decision_date = clean_value(candidate.get("decision_date", ""))
            if decision_date and not is_placeholder_reference(decision_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", decision_date):
                errors.append(f"ideas.md {status} candidate {idea_id or heading_id} requires decision_date=YYYY-MM-DD")
            if not idea_decision_refs_resolve(candidate, run_dir):
                errors.append(
                    f"ideas.md {status} candidate {idea_id or heading_id} requires research_ref=research.md#... "
                    "and evidence_ref=evidence.md#... or an existing in-run artifact"
                )

    # Catch copied templates that include field names but no concrete gate or candidate.
    if not candidates and viewpoint_count != "0" and ("idea_id" in lower_text or "research_status" in lower_text):
        errors.append("ideas.md appears to contain a copied template without concrete ### IDEA-* candidates")

    return errors


def validated_idea_ids(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    _, candidates, _ = parse_ideas_artifact(path)
    run_dir = path.parent
    return {
        clean_value(candidate.get("idea_id", ""))
        for candidate in candidates
        if clean_value(candidate.get("research_status", "")).lower() == "validated"
        and idea_decision_refs_resolve(candidate, run_dir)
    }


def idea_refs_in_plan(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    refs: set[str] = set()
    for match in re.finditer(
        r"`?(?:idea_ref|idea_id)`?\s*[:=]\s*`?(IDEA-[A-Za-z0-9_-]+)`?",
        text,
        flags=re.IGNORECASE,
    ):
        refs.add(clean_value(match.group(1)))
    return refs


def authority_snapshot_paths(run_dir: Path) -> list[Path]:
    names = ["source.md", REQUIRED_IDEAS_REF, "research.md", "revised-plan.md", "evidence.md", "handoff.md"]
    return [path for path in (run_dir / name for name in names) if path.exists() and path.is_file()]


def authority_snapshot_bytes(path: Path) -> bytes:
    if path.name != "handoff.md":
        return path.read_bytes()

    # Proof fields carry subject_digest and refs, so including them in the
    # subject digest creates an impossible self-reference. Bind proof to the
    # live authority state by hashing handoff minus proof-evidence payloads.
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.lstrip()
        redacted = False
        for field in SUBJECT_DIGEST_REDACTED_HANDOFF_FIELDS:
            if stripped.startswith(f"- `{field}`:"):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}- `{field}`: <redacted-for-subject-digest>")
                redacted = True
                break
        if not redacted:
            lines.append(line)
    return ("\n".join(lines) + "\n").encode("utf-8")


def compute_subject_digest(run_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in authority_snapshot_paths(run_dir):
        relative = path.relative_to(run_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(authority_snapshot_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def compute_source_digest(run_dir: Path) -> str:
    source_path = run_dir / REQUIRED_SOURCE_REF
    if not source_path.exists() or not source_path.is_file():
        return ""

    digest = hashlib.sha256()
    digest.update(REQUIRED_SOURCE_REF.encode("utf-8"))
    digest.update(b"\0")
    digest.update(source_path.read_bytes())
    return digest.hexdigest()


def latest_authority_mtime(run_dir: Path) -> float:
    paths = authority_snapshot_paths(run_dir)
    if not paths:
        return 0.0
    return max(path.stat().st_mtime for path in paths)


def is_placeholder_reference(value: str | None) -> bool:
    if value is None:
        return True
    normalized = clean_value(value)
    if is_noneish(normalized):
        return True
    lower = normalized.lower()
    if lower in {"<...>", "<ref>", "<value>", "tbd", "todo"}:
        return True
    return bool(re.fullmatch(r"<[^>]+>", normalized))


def authority_ref_is_resolved(value: str | None, run_dir: Path) -> bool:
    return resolve_run_scoped_ref(value, run_dir) is not None


def authority_receipt_is_valid(path: Path, expected_kind: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "authority_receipt_version").lower() != "v1":
        return False
    if extract_artifact_field(text, "authority_kind").lower() != expected_kind.lower():
        return False
    if not (
        extract_artifact_field(text, "message_id")
        or extract_artifact_field(text, "event_id")
        or extract_artifact_field(text, "source_ref")
        or extract_artifact_field(text, "excerpt")
    ):
        return False
    return True


def normalize_ref_token(value: str | None) -> str:
    if value is None:
        return ""
    text = clean_value(value)
    if not text:
        return ""
    return Path(text).as_posix()


def artifact_is_fresh_for_closeout(path: Path, handoff_path: Path, max_gap_seconds: int) -> bool:
    if not path.exists() or not handoff_path.exists():
        return False
    gap_seconds = abs(handoff_path.stat().st_mtime - path.stat().st_mtime)
    return gap_seconds <= max_gap_seconds


def host_boundary_receipt_is_valid(path: Path, closeout_round_id: str, attempt_ref: str) -> bool:
    if not authority_receipt_is_valid(path, "host_turn_boundary"):
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False

    receipt_attempt_ref = normalize_ref_token(extract_artifact_field(text, "attempt_ref"))
    if not receipt_attempt_ref:
        return False

    return receipt_attempt_ref == normalize_ref_token(attempt_ref)


def user_stop_receipt_is_valid(path: Path, closeout_round_id: str) -> bool:
    if not authority_receipt_is_valid(path, "explicit_user_stop"):
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False
    if extract_artifact_field(text, "source_ref").lower() != "current_user_message":
        return False
    if not extract_artifact_field(text, "excerpt"):
        return False
    return True


def resolve_run_scoped_ref(value: str | None, run_dir: Path) -> Path | None:
    if value is None or is_placeholder_reference(value):
        return None
    ref_path = Path(clean_value(value))
    if not ref_path.is_absolute():
        ref_path = (run_dir / ref_path).resolve()
    else:
        ref_path = ref_path.resolve()
    try:
        ref_path.relative_to(run_dir.resolve())
    except ValueError:
        return None
    if not ref_path.exists() or not ref_path.is_file():
        return None
    return ref_path


def has_actionable_resume_instructions(value: object) -> bool:
    flattened = flatten_multivalue_text(value)
    if is_noneish(flattened):
        return False
    if "?" in flattened or contains_any_pattern(flattened, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
        return False

    action_patterns = [
        r"\bopen\b",
        r"\bread\b",
        r"\brun\b",
        r"\brerun\b",
        r"\binspect\b",
        r"\breview\b",
        r"\bverify\b",
        r"\bfocus\b",
        r"열",
        r"읽",
        r"실행",
        r"재실행",
        r"확인",
        r"검토",
    ]
    has_action = contains_any_pattern(flattened, action_patterns)
    has_anchor = any(
        marker in flattened.lower()
        for marker in ("run directory", "/", ".md", ".py", ".json", ".png", ".txt", "next_mandatory_action")
    )
    has_multiple_steps = isinstance(value, list) and len([item for item in value if clean_value(str(item))]) >= 2
    return has_action and (has_anchor or has_multiple_steps)


def extract_anchor_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9_-]{4,}|[가-힣]{2,}", text.lower())
    stopwords = {
        "this",
        "that",
        "with",
        "from",
        "into",
        "after",
        "before",
        "while",
        "current",
        "next",
        "action",
        "focus",
        "open",
        "read",
        "run",
        "rerun",
        "inspect",
        "review",
        "verify",
        "directory",
        "handoff",
        "research",
        "evidence",
        "continue",
        "resume",
        "loop",
        "work",
        "again",
        "then",
        "the",
        "and",
        "for",
        "none",
        "readme",
        "openai",
        "current_or_next_stage",
        "next_mandatory_action",
    }
    return {token for token in tokens if token not in stopwords}


def has_anchor_overlap(left: object, right: object) -> bool:
    left_tokens = extract_anchor_tokens(clean_value(str(left)))
    right_tokens = extract_anchor_tokens(clean_value(str(right)))
    if not left_tokens or not right_tokens:
        return False
    return bool(left_tokens & right_tokens)


def parse_handoff(path: Path) -> dict[str, object]:
    fields: dict[str, object] = {}
    current_key: str | None = None
    nested: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^- `([^`]+)`: ?(.*)$", line)
        if match:
            if current_key is not None:
                fields[current_key] = nested[:] if nested else ""
            current_key = match.group(1)
            remainder = match.group(2).strip()
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
                fields[current_key] = nested[:] if nested else clean_value(line)
                current_key = None
                nested = []

    if current_key is not None:
        fields[current_key] = nested[:] if nested else ""

    return fields


def inspect_canonical_handoff(path: Path) -> tuple[list[str], list[str]]:
    duplicates: list[str] = []
    unknown_fields: list[str] = []
    seen: set[str] = set()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- `([^`]+)`: ?(.*)$", raw_line.rstrip())
        if not match:
            continue
        key = clean_value(match.group(1))
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
        if key not in CANONICAL_FIELD_NAMES and key not in unknown_fields:
            unknown_fields.append(key)

    return duplicates, unknown_fields


def has_flat_legacy_lines(path: Path) -> bool:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("- "):
            continue
        if re.match(r"^[a-z_]+:\s", line):
            return True
    return False


def extract_plan_remaining(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    inside = False
    collected: list[str] = []
    for line in lines:
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if heading:
            if inside:
                break
            title = clean_value(heading.group(1)).rstrip(":")
            inside = title in {"Remaining Required Stages", "Remaining Stage Queue"}
            continue
        if inside:
            bullet = re.match(r"^\s*-\s+(.*)$", line)
            if bullet:
                collected.append(clean_value(bullet.group(1)))
            elif line.strip():
                collected.append(clean_value(line))
    return collected if inside else None


def source_has_sequential_markers(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return any(re.search(pattern, text) for pattern in SEQUENTIAL_PATTERNS)


def source_explicit_planning_only(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return any(re.search(pattern, text) for pattern in PLANNING_ONLY_SOURCE_PATTERNS)


def is_inspection_only_continue_exit(status: str, evidence: object) -> bool:
    if clean_value(status) != "next_action_started":
        return False

    text = clean_value(str(evidence))
    if not text:
        return False

    weak_hit = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in WEAK_CONTINUE_EXIT_PATTERNS)
    strong_hit = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in STRONG_CONTINUE_EXIT_PATTERNS)
    return weak_hit and not strong_hit


def is_open_ended_candidate_hunt(value: object) -> bool:
    text = clean_value(str(value))
    if not text:
        return False

    candidate_hunt_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in CANDIDATE_HUNT_PATTERNS
    )
    if candidate_hunt_hit:
        return True

    open_ended_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in OPEN_ENDED_CONTINUE_PATTERNS
    )
    if not open_ended_hit:
        return False

    closeout_ready_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in STRONG_CONTINUE_EXIT_PATTERNS
    )
    return not closeout_ready_hit


def has_unverified_local_edit_signal(value: object) -> bool:
    text = clean_value(str(value))
    if not text:
        return False

    local_edit_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in LOCAL_EDIT_CONTINUE_PATTERNS
    )
    if not local_edit_hit:
        return False

    validation_hit = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in VALIDATION_EVIDENCE_PATTERNS
    )
    return not validation_hit


def turn_exit_evidence_matches_cause(cause: str, evidence: object) -> bool:
    text = clean_value(str(evidence))
    if not text:
        return False

    if cause == "host_turn_boundary_pause":
        return contains_any_pattern(text, HOST_BOUNDARY_REASON_PATTERNS) and contains_any_pattern(
            text, HOST_BOUNDARY_FORCE_PATTERNS
        )

    patterns_by_cause = {
        "context_budget_exhausted": CONTEXT_BUDGET_TURN_EXIT_PATTERNS,
        "tool_timeout_after_batch_shrink": TIMEOUT_BATCH_SHRINK_TURN_EXIT_PATTERNS,
        "blocked_during_attempt": BLOCKED_DURING_ATTEMPT_TURN_EXIT_PATTERNS,
        "user_interrupt": USER_INTERRUPT_TURN_EXIT_PATTERNS,
    }
    patterns = patterns_by_cause.get(cause)
    if patterns is None:
        return False
    return contains_any_pattern(text, patterns)


def is_delegated_quota_blocker(*values: object) -> bool:
    combined = " ".join(clean_value(str(value)).lower() for value in values if clean_value(str(value)))
    if not combined:
        return False

    has_delegation = contains_any_pattern(
        combined,
        [
            r"\bspawn_agent\b",
            r"\bdelegated[- ]agent\b",
            r"\bdelegated\b",
            r"\bagent lane\b",
            r"\blane\b",
            r"에이전트",
        ],
    )
    has_quota = contains_any_pattern(
        combined,
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
    return has_delegation and has_quota


def extract_consensus_refs(evidence: object) -> list[str]:
    text = clean_value(str(evidence))
    match = re.search(r"refs=([^\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return []
    raw_refs = match.group(1).strip()
    return [clean_value(part) for part in re.split(r"[|,]", raw_refs) if clean_value(part)]


def extract_artifact_field(text: str, key: str) -> str:
    patterns = [
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*=\s*(.+)$",
        rf"^\s*(?:-\s*)?`?{re.escape(key)}`?\s*:\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return clean_value(match.group(1))
    return ""


def extract_challenge_round_id(evidence: object) -> str:
    return clean_value(extract_inline_token_value(clean_value(str(evidence)), "challenge_round_id") or "")


def extract_closeout_round_id(evidence: object) -> str:
    return clean_value(extract_inline_token_value(clean_value(str(evidence)), "closeout_round_id") or "")


def extract_attempt_ref(evidence: object) -> str:
    return clean_value(extract_structured_value(clean_value(str(evidence)), "attempt_ref") or "")


def extract_source_digest_token(text: str) -> str:
    return clean_value(
        extract_inline_token_value(text, "source_digest")
        or extract_inline_token_value(text, "source_digest_sha256")
        or ""
    )


def final_audit_evidence_is_valid(evidence: object, run_dir: Path) -> bool:
    text = clean_value(str(evidence)).lower()
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False

    required_tokens = {
        "source_ref": REQUIRED_SOURCE_REF,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
        "audit_gap_count": "0",
        "scope_verdict": REQUIRED_FINAL_AUDIT_SCOPE_VERDICT,
    }
    for key, expected in required_tokens.items():
        if clean_value(extract_inline_token_value(text, key) or "").lower() != expected:
            return False

    return extract_source_digest_token(text).lower() == source_digest.lower()


def artifact_field_equals(text: str, key: str, expected: str) -> bool:
    return clean_value(extract_artifact_field(text, key)).lower() == expected.lower()


def final_audit_artifact_is_valid(text: str, run_dir: Path, required_phase: str) -> bool:
    source_digest = compute_source_digest(run_dir)
    if not source_digest:
        return False

    required_fields = {
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "source_requirements_reconstructed": REQUIRED_FINAL_AUDIT_REQUIREMENTS_RECONSTRUCTED,
        "claim_files_trust": REQUIRED_FINAL_AUDIT_CLAIM_FILES_TRUST,
        "repo_inspection": REQUIRED_FINAL_AUDIT_REPO_INSPECTION,
        "audit_gap_count": "0",
        "scope_verdict": REQUIRED_FINAL_AUDIT_SCOPE_VERDICT,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False

    if required_phase == "goal_completion" and not artifact_field_equals(
        text,
        "source_alignment_verdict",
        REQUIRED_GOAL_COMPLETION_ALIGNMENT_VERDICT,
    ):
        return False

    return True


def dispatch_receipt_is_valid(
    path: Path,
    *,
    required_phase: str,
    challenge_round_id: str,
    closeout_round_id: str,
    source_digest: str,
    viewpoint: str,
    agent_id: str,
) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fields = {
        "dispatch_receipt_version": "v1",
        "phase": required_phase,
        "agent_id": agent_id,
        "viewpoint": viewpoint,
        "challenge_round_id": challenge_round_id,
        "closeout_round_id": closeout_round_id,
        "source_ref": REQUIRED_SOURCE_REF,
        "source_digest": source_digest,
        "context_mode": REQUIRED_FINAL_AUDIT_CONTEXT_MODE,
        "authority_basis": REQUIRED_FINAL_AUDIT_AUTHORITY_BASIS,
        "full_history_fork": "false",
        "spawn_model_binding": REQUIRED_DELEGATED_MODEL_BINDING,
        "spawn_tool_args_model": REQUIRED_DELEGATED_MODEL_SLUG,
        "spawn_tool_args_reasoning_effort": REQUIRED_DELEGATED_REASONING_EFFORT,
    }
    for key, expected in required_fields.items():
        if not artifact_field_equals(text, key, expected):
            return False
    return True


def challenge_round_id_seen_in_receipts(run_dir: Path, round_id: str) -> bool:
    if not round_id:
        return False
    receipts_dir = run_dir / "closeout-receipts"
    if not receipts_dir.exists():
        return False
    pattern = rf"\bchallenge_round_id={re.escape(round_id)}\b"
    for receipt_path in receipts_dir.glob("*.md"):
        text = receipt_path.read_text(encoding="utf-8", errors="ignore")
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def closeout_round_id_seen_in_receipts(run_dir: Path, round_id: str) -> bool:
    if not round_id:
        return False
    for dirname in ("closeout-receipts", "status-receipts"):
        receipts_dir = run_dir / dirname
        if not receipts_dir.exists():
            continue
        pattern = rf"\bcloseout_round_id\b.*{re.escape(round_id)}|\bcloseout_round_id={re.escape(round_id)}\b"
        for receipt_path in receipts_dir.glob("*.md"):
            text = receipt_path.read_text(encoding="utf-8", errors="ignore")
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
    return False


def attempt_receipt_is_valid(path: Path, closeout_round_id: str, next_action: str, continue_exit_status: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if extract_artifact_field(text, "attempt_receipt_version").lower() != "v1":
        return False
    if extract_artifact_field(text, "closeout_round_id").lower() != closeout_round_id.lower():
        return False
    if extract_artifact_field(text, "attempt_status").lower() != continue_exit_status.lower():
        return False
    if not has_anchor_overlap(extract_artifact_field(text, "next_action"), next_action):
        return False
    if not (
        extract_artifact_field(text, "command_ref")
        or extract_artifact_field(text, "artifact_ref")
        or extract_artifact_field(text, "summary")
    ):
        return False
    return True


def has_unanimous_codex_proof(
    evidence: object,
    run_dir: Path,
    required_phase: str,
    closeout_round_id: str,
) -> bool:
    text = clean_value(str(evidence)).lower()
    if not text:
        return False

    required_tokens = [
        f"allow_count={REQUIRED_DELEGATED_AGENT_COUNT}",
        "deny_count=0",
        "ambiguous_count=0",
        "missing_count=0",
    ]
    if not all(token in text for token in required_tokens):
        return False

    viewpoint_set = extract_pipe_value_set(extract_inline_token_value(text, "viewpoint_set"))
    if viewpoint_set != REQUIRED_STOP_VIEWPOINTS:
        return False

    challenge_round_id = extract_inline_token_value(text, "challenge_round_id")
    if challenge_round_id is None or is_placeholder_reference(challenge_round_id):
        return False
    if extract_closeout_round_id(evidence).lower() != closeout_round_id.lower():
        return False

    subject_digest = extract_inline_token_value(text, "subject_digest")
    if subject_digest is None or is_placeholder_reference(subject_digest):
        return False
    if clean_value(subject_digest).lower() != compute_subject_digest(run_dir).lower():
        return False

    if extract_inline_token_value(text, "model_policy") != "resolved_strongest_hard_pin":
        return False
    if clean_value(extract_inline_token_value(text, "resolved_model_slug") or "").lower() != REQUIRED_DELEGATED_MODEL_SLUG.lower():
        return False
    if (
        clean_value(extract_inline_token_value(text, "resolved_reasoning_effort") or "").lower()
        != REQUIRED_DELEGATED_REASONING_EFFORT.lower()
    ):
        return False
    if extract_inline_token_value(text, "spawn_model_binding") != REQUIRED_DELEGATED_MODEL_BINDING:
        return False
    if not final_audit_evidence_is_valid(evidence, run_dir):
        return False

    refs = extract_consensus_refs(evidence)
    if len(refs) != REQUIRED_DELEGATED_AGENT_COUNT or len(set(refs)) != REQUIRED_DELEGATED_AGENT_COUNT:
        return False

    seen_agent_ids: set[str] = set()
    seen_viewpoints: set[str] = set()
    current_authority_mtime = latest_authority_mtime(run_dir)
    source_digest = compute_source_digest(run_dir)

    for ref in refs:
        ref_path = Path(ref)
        if ref_path.is_absolute():
            ref_path = ref_path.resolve()
        else:
            ref_path = (run_dir / ref_path).resolve()
        try:
            ref_path.relative_to(run_dir.resolve())
        except ValueError:
            return False
        if not ref_path.exists() or not ref_path.is_file():
            return False
        if current_authority_mtime and ref_path.stat().st_mtime < current_authority_mtime:
            return False

        artifact_text = ref_path.read_text(encoding="utf-8", errors="ignore")
        if extract_artifact_field(artifact_text, "phase").lower() != required_phase:
            return False
        if extract_artifact_field(artifact_text, "vote").lower() != "allow":
            return False
        if not final_audit_artifact_is_valid(artifact_text, run_dir, required_phase):
            return False

        agent_id = extract_artifact_field(artifact_text, "agent_id").lower()
        if not agent_id or agent_id in seen_agent_ids:
            return False
        seen_agent_ids.add(agent_id)

        viewpoint = extract_artifact_field(artifact_text, "viewpoint").lower()
        if viewpoint not in REQUIRED_STOP_VIEWPOINTS or viewpoint in seen_viewpoints:
            return False
        seen_viewpoints.add(viewpoint)

        artifact_round_id = (
            extract_artifact_field(artifact_text, "challenge_round_id")
            or extract_artifact_field(artifact_text, "freshness_ref")
        )
        if clean_value(artifact_round_id).lower() != challenge_round_id.lower():
            return False
        artifact_closeout_round_id = (
            extract_artifact_field(artifact_text, "closeout_round_id")
            or extract_artifact_field(artifact_text, "closeout_ref")
            or extract_artifact_field(artifact_text, "freshness_anchor")
        )
        if clean_value(artifact_closeout_round_id).lower() != closeout_round_id.lower():
            return False
        if extract_artifact_field(artifact_text, "subject_digest").lower() != clean_value(subject_digest).lower():
            return False

        if extract_artifact_field(artifact_text, "model_policy").lower() != "resolved_strongest_hard_pin":
            return False
        if (
            clean_value(extract_artifact_field(artifact_text, "resolved_model_slug")).lower()
            != REQUIRED_DELEGATED_MODEL_SLUG.lower()
        ):
            return False
        if (
            clean_value(extract_artifact_field(artifact_text, "resolved_reasoning_effort")).lower()
            != REQUIRED_DELEGATED_REASONING_EFFORT.lower()
        ):
            return False
        if not extract_artifact_field(artifact_text, "model_resolution_basis_ref"):
            return False
        if extract_artifact_field(artifact_text, "spawn_model_binding").lower() != REQUIRED_DELEGATED_MODEL_BINDING:
            return False
        if (
            clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_model")).lower()
            != REQUIRED_DELEGATED_MODEL_SLUG.lower()
        ):
            return False
        if (
            clean_value(extract_artifact_field(artifact_text, "spawn_tool_args_reasoning_effort")).lower()
            != REQUIRED_DELEGATED_REASONING_EFFORT.lower()
        ):
            return False
        spawn_tool_call_ref = extract_artifact_field(artifact_text, "spawn_tool_call_ref")
        if is_placeholder_reference(spawn_tool_call_ref):
            return False
        dispatch_path = resolve_run_scoped_ref(spawn_tool_call_ref, run_dir)
        if dispatch_path is None or not dispatch_receipt_is_valid(
            dispatch_path,
            required_phase=required_phase,
            challenge_round_id=challenge_round_id,
            closeout_round_id=closeout_round_id,
            source_digest=source_digest,
            viewpoint=viewpoint,
            agent_id=agent_id,
        ):
            return False

        freshness_status = (
            extract_artifact_field(artifact_text, "freshness_status")
            or extract_artifact_field(artifact_text, "freshness")
        ).lower()
        if freshness_status not in FRESH_PROOF_STATUSES:
            return False

    return seen_viewpoints == REQUIRED_STOP_VIEWPOINTS


def has_stop_authorization_proof(evidence: object, run_dir: Path, closeout_round_id: str) -> bool:
    return has_unanimous_codex_proof(
        evidence,
        run_dir,
        required_phase="stop_authorization",
        closeout_round_id=closeout_round_id,
    )


def has_goal_completion_proof(evidence: object, run_dir: Path, closeout_round_id: str) -> bool:
    return has_unanimous_codex_proof(
        evidence,
        run_dir,
        required_phase="goal_completion",
        closeout_round_id=closeout_round_id,
    )


def completion_candidate_points_at_challenge(*values: object) -> bool:
    combined = " ".join(clean_value(str(value)).lower() for value in values if clean_value(str(value)))
    return contains_any_pattern(combined, COMPLETION_GATE_PATTERNS)


def validate_fields(
    fields: dict[str, object],
    run_dir: Path,
    require_consensus: bool,
    live_state: bool = False,
    resume_state: bool = False,
) -> list[str]:
    errors: list[str] = []

    for key in SCALAR_FIELDS:
        if key not in fields:
            errors.append(f"missing handoff field: {key}")
    for key in LIST_OR_SCALAR_FIELDS:
        if key not in fields:
            errors.append(f"missing handoff field: {key}")

    if errors:
        return errors

    for key, allowed in ENUMS.items():
        value = clean_value(str(fields.get(key, "")))
        if value not in allowed:
            errors.append(f"{key} must be one of {sorted(allowed)}, got: {value}")

    if errors:
        return errors

    run_decision = clean_value(str(fields["run_decision"]))
    loop_state = clean_value(str(fields["loop_state"]))
    continuation_mode = clean_value(str(fields["continuation_mode"]))
    closeout_round_id = clean_value(str(fields["closeout_round_id"]))
    host_resume_mode = clean_value(str(fields["host_resume_mode"]))
    sequential_status = clean_value(str(fields["sequential_objectives_status"]))
    stop_status = clean_value(str(fields["stop_authorization_status"]))
    stop_consensus_status = clean_value(str(fields["stop_consensus_status"]))
    external_basis = clean_value(str(fields["external_authority_basis"]))
    pause_reason = clean_value(str(fields["pause_reason"])).lower()
    stop_evidence = clean_value(str(fields["stop_authorization_evidence"])).lower()
    continue_exit_status = clean_value(str(fields["continue_exit_status"]))
    continue_exit_evidence = clean_value(str(fields["continue_exit_evidence"]))
    turn_exit_cause = clean_value(str(fields["turn_exit_cause"]))
    turn_exit_evidence = clean_value(str(fields["turn_exit_evidence"]))
    turn_exit_host_boundary_ref = extract_structured_value(turn_exit_evidence, "host_boundary_ref")
    goal_completion_status = clean_value(str(fields["goal_completion_status"]))
    goal_completion_evidence = clean_value(str(fields["goal_completion_evidence"]))
    capability_mode = clean_value(str(fields["capability_mode"]))
    stop_round_id = extract_challenge_round_id(fields["stop_consensus_evidence"])
    goal_round_id = extract_challenge_round_id(fields["goal_completion_evidence"])
    run_intent = clean_value(str(fields["run_intent"])).lower()
    host_boundary_pause = run_decision == "pause" and external_basis == "host_turn_boundary"
    host_boundary_continue = (
        run_decision == "continue"
        and host_resume_mode == "same_turn_only"
        and turn_exit_cause == "host_turn_boundary_pause"
    )
    explicit_user_stop_override = (
        run_decision == "stop"
        and stop_status == "external_authority"
        and external_basis == "explicit_user_stop"
    )
    live_continue_state = (
        live_state
        and run_decision == "continue"
        and loop_state not in {"paused", "stopped"}
        and turn_exit_cause == "not_applicable"
        and is_noneish(turn_exit_evidence)
    )
    resume_instructions_text = flatten_multivalue_text(fields["resume_instructions"]).lower()
    current_stage = clean_value(str(fields["current_or_next_stage"]))
    next_action = clean_value(str(fields["next_mandatory_action"]))
    handoff_path = run_dir / "handoff.md"
    remaining_required_stages = fields["remaining_required_stages"]
    blocking_findings_text = flatten_multivalue_text(fields["blocking_findings"])
    implementation_like_intent = run_intent in IMPLEMENTATION_INTENTS
    source_path = run_dir / "source.md"
    ideas_path = run_dir / REQUIRED_IDEAS_REF
    research_path = run_dir / "research.md"
    revised_plan_path = run_dir / "revised-plan.md"
    evidence_path = run_dir / "evidence.md"
    continue_attempt_ref = extract_attempt_ref(continue_exit_evidence)

    if implementation_like_intent and continuation_mode != "nonstop":
        errors.append("implementation-oriented runs must use continuation_mode=nonstop")

    capability_mode_lower = capability_mode.lower()

    if "delegated_agents_authorized_by_loop" not in capability_mode_lower:
        errors.append(
            "agent-loop handoffs must record capability_mode with "
            "delegated_agents_authorized_by_loop; tool availability belongs in "
            "the suffix, not as a separate permission gate"
        )
    elif not any(token in capability_mode_lower for token in REQUIRED_CAPABILITY_MODE_TOKENS):
        errors.append(
            "agent-loop handoffs must record capability_mode with one of "
            "delegated_agents_authorized_by_loop_tool_available, "
            "delegated_agents_authorized_by_loop_tool_unavailable, or "
            "delegated_agents_authorized_by_loop_tool_state_unknown"
        )

    delegation_permission_checkpoint_text = " | ".join(
        [
            capability_mode,
            current_stage,
            next_action,
            flatten_multivalue_text(remaining_required_stages),
            blocking_findings_text,
            pause_reason,
            resume_instructions_text,
        ]
    )
    if (
        implementation_like_intent
        and continuation_mode == "nonstop"
        and contains_any_pattern(delegation_permission_checkpoint_text, DELEGATION_PERMISSION_CHECKPOINT_PATTERNS)
    ):
        errors.append(
            "implementation-oriented $loop runs may not make delegated-agent use a separate user-authorization checkpoint; "
            "$loop already authorizes spawn_agent lanes when available"
        )

    if run_decision in {"continue", "pause", "stop", "planning_complete"} and is_noneish(closeout_round_id):
        errors.append("turn-ending handoffs require a concrete closeout_round_id")
    elif not (resume_state and run_decision in {"continue", "pause"}) and closeout_round_id_seen_in_receipts(run_dir, closeout_round_id):
        errors.append("closeout_round_id was already used in a prior status/closeout receipt; closeout rounds must be fresh and non-reusable")

    requires_default_artifacts = run_decision in {"continue", "pause", "stop", "planning_complete"}
    requires_default_artifacts = (
        requires_default_artifacts
        or stop_consensus_status == "allow_unanimous"
        or goal_completion_status == VERIFIED_COMPLETE_STATUS
    )

    if requires_default_artifacts:
        if not source_path.exists():
            errors.append("agent-loop closeout validation requires source.md")
        if not ideas_path.exists():
            errors.append("agent-loop closeout validation requires ideas.md")
        else:
            errors.extend(
                validate_ideas_artifact(
                    ideas_path,
                    allow_in_progress_ideation=live_state and loop_state == "ideation",
                )
            )
        if not research_path.exists():
            errors.append("agent-loop closeout validation requires research.md")
        if not revised_plan_path.exists():
            errors.append("agent-loop closeout validation requires revised-plan.md")
        if not evidence_path.exists():
            errors.append("agent-loop closeout validation requires evidence.md")

        invalid_plan_idea_refs = idea_refs_in_plan(revised_plan_path) - validated_idea_ids(ideas_path)
        if invalid_plan_idea_refs:
            errors.append(
                "revised-plan.md may only cite validated ideas with research_ref/evidence_ref; invalid idea_ref(s): "
                + ", ".join(sorted(invalid_plan_idea_refs))
            )

    if stop_status == "external_authority" and external_basis == "none":
        errors.append("stop_authorization_status=external_authority requires an explicit external_authority_basis")
    if stop_status != "external_authority" and external_basis != "none":
        errors.append("external_authority_basis must be none unless stop_authorization_status=external_authority")
    if stop_status == "allow" and stop_consensus_status != "allow_unanimous":
        errors.append("stop_authorization_status=allow requires stop_consensus_status=allow_unanimous")
    if stop_status == "external_authority" and stop_consensus_status != "waived_external_authority":
        errors.append("stop_authorization_status=external_authority requires stop_consensus_status=waived_external_authority")
    if stop_status in {"not_applicable", "not_run", "deny"} and stop_consensus_status in {"allow_unanimous", "waived_external_authority"}:
        errors.append("stop_consensus_status may not claim halt proof or waiver when stop_authorization_status is not allow/external_authority")
    if stop_consensus_status == "allow_unanimous" and not has_stop_authorization_proof(
        fields["stop_consensus_evidence"], run_dir, closeout_round_id
    ):
        errors.append(
            f"stop_consensus_status=allow_unanimous requires explicit stop_authorization phase "
            f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent proof in stop_consensus_evidence"
        )
    if stop_round_id and challenge_round_id_seen_in_receipts(run_dir, stop_round_id):
        errors.append("stop_consensus_evidence challenge_round_id was already used in a prior closeout receipt; challenge rounds must be fresh and non-reusable")
    if stop_consensus_status in {"allow_unanimous", "waived_external_authority"} and is_noneish(fields["stop_consensus_evidence"]):
        errors.append("stop_consensus_status requires concrete stop_consensus_evidence")

    if is_noneish(fields["goal_completion_status"]):
        errors.append("goal_completion_status must be concrete")
    if is_noneish(fields["goal_completion_evidence"]):
        errors.append("goal_completion_evidence must be concrete")
    if goal_completion_status == VERIFIED_COMPLETE_STATUS and not has_goal_completion_proof(
        fields["goal_completion_evidence"], run_dir, closeout_round_id
    ):
        errors.append(
            f"goal_completion_status={VERIFIED_COMPLETE_STATUS} requires explicit goal_completion phase "
            f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent proof in goal_completion_evidence"
        )
    if goal_round_id and challenge_round_id_seen_in_receipts(run_dir, goal_round_id):
        errors.append("goal_completion_evidence challenge_round_id was already used in a prior closeout receipt; completion rounds must be fresh and non-reusable")

    if run_decision == "continue":
        if loop_state in {"paused", "stopped"}:
            errors.append("run_decision=continue cannot use loop_state paused/stopped")
        if is_noneish(current_stage):
            errors.append("run_decision=continue requires a live current_or_next_stage")
        if is_noneish(next_action):
            errors.append("run_decision=continue requires a live next_mandatory_action")
        elif is_open_ended_candidate_hunt(next_action):
            errors.append(
                "run_decision=continue may not end a turn on a pure triage/sweep/candidate-hunt next_mandatory_action; keep working until a concrete bounded patch, test batch, or blocker is actually in flight"
            )
        if is_noneish(remaining_required_stages):
            errors.append("run_decision=continue requires at least one remaining required stage")
        if continue_exit_status == "not_applicable":
            errors.append("run_decision=continue requires continue_exit_status to prove the latest next-action attempt")
        if is_noneish(continue_exit_evidence):
            errors.append("run_decision=continue requires concrete continue_exit_evidence")
        if is_inspection_only_continue_exit(continue_exit_status, continue_exit_evidence):
            errors.append("inspection-only continue_exit_evidence is illegal for continue_exit_status=next_action_started")
        if has_unverified_local_edit_signal(continue_exit_evidence):
            errors.append(
                "run_decision=continue may not close the turn on local-edit evidence without matching targeted validation; bundle apply_patch-sized edits with the smallest relevant test/lint/type/build proof first"
            )
        if not continue_attempt_ref:
            errors.append("run_decision=continue requires continue_exit_evidence to record attempt_ref=<in-run-artifact>")
        else:
            attempt_path = resolve_run_scoped_ref(continue_attempt_ref, run_dir)
            if attempt_path is None:
                errors.append("run_decision=continue requires attempt_ref to resolve to an existing in-run artifact")
            elif not attempt_receipt_is_valid(attempt_path, closeout_round_id, next_action, continue_exit_status):
                errors.append("run_decision=continue requires attempt_ref to resolve to a valid v1 attempt receipt bound to the current closeout_round_id and next_action")
            elif not artifact_is_fresh_for_closeout(
                attempt_path,
                handoff_path,
                MAX_TURN_END_ATTEMPT_STALENESS_SECONDS,
            ):
                errors.append("run_decision=continue requires attempt_ref to stay fresh relative to handoff.md; stale attempt proof suggests voluntary_turn_close")
        if extract_closeout_round_id(continue_exit_evidence).lower() != closeout_round_id.lower():
            errors.append("run_decision=continue requires continue_exit_evidence to record closeout_round_id=<current-closeout-round>")
        if not live_continue_state:
            if turn_exit_cause == "not_applicable":
                errors.append("run_decision=continue requires a concrete turn_exit_cause for any turn-ending continue state")
            if is_noneish(turn_exit_evidence):
                errors.append("run_decision=continue requires concrete turn_exit_evidence")
            elif not turn_exit_evidence_matches_cause(turn_exit_cause, turn_exit_evidence):
                errors.append(f"run_decision=continue requires turn_exit_evidence to match turn_exit_cause={turn_exit_cause}")
            if host_resume_mode == "same_turn_only" and turn_exit_cause != "host_turn_boundary_pause":
                errors.append("host_resume_mode=same_turn_only run_decision=continue requires turn_exit_cause=host_turn_boundary_pause")
            if host_resume_mode == "same_turn_only" and turn_exit_cause == "host_turn_boundary_pause":
                if turn_exit_host_boundary_ref is None:
                    errors.append(
                        "host_resume_mode=same_turn_only run_decision=continue requires turn_exit_evidence to record host_boundary_ref=<authority-receipt-path>"
                    )
                elif is_placeholder_reference(turn_exit_host_boundary_ref):
                    errors.append(
                        "host_resume_mode=same_turn_only run_decision=continue requires a concrete non-placeholder host_boundary_ref value"
                    )
                else:
                    authority_path = resolve_run_scoped_ref(turn_exit_host_boundary_ref, run_dir)
                    if authority_path is None:
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires host_boundary_ref to resolve to an existing in-run authority receipt artifact"
                        )
                    elif not host_boundary_receipt_is_valid(authority_path, closeout_round_id, continue_attempt_ref):
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires host_boundary_ref to resolve to a valid v1 authority receipt artifact bound to the current closeout_round_id and attempt_ref"
                        )
                    elif not artifact_is_fresh_for_closeout(
                        authority_path,
                        handoff_path,
                        MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS,
                    ):
                        errors.append(
                            "host_resume_mode=same_turn_only run_decision=continue requires a fresh host_boundary_ref receipt close to handoff.md; stale boundary proof suggests voluntary_turn_close"
                        )
            if continue_exit_status == "next_action_started" and turn_exit_cause == "blocked_during_attempt":
                errors.append("turn_exit_cause=blocked_during_attempt requires continue_exit_status=blocked_during_attempt")
            allowed_blocked_turn_causes = {
                "blocked_during_attempt",
                "tool_timeout_after_batch_shrink",
            }
            if host_boundary_continue:
                # The latest bounded action can be blocked while the visible
                # turn ends for the separate same-turn-only host boundary.
                allowed_blocked_turn_causes.add("host_turn_boundary_pause")
            if continue_exit_status == "blocked_during_attempt" and turn_exit_cause not in allowed_blocked_turn_causes:
                errors.append("continue_exit_status=blocked_during_attempt requires a matching blocker-style turn_exit_cause")
            if turn_exit_cause == "tool_timeout_after_batch_shrink" and continue_exit_status != "blocked_during_attempt":
                errors.append("turn_exit_cause=tool_timeout_after_batch_shrink requires continue_exit_status=blocked_during_attempt")
        if goal_completion_status == VERIFIED_COMPLETE_STATUS:
            errors.append(f"run_decision=continue may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")
        if goal_completion_status == "completion_candidate" and not completion_candidate_points_at_challenge(
            next_action,
            continue_exit_evidence,
            goal_completion_evidence,
        ):
            errors.append(
                f"goal_completion_status=completion_candidate requires the live continue state to point at the fresh "
                f"{REQUIRED_DELEGATED_AGENT_COUNT}-agent completion challenge"
            )

    if continue_exit_status in {"next_action_started", "blocked_during_attempt"} and run_decision != "continue" and not host_boundary_pause:
        errors.append("continue_exit_status may only prove a turn-ending continue state or a host_turn_boundary pause")
    if turn_exit_cause != "not_applicable" and run_decision != "continue" and not host_boundary_pause:
        errors.append("turn_exit_cause may only be non-default for turn-ending continue states or host_turn_boundary pauses")
    if run_decision != "continue" and not host_boundary_pause and not is_noneish(turn_exit_evidence):
        errors.append("turn_exit_evidence must stay empty unless run_decision=continue or external_authority_basis=host_turn_boundary")
    if turn_exit_cause == "host_turn_boundary_pause" and not (host_boundary_pause or host_boundary_continue):
        errors.append("turn_exit_cause=host_turn_boundary_pause requires either host-boundary pause or same_turn_only continue")

    if run_decision == "planning_complete":
        if run_intent not in PLANNING_ONLY_INTENTS:
            errors.append("run_decision=planning_complete requires run_intent=planning_only")
        if not source_explicit_planning_only(source_path):
            errors.append("run_decision=planning_complete requires source.md to explicitly record a planning-only request")
        if loop_state != "planning":
            errors.append("run_decision=planning_complete requires loop_state=planning")
        if continuation_mode == "nonstop":
            errors.append("run_decision=planning_complete is illegal in continuation_mode=nonstop")
        if stop_status != "external_authority":
            errors.append("run_decision=planning_complete requires stop_authorization_status=external_authority")
        if stop_consensus_status != "waived_external_authority":
            errors.append("run_decision=planning_complete requires stop_consensus_status=waived_external_authority")
        if external_basis != "explicit_user_redirect":
            errors.append("run_decision=planning_complete requires external_authority_basis=explicit_user_redirect")
        if is_noneish(fields["stop_authorization_evidence"]):
            errors.append("run_decision=planning_complete requires stop_authorization_evidence")
        if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
            errors.append("run_decision=planning_complete may not use consent-seeking or report-driven phrasing in pause_reason")

    if run_decision in {"pause", "stop"}:
        if stop_status not in {"allow", "external_authority"}:
            errors.append(f"run_decision={run_decision} requires stop_authorization_status=allow or external_authority")
        if is_noneish(fields["stop_authorization_evidence"]):
            errors.append(f"run_decision={run_decision} requires stop_authorization_evidence")
        if is_noneish(fields["pause_reason"]):
            errors.append(f"run_decision={run_decision} requires a concrete pause_reason")
        if run_decision == "pause" and loop_state != "paused":
            errors.append("run_decision=pause requires loop_state=paused")
        if run_decision == "stop" and loop_state != "stopped":
            errors.append("run_decision=stop requires loop_state=stopped")
        if run_decision == "stop" and sequential_status == "open" and not explicit_user_stop_override:
            errors.append("run_decision=stop is illegal while sequential_objectives_status=open")
        if require_consensus and stop_status == "not_run":
            errors.append("consensus-required mode forbids stop_authorization_status=not_run")
        if run_decision == "pause" and is_noneish(next_action):
            errors.append("run_decision=pause requires an explicit next_mandatory_action")
        if run_decision == "pause" and is_noneish(remaining_required_stages):
            errors.append("run_decision=pause requires live remaining_required_stages; do not pause in a semantically finished state")

        if run_decision == "pause":
            if goal_completion_status == VERIFIED_COMPLETE_STATUS:
                errors.append(f"run_decision=pause may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")
            if contains_any_pattern(pause_reason, PAUSE_CLOSURE_SCENT_PATTERNS):
                errors.append("run_decision=pause may not use completion-scent phrasing in pause_reason")
            if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("run_decision=pause may not use consent-seeking or report-driven phrasing in pause_reason")
            if contains_any_pattern(current_stage.lower(), PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("run_decision=pause current_or_next_stage must stay live and non-closure-scented")
            if contains_any_pattern(next_action.lower(), PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("run_decision=pause next_mandatory_action must stay live and non-closure-scented")
            if contains_any_pattern(resume_instructions_text, WEAK_PAUSE_RESUME_PATTERNS):
                errors.append("run_decision=pause may not use vague, consent-seeking, or closure-scent phrasing in resume_instructions")
            if not has_actionable_resume_instructions(fields["resume_instructions"]):
                errors.append("run_decision=pause requires actionable resume_instructions anchored to concrete restart steps")
            else:
                next_action_tokens = extract_anchor_tokens(next_action)
                resume_tokens = extract_anchor_tokens(resume_instructions_text)
                if next_action_tokens:
                    if not (next_action_tokens & resume_tokens):
                        errors.append("run_decision=pause requires resume_instructions to stay aligned with next_mandatory_action")
                elif "next_mandatory_action" not in resume_instructions_text and "current_or_next_stage" not in resume_instructions_text:
                    errors.append("run_decision=pause requires resume_instructions to reference the paused work when next_mandatory_action lacks stable anchor tokens")

            if goal_completion_status == "completion_candidate" and not completion_candidate_points_at_challenge(
                next_action,
                resume_instructions_text,
                goal_completion_evidence,
            ):
                errors.append(
                    f"goal_completion_status=completion_candidate requires next_mandatory_action or resume_instructions "
                    f"to point at the fresh {REQUIRED_DELEGATED_AGENT_COUNT}-agent completion challenge"
                )

            if external_basis == "host_turn_boundary":
                if is_delegated_quota_blocker(continue_exit_evidence, pause_reason):
                    errors.append(
                        "delegated-agent quota blockers must use run_decision=continue with "
                        "continue_exit_status=blocked_during_attempt and auto-resume; they are not host-boundary pause authority"
                    )
                if turn_exit_cause != "host_turn_boundary_pause":
                    errors.append("host_turn_boundary pauses require turn_exit_cause=host_turn_boundary_pause")
                if is_noneish(turn_exit_evidence):
                    errors.append("host_turn_boundary pauses require concrete turn_exit_evidence")
                elif not turn_exit_evidence_matches_cause(turn_exit_cause, turn_exit_evidence):
                    errors.append(f"host_turn_boundary pause turn_exit_evidence must match turn_exit_cause={turn_exit_cause}")
                if continue_exit_status == "not_applicable":
                    errors.append("host_turn_boundary pauses require continue_exit_status to prove the latest next-action attempt")
                if is_noneish(continue_exit_evidence):
                    errors.append("host_turn_boundary pauses require concrete continue_exit_evidence")
                elif is_inspection_only_continue_exit(continue_exit_status, continue_exit_evidence):
                    errors.append("host_turn_boundary pauses may not use inspection-only continue_exit_evidence for continue_exit_status=next_action_started")
                elif has_unverified_local_edit_signal(continue_exit_evidence):
                    errors.append(
                        "host_turn_boundary pauses may not close on local-edit evidence without matching targeted validation; finish the smallest relevant verification batch before yielding the visible turn"
                    )
                elif not has_anchor_overlap(next_action, continue_exit_evidence):
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to stay anchored to next_mandatory_action")
                host_attempt_ref = extract_attempt_ref(continue_exit_evidence)
                if not host_attempt_ref:
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to record attempt_ref=<in-run-artifact>")
                else:
                    attempt_path = resolve_run_scoped_ref(host_attempt_ref, run_dir)
                    if attempt_path is None:
                        errors.append("host_turn_boundary pauses require attempt_ref to resolve to an existing in-run artifact")
                    elif not attempt_receipt_is_valid(attempt_path, closeout_round_id, next_action, continue_exit_status):
                        errors.append("host_turn_boundary pauses require attempt_ref to resolve to a valid v1 attempt receipt bound to the current closeout_round_id and next_action")
                    elif not artifact_is_fresh_for_closeout(
                        attempt_path,
                        handoff_path,
                        MAX_TURN_END_ATTEMPT_STALENESS_SECONDS,
                    ):
                        errors.append("host_turn_boundary pauses require attempt_ref to stay fresh relative to handoff.md; stale attempt proof suggests voluntary_turn_close")
                if extract_closeout_round_id(continue_exit_evidence).lower() != closeout_round_id.lower():
                    errors.append("host_turn_boundary pauses require continue_exit_evidence to record closeout_round_id=<current-closeout-round>")

        if run_decision == "stop":
            if contains_any_pattern(pause_reason, PAUSE_CLOSURE_SCENT_PATTERNS):
                errors.append("run_decision=stop may not use soft-close or queued-for-later phrasing in pause_reason")
            if contains_any_pattern(pause_reason, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("run_decision=stop may not use consent-seeking or report-driven phrasing in pause_reason")
            if external_basis == "explicit_user_stop":
                if goal_completion_status == "completion_candidate":
                    errors.append("explicit_user_stop may not leave goal_completion_status=completion_candidate")
            elif goal_completion_status != VERIFIED_COMPLETE_STATUS:
                errors.append(
                    f"run_decision=stop requires goal_completion_status={VERIFIED_COMPLETE_STATUS} unless the basis is a direct explicit user stop"
                )
            if stop_status == "allow":
                stop_round_id = extract_challenge_round_id(fields["stop_consensus_evidence"])
                goal_round_id = extract_challenge_round_id(fields["goal_completion_evidence"])
                if not stop_round_id or not goal_round_id:
                    errors.append("autonomous stop requires explicit challenge_round_id in both stop_consensus_evidence and goal_completion_evidence")
                elif stop_round_id == goal_round_id:
                    errors.append(
                        f"autonomous stop requires distinct fresh {REQUIRED_DELEGATED_AGENT_COUNT}-agent rounds for halt proof and goal-completion proof"
                    )

        if host_resume_mode == "same_turn_only" and run_decision == "pause":
            if stop_status != "external_authority":
                errors.append("host_resume_mode=same_turn_only requires run_decision=pause to use stop_authorization_status=external_authority")
            if external_basis not in {
                "explicit_user_pause",
                "explicit_user_redirect",
                "human_decision_required",
                "host_turn_boundary",
            }:
                errors.append("host_resume_mode=same_turn_only requires run_decision=pause to use a truthful external authority basis")

    if stop_status == "external_authority":
        if external_basis in {"explicit_user_pause", "human_decision_required"} or (
            external_basis == "explicit_user_redirect" and run_decision != "planning_complete"
        ):
            errors.append(
                "explicit_user_pause, explicit_user_redirect, and human_decision_required require host-produced "
                "immutable authority and are unsupported in the default local file-backed profile"
            )
        if run_decision == "pause" and external_basis not in {
            "explicit_user_pause",
            "explicit_user_redirect",
            "human_decision_required",
            "host_turn_boundary",
        }:
            errors.append("run_decision=pause with external_authority requires pause/redirect/decision basis")
        if run_decision == "stop" and external_basis != "explicit_user_stop":
            errors.append("run_decision=stop with external_authority requires external_authority_basis=explicit_user_stop")
        if any(re.search(pattern, pause_reason) for pattern in INFERRED_AUTHORITY_PATTERNS):
            errors.append("external_authority may not be justified by inferred closure phrasing in pause_reason")
        if any(re.search(pattern, stop_evidence) for pattern in INFERRED_AUTHORITY_PATTERNS):
            errors.append("external_authority may not be justified by inferred closure phrasing in stop_authorization_evidence")
        if external_basis == "human_decision_required" and "human_decision_gate=unresolved_after_5_codex" not in stop_evidence:
            errors.append("human_decision_required requires stop_authorization_evidence to record human_decision_gate=unresolved_after_5_codex")
        if external_basis == "host_turn_boundary" and host_resume_mode != "same_turn_only":
            errors.append("external_authority_basis=host_turn_boundary requires host_resume_mode=same_turn_only")
        if external_basis == "explicit_user_pause":
            user_pause_ref = extract_structured_value(stop_evidence, "user_pause_ref")
            if user_pause_ref is None:
                errors.append("explicit_user_pause requires stop_authorization_evidence to record user_pause_ref=<...>")
            elif is_placeholder_reference(user_pause_ref):
                errors.append("explicit_user_pause requires a concrete non-placeholder user_pause_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_pause_ref, run_dir)
                if authority_path is None or not authority_receipt_is_valid(authority_path, "explicit_user_pause"):
                    errors.append("explicit_user_pause requires user_pause_ref to resolve to a valid v1 authority receipt artifact")
        if external_basis == "explicit_user_redirect":
            user_redirect_ref = extract_structured_value(stop_evidence, "user_redirect_ref")
            if user_redirect_ref is None:
                errors.append("explicit_user_redirect requires stop_authorization_evidence to record user_redirect_ref=<...>")
            elif is_placeholder_reference(user_redirect_ref):
                errors.append("explicit_user_redirect requires a concrete non-placeholder user_redirect_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_redirect_ref, run_dir)
                if authority_path is None or not authority_receipt_is_valid(authority_path, "explicit_user_redirect"):
                    errors.append("explicit_user_redirect requires user_redirect_ref to resolve to a valid v1 authority receipt artifact")
        if external_basis == "host_turn_boundary":
            host_boundary_ref = extract_structured_value(stop_evidence, "host_boundary_ref")
            if host_boundary_ref is None:
                errors.append("host_turn_boundary requires stop_authorization_evidence to record host_boundary_ref=<...>")
            elif is_placeholder_reference(host_boundary_ref):
                errors.append("host_turn_boundary requires stop_authorization_evidence to carry a concrete non-placeholder host_boundary_ref value")
            else:
                authority_path = resolve_run_scoped_ref(host_boundary_ref, run_dir)
                if authority_path is None:
                    errors.append("host_turn_boundary requires host_boundary_ref to resolve to an existing in-run authority receipt artifact")
                elif not host_boundary_receipt_is_valid(authority_path, closeout_round_id, continue_attempt_ref):
                    errors.append("host_turn_boundary requires host_boundary_ref to resolve to a valid v1 authority receipt artifact bound to the current closeout_round_id and attempt_ref")
                elif not artifact_is_fresh_for_closeout(
                    authority_path,
                    handoff_path,
                    MAX_HOST_BOUNDARY_RECEIPT_STALENESS_SECONDS,
                ):
                    errors.append("host_turn_boundary requires a fresh host_boundary_ref receipt close to handoff.md; stale boundary proof suggests voluntary_turn_close")
            if not contains_any_pattern(pause_reason, HOST_BOUNDARY_REASON_PATTERNS) or not contains_any_pattern(
                pause_reason, HOST_BOUNDARY_FORCE_PATTERNS
            ):
                errors.append("host_turn_boundary pauses must describe a forced visible turn boundary in pause_reason")
            if contains_any_pattern(pause_reason, NON_HOST_PAUSE_CAUSE_PATTERNS):
                errors.append("host_turn_boundary pauses may not mix in non-host pause causes inside pause_reason")
        if external_basis == "explicit_user_stop":
            user_stop_ref = extract_structured_value(stop_evidence, "user_stop_ref")
            if user_stop_ref is None:
                errors.append("explicit_user_stop requires stop_authorization_evidence to record user_stop_ref=<...>")
            elif is_placeholder_reference(user_stop_ref):
                errors.append("explicit_user_stop requires a concrete non-placeholder user_stop_ref value")
            else:
                authority_path = resolve_run_scoped_ref(user_stop_ref, run_dir)
                if authority_path is None:
                    errors.append("explicit_user_stop requires user_stop_ref to resolve to an existing in-run authority receipt artifact")
                elif not user_stop_receipt_is_valid(authority_path, closeout_round_id):
                    errors.append(
                        "explicit_user_stop requires user_stop_ref to resolve to a valid v1 authority receipt "
                        "artifact bound to the current closeout_round_id and current_user_message source"
                    )
                elif not artifact_is_fresh_for_closeout(
                    authority_path,
                    handoff_path,
                    MAX_USER_STOP_RECEIPT_STALENESS_SECONDS,
                ):
                    errors.append("explicit_user_stop requires a fresh user_stop_ref receipt close to handoff.md")

    if continuation_mode == "nonstop" and run_decision == "pause" and stop_status == "allow":
        if is_noneish(blocking_findings_text):
            errors.append("continuation_mode=nonstop only allows autonomous pause with concrete blocking_findings")
        elif not has_anchor_overlap(blocking_findings_text, next_action):
            errors.append("blocking_findings must stay anchored to the paused next_mandatory_action for a nonstop autonomous pause")
        if not has_anchor_overlap(blocking_findings_text, pause_reason):
            errors.append("continuation_mode=nonstop autonomous pause requires pause_reason to stay anchored to blocking_findings")

    if continuation_mode == "nonstop" and run_decision == "pause" and external_basis == "host_turn_boundary" and goal_completion_status == VERIFIED_COMPLETE_STATUS:
        errors.append("host_turn_boundary pauses in continuation_mode=nonstop may not claim a fully verified completed goal")

    plan_remaining = extract_plan_remaining(run_dir / "revised-plan.md")
    if plan_remaining is not None:
        if run_decision == "continue" and is_noneish(plan_remaining):
            errors.append("revised-plan.md has no remaining required stages but handoff says continue")
        if run_decision == "pause" and is_noneish(plan_remaining):
            errors.append("revised-plan.md has no remaining required stages but handoff says pause")
        if run_decision == "stop" and not is_noneish(plan_remaining) and not explicit_user_stop_override:
            errors.append("revised-plan.md still has remaining required stages but handoff says stop")

    if source_has_sequential_markers(run_dir / "source.md"):
        if sequential_status == "none_detected":
            errors.append("source.md contains sequential markers but sequential_objectives_status=none_detected")
        if run_decision == "stop" and sequential_status != "satisfied" and not explicit_user_stop_override:
            errors.append("source.md contains sequential markers, so stop requires sequential_objectives_status=satisfied")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate agent-loop handoff closeout invariants.")
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--require-consensus",
        action="store_true",
        help="Reject autonomous halt states that lack recorded halt authorization",
    )
    parser.add_argument(
        "--live-state",
        action="store_true",
        help="Validate an in-progress handoff without requiring turn-ending continue evidence",
    )
    parser.add_argument(
        "--resume-state",
        action="store_true",
        help="Validate an already-emitted continue/pause handoff during resume without treating its own closeout receipt as stale replay authority",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"[FAIL] handoff.md not found: {handoff_path}")
        return 1

    if has_flat_legacy_lines(handoff_path):
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print("- mixed-format legacy handoff detected; refresh it with scripts/refresh_legacy_handoffs.py and keep only canonical v2 fields")
        return 1

    duplicate_fields, unknown_fields = inspect_canonical_handoff(handoff_path)
    if duplicate_fields:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print(f"- duplicate canonical handoff fields are illegal: {', '.join(duplicate_fields)}")
        return 1
    if unknown_fields:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        print(f"- unknown canonical handoff fields are illegal: {', '.join(unknown_fields)}")
        return 1

    fields = parse_handoff(handoff_path)
    errors = validate_fields(
        fields,
        run_dir,
        require_consensus=args.require_consensus,
        live_state=args.live_state,
        resume_state=args.resume_state,
    )
    if errors:
        print(f"[FAIL] Handoff validation failed: {run_dir}")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[OK] Handoff validation passed: {run_dir}")
    print(f"run_decision={clean_value(str(fields['run_decision']))}")
    print(f"loop_state={clean_value(str(fields['loop_state']))}")
    print(f"stop_authorization_status={clean_value(str(fields['stop_authorization_status']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
