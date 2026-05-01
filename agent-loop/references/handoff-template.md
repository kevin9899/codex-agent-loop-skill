# Handoff Template

Use this as the starting shape for new `handoff.md` files.

Use only this bullet-form shape. Do not mix it with flat `key: value` lines. If a run already has a legacy flat handoff or missing v2 closeout fields, refresh it first:

```bash
python <agent-loop-skill-dir>/scripts/refresh_legacy_handoffs.py <run-dir> --write --continue-exit-status <next_action_started|blocked_during_attempt> --continue-exit-evidence "<latest-attempt-proof>" --turn-exit-evidence "<forced-host-boundary-proof>"
```

```md
# Handoff

- `handoff_schema_version`: `v2-stop-consensus`
- `working_goal`: <current working goal>
- `run_intent`: `<implementation_oriented|planning_only|implementation_loop>`
- `host_resume_mode`: `<same_turn_only|durable_runtime>`
- `capability_mode`: `<must include delegated_agents_authorized_by_loop plus tool_available|tool_unavailable|tool_state_unknown>`
- `current_or_next_stage`: `<active stage or next bounded stage>`
- `stage_status`: `<short status>`
- `remaining_required_stages`:
  - `<stage 1>`
- `latest_evidence_summary`:
  - `<evidence summary>`
- `blocking_findings`:
  - none
- `residual_risks`:
  - `<risk or none>`
- `goal_completion_status`: `<not_reached|completion_candidate|verified_complete_5agent>`
- `goal_completion_evidence`: `<evidence or none>`
- `loop_state`: `<ideation|research|planning|execution|verify|reassessment_pending|paused|stopped>`
- `continuation_mode`: `<default|nonstop>`
- `closeout_round_id`: `<current turn-ending freshness anchor>`
- `run_decision`: `<planning_complete|continue|pause|stop>`
- `sequential_objectives_status`: `<none_detected|open|satisfied>`
- `stop_authorization_status`: `<not_applicable|not_run|deny|allow|external_authority>`
- `stop_authorization_evidence`: `<evidence or none>`
- `stop_consensus_status`: `<not_applicable|not_run|deny|allow_unanimous|waived_external_authority>`
- `stop_consensus_evidence`: `<unanimous 5-agent proof or explicit waiver note>`
- `external_authority_basis`: `<none|explicit_user_pause|explicit_user_stop|explicit_user_redirect|human_decision_required|host_turn_boundary>`
- `pause_reason`: `<reason or none>`
- `next_mandatory_action`: `<next action>`
- `continue_exit_status`: `<not_applicable|next_action_started|blocked_during_attempt>`
- `continue_exit_evidence`: `<evidence or none>`
- `turn_exit_cause`: `<not_applicable|context_budget_exhausted|tool_timeout_after_batch_shrink|blocked_during_attempt|host_turn_boundary_pause|user_interrupt>`
- `turn_exit_evidence`: `<evidence or none>`
- `resume_instructions`:
  - `<resume step>`
```

Notes:

- Treat `handoff.md` as live continuation state, not as a stage-close summary.
- Keep exactly one `working_goal` per run. If the user later opens a
  materially different `$loop` goal, create a sibling run instead of rewriting
  the old run as if it covered both goals.
- If `run_decision=continue`, keep `current_or_next_stage`, `remaining_required_stages`, and `next_mandatory_action` live.
- For live in-progress state that is not being emitted as a user-visible turn end, validate with `validate_handoff.py <run-dir> --require-consensus --live-state`; this allows `turn_exit_cause=not_applicable` and `turn_exit_evidence=none` while tool work continues.
- Always keep `goal_completion_status` current:
  - `not_reached` while required work remains
  - `completion_candidate` only when implementation looks done, no fresh final-audit gap is known, and the fresh `5 Codex` completion challenge still has not run
  - `verified_complete_5agent` only after a fresh unanimous source-first `5 Codex` completion challenge
  - any final-audit gap against the original prompt demotes the run to `not_reached`
- If `host_resume_mode=same_turn_only`, record a user-visible turn end with remaining work as `run_decision=continue` when the current run can auto-resume on the next ordinary follow-up. Keep `continue_exit_status=next_action_started|blocked_during_attempt`, `continue_exit_evidence` with a fresh `attempt_ref=<in-run-artifact>` and `closeout_round_id=<current closeout round>`, plus `turn_exit_cause=host_turn_boundary_pause`.
- For that same-turn-only `run_decision=continue` shape, keep `stop_authorization_status=not_applicable`, `stop_consensus_status=not_applicable`, and `external_authority_basis=none`; the host boundary belongs in `turn_exit_cause` / `turn_exit_evidence`, not in pause authority fields.
- For that same-turn-only `run_decision=continue` shape, the emitted receipt must also include `stop_status=not_stopped`, `host_boundary_effect=visible_turn_only_not_goal_stop`, `auto_resume_trigger=any_followup_message`, `followup_resume_policy=auto_resume_any_followup`, and `resume_command=$loop <run-dir>`.
- On the first ordinary follow-up after that receipt, record `resume-events/<timestamp>-resume.md` using `scripts/record_resume_event.py <run-dir> --trigger any_followup_message` before new work. The event must bind to a previous continue receipt for the same `closeout_round_id`; if none exists yet, record `previous_continue_receipt: none` plus an explicit alignment status instead of pointing at an older unrelated receipt.
- If all required delegated agents hit usage limits, quotas, credits, or rate
  limits after explicit strongest-model dispatch, use the same
  `run_decision=continue` shape when auto-resume is safe:
  `continue_exit_status=blocked_during_attempt` records the delegated quota
  blocker, `turn_exit_cause=host_turn_boundary_pause` records the visible
  same-turn host boundary, and no stop or pause authority is granted.
- For delegated quota blockers, never downshift the model, never reduce the
  required five lanes, and never treat errored/skipped lanes as halt or
  completion proof.
- If `host_resume_mode=same_turn_only` cannot safely encode auto-resume, write a truthful fallback `pause` state instead: `run_decision=pause`, `loop_state=paused`, `stop_authorization_status=external_authority`, `stop_consensus_status=waived_external_authority`, `goal_completion_status=not_reached|completion_candidate`, with a concrete `pause_reason`, live `next_mandatory_action`, and explicit `resume_instructions`. Use `external_authority_basis=host_turn_boundary` only for host-forced exits, and keep stronger explicit human bases such as `explicit_user_pause`, `explicit_user_redirect`, or `human_decision_required` when those are the real cause.
- `host_resume_mode=same_turn_only` does not forbid a lawful autonomous `run_decision=stop` when both the halt gate and the goal-completion gate have fresh unanimous `5 Codex` proof for the current authority snapshot.
- For `same_turn_only` host-boundary pauses, start `resume_instructions` with an exact `$loop <run-dir>` restart step so the pause receipt can surface a copy-paste resume command.
- For implementation-oriented bare `$loop` runs, default `continuation_mode` to `nonstop`; if you keep `default`, record why.
- For implementation-oriented `$loop` / `$agent-loop` runs, delegated
  `spawn_agent` lanes are authorized by the operator token when the tool is
  available. Record that in `capability_mode` as
  `delegated_agents_authorized_by_loop`; do not create stages named
  `when_delegation_authorized`, `ask_to_open_agents`, or similar.
- Treat the `$loop` token as plain-language delegation authority as well as a
  continuation command. If a reader could interpret `handoff.md` as "agents
  still need approval," the handoff is underspecified and should be repaired.
- Do not record residual blockers such as `waiting_for_agent_permission` or
  `subagent delegation not explicit` inside a live `$loop` run unless the host
  truly lacks the tool; the token itself already grants delegation authority.
- Keep the authorization token and tool availability separate inside
  `capability_mode`. Good forms include
  `delegated_agents_authorized_by_loop_tool_available`,
  `delegated_agents_authorized_by_loop_tool_unavailable`, and
  `delegated_agents_authorized_by_loop_tool_state_unknown`.
- If `run_decision=continue`, `next_mandatory_action` should be one atomic next action, not a compound placeholder like `A and B` or `choose and implement`.
- Keep `continue_exit_status` and `continue_exit_evidence` present in every authoritative handoff, even when their value is `not_applicable`.
- If `run_decision=continue`, `continue_exit_status` cannot stay `not_applicable`; it must prove that the latest next action was started or blocked during an attempt.
- If `run_decision=continue`, `continue_exit_evidence` should cite the actual started command, file edit, launched batch, produced artifact, or blocker rather than repeating the plan text. Inspection-only evidence is illegal for `next_action_started`.
- If `run_decision=continue`, `continue_exit_evidence` must carry `attempt_ref=<in-run-artifact>` and `closeout_round_id=<current closeout round>`, and the referenced artifact should include the same `closeout_round_id`.
- If `run_decision=continue`, keep the referenced `attempt_ref` fresh relative to the current `handoff.md`; stale attempt receipts are evidence that the turn ended voluntarily instead of at a real boundary.
- If `run_decision=continue`, `turn_exit_cause` and `turn_exit_evidence` must explain why the turn-ending continue reply was unavoidable.
- If `run_decision=continue` and `continue_exit_status=blocked_during_attempt`,
  `turn_exit_cause=host_turn_boundary_pause` is valid in `same_turn_only`
  hosts because the blocker belongs to `continue_exit_evidence` and the visible
  boundary belongs to `turn_exit_evidence`.
- If `host_resume_mode=same_turn_only` and `run_decision=continue`,
  `turn_exit_evidence` must also carry
  `host_boundary_ref=<authority-receipt-path>` bound to the same
  `closeout_round_id` and latest `attempt_ref`; do not claim a forced visible
  host boundary without a fresh authority receipt.
- If `external_authority_basis=host_turn_boundary`, `turn_exit_cause` must be `host_turn_boundary_pause`, `turn_exit_evidence` must explain the concrete forced visible boundary, and `continue_exit_status` / `continue_exit_evidence` must still prove the latest bounded action attempt.
- If `external_authority_basis=host_turn_boundary`, `host_boundary_ref` should resolve to a fresh authority receipt that echoes the same `closeout_round_id` and latest `attempt_ref`; do not reuse a generic boundary note across closeouts.
- If `stop_authorization_status=allow` or `goal_completion_status=verified_complete_5agent`, bind both proof bundles to the same `closeout_round_id` field in `handoff.md`, while still using distinct `challenge_round_id`s for halt versus completion.
- If `stop_authorization_status=external_authority`, do not use `external_authority_basis=none`.
- If `stop_authorization_status=allow`, require `stop_consensus_status=allow_unanimous` and explicit source-first proof such as `allow_count=5 deny_count=0 ambiguous_count=0 missing_count=0 challenge_round_id=<fresh-round> subject_digest=<current-authority-digest> source_ref=source.md source_digest=<sha256(source.md)> context_mode=clean_source_first authority_basis=source_md_original_user_prompt source_requirements_reconstructed=yes claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality model_policy=resolved_strongest_hard_pin resolved_model_slug=gpt-5.5 resolved_reasoning_effort=xhigh spawn_model_binding=explicit_tool_args refs=<...>`.
- If `run_decision=stop` claims the goal is complete, require `goal_completion_status=verified_complete_5agent` and the same explicit source-first unanimous `5 Codex` proof shape in `goal_completion_evidence`.
- The final five Codex challenge agents must be viewpoint-separated. The proof
  refs must include exactly one artifact for each required viewpoint
  (`architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, `implementation_quality`); duplicate, omitted, or
  generic/blended perspectives are inadmissible.
- Each referenced halt-lane artifact should be an existing file that records `phase=stop_authorization`, `vote=allow`, `viewpoint=<required-viewpoint>`, `challenge_round_id=<same fresh-round>`, `subject_digest=<same current-authority-digest>`, `source_ref=source.md`, `source_digest=<sha256(source.md)>`, `context_mode=clean_source_first`, `authority_basis=source_md_original_user_prompt`, `source_requirements_reconstructed=yes`, `claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff`, `repo_inspection=fresh`, `audit_gap_count=0`, `scope_verdict=original_request_satisfied`, `model_policy=resolved_strongest_hard_pin`, `resolved_model_slug=gpt-5.5`, `resolved_reasoning_effort=xhigh`, `model_resolution_basis_ref=<catalog-or-skill-ref>`, `spawn_model_binding=explicit_tool_args`, `spawn_tool_args_model=gpt-5.5`, `spawn_tool_args_reasoning_effort=xhigh`, `spawn_tool_call_ref=<dispatch receipt>`, `freshness_status=fresh|current_pass|current_cycle`, and a unique `agent_id=<...>`.
- Each referenced goal-completion lane artifact should carry the same fields plus `source_alignment_verdict=all_source_requirements_satisfied`.
- Each `spawn_tool_call_ref` should resolve to an in-run v1 dispatch receipt that records the same phase, agent id, viewpoint, `challenge_round_id`, `closeout_round_id`, `source_digest`, explicit model args, `context_mode=clean_source_first`, and `full_history_fork=false`.
- Each referenced halt-lane artifact should stay inside the current run directory; do not point `refs=` at unrelated absolute paths.
- If `stop_authorization_status=external_authority`, require `stop_consensus_status=waived_external_authority`.
- For external-authority waivers, use structured evidence keys instead of free-form prose:
  - `explicit_user_pause` -> `user_pause_ref=<...>`
  - `explicit_user_stop` -> `user_stop_ref=<authority-receipt-path>` from `scripts/record_user_stop_receipt.py <run-dir> --excerpt "<direct stop>"`
  - `explicit_user_redirect` -> `user_redirect_ref=<...>`
  - `human_decision_required` -> `human_decision_gate=unresolved_after_5_codex`
  - `host_turn_boundary` -> `host_boundary_ref=<authority-receipt-path>`
- A `host_turn_boundary` authority receipt should record `authority_receipt_version=v1`, `authority_kind=host_turn_boundary`, `closeout_round_id=<current closeout round>`, and `attempt_ref=<latest attempt receipt path>`.
- If `run_decision=planning_complete`, require `run_intent=planning_only`, `stop_authorization_status=external_authority`, `stop_consensus_status=waived_external_authority`, and `external_authority_basis=explicit_user_redirect`.
- In the default local file-backed profile, autonomous `run_decision=stop` is legal only when both the halt gate and the goal-completion gate have fresh unanimous `5 Codex` proof.
- If `external_authority_basis=human_decision_required`, record `human_decision_gate=unresolved_after_5_codex` in `stop_authorization_evidence`.
- Use `scripts/closeout_gate.py` as the canonical public turn-end command. Direct `emit_*_reply.py` scripts are internal helpers and reject direct invocation outside the gate.
