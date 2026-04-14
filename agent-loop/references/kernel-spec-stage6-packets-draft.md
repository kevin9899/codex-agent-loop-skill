# Stage 6 Packet Draft

This draft turns the validated Stage 1-5 kernel into minimal role packets.

It does not finalize public skill reflection or repo-local agent assets yet.

It assumes these files are already authoritative for lifecycle and oracle behavior:

- [kernel-spec-stage1-3-draft.md](./kernel-spec-stage1-3-draft.md)
- [kernel-spec-stage5-oracle-draft.md](./kernel-spec-stage5-oracle-draft.md)

If Stage 6 passes, the next downstream template work lives in [kernel-spec-stage7-packet-templates-draft.md](./kernel-spec-stage7-packet-templates-draft.md).

## Stage 6 Goal

Stage 6 exists to define the smallest packet set that lets `$loop` run a highest-model multi-agent loop without leaking authority or bloating context.

Stage 6 is valid only when:

- every delegated role consumes a narrow packet instead of a broad transcript
- every packet names its authoritative input artifacts explicitly
- every packet names the output artifact it is allowed to produce
- no packet lets a delegated role invent controller transitions
- the main CLI thread stays orchestration-first and packet-driven
- the same packet set can support both plan challenge and verify challenge

## Global Packet Rules

- Before any delegated packet is emitted, the controller resolves one concrete strongest-model pin from the local runtime config plus the current local model catalog.
- All delegated lanes use that exact resolved hard pin for the full live invocation unless the user explicitly overrides it before dispatch.
- Emitting a packet is not sufficient by itself; the matching delegated `spawn_agent` call must also carry the same concrete `model` and `reasoning_effort` fields.
- The main CLI thread owns orchestration and may consume packet outputs, but it does not relax packet authority.
- Packets may reference only authoritative artifacts or explicitly named draft candidates from the current lane.
- Raw lane output is advisory until the integrator adopts it into an authoritative artifact.
- A delegated role may not mutate `handoff_packet`, `revised_plan`, `decision_ledger`, `evidence_packet`, or claim state directly.
- A delegated role may propose findings, candidate artifacts, diffs, or checks only within its packet contract.
- Every packet must fit within one current `run_id`, one current `cycle_id`, and at most one current `stage_id`.
- Every packet must name whether it is `planning_phase` or `verify_phase` when challenge semantics depend on phase.
- Any packet field described as a summary, excerpt, or probe must be a non-persistent derived view keyed to exact authoritative refs listed in `authoritative_inputs`.

## Common Packet Envelope

Every delegated packet must carry at least:

- `packet_id`
- `packet_kind`
- `model_policy=resolved_strongest_hard_pin`
- `resolved_model_slug`
- `resolved_reasoning_effort`
- `model_resolution_basis_ref`
- `dispatch_mode=bootstrap|resume`
- `run_id`
- `cycle_id`
- `stage_id` as concrete id or `none_yet`
- `plan_snapshot_id` as concrete id or `none_yet`
- `working_goal_ref`
- `source_packet_ref`
- `request_intent_ref`
- `authoritative_handoff_ref` as concrete ref or `none_yet`
- `authoritative_inputs`
- `required_outputs`
- `forbidden_actions`
- `completion_gate`

Required common rules:

- `authoritative_handoff_ref` must point to the latest sealed `handoff_packet`, except in `dispatch_mode=bootstrap` before the first seal where it must be `none_yet`
- `request_intent_ref` must point to the immutable per-run explicit-user-request artifact, not to source-document wording
- `request_intent_ref` must be one of `planning_deliverable_only|end_to_end_progress`
- `model_policy` must be `resolved_strongest_hard_pin`
- `resolved_model_slug` and `resolved_reasoning_effort` must be concrete whenever the controller successfully resolved the current strongest model pin before dispatch
- all delegated packets in the same live invocation must carry the same `resolved_model_slug` and `resolved_reasoning_effort` unless the user explicitly overrides before the next dispatch
- the delegated `spawn_agent` call that consumes the packet must pass `model=<resolved_model_slug>` and `reasoning_effort=<resolved_reasoning_effort>` explicitly
- any delegated output produced without the packet's concrete model pin, or on a weaker model/effort pair, is inadmissible
- `authoritative_inputs` must name exact artifact refs, not prose descriptions alone
- `forbidden_actions` must include any controller mutation the role is not allowed to perform
- `completion_gate` must be checkable from the packet output alone
- source content may inform planning, but it may never override `request_intent_ref`

Dispatch-opening packets must also carry:

- `preflight_result_ref`
- `dispatch_basis`

Additional dispatch-opening rules:

- `preflight_result_ref` must point to the fresh pre-dispatch legality result that already evaluated mismatch routing and newborn-child parent-lineage invalidation precedence
- `dispatch_basis` must name whether packet emission comes from `source_packet + fresh run bootstrap context` or from the latest sealed handoff after fresh preflight
- packet emission is illegal until the current `preflight_result_ref` authorizes the chosen dispatch target

## Packet Kinds

The minimum packet set is:

- `research_packet`
- `planning_packet`
- `challenge_packet`
- `worker_packet`
- `verification_packet`
- `integration_packet`

No other delegated packet kind is required at Stage 6.

## Research Packet

`research_packet` is used:

- before first plan lock
- after each cycle close through `commit|rescope|escalate`
- after a full current plan is exhausted

Exactly three `research_packet` emissions must occur per research phase, one per
`research_viewpoint`:

- `architecture_dependency`
- `failure_verification`
- `goal_efficiency`

The first `research_packet` pass is mandatory regardless of source shape. A source packet that
already looks like a plan, roadmap, authority note, or implementation checklist still enters the
same initial `research -> planning -> challenge -> integrate_plan` path before any
execution-stage dispatch becomes legal.

### Required Inputs

- latest sealed `handoff_packet` or bootstrap context when `authoritative_handoff_ref=none_yet`
- `working_goal_ref`
- `source_packet_ref`
- `research_viewpoint`
- current authoritative `revised_plan` snapshot when one exists
- exact stage refs plus optional derived `stage_view` when one exists
- `decision_ledger_ref` plus optional derived `decision_ledger_view`
- `evidence_packet_ref` plus optional derived `evidence_view` when verifying or reassessing after execution
- exact probe refs plus optional derived `probe_view`

### Required Outputs

- `research_synthesis_candidate`

That candidate must contain at least:

- `synthesis_mode=lane|merged`
- `research_viewpoint` when `synthesis_mode=lane`
- `research_viewpoint_set` when `synthesis_mode=merged`
- `lane_candidate_refs` when `synthesis_mode=merged`
- `phase`
- `current_state_findings`
- `goal_alignment_assessment`
- `admissible_candidates`
- `efficiency_opportunities`
- `risk_findings`
- `recommended_ordering_changes`
- `counter_check`

`phase` in `research_synthesis_candidate` must mirror the packet's `research_mode` exactly:

- `pre_plan`
- `post_stage`
- `goal_reassessment`

`counter_check` must contain at least:

- `admissible_candidate_result=some|none`
- `remaining_required_stage_result=some|none`
- `evidence_refs`
- `why_not_more`

Delegated `research_packet` emissions must produce `synthesis_mode=lane` with exactly one
concrete `research_viewpoint`.

A research phase is complete only when the main CLI has assembled one merged
`research_synthesis_candidate` with:

- `synthesis_mode=merged`
- `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`
- concrete `lane_candidate_refs` that map each required viewpoint to one lane-local candidate from
  the current research phase

`planning_packet` and run-level reassessment may consume fresh research only from that merged
candidate or from an authoritative `research_synthesis` produced from it.

When the latest authoritative `revised_plan` exists and `run_intent=implementation_oriented`,
`remaining_required_stage_result` must evaluate whether any incomplete `current_stage` or
`remaining_stage_queue` entry still carries `stage_obligation=required_for_success`.

### Forbidden Actions

- inventing a new `cycle_id`
- mutating the active `revised_plan`
- issuing `continue|stop`
- issuing `commit|rework|rescope|escalate`
- writing worker claims

## Planning Packet

`planning_packet` is used:

- after initial research
- after any accepted rework or rescope
- after post-stage fresh research updates remaining work

A prewritten plan inside `source_packet_ref` never bypasses `planning_packet`. It is reconstructed
into an authoritative `revised_plan_candidate` only after the initial research pass and remains
non-authoritative source evidence until `integrate_plan` seals the resulting `revised_plan`.

### Required Inputs

- latest sealed `handoff_packet` or bootstrap context when `authoritative_handoff_ref=none_yet`
- `working_goal_ref`
- `source_packet_ref`
- `request_intent_ref`
- merged `current-cycle research_synthesis_candidate` only for pre-`integrate_plan` planning in the current cycle
- latest authoritative `research_synthesis` for same-cycle rework, resumed planning, or historical context
- current authoritative `revised_plan` snapshot when one exists
- `decision_ledger_ref` plus optional derived `decision_ledger_view`
- exact stage refs plus optional derived `stage_view`
- exact queue refs plus optional derived `queue_view`

Bootstrap planning before the first `integrate_plan` seal of a cycle requires concrete merged
`current-cycle research_synthesis_candidate`.

Every `planning_packet` must carry at least one concrete research basis:

- `current-cycle research_synthesis_candidate`, or
- `latest authoritative research_synthesis`

Any research artifact consumed by `planning_packet` must expose exact
`research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`.

### Required Outputs

- `revised_plan_candidate`

That candidate must contain at least:

- `run_intent`
- `working_goal`
- `success_condition`
- `current_stage`
- `dispatchable_slice_specs`
- `remaining_stage_queue`
- `quality_gates`
- `research_hooks`
- `open_questions`
- `progress_ledger_candidate`

`run_intent` must be one of:

- `planning_only`
- `implementation_oriented`

`run_intent` must be derived from `request_intent_ref` plus fresh research, never copied from
source-document wording alone.

`planning_only` is legal only when `request_intent_ref=planning_deliverable_only`.

If `request_intent_ref=end_to_end_progress`, `run_intent` must be `implementation_oriented`.

If `request_intent_ref=planning_deliverable_only`, the loop still must complete the same initial
`research -> planning -> challenge -> integrate_plan` path before the run may stop with the
authoritative `revised_plan` as its requested deliverable.

Concrete `current_stage` entries must contain at least:

- `stage_id`
- `stage_summary`
- `stage_obligation=required_for_success|optional_followup`

`current_stage` in `revised_plan_candidate` must always be concrete. `none_yet` remains legal only
on newborn-cycle `research` handoffs before the first `integrate_plan` seal of a cycle.

Each `remaining_stage_queue` entry must contain at least:

- `stage_id`
- `stage_summary`
- `stage_obligation=required_for_success|optional_followup`

`dispatchable_slice_specs` must contain at least:

- `slice_id`
- `requested_output`
- `read_scope`
- `write_scope`
- `gate_refs`
- `recovery_republish_rule`

If `source_packet_ref` already contains a staged plan, authority note, or implementation checklist,
the planner must still re-expand it against the normalized `working_goal_ref`, current target
state, and fresh research before treating it as executable. Missing `required_for_success` stages,
preparatory-only endpoints, or narrowed success conditions must be corrected in the emitted
`revised_plan_candidate`.

`parallel_worker_lanes` may exist only as a derived human-readable view keyed to `dispatchable_slice_specs`.

### Forbidden Actions

- sealing a `handoff_packet`
- activating the candidate as executable
- mutating existing claim state directly
- issuing controller decisions

## Challenge Packet

`challenge_packet` is used for both plan challenge and verify challenge.

Exactly three challenge packets must be emitted per challenge phase, one per viewpoint:

- `architecture_dependency`
- `failure_verification`
- `goal_efficiency`

### Required Inputs

- latest sealed `handoff_packet` or bootstrap context when `authoritative_handoff_ref=none_yet`
- `phase=planning_phase|verify_phase`
- authoritative `challenge_review_mode`
- `viewpoint`
- one authoritative or lane-local review target:
  - `revised_plan_candidate` only when `phase=planning_phase` and `challenge_review_mode=plan_review`
  - `verification_candidate` by default when `phase=verify_phase` and `challenge_review_mode=verify_current_pass`
  - authoritative `evidence_packet` only when `phase=verify_phase` and `challenge_review_mode=post_close_revalidation|cold_start_revalidation`, and only when it matches the active `plan_snapshot_id` and `target_fingerprint`
- applicable gate set
- accepted constraints and dependencies

`challenge_review_mode` must be one of:

- `plan_review`
- `verify_current_pass`
- `post_close_revalidation`
- `cold_start_revalidation`

`plan_review` is legal only in `planning_phase`.

`verify_current_pass|post_close_revalidation|cold_start_revalidation` are legal only in `verify_phase`.

### Required Outputs

- `challenge_result_candidate`

That candidate must contain at least:

- `phase`
- `challenge_review_mode`
- `viewpoint`
- `review_target_ref`
- `gate_verdict`
- `blocking_findings`
- `non_blocking_findings`
- `source_drift_risks`
- `missing_gates`
- `dependency_order_fixes`
- `recommended_reordering`
- `execution_ready`

Each finding must contain at least:

- `severity`
- `summary`
- `why_it_matters`
- `evidence`
- `blocking`
- `plan_change`

`challenge_result_candidate` must preserve the packet's `phase`, `challenge_review_mode`, and
concrete `review_target_ref`.

When `phase=verify_phase` and `challenge_review_mode=verify_current_pass`,
`review_target_ref` must equal the current `verification_candidate_ref`.

### Forbidden Actions

- implementing the fix directly
- mutating controller state
- mutating claim state
- emitting final acceptance on behalf of the integrator

## Worker Packet

`worker_packet` is the only delegated packet that may propose code or target changes.

It is bounded to one claimed slice.

### Required Inputs

- latest sealed `handoff_packet`
- active `revised_plan` snapshot
- authoritative claim record
- concrete `claim_id`
- `claim_status=open`
- concrete `slice_id`
- concrete `plan_snapshot_id`
- concrete `stage_id`
- `open_write_claims_ref` plus mirror proof that this claim is still in the current authoritative open-claim set
- `dispatch_safety_ref` proving scope comparability and pairwise dispatch safety against the current authoritative open-claim set
- `replacement_lineage_ref` as concrete ref or `none_yet`
- `read_scope`
- `write_scope`
- exact gate refs plus optional derived `gate_view`
- exact requested output

### Required Outputs

- `worker_delta_candidate`

That candidate must contain at least:

- `claim_id`
- `plan_snapshot_id`
- `diff_summary`
- `artifact_refs`
- `check_results` when locally run
- `open_risks`
- `requested_followup_checks`

### Forbidden Actions

- touching any ownership unit outside declared `write_scope`
- reopening or republishing claims
- merging its own output
- mutating authoritative artifacts directly
- assuming authority outside the packet's `plan_snapshot_id`
- emitting from a closed, superseded, invalidated, or replacement-required claim
- emitting without current dispatch-safety proof

## Verification Packet

`verification_packet` collects direct evidence for the current stage before verify challenge.

### Required Inputs

- latest sealed `handoff_packet`
- active `revised_plan` snapshot
- exact stage gate refs plus optional derived `gate_view`
- exact claim-state refs plus optional derived `claim_state_view`
- direct artifact refs from worker outputs or integrated changes
- current check plan

### Required Outputs

- `verification_candidate`

That candidate must contain at least:

- `plan_snapshot_id`
- `target_fingerprint`
- `target_refs`
- `artifact_refs`
- `check_results`
- `log_refs`
- `observed_findings`
- `freshness_status`
- `stale_reason`
- `collected_at`
- `gate_assessment`

### Forbidden Actions

- closing the stage
- sealing `evidence_packet`
- mutating findings directly in `decision_ledger`
- issuing `commit|rework|rescope|escalate`

## Integration Packet

`integration_packet` is consumed by the main CLI thread or a tightly scoped integrator lane.

It is the only packet allowed to prepare barrier-scoped authority changes.

### Required Inputs

- latest sealed `handoff_packet` or bootstrap context when the first `integrate_plan` seal has not succeeded yet
- immutable `request_intent_ref`
- latest authoritative `revised_plan` snapshot when one exists
- current `decision_ledger`
- current authoritative `evidence_packet_ref` when `seal_point=integrate_verify` revalidation consumes an existing evidence target
- `seal_point`
- candidate artifacts relevant to the current seal point:
  - merged `research_synthesis_candidate` with exact `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}` when `seal_point=integrate_plan|goal_reassessment`
  - `revised_plan_candidate`
  - `challenge_result_candidates` as an exact three-item set keyed by `architecture_dependency`, `failure_verification`, and `goal_efficiency` when `seal_point=integrate_plan|integrate_verify`; when `seal_point=integrate_verify`, exactly one legal subcase must hold:
    - current-pass subcase: concrete `verification_candidate`, and each candidate carries `phase=verify_phase`, `challenge_review_mode=verify_current_pass`, and `review_target_ref` equal to the current `verification_candidate`
    - revalidation subcase: concrete authoritative `evidence_packet_ref`, and each candidate carries `phase=verify_phase`, `challenge_review_mode=post_close_revalidation|cold_start_revalidation`, and `review_target_ref` equal to that authoritative `evidence_packet_ref`
  - concrete `verification_candidate` only for the `integrate_verify` current-pass subcase
  - `worker_delta_candidate`
- `fixed_cycle_close_decision_ref` plus exact legality refs when `seal_point=cycle_decision`
- `fixed_termination_posture_ref` plus exact legality refs when `seal_point=run_decision`

### Required Outputs

- `integration_result_candidate`

That candidate must contain at least:

- `seal_point`
- `success_bundle`
- `candidate_bundle_manifest`
- `failure_fallback`
- `draft_publications`

`success_bundle` must name the exact publish-together bundle required at that `seal_point`.

`candidate_bundle_manifest` must record the exact `research_viewpoint_set` whenever a
`research_synthesis_candidate` is consumed.

Allowed `seal_point` values:

- `integrate_plan`
- `integrate_verify`
- `cycle_decision`
- `goal_reassessment`
- `run_decision`

Seal-point bundle rules:

- `integrate_plan`
  - draft publications may include `research_synthesis_candidate` and `revised_plan_candidate`
  - success bundle must pair the authoritative `research_synthesis`, authoritative `revised_plan`, authoritative `decision_ledger` mutation, authoritative claim state with exact `open_write_claims` parity, and a sealed `planning` handoff carrying either the directly resumable planning row or the terminal planning-deliverable row when immutable `request_intent_ref=planning_deliverable_only`
- `integrate_verify`
  - draft publications may include `verification_candidate`-derived `evidence_packet` and any required `revised_plan` candidate
  - success bundle must pair the authoritative `evidence_packet`, which is derived from the current `verification_candidate` and preserves its current-pass `plan_snapshot_id`, `target_fingerprint`, and `target_refs` in the current-pass subcase, or is refreshed from the current authoritative `evidence_packet_ref` and preserves that revalidation target in the `post_close_revalidation|cold_start_revalidation` subcase, authoritative `decision_ledger` mutation, authoritative claim state with exact `open_write_claims` parity, any authoritative `revised_plan` change, and a sealed `cycle_decision` handoff carrying the full universal plus row-specific schema together
- `cycle_decision`
  - success bundle must pair the already fixed `cycle_close_decision` token, its legality refs, any required `decision_ledger` mutation, and the sealed successor handoff carrying the full universal plus row-specific schema together
- `goal_reassessment`
  - success bundle must pair the authoritative `research_synthesis`, any required `decision_ledger` mutation, and a sealed `run_decision` handoff carrying the full universal plus row-specific schema together
- `run_decision`
  - success bundle must pair the already fixed `termination_posture`, its legality refs, and the sealed successor handoff carrying the full universal plus row-specific schema together
  - if `termination_posture=continue`, any later live-invocation pause is legal only after that successor handoff is the newborn-cycle `research` row
  - if the live invocation will intentionally yield immediately after that seal, the success bundle may also carry the required authoritative `decision_ledger` pause record for the close-out summary
  - live-invocation pause reasons such as recorded time/resource ceiling are close-out narration layered on top of the sealed successor handoff; they do not replace the successor handoff or introduce a third terminal posture

`failure_fallback` must state that the prior sealed authority remains authoritative and must identify any seal-point-specific draft visibility explicitly permitted by Stage 5 `allowed_draft_visibility`.

### Forbidden Actions

- consuming unnamed candidate artifacts
- skipping Stage 5 barrier rules
- leaking unsealed candidates as authoritative
- changing controller decisions outside legal seal points
- minting or selecting `cycle_close_decision` or terminal run-decision `termination_posture` inside `integration_packet`, except the fixed terminal planning posture `stop_planning_deliverable` derived from immutable `request_intent_ref` at `seal_point=integrate_plan`

## Packet-to-State Mapping

| Controller State | Delegated Packet(s) | Expected Candidate Output |
| --- | --- | --- |
| `research` | `research_packet` | `research_synthesis_candidate` |
| `planning` | `planning_packet` | `revised_plan_candidate` |
| `plan_challenge` | three `challenge_packet` with `phase=planning_phase` | three `challenge_result_candidate` |
| `integrate_plan` | `integration_packet` with `seal_point=integrate_plan` | `integration_result_candidate` |
| `execute` | one or more `worker_packet` | `worker_delta_candidate` |
| `verify` | `verification_packet` | `verification_candidate` |
| `verify_challenge` | three `challenge_packet` with `phase=verify_phase` | three `challenge_result_candidate` |
| `integrate_verify` | `integration_packet` with `seal_point=integrate_verify` | `integration_result_candidate` |
| `cycle_decision` | main CLI / `integration_packet` with `seal_point=cycle_decision` | `integration_result_candidate` |
| `goal_reassessment` | `research_packet` then `integration_packet` with `seal_point=goal_reassessment` | `integration_result_candidate` |
| `run_decision` | main CLI / `integration_packet` with `seal_point=run_decision` | `integration_result_candidate` |

## Main CLI Orchestration Rules

The main CLI thread must:

- dispatch packets from the latest sealed `handoff_packet` or from bootstrap context before the first seal
- keep only compact packet inputs in context for delegated lanes
- merge candidate outputs only through the integration path
- never hand a worker broad transcript context when a slice packet is sufficient
- keep controller transitions local unless a narrow critical-path local step is cheaper than delegation

The main CLI thread may not:

- let workers infer their own claim scope
- let challengers review from stale or superseded artifacts
- let research bypass the current authoritative goal or handoff
- let any delegated lane decide controller transitions by narrative summary

## Stage 6 Acceptance Target

Stage 6 is ready for challenge only if:

- every lane has exactly one packet kind
- every packet names exact authoritative inputs
- every packet names exact forbidden actions
- `challenge_packet` is phase-agnostic except for its review target
- `worker_packet` is slice-bounded and snapshot-bounded
- `integration_packet` is the only authority-producing packet
- the packet set is small enough that Stage 7 can challenge it without reintroducing transcript-sized context
