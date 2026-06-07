# Handoff Template

Use this as the starting shape for new `handoff.md` files.

Use only this bullet-form shape. Do not mix it with flat `key: value` lines. If a run already has a legacy flat handoff or missing v2 closeout fields, refresh it first:

```bash
python <skill-dir>/scripts/refresh_legacy_handoffs.py <run-dir> --write --continue-exit-status <next_action_started|blocked_during_attempt> --continue-exit-evidence "<latest-attempt-proof>" --turn-exit-evidence "<forced-host-boundary-proof>"
```

```md
# Handoff

- `handoff_schema_version`: `<v2-stop-consensus|v3-worktype-authority>`
- `working_goal`: <current working goal>
- `run_intent`: `<implementation_oriented|planning_only|implementation_loop>`
- `work_type`: `<implementation|research|docs|planning|review|mixed>`
- `review_kind`: `<not_applicable|plan_review|artifact_review|completion_challenge|audit>`
- `host_resume_mode`: `<same_turn_only|durable_runtime>`
- `capability_mode`: `<must include delegated_agents_authorized_by_loop plus tool_available|tool_unavailable|tool_state_unknown>`
- `authority_record_ref`: `<run://authority/run-authority.json or none>`
- `run_authority_status`: `<active|superseded|completed|blocked|quarantined|not_applicable>`
- `run_authority_revision`: `<integer or none>`
- `run_authority_epoch`: `<integer or none>`
- `source_digest`: `<sha256(raw source.md bytes) or none>`
- `stage_graph_digest`: `<sha256:... or none>`
- `adapter_manifest_ref`: `<run://authority/default-adapter.json or run://authority/project-adapter.json or none>`
- `adapter_conformance_status`: `<compatible|requires_adapter|requires_migration|fail_closed|not_applicable>`
- `adapter_effective_config_digest`: `<sha256:... or none>`
- `resource_telemetry_ref`: `<run://telemetry/resource-events.jsonl or none>`
- `research_cycle_ref`: `<run://research-cycles/... or none>`
- `research_cycle_status`: `<not_applicable|not_run|running|deny|allow_unanimous|stale|schema_invalid|blocked>`
- `research_cycle_digest_set`: `<sha256:... or none>`
- `completion_subject_type`: `<repo_diff|document_artifact|research_packet|plan_artifact|plan_review|artifact_review|completion_challenge|audit_packet|operation_record|composite_subject>`
- `completion_subject_ref`: `<run://completion-subjects/... or none>`
- `completion_subject_digest`: `<sha256:... or none>`
- `composite_subject_digest`: `<sha256:... or none>`
- `challenge_cycle_ref`: `<run://challenge-cycles/... or none>`
- `challenge_cycle_status`: `<not_applicable|not_run|running|deny|allow_unanimous|stale|schema_invalid>`
- `challenge_cycle_digest_set`: `<sha256:... or none>`
- `visible_output_contract`: `<live_status|challenge_result|forced_boundary_continue|blocked_external_gate|terminal_completion|not_applicable>`
- `current_or_next_stage`: `<active stage or next bounded stage>`
- `stage_status`: `<short status>`
- `current_batch`: `<batch_id or none>`
- `risk_tier`: `<tier0_trivial|tier1_local|tier2_material|tier3_high_risk|not_classified>`
- `implementation_gate_status`: `<not_applicable|strategy_pending|pre_challenge_pending|implementation_in_progress|verification_pending|post_challenge_pending|accepted|blocked>`
- `implementation_gate_evidence`: `<for accepted file-changing gates: either recognized tier0/tier1 local skip/self-check evidence, or strategy_ref=<top-model-strategy-artifact> verification_agent_ref=<verification-agent-artifact> pre_plan_validation_lane_count=2 pre_plan_validation_viewpoint_set=operator_execution_fit|verification_evidence_fit pre_plan_validation_verdict=pass_unanimous pre_plan_validation_refs=<2 pre_implementation_plan_validation artifacts> post_plan_validation_lane_count=2 post_plan_validation_viewpoint_set=operator_execution_fit|verification_evidence_fit post_plan_validation_verdict=pass_unanimous post_plan_validation_refs=<2 post_implementation_plan_validation artifacts>; for tier2/tier3 also add pre_challenge_lane_count=5 pre_challenge_viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality pre_challenge_verdict=pass_unanimous pre_challenge_refs=<5 pre_implementation_challenge artifacts> post_challenge_lane_count=5 post_challenge_viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality post_challenge_verdict=pass_unanimous post_challenge_refs=<5 post_implementation_challenge artifacts>; otherwise none>`
- `commit_queue_status`: `<not_applicable|intent_needed|ready_to_commit|needs_commit_owner|orphan_or_conflicted|committed|blocked>`
- `remaining_required_stages`:
  - `<stage 1>`
- `latest_evidence_summary`:
  - `<evidence summary>`
- `blocking_findings`:
  - none
- `residual_risks`:
  - `<risk or none>`
- `goal_completion_status`: `<not_reached|completion_candidate|verified_complete_5lane>`
- `goal_completion_evidence`: `<evidence or none>`
- `loop_state`: `<ideation|research|planning|execution|verify|reassessment_pending|paused|stopped>`
- `continuation_mode`: `<default|nonstop>`
- `closeout_round_id`: `<current turn-ending freshness anchor>`
- `run_decision`: `<planning_complete|continue|pause|stop>`
- `sequential_objectives_status`: `<none_detected|open|satisfied>`
- `stop_authorization_status`: `<not_applicable|not_run|deny|allow|external_authority>`
- `stop_authorization_evidence`: `<evidence or none>`
- `stop_consensus_status`: `<not_applicable|not_run|deny|allow_unanimous|waived_external_authority>`
- `stop_consensus_evidence`: `<unanimous 5-lane proof or explicit waiver note>`
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
- New runs should populate the work-type and authority fields above. Existing
  v2 handoffs may be refreshed incrementally, but terminal stop for v3-style
  work requires the authority, subject, challenge-cycle, and digest fields.
- `not_classified` is a legacy migration value only. New v3 runs must choose a
  concrete `work_type` and `completion_subject_type`.
- Keep exactly one `working_goal` per run. If the user later opens a
  materially different `$loop` goal, create a sibling run instead of rewriting
  the old run as if it covered both goals.
- `work_type` is separate from `run_intent`. `run_intent` describes why the
  operator invoked `$loop`; `work_type` selects lifecycle gates and completion
  subject shape.
- For `work_type=review`, `review_kind` must be concrete. For other work
  types, use `not_applicable`.
- For `work_type=mixed`, `completion_subject_type=composite_subject` and
  `composite_subject_digest` must cover every required stage contribution.
- For non-`repo_diff` subjects without code artifacts, the controller and lanes
  must not produce code-review-shaped output unless the referenced subject
  explicitly supports it.
- `work_type` constrains `completion_subject_type`: implementation uses
  `repo_diff|operation_record`; research uses `research_packet`; docs use
  `document_artifact`; planning uses `plan_artifact`; review uses the matching
  review subject; mixed uses `composite_subject`.
- `research_cycle_status=allow_unanimous` requires a JSON `research-cycle-v1`
  artifact with concrete `cycle_id`, exactly the five initial research lanes
  `architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, and `implementation_quality`, explicit
  `gpt-5.5` model args with exactly three `xhigh` lanes and two `high` lanes,
  `agent_role=research_agent`, `model_resolution_basis_ref`, source/authority
  revision/epoch binding, resolvable `dispatch_receipt_version=v1` spawn
  receipts for every lane that also record `model_resolution_basis_ref`, and all
  lanes merged before plan lock.
- `challenge_cycle_status=allow_unanimous` is admissible only for one current
  JSON `challenge-cycle-v1` artifact where every lane reviewed the same
  `source_digest`, `stage_graph_digest`, `adapter_manifest_ref`,
  `adapter_effective_config_digest`, `completion_subject_type`, and
  `completion_subject_digest` under the same schema, policy, prompt,
  validator, authority revision, and authority epoch. Lane entries must exactly
  cover `architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, and `implementation_quality`, and each lane must
  reference an in-run artifact with `vote=allow` bound to the same concrete
  `cycle_id`. For terminal completion, `goal_completion_evidence refs=` must
  exactly match the accepted challenge-cycle `lanes` artifact refs. If
  autonomous stop is allowed, the same challenge cycle must also include
  `stop_lanes` whose artifact refs exactly match `stop_consensus_evidence
  refs=`, and every referenced lane must validate its dispatch receipt phase,
  challenge mode, model args, source digest, authority revision/epoch, and
  cycle id.
- Accepted implementation gates must satisfy exactly one recognized acceptance
  shape: tier0 deterministic skip evidence; tier1 deterministic skip evidence;
  tier1 structured self-check evidence; non-file-changing evidence; or the
  delegated mini pre/post plan-validation evidence above, including a distinct
  `verification_agent_ref` artifact with `agent_role=verification_agent`.
  Tier0 skip evidence records
  `mini_plan_validation_skip=tier0_trivial|single_file_local_fix|user_specified_exact_change|no_behavior_change`.
  Tier1 skip evidence records
  `mini_plan_validation_skip=<single_file_local_fix|user_specified_exact_change|no_behavior_change>`
  with `local_verification` and `skip_scope_evidence`. Tier1 self-check
  evidence records `tier1_self_check=pass`, `risk_expanded=false`,
  implementation summary, verification plan, requirement trace, local
  verification result/ref, scoped files, and no
  external/API/DB/security/shared-boundary scope. Tier2 and tier3 accepted gates
  must use concrete pre/post 5-lane challenge artifacts; waiver prose is valid
  only for non-accepted blocked/override states.
- Autonomous terminal `run_decision=stop` with
  `goal_completion_status=verified_complete_5lane` requires
  `handoff_schema_version=v3-worktype-authority`; v2 handoffs are valid only
  for nonterminal compatibility or direct explicit-user-stop paths.
- Terminal `run_decision=stop` requires
  `visible_output_contract=terminal_completion`,
  `adapter_conformance_status=compatible`, `run_authority_status=completed`,
  `adapter_manifest_ref`, fresh source/stage/subject digests, and
  CAS-completed authority state with `cas_transition_ref` pointing at a valid
  `authority_transition_receipt_version=v1` pre/post digest receipt.
- If `run_decision=continue`, keep `current_or_next_stage`, `remaining_required_stages`, and `next_mandatory_action` live.
- For live in-progress state that is not being emitted as a user-visible turn end, validate with `validate_handoff.py <run-dir> --require-consensus --live-state`; this allows `turn_exit_cause=not_applicable` and `turn_exit_evidence=none` while tool work continues.
- Always keep `goal_completion_status` current:
  - `not_reached` while required work remains
  - `completion_candidate` only when implementation looks done, no fresh final-audit gap is known, and the fresh `5 Codex` completion challenge still has not run
  - `verified_complete_5lane` only after a fresh unanimous source-first `5 Codex` completion challenge
  - any final-audit gap against the original prompt demotes the run to `not_reached`
- If `host_resume_mode=same_turn_only`, record a user-visible turn end with remaining work as `run_decision=continue` when the current run can auto-resume on the next ordinary follow-up. Keep `continue_exit_status=next_action_started|blocked_during_attempt`, `continue_exit_evidence` with a fresh `attempt_ref=<in-run-artifact>` and `closeout_round_id=<current closeout round>`, plus `turn_exit_cause=host_turn_boundary_pause`.
- For that same-turn-only `run_decision=continue` shape, keep `stop_authorization_status=not_applicable`, `stop_consensus_status=not_applicable`, and `external_authority_basis=none`; the host boundary belongs in `turn_exit_cause` / `turn_exit_evidence`, not in pause authority fields.
- For that same-turn-only `run_decision=continue` shape, the emitted receipt must also include `stop_status=not_stopped`, `host_boundary_effect=visible_turn_only_not_goal_stop`, `auto_resume_trigger=any_followup_message`, `followup_resume_policy=auto_resume_any_followup`, and `resume_command=$loop <run-dir>`.
- On the first ordinary follow-up after that receipt, record `resume-events/<timestamp>-resume.md` using `scripts/record_resume_event.py <run-dir> --trigger any_followup_message` before new work. The event must bind to a previous continue receipt for the same `closeout_round_id`; if none exists yet, record `previous_continue_receipt: none` plus an explicit alignment status instead of pointing at an older unrelated receipt.
- If all required delegated agents hit usage limits, quotas, credits, or rate
  limits after explicit `frontier_loop_authority_v1/high`-or-stronger dispatch, use the same
  `run_decision=continue` shape when auto-resume is safe:
  `continue_exit_status=blocked_during_attempt` records the delegated quota
  blocker, `turn_exit_cause=host_turn_boundary_pause` records the visible
  same-turn host boundary, and no stop or pause authority is granted.
- For delegated quota blockers, never downshift below the required capability
  class, never reduce the
  required five lanes, and never treat errored/skipped lanes as halt or
  completion proof. 5.4, Spark, 5.3, mini-model, `low`, and `medium` fallback
  is inadmissible. A halt or completion proof requires three
  `gpt-5.5/xhigh` lanes and two `gpt-5.5/high` lanes.
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
- If a visible recap names remaining bounded work, `run_decision=stop` is invalid and a
  normal final answer is invalid. The handoff must instead set
  `run_decision=continue`, keep those items in `remaining_required_stages`, and
  cite the concrete next started action or a canonical no-bounded-action blocker.
- For implementation loops derived from a prior roadmap/research artifact,
  `goal_completion_evidence` must reference the current implementation-scope
  authority, not only the earlier roadmap-generation completion proof.
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
- If `stop_authorization_status=allow` or `goal_completion_status=verified_complete_5lane`, bind both proof bundles to the same `closeout_round_id` field in `handoff.md`, while still using distinct `challenge_round_id`s for halt versus completion.
- If `stop_authorization_status=external_authority`, do not use `external_authority_basis=none`.
## Final Proof

- If `stop_authorization_status=allow`, require `stop_consensus_status=allow_unanimous` and explicit source-first proof such as `allow_count=5 deny_count=0 ambiguous_count=0 missing_count=0 challenge_round_id=<fresh-round> agent_role=challenge_agent challenge_review_mode=autonomous_stop_challenge subject_digest=<current-authority-digest> source_ref=source.md source_digest=<sha256(raw source.md bytes)> context_mode=clean_source_first authority_basis=source_md_original_user_prompt source_requirements_reconstructed=yes claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff repo_inspection=fresh audit_gap_count=0 scope_verdict=original_request_satisfied route_context=final_halt_completion loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof policy_ref_digests=sha256:<skill-digest>|sha256:<template-digest> policy_coverage_verdict=route_required_refs_loaded viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality coverage_viewpoint_set=architecture_dependency|failure_verification|goal_efficiency|requirement_alignment|implementation_quality model_policy=gpt_5_5_high_minimum_explicit top_model_lane_min=5 resolved_model_slug=gpt-5.5 resolved_reasoning_effort=xhigh spawn_model_binding=explicit_tool_args refs=<...>`.
- If `run_decision=stop` claims the goal is complete, require `goal_completion_status=verified_complete_5lane` and the same explicit source-first unanimous `5 Codex` proof shape in `goal_completion_evidence`.
- The final five Codex challenge agents must be lane-separated. The proof refs
  must include exactly one artifact for each required lane
  (`architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, `implementation_quality`); duplicate, omitted, or
  generic/blended perspectives are inadmissible.
- The final five Codex agents must be challenge-role lanes, not workers,
  explorers, summarizers, or generic reviewers. Aggregate evidence, each lane
  artifact, and each dispatch receipt must record
  `agent_role=challenge_agent`.
- Each referenced halt-lane artifact should be an existing file that records `phase=stop_authorization`, `agent_role=challenge_agent`, `challenge_review_mode=autonomous_stop_challenge`, `vote=allow`, `viewpoint=<required-lane>`, `coverage_viewpoints=<same required lane>`, `challenge_round_id=<same fresh-round>`, `subject_digest=<same current-authority-digest>`, `source_ref=source.md`, `source_digest=<sha256(raw source.md bytes)>`, `context_mode=clean_source_first`, `authority_basis=source_md_original_user_prompt`, `source_requirements_reconstructed=yes`, `claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff`, `repo_inspection=fresh`, `audit_gap_count=0`, `scope_verdict=original_request_satisfied`, `route_context=final_halt_completion`, `loaded_policy_refs=SKILL.md#NonNegotiableInvariants|handoff-template.md#FinalProof`, `policy_ref_digests=sha256:<skill-digest>|sha256:<template-digest>`, `policy_coverage_verdict=route_required_refs_loaded`, `model_policy=gpt_5_5_high_minimum_explicit`, `resolved_model_slug=<lane-model>`, `resolved_reasoning_effort=<lane-effort>`, `model_resolution_basis_ref=<catalog-or-skill-ref>`, `spawn_model_binding=explicit_tool_args`, `spawn_tool_args_model=<same-lane-model>`, `spawn_tool_args_reasoning_effort=<same-lane-effort>`, `spawn_tool_call_ref=<dispatch receipt>`, `freshness_status=fresh|current_pass|current_cycle`, and a unique `agent_id=<...>`.
- Across the five final lane artifacts, the exact model mix is three
  `gpt-5.5/xhigh` lanes and two `gpt-5.5/high` lanes.
- Each referenced goal-completion lane artifact should carry the same fields except `challenge_review_mode=goal_completion_challenge`, plus `source_alignment_verdict=all_source_requirements_satisfied`.
- Each `spawn_tool_call_ref` should resolve to an in-run v1 dispatch receipt that records the same phase, agent id, viewpoint, `agent_role=challenge_agent`, phase-specific `challenge_review_mode`, `challenge_round_id`, `closeout_round_id`, `source_digest`, explicit model args, `route_context`, `loaded_policy_refs`, `policy_ref_digests`, `policy_coverage_verdict`, `context_mode=clean_source_first`, and `full_history_fork=false`.
- If the selected run binds to a repo root containing `AGENTS.md`, the aggregate proof, every lane artifact, and every dispatch receipt must include `AGENTS.md#LoopCompletionGate` in `loaded_policy_refs` and the digest of that section in `policy_ref_digests`. If there is no bound repo `AGENTS.md`, omit both together.
- Each referenced halt-lane artifact should stay inside the current run directory; do not point `refs=` at unrelated absolute paths.
- If `stop_authorization_status=external_authority`, require `stop_consensus_status=waived_external_authority`.
- For external-authority waivers, use structured evidence keys instead of free-form prose:
  - `explicit_user_pause` -> `user_pause_ref=<...>`
  - `explicit_user_stop` -> `user_stop_ref=<authority-receipt-path>` from `scripts/record_user_stop_receipt.py <run-dir> --excerpt "<direct stop>"`
  - `explicit_user_redirect` -> `user_redirect_ref=<...>`
  - `human_decision_required` -> `human_decision_gate=unresolved_after_3_codex`
  - `host_turn_boundary` -> `host_boundary_ref=<authority-receipt-path>`
- A `host_turn_boundary` authority receipt should record `authority_receipt_version=v1`, `authority_kind=host_turn_boundary`, `closeout_round_id=<current closeout round>`, and `attempt_ref=<latest attempt receipt path>`.
- If `run_decision=planning_complete`, require `run_intent=planning_only`, `stop_authorization_status=external_authority`, `stop_consensus_status=waived_external_authority`, and `external_authority_basis=explicit_user_redirect`.
- In the default local file-backed profile, autonomous `run_decision=stop` is legal only when both the halt gate and the goal-completion gate have fresh unanimous `5 Codex` proof.
- If `external_authority_basis=human_decision_required`, record `human_decision_gate=unresolved_after_3_codex` in `stop_authorization_evidence`.
- Use `scripts/closeout_gate.py` as the canonical public turn-end command. Direct `emit_*_reply.py` scripts are internal helpers and reject direct invocation outside the gate.
