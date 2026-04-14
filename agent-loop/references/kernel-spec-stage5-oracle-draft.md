# Stage 5 Oracle Draft

This draft turns the Stage 1-4 kernel into falsifiable dry-run oracles.

It does not finalize worker packets, challenger packets, verifier packets, or public skill reflection.

It assumes [kernel-spec-stage1-3-draft.md](./kernel-spec-stage1-3-draft.md) is the source-of-truth kernel for lifecycle, handoff, evidence, and worker ownership behavior.

If Stage 5 passes, the next downstream packet-contract work lives in [kernel-spec-stage6-packets-draft.md](./kernel-spec-stage6-packets-draft.md).

## Stage 5 Goal

Stage 5 exists to prove that the Stage 1-4 kernel can be exercised without inventing new behavior.

A Stage 5 oracle is valid only when:

- every scenario maps to named kernel clauses
- every scenario can pass or fail from observable artifacts and transitions
- every scenario names explicit forbidden shortcuts
- no scenario relies on narrative agent self-report as decisive proof

## Oracle Scenario Schema

Every Stage 5 scenario must provide:

- `scenario_id`
- `title`
- `kernel_targets`
- `preconditions`
- `injected_fault`
- `expected_transitions`
- `required_artifact_mutations`
- `minimum_evidence`
- `expected_decision`
- `forbidden_shortcuts`
- `exact_fail_conditions`

When a scenario permits non-authoritative draft visibility before seal success, it must also provide:

- `allowed_draft_visibility`

## Oracle Evaluation Rules

- The oracle may trust only sealed handoffs, authoritative snapshots, evidence defined by the kernel, and fresh preflight against those artifacts.
- Draft snapshots and unsealed outputs are never authoritative.
- If a scenario outcome depends on undefined behavior, the scenario fails and the kernel must be sharpened.
- Any scenario that relies on a sealed `handoff_packet` must require the full universal handoff schema in addition to any row-specific resume fields.
- State-conditional `handoff_packet` fields must be absent when not permitted. In particular, `parent_cycle_id` and `parent_run_decision_handoff_ref` are legal only on stored newborn-cycle `research`.
- In failure-injected scenarios, the named injected fault may be used as scenario-harness evidence that an attempted failure path was exercised; outcome proof must still come from authoritative state and absence or presence of externally visible successor state.
- `expected_transitions` must describe controller routing only. If the scenario is purely about legality, claim state, or artifact mutation, it must say `no controller transition`.
- `required_artifact_mutations` must be checkable from authoritative artifacts or explicit rejection events.
- Side effects, claim-state changes, and audit mutations belong in `required_artifact_mutations`, not in `expected_transitions`.
- `exact_fail_conditions` must be strong enough that a narrative summary cannot pass the scenario.
- If a scenario grants draft visibility before seal success, `allowed_draft_visibility` must enumerate the visible draft refs and prove they remain non-authoritative and non-dispatchable until a later legal seal succeeds.

## Conformance Matrix

| Kernel Requirement | Scenario IDs |
| --- | --- |
| invalid-source intake | `S5-001` |
| canonical direct newborn `research` dispatch | `S5-002` |
| canonical direct `planning` dispatch | `S5-003` |
| canonical direct `cycle_decision` dispatch | `S5-004` |
| canonical direct `goal_reassessment` dispatch | `S5-005` |
| canonical direct `run_decision` dispatch | `S5-006`, `S5-018` |
| `stale_source -> run_bootstrap` | `S5-007` |
| `stale_target_pre_verify -> research` | `S5-008` |
| `stale_cycle_decision_evidence -> verify` | `S5-009` |
| post-close invalidation to same-cycle `verify` | `S5-010`, `S5-021`, `S5-038` |
| post-`continue` child-void restore to parent lineage | `S5-011` |
| `integrate_plan` handoff seal and activation | `S5-012` |
| terminal planning-deliverable cold-start closure | `S5-045` |
| exact-three-viewpoint research completeness for planning and run-level decisions | `S5-003`, `S5-016`, `S5-017`, `S5-034` |
| `integrate_verify` handoff seal and activation | `S5-013` |
| seal-failure authority fallback | `S5-041` |
| seal-point-specific draft visibility permission | `S5-041` |
| `cycle_decision -> planning` via `rework` | `S5-014` |
| `cycle_decision -> goal_reassessment` via `commit|rescope|escalate` | `S5-015`, `S5-036`, `S5-037` |
| `goal_reassessment -> run_decision` | `S5-016` |
| `run_decision -> research` via `continue` | `S5-017` |
| terminal `run_decision` stop seal | `S5-018` |
| blocking close auto-reopen on target drift | `S5-019` |
| blocking close auto-reopen on snapshot drift | `S5-020` |
| stale evidence mutation after close | `S5-021`, `S5-038` |
| finding dedupe and supersession lineage | `S5-022` |
| pre-verify legal and illegal close decisions | `S5-023` |
| ownership-unit comparability before claim admission | `S5-042` |
| pairwise parallel-safe claims | `S5-024` |
| write/write overlap forcing serialization | `S5-025` |
| write/read overlap forcing serialization | `S5-026` |
| undeclared write rejection | `S5-027` |
| cold-start planning recovery via replacement claim on newer snapshot | `S5-028`, `S5-043` |
| explicit planning-deliverable completion after first `integrate_plan` seal | `S5-044` |
| claim republish lineage and legal claim status transitions | `S5-028`, `S5-039` |
| timeout or disappearance without implicit auto-close | `S5-029` |
| stale output after claim closure | `S5-030` |
| stale output after snapshot supersession | `S5-031` |
| stale worker claim invalidation after snapshot supersession | `S5-040` |
| derived-artifact disagreement with latest sealed handoff | `S5-032` |
| `continue` legality | `S5-017`, `S5-033` |
| `stop_goal_saturated` legality | `S5-018`, `S5-034` |
| `stop_escalation_halt` legality | `S5-018`, `S5-035` |

## Scenario Catalog

### S5-001 invalid_source_abort

- `kernel_targets`: `run_bootstrap`, invalid-source abort
- `preconditions`: no sealed handoff; unreadable or invalid source input
- `injected_fault`: provide unreadable path or invalid source document
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: no authoritative handoff seal
- `minimum_evidence`: failed source resolution
- `expected_decision`: `invalid_source`
- `forbidden_shortcuts`: opening a run; sealing `research`
- `exact_fail_conditions`: any `cycle_id` minted or any handoff sealed

### S5-002 newborn_research_direct_dispatch

- `kernel_targets`: canonical stored newborn `research`
- `preconditions`: latest sealed handoff is newborn-cycle `research`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> research`
- `required_artifact_mutations`: none before `research`
- `minimum_evidence`: sealed newborn `research` handoff with concrete `source_packet_ref`, concrete `parent_cycle_id`, concrete `parent_run_decision_handoff_ref`, `stage_id=none_yet`, `plan_snapshot_id=none_yet`, `research_synthesis_ref=none_yet`, `evidence_packet_ref=none_yet`, `cycle_close_decision=none_yet`, `termination_posture=continue`, `post_close_invalidation=none`, and empty `open_write_claims`
- `expected_decision`: direct dispatch to `research`
- `forbidden_shortcuts`: direct `planning`; direct `verify`
- `exact_fail_conditions`: any dispatch target other than `research`, or any required newborn-cycle handoff field is missing or has the wrong `none_yet|continue|empty` value

### S5-003 planning_direct_dispatch

- `kernel_targets`: canonical direct `planning` dispatch
- `preconditions`: latest sealed handoff stores `resume_entry_state=planning`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> planning`
- `required_artifact_mutations`: none before dispatch
- `minimum_evidence`: sealed `planning` handoff with concrete `source_packet_ref`, concrete `research_synthesis_ref`, concrete `plan_snapshot_id`, `evidence_packet_ref=none_yet`, `cycle_close_decision=none_yet`, and `termination_posture=undecided`, plus a referenced `research_synthesis` whose `research_viewpoint_set` is exactly `architecture_dependency`, `failure_verification`, and `goal_efficiency`
- `expected_decision`: direct dispatch to `planning`
- `forbidden_shortcuts`: direct `execute`; direct `verify`
- `exact_fail_conditions`: any dispatch target other than `planning`, any required planning-row handoff field is missing or has the wrong `none_yet|undecided` value, `parent_cycle_id|parent_run_decision_handoff_ref` appears on a non-newborn handoff, or the referenced `research_synthesis` omits or duplicates one of the required research viewpoints

### S5-004 cycle_decision_direct_dispatch

- `kernel_targets`: canonical direct `cycle_decision` dispatch
- `preconditions`: latest sealed handoff stores `resume_entry_state=cycle_decision`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> cycle_decision`
- `required_artifact_mutations`: none before dispatch
- `minimum_evidence`: sealed `cycle_decision` handoff with concrete `source_packet_ref`, concrete `research_synthesis_ref`, concrete `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet`, `cycle_close_decision=none_yet`, `termination_posture=undecided`, empty `open_write_claims`, and fresh evidence when `evidence_packet_ref` is concrete
- `expected_decision`: direct dispatch to `cycle_decision`
- `forbidden_shortcuts`: direct `goal_reassessment`; mismatch-routed `verify` without stale evidence
- `exact_fail_conditions`: stale evidence still dispatches directly to `cycle_decision`, any required cycle-decision-row handoff field is missing or has the wrong `none_yet|undecided|empty` value, or `parent_cycle_id|parent_run_decision_handoff_ref` appears on a non-newborn handoff

### S5-005 goal_reassessment_direct_dispatch

- `kernel_targets`: canonical direct `goal_reassessment` dispatch
- `preconditions`: latest sealed handoff stores `resume_entry_state=goal_reassessment`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> goal_reassessment`
- `required_artifact_mutations`: none before dispatch
- `minimum_evidence`: sealed `goal_reassessment` handoff with concrete `source_packet_ref`, `research_synthesis_ref=none_yet`, concrete `cycle_id`, concrete `stage_id` for the most recently closed stage, concrete `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet`, concrete `cycle_close_decision`, `termination_posture=undecided`, `post_close_invalidation=none`, and empty `open_write_claims`
- `expected_decision`: direct dispatch to `goal_reassessment`
- `forbidden_shortcuts`: direct `run_decision` without fresh reassessment
- `exact_fail_conditions`: any dispatch target other than `goal_reassessment`, any carried `open_write_claims`, any required goal-reassessment-row handoff field is missing or has the wrong `none_yet|undecided|empty` value, or `parent_cycle_id|parent_run_decision_handoff_ref` appears on a non-newborn handoff

### S5-006 run_decision_direct_dispatch

- `kernel_targets`: canonical direct `run_decision` dispatch
- `preconditions`: latest sealed handoff stores pre-terminal `run_decision`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> run_decision`
- `required_artifact_mutations`: none before dispatch
- `minimum_evidence`: sealed `run_decision` handoff with concrete `source_packet_ref`, concrete `research_synthesis_ref`, concrete `cycle_id`, concrete `stage_id` for the most recently closed stage, concrete `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet`, concrete `cycle_close_decision`, `termination_posture=undecided`, `post_close_invalidation=none`, and empty `open_write_claims`
- `expected_decision`: direct dispatch to `run_decision`
- `forbidden_shortcuts`: direct `research` without `continue`
- `exact_fail_conditions`: any dispatch target other than `run_decision`, any carried `open_write_claims`, any required run-decision-row handoff field is missing or has the wrong `undecided|none|empty` value, or `parent_cycle_id|parent_run_decision_handoff_ref` appears on a non-newborn handoff

### S5-007 stale_source_reroute

- `kernel_targets`: resume mismatch `stale_source`
- `preconditions`: sealed handoff exists
- `injected_fault`: source fingerprint mismatch
- `expected_transitions`: `run_bootstrap -> cycle_ready -> run_bootstrap`
- `required_artifact_mutations`: no direct resume dispatch
- `minimum_evidence`: sealed handoff source fingerprint and fresh preflight mismatch
- `expected_decision`: mismatch class `stale_source`
- `forbidden_shortcuts`: direct `planning`; direct `research`
- `exact_fail_conditions`: any direct resume dispatch occurs

### S5-008 stale_target_pre_verify_to_research

- `kernel_targets`: resume mismatch `stale_target_pre_verify`
- `preconditions`: sealed `planning` handoff with carried open claims
- `injected_fault`: target fingerprint drift before verify evidence exists
- `expected_transitions`: `run_bootstrap -> cycle_ready -> research`
- `required_artifact_mutations`: carried claims become non-dispatchable; next `integrate_plan` invalidates, supersedes, or republishes them
- `minimum_evidence`: sealed `planning` handoff, open claims, target drift, `evidence_packet_ref=none_yet`
- `expected_decision`: mismatch class `stale_target_pre_verify`
- `forbidden_shortcuts`: direct `planning`; worker re-entry before `integrate_plan`
- `exact_fail_conditions`: any carried claim dispatches before `integrate_plan` seal

### S5-009 stale_cycle_decision_evidence_to_verify

- `kernel_targets`: `stale_cycle_decision_evidence`
- `preconditions`: sealed `cycle_decision` handoff with concrete evidence
- `injected_fault`: evidence becomes stale against active snapshot or target
- `expected_transitions`: `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: none before verify dispatch
- `minimum_evidence`: sealed `cycle_decision` handoff, concrete stale evidence
- `expected_decision`: mismatch class `stale_cycle_decision_evidence`
- `forbidden_shortcuts`: direct `cycle_decision`
- `exact_fail_conditions`: stale evidence still dispatches to `cycle_decision`

### S5-010 post_close_blocker_reopen_to_verify

- `kernel_targets`: post-close invalidation from `goal_reassessment|run_decision`
- `preconditions`: latest sealed handoff stores `resume_entry_state=goal_reassessment|run_decision`, `cycle_close_decision=commit`, concrete `cycle_id`, concrete `stage_id`, concrete `plan_snapshot_id`, concrete `evidence_packet_ref`, and `post_close_invalidation=blocker_reopen`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: none during routing; the latest sealed handoff already carries `post_close_invalidation=blocker_reopen`; compared with the superseded post-close handoff, only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ
- `minimum_evidence`: latest sealed handoff with `post_close_invalidation=blocker_reopen` plus concrete close-state refs
- `expected_decision`: mismatch class `post_close_invalidation`
- `forbidden_shortcuts`: direct `goal_reassessment`; direct `run_decision`; opening a new cycle
- `exact_fail_conditions`: any dispatch target other than same-cycle `verify`, any `continue|stop` becomes externally visible before same-cycle re-close, or the invalidation supersession rewrites any handoff field other than `source_fingerprint`, `target_fingerprint`, or `post_close_invalidation`

### S5-011 post_continue_child_void_restore

- `kernel_targets`: post-`continue` late invalidation restore
- `preconditions`: newborn `research` handoff sealed after `continue`
- `injected_fault`: late parent target drift, snapshot drift, or blocker reopen
- `expected_transitions`: `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: restored handoff clones the referenced parent handoff's control fields and referenced artifact ids verbatim; child handoff is superseded; the provisional child `cycle_id` is absent from the restored handoff
- `minimum_evidence`: newborn `research` handoff with concrete `parent_run_decision_handoff_ref`
- `expected_decision`: `post_close_invalidation`
- `forbidden_shortcuts`: child `research`; child `planning`
- `exact_fail_conditions`: child cycle remains dispatchable after late parent invalidation, or the restored handoff rewrites any parent control field or referenced artifact id instead of restoring it verbatim

### S5-012 integrate_plan_activation_switch

- `kernel_targets`: `integrate_plan` publication barrier
- `preconditions`: research and plan-challenge outputs ready; no blocker forces `integrate_plan -> cycle_decision` before execution
- `injected_fault`: none
- `expected_transitions`: `plan_challenge -> integrate_plan -> execute`
- `required_artifact_mutations`: current-cycle `research_synthesis` published; new authoritative snapshot and sealed `planning` handoff published together at the barrier
- `minimum_evidence`: sealed `planning` handoff referencing the newly published snapshot
- `expected_decision`: executable activation changes only at handoff seal
- `forbidden_shortcuts`: workers act on unsealed snapshot
- `exact_fail_conditions`: draft snapshot becomes executable before handoff seal

### S5-013 integrate_verify_activation_switch

- `kernel_targets`: `integrate_verify` publication barrier
- `preconditions`: either a fresh current-pass `verification_candidate` with fresh exact-three `verify_current_pass` challenge results keyed by `architecture_dependency`, `failure_verification`, and `goal_efficiency`, or a concrete authoritative `evidence_packet_ref` with fresh exact-three `post_close_revalidation|cold_start_revalidation` challenge results keyed by the same viewpoints, is ready
- `injected_fault`: none
- `expected_transitions`: `verify_challenge -> integrate_verify -> cycle_decision`
- `required_artifact_mutations`: evidence packet published or refreshed from the legal `integrate_verify` review target; new authoritative snapshot sealed if executable instructions or embedded claim state changed; the consumed verify challenge set must be exact-three, `phase=verify_phase`, and either:
  - `challenge_review_mode=verify_current_pass` targeted to the same current `verification_candidate`, or
  - `challenge_review_mode=post_close_revalidation|cold_start_revalidation` targeted to the same authoritative `evidence_packet_ref`
- `minimum_evidence`: either concrete current `verification_candidate` plus exact-three verify-current-pass challenge results targeted to that verification artifact, or concrete authoritative `evidence_packet_ref` plus exact-three revalidation challenge results targeted to that evidence artifact, together with sealed `cycle_decision` handoff and authoritative snapshot linkage
- `expected_decision`: executable activation changes only at handoff seal
- `forbidden_shortcuts`: claim-state mutation without newly sealed authoritative snapshot
- `exact_fail_conditions`: open-claim set changes without a newly sealed authoritative snapshot, `integrate_verify` succeeds without either a concrete current `verification_candidate` or a concrete authoritative `evidence_packet_ref`, or the consumed verify challenge set is missing a viewpoint, uses `phase!=verify_phase`, mixes current-pass and revalidation modes, or targets a review artifact other than the legal current-pass or revalidation target for the active subcase

### S5-014 cycle_decision_rework_path

- `kernel_targets`: `rework`
- `preconditions`: verify evidence concrete; required plan change stays inside the same `stage_id` boundary and does not require new control authority
- `injected_fault`: local failing gate
- `expected_transitions`: `cycle_decision -> planning`
- `required_artifact_mutations`: sealed `planning` handoff with the same `cycle_id`, the same `stage_id`, and `cycle_close_decision=none_yet`
- `minimum_evidence`: `S2` or stronger plus concrete verify evidence and a bounded same-stage plan change
- `expected_decision`: `rework`
- `forbidden_shortcuts`: `commit`; `goal_reassessment`
- `exact_fail_conditions`: `rework` emitted without concrete verify evidence, or `rework` emitted when the required fix crosses the current `stage_id` boundary or unresolved conflict should force `rescope|escalate`

### S5-015 cycle_decision_commit_close_path

- `kernel_targets`: `commit`
- `preconditions`: `cycle_decision` entered legally; `evidence_packet_ref` is concrete and fresh; no blocking finding remains open
- `injected_fault`: none
- `expected_transitions`: `cycle_decision -> goal_reassessment`
- `required_artifact_mutations`: sealed `goal_reassessment` handoff with concrete `cycle_close_decision=commit`, the same `cycle_id`, the same `stage_id`, and `post_close_invalidation=none`
- `minimum_evidence`: `S5`
- `expected_decision`: `commit`
- `forbidden_shortcuts`: direct `run_decision`; `commit` while any blocking finding remains open
- `exact_fail_conditions`: `commit` accepted with stale or missing verify evidence, any open blocking finding, or any close path that skips `goal_reassessment`

### S5-016 goal_reassessment_bridge

- `kernel_targets`: `goal_reassessment -> run_decision`
- `preconditions`: cycle closed through one of three explicit subcases: incoming `cycle_close_decision=commit`, incoming `cycle_close_decision=rescope`, or incoming `cycle_close_decision=escalate`
- `injected_fault`: none
- `expected_transitions`: `goal_reassessment -> run_decision`
- `required_artifact_mutations`: fresh `research_synthesis` published before `run_decision` seal, with exact `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}` and concrete lane refs; in each subcase the sealed `run_decision` handoff preserves the incoming concrete `cycle_close_decision` verbatim and sets `termination_posture=undecided`
- `minimum_evidence`: fresh reassessment output backed by a fresh exact-three-viewpoint `research_synthesis`
- `expected_decision`: pre-terminal `run_decision`
- `forbidden_shortcuts`: `run_decision` without fresh reassessment
- `exact_fail_conditions`: no fresh `research_synthesis` published for the run-close attempt, the fresh `research_synthesis` omits or duplicates one of the required research viewpoints, or any `commit|rescope|escalate` subcase fails to preserve the incoming concrete `cycle_close_decision` verbatim

### S5-017 run_decision_continue

- `kernel_targets`: `continue`
- `preconditions`: reassessment complete; at least one admissible improvement candidate or one remaining incomplete `required_for_success` stage still justifies keeping the run open
- `injected_fault`: none
- `expected_transitions`: `run_decision -> research`
- `required_artifact_mutations`: newborn `research` handoff sealed with new `cycle_id` only when fresh exact-three-viewpoint research provides `S4` evidence and explicit evidence refs for at least one admissible improvement candidate or at least one remaining incomplete `required_for_success` stage in the latest authoritative `revised_plan`
- `minimum_evidence`: fresh exact-three-viewpoint `S4` research, explicit `counter_check.admissible_candidate_result`, explicit `counter_check.remaining_required_stage_result`, exact `research_viewpoint_set`, and explicit evidence refs showing at least one admissible improvement candidate or at least one remaining incomplete `required_for_success` stage in the latest authoritative `revised_plan`
- `expected_decision`: `continue`
- `forbidden_shortcuts`: `continue` while unresolved `escalate`; `continue` under revalidation requirement
- `exact_fail_conditions`: new cycle opens while post-close invalidation remains unresolved, `continue` is accepted from research that omits or duplicates one of the required viewpoints, or `continue` is accepted below the fresh `S4` evidence floor or without explicit evidence refs for an admissible improvement candidate or remaining incomplete `required_for_success` stage

### S5-018 terminal_run_decision_stop_seal_and_resume

- `kernel_targets`: terminal stop seal
- `preconditions`: `run_decision` reached legally
- `injected_fault`: none
- `expected_transitions`: sealing subcase `run_decision -> terminal stop`; cold-start subcase `run_bootstrap -> cycle_ready -> run_decision`
- `required_artifact_mutations`: terminal `run_decision` handoff sealed with `resume_entry_state=run_decision`, concrete `cycle_close_decision`, `termination_posture=stop_goal_saturated|stop_escalation_halt`, `post_close_invalidation=none`, empty `open_write_claims`, and no new-cycle reopening
- `minimum_evidence`: decision-specific stop evidence
- `expected_decision`: one stop posture
- `forbidden_shortcuts`: stop without terminal handoff
- `exact_fail_conditions`: run closes without a terminal `run_decision` handoff, the terminal handoff is missing any required terminal field, or any new cycle becomes reopenable from the sealed terminal state

### S5-019 blocking_reopen_on_target_drift

- `kernel_targets`: blocking reopen on target drift
- `preconditions`: blocking finding previously `closed` with `closure_evidence_level>=S4`, concrete `closure_snapshot_id`, and concrete `closure_target_fingerprint`; latest sealed handoff already crossed into `goal_reassessment|run_decision` with `cycle_close_decision=commit`
- `injected_fault`: target fingerprint drift after closure
- `expected_transitions`: `no controller transition`; next cold-start routing must be `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: finding `status=open`; `reopen_reason=target_drift`; concrete `reopened_from_snapshot_id`; appended `decision_ledger` reopen event; latest sealed `goal_reassessment|run_decision` handoff superseded with `post_close_invalidation=blocker_reopen`; compared with the superseded post-close handoff, only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ
- `minimum_evidence`: prior blocking closure, target mismatch, reopen event, and superseded post-close handoff
- `expected_decision`: blocker reopened
- `forbidden_shortcuts`: keeping `commit` legal
- `exact_fail_conditions`: blocker stays closed after target drift, the prior closure was not kernel-legal, no `decision_ledger` reopen event is recorded, `post_close_invalidation=blocker_reopen` is not sealed for the post-close lineage, any dispatch other than same-cycle `verify` becomes legal before re-close, or the invalidation supersession rewrites any handoff field other than `source_fingerprint`, `target_fingerprint`, or `post_close_invalidation`

### S5-020 blocking_reopen_on_snapshot_drift

- `kernel_targets`: blocking reopen on snapshot drift
- `preconditions`: blocking finding previously `closed` with `closure_evidence_level>=S4`, concrete `closure_snapshot_id`, and concrete `closure_target_fingerprint`; latest sealed handoff already crossed into `goal_reassessment|run_decision` with `cycle_close_decision=commit`
- `injected_fault`: snapshot superseded after closure
- `expected_transitions`: `no controller transition`; next cold-start routing must be `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: finding `status=open`; `reopen_reason=snapshot_drift`; concrete `reopened_from_snapshot_id`; appended `decision_ledger` reopen event; latest sealed `goal_reassessment|run_decision` handoff superseded with `post_close_invalidation=blocker_reopen`; compared with the superseded post-close handoff, only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ
- `minimum_evidence`: prior blocking closure, snapshot mismatch, reopen event, and superseded post-close handoff
- `expected_decision`: blocker reopened
- `forbidden_shortcuts`: keeping `commit` legal
- `exact_fail_conditions`: blocker stays closed after snapshot drift, the prior closure was not kernel-legal, no `decision_ledger` reopen event is recorded, `post_close_invalidation=blocker_reopen` is not sealed for the post-close lineage, any dispatch other than same-cycle `verify` becomes legal before re-close, or the invalidation supersession rewrites any handoff field other than `source_fingerprint`, `target_fingerprint`, or `post_close_invalidation`

### S5-021 stale_evidence_target_drift_after_close

- `kernel_targets`: stale evidence mutation after close
- `preconditions`: latest sealed handoff stores `resume_entry_state=goal_reassessment|run_decision`, `cycle_close_decision=commit`, concrete `plan_snapshot_id`, concrete `evidence_packet_ref`, and `post_close_invalidation=none`
- `injected_fault`: target fingerprint drift after close
- `expected_transitions`: `no controller transition`; next cold-start routing must be `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: `evidence_packet.freshness_status=stale`; `evidence_packet.stale_reason=target_drift`; appended `decision_ledger` stale-state event; latest sealed handoff superseded with `post_close_invalidation=target_drift`; compared with the superseded post-close handoff, only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ
- `minimum_evidence`: stale evidence event, active target mismatch, and superseded post-close handoff
- `expected_decision`: `post_close_invalidation=target_drift`
- `forbidden_shortcuts`: `continue`; `stop`
- `exact_fail_conditions`: stale close remains directly resumable, `continue|stop` stays legal, the stale-state mutation is not observable from authoritative artifacts, or the invalidation supersession rewrites any handoff field other than `source_fingerprint`, `target_fingerprint`, or `post_close_invalidation`

### S5-022 finding_dedupe_and_supersession

- `kernel_targets`: finding identity and supersession
- `preconditions`: multiple observations on related root cause
- `injected_fault`: new observation broadens or refines scope
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: finding reused, superseded, or minted according to the full identity rule, including `root_cause_hash`, `normalized_scope_id`, blocking posture, `origin_phase`, and concrete `superseded_by` lineage when scope changes on the same root cause
- `minimum_evidence`: compared `root_cause_hash`, `normalized_scope_id`, blocking posture, `origin_phase`, scope comparison, and any predecessor or successor linkage
- `expected_decision`: correct reuse or new `finding_id`
- `forbidden_shortcuts`: silent drop of prior finding
- `exact_fail_conditions`: wrong `finding_id` reuse, wrong minting of a new `finding_id`, missing predecessor or successor lineage on supersession, identity decisions that ignore blocking posture or `origin_phase`, or supersession without equal-or-stronger evidence

### S5-023 pre_verify_close_legality

- `kernel_targets`: pre-verify close matrix
- `preconditions`: `evidence_packet_ref=none_yet`
- `injected_fault`: request each candidate close token
- `expected_transitions`: legal subcases `cycle_decision -> goal_reassessment`; illegal subcases `no controller transition`
- `required_artifact_mutations`: illegal tokens rejected; legal `rescope|escalate` seals a `goal_reassessment` handoff
- `minimum_evidence`: no verify evidence
- `expected_decision`: `rescope|escalate` allowed, others denied
- `forbidden_shortcuts`: `commit`; `continue`; stop tokens
- `exact_fail_conditions`: any illegal token is accepted

### S5-024 parallel_safe_claims

- `kernel_targets`: parallel dispatch legality
- `preconditions`: two proposed claims on the same current executable `plan_snapshot_id` with distinct `slice_id`
- `injected_fault`: none
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: both claims remain `open` on same snapshot
- `minimum_evidence`: disjoint write scopes and no read/write conflicts
- `expected_decision`: parallel dispatch allowed
- `forbidden_shortcuts`: forced serialization without overlap
- `exact_fail_conditions`: non-overlapping claims treated as conflicting, duplicate `slice_id` claims are admitted on the same snapshot, or cross-snapshot lineage is mistaken for same-snapshot parallel legality

### S5-025 write_write_overlap_serialization

- `kernel_targets`: write/write overlap
- `preconditions`: one open claim already exists on the same current executable `plan_snapshot_id`
- `injected_fault`: second claim proposes overlapping `write_scope`
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: integrator serializes, supersedes, or re-scopes before opening the second claim
- `minimum_evidence`: non-empty `write_scope` intersection
- `expected_decision`: no parallel dispatch
- `forbidden_shortcuts`: concurrently opening both claims
- `exact_fail_conditions`: overlapping writers dispatch together, `escalate` is used as a claim-admission outcome for the not-yet-open second claim, or cross-snapshot lineage is mistaken for same-snapshot overlap

### S5-026 write_read_overlap_serialization

- `kernel_targets`: write/read overlap
- `preconditions`: one open claim already exists on the same current executable `plan_snapshot_id`
- `injected_fault`: second claim proposes `write_scope` intersecting first claim's `read_scope`, or vice versa
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: integrator serializes, supersedes, or re-scopes before opening the second claim
- `minimum_evidence`: non-empty write/read intersection
- `expected_decision`: no parallel dispatch
- `forbidden_shortcuts`: concurrently opening conflicting claims
- `exact_fail_conditions`: conflicting writer and reader dispatch together, `escalate` is used as a claim-admission outcome for the not-yet-open second claim, or cross-snapshot lineage is mistaken for same-snapshot overlap

### S5-027 undeclared_write_rejection

- `kernel_targets`: out-of-scope write rejection
- `preconditions`: claim is open and targets current snapshot
- `injected_fault`: worker output touches ownership unit outside declared `write_scope`
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: reject or escalate the output
- `minimum_evidence`: output diff plus declared `write_scope`
- `expected_decision`: merge denied
- `forbidden_shortcuts`: optimistic merge
- `exact_fail_conditions`: output merges despite undeclared write

### S5-028 planning_recovery_replacement_claim

- `kernel_targets`: cold-start planning recovery
- `preconditions`: sealed `planning` handoff; open claim exists on current snapshot
- `injected_fault`: cold-start interruption before worker completion
- `expected_transitions`: `run_bootstrap -> cycle_ready -> planning`
- `required_artifact_mutations`: newer snapshot sealed; prior claim closes as `superseded`; replacement claim opens with concrete `parent_claim_id` pointing to that superseded claim, a newer `plan_snapshot_id`, and `status=open`; `handoff_packet.open_write_claims` mirrors only the replacement open claim set
- `minimum_evidence`: sealed `planning` handoff and open claim mirror
- `expected_decision`: replacement claim published on newer snapshot
- `forbidden_shortcuts`: direct worker resume on old claim
- `exact_fail_conditions`: same claim re-enters execution without a newer sealed snapshot, without the parent claim becoming `superseded`, or without the replacement claim appearing as the only authoritative open claim for that `slice_id`

### S5-029 timeout_without_auto_close

- `kernel_targets`: timeout or disappearance
- `preconditions`: open claim exists
- `injected_fault`: worker times out or disappears
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: claim stays open but non-running until integrator supersedes or explicitly closes it
- `minimum_evidence`: timeout event and latest sealed snapshot
- `expected_decision`: no implicit auto-close
- `forbidden_shortcuts`: automatic `invalidated` or `merged`
- `exact_fail_conditions`: claim closes without integrator sealing

### S5-030 stale_output_after_claim_closure

- `kernel_targets`: stale output after claim closure
- `preconditions`: claim already closed
- `injected_fault`: late worker output arrives
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: output treated as stale evidence only
- `minimum_evidence`: closed claim plus late output
- `expected_decision`: merge denied
- `forbidden_shortcuts`: reopening claim from worker output
- `exact_fail_conditions`: closed-claim output regains merge authority

### S5-031 stale_output_after_snapshot_supersession

- `kernel_targets`: stale output after supersession
- `preconditions`: worker output produced against older snapshot
- `injected_fault`: snapshot superseded before output adoption
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: output remains stale evidence only and may inform audit, replanning, or a republished claim lineage; it may never be merged directly into the authoritative snapshot; any still-open claim on the superseded snapshot remains subject to `S5-040` before further dispatch
- `minimum_evidence`: output snapshot id older than authoritative snapshot
- `expected_decision`: direct merge denied
- `forbidden_shortcuts`: direct adoption into authoritative snapshot
- `exact_fail_conditions`: stale output merges directly into the authoritative snapshot for any reason, including through a replacement claim on a newer snapshot without explicit republish lineage

### S5-032 derived_artifact_disagreement

- `kernel_targets`: disagreement with latest sealed handoff
- `preconditions`: derived artifact conflicts with sealed handoff
- `injected_fault`: mutate derived state while sealed handoff remains unchanged
- `expected_transitions`: `no controller transition`; next resume routing must still follow the latest sealed handoff or the mismatch matrix
- `required_artifact_mutations`: disagreement becomes audit finding
- `minimum_evidence`: sealed handoff and contradictory derived artifact
- `expected_decision`: handoff-authoritative routing
- `forbidden_shortcuts`: routing from derived artifact instead of handoff
- `exact_fail_conditions`: derived artifact overrides sealed handoff for resume routing

### S5-033 continue_legality

- `kernel_targets`: `continue`
- `preconditions`: `run_decision` reached
- `injected_fault`: vary one of `research_synthesis.counter_check.admissible_candidate_result=none`, `research_synthesis.counter_check.remaining_required_stage_result=none|some`, unresolved `cycle_close_decision=escalate`, `post_close_invalidation!=none`, or fresh fingerprint or snapshot mismatch
- `expected_transitions`: legal subcase `run_decision -> research`; all illegal subcases `no controller transition`
- `required_artifact_mutations`: newborn `research` handoff sealed only when (`research_synthesis.counter_check.admissible_candidate_result=some` or `research_synthesis.counter_check.remaining_required_stage_result=some`), `cycle_close_decision!=escalate`, `post_close_invalidation=none`, fresh preflight matches the stored fingerprints and snapshot, and fresh exact-three-viewpoint research provides `S4` evidence plus explicit evidence refs for either at least one admissible improvement candidate or at least one remaining incomplete `required_for_success` stage in the latest authoritative `revised_plan`; if the injected fault is `post_close_invalidation!=none` or a fresh committed-close mismatch, this scenario only requires that `continue` be denied here, with any later `verify` reroute justified separately by `S5-010|S5-021|S5-038`
- `minimum_evidence`: fresh exact-three-viewpoint `S4` `research_synthesis`, explicit `counter_check.admissible_candidate_result`, explicit `counter_check.remaining_required_stage_result`, exact `research_viewpoint_set`, current `cycle_close_decision`, current `post_close_invalidation`, fresh fingerprint and snapshot preflight, and explicit evidence refs for at least one admissible improvement candidate or at least one remaining incomplete `required_for_success` stage
- `expected_decision`: `continue` accepted only under legal conditions
- `forbidden_shortcuts`: `continue` while unresolved `escalate`; `continue` under invalidation
- `exact_fail_conditions`: any new cycle opens when both `counter_check.admissible_candidate_result=none` and `counter_check.remaining_required_stage_result=none`, when `cycle_close_decision=escalate` remains unresolved, when `post_close_invalidation!=none`, when fresh preflight disagrees with the stored fingerprint or snapshot, when the consumed `research_synthesis` omits or duplicates one of the required viewpoints, or when `continue` is accepted below the fresh `S4` bar or without explicit evidence refs for an admissible improvement candidate or remaining incomplete `required_for_success` stage; or a legal `continue` is denied despite either `counter_check.admissible_candidate_result=some` or `counter_check.remaining_required_stage_result=some` and no other blocker

### S5-034 stop_goal_saturated_legality

- `kernel_targets`: `stop_goal_saturated`
- `preconditions`: `run_decision` reached
- `injected_fault`: vary blocker status, success-condition evidence, `research_synthesis.counter_check.admissible_candidate_result`, `research_synthesis.counter_check.remaining_required_stage_result`, `revised_plan.run_intent`, and post-close invalidation state
- `expected_transitions`: legal subcase `run_decision -> terminal stop`; all illegal subcases `no controller transition`
- `required_artifact_mutations`: terminal `run_decision` handoff with `termination_posture=stop_goal_saturated` and `post_close_invalidation=none` appears only when no blocking finding remains open, fresh exact-three-viewpoint research finds zero admissible candidates, `research_synthesis.counter_check.admissible_candidate_result=none`, and concrete success-condition evidence from authoritative kernel-defined artifacts shows the current success condition is satisfied; if `revised_plan.run_intent=implementation_oriented`, terminal stop also requires `research_synthesis.counter_check.remaining_required_stage_result=none` plus evidence that no incomplete `required_for_success` stage remains in the latest authoritative `revised_plan`; if the injected fault is `post_close_invalidation!=none` or a fresh committed-close mismatch, this scenario only requires that `stop_goal_saturated` be denied here, with any later `verify` reroute justified separately by `S5-010|S5-021|S5-038`
- `minimum_evidence`: `S5`, exact-three-viewpoint `research_synthesis`, `research_synthesis.counter_check.admissible_candidate_result=none`, `research_synthesis.counter_check.remaining_required_stage_result`, no open blocking findings, and concrete success-condition evidence from authoritative kernel-defined artifacts
- `expected_decision`: `stop_goal_saturated`
- `forbidden_shortcuts`: stop with open blockers; stop under mismatch
- `exact_fail_conditions`: goal-saturated stop accepted while any blocking finding remains open, while `post_close_invalidation!=none`, while fresh preflight disagrees with the stored fingerprint or snapshot, while success-condition evidence is missing or unsatisfied, while the consumed `research_synthesis` omits or duplicates one of the required viewpoints, while `research_synthesis.counter_check.admissible_candidate_result!=none`, or, for `revised_plan.run_intent=implementation_oriented`, while `research_synthesis.counter_check.remaining_required_stage_result!=none` or any incomplete `required_for_success` stage remains in the latest authoritative `revised_plan`

### S5-035 stop_escalation_halt_legality

- `kernel_targets`: `stop_escalation_halt`
- `preconditions`: unresolved `escalate` already crossed into `run_decision`
- `injected_fault`: none
- `expected_transitions`: `run_decision -> terminal stop`
- `required_artifact_mutations`: terminal `run_decision` handoff with `termination_posture=stop_escalation_halt`, `resume_entry_state=run_decision`, `cycle_close_decision=escalate`, and `post_close_invalidation=none`
- `minimum_evidence`: sealed unresolved escalate lineage that already crossed `cycle_decision -> goal_reassessment -> run_decision`
- `expected_decision`: `stop_escalation_halt`
- `forbidden_shortcuts`: pre-verify stop escalation halt; stop without unresolved `escalate`
- `exact_fail_conditions`: `stop_escalation_halt` accepted outside the `run_decision` unresolved-escalate bridge, accepted with `cycle_close_decision!=escalate`, or accepted while `post_close_invalidation!=none`

### S5-036 cycle_decision_rescope_close_path

- `kernel_targets`: `rescope`
- `preconditions`: `cycle_decision` entered legally; either `evidence_packet_ref=none_yet` or concrete evidence shows the current stage boundary or gate set no longer matches the active work
- `injected_fault`: explicit gate mismatch or changed constraint
- `expected_transitions`: `cycle_decision -> goal_reassessment`
- `required_artifact_mutations`: sealed `goal_reassessment` handoff with concrete `cycle_close_decision=rescope`, the same `cycle_id`, and the closing `stage_id`
- `minimum_evidence`: `S2` plus explicit gate mismatch or changed constraint
- `expected_decision`: `rescope`
- `forbidden_shortcuts`: direct `run_decision`; `rescope` without boundary or constraint change
- `exact_fail_conditions`: `rescope` accepted without concrete evidence of a changed stage boundary or constraint, or the close path skips `goal_reassessment`

### S5-037 cycle_decision_escalate_close_path

- `kernel_targets`: `escalate`
- `preconditions`: `cycle_decision` entered legally
- `injected_fault`: repeated blocker, unresolved conflict, or authority ambiguity
- `expected_transitions`: `cycle_decision -> goal_reassessment`
- `required_artifact_mutations`: sealed `goal_reassessment` handoff with concrete `cycle_close_decision=escalate`, the same `cycle_id`, and the closing `stage_id`
- `minimum_evidence`: `S2` plus repeated blocker, unresolved conflict, or authority ambiguity
- `expected_decision`: `escalate`
- `forbidden_shortcuts`: direct `run_decision`; optimistic `commit`
- `exact_fail_conditions`: `escalate` accepted without evidence of repeated blocker, unresolved conflict, or authority ambiguity, or the close path skips `goal_reassessment`

### S5-038 stale_evidence_snapshot_drift_after_close

- `kernel_targets`: stale evidence mutation after close
- `preconditions`: latest sealed handoff stores `resume_entry_state=goal_reassessment|run_decision`, `cycle_close_decision=commit`, concrete `plan_snapshot_id`, concrete `evidence_packet_ref`, and `post_close_invalidation=none`
- `injected_fault`: authoritative snapshot superseded after close
- `expected_transitions`: `no controller transition`; next cold-start routing must be `run_bootstrap -> cycle_ready -> verify`
- `required_artifact_mutations`: `evidence_packet.freshness_status=stale`; `evidence_packet.stale_reason=snapshot_drift`; appended `decision_ledger` stale-state event; latest sealed handoff superseded with `post_close_invalidation=snapshot_drift`; compared with the superseded post-close handoff, only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation` may differ
- `minimum_evidence`: stale evidence event, snapshot mismatch, and superseded post-close handoff
- `expected_decision`: `post_close_invalidation=snapshot_drift`
- `forbidden_shortcuts`: `continue`; `stop`
- `exact_fail_conditions`: stale close remains directly resumable, `continue|stop` stays legal, the stale-state mutation is not observable from authoritative artifacts, or the invalidation supersession rewrites any handoff field other than `source_fingerprint`, `target_fingerprint`, or `post_close_invalidation`

### S5-039 claim_republish_and_status_transition_matrix

- `kernel_targets`: claim republish lineage and legal claim status transitions
- `preconditions`: one claim is `open` on the current executable snapshot
- `injected_fault`: attempt legal and illegal claim transitions, including republish onto a newer snapshot
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: only integrator-sealed `open -> merged|rejected|invalidated|superseded|escalated` transitions are accepted; the republish subcase closes the parent claim as `superseded` and mints one replacement claim with concrete `parent_claim_id` and a newer `plan_snapshot_id`; terminal claims stay terminal; every seal must keep `handoff_packet.open_write_claims` exactly equal to the full `status=open` claim set embedded in the referenced `revised_plan`
- `minimum_evidence`: sealed claim history across the attempted transitions plus the authoritative `handoff_packet.open_write_claims` view for each seal
- `expected_decision`: legal transitions accepted; illegal transitions denied
- `forbidden_shortcuts`: worker self-transition; terminal-to-nonterminal transition; republish without parent lineage
- `exact_fail_conditions`: any non-integrator mutation moves a claim out of `open`, any illegal transition is accepted, a republish omits the superseded parent or the replacement `parent_claim_id`, or any handoff seal carries `open_write_claims` that do not exactly match the referenced plan's full open-claim set

### S5-040 stale_open_claim_after_snapshot_supersession

- `kernel_targets`: stale worker claim invalidation after snapshot supersession
- `preconditions`: one claim remains `open` on `plan_snapshot_id=old`; a newer authoritative snapshot is sealed
- `injected_fault`: attempt to keep dispatching the old open claim after supersession
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: the stale open claim becomes non-dispatchable immediately; the next sealed snapshot marks that old claim `invalidated` or `superseded`; if work is republished, only the replacement claim on the newer `plan_snapshot_id` may remain in `handoff_packet.open_write_claims`
- `minimum_evidence`: old open claim, newer sealed snapshot, and the next authoritative claim-state seal
- `expected_decision`: dispatch from the stale open claim is denied
- `forbidden_shortcuts`: dispatch from the old claim after supersession; keeping both old and replacement claims `open` for the same `slice_id`
- `exact_fail_conditions`: the old claim remains dispatchable after supersession, survives as `status=open` in the next authoritative claim set without a valid replacement lineage, or worker output from the stale claim is merged directly

### S5-041 seal_failure_authority_fallback

- `kernel_targets`: seal-failure authority fallback
- `preconditions`: either a previously sealed handoff and executable snapshot are authoritative, or a newborn-cycle `research` handoff is authoritative with `plan_snapshot_id=none_yet`; one legal seal point attempts a successor state at `integrate_plan|integrate_verify|cycle_decision|goal_reassessment|run_decision`
- `injected_fault`: the successor seal fails after draft publication or draft decision preparation
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: the prior authoritative handoff remains the latest resume artifact; if a prior sealed executable snapshot existed it remains the active executable source; if the failure occurs before the first `integrate_plan` seal, no executable snapshot becomes active and the newborn `research` handoff remains authoritative; publication-barrier subcases at `integrate_plan|integrate_verify` may leave unsealed draft successor artifacts, but those drafts may not become authoritative or dispatchable; decision-seal subcases at `cycle_decision|goal_reassessment|run_decision` may not leave any externally visible successor result
- `allowed_draft_visibility`: `integrate_plan|integrate_verify` may expose only the named draft publications from the attempted barrier bundle, marked explicitly as drafts and never as dispatchable or authoritative; `cycle_decision|goal_reassessment|run_decision` permit `visible_drafts=none`
- `minimum_evidence`: authoritative pre-state refs, the named injected failed attempt at a legal seal point, and absence of any newer sealed or authority-bearing successor state after that attempt
- `expected_decision`: prior authority preserved
- `forbidden_shortcuts`: dispatching from the failed successor draft; activating an unsealed snapshot
- `exact_fail_conditions`: any failed seal changes the authoritative handoff or executable snapshot, grants dispatch or executable authority to the attempted successor state, activates a first-cycle executable snapshot after a failed first `integrate_plan` seal, leaves an externally visible successor result after a failed `cycle_decision|goal_reassessment|run_decision` seal, or exposes any draft visibility outside the `allowed_draft_visibility` contract above

### S5-042 incomparable_scope_claim_admission_denial

- `kernel_targets`: ownership-unit comparability before claim admission
- `preconditions`: a proposed claim targets the current executable `plan_snapshot_id`, but its `read_scope` or `write_scope` cannot be compared for overlap against the current open-claim set
- `injected_fault`: attempt claim admission with incomparable ownership units
- `expected_transitions`: `no controller transition`
- `required_artifact_mutations`: claim admission is denied until the integrator narrows the scope or re-scopes the stage; no new `status=open` claim is published for that slice
- `minimum_evidence`: current open claims, proposed claim scopes, and proof that overlap comparability is unavailable
- `expected_decision`: claim not dispatchable
- `forbidden_shortcuts`: optimistic claim admission; worker dispatch before comparability is restored
- `exact_fail_conditions`: a claim opens or dispatches despite incomparable ownership units

### S5-043 planning_recovery_preflight_denial

- `kernel_targets`: cold-start planning recovery preflight legality
- `preconditions`: the latest sealed `planning` handoff exists after interruption
- `injected_fault`: vary one illegal recovery condition among claim not `open`, illegal or incomparable scope, or mismatch status requiring reroute
- `expected_transitions`: mismatch subcases follow the mismatch matrix; all other illegal recovery subcases `no controller transition`
- `required_artifact_mutations`: no replacement claim may be published until current snapshot, claim openness, scope legality, and mismatch status are revalidated
- `minimum_evidence`: latest sealed `planning` handoff plus the specific claim-status, scope-legality or scope-comparability, or mismatch artifact that makes recovery illegal
- `expected_decision`: recovery republish denied
- `forbidden_shortcuts`: replacement claim publication before preflight legality is restored
- `exact_fail_conditions`: a replacement claim is published despite non-open claim state, illegal or incomparable scope, or a mismatch status that should reroute control, or recovery is driven from any non-latest `planning` handoff

### S5-044 planning_deliverable_completion_legality

- `kernel_targets`: explicit planning-deliverable completion
- `preconditions`: immutable `request_intent=planning_deliverable_only`; the first `integrate_plan` seal of the run succeeded and published a challenge-reviewed authoritative `revised_plan` plus sealed `planning` handoff
- `injected_fault`: vary one of missing `planning_delivery_complete` event, attempted completion before `integrate_plan`, or `request_intent=end_to_end_progress`
- `expected_transitions`: legal subcase `integrate_plan -> terminal planning_delivery_complete`; illegal subcases `no controller transition`
- `required_artifact_mutations`: legal completion seals a terminal `planning` handoff with `termination_posture=stop_planning_deliverable`, records a concrete `planning_delivery_complete` event in `decision_ledger` referencing the active `plan_snapshot_id` and `working_goal`, and leaves no legal `execute`, worker dispatch, or cycle-close decision after that terminal seal
- `minimum_evidence`: immutable `request_intent`, sealed terminal `planning` handoff with `termination_posture=stop_planning_deliverable`, authoritative `revised_plan`, and the referenced `decision_ledger` completion event
- `expected_decision`: planning deliverable accepted only after the first challenge-reviewed authoritative `revised_plan` is sealed
- `forbidden_shortcuts`: stopping on planning-deliverable grounds before `integrate_plan`; inferring planning-deliverable intent from `source_packet` text alone; entering `execute` after legal planning-deliverable completion
- `exact_fail_conditions`: planning-deliverable completion is accepted before the first successful `integrate_plan` seal, accepted when `request_intent!=planning_deliverable_only`, accepted without a sealed terminal `planning` handoff or without a concrete `planning_delivery_complete` event, or followed by `execute`, worker dispatch, or any cycle-close decision in the same run

### S5-045 terminal_planning_deliverable_cold_start_closure

- `kernel_targets`: cold-start closure from terminal planning-deliverable handoff
- `preconditions`: latest sealed handoff stores `resume_entry_state=planning`, `termination_posture=stop_planning_deliverable`, concrete `plan_snapshot_id`, and `post_close_invalidation=none`
- `injected_fault`: none
- `expected_transitions`: `run_bootstrap -> cycle_ready -> terminal planning_delivery_complete`
- `required_artifact_mutations`: none; the run remains closed and no controller state becomes active again
- `minimum_evidence`: sealed terminal `planning` handoff with `termination_posture=stop_planning_deliverable`
- `expected_decision`: closed planning-deliverable run stays closed on cold start
- `forbidden_shortcuts`: direct dispatch back to `planning`; opening `execute`; opening a new cycle
- `exact_fail_conditions`: cold start resumes into `planning`, `execute`, `cycle_decision`, `goal_reassessment`, or `run_decision` from the sealed terminal planning-deliverable handoff
