# Stage 7 Packet Templates Draft

This draft turns the validated Stage 6 packet contract into concrete reusable packet templates.

It does not yet rewrite `SKILL.md` or repo-local agent assets.

It assumes these files are already authoritative:

- [kernel-spec-stage1-3-draft.md](./kernel-spec-stage1-3-draft.md)
- [kernel-spec-stage5-oracle-draft.md](./kernel-spec-stage5-oracle-draft.md)
- [kernel-spec-stage6-packets-draft.md](./kernel-spec-stage6-packets-draft.md)

## Stage 7 Goal

Stage 7 exists to define concrete packet skeletons that the main CLI can fill without re-inventing prompt structure at runtime.

Stage 7 is valid only when:

- every packet template is directly compatible with Stage 6 packet fields
- every template preserves controller authority boundaries
- every template keeps context narrow enough for delegated lanes
- challenge templates stay viewpoint-specific without changing packet shape
- integration templates preserve seal-point bundle rules instead of narrating them loosely

## Template Rules

- All templates assume `model_policy=resolved_strongest_hard_pin`.
- All template-driven delegated dispatches must copy `resolved_model_slug` and `resolved_reasoning_effort` onto the actual `spawn_agent` tool call. Template fields alone do not satisfy the model-pin contract.
- Templates must be fillable from authoritative refs plus small derived views.
- Templates may carry short operator notes, but not transcript replay.
- Templates must separate:
  - `packet_envelope`
  - `authoritative_inputs`
  - `role_objective`
  - `forbidden_actions`
  - `required_outputs`
- A template may not hide a required field in prose only.

## Common Envelope Template

```yaml
packet_envelope:
  packet_id: <generated>
  packet_kind: <research_packet|planning_packet|challenge_packet|worker_packet|verification_packet|integration_packet>
  model_policy: resolved_strongest_hard_pin
  resolved_model_slug: <resolved_model_slug>
  resolved_reasoning_effort: <resolved_reasoning_effort>
  model_resolution_basis_ref: <model_resolution_basis_ref>
  dispatch_mode: <bootstrap|resume>
  run_id: <run_id>
  cycle_id: <cycle_id>
  stage_id: <stage_id|none_yet>
  plan_snapshot_id: <plan_snapshot_id|none_yet>
  working_goal_ref: <working_goal_ref>
  source_packet_ref: <source_packet_ref>
  request_intent_ref: <request_intent_ref>
  authoritative_handoff_ref: <handoff_ref|none_yet>
  preflight_result_ref: <preflight_ref|omit_when_not_dispatch_opening>
  dispatch_basis: <bootstrap_basis|resume_basis|omit_when_not_dispatch_opening>
```

A filled packet is dispatch-legal only when the delegated `spawn_agent` call repeats `model=<resolved_model_slug>` and `reasoning_effort=<resolved_reasoning_effort>` explicitly. Relying on inherited or default selection is illegal.

## Research Packet Template

```yaml
packet_envelope:
  packet_kind: research_packet
research_mode: <pre_plan|post_stage|goal_reassessment>
authoritative_inputs:
  handoff_or_bootstrap_ref: <handoff_ref|bootstrap_ref>
  working_goal_ref: <working_goal_ref>
  source_packet_ref: <source_packet_ref>
  research_viewpoint: <architecture_dependency|failure_verification|goal_efficiency>
  revised_plan_ref: <plan_snapshot_ref|none_yet>
  stage_refs: <stage_refs|none_yet>
  decision_ledger_ref: <decision_ledger_ref>
  evidence_packet_ref: <evidence_packet_ref|none_yet>
  probe_refs: <probe_refs>
derived_views:
  stage_view: <compact_stage_view|omit>
  decision_ledger_view: <compact_decision_ledger_view|omit>
  evidence_view: <compact_evidence_view|omit>
  probe_view: <compact_probe_view|omit>
role_objective:
  primary: produce current-cycle or goal-level research that sharpens next planning or stop decisions
  viewpoint_focus:
    - <resolved_focus_for_selected_research_viewpoint_only>
  focus:
    - current state deltas
    - admissible improvement candidates
    - efficiency opportunities
    - risks and constraints
    - counter-check
mode_focus:
  pre_plan:
    - initial target analysis
    - option space
    - first-stage leverage
  post_stage:
    - next ordering changes
    - newly visible debt
    - higher-quality follow-up
  goal_reassessment:
    - goal saturation
    - remaining admissible candidates
    - stop vs continue pressure
forbidden_actions:
  - invent cycle_id
  - mutate revised_plan
  - issue continue or stop
  - issue commit, rework, rescope, or escalate
  - write worker claims
required_outputs:
  packet_kind: research_synthesis_candidate
  fields:
    - synthesis_mode
    - research_viewpoint
    - research_viewpoint_set
    - lane_candidate_refs
    - phase
    - current_state_findings
    - goal_alignment_assessment
    - admissible_candidates
    - efficiency_opportunities
    - risk_findings
    - recommended_ordering_changes
    - counter_check
  counter_check_fields:
    - admissible_candidate_result
    - remaining_required_stage_result
    - evidence_refs
    - why_not_more
completion_gate:
  - delegated lane output sets `synthesis_mode=lane`
  - delegated lane output carries exactly one explicit `research_viewpoint`
  - output `phase` matches packet `research_mode`
  - counter_check includes admissible_candidate_result and evidence_refs
  - every recommendation cites authoritative refs
```

Research phase consolidation rule:

- exactly three delegated `research_packet` lanes must run per research phase, one per
  `architecture_dependency`, `failure_verification`, and `goal_efficiency`
- before any `planning_packet` or run-level stop/continue decision may consume fresh research, the
  main CLI must assemble a merged `research_synthesis_candidate` with:
  - `synthesis_mode=merged`
  - `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`
  - concrete `lane_candidate_refs` for all three delegated lane outputs

## Planning Packet Template

```yaml
packet_envelope:
  packet_kind: planning_packet
authoritative_inputs:
  handoff_or_bootstrap_ref: <handoff_ref|bootstrap_ref>
  working_goal_ref: <working_goal_ref>
  source_packet_ref: <source_packet_ref>
  request_intent_ref: <request_intent_ref>
  current_cycle_research_candidate_ref: <research_candidate_ref|omit_when_not_pre_integrate_plan>
  authoritative_research_ref: <research_synthesis_ref|omit_when_not_available>
  revised_plan_ref: <plan_snapshot_ref|none_yet>
  decision_ledger_ref: <decision_ledger_ref>
  stage_refs: <stage_refs|none_yet>
  queue_refs: <queue_refs|none_yet>
derived_views:
  decision_ledger_view: <compact_decision_ledger_view|omit>
  stage_view: <compact_stage_view|omit>
  queue_view: <compact_queue_view|omit>
  parallel_worker_lanes: <human_view_derived_from_dispatchable_slice_specs|optional>
role_objective:
  primary: produce the next executable staged plan candidate without changing controller state
  focus:
    - preserve goal
    - preserve dependencies unless justified
    - keep current stage bounded
    - define dispatchable slice specs
forbidden_actions:
  - seal handoff_packet
  - activate candidate as executable
  - mutate claim state
  - issue controller decisions
required_outputs:
  packet_kind: revised_plan_candidate
  fields:
    - run_intent
    - working_goal
    - success_condition
    - current_stage
    - dispatchable_slice_specs
    - remaining_stage_queue
    - quality_gates
    - research_hooks
    - open_questions
    - progress_ledger_candidate
  run_intent_enum:
    - planning_only
    - implementation_oriented
  current_stage_template:
    stage_id: <stage_id>
    stage_summary: <stage_summary>
    stage_obligation: <required_for_success|optional_followup>
  remaining_stage_queue_entry_template:
    stage_id: <stage_id>
    stage_summary: <stage_summary>
    stage_obligation: <required_for_success|optional_followup>
  dispatchable_slice_specs_template_ref: dispatchable_slice_spec_template
completion_gate:
  - current_stage is concrete
  - run_intent is explicit
  - run_intent is derived from `request_intent_ref`, not copied from source text alone
  - bootstrap planning uses concrete `current_cycle_research_candidate_ref`
  - at least one of `current_cycle_research_candidate_ref` or `authoritative_research_ref` is concrete
  - any consumed research artifact exposes `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`
  - every dispatchable_slice_spec follows the shared `dispatchable_slice_spec_template`
```

## Shared Dispatchable Slice Spec Template

```yaml
dispatchable_slice_spec_template:
  slice_id: <slice_id>
  requested_output: <requested_output>
  read_scope: <read_scope>
  write_scope: <write_scope>
  gate_refs: <gate_refs>
  recovery_republish_rule: <recovery_republish_rule>
```

## Challenge Packet Template

```yaml
packet_envelope:
  packet_kind: challenge_packet
authoritative_inputs:
  handoff_or_bootstrap_ref: <handoff_ref|bootstrap_ref>
  phase: <planning_phase|verify_phase>
  challenge_review_mode: <plan_review|verify_current_pass|post_close_revalidation|cold_start_revalidation>
  viewpoint: <architecture_dependency|failure_verification|goal_efficiency>
  review_target_ref: <revised_plan_candidate_ref|verification_candidate_ref|evidence_packet_ref>
  active_plan_snapshot_id_ref: <plan_snapshot_id_ref|none_yet>
  active_target_fingerprint_ref: <target_fingerprint_ref>
  gate_refs: <gate_refs>
  constraint_refs: <constraint_refs>
  dependency_refs: <dependency_refs>
review_target_rules:
  - `challenge_review_mode` is authoritative and must be explicit
  - `revised_plan_candidate_ref` is legal only in `phase=planning_phase` with `challenge_review_mode=plan_review`
  - `verification_candidate_ref` is the default legal target in `phase=verify_phase` with `challenge_review_mode=verify_current_pass`
  - `evidence_packet_ref` is legal only in `phase=verify_phase` with `challenge_review_mode=post_close_revalidation|cold_start_revalidation`
  - `active_plan_snapshot_id_ref=none_yet` is legal only in `phase=planning_phase` with `challenge_review_mode=plan_review` before the first `integrate_plan` seal of the cycle
  - `evidence_packet_ref` must match the active `plan_snapshot_id` and `target_fingerprint`
role_objective:
  primary: attack the current plan or verification target without implementing fixes
  viewpoint_focus:
    - <resolved_focus_for_selected_viewpoint_only>
forbidden_actions:
  - implement the fix
  - mutate controller state
  - mutate claim state
  - emit final acceptance
required_outputs:
  packet_kind: challenge_result_candidate
  fields:
    - phase
    - challenge_review_mode
    - viewpoint
    - review_target_ref
    - gate_verdict
    - blocking_findings
    - non_blocking_findings
    - source_drift_risks
    - missing_gates
    - dependency_order_fixes
    - recommended_reordering
    - execution_ready
  finding_template:
    - severity
    - summary
    - why_it_matters
    - evidence
    - blocking
    - plan_change
completion_gate:
  - findings cite evidence
  - blocking findings are explicit
  - `challenge_review_mode` is explicit and self-consistent with `phase` and `review_target_ref`
  - output does not mutate plan or evidence directly
```

## Worker Packet Template

```yaml
packet_envelope:
  packet_kind: worker_packet
authoritative_inputs:
  handoff_ref: <handoff_ref>
  revised_plan_ref: <plan_snapshot_ref>
  embedded_claim_path_ref: <embedded_claim_path_ref>
  claim_id: <claim_id>
  claim_status: open
  slice_id: <slice_id>
  plan_snapshot_id: <plan_snapshot_id>
  stage_id: <stage_id>
  open_write_claims_ref: <open_write_claims_ref>
  open_claim_membership_ref: <claim_membership_ref>
  dispatch_safety_ref: <dispatch_safety_ref>
  replacement_lineage_ref: <replacement_lineage_ref|none_yet>
  read_scope: <read_scope>
  write_scope: <write_scope>
  gate_refs: <gate_refs>
  requested_output: <requested_output>
derived_views:
  gate_view: <compact_gate_view|omit>
role_objective:
  primary: produce one bounded delta candidate for one still-open claim on one current snapshot
forbidden_actions:
  - write outside write_scope
  - reopen or republish claims
  - merge own output
  - mutate authoritative artifacts
  - assume authority outside the packet's plan_snapshot_id
  - emit from closed, superseded, invalidated, or replacement-required claim
  - emit without dispatch_safety_ref
required_outputs:
  packet_kind: worker_delta_candidate
  fields:
    - claim_id
    - plan_snapshot_id
    - diff_summary
    - artifact_refs
    - check_results
    - open_risks
    - requested_followup_checks
completion_gate:
  - output is scoped to claim_id and plan_snapshot_id
  - no undeclared write is proposed
```

## Verification Packet Template

```yaml
packet_envelope:
  packet_kind: verification_packet
authoritative_inputs:
  handoff_ref: <handoff_ref>
  revised_plan_ref: <plan_snapshot_ref>
  gate_refs: <gate_refs>
  claim_state_refs: <claim_state_refs>
  artifact_refs: <artifact_refs>
  check_plan_ref: <check_plan_ref>
derived_views:
  gate_view: <compact_gate_view|omit>
  claim_state_view: <compact_claim_state_view|omit>
role_objective:
  primary: assemble fresh current-stage verification evidence for verify challenge and integration
forbidden_actions:
  - close the stage
  - seal evidence_packet
  - mutate decision_ledger
  - issue controller decisions
required_outputs:
  packet_kind: verification_candidate
  fields:
    - plan_snapshot_id
    - target_fingerprint
    - target_refs
    - artifact_refs
    - check_results
    - log_refs
    - observed_findings
    - freshness_status
    - stale_reason
    - collected_at
    - gate_assessment
completion_gate:
  - freshness fields are explicit
  - `plan_snapshot_id`, `target_fingerprint`, and `target_refs` are explicit and self-consistent
```

## Integration Packet Template

```yaml
packet_envelope:
  packet_kind: integration_packet
authoritative_inputs:
  handoff_or_bootstrap_ref: <handoff_ref|bootstrap_ref>
  request_intent_ref: <request_intent_ref>
  revised_plan_ref: <plan_snapshot_ref|none_yet>
  decision_ledger_ref: <decision_ledger_ref>
  active_evidence_packet_ref: <evidence_packet_ref|required_for_integrate_verify_revalidation|omit_otherwise>
  seal_point: <integrate_plan|integrate_verify|cycle_decision|goal_reassessment|run_decision>
  candidate_refs:
    research_synthesis_candidate_ref: <ref|required_for_integrate_plan_or_goal_reassessment|omit_otherwise>
    revised_plan_candidate_ref: <ref|omit>
    challenge_result_candidate_refs:
      architecture_dependency: <ref|required_for_integrate_plan_or_integrate_verify>
      failure_verification: <ref|required_for_integrate_plan_or_integrate_verify>
      goal_efficiency: <ref|required_for_integrate_plan_or_integrate_verify>
    verification_candidate_ref: <ref|required_for_integrate_verify_current_pass|omit_for_revalidation_subcases>
    worker_delta_candidate_refs: <refs|omit>
  fixed_cycle_close_decision_ref: <ref|omit_when_not_cycle_decision>
  fixed_termination_posture_ref: <ref|omit_when_not_run_decision>
  legality_refs: <legality_refs|omit_when_not_required>
role_objective:
  primary: prepare one barrier-scoped integration result candidate without leaking authority before seal success
forbidden_actions:
  - mint cycle_close_decision
  - mint termination_posture, except the fixed terminal planning posture `stop_planning_deliverable` derived from immutable `request_intent_ref` at `seal_point=integrate_plan`
  - leak unsealed candidates as authoritative
  - skip barrier bundle rules
required_outputs:
  packet_kind: integration_result_candidate
  fields:
    - seal_point
    - candidate_bundle_manifest
    - success_bundle
    - failure_fallback
    - draft_publications
  candidate_bundle_manifest_template:
    seal_point: <seal_point>
    candidate_refs_consumed: <candidate_refs_consumed>
    research_viewpoint_set: <research_viewpoint_set|omit_when_no_research_candidate_ref>
    challenge_viewpoint_set: <challenge_viewpoint_set|omit_when_not_integrate_plan_or_integrate_verify>
  draft_visibility_template:
    seal_point: <seal_point>
    visible_drafts: <visible_drafts|none>
    draft_only_until_seal_success: true
  failure_fallback_template:
    prior_authoritative_handoff_ref: <prior_authoritative_handoff_ref>
    prior_executable_plan_snapshot_ref: <prior_executable_plan_snapshot_ref|none_yet>
    allowed_draft_visibility: draft_visibility_template
seal_point_bundle_rules:
  integrate_plan:
    success_bundle:
      - authoritative_research_synthesis
      - authoritative_revised_plan
      - authoritative_decision_ledger_mutation
      - authoritative_claim_state_with_open_write_claims_parity
      - sealed_planning_handoff_with_full_schema
  integrate_verify:
    success_bundle:
      - authoritative_evidence_packet_bound_to_the_legal_integrate_verify_subcase_target
      - authoritative_decision_ledger_mutation
      - authoritative_claim_state_with_open_write_claims_parity
      - authoritative_revised_plan_when_changed
      - sealed_cycle_decision_handoff_with_full_schema
  cycle_decision:
    success_bundle:
      - fixed_cycle_close_decision_ref
      - legality_refs
      - authoritative_decision_ledger_mutation_when_required
      - sealed_successor_handoff_with_full_schema
  goal_reassessment:
    success_bundle:
      - authoritative_research_synthesis
      - authoritative_decision_ledger_mutation_when_required
      - sealed_run_decision_handoff_with_full_schema
  run_decision:
    success_bundle:
      - fixed_termination_posture_ref
      - legality_refs
      - sealed_successor_handoff_with_full_schema
completion_gate:
  - success_bundle is valid for exactly one seal_point
  - when a `research_synthesis_candidate_ref` is consumed, `candidate_bundle_manifest.research_viewpoint_set` contains exactly `architecture_dependency`, `failure_verification`, and `goal_efficiency`
  - when `seal_point=integrate_plan|integrate_verify`, `candidate_bundle_manifest.challenge_viewpoint_set` contains exactly `architecture_dependency`, `failure_verification`, and `goal_efficiency`
  - when `seal_point=integrate_verify`, exactly one legal subcase holds:
    - current-pass subcase: `verification_candidate_ref` is concrete, every consumed challenge result is `phase=verify_phase` with `challenge_review_mode=verify_current_pass` and `review_target_ref=verification_candidate_ref`, and the authoritative evidence packet in `success_bundle` is derived from `verification_candidate_ref` with matching `plan_snapshot_id`, `target_fingerprint`, and `target_refs`
    - revalidation subcase: `active_evidence_packet_ref` is concrete, every consumed challenge result is `phase=verify_phase` with `challenge_review_mode=post_close_revalidation|cold_start_revalidation` and `review_target_ref=active_evidence_packet_ref`, and the authoritative evidence packet in `success_bundle` preserves that revalidation target
  - failure_fallback preserves prior authority through named fallback refs
  - `failure_fallback.allowed_draft_visibility` follows `draft_visibility_template` when draft visibility is permitted and `draft_publications` remain non-authoritative until paired seal success
```

`failure_fallback` must follow `failure_fallback_template`.

`failure_fallback.allowed_draft_visibility` must use the same `draft_visibility_template` shape, and draft visibility may be granted only where a Stage 5 `allowed_draft_visibility` contract explicitly permits it for that seal point.

## Shared Handoff Draft Template

```yaml
handoff_packet_draft:
  handoff_packet_id: <generated_on_seal>
  run_id: <run_id>
  cycle_id: <cycle_id>
  stage_id: <stage_id|none_yet>
  plan_snapshot_id: <plan_snapshot_id|none_yet>
  cycle_close_decision: <none_yet|commit|rescope|escalate>
  termination_posture: <undecided|continue|stop_planning_deliverable|stop_goal_saturated|stop_escalation_halt>
  post_close_invalidation: <none|target_drift|snapshot_drift|blocker_reopen>
  working_goal_ref: <working_goal_ref>
  source_packet_ref: <source_packet_ref>
  research_synthesis_ref: <research_synthesis_ref|none_yet>
  evidence_packet_ref: <evidence_packet_ref|none_yet>
  source_fingerprint: <source_fingerprint>
  target_fingerprint: <target_fingerprint>
  open_write_claims: <open_write_claims>
  resume_entry_state: <research|planning|cycle_decision|goal_reassessment|run_decision>
  parent_cycle_id: <parent_cycle_id|absent_when_not_newborn>
  parent_run_decision_handoff_ref: <parent_handoff_ref|absent_when_not_newborn>
```

## Sealed Handoff Row Templates

```yaml
planning_row_template:
  pre_terminal:
    resume_entry_state: planning
    required_present_refs:
      - source_packet_ref
      - research_synthesis_ref
      - plan_snapshot_id
    stage_id_semantics: current_stage_from_authoritative_revised_plan
    required_fixed_fields:
      cycle_close_decision: none_yet
      termination_posture: undecided
      evidence_packet_ref: none_yet
      post_close_invalidation: none
    required_absent_fields:
      - parent_cycle_id
      - parent_run_decision_handoff_ref
  terminal_planning_deliverable:
    resume_entry_state: planning
    required_present_refs:
      - source_packet_ref
      - research_synthesis_ref
      - plan_snapshot_id
    stage_id_semantics: current_stage_from_authoritative_revised_plan
    required_fixed_fields:
      cycle_close_decision: none_yet
      termination_posture: stop_planning_deliverable
      evidence_packet_ref: none_yet
      post_close_invalidation: none
      open_write_claims: []
    required_absent_fields:
      - parent_cycle_id
      - parent_run_decision_handoff_ref

cycle_decision_row_template:
  resume_entry_state: cycle_decision
  required_present_refs:
    - source_packet_ref
    - research_synthesis_ref
    - plan_snapshot_id
  allowed_evidence_packet_ref: <concrete_fresh|none_yet>
  required_fixed_fields:
    cycle_close_decision: none_yet
    termination_posture: undecided
    post_close_invalidation: none
    open_write_claims: []
  required_absent_fields:
    - parent_cycle_id
    - parent_run_decision_handoff_ref

goal_reassessment_row_template:
  resume_entry_state: goal_reassessment
  required_present_refs:
    - source_packet_ref
    - plan_snapshot_id
  allowed_evidence_packet_ref: <concrete|none_yet>
  required_fixed_fields:
    research_synthesis_ref: none_yet
    cycle_close_decision: <same_fixed_cycle_close_decision_ref_preserved_verbatim_from_cycle_decision>
    termination_posture: undecided
    post_close_invalidation: none
    open_write_claims: []
  stage_id_semantics: most_recently_closed_stage
  required_absent_fields:
    - parent_cycle_id
    - parent_run_decision_handoff_ref

run_decision_row_template:
  pre_terminal:
    resume_entry_state: run_decision
    required_present_refs:
      - source_packet_ref
      - research_synthesis_ref
      - plan_snapshot_id
    allowed_evidence_packet_ref: <concrete|none_yet>
    required_fixed_fields:
      cycle_close_decision: <same_fixed_cycle_close_decision_ref_preserved_verbatim_from_goal_reassessment>
      termination_posture: undecided
      post_close_invalidation: none
      open_write_claims: []
    stage_id_semantics: most_recently_closed_stage
    required_absent_fields:
      - parent_cycle_id
      - parent_run_decision_handoff_ref
  stop_goal_saturated_terminal:
    resume_entry_state: run_decision
    required_present_refs:
      - source_packet_ref
      - research_synthesis_ref
      - plan_snapshot_id
    allowed_evidence_packet_ref: <concrete|none_yet>
    required_fixed_fields:
      cycle_close_decision: <same_fixed_cycle_close_decision_ref_preserved_verbatim_from_goal_reassessment>
      termination_posture: stop_goal_saturated
      post_close_invalidation: none
      open_write_claims: []
    stage_id_semantics: most_recently_closed_stage
    required_absent_fields:
      - parent_cycle_id
      - parent_run_decision_handoff_ref
  stop_escalation_halt_terminal:
    resume_entry_state: run_decision
    required_present_refs:
      - source_packet_ref
      - research_synthesis_ref
      - plan_snapshot_id
    allowed_evidence_packet_ref: <concrete|none_yet>
    required_fixed_fields:
      cycle_close_decision: escalate
      termination_posture: stop_escalation_halt
      post_close_invalidation: none
      open_write_claims: []
    stage_id_semantics: most_recently_closed_stage
    required_absent_fields:
      - parent_cycle_id
      - parent_run_decision_handoff_ref

newborn_research_row_template:
  resume_entry_state: research
  required_present_refs:
    - source_packet_ref
    - parent_cycle_id
    - parent_run_decision_handoff_ref
  required_fixed_fields:
    stage_id: none_yet
    plan_snapshot_id: none_yet
    research_synthesis_ref: none_yet
    evidence_packet_ref: none_yet
    cycle_close_decision: none_yet
    termination_posture: continue
    post_close_invalidation: none
    open_write_claims: []

post_close_invalidation_restore_row_template:
  legal_source_resume_entry_state: <goal_reassessment|run_decision>
  required_present_refs:
    - source_packet_ref
    - plan_snapshot_id
    - evidence_packet_ref
  required_fixed_fields:
    cycle_close_decision: commit
    open_write_claims: []
    post_close_invalidation: <target_drift|snapshot_drift|blocker_reopen>
  required_absent_fields:
    - parent_cycle_id
    - parent_run_decision_handoff_ref
  lineage_rules:
    - stored resume_entry_state remains the superseded `goal_reassessment|run_decision`
    - stored resume_entry_state is lineage-only and not directly dispatchable
    - `cycle_id`, `stage_id`, `plan_snapshot_id`, `cycle_close_decision`, `termination_posture`, `resume_entry_state`, and referenced artifact ids inherit from the superseded lineage except where fixed fields above require the same value explicitly
    - only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ from the superseded post-close lineage
    - next cold-start route is mismatch-routed `verify` in the same `cycle_id` and `stage_id`
```

## Successor Handoff Template Selector

```yaml
successor_handoff_template_selector:
  integrate_plan:
    continue_execution: planning_row_template.pre_terminal
    planning_deliverable_complete: planning_row_template.terminal_planning_deliverable
  integrate_verify: cycle_decision_row_template
  cycle_decision:
    rework: planning_row_template.pre_terminal
    commit: goal_reassessment_row_template
    rescope: goal_reassessment_row_template
    escalate: goal_reassessment_row_template
  goal_reassessment:
    run_decision: run_decision_row_template.pre_terminal
  run_decision:
    continue: newborn_research_row_template
    stop_goal_saturated: run_decision_row_template.stop_goal_saturated_terminal
    stop_escalation_halt: run_decision_row_template.stop_escalation_halt_terminal
  post_close_invalidation_restore: post_close_invalidation_restore_row_template
```

Resume-entry overlays:

- `planning_overlay`
  - pre-terminal template: `planning_row_template.pre_terminal`
  - terminal planning-deliverable template: `planning_row_template.terminal_planning_deliverable`
- `cycle_decision_overlay`
  - template: `cycle_decision_row_template`
- `goal_reassessment_overlay`
  - template: `goal_reassessment_row_template`
- `run_decision_overlay`
  - pre-terminal template: `run_decision_row_template.pre_terminal`
  - `stop_goal_saturated` template: `run_decision_row_template.stop_goal_saturated_terminal`
  - `stop_escalation_halt` template: `run_decision_row_template.stop_escalation_halt_terminal`
- `newborn_research_overlay`
  - template: `newborn_research_row_template`
- `post_close_invalidation_restore_overlay`
  - template: `post_close_invalidation_restore_row_template`

## Next Reflection

If Stage 7 passes challenge, the next step is to reflect validated packet templates into:

- [SKILL.md](../SKILL.md)
- repo-local or personal agent asset files only where needed
