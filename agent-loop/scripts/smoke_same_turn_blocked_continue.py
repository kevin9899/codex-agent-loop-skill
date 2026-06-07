#!/usr/bin/env python3
from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    import closeout_gate
    import validate_handoff as validator

    real_quota_fields = {
        "stage_status": "delegated dispatch blocked by quota",
        "blocking_findings": "delegated quota blocked challenge dispatch",
    }
    if not validator.telemetry_required_for_fields(real_quota_fields):
        print("[FAIL] real delegated quota blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    plural_usage_limit_fields = {
        "blocking_findings": "spawn_agent blocked by usage limits",
    }
    if not validator.telemetry_required_for_fields(plural_usage_limit_fields):
        print("[FAIL] plural usage limits blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*plural_usage_limit_fields.values()):
        print("[FAIL] plural usage limits blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    quota_limit_reached_fields = {
        "blocking_findings": "spawn_agent delegated lanes failed: quota limit reached during challenge dispatch",
    }
    if not validator.telemetry_required_for_fields(quota_limit_reached_fields):
        print("[FAIL] quota limit reached blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*quota_limit_reached_fields.values()):
        print("[FAIL] quota limit reached blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    split_quota_limit_reached_fields = {
        "blocking_findings": "spawn_agent dispatch failed: quota limit reached",
    }
    if not validator.telemetry_required_for_fields(split_quota_limit_reached_fields):
        print("[FAIL] split quota limit reached blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*split_quota_limit_reached_fields.values()):
        print("[FAIL] split quota limit reached blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    reverse_split_quota_limit_reached_fields = {
        "blocking_findings": "quota limit reached: spawn_agent dispatch failed",
    }
    if not validator.telemetry_required_for_fields(reverse_split_quota_limit_reached_fields):
        print("[FAIL] reverse split quota limit reached blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*reverse_split_quota_limit_reached_fields.values()):
        print("[FAIL] reverse split quota limit reached blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    quota_exhausted_fields = {
        "blocking_findings": "spawn_agent quota exhausted during challenge dispatch",
    }
    if not validator.telemetry_required_for_fields(quota_exhausted_fields):
        print("[FAIL] quota exhausted blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*quota_exhausted_fields.values()):
        print("[FAIL] quota exhausted blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    credits_exhausted_fields = {
        "blocking_findings": "spawn_agent dispatch failed: credits exhausted",
    }
    if not validator.telemetry_required_for_fields(credits_exhausted_fields):
        print("[FAIL] credits exhausted blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*credits_exhausted_fields.values()):
        print("[FAIL] credits exhausted blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    negated_usage_limit_fields = {
        "blocking_findings": "spawn_agent was not blocked by usage limits",
    }
    if validator.telemetry_required_for_fields(negated_usage_limit_fields):
        print("[FAIL] negated usage limits blocker unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*negated_usage_limit_fields.values()):
        print("[FAIL] negated usage limits blocker was counted as delegated quota blocker", file=sys.stderr)
        return 1
    usage_limits_ruled_out_fields = {
        "blocking_findings": "spawn_agent usage limits were ruled out",
    }
    if validator.telemetry_required_for_fields(usage_limits_ruled_out_fields):
        print("[FAIL] usage limits ruled out unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*usage_limits_ruled_out_fields.values()):
        print("[FAIL] usage limits ruled out counted as delegated quota blocker", file=sys.stderr)
        return 1
    quota_limits_ruled_out_fields = {
        "blocking_findings": "spawn_agent quota limits were ruled out",
    }
    if validator.telemetry_required_for_fields(quota_limits_ruled_out_fields):
        print("[FAIL] quota limits ruled out unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*quota_limits_ruled_out_fields.values()):
        print("[FAIL] quota limits ruled out counted as delegated quota blocker", file=sys.stderr)
        return 1
    no_usage_limits_fields = {
        "blocking_findings": "no usage limits blocked spawn_agent dispatch",
    }
    if validator.telemetry_required_for_fields(no_usage_limits_fields):
        print("[FAIL] no usage limits wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*no_usage_limits_fields.values()):
        print("[FAIL] no usage limits wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    quota_limit_not_reached_fields = {
        "blocking_findings": "spawn_agent quota limit was not reached during challenge dispatch",
    }
    if validator.telemetry_required_for_fields(quota_limit_not_reached_fields):
        print("[FAIL] quota limit not reached unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*quota_limit_not_reached_fields.values()):
        print("[FAIL] quota limit not reached counted as delegated quota blocker", file=sys.stderr)
        return 1
    usage_limits_not_reached_fields = {
        "blocking_findings": "delegated dispatch usage limits were not reached",
    }
    if validator.telemetry_required_for_fields(usage_limits_not_reached_fields):
        print("[FAIL] usage limits not reached unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*usage_limits_not_reached_fields.values()):
        print("[FAIL] usage limits not reached counted as delegated quota blocker", file=sys.stderr)
        return 1
    terse_quota_limit_not_reached_fields = {
        "blocking_findings": "spawn_agent quota limit not reached during challenge dispatch",
    }
    if validator.telemetry_required_for_fields(terse_quota_limit_not_reached_fields):
        print("[FAIL] terse quota limit not reached unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*terse_quota_limit_not_reached_fields.values()):
        print("[FAIL] terse quota limit not reached counted as delegated quota blocker", file=sys.stderr)
        return 1
    terse_usage_limit_not_reached_fields = {
        "blocking_findings": "dispatch usage limit not reached",
    }
    if validator.telemetry_required_for_fields(terse_usage_limit_not_reached_fields):
        print("[FAIL] terse usage limit not reached unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*terse_usage_limit_not_reached_fields.values()):
        print("[FAIL] terse usage limit not reached counted as delegated quota blocker", file=sys.stderr)
        return 1
    contracted_usage_limit_not_reached_fields = {
        "blocking_findings": "dispatch usage limits weren't reached",
    }
    if validator.telemetry_required_for_fields(contracted_usage_limit_not_reached_fields):
        print("[FAIL] contracted usage limits not reached unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*contracted_usage_limit_not_reached_fields.values()):
        print("[FAIL] contracted usage limits not reached counted as delegated quota blocker", file=sys.stderr)
        return 1
    has_not_quota_limit_reached_fields = {
        "blocking_findings": "spawn_agent dispatch failed: quota limit has not been reached",
    }
    if validator.telemetry_required_for_fields(has_not_quota_limit_reached_fields):
        print("[FAIL] has-not quota limit reached wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*has_not_quota_limit_reached_fields.values()):
        print("[FAIL] has-not quota limit reached wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    havent_usage_limits_reached_fields = {
        "blocking_findings": "dispatch usage limits haven't been reached",
    }
    if validator.telemetry_required_for_fields(havent_usage_limits_reached_fields):
        print("[FAIL] haven't usage limits reached wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*havent_usage_limits_reached_fields.values()):
        print("[FAIL] haven't usage limits reached wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    korean_negated_quota_fields = {
        "blocking_findings": "에이전트 쿼터 아님",
    }
    if validator.telemetry_required_for_fields(korean_negated_quota_fields):
        print("[FAIL] Korean negated quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*korean_negated_quota_fields.values()):
        print("[FAIL] Korean negated quota wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    docs_rate_limits_fields = {
        "latest_evidence_summary": "docs updated to explain rate limits",
    }
    if validator.telemetry_required_for_fields(docs_rate_limits_fields):
        print("[FAIL] docs rate limits wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    docs_spawn_agent_quota_fields = {
        "latest_evidence_summary": "docs updated to explain spawn_agent quota limit reached",
    }
    if validator.telemetry_required_for_fields(docs_spawn_agent_quota_fields):
        print("[FAIL] docs spawn_agent quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*docs_spawn_agent_quota_fields.values()):
        print("[FAIL] docs spawn_agent quota wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    docs_prefix_quota_fields = {
        "latest_evidence_summary": "docs: spawn_agent quota limit reached",
    }
    if validator.telemetry_required_for_fields(docs_prefix_quota_fields):
        print("[FAIL] docs prefix quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*docs_prefix_quota_fields.values()):
        print("[FAIL] docs prefix quota wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    docs_semicolon_then_real_quota_fields = {
        "latest_evidence_summary": "docs; delegated dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(docs_semicolon_then_real_quota_fields):
        print("[FAIL] docs semicolon masked later real delegated quota blocker", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*docs_semicolon_then_real_quota_fields.values()):
        print("[FAIL] docs semicolon masked later delegated quota blocker classification", file=sys.stderr)
        return 1
    docs_newline_then_real_quota_fields = {
        "latest_evidence_summary": "docs\ndelegated dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(docs_newline_then_real_quota_fields):
        print("[FAIL] docs newline masked later real delegated quota blocker", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*docs_newline_then_real_quota_fields.values()):
        print("[FAIL] docs newline masked later delegated quota blocker classification", file=sys.stderr)
        return 1
    docs_prefix_then_real_quota_fields = {
        "latest_evidence_summary": "docs: spawn_agent quota limit reached; delegated dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(docs_prefix_then_real_quota_fields):
        print("[FAIL] docs prefix masked later real delegated quota blocker", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*docs_prefix_then_real_quota_fields.values()):
        print("[FAIL] docs prefix masked later delegated quota blocker classification", file=sys.stderr)
        return 1
    test_coverage_tool_limit_fields = {
        "latest_evidence_summary": "smoke coverage for tool-limit parsing passed",
    }
    if validator.telemetry_required_for_fields(test_coverage_tool_limit_fields):
        print("[FAIL] smoke coverage tool-limit wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    test_coverage_resource_busy_fields = {
        "latest_evidence_summary": "test coverage for resource-busy parsing passed",
    }
    if validator.telemetry_required_for_fields(test_coverage_resource_busy_fields):
        print("[FAIL] test coverage resource-busy wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    try_again_review_fields = {
        "blocking_findings": "agent will try again after review",
    }
    if validator.is_delegated_quota_blocker(*try_again_review_fields.values()):
        print("[FAIL] benign try-again wording counted as delegated quota blocker", file=sys.stderr)
        return 1
    negated_quota_fields = {
        "blocking_findings": "delegated challenge was not blocked by quota",
    }
    if validator.telemetry_required_for_fields(negated_quota_fields):
        print("[FAIL] negated delegated quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*negated_quota_fields.values()):
        print("[FAIL] negated delegated quota wording unexpectedly counted as delegated quota blocker", file=sys.stderr)
        return 1
    negated_contraction_fields = {
        "blocking_findings": "delegated challenge wasn't blocked by quota",
    }
    if validator.telemetry_required_for_fields(negated_contraction_fields):
        print("[FAIL] contracted negated quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    negated_quota_limit_fields = {
        "blocking_findings": "delegated dispatch without quota limit",
    }
    if validator.telemetry_required_for_fields(negated_quota_limit_fields):
        print("[FAIL] without quota limit wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    storybook_quota_copy_fields = {
        "latest_evidence_summary": "Storybook delegated quota-limit error state copy only",
    }
    if validator.telemetry_required_for_fields(storybook_quota_copy_fields):
        print("[FAIL] Storybook quota-limit copy unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    storybook_dispatch_copy_fields = {
        "latest_evidence_summary": "Storybook UI error copy renders: dispatch blocked by quota.",
    }
    if validator.telemetry_required_for_fields(storybook_dispatch_copy_fields):
        print("[FAIL] Storybook dispatch quota copy unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*storybook_dispatch_copy_fields.values()):
        print("[FAIL] Storybook dispatch quota copy unexpectedly counted as delegated quota blocker", file=sys.stderr)
        return 1
    storybook_semicolon_dispatch_copy_fields = {
        "latest_evidence_summary": "Storybook UI error copy renders; dispatch blocked by quota.",
    }
    if validator.telemetry_required_for_fields(storybook_semicolon_dispatch_copy_fields):
        print("[FAIL] Storybook semicolon dispatch quota copy unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*storybook_semicolon_dispatch_copy_fields.values()):
        print("[FAIL] Storybook semicolon dispatch quota copy unexpectedly counted as delegated quota blocker", file=sys.stderr)
        return 1
    korean_ui_copy_fields = {
        "latest_evidence_summary": "한국어 UI 오류 상태가 '에이전트 사용량 한도' 문구를 표시함",
    }
    if validator.telemetry_required_for_fields(korean_ui_copy_fields):
        print("[FAIL] Korean UI usage-limit copy unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    if validator.is_delegated_quota_blocker(*korean_ui_copy_fields.values()):
        print("[FAIL] Korean UI usage-limit copy unexpectedly counted as delegated quota blocker", file=sys.stderr)
        return 1
    not_actually_blocked_fields = {
        "blocking_findings": "delegated dispatch was not actually blocked by quota",
    }
    if validator.telemetry_required_for_fields(not_actually_blocked_fields):
        print("[FAIL] not actually blocked by quota wording unexpectedly required resource telemetry", file=sys.stderr)
        return 1
    mixed_ui_and_real_quota_fields = {
        "latest_evidence_summary": "UI displays quota/tool blocked copy only; delegated dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(mixed_ui_and_real_quota_fields):
        print("[FAIL] mixed UI copy plus real delegated quota blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    mixed_comma_ui_and_real_quota_fields = {
        "latest_evidence_summary": "UI displays quota/tool blocked copy only, delegated dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(mixed_comma_ui_and_real_quota_fields):
        print("[FAIL] comma UI copy plus real delegated quota blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*mixed_comma_ui_and_real_quota_fields.values()):
        print("[FAIL] comma real dispatch quota blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    mixed_list_ui_and_real_quota_fields = {
        "latest_evidence_summary": ["UI displays quota/tool blocked copy only", "delegated dispatch blocked by quota"],
    }
    if not validator.telemetry_required_for_fields(mixed_list_ui_and_real_quota_fields):
        print("[FAIL] list UI copy plus real delegated quota blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*mixed_list_ui_and_real_quota_fields.values()):
        print("[FAIL] list real dispatch quota blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    ambiguous_list_ui_and_real_quota_fields = {
        "blocking_findings": ["UI displays quota/tool blocked copy only", "dispatch blocked by quota"],
    }
    if not validator.telemetry_required_for_fields(ambiguous_list_ui_and_real_quota_fields):
        print("[FAIL] list UI copy plus ambiguous real quota blocker unexpectedly skipped resource telemetry", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*ambiguous_list_ui_and_real_quota_fields.values()):
        print("[FAIL] list ambiguous real quota blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    negated_then_real_quota_fields = {
        "blocking_findings": "delegated challenge wasn't blocked by quota, dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(negated_then_real_quota_fields):
        print("[FAIL] negated quota clause masked later real dispatch quota blocker", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*negated_then_real_quota_fields.values()):
        print("[FAIL] later real dispatch quota blocker was not counted as delegated quota blocker", file=sys.stderr)
        return 1
    negated_and_real_quota_fields = {
        "blocking_findings": "delegated challenge wasn't blocked by quota and dispatch blocked by quota",
    }
    if not validator.telemetry_required_for_fields(negated_and_real_quota_fields):
        print("[FAIL] negated quota clause masked later real dispatch quota blocker joined with and", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*negated_and_real_quota_fields.values()):
        print("[FAIL] later real dispatch quota blocker joined with and was not counted", file=sys.stderr)
        return 1
    negated_then_plural_usage_limit_fields = {
        "blocking_findings": "delegated challenge wasn't blocked by quota; dispatch blocked by usage limits",
    }
    if not validator.telemetry_required_for_fields(negated_then_plural_usage_limit_fields):
        print("[FAIL] negated quota clause masked later plural usage limits blocker", file=sys.stderr)
        return 1
    if not validator.is_delegated_quota_blocker(*negated_then_plural_usage_limit_fields.values()):
        print("[FAIL] later plural usage limits blocker was not counted", file=sys.stderr)
        return 1
    negated_then_tool_limit_fields = {
        "continue_exit_evidence": (
            "provider was not rate-limited; spawn_agent delegated lanes blocked by tool-limit during challenge dispatch"
        ),
    }
    if not validator.telemetry_required_for_fields(negated_then_tool_limit_fields):
        print("[FAIL] negated rate-limit clause masked later real tool-limit blocker", file=sys.stderr)
        return 1
    negated_colon_tool_limit_fields = {
        "continue_exit_evidence": (
            "provider was not rate-limited: spawn_agent delegated lanes blocked by tool-limit during challenge dispatch"
        ),
    }
    if not validator.telemetry_required_for_fields(negated_colon_tool_limit_fields):
        print("[FAIL] colon-separated negated rate-limit clause masked later real tool-limit blocker", file=sys.stderr)
        return 1
    negated_then_resource_busy_fields = {
        "continue_exit_evidence": (
            "provider was not rate-limited; spawn_agent delegated lanes blocked by resource-busy during challenge dispatch"
        ),
    }
    if not validator.telemetry_required_for_fields(negated_then_resource_busy_fields):
        print("[FAIL] negated rate-limit clause masked later real resource-busy blocker", file=sys.stderr)
        return 1
    negated_colon_resource_busy_fields = {
        "continue_exit_evidence": (
            "provider was not rate-limited: spawn_agent delegated lanes blocked by resource-busy during challenge dispatch"
        ),
    }
    if not validator.telemetry_required_for_fields(negated_colon_resource_busy_fields):
        print("[FAIL] colon-separated negated rate-limit clause masked later real resource-busy blocker", file=sys.stderr)
        return 1
    dispatch_ui_branch_fields = {
        "continue_exit_evidence": "dispatch blocked by quota while reviewing UI branch",
    }
    if not validator.telemetry_required_for_fields(dispatch_ui_branch_fields):
        print("[FAIL] dispatch quota blocker with incidental UI branch wording skipped resource telemetry", file=sys.stderr)
        return 1
    ui_quota_copy_fields = {
        "latest_evidence_summary": "UI displays quota/tool blocked copy only",
    }
    if validator.telemetry_required_for_fields(ui_quota_copy_fields):
        print("[FAIL] UI quota/tool blocked copy unexpectedly required resource telemetry", file=sys.stderr)
        return 1

    closeout_pause_base = {
        "run_decision": "pause",
        "continuation_mode": "nonstop",
        "external_authority_basis": "host_turn_boundary",
        "continue_exit_status": "blocked_during_attempt",
    }
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="delegated challenge was not blocked by quota")
    ):
        print("[FAIL] closeout gate treated negated delegated quota wording as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="spawn_agent was not blocked by usage limits")
    ):
        print("[FAIL] closeout gate treated negated usage limits wording as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="에이전트 쿼터 아님")
    ):
        print("[FAIL] closeout gate treated Korean negated quota wording as pause blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="delegated challenge wasn't blocked by quota, dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed later real dispatch quota blocker after negated clause", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="delegated challenge wasn't blocked by quota and dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed later real dispatch quota blocker joined with and", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="delegated challenge was not blocked by quota: dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed colon-separated later real dispatch quota blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="spawn_agent blocked by usage limits")
    ):
        print("[FAIL] closeout gate missed plural usage limits blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(
            closeout_pause_base,
            pause_reason="Storybook UI error copy renders",
            blocking_findings="delegated dispatch blocked by quota",
        )
    ):
        print("[FAIL] closeout gate let pause_reason UI copy mask blocking_findings quota blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(
            closeout_pause_base,
            pause_reason="Storybook UI error copy renders",
            blocking_findings="spawn_agent blocked by usage limits",
        )
    ):
        print("[FAIL] closeout gate let pause_reason UI copy mask blocking_findings usage limit blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(
            closeout_pause_base,
            blocking_findings=["UI displays quota/tool blocked copy only", "delegated dispatch blocked by quota"],
        )
    ):
        print("[FAIL] closeout gate missed list real dispatch quota blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(
            closeout_pause_base,
            blocking_findings=["UI displays quota/tool blocked copy only", "dispatch blocked by quota"],
        )
    ):
        print("[FAIL] closeout gate missed list ambiguous real quota blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="Storybook UI error copy renders: dispatch blocked by quota.")
    ):
        print("[FAIL] closeout gate treated Storybook dispatch quota copy as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="Storybook UI error copy renders; dispatch blocked by quota.")
    ):
        print("[FAIL] closeout gate treated Storybook semicolon dispatch quota copy as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="한국어 UI 오류 상태가 '에이전트 사용량 한도' 문구를 표시함")
    ):
        print("[FAIL] closeout gate treated Korean UI usage-limit copy as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="docs updated to explain spawn_agent quota limit reached")
    ):
        print("[FAIL] closeout gate treated docs spawn_agent quota wording as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="docs: spawn_agent quota limit reached")
    ):
        print("[FAIL] closeout gate treated docs prefix quota wording as pause blocker", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="docs: spawn_agent quota limit reached; delegated dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed real blocker after docs prefix quota wording", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="docs; delegated dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed real blocker after docs semicolon wording", file=sys.stderr)
        return 1
    if not closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="docs\ndelegated dispatch blocked by quota")
    ):
        print("[FAIL] closeout gate missed real blocker after docs newline wording", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="한국어 문구: 에이전트 사용량 한도")
    ):
        print("[FAIL] closeout gate treated Korean copy prefix usage-limit wording as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="Korean copy: 에이전트 사용량 한도")
    ):
        print("[FAIL] closeout gate treated Korean copy label usage-limit wording as pause blocker", file=sys.stderr)
        return 1
    if closeout_gate.delegated_quota_pause_error(
        dict(closeout_pause_base, blocking_findings="agent will try again after review")
    ):
        print("[FAIL] closeout gate treated benign try-again wording as pause blocker", file=sys.stderr)
        return 1

    closeout_round_id = "closeout-smoke-same-turn-blocked-continue"
    next_action = "Run 5-lane gpt-5.5/high-minimum challenge dispatch"
    turn_exit_evidence = (
        "same_turn_only host visible turn boundary forced after delegated quota blocked the latest action"
    )

    with tempfile.TemporaryDirectory(prefix="agent-loop-smoke-") as tmp:
        run_dir = Path(tmp)
        write(run_dir / "source.md", "# Source\n\nSmoke blocked continue.\n")
        write(
            run_dir / "ideas.md",
            "\n".join(
                [
                    "# Ideas",
                    "",
                    "## Ideation Gate",
                    "",
                    "- `ideation_status`: `not_material`",
                    "- `lane_count`: `0`",
                    "- `cap`: `timebox_minutes=1 candidate_limit=1 external_source_limit=1`",
                    "- `skip_or_reopen_reason`: `ideation_not_material`",
                    "",
                    "ideation_not_material: smoke fixture deterministic blocked-continue validation.",
                    "",
                ]
            ),
        )
        write(run_dir / "research.md", "# Research\n\nSmoke fixture.\n")
        write(
            run_dir / "revised-plan.md",
            "# Revised Plan\n\n## Remaining Required Stages\n\n- Stage smoke blocked continue\n",
        )
        write(run_dir / "evidence.md", "# Evidence\n\nSmoke fixture.\n")
        write(
            run_dir / "telemetry" / "resource-events.jsonl",
            json.dumps(
                {
                    "telemetry_schema_version": "resource-telemetry-v1",
                    "event_id": "smoke-quota-limit",
                    "observed_at": "2026-05-26T00:00:00Z",
                    "event_type": "usage_limit",
                    "affected_action": "5-lane challenge dispatch",
                    "resource": "spawn_agent",
                    "decision_impact": "continue receipt emitted because required delegated lanes could not be dispatched",
                    "next_action": next_action,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
        )
        write(
            run_dir / "receipts" / "blocked-attempt.md",
            "\n".join(
                [
                    "attempt_receipt_version=v1",
                    f"closeout_round_id={closeout_round_id}",
                    "attempt_status=blocked_during_attempt",
                    f"next_action={next_action}",
                    "summary=spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch",
                    "command_ref=spawn_agent model=gpt-5.5 reasoning_effort=xhigh plus two model=gpt-5.5 reasoning_effort=high lanes",
                    "",
                ]
            ),
        )
        write(
            run_dir / "authority" / "host-turn-boundary.md",
            "\n".join(
                [
                    "# Authority Receipt",
                    "authority_receipt_version=v1",
                    "authority_kind=host_turn_boundary",
                    "event_id=smoke-host-boundary",
                    "event_id_source=controller_generated_same_turn_boundary",
                    f"closeout_round_id={closeout_round_id}",
                    "attempt_ref=receipts/blocked-attempt.md",
                    f"excerpt={turn_exit_evidence}",
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
                    "- `working_goal`: `smoke same-turn blocked continue`",
                    "- `run_intent`: `implementation_loop`",
                    "- `host_resume_mode`: `same_turn_only`",
                    "- `capability_mode`: `delegated_agents_authorized_by_loop_tool_available_smoke`",
                    "- `current_or_next_stage`: `Stage smoke blocked continue`",
                    "- `stage_status`: `delegated dispatch blocked by quota; auto-resume continue should validate`",
                    "- `current_batch`: `same-turn-blocked-continue-smoke`",
                    "- `risk_tier`: `tier1_local`",
                    "- `implementation_gate_status`: `not_applicable`",
                    "- `implementation_gate_evidence`: `smoke fixture validates continue closeout UX contract only`",
                    "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
                    "- `remaining_required_stages`:",
                    "  - `Stage smoke blocked continue`",
                    "- `latest_evidence_summary`:",
                    "  - `spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit`",
                    "- `blocking_findings`:",
                    "  - `delegated quota blocked challenge dispatch`",
                    "- `residual_risks`:",
                    "  - none",
                    "- `goal_completion_status`: `not_reached`",
                    "- `goal_completion_evidence`: `fresh 5-lane completion challenge not available`",
                    "- `loop_state`: `reassessment_pending`",
                    "- `continuation_mode`: `nonstop`",
                    f"- `closeout_round_id`: `{closeout_round_id}`",
                    "- `run_decision`: `continue`",
                    "- `sequential_objectives_status`: `open`",
                    "- `stop_authorization_status`: `not_applicable`",
                    "- `stop_authorization_evidence`: `none`",
                    "- `stop_consensus_status`: `not_applicable`",
                    "- `stop_consensus_evidence`: `fresh 5-lane completion challenge pending`",
                    "- `external_authority_basis`: `none`",
                    "- `pause_reason`: `none`",
                    f"- `next_mandatory_action`: `{next_action}`",
                    "- `continue_exit_status`: `blocked_during_attempt`",
                    f"- `continue_exit_evidence`: `spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch; scheduling_impact=quota; attempt_ref=receipts/blocked-attempt.md; closeout_round_id={closeout_round_id}`",
                    "- `turn_exit_cause`: `host_turn_boundary_pause`",
                    f"- `turn_exit_evidence`: `{turn_exit_evidence}; host_boundary_ref=authority/host-turn-boundary.md`",
                    "- `resume_instructions`:",
                    f"  - `$loop {run_dir}`",
                    f"  - `{next_action}`",
                    "",
                ]
            ),
        )

        validate = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if validate.returncode != 0:
            sys.stderr.write(validate.stdout)
            sys.stderr.write(validate.stderr)
            return validate.returncode

        handoff_path = run_dir / "handoff.md"
        original_handoff = handoff_path.read_text(encoding="utf-8")
        handoff_path.write_text(
            original_handoff.replace(
                "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
                "- `resource_telemetry_ref`: `none`",
            ),
            encoding="utf-8",
        )
        missing_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if missing_telemetry.returncode == 0:
            print("[FAIL] quota-blocked continue without resource telemetry unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        for marker in ("tool-limit", "tool limit", "quota/tool blocked", "resource-busy", "rate-limited"):
            marker_handoff = original_handoff.replace(
                "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch",
                f"spawn_agent delegated lanes blocked by {marker} during challenge dispatch",
            ).replace(
                "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
                "- `resource_telemetry_ref`: `none`",
            )
            handoff_path.write_text(marker_handoff, encoding="utf-8")
            marker_result = subprocess.run(
                [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
                text=True,
                capture_output=True,
            )
            if marker_result.returncode == 0:
                print(f"[FAIL] {marker} continue without telemetry unexpectedly passed", file=sys.stderr)
                return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        negated_handoff = original_handoff.replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit",
            "provider was not rate-limited and resource-busy was ruled out",
        ).replace(
            "delegated dispatch blocked by quota; auto-resume continue should validate",
            "provider was not rate-limited; continue normally",
        ).replace(
            "delegated quota blocked challenge dispatch",
            "resource-busy was ruled out before normal continuation",
        ).replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch; scheduling_impact=quota;",
            "provider was not rate-limited; resource-busy was ruled out;",
        ).replace(
            "same_turn_only host visible turn boundary forced after delegated quota blocked the latest action",
            "same_turn_only host visible turn boundary forced after provider was not rate-limited and resource-busy was ruled out",
        ).replace(
            "scheduling_impact=quota;",
            "scheduling_impact=none;",
        ).replace(
            "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
            "- `resource_telemetry_ref`: `none`",
        )
        handoff_path.write_text(negated_handoff, encoding="utf-8")
        negated_result = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if negated_result.returncode != 0:
            print("[FAIL] negated resource telemetry wording unexpectedly required telemetry", file=sys.stderr)
            print(negated_result.stdout, file=sys.stderr)
            print(negated_result.stderr, file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        mixed_explicit_handoff = original_handoff.replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch",
            "provider was not rate-limited; scheduling_impact=quota; delegated dispatch blocked by quota",
        ).replace(
            "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
            "- `resource_telemetry_ref`: `none`",
        )
        handoff_path.write_text(mixed_explicit_handoff, encoding="utf-8")
        mixed_explicit_result = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if mixed_explicit_result.returncode == 0:
            print("[FAIL] explicit scheduling impact with negated wording unexpectedly skipped telemetry", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        mocked_ui_handoff = original_handoff.replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit",
            "mocked rate-limited UI error state passed",
        ).replace(
            "delegated dispatch blocked by quota; auto-resume continue should validate",
            "mocked rate-limited error state passed",
        ).replace(
            "delegated quota blocked challenge dispatch",
            "local UI mocked rate-limited copy verified",
        ).replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch; scheduling_impact=quota;",
            "mocked rate-limited UI error state passed;",
        ).replace(
            "same_turn_only host visible turn boundary forced after delegated quota blocked the latest action",
            "same_turn_only host visible turn boundary forced after local UI mocked rate-limited copy verification",
        ).replace(
            "scheduling_impact=quota;",
            "scheduling_impact=none;",
        ).replace(
            "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
            "- `resource_telemetry_ref`: `none`",
        )
        handoff_path.write_text(mocked_ui_handoff, encoding="utf-8")
        mocked_ui_result = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if mocked_ui_result.returncode != 0:
            print("[FAIL] mocked rate-limited UI copy unexpectedly required telemetry", file=sys.stderr)
            print(mocked_ui_result.stdout, file=sys.stderr)
            print(mocked_ui_result.stderr, file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        ui_quota_copy_handoff = original_handoff.replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit",
            "UI displays quota/tool blocked copy only",
        ).replace(
            "delegated dispatch blocked by quota; auto-resume continue should validate",
            "UI displays quota/tool blocked copy only",
        ).replace(
            "delegated quota blocked challenge dispatch",
            "local UI quota/tool blocked copy verified",
        ).replace(
            "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit during challenge dispatch; scheduling_impact=quota;",
            "UI displays quota/tool blocked copy only;",
        ).replace(
            "same_turn_only host visible turn boundary forced after delegated quota blocked the latest action",
            "same_turn_only host visible turn boundary forced after local UI quota/tool blocked copy verification",
        ).replace(
            "scheduling_impact=quota;",
            "scheduling_impact=none;",
        ).replace(
            "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
            "- `resource_telemetry_ref`: `none`",
        )
        handoff_path.write_text(ui_quota_copy_handoff, encoding="utf-8")
        ui_quota_copy_result = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if ui_quota_copy_result.returncode != 0:
            print("[FAIL] UI quota/tool blocked copy unexpectedly required telemetry", file=sys.stderr)
            print(ui_quota_copy_result.stdout, file=sys.stderr)
            print(ui_quota_copy_result.stderr, file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        write(run_dir / "telemetry" / "alternate-events.jsonl", (run_dir / "telemetry" / "resource-events.jsonl").read_text(encoding="utf-8"))
        handoff_path.write_text(
            original_handoff.replace(
                "- `resource_telemetry_ref`: `run://telemetry/resource-events.jsonl`",
                "- `resource_telemetry_ref`: `run://telemetry/alternate-events.jsonl`",
            ),
            encoding="utf-8",
        )
        noncanonical_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if noncanonical_telemetry.returncode == 0:
            print("[FAIL] noncanonical resource telemetry ref unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        original_telemetry = (run_dir / "telemetry" / "resource-events.jsonl").read_text(encoding="utf-8")
        write(
            run_dir / "telemetry" / "resource-events.jsonl",
            '{"telemetry_schema_version":"resource-telemetry-v1","event_id":"dup","observed_at":"2026-05-26T00:00:00Z","event_type":"usage_limit","event_type":"rate_limit","affected_action":"dispatch","decision_impact":"retry later","next_action":"retry"}\n',
        )
        duplicate_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if duplicate_telemetry.returncode == 0:
            print("[FAIL] duplicate-key resource telemetry unexpectedly passed", file=sys.stderr)
            return 1
        write(run_dir / "telemetry" / "resource-events.jsonl", original_telemetry)

        write(
            run_dir / "telemetry" / "resource-events.jsonl",
            '{"telemetry_schema_version":"resource-telemetry-v1","event_id":"nan","observed_at":"2026-05-26T00:00:00Z","event_type":NaN,"affected_action":"dispatch","decision_impact":"retry later","next_action":"retry"}\n',
        )
        non_rfc_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if non_rfc_telemetry.returncode == 0:
            print("[FAIL] non-RFC NaN resource telemetry unexpectedly passed", file=sys.stderr)
            return 1
        write(run_dir / "telemetry" / "resource-events.jsonl", original_telemetry)

        write(
            run_dir / "telemetry" / "resource-events.jsonl",
            '{"telemetry_schema_version":"resource-telemetry-v1","event_id":"overflow","observed_at":"2026-05-26T00:00:00Z","event_type":"usage_limit","affected_action":"dispatch","decision_impact":1e999,"next_action":"retry"}\n',
        )
        overflow_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if overflow_telemetry.returncode == 0:
            print("[FAIL] non-finite overflow resource telemetry unexpectedly passed", file=sys.stderr)
            return 1
        write(run_dir / "telemetry" / "resource-events.jsonl", original_telemetry)

        write(
            run_dir / "telemetry" / "resource-events.jsonl",
            '{"telemetry_schema_version":"resource-telemetry-v1","event_id":"nested","observed_at":"2026-05-26T00:00:00Z","event_type":"usage_limit","affected_action":"dispatch","decision_impact":{"nested":"not flat"},"next_action":"retry"}\n',
        )
        nested_telemetry = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if nested_telemetry.returncode == 0:
            print("[FAIL] nested-object resource telemetry unexpectedly passed", file=sys.stderr)
            return 1
        write(run_dir / "telemetry" / "resource-events.jsonl", original_telemetry)

        handoff_path.write_text(
            original_handoff.replace("attempt_ref=receipts/blocked-attempt.md", "not_attempt_ref=receipts/blocked-attempt.md"),
            encoding="utf-8",
        )
        prefixed_attempt = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if prefixed_attempt.returncode == 0:
            print("[FAIL] prefixed not_attempt_ref unexpectedly satisfied attempt_ref", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace("host_boundary_ref=authority/host-turn-boundary.md", "not_host_boundary_ref=authority/host-turn-boundary.md"),
            encoding="utf-8",
        )
        prefixed_host_boundary = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if prefixed_host_boundary.returncode == 0:
            print("[FAIL] prefixed not_host_boundary_ref unexpectedly satisfied host_boundary_ref", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace(
                "attempt_ref=receipts/blocked-attempt.md; closeout_round_id=",
                "attempt_ref=receipts/blocked-attempt.md; attempt_ref=receipts/other.md; closeout_round_id=",
            ),
            encoding="utf-8",
        )
        duplicate_attempt_ref = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if duplicate_attempt_ref.returncode == 0:
            print("[FAIL] duplicate attempt_ref unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace(
                "attempt_ref=receipts/blocked-attempt.md; closeout_round_id=",
                "attempt_ref=receipts/blocked-attempt.md attempt_ref=receipts/other.md; closeout_round_id=",
            ),
            encoding="utf-8",
        )
        duplicate_attempt_ref_space = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if duplicate_attempt_ref_space.returncode == 0:
            print("[FAIL] space-duplicate attempt_ref unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace(
                "host_boundary_ref=authority/host-turn-boundary.md",
                "host_boundary_ref=authority/host-turn-boundary.md; host_boundary_ref=authority/other.md",
            ),
            encoding="utf-8",
        )
        duplicate_host_boundary_ref = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if duplicate_host_boundary_ref.returncode == 0:
            print("[FAIL] duplicate host_boundary_ref unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        handoff_path.write_text(
            original_handoff.replace(
                "host_boundary_ref=authority/host-turn-boundary.md",
                "host_boundary_ref=authority/host-turn-boundary.md, host_boundary_ref=authority/other.md",
            ),
            encoding="utf-8",
        )
        duplicate_host_boundary_ref_comma = subprocess.run(
            [sys.executable, str(scripts_dir / "validate_handoff.py"), str(run_dir), "--require-consensus"],
            text=True,
            capture_output=True,
        )
        if duplicate_host_boundary_ref_comma.returncode == 0:
            print("[FAIL] comma-duplicate host_boundary_ref unexpectedly passed", file=sys.stderr)
            return 1
        handoff_path.write_text(original_handoff, encoding="utf-8")

        env = os.environ.copy()
        env["AGENT_LOOP_CONFIRMED_HOST_TURN_END"] = "1"
        env["AGENT_LOOP_FORCED_TURN_END_REASON"] = "host_turn_boundary_pause"
        env["AGENT_LOOP_FORCED_TURN_END_EVIDENCE"] = turn_exit_evidence
        gate = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "closeout_gate.py"),
                str(run_dir),
                "--active-delta",
                "dispatching 5-lane gpt-5.5/high-minimum challenge lanes",
                "--blocking-or-risk",
                "spawn_agent delegated gpt-5.5/high-minimum lanes blocked by usage limit",
                "--blocked-action-ko",
                "차단된 작업: gpt-5.5/high 이상 5개 챌린지 lane dispatch입니다.",
                "--needed-condition-ko",
                "필요 조건: delegated agent 사용량 제한이 풀려야 합니다.",
            ],
            text=True,
            capture_output=True,
            env=env,
        )
        if gate.returncode != 0:
            sys.stderr.write(gate.stdout)
            sys.stderr.write(gate.stderr)
            return gate.returncode

        required_reply_tokens = [
            "run_decision=continue",
            "semantic_state=incomplete_forced_boundary",
            "continuation_authority=standing",
            "user_visible_status_ko=멈춘 것이 아닙니다. final 채널에 남긴 강제 턴 경계 영수증이며, 아무 후속 메시지나 보내면 같은 run을 자동 재개합니다.",
            "blocked_action_ko=차단된 작업: gpt-5.5/high 이상 5개 챌린지 lane dispatch입니다.",
            "needed_condition_ko=필요 조건: delegated agent 사용량 제한이 풀려야 합니다.",
            "human_readable_reason=필요 조건: delegated agent 사용량 제한이 풀려야 합니다.",
            "user_visible_note=사용자 표시용: 멈춘 게 아니라 호스트가 보이는 답변만 한 번 끊은 상태입니다.",
            "final_copy_policy=copy_closeout_gate_stdout_verbatim_no_summary_no_omission",
            "forced_boundary_note=호스트가 백그라운드 실행을 이어주지 않아 final 채널로 경계 영수증을 남긴 것입니다.",
            "turn_exit_cause=host_turn_boundary_pause",
            "followup_resume_policy=auto_resume_any_followup",
            "resume_command=$loop",
            "blocking_or_risk=",
        ]
        missing = [token for token in required_reply_tokens if token not in gate.stdout]
        if missing:
            print(f"[FAIL] closeout reply missing tokens: {missing}", file=sys.stderr)
            print(gate.stdout, file=sys.stderr)
            return 1

    print("[OK] same-turn blocked continue smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
