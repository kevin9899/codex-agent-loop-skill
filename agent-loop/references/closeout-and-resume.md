# Closeout And Resume

Use this reference when updating `handoff.md`, choosing `run_decision`, or
checking whether a loop may legally pause or stop.

For new runs, start from [handoff-template.md](handoff-template.md) instead of
writing `handoff.md` from scratch.

## Nonstop First

- treat implementation-oriented bare `$loop` as nonstop unless the request is explicitly planning-only
- treat the first accepted loop goal as standing authority to continue; do not ask whether to keep going just because one batch finished or a status update was given
- if a later user turn explicitly opens a materially different `$loop` /
  `$agent-loop` goal, treat that as a new visible-answer authority snapshot and
  start a sibling run for it; do not let the older run remain the only live
  authority just because it is near completion
- treat the `$loop` / `$agent-loop` token itself as the delegated-agent grant;
  once the loop is accepted, lack of a second explicit "use agents" sentence is
  not a blocker
- read `$loop` as plain-language permission to "keep going and use agents when
  useful"; if artifacts make delegation look optional or separately gated,
  repair the artifacts rather than pausing the run
- treat `$loop` / `$agent-loop` as standing authority to use delegated
  `spawn_agent` lanes when the tool is available and delegation helps; do not
  insert a separate "open agents?" permission checkpoint
- if another bounded local action is still available, do that action instead of ending the turn
- in `same_turn_only` hosts, keep working until the host forces the visible boundary
- in `same_turn_only` hosts, a visible final reply with `run_decision=continue`
  is a forced-boundary receipt only; it is not semantic stop and does not
  satisfy the halt condition
- after each verified batch, reopen the next remaining gap immediately unless fresh unanimous `5 Codex` halt/completion proof already exists
- if the latest closeout challenge is only missing one or more timed-out lanes
  and a deterministic replacement or shrunken retry can still be launched now,
  launch that replacement now instead of emitting a handoff or pause
- when that boundary arrives with live remaining work, prefer a truthful `continue` receipt with `turn_exit_cause=host_turn_boundary_pause`, fresh `continue_exit_*` proof, and an auto-resume path; use `pause` only if the environment cannot encode safe auto-resume or another real external pause basis exists
- when the latest bounded action was blocked by delegated-agent usage limits,
  quotas, credits, or rate limits, record that as
  `continue_exit_status=blocked_during_attempt`; in same-turn-only hosts the
  visible turn may still end with `turn_exit_cause=host_turn_boundary_pause`
  because the blocker and the visible boundary are separate facts
- delegated-agent quota blockers are not stop authority and are not host-boundary
  pause authority when the auto-resume `continue` shape can be encoded
- in `same_turn_only` hosts, that `continue` receipt must include
  `stop_status=not_stopped`,
  `forced_boundary_note=호스트가 백그라운드 실행을 이어주지 않아 final 채널로 경계 영수증을 남긴 것입니다. 루프는 목표 완료/정지로 처리되지 않았고, 아무 후속 메시지나 보내면 같은 run을 즉시 이어갑니다.`,
  `host_boundary_effect=visible_turn_only_not_goal_stop`,
  `auto_resume_trigger=any_followup_message`,
  `followup_resume_policy=auto_resume_any_followup`, and
  `resume_command=$loop <run-dir>`; this makes a later ordinary user follow-up a
  mandatory auto-resume trigger instead of a permission prompt
- if `continue_exit_status=blocked_during_attempt`, the receipt must also carry
  Korean user-facing blocker fields before `stop_status`:
  `user_visible_status_ko=...`, `blocked_action_ko=...`,
  `needed_condition_ko=...`, and `human_readable_reason=...`. The blocked action
  and needed condition must be concrete; vague text like "확인 필요", "대기", or
  "추후" is invalid
- an external-gate-only state with no bounded local action remaining is not a
  valid auto-resume continue state. If the source completion criteria allow
  local/free work to end once user/external actions are recorded, run the fresh
  completion proof and stop. Otherwise use a truthful external-gate pause
  instead of telling the user any follow-up will keep executing
- when that later follow-up arrives, record the actual resume event before new
  work with
  `python <skill-dir>/scripts/record_resume_event.py <run-dir> --trigger any_followup_message`
  and then continue `next_mandatory_action` immediately; the event is evidence
  that the previous final-channel boundary was a visible host boundary, not a
  goal stop. The recorded `previous_continue_receipt` must match the same
  `closeout_round_id`; if no matching receipt exists yet, record `none` plus an
  explicit alignment status instead of borrowing an older continue receipt
- for that truthful `continue` receipt, keep `stop_authorization_status=not_applicable`, `stop_consensus_status=not_applicable`, and `external_authority_basis=none`; `host_turn_boundary` as an external authority basis is reserved for the fallback pause shape
- do not let `same_turn_only` block a lawful autonomous terminal `stop` when both fresh unanimous `5 Codex` halt proof and fresh unanimous `5 Codex` goal-completion proof already exist for the current authority snapshot
- for authority-aware runs, terminal stop also requires a selected active
  `run_authority_record`, compatible project adapter, current completion
  subject, current challenge cycle, freshness revalidation, and successful CAS
  transition to `completed`
- treat `host_turn_boundary` as legal only when `turn_exit_cause=host_turn_boundary_pause`, `turn_exit_evidence` proves the forced visible boundary, and `continue_exit_*` proves the latest bounded action attempt
- for `run_decision=continue` and `host_turn_boundary` pauses, keep `attempt_ref` fresh relative to the current `handoff.md`; stale attempt receipts are evidence of `voluntary_turn_close`
- for `host_turn_boundary` pauses, require `host_boundary_ref` to resolve to a fresh authority receipt bound to the same `closeout_round_id` and `attempt_ref`
- `handoff.md` is continuation bookkeeping, not permission to stop
- `npm run loop:handoff` output is also continuation bookkeeping. When it reports
  `run_decision=continue` or `completionStopAllowed=false`, it cannot justify a
  free-form final recap; immediately start the next bounded action, dispatch the
  required stop/completion challenge, or record a canonical no-bounded-action
  blocker with tool evidence.
- flat `key: value` handoffs and legacy partial schemas are invalid; refresh them before validating or resuming:

```bash
python <skill-dir>/scripts/refresh_legacy_handoffs.py <run-dir> --write --continue-exit-status <next_action_started|blocked_during_attempt> --continue-exit-evidence "<latest-attempt-proof>" --turn-exit-evidence "<forced-host-boundary-proof>"
```

## Status Versus Closeout

Treat a user status request as live-state reporting, not as permission to pause
or stop.

- prefer live-state lines over completion-style recap
- for user-visible status replies, prefer the canonical live-state gate:

```bash
python <skill-dir>/scripts/emit_status_reply.py <run-dir> [--blocking-or-risk "..."]
```

- keep the answer anchored to `loop_state`, `current_or_next_stage`,
  `next_mandatory_action`, and only the blocker or risk that matters now
- do not mutate `run_decision` just because the user asked "where are we now?"
- do not append `continue?`, `want me to keep going?`, `open agents?`,
  `진행할까요`, `에이전트 열까요`, or similar consent-seeking language; `$loop`
  already authorizes continuation and delegated-agent use where available, with
  the operator token itself acting as the delegation grant
- if the host then forces a visible turn end, record a truthful pause without
  rewriting the goal as complete
- in `same_turn_only` hosts, the boundary is still a real pause; the status
  request does not erase the need for canonical pause bookkeeping
- a status answer that reads like a wrap-up is still a semantic-stop defect
- if the user says the loop stopped after a host-boundary pause, treat that as
  evidence of a pause-shape UX defect first: tighten the receipt/validator and
  continue the run instead of arguing that the pause was already clear
- pure `triage`, `sweep`, `scan`, `candidate` selection, or route-classification
  work is not a legal `next_action_started` turn-end state; keep that search
  inside the turn until it produces a concrete bounded patch, test batch, or
  blocker
- pure local-edit progress is also not a legal turn-end state. If the latest
  batch landed an `apply_patch`-style code edit, the same bounded batch must
  also carry the smallest relevant validation evidence before any visible
  continue/pause receipt can pass

## Mandatory Turn-End Sequence

Before deciding that any visible `final` answer is allowed, re-open the live
`handoff.md`. If `run_decision=continue`, `goal_completion_status` is not
`verified_complete_5lane`, or `remaining_required_stages` is non-empty, a
normal completion summary is forbidden. Keep executing the next bounded
tool-backed action. The only lawful final-channel answer with remaining work is
validated `closeout_gate.py` output for a genuinely forced host boundary.
If `completionStopAllowed=false`, treat "the verified batch is done" as
`pre_final_reassessment_required`, not as a closeout reason. The controller must
choose one allowed transition: start the next bounded action, dispatch the
required challenge, record a canonical no-bounded-action blocker, or emit
validated forced-boundary gate output.
If `loop-final-guard`, `closeout_gate.py`, `validate_continue_reply.py`,
handoff validation, or any explicit completion gate blocks a terminal answer,
the blocked gate result is not a public status update. Treat it as proof that
the controller must continue or repair. A final answer that says the guard
blocked "as expected" and names the remaining stages is a
`blocked_guard_status_final` defect unless it is the exact validated forced
boundary gate output.
If the user reports "stopped" immediately after a valid same-turn-only continue
receipt, classify the next turn as `receipt_only_final_boundary_perceived_stop`.
Record a resume event, preserve the previous receipt/handoff as evidence, and
run a tool-backed controller repair, validator smoke, or recorded next action
before any further turn-ending receipt. Do not answer with a second receipt-only
message while tools are still available.
Also reopen the latest final-audit/completion artifacts. If the latest audit
found gaps against the original prompt in `source.md`, a terminal stop or
normal final summary is illegal even if older artifacts or the current
`revised-plan.md` look complete.

Before any user-visible turn end:

1. Refresh `ideas.md`, `research.md`, `revised-plan.md`, and `handoff.md`.
2. Ensure `handoff.md` is canonical bullet-form. v2 is valid for compatibility
   and nonterminal/explicit-user-stop paths; verified autonomous terminal stops
   use v3 work-type authority fields.
3. Run:

```bash
python <skill-dir>/scripts/validate_handoff.py <run-dir> --require-consensus
```

4. If `host_resume_mode=same_turn_only`, record concrete `turn_exit_cause` and `turn_exit_evidence` first.
5. Emit the turn-ending reply only through:

```bash
python <skill-dir>/scripts/closeout_gate.py <run-dir> [--active-delta "..." --blocking-or-risk "..."]
```

6. Do not add free-form wrap-up prose after the validated gate output.
7. Treat `emit_pause_reply.py`, `emit_continue_reply.py`, and `emit_terminal_reply.py` as gate-only internals; they reject direct invocation.
8. For `run_decision=stop`, the terminal receipt should surface the canonical stop fields plus compact derived `work_process=`, `work_summary=`, `verification_summary=`, and `need_to_know=` lines so the visible stop state includes the process, outcome, validation/proof status, and user-facing caveats without exposing raw proof internals.
9. Keep the terminal stop briefing gate-produced and validator-enforced. Do not append free-form prose after the receipt, and do not add full-work briefing fields to `run_decision=continue` or `run_decision=pause`.

## Root Cause To Avoid

A loop can stop semantically even when no halt was authorized if the artifacts
say some version of:

- `remaining_required_stages: none`
- `next_mandatory_action: none`
- `pause_reason: none - goal satisfied`
- a closure-style final response

That combination is illegal unless a real stop or pause has already been
authorized and recorded.

In nonstop runs, a second root cause is also common:

- artifacts say `continue`, but the turn-ending final response leads with completed-work recap
- the response mentions the next stage only as future work
- the orchestrator did not actually start `next_mandatory_action`

A third root cause is recap dominance:

- the response technically starts with live-state fields
- but removing those lines leaves a standalone completion-style report
- the majority of the message still sounds like a wrap-up rather than an in-flight continuation update

That is also an illegal semantic stop, even if the run artifacts are otherwise valid.

An additional same-turn-only closeout defect is:

- artifacts say `continue`
- `next_mandatory_action` or `active_delta` is still only `triage`, `sweep`,
  `scan`, `candidate` selection, or similar open-ended gap-search language
- the controller still emitted a turn-ending continue receipt

That is also an illegal semantic stop. Keep working until the search produces a
concrete bounded patch, launched validation batch, or real blocker.

An additional same-turn-only receipt defect is:

- artifacts correctly say `continue`
- but the public continue receipt does not contain an explicit human-readable
  `forced_boundary_note=` saying the host merely forced a visible reply and the
  loop did not stop

That is also a loop-control defect because users can reasonably read the turn as
completion even when the machine-readable fields are technically correct.

An additional same-turn-only host UX defect can happen when:

- artifacts correctly say `continue`
- the reply is forced through `final`, so the host does not keep background
  execution alive
- the receipt does not state that any ordinary follow-up auto-resumes the exact
  run

That is not a goal stop, but it is still a loop-control defect. Repair the
continue receipt contract and keep executing the recorded `next_mandatory_action`.
If the receipt already contains the auto-resume fields but the user still
perceives a stop, record a resume event and continue. Treat the perception gap
as a host-boundary UX defect, not as a new permission checkpoint. Tighten the
next receipt so the human-readable note names the final-channel host boundary
and says that the next ordinary message is the same-run auto-resume signal.

An additional receipt-only final-boundary defect is:

- artifacts correctly say `continue`
- the public receipt is syntactically valid and includes auto-resume fields
- the host still ends the visible turn and the user reports that the loop
  stopped
- the controller responds with another explanation or receipt instead of
  recording resume evidence and running a tool-backed repair or next action

That defect label is `receipt_only_final_boundary_perceived_stop`. Repair by
capturing the raw receipt/handoff, running `record_resume_event.py`, tightening
the controller contract or deterministic script, validating the repair, and then
continuing the recorded `next_mandatory_action`.

A fourth root cause is voluntary turn close:

- artifacts still say `continue`
- no host, tool, or user blocker was recorded
- the orchestrator simply chose to end the turn after one useful batch even though another bounded local action was still available

That is also an illegal semantic stop.

A closely related root cause is final-channel recap override:

- `handoff.md` correctly says `run_decision=continue`
- `goal_completion_status` is still `not_reached`
- `remaining_required_stages` still lists work
- the assistant nevertheless emits a normal final answer summarizing completed
  work and naming remaining items as future work

That is an illegal semantic stop even if the artifacts are otherwise valid. The
next follow-up must be treated as auto-resume plus loop-control repair: record
the defect, strengthen the guard, and continue the next bounded action without a
permission checkpoint.

A related blocked-guard status final defect is:

- `loop-final-guard`, `closeout_gate.py`, `validate_continue_reply.py`, handoff
  validation, or an explicit completion gate correctly rejects terminal closeout
- the controller reports that blocked result in a normal final answer
- the answer lists the remaining stages but does not start, dispatch, or record
  the next bounded action

That is still an illegal semantic stop. A blocked completion guard is evidence
to keep the loop moving, not a permission slip to publish a wrap-up/status final.

An additional bounded-batch defect is unverified local edit closeout:

- the latest progress included a local code edit
- the visible receipt or handoff attempted to close the turn before the
  smallest relevant test/lint/type/build proof was attached

That is also an illegal semantic stop. Keep the patch and its first validation
step in the same bounded batch before yielding a same-turn-only reply.

A fifth root cause is unproven continue exit:

- the final response obeys the live-state field shape
- but the artifacts do not prove that `next_mandatory_action` was started or blocked during an attempt
- the turn still ended on a status-only handoff refresh

That is also an illegal semantic stop.

A sixth root cause is timeout without batch shrink:

- the latest evidence or capture attempt timed out
- the next action was still feasible through a smaller deterministic batch
- the orchestrator ended the turn without running the shrunken retry

That is also an illegal semantic stop.

A seventh root cause is consent-seeking detour:

- the response ends by asking whether to continue, resume, open agents, or open
  the next batch
- no real external approval gate was recorded
- the loop transformed standing `$loop` authority into an unnecessary check-in

That is also an illegal semantic stop.

An eighth root cause is report-driven pause:

- the pause reason is framed as reporting progress, status update, or check-in
- the real cause was not a forced host boundary or external authority

That is also an illegal semantic stop.

A ninth root cause is stale closeout proof:

- the latest `attempt_ref` is materially older than the current `handoff.md`
- or `host_boundary_ref` is not bound to the current `closeout_round_id` and latest `attempt_ref`
- the closeout reused stale proof instead of refreshing the current turn-ending state

That is also an illegal semantic stop.

A tenth root cause is forced boundary override misuse:

- `AGENT_LOOP_CONFIRMED_HOST_TURN_END=1` was set manually while another bounded local action was still available
- no hard forced-turn-end reason was recorded in `AGENT_LOOP_FORCED_TURN_END_REASON`
- no concrete `AGENT_LOOP_FORCED_TURN_END_EVIDENCE` was echoed in `turn_exit_evidence`
- for same-turn-only hosts, `host_turn_boundary_pause` is a valid forced-turn-end
  reason only when the evidence names the concrete visible host boundary and the
  loop has already started or blocked on the latest `next_mandatory_action`

That is also an illegal semantic stop. Treat the attempted closeout as a failed gate, repair the `$loop` guard if needed, and continue the recorded `next_mandatory_action`.

An eleventh root cause is cross-goal authority mismatch:

- an older run reached lawful terminal `stop`
- but the user had already opened a materially different newer `$loop` goal in
  the same conversation
- the older run's stop was emitted as the visible answer to the newer goal

That is also an orchestration defect. Preserve the older run as evidence if it
matters, but create or resume a sibling run for the newer goal instead of
defending the old stop.

A twelfth root cause is quota-blocker pause fallback:

- all required delegated lanes were launched with the explicit strongest model
  pin but failed with usage limits, credits, quotas, or rate limits
- the handoff used `run_decision=pause` and
  `external_authority_basis=host_turn_boundary`
- a safe auto-resume `run_decision=continue` shape was available

That is a pause-shape defect. The correct shape keeps
`stop_authorization_status=not_applicable`, records
`continue_exit_status=blocked_during_attempt`, records the quota blocker in
`continue_exit_evidence`, records the visible host boundary separately in
`turn_exit_cause=host_turn_boundary_pause`, and emits an auto-resume continue
receipt.

A thirteenth root cause is partial closeout consensus without replacement:

- the latest closeout challenge reached only partial consensus because one or
  more lanes timed out
- another deterministic replacement or shrunken closeout lane was still
  launchable in the same turn
- the orchestrator ended the turn anyway and encoded the missing lane as
  handoff state instead of continuing execution

That is also an illegal semantic stop. Replace the timed-out lane in the same
turn when tools remain available; only carry it into a continue receipt when a
real host/tool boundary prevented the replacement attempt.

A fourteenth root cause is final audit gap closed as done:

- the latest clean final audit found an unmet original-prompt requirement,
  narrowed-scope plan error, or denying lane
- the controller still emitted `stop`, left `remaining_required_stages` empty,
  or wrote a completion recap
- the gap was not promoted back into `revised-plan.md`, `handoff.md`, and the
  next bounded repair action

That is also an illegal semantic stop. Repair by setting
`run_decision=continue`, `goal_completion_status=not_reached`, recording each
gap under `remaining_required_stages`, and immediately continuing the first
bounded repair/verification action.

## Stop-Like Failure Repair Process

When a user reports that `$loop` stopped but no fresh 5-lane terminal proof or
direct explicit user stop exists:

1. Record the report as a loop-control defect, not as a permission checkpoint.
2. Capture raw evidence: user trigger, latest visible receipt/final text,
   `handoff.md`, `HEAD`, attempt refs, authority receipts, validator output,
   and resume-event path.
3. Assign one canonical defect label from the taxonomy in this file; use
   `receipt_only_final_boundary_perceived_stop` when the receipt was valid but
   still read as a stop to the user.
4. If the user requests N-agent analysis, dispatch N bounded analysis lanes
   when `spawn_agent` is available, while the controller continues local repair
   work on the critical path.
5. Convert the diagnosis into one enforceable invariant: illegal state,
   required evidence, and required next transition.
6. Put fragile enforcement in scripts or validators when possible; keep
   `SKILL.md` to the short invariant and this reference to the detailed
   workflow.
7. Add or run a deterministic smoke for the exact failure mode.
8. Record the patch, validation, residual risk, and next action in the active
   run artifacts.
9. Resume the original `next_mandatory_action`; do not end with a recap unless
   canonical stop proof exists.

## Required Handoff Fields

Keep these fields explicit:

- `handoff_schema_version`: `v2-stop-consensus` or `v3-worktype-authority`
- `work_type`: `implementation`, `research`, `docs`, `planning`, `review`, or `mixed` (`not_classified` is legacy migration only)
- `review_kind`: `not_applicable`, `plan_review`, `artifact_review`, `completion_challenge`, or `audit`
- `authority_record_ref`, `run_authority_status`, `run_authority_revision`, and `run_authority_epoch` for v3 authority runs
- `source_digest`, `stage_graph_digest`, `completion_subject_type`, `completion_subject_ref`, and `completion_subject_digest` for v3 authority runs
- `challenge_cycle_ref`, `challenge_cycle_status`, and `challenge_cycle_digest_set` for v3 challenge aggregation
- `adapter_manifest_ref`, `adapter_conformance_status`, and
  `adapter_effective_config_digest` for project adapter compatibility
- `research_cycle_ref`, `research_cycle_status`, and
  `research_cycle_digest_set` for the initial five-lane research gate
- `visible_output_contract`: `live_status`, `challenge_result`, `forced_boundary_continue`, `blocked_external_gate`, `terminal_completion`, or `not_applicable`
- `continuation_mode`: `default` or `nonstop`
- `host_resume_mode`: `same_turn_only` or `durable_runtime`
- `run_decision`: `planning_complete`, `continue`, `pause`, or `stop`
- `sequential_objectives_status`: `none_detected`, `open`, or `satisfied`
- `stop_authorization_status`: `not_applicable`, `not_run`, `deny`, `allow`, or `external_authority`
- `stop_authorization_evidence`: path or short evidence note
- `stop_consensus_status`: `not_applicable`, `not_run`, `deny`, `allow_unanimous`, or `waived_external_authority`
- `stop_consensus_evidence`: explicit unanimous-vote proof or external-authority waiver note
- `external_authority_basis`: `none`, `explicit_user_pause`, `explicit_user_stop`, `explicit_user_redirect`, `human_decision_required`, or `host_turn_boundary`
- `goal_completion_status`: `not_reached`, `completion_candidate`, or `verified_complete_5lane`
- `goal_completion_evidence`: explicit goal-state evidence, including fresh `5 Codex` completion proof for terminal goal-satisfied stops
- `closeout_round_id`: current turn-ending freshness anchor that binds attempt proof and closeout proof to this exact closeout event
- `turn_exit_cause`: `not_applicable`, `context_budget_exhausted`, `tool_timeout_after_batch_shrink`, `blocked_during_attempt`, `host_turn_boundary_pause`, or `user_interrupt`
- `turn_exit_evidence`: concrete reason the turn-ending continue reply or host-boundary pause was unavoidable

## Validator Workflow

1. Update `ideas.md`, `research.md`, `revised-plan.md`, and `handoff.md`.
2. Run:

```bash
python <skill-dir>/scripts/validate_handoff.py <run-dir> --require-consensus
```

3. If validation fails, repair the artifacts and default to `continue`.
4. Only after a passing validation may the loop emit an autonomous pause or stop.

Treat `run_decision=continue` the same way: if `continue_exit_*` is stale, placeholder, or absent, repair the handoff before trusting it as a legal turn-close state.
Treat `closeout_round_id` the same way: if it is missing or not echoed by the current attempt/proof artifacts, the closeout is stale by definition.
Treat `subject_digest` as the digest of live authority state, not the proof text itself. The validator hashes `source.md`, `ideas.md`, `research.md`, `revised-plan.md`, `evidence.md`, and `handoff.md` with self-referential proof evidence fields redacted so `subject_digest` can bind proof to the current authority snapshot without requiring a cryptographic fixed point.
Treat `turn_exit_*` the same way for a turn-ending `continue` reply: a boundary with no explicit cause/evidence is `voluntary_turn_close` by default.
For a live in-progress handoff that is not a turn-close state, use `validate_handoff.py <run-dir> --require-consensus --live-state`. Do not invent `host_turn_boundary_pause` or other turn-exit evidence just to validate a live handoff while tool work remains available.
When resuming from a previously emitted same-turn continue or pause receipt, use `validate_handoff.py <run-dir> --require-consensus --resume-state` before mutating the handoff. This permits the already-emitted `closeout_round_id` to appear in closeout receipts while still requiring a fresh `closeout_round_id` before the next turn-ending reply.
If `host_resume_mode=same_turn_only`, trust turn-ending `continue` only when `continue_exit_*` proves the latest action was started or blocked and `turn_exit_cause=host_turn_boundary_pause` records the forced visible boundary. Otherwise classify the turn end as a pause-shape or voluntary-close defect.
If a user reports that the loop stopped and no valid 5-lane halt proof exists, treat the report as evidence that the host should be classified `same_turn_only` unless durable background execution is directly proven.
If `external_authority_basis=host_turn_boundary`, classify the immediate cause as `host_turn_boundary_pause` before looking for a semantic-stop defect. That condition is a host capability ceiling, not by itself proof that the loop yielded too early.
If `external_authority_basis=host_turn_boundary` but `turn_exit_cause=not_applicable` or `turn_exit_evidence` is empty, reclassify it as an unproven semantic-stop defect instead of a host ceiling.
Do not describe a `same_turn_only` host as "won't stop" in user-facing metadata. The truthful promise in that host is same-turn continuation plus resumable pause state.
If validation fails because the handoff is legacy or mixed-format, refresh it first, then re-run validation before making any closeout decision.

Autonomous halt proof is low-freedom:

- `stop_authorization_status=allow` is legal only with:
  - `stop_consensus_status=allow_unanimous`
  - `stop_consensus_evidence=allow_count=5 deny_count=0 ambiguous_count=0 missing_count=0 challenge_round_id=<fresh-round> closeout_round_id=<current-closeout-round> agent_role=challenge_agent challenge_review_mode=autonomous_stop_challenge subject_digest=<current-authority-digest> source_ref=source.md source_digest=<sha256(raw source.md bytes)> context_mode=clean_source_first authority_basis=source_md_original_user_prompt source_requirements_reconstructed=yes claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied route_context=final_halt_completion loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof policy_ref_digests=sha256:<skill-digest>|sha256:<template-digest> policy_coverage_verdict=route_required_refs_loaded viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality coverage_viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality model_policy=gpt_5_5_high_minimum_explicit top_model_lane_min=5 resolved_model_slug=gpt-5.5 resolved_reasoning_effort=xhigh spawn_model_binding=explicit_tool_args refs=<...>`
- `goal_completion_status=verified_complete_5lane` is legal only with:
  - `handoff_schema_version=v3-worktype-authority` for autonomous terminal stop.
  - `goal_completion_evidence=allow_count=5 deny_count=0 ambiguous_count=0 missing_count=0 challenge_round_id=<fresh-round> closeout_round_id=<current-closeout-round> agent_role=challenge_agent challenge_review_mode=goal_completion_challenge subject_digest=<current-authority-digest> source_ref=source.md source_digest=<sha256(raw source.md bytes)> context_mode=clean_source_first authority_basis=source_md_original_user_prompt source_requirements_reconstructed=yes claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied route_context=final_halt_completion loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof policy_ref_digests=sha256:<skill-digest>|sha256:<template-digest> policy_coverage_verdict=route_required_refs_loaded viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality coverage_viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality model_policy=gpt_5_5_high_minimum_explicit top_model_lane_min=5 resolved_model_slug=gpt-5.5 resolved_reasoning_effort=xhigh spawn_model_binding=explicit_tool_args refs=<...>`
- for v3 authority runs, both stop and goal-completion evidence must also bind
  to `authority_record_ref`, `authority_revision`, `authority_epoch`,
  `source_digest`, `adapter_manifest_ref`, `adapter_effective_config_digest`,
  `completion_subject_type`, `completion_subject_digest`, `stage_graph_digest`,
  `challenge_cycle_ref`, and `challenge_cycle_digest_set`. The terminal reply
  is invalid if any of those fields changed after the accepted challenge cycle.
- the five referenced Codex lane artifacts must cover the required final lane
  set exactly once: one fresh agent for each of `architecture_dependency`,
  `failure_verification`, `goal_efficiency`, `requirement_alignment`, and
  `implementation_quality`. A duplicate lane, missing lane, uncovered viewpoint,
  or generic challenge prompt is not five-lane proof.
- all five lanes must be final challenge agents. Each lane artifact and its
  dispatch receipt must carry `agent_role=challenge_agent` plus
  `challenge_review_mode=autonomous_stop_challenge` for
  `phase=stop_authorization` or
  `challenge_review_mode=goal_completion_challenge` for
  `phase=goal_completion`; any worker, explorer, summarizer, or generic
  reviewer lane is inadmissible.
- each referenced halt-lane artifact must exist and carry:
  - `phase=stop_authorization`
  - `agent_role=challenge_agent`
  - `challenge_review_mode=autonomous_stop_challenge`
  - `vote=allow`
  - `viewpoint=<required-final-lane>`
  - `coverage_viewpoints=<same required final lane>`
  - `challenge_round_id=<same fresh-round>`
  - `subject_digest=<same current-authority-digest>`
  - `source_ref=source.md`
  - `source_digest=<sha256(raw source.md bytes)>`
  - `context_mode=clean_source_first`
  - `authority_basis=source_md_original_user_prompt`
  - `source_requirements_reconstructed=yes`
  - `claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff`
  - `repo_inspection=fresh`
  - `audit_gap_count=0`
  - `scope_verdict=original_request_satisfied`
  - `route_context=final_halt_completion`
  - `loaded_policy_refs=AGENTS.md#LoopCompletionGate|SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof` when a bound repo root contains `AGENTS.md`; otherwise omit both the `AGENTS.md#LoopCompletionGate` token and `<agents-digest>`
  - `policy_ref_digests=sha256:<agents-digest>|sha256:<skill-digest>|sha256:<template-digest>` when `AGENTS.md#LoopCompletionGate` is required; otherwise `policy_ref_digests=sha256:<skill-digest>|sha256:<template-digest>`
  - `policy_coverage_verdict=route_required_refs_loaded`
  - `model_policy=gpt_5_5_high_minimum_explicit`
  - `resolved_model_slug=<lane-model-gpt-5.5-or-stronger>`
  - `resolved_reasoning_effort=<lane-effort>`
  - `model_resolution_basis_ref=<catalog-or-skill-ref>`
  - `spawn_model_binding=explicit_tool_args`
  - `spawn_tool_args_model=<same-lane-model>`
  - `spawn_tool_args_reasoning_effort=<same-lane-effort>`
  - `spawn_tool_call_ref=<dispatch receipt>`
  - `freshness_status=fresh|current_pass|current_cycle`
  - `agent_id=<unique>`
- across the five lane artifacts, exactly three of the five lanes must carry
  `resolved_model_slug=gpt-5.5` and `resolved_reasoning_effort=xhigh`, two
  lanes must carry `resolved_model_slug=gpt-5.5` and
  `resolved_reasoning_effort=high`
- no lane artifact or dispatch receipt may use `resolved_reasoning_effort=low`
  or `resolved_reasoning_effort=medium`
- each referenced goal-completion lane artifact must carry the same
  source-first fields plus
  `challenge_review_mode=goal_completion_challenge` and
  `source_alignment_verdict=all_source_requirements_satisfied`
- each `spawn_tool_call_ref` must resolve to a v1 in-run dispatch receipt bound
  to the same phase, agent id, viewpoint, challenge round, closeout round,
  `source_digest`, `agent_role=challenge_agent`, the phase-specific
  `challenge_review_mode`, explicit model args, route metadata
  (`route_context`, `loaded_policy_refs`, `policy_ref_digests`,
  `policy_coverage_verdict`), `context_mode=clean_source_first`, and
  `full_history_fork=false`
- each `refs=` path must resolve inside the current run directory; absolute or escaped paths to unrelated artifacts are illegal
- any missing, ambiguous, failed, or denying required Codex halt lane means default to `continue`
- `subject_digest` is freshness binding over the live run snapshot; it is not
  original-scope authority. `source_digest` and the source-first lane fields are
  the authority binding to the original user prompt.
- `stop_authorization_status=external_authority` is not agent consensus; pair it with:
  - `stop_consensus_status=waived_external_authority`
  - `stop_consensus_evidence=<explicit waiver basis>`
- treat that waiver as non-autonomous by default:
  - it can justify `pause`
  - it cannot justify `stop` except for a direct explicit user stop override
- `host_turn_boundary` is a pause waiver, never autonomous stop proof

Claude CLI usage limits are not a legal stop reason. Skip Claude lanes, record the
degradation in `stop_authorization_evidence` or `research.md`, and continue with
the required Codex halt lanes.

`external_authority` is narrow. It applies when a human explicitly pauses,
stops, redirects the work, when a real human decision is still required, or
when a `same_turn_only` host forces a truthful `host_turn_boundary` pause. It
does not apply just because one bounded subgoal was completed.

In the default local file-backed profile, direct current-turn
`explicit_user_stop` is the only supported human stop override. Record it with
`scripts/record_user_stop_receipt.py <run-dir> --excerpt "<direct stop>"` and
cite `user_stop_ref=<receipt>` in `stop_authorization_evidence`.
`explicit_user_pause`, `explicit_user_redirect`, and `human_decision_required`
remain unsupported unless the host can provide immutable authority outside the
mutable run directory.

If `external_authority_basis=human_decision_required`, record
`human_decision_gate=unresolved_after_3_codex` in `stop_authorization_evidence`.

## Decision Matrix

- `continue`
  - use when the next stage is explicit, a blocker does not require human authority, halt validation fails, or the clean final audit finds any original-prompt gap
- `pause`
  - use when the next mandatory action is explicit, a concrete reason exists, and authorization is either:
    - `allow` plus unanimous 5-lane halt proof
    - `external_authority` plus an explicit waiver basis
  - keep `goal_completion_status=not_reached` unless implementation looks done but the fresh completion challenge still has not run, in which case use `completion_candidate`
- `stop`
  - use only when the original prompt in `source.md` is saturated, not merely the latest narrowed plan, and authorization is either:
    - `allow` plus fresh unanimous `5 Codex` halt proof and fresh unanimous `5 Codex` goal-completion proof
    - `external_authority` only for a direct explicit user stop with `external_authority_basis=explicit_user_stop`
  - do not use when a newer materially different `$loop` goal is now the
    visible-answer authority for the conversation; fork or resume the newer run
    first
  - `host_resume_mode=same_turn_only` does not forbid this autonomous stop path; it only forbids pretending unfinished work can continue across a visible turn boundary

Fresh challenge lanes should judge the synchronized current run state. They may
cite missing current evidence or contradictory handoff state as blockers, but
they should not deny solely because the same round's canonical proof artifacts
have not yet been synthesized. Those artifacts are normally written after the
lane outputs return. They also should not deny solely because the same round's
lane verdict set is not already present in the run directory; that verdict set
is being generated by the live challenge itself.
- `planning_complete`
  - use only for explicit planning-only requests that redirect the run into a planning deliverable close
  - treat it as a scoped external-authority close, not as autonomous halt
  - never use it to terminate implementation-oriented or nonstop runs

## Invalid Patterns

- `run_decision=continue` with `current_or_next_stage: none`
- `run_decision=continue` with `next_mandatory_action: none`
- any pause or stop state that omits `goal_completion_status` or `goal_completion_evidence`
- `run_decision=stop` without `goal_completion_status=verified_complete_5lane` unless the basis is a direct explicit user stop
- `run_decision=planning_complete` without `run_intent=planning_only`
- `run_decision=planning_complete` in a nonstop run
- `run_decision=planning_complete` without a scoped external-authority record
- implementation-oriented bare `$loop` run left at `continuation_mode=default` without a recorded reason
- `run_decision=continue` with a turn-ending final response that leads with completed-work recap
- `run_decision=continue` where `next_mandatory_action` was explicit and feasible but no attempt was made before the turn ended
- `run_decision=continue` where the turn ended by choice even though another bounded local action was still available
- `run_decision=continue` at a turn boundary with `continue_exit_status=not_applicable`
- `run_decision=continue` at a turn boundary without concrete `continue_exit_evidence`
- `run_decision=continue` without `continue_exit_evidence` carrying `attempt_ref=<...>` and `closeout_round_id=<current-closeout-round>`
- `run_decision=continue` with stale `attempt_ref` proof that is no longer fresh relative to the current `handoff.md`
- `run_decision=continue` with stale `continue_exit_*` copied from an older action instead of the latest attempted next action
- `run_decision=continue` at a turn boundary with `turn_exit_cause=not_applicable`
- `run_decision=continue` at a turn boundary without concrete `turn_exit_evidence`
- `host_resume_mode=same_turn_only` `run_decision=continue` without `turn_exit_evidence` carrying `host_boundary_ref=<authority-receipt-path>` bound to the current `closeout_round_id` and latest `attempt_ref`
- `run_decision=continue` with inspection-only `continue_exit_evidence` for `continue_exit_status=next_action_started`
- `external_authority_basis=host_turn_boundary` without concrete `continue_exit_evidence`
- `external_authority_basis=host_turn_boundary` without `continue_exit_evidence` carrying `attempt_ref=<...>` and `closeout_round_id=<current-closeout-round>`
- `external_authority_basis=host_turn_boundary` without `continue_exit_status=next_action_started|blocked_during_attempt`
- `external_authority_basis=host_turn_boundary` with `turn_exit_cause` other than `host_turn_boundary_pause`
- any status or progress reply that asks whether to continue when no real external approval gate exists
- any host-boundary pause justified as reporting, check-in, or optional user handoff instead of a forced visible boundary
- `host_resume_mode=same_turn_only` with a turn-ending `run_decision=continue` that lacks fresh `continue_exit_*` proof, `turn_exit_cause=host_turn_boundary_pause`, or an auto-resume path
- `host_resume_mode=same_turn_only` with a free-form pause final instead of the validated pause-receipt line shape
- `run_decision=pause|stop` with `stop_authorization_status=not_run`
- `run_decision=pause|stop` with `stop_authorization_status=allow` but without `stop_consensus_status=allow_unanimous`
- `run_decision=pause|stop` with `stop_consensus_status=allow_unanimous` but without `allow_count=5 deny_count=0 ambiguous_count=0 missing_count=0` proof
- `stop_consensus_status=allow_unanimous` or `goal_completion_status=verified_complete_5lane` without `agent_role=challenge_agent` and the matching phase-specific `challenge_review_mode` in aggregate evidence, every lane artifact, and every dispatch receipt
- `stop_consensus_status=allow_unanimous` without source-first clean audit tokens: `source_ref=source.md`, matching `source_digest`, `context_mode=clean_source_first`, `audit_gap_count=0`, and `scope_verdict=original_request_satisfied`
- `goal_completion_status=verified_complete_5lane` without source-first clean audit tokens or without lane artifacts carrying `source_alignment_verdict=all_source_requirements_satisfied`
- any final audit proof that treats `ideas.md`, `research.md`, `revised-plan.md`, `evidence.md`, or `handoff.md` as the scope authority instead of untrusted implementation claims checked against `source.md`
- `run_decision=pause|stop` with `stop_authorization_status=external_authority` but without `stop_consensus_status=waived_external_authority`
- `stop_authorization_status=external_authority` with `external_authority_basis=none`
- `stop_authorization_status=external_authority` justified only by "bounded objective complete", "goal satisfied", or similar inferred closure
- `external_authority_basis=human_decision_required` without `human_decision_gate=unresolved_after_3_codex`
- `external_authority_basis=explicit_user_pause` without `user_pause_ref=<...>`
- `external_authority_basis=explicit_user_redirect` without `user_redirect_ref=<...>`
- `external_authority_basis=host_turn_boundary` without `host_boundary_ref=<authority-receipt-path>`
- `external_authority_basis=host_turn_boundary` with `host_boundary_ref` that is not bound to the current `closeout_round_id` and latest `attempt_ref`
- `external_authority_basis=host_turn_boundary` with stale `host_boundary_ref` proof that is no longer fresh relative to the current `handoff.md`
- `external_authority_basis=host_turn_boundary` with `turn_exit_cause=not_applicable`
- `external_authority_basis=host_turn_boundary` without concrete `turn_exit_evidence`
- nonstop turn-ending `continue` or `host_turn_boundary` pause accepted only because `AGENT_LOOP_CONFIRMED_HOST_TURN_END=1` was set, without a valid `AGENT_LOOP_FORCED_TURN_END_REASON` such as `host_turn_boundary_pause` and echoed `AGENT_LOOP_FORCED_TURN_END_EVIDENCE`
- any mixed-format handoff that still contains legacy flat `key: value` lines alongside bullet-form v2 fields
- `run_decision=stop` while `sequential_objectives_status=open`
- source text contains sequential markers but `sequential_objectives_status=none_detected`
- claiming Claude halt consensus when Claude CLI lanes were actually skipped for usage limits
- a final response sounds complete while `run_decision=continue`

## Nonstop Delivery Check

When `continuation_mode=nonstop` and `run_decision=continue`:

1. Treat `final` as a delivery fallback only. If another concrete local action is still available, keep working instead of choosing a turn boundary.
2. Start `next_mandatory_action` before the turn ends unless a real blocker appeared during the attempt.
3. If a final response is unavoidable, put these first:
   - `loop_state=...`
   - `run_decision=continue`
   - `semantic_state=incomplete_forced_boundary`
   - `continuation_authority=standing`
   - `current_or_next_stage=...`
   - `next_mandatory_action=...`
   - `goal_completion_status=...`
   - `turn_exit_cause=...`
   - `turn_exit_evidence=...`
4. Before sending that reply, persist turn-exit proof in `handoff.md`:
   - `continue_exit_status=next_action_started` or `blocked_during_attempt`
   - `continue_exit_evidence=<started command, file edit, launched batch, produced artifact, or blocker note>`
   - `continue_exit_status=not_applicable` is illegal once the turn-ending `continue` reply is about to be sent
   - `turn_exit_cause=<context_budget_exhausted|tool_timeout_after_batch_shrink|blocked_during_attempt|host_turn_boundary_pause|user_interrupt>`
   - `turn_exit_evidence=<what boundary forced the continue reply>`
   - if `host_resume_mode=same_turn_only`, first record a fresh authority
     receipt with
     `python <skill-dir>/scripts/record_host_boundary_receipt.py <run-dir> --evidence "<forced visible boundary proof>"`
     and include `host_boundary_ref=<that-receipt>` inside `turn_exit_evidence`
   - for delegated-agent usage limits, keep `turn_exit_cause` as the visible
     host boundary in same-turn-only hosts; put the quota blocker in
     `continue_exit_evidence` and `blocking_or_risk`
5. After those lines, use only:
   - `active_delta=...`
   - `user_visible_status_ko=...` for `blocked_during_attempt`
   - `blocked_action_ko=...` for `blocked_during_attempt`
   - `needed_condition_ko=...` for `blocked_during_attempt`
   - `human_readable_reason=...` for `blocked_during_attempt`
   - `stop_status=not_stopped`
   - `host_boundary_effect=visible_turn_only_not_goal_stop` for `same_turn_only`
   - `auto_resume_trigger=any_followup_message` for `same_turn_only`
   - `followup_resume_policy=auto_resume_any_followup` for `same_turn_only`
   - `resume_command=$loop <run-dir>` for `same_turn_only`
   - optional `blocking_or_risk=...`
6. Do not add headings, bullets, or free-form recap lines after the live-state fields.
7. Apply the `delete-the-preamble` test:
   - if deleting the live-state field lines leaves a response that still reads like a completion summary, it is a semantic-stop defect
8. Avoid closure-scent phrasing while `run_decision=continue`, including `완료`, `마무리`, `정리`, `끝`, `done`, `completed`, `finished`, `queued`, `resume`, `next loop`, `if needed`, `can take`, `could`, `awaiting`, and similar wrap-up or handoff language.
9. Generate the reply mechanically:

```bash
python <skill-dir>/scripts/closeout_gate.py <run-dir> --active-delta "..." [--blocking-or-risk "..."] [--blocked-action-ko "..."] [--needed-condition-ko "..."]
```

10. Validate the draft or generated reply with:

```bash
python <skill-dir>/scripts/validate_continue_reply.py <reply.txt> --run-dir <run-dir>
```

   - stdin is also allowed
   - `--run-dir` is mandatory for real turn-ending continue replies
   - a failed reply check is not a blocker; repair the handoff or compress the reply and retry
11. Use one defect label when the user says the loop stopped:
   - `voluntary_turn_close`
   - `next_action_not_attempted`
   - `recap_dominant_final`
   - `completion_scent_phrasing`
   - `artifact_pause_shape`
   - `continue_exit_unproven`
   - `timeout_without_batch_shrink`
   - `forced_boundary_override_misuse`
12. If the user says the loop stopped, treat that as defect evidence, record the root cause, tighten the skill or closeout contract, and continue the run.
13. If the latest blocker was a timeout and a smaller deterministic batch is available, run that shrunken retry before any turn-ending `continue` reply.
14. Do not ask the user whether to continue or resume; the initial `$loop` goal already provides that authority until a real stop basis exists.

## Same-Turn-Only Hosts

When `host_resume_mode=same_turn_only` and live remaining work still exists:

1. Treat any user-visible `final` as a real pause boundary, not as an in-flight continuation surface.
2. Diagnose the cause honestly:
   - `host_turn_boundary_pause` if the loop worked until the forced visible boundary
   - semantic-stop defect only if the orchestrator yielded early, implied completion, or skipped an available next action
2. For live `continue`, persist:
   - `run_decision=continue`
   - `loop_state=<ideation|research|planning|execution|verify|reassessment_pending>`
   - `continue_exit_status=next_action_started|blocked_during_attempt`
   - `continue_exit_evidence=<fresh attempt_ref and closeout_round_id>`
   - `turn_exit_cause=host_turn_boundary_pause`
   - `turn_exit_evidence=<forced visible host boundary>`
3. For fallback `pause`, persist a truthful pause state instead:
   - `run_decision=pause`
   - `loop_state=paused`
   - `stop_authorization_status=external_authority`
   - `stop_consensus_status=waived_external_authority`
   - `external_authority_basis=host_turn_boundary` for host-forced exits, or keep the stronger real pause basis when the user explicitly paused, redirected, or a human decision gate is what actually stopped the run
   - `goal_completion_status=not_reached|completion_candidate`
   - concrete `pause_reason`
   - live `next_mandatory_action`
4. Keep `continue_exit_status=next_action_started|blocked_during_attempt` when `external_authority_basis=host_turn_boundary`; host-boundary pauses still need last-attempt proof.
5. Require concrete forced-boundary proof in the handoff:
   - `turn_exit_cause=host_turn_boundary_pause`
   - `turn_exit_evidence=<what forced the visible boundary now>`
   - `continue_exit_status=<next_action_started|blocked_during_attempt>`
   - `continue_exit_evidence=<what latest bounded action was already attempting>`
   - `turn_exit_cause=not_applicable` is illegal for `external_authority_basis=host_turn_boundary`
6. Keep `resume_instructions` explicit so the next `$loop` call can restart cleanly from disk.
7. Treat the turn-ending pause reply as low-freedom:
   - the reply must contain only these non-empty lines, in this order:
     - `loop_state=paused`
     - `host_resume_mode=...`
     - `pause_scope=...`
     - `continuation_authority=...`
     - `semantic_state=...`
     - `followup_resume_policy=...`
     - `current_or_next_stage=...`
     - `next_mandatory_action=...`
     - `goal_completion_status=...`
     - `turn_exit_cause=...`
     - `turn_exit_evidence=...`
     - `pause_reason=...`
     - `external_authority_basis=...`
     - `resume_command=$loop <run-dir>`
     - `resume_instructions=...`
   - generate it mechanically:

```bash
python <skill-dir>/scripts/closeout_gate.py <run-dir>
```

   - validate the draft or generated reply with:

```bash
python <skill-dir>/scripts/validate_pause_reply.py <reply.txt> --run-dir <run-dir>
```

   - stdin is also allowed
   - a failed pause-reply check is not a blocker; repair `handoff.md`, compress the receipt back to the fixed line shape, and retry
   - treat `resume_command` as the same-turn workaround surface: the next user
     turn can paste that exact `$loop <run-dir>` command to resume from the
     stored run artifacts instead of rebuilding context manually
   - for `external_authority_basis=host_turn_boundary`, require
     `pause_scope=host_boundary_only` and
     `continuation_authority=standing` so the receipt says explicitly that only
     the host boundary paused the run and the original continuation authority is
     still live
   - for `external_authority_basis=host_turn_boundary`, require
     `followup_resume_policy=auto_resume_any_followup` so the next ordinary
     user message resumes the stored run even when they do not paste the
     explicit `resume_command`
8. Validate the handoff itself before rendering the pause receipt; pause-reply shape alone is not enough.
9. In `same_turn_only` hosts, `continuation_mode=nonstop` still means "keep working until a visible turn boundary is forced". Once an unfinished turn must end, the truthful result should be a live continue receipt when safe, otherwise a pause receipt. If the goal is already fully proven complete, use the lawful terminal `stop` path instead of a fake pause.
10. Make the pause semantics explicit in the rendered receipt:
    - `semantic_state=incomplete_forced_boundary` for `host_turn_boundary`
    - `semantic_state=incomplete_paused_by_authority` for explicit user pause or redirect
    - `semantic_state=incomplete_blocked_pending_human` for unresolved human-decision gates
    - do not let a pause receipt omit the incomplete-state marker
11. Make the follow-up contract explicit in the rendered receipt:
    - `followup_resume_policy=auto_resume_any_followup` for `host_turn_boundary`
    - `followup_resume_policy=explicit_resume_required` for explicit user pause or stop
    - `followup_resume_policy=redirected_by_user` for explicit user redirect
    - `followup_resume_policy=await_human_decision` for unresolved human-decision gates
    - do not leave the user guessing whether the next ordinary message resumes the stored run

## Legacy Run Migration

Older run folders may not contain the new closeout fields. Treat them as legacy
runs, not as valid proof that a stop was legal. Refresh the artifacts before
resuming or before trusting the old closeout state.
