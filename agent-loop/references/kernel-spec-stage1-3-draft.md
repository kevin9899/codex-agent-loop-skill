# Stage 1-4 Kernel Spec Draft

This draft is published as a supporting design appendix for the public skill. `SKILL.md` remains the only public operator contract, and this draft may evolve between tagged releases.

These references are non-authoritative maintainer appendices. They may explain lower-level lifecycle or packet detail, but they do not add, widen, or override the public operator contract in `SKILL.md`.

## Scope

This draft covers only:

- Stage 1: lifecycle scope and control ownership
- Stage 2: executable authority and handoff contract
- Stage 3: evidence and verdict kernel
- Stage 4: worker ownership and recovery

This draft does not finalize:

- worker packet wording
- challenger packet wording
- verifier packet wording
- public skill-doc reflection

Those remain downstream of validated dry-runs.

## Stage 0 Prerequisite

Before this kernel is adopted, Stage 0 must produce `delta_ledger` with:

- solved rules already present in the current skill docs
- unresolved rules this kernel must close
- prior blocker -> closure rule mapping
- prior blocker -> proof dry-run mapping

No later stage should redesign an already-solved rule without a new blocker that explicitly forces it.

## Kernel Acceptance Target

This kernel is ready for Stage 5 only if all of these hold:

- `revised_plan` is the only executable artifact
- `handoff_packet` is the only resume-authoritative artifact
- `handoff_packet + fresh target state` is sufficient for cold-start resume
- run and cycle control authority are explicit and nested rather than flat
- evidence sufficiency and verdict merge rules are explicit
- `commit`, `rework`, `continue`, `rescope`, `escalate`, and `stop` are evidence-backed decisions
- Stage 5 can attach a falsifiable dry-run oracle to every required scenario without inventing new kernel behavior
- every unresolved blocker in `delta_ledger` maps to at least one kernel clause and one required Stage 5 oracle scenario

## Stage 1: Lifecycle Scope Map

### Scope Hierarchy

- `run`
  A goal-bounded improvement effort. A run can span multiple cycles.
- `cycle`
  One bounded pass over exactly one current stage.
- `stage`
  One plan-defined unit of work that can be executed, verified, and closed inside a cycle.
- `worker_slice`
  One bounded subtask inside a stage with declared ownership.

### Scope Ownership Table

| Scope | Control Owner | Mutation Authority | Entry Criteria | Exit Criteria | Legal Re-entry | Control Source | Executable Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run` | orchestrator | orchestrator | valid source resolved, working goal established, explicit `request_intent` captured | explicit `stop` recorded by `run_decision`, or explicit planning-deliverable completion recorded after the first challenge-reviewed `integrate_plan` seal when `request_intent=planning_deliverable_only`; in either case final only while the latest sealed handoff has `post_close_invalidation=none` | resume from latest sealed `handoff_packet` plus fresh target preflight | latest sealed `handoff_packet` | referenced `revised_plan` snapshot from latest sealed `handoff_packet` |
| `cycle` | orchestrator | integrator during integration and decision states | either a bootstrap/replanning cycle opened at `research`, or one current stage selected from the active executable snapshot | `commit`, `rescope`, or `escalate` recorded; a `commit` close is final only while the latest sealed handoff has `post_close_invalidation=none` | resume through the canonical cold-start path `run_bootstrap -> mismatch routing -> cycle_ready -> legal resume dispatch` only | latest sealed `handoff_packet` for the active cycle when one exists, otherwise `source_packet` plus fresh run bootstrap context | current `revised_plan` snapshot when one exists; otherwise none until the first `integrate_plan` seal of the cycle |
| `stage` | orchestrator | integrator | stage definition published in current executable snapshot | stage decision recorded as `commit`, `rework`, `rescope`, or `escalate` | re-enter only through cycle controller, never by worker self-claim | current cycle entry in latest sealed `handoff_packet` | current stage block in current `revised_plan` snapshot; `none_yet` during bootstrap/replanning before the first executable snapshot of the cycle |
| `worker_slice` | integrator | assigned worker within declared claim | integrator publishes snapshot-bound slice with write/read scope | slice result merged, rejected, invalidated, or escalated | re-enter only if integrator republishes slice against the current executable snapshot | current stage block plus current claim status in latest sealed `handoff_packet` | published worker assignment embedded in current `revised_plan` snapshot |

### Canonical Authority Map

There are only two authorities in the kernel:

- `orchestrator`
  - owns `run_controller`
  - opens cycles
  - admits or denies resume
  - selects the current stage
  - owns `source_packet`, `request_intent`, and `delta_ledger`
  - emits final `continue|stop`
- `integrator`
  - operates only inside `integrate_plan`, `integrate_verify`, `cycle_decision`, `goal_reassessment`, and `run_decision`
  - publishes `revised_plan`
  - seals `handoff_packet`
  - records `decision_ledger`
  - issues or revokes worker claims
  - emits `rework|rescope|escalate|commit`

These are not additional authorities:

- `run_controller`
  The orchestrator's state machine, not a separate actor.
- `cycle_controller`
  The orchestrator-managed state machine for the active cycle, with integrator mutation rights in integration and decision states.
- `research integrator`
  Alias for the integrator when consolidating research output.
- `verifier integrator`
  Alias for the integrator when consolidating verification output.
- `planner`, `researcher`, `challenger`, `verifier`, `worker`
  Proposal and evidence producers only. They never own control transitions.

### Nested Control Model

The control model is nested, not flat.

- `run_controller`
  Owns intake, goal tracking, cross-cycle continuity, goal reassessment, and final `continue|stop`.
- `cycle_controller`
  Owns the current stage, the challenge/verify loop, stage-close decisions, and re-research before the next stage.

The `run_controller` may open many cycles.

The `cycle_controller` may never terminate a run directly. It can only emit:

- `rework`
- `commit`
- `rescope`
- `escalate`

The `run_controller` consumes those outputs and decides:

- `continue`
- `stop`

Only the `run_controller` may mint a `cycle_id`.

- it may mint the initial `cycle_id` inside `run_bootstrap` for a fresh run
- it may mint each subsequent `cycle_id` inside `run_decision` immediately before sealing the newborn-cycle handoff to `research`

### Run Controller

The `run_controller` has these states:

1. `run_bootstrap`
   - resolve source
   - establish working goal
   - load latest handoff if resuming
2. `cycle_ready`
   - determine the next cycle entry
   - fresh run or post-`continue` re-entry must open at `research`
   - resumed active cycles may dispatch to the sealed `resume_entry_state`
3. `goal_reassessment`
   - collect, integrate, and consume fresh research after a cycle closes
   - compare current codebase state against the original goal
4. `run_decision`
   - consume the latest terminal cycle decision plus reassessment output
   - emit `continue` or `stop(stop_reason)`

`run_controller` re-entry is legal only at:

- `run_bootstrap`
- `cycle_ready`
- `goal_reassessment`
- `run_decision`

### Fresh-Run And Next-Cycle Genesis Rule

If no sealed handoff exists, or if `run_decision` has just emitted `continue`, the next cycle has no active executable stage yet.

In that situation:

- `cycle_ready` must dispatch to `research`
- `stage_id = none_yet` until `integrate_plan` publishes the first executable snapshot of that cycle
- `plan_snapshot_id = none_yet` until `integrate_plan` publishes the first executable snapshot of that cycle

### Cycle Controller

The `cycle_controller` has these states:

1. `research`
2. `planning`
3. `plan_challenge`
4. `integrate_plan`
5. `execute`
6. `verify`
7. `verify_challenge`
8. `integrate_verify`
9. `cycle_decision`

`cycle_decision` may emit only:

- `rework`
- `commit`
- `rescope`
- `escalate`

If a cycle emits `commit`, `rescope`, or `escalate`, the `run_controller` must still perform `goal_reassessment` before the next cycle opens or stops.

`rework` is a first-class `cycle_decision` token, but it is not a cycle-close outcome.

- `rework` keeps the same `cycle_id`
- `rework` loops back into the same stage
- only `commit`, `rescope`, and `escalate` close the current cycle

### Legal Transition Tables

Run controller transitions:

| Current State | Allowed Next State | Skip Allowed | Forced Redirect |
| --- | --- | --- | --- |
| `run_bootstrap` | `cycle_ready` | no | if source is unreadable or invalid, abort before the run opens with reason `invalid_source` |
| `cycle_ready` | `research`, `planning`, terminal `planning_delivery_complete`, `verify`, `cycle_decision`, `goal_reassessment`, `run_decision` | no | if no sealed handoff exists, dispatch must go to `research`; if resume is illegal, force `run_bootstrap`; otherwise dispatch only to the direct-dispatch state or terminal closed-run posture validated by the canonical resume contract, or to the mismatch-routed `research|verify` path validated by the mismatch matrix |
| `goal_reassessment` | `run_decision`, `verify` | no | if fresh research has not yet been integrated for the current run-close attempt, the integrator must publish `research_synthesis` and seal a new handoff before `run_decision` is legal; if ledger-backed stale evidence mutation, fresh preflight invalidation, or ledger-backed blocker reopen invalidates the current cycle close, redirect to `verify` in the same `cycle_id` and `stage_id` |
| `run_decision` | `research`, terminal `stop`, `verify` | no | if carried or freshly derived post-close invalidation exists, redirect to `verify` in the same `cycle_id` and `stage_id`; otherwise `continue` mints the next `cycle_id`, seals a newborn-cycle handoff to `research`, and opens the next cycle; `stop` seals a terminal handoff with the chosen stop posture before the run ends |

Cycle controller transitions:

| Current State | Allowed Next State | Skip Allowed | Forced Redirect |
| --- | --- | --- | --- |
| `research` | `planning` | no | if the active research phase has not yet produced a merged exact-three-viewpoint research synthesis candidate, remain in `research` |
| `planning` | `plan_challenge` | no | none |
| `plan_challenge` | `integrate_plan` | no | none |
| `integrate_plan` | `execute`, `cycle_decision`, terminal `planning_delivery_complete` | no | if blockers force decision before execution, go to `cycle_decision`; if immutable `request_intent=planning_deliverable_only`, the run may end after the first challenge-reviewed authoritative `revised_plan` seal instead of entering execution |
| `execute` | `verify` | no | interrupted or superseded execution resumes through `planning`, never directly back into `execute` |
| `verify` | `verify_challenge` | no | live in-process recovery may return to `verify` if fingerprints still match; ordinary cold-start recovery before `integrate_verify` resumes through `planning`, except when the stale-evidence or post-close-invalidation revalidation rules explicitly authorize same-cycle cold-start `verify` |
| `verify_challenge` | `integrate_verify` | no | none |
| `integrate_verify` | `cycle_decision` | no | none |
| `cycle_decision` | `planning`, `verify`, `goal_reassessment` | no | `rework` loops to `planning` in the same cycle only when concrete verify evidence exists; same-cycle revalidation on stale evidence or blocker reopen loops to `verify` in the same cycle; if `evidence_packet_ref=none_yet`, only `rescope` or `escalate` are legal; `commit`, `rescope`, and `escalate` transfer control to `goal_reassessment`; `rescope` and `escalate` still close the current cycle |

No other transitions are legal.

### Explicit Planning-Deliverable Completion Rule

If immutable `request_intent=planning_deliverable_only`, the loop must still execute the same
initial `research -> planning -> plan_challenge -> integrate_plan` path.

That request intent may never be inferred from `source_packet` content alone.

After the first successful `integrate_plan` seal publishes the challenge-reviewed authoritative
`revised_plan`, the orchestrator may end the run without entering `execute`, but only by sealing a
terminal `planning` handoff with `termination_posture=stop_planning_deliverable` and recording a
concrete `planning_delivery_complete` event in `decision_ledger` referencing the active
`plan_snapshot_id` and `working_goal`.

Before that event exists, stopping the run on planning-deliverable grounds is illegal.

### Exact Three-Viewpoint Research Completion Rule

Every research phase in the kernel is exact-set complete only when it includes one lane result for
each of these viewpoints:

- `architecture_dependency`
- `failure_verification`
- `goal_efficiency`

Raw lane outputs remain draft-only.

`planning` is legal only after the current research phase has produced one merged
`research_synthesis_candidate` that records:

- `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`
- concrete `lane_candidate_refs` with exactly one lane result per viewpoint from the current
  research phase

Fresh research consumed by `goal_reassessment -> run_decision` must preserve the same exact-set
completeness after integration into authoritative `research_synthesis`.

### Transition Authority Rules

- workers cannot advance controller state
- challengers cannot advance controller state
- verifiers cannot advance controller state
- only the integrator can publish a new executable snapshot
- only the orchestrator can open a new cycle
- only the run controller can emit `stop`
- only the run controller can consume terminal `commit|rescope|escalate` and decide whether a new cycle may open

### Main Thread Exception Rule

The main CLI thread stays orchestration-first by default.

It may perform direct local work only when:

- the next control decision is blocked on a narrow critical-path step
- delegating that step would add more coordination cost than local completion
- the step does not collapse the stage boundary or bypass the artifact rules

If the main thread does local work, it still must write results back through the same evidence and integration path as any worker.

## Stage 2: Executable Authority And Handoff Contract

### Single Executable Authority

`revised_plan` is the only executable artifact.

`handoff_packet` is the only resume-authoritative artifact.

Everything else is one of:

- intake artifact
- evidence artifact
- audit artifact
- restart artifact

`decision_ledger` is audit and event history only. It never gives workers or verifiers executable instructions, and no ledger mutation becomes cold-start-visible until a successor `handoff_packet` is sealed with the resulting authoritative state.

Raw challenger outputs are transient and invalid for downstream control after integration completes.

### Publication Barrier

`integrate_plan` barrier:

1. integrator consumes allowed upstream artifacts
2. integrator publishes the current-cycle `research_synthesis` before sealing any `planning` handoff
3. integrator updates or republishes `revised_plan`
4. integrator finalizes the next claim set for that snapshot
5. integrator invalidates stale claims and stale worker outputs
6. integrator records accepted/rejected findings in `decision_ledger`
7. integrator seals `handoff_packet` that points to the exact `plan_snapshot_id` published in this barrier
8. all prior raw challenge outputs become downstream-invalid

`integrate_verify` barrier:

1. integrator consumes allowed upstream artifacts
2. integrator computes `final_plan_snapshot_id` for this barrier
3. if verify integration changes executable instructions or embedded claim state, integrator republishes `revised_plan` as `final_plan_snapshot_id`; otherwise the existing executable snapshot remains `final_plan_snapshot_id`
4. integrator finalizes the claim set referenced by `final_plan_snapshot_id`
5. integrator publishes or refreshes the current `evidence_packet` before sealing any handoff that references it
6. integrator invalidates stale claims and stale worker outputs
7. integrator records accepted/rejected findings in `decision_ledger`
8. integrator seals `handoff_packet` that references the same `final_plan_snapshot_id`
9. executable activation switches only at this seal point
10. all prior raw challenge outputs become downstream-invalid

No worker, verifier, or controller may act on unsealed post-challenge state.

### Decision Seal Barriers

`cycle_decision` seal barrier:

1. the cycle controller fixes `cycle_close_decision`
2. if stale evidence or blocker reopen requires same-cycle revalidation, the orchestrator redirects to `verify` and no close handoff is sealed
3. otherwise the integrator seals the handoff for `planning` or `goal_reassessment`
4. if sealing fails, the prior handoff remains authoritative and the decision is not externally visible

`goal_reassessment` seal barrier:

1. the run controller keeps the current concrete `cycle_close_decision` fixed
2. the integrator publishes `research_synthesis`
3. the integrator seals the handoff to `run_decision` with `termination_posture=undecided`
4. if sealing fails, the prior handoff remains authoritative and the reassessment result is not externally visible

`run_decision` seal barrier:

1. the run controller fixes `termination_posture`
2. if `termination_posture=continue`, the run controller mints the next `cycle_id`
3. if `termination_posture=continue`, the integrator seals a newborn-cycle handoff to `research` with `parent_cycle_id` set to the closing cycle id, `parent_run_decision_handoff_ref` set to the superseded parent `run_decision` lineage, `stage_id=none_yet`, and `plan_snapshot_id=none_yet`
4. if `termination_posture` is a stop value, the integrator seals a terminal handoff to `run_decision` with that stop posture
5. if a continue or stop seal fails, the prior handoff remains authoritative and the attempted terminal decision is not externally visible

### Executable Snapshot Rule

Every executable snapshot must have:

- `run_id`
- `cycle_id`
- `stage_id`
- `plan_snapshot_id`
- `published_at`
- `source_fingerprint`
- `target_fingerprint`

The newest sealed `plan_snapshot_id` is the only executable source.

### Executable Activation Rule

A published `revised_plan` snapshot is not executable merely because it exists.

It becomes executable only when the latest sealed `handoff_packet` references its `plan_snapshot_id`.

If a publication attempt completes but handoff sealing does not, the previously sealed executable snapshot remains active.

### Worker Claim Invariants

Worker claims stay embedded inside `revised_plan` and `handoff_packet.open_write_claims`.

Every claim must carry:

- `claim_id`
- `parent_claim_id`
- `slice_id`
- `worker_id`
- `plan_snapshot_id`
- `status`
- `read_scope`
- `write_scope`

Allowed `status` values:

- `open`
- `merged`
- `rejected`
- `invalidated`
- `superseded`
- `escalated`

Only these invariants matter at kernel level:

- root claims use `parent_claim_id = none`
- every `open` claim belongs to exactly one `plan_snapshot_id`
- within one current executable `plan_snapshot_id`, at most one `status=open` claim may reference a given `slice_id`
- only the integrator may move a claim out of `open`
- only `open -> merged|rejected|invalidated|superseded|escalated` is legal
- `republish` is an integrator event that creates a new claim against a newer `plan_snapshot_id` while the parent claim closes as `superseded`
- merged, rejected, invalidated, superseded, and escalated claims are terminal
- workers may never self-republish, reopen, or merge their own claims
- a worker output may be merged only if its claim is still `open` and its `plan_snapshot_id` matches the current executable snapshot
- `handoff_packet.open_write_claims` must exactly equal the complete set of `status=open` claims embedded in the referenced `revised_plan`; any mismatch makes the handoff illegal

### Artifact Necessity Rule

No persistent artifact is allowed unless it has:

- named producer
- named consumer
- restart role or audit role
- proof dry-run that depends on it

If an artifact has no consumer and no proof scenario, remove it.

Worker claims are embedded substructures of `revised_plan` and `handoff_packet.open_write_claims`, not first-class standalone artifacts.

### Canonical Artifact Table

| Artifact | Producer | Primary Consumer | Mutable | Executable | Resume-Authoritative | Unique Operator Query |
| --- | --- | --- | --- | --- | --- | --- |
| `source_packet` | orchestrator | planner, research | immutable per run unless source changes | no | no | what exact source is this run based on |
| `request_intent` | orchestrator | planner, run controller | immutable per run unless the user explicitly changes the ask | no | no | what delivery posture did the user explicitly request |
| `working_goal` | orchestrator | planner, run controller | immutable per run unless the user explicitly changes the goal | no | no | what exact goal this run is pursuing |
| `delta_ledger` | orchestrator | orchestrator, doc reflection | mutable until reflection | no | no | which blockers are already solved vs still open in the redesign |
| `research_synthesis` | integrator | planner, run controller | immutable once referenced by sealed handoff; superseded by newer version | no | no | what fresh exact-three-viewpoint research changed the next plan or stop decision |
| `revised_plan` | integrator | orchestrator, workers, verifiers | immutable once published; superseded by newer snapshot | yes | no | what exact work is executable right now |
| `decision_ledger` | integrator | audit, reflection | append-only | no | no | why each finding was accepted, rejected, or superseded |
| `evidence_packet` | integrator | verify challengers, integrator | payload immutable once referenced by sealed handoff; `freshness_status` and `stale_reason` may flip through ledger-backed stale mutation | no | no | what evidence is being judged in the current verify pass |
| `handoff_packet` | integrator | run bootstrap, cycle ready | immutable once sealed | no | yes | how to resume deterministically from cold start |

### Supersession Rules

- `request_intent` is source-independent. `source_packet` text may inform interpretation, but it may never override the explicit-user-request artifact.
- only a `revised_plan` snapshot referenced by the latest sealed `handoff_packet` supersedes the previously authoritative executable snapshot for control or resume purposes
- `decision_ledger` never supersedes `revised_plan`
- `handoff_packet` must point to exactly one sealed `revised_plan` snapshot unless it is a newborn-cycle `research` handoff with `plan_snapshot_id=none_yet`
- if `handoff_packet` points to a superseded snapshot, resume is illegal until a new handoff is sealed
- worker claims and worker slice outputs are valid only for the `plan_snapshot_id` that published them
- only `open` worker claims may appear in `handoff_packet.open_write_claims`
- any worker output produced against an older `plan_snapshot_id` is stale and may not be merged directly; it may only inform audit, replanning, or a newly republished claim lineage
- unsealed published snapshots are draft-only and do not supersede the latest handoff-authoritative executable snapshot or its claim mirror

### Handoff Contract

`handoff_packet` is a strict resume manifest.

It must be sufficient, together with fresh target preflight, to recover:

- working goal
- current stage
- latest cycle-close decision
- current termination posture
- exact executable snapshot when one exists, otherwise explicit `plan_snapshot_id=none_yet`

During cold-start resume, the system may read other artifacts only through immutable references contained in the latest sealed `handoff_packet`.

Any cold-start freshness or invalidation mismatch must be derived only from:

- fingerprints stored in the latest sealed `handoff_packet`
- immutable fields of artifacts referenced by that handoff, including the referenced `evidence_packet`
- fresh source or target preflight against those stored values

If any derived artifact disagrees with the latest sealed `handoff_packet`:

- the handoff wins for resume routing
- the disagreement itself becomes a new audit finding
- if the disagreement breaks freshness or snapshot legality, resume becomes illegal and must follow the mismatch matrix

### Handoff Packet Fields

`handoff_packet` must contain at least:

- `handoff_packet_id`
- `run_id`
- `cycle_id`
- `stage_id`
- `plan_snapshot_id`
- `cycle_close_decision`
- `termination_posture`
- `post_close_invalidation`
- `working_goal_ref`
- `source_packet_ref`
- `research_synthesis_ref`
- `evidence_packet_ref`
- `source_fingerprint`
- `target_fingerprint`
- `open_write_claims`
- `resume_entry_state`

State-conditional `handoff_packet` fields:

- `parent_cycle_id`
  Required on stored newborn-cycle `research`; must be absent otherwise.
- `parent_run_decision_handoff_ref`
  Required on stored newborn-cycle `research`; it is the concrete parent `handoff_packet_id` for the just-closed `run_decision` lineage and authorizes lookup of that lineage if late invalidation voids the child handoff. It must be absent otherwise.

Allowed `resume_entry_state` values:

- `research`
- `planning`
- `cycle_decision`
- `goal_reassessment`
- `run_decision`

`verify` is mismatch-routed only. It can never be produced by a direct seal point.

Allowed `cycle_close_decision` values:

- `none_yet`
- `commit`
- `rescope`
- `escalate`

Allowed `termination_posture` values:

- `undecided`
- `continue`
- `stop_planning_deliverable`
- `stop_goal_saturated`
- `stop_escalation_halt`

Allowed `post_close_invalidation` values:

- `none`
- `target_drift`
- `snapshot_drift`
- `blocker_reopen`

`cycle_close_decision` is minted only in `cycle_decision`, carried forward only inside that closed-cycle lineage, and reset to `none_yet` when `run_decision=continue` opens a newborn cycle.

`termination_posture` is minted only by the `run_controller` inside `run_decision`, except
`stop_planning_deliverable`, which may be minted at `integrate_plan` when immutable
`request_intent=planning_deliverable_only`; the integrator may seal it but may not rewrite it.

`cycle_id` must always be concrete.

`parent_cycle_id` is a state-conditional lineage field. On stored newborn-cycle `research`, it is required and used only to recover the just-closed parent cycle if late post-`continue` invalidation voids the child handoff. Outside stored newborn-cycle `research`, it must be absent.

When both `parent_cycle_id` and `parent_run_decision_handoff_ref` are present, `parent_cycle_id` must equal the referenced parent handoff's `cycle_id`.

`stage_id` may be:

- a concrete stage id for an active or just-closed stage
- `none_yet` only for newborn-cycle `research`

`plan_snapshot_id` may be:

- a concrete id when an executable snapshot already exists for the cycle
- `none_yet` only for newborn-cycle `research`

`research_synthesis_ref` may be:

- a concrete id when the current resume target depends on already-integrated research
- `none_yet` only when `resume_entry_state` is `research` or `goal_reassessment`

`evidence_packet_ref` may be:

- a concrete id when verify evidence exists for the active cycle
- `none_yet` for all pre-verify resume points and pre-verify cycle-close attempts

### Between-Cycle Handoff Invariants

If `resume_entry_state` is directly resumable `planning`:

- `cycle_close_decision` must be `none_yet`
- `termination_posture` must be `undecided`

If `resume_entry_state` is terminal `planning`:

- `cycle_close_decision` must be `none_yet`
- `termination_posture` must be `stop_planning_deliverable`
- `evidence_packet_ref` must be `none_yet`
- `post_close_invalidation` must be `none`
- the run is already closed and may not enter `execute`, `cycle_decision`, or a new cycle

If `resume_entry_state` is `cycle_decision`:

- `cycle_close_decision` must be `none_yet`
- `termination_posture` must be `undecided`
- `open_write_claims` must be empty

If `resume_entry_state` is directly resumable `goal_reassessment` or pre-terminal `run_decision`:

- `open_write_claims` must be empty
- `stage_id` refers to the most recently closed stage, not a newly opened stage
- `plan_snapshot_id` refers to the most recently sealed executable snapshot under reassessment, not an active worker grant
- `cycle_close_decision` must be concrete
- `termination_posture` must be `undecided`
- `post_close_invalidation` must be `none`
- no worker may claim ownership again until `run_decision -> research` opens the next cycle

If `resume_entry_state` is terminal `run_decision`:

- `open_write_claims` must be empty
- `cycle_close_decision` must be concrete
- `termination_posture` must be `stop_goal_saturated` or `stop_escalation_halt`
- `post_close_invalidation` must be `none`
- the run is already closed and may not open a new cycle

If the latest sealed handoff carries `post_close_invalidation != none`:

- the stored `resume_entry_state` must still be `goal_reassessment` or `run_decision`
- the stored `resume_entry_state` is lineage-only and is not directly dispatchable
- the handoff is nonterminal for control purposes regardless of its stored `termination_posture`
- `cycle_close_decision` must be `commit`
- `evidence_packet_ref` must be concrete
- `plan_snapshot_id` must be concrete
- `post_close_invalidation` may be only `target_drift`, `snapshot_drift`, or `blocker_reopen`
- the prior close is no longer terminal for control purposes
- any carried `stop_*` posture is lineage-only and may not end the run until revalidation clears the invalidation
- cold-start routing must dispatch to `verify` in the same `cycle_id` and `stage_id`
- `run_decision` consumption is suspended until a fresh `integrate_verify -> cycle_decision` seal clears the invalidation
- no new cycle may open until that same-cycle revalidation path completes

If `resume_entry_state` is newborn-cycle `research`:

- `cycle_id` must already be the newly minted next-cycle id
- `parent_cycle_id` must be concrete
- `parent_run_decision_handoff_ref` must be concrete
- `stage_id` must be `none_yet`
- `plan_snapshot_id` must be `none_yet`
- `cycle_close_decision` must be `none_yet`
- `termination_posture` must be `continue`
- `post_close_invalidation` must be `none`
- `open_write_claims` must be empty

If a parent committed cycle later acquires `target_drift`, `snapshot_drift`, or `blocker_reopen` after `run_decision=continue` already sealed a newborn-cycle `research` handoff:

- that newborn handoff becomes non-dispatchable
- the integrator must supersede the latest handoff back into the parent-cycle `run_decision` lineage referenced by `parent_run_decision_handoff_ref`, with the derived `post_close_invalidation`
- the restored handoff must inherit the referenced parent handoff's control fields verbatim: `cycle_id`, `stage_id`, `plan_snapshot_id`, `cycle_close_decision`, `termination_posture`, `resume_entry_state`, and referenced artifact ids
- the provisional child `cycle_id` is void and may not resume again unless `run_decision` re-emits `continue` after the parent cycle is re-closed
- the void child `cycle_id` may not appear anywhere in the restored handoff

The parent revalidation window ends at the first non-newborn child handoff sealed after that newborn `research` handoff.

- that first non-newborn child handoff must omit `parent_cycle_id` and `parent_run_decision_handoff_ref`
- once that window closes, later invalidation no longer restores parent-cycle lineage and must route only through the child cycle's own mismatch rules

### Resume Freshness Rule

Cold-start resume is legal only if:

- `source_fingerprint` still matches
- `target_fingerprint` still matches, or the kernel requires explicit revalidation
- if `plan_snapshot_id` is concrete, it is still the newest sealed executable snapshot
- if `plan_snapshot_id=none_yet`, `resume_entry_state` must be newborn-cycle `research` with `termination_posture=continue`

If any freshness check fails:

- resume cannot jump directly to `execute`
- the next state must come from the mismatch table below

### Resume Mismatch Matrix

| Mismatch Class | Authority Owner | Same Cycle Survives | Next State |
| --- | --- | --- | --- |
| `none` | orchestrator | yes | `resume_entry_state` |
| `stale_source` | orchestrator | no | `run_bootstrap` |
| `stale_target_pre_verify` | orchestrator | yes | `research` |
| `stale_cycle_decision_evidence` | orchestrator | yes | `verify` |
| `post_close_invalidation` | orchestrator | yes | `verify` |

`post_close_invalidation` is observable either when the latest sealed handoff already carries `post_close_invalidation=target_drift|snapshot_drift|blocker_reopen`, or when fresh preflight derives the same mismatch from a stored `goal_reassessment|run_decision` handoff with `cycle_close_decision=commit`, concrete `plan_snapshot_id`, and concrete `evidence_packet_ref` that no longer validate against the active snapshot or target fingerprint. In both cases, same-cycle `verify` is mandatory before any other dispatch.

`stale_cycle_decision_evidence` is observable only when the latest sealed handoff stores `resume_entry_state=cycle_decision`, `evidence_packet_ref` is concrete, and immutable fields of that handoff-referenced evidence plus fresh target preflight show the evidence is no longer fresh for the active `plan_snapshot_id` or `target_fingerprint`.

`stale_target_pre_verify -> research` makes any carried `open_write_claims` immediately non-dispatchable. The next `integrate_plan` seal must invalidate, supersede, or republish them before any worker may write again.

Precedence rule: when the latest sealed handoff is newborn-cycle `research` with concrete `parent_cycle_id` and `parent_run_decision_handoff_ref`, resume must evaluate late invalidation of that just-closed parent lineage before it applies `stale_target_pre_verify -> research`. If the parent lineage has acquired `target_drift`, `snapshot_drift`, or propagated `blocker_reopen`, the child `cycle_id` is void and the mismatch class becomes `post_close_invalidation -> verify` through the restored parent lineage.

### Canonical Resume Contract

After `run_bootstrap -> cycle_ready`, exactly one dispatch path is legal:

This table lists only state-conditional refs. Universal `handoff_packet` fields, including `working_goal_ref`, are always required.

| Stored `resume_entry_state` | Required Refs In `handoff_packet` | Legal Next State |
| --- | --- | --- |
| `research` | `source_packet_ref`, concrete `parent_cycle_id`, concrete `parent_run_decision_handoff_ref`, `plan_snapshot_id=none_yet`, `research_synthesis_ref=none_yet`, `evidence_packet_ref=none_yet`; stored `research` is newborn-cycle only | `research` |
| `planning` | `source_packet_ref`, `research_synthesis_ref`, concrete `plan_snapshot_id`, `evidence_packet_ref=none_yet`, `termination_posture=undecided` | `planning` |
| `planning` | `source_packet_ref`, `research_synthesis_ref`, concrete `plan_snapshot_id`, `evidence_packet_ref=none_yet`, `termination_posture=stop_planning_deliverable` | terminal `planning_delivery_complete` |
| `cycle_decision` | `source_packet_ref`, `research_synthesis_ref`, `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet`; if `evidence_packet_ref` is concrete it must still be fresh | `cycle_decision` |
| `goal_reassessment` | `source_packet_ref`, `research_synthesis_ref=none_yet`, `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet` | `goal_reassessment` |
| `run_decision` | `source_packet_ref`, `research_synthesis_ref`, `plan_snapshot_id`, `evidence_packet_ref` as concrete id or `none_yet` | `run_decision` |

These direct-dispatch rows apply only when `post_close_invalidation=none`.

If the required refs are not present, the requested `resume_entry_state` is illegal.

Pre-verify drift may still route to runtime `research` through the mismatch matrix, but that is not a stored `resume_entry_state=research` handoff.

### Mismatch-Routed Verify Dispatch

`verify` is never a stored `resume_entry_state`.

It becomes the legal next state only when all of these hold:

- either the latest sealed handoff already carries `post_close_invalidation != none`, or fresh preflight derives the same invalidation from a stored `goal_reassessment|run_decision` handoff with `cycle_close_decision=commit`
- the stored `resume_entry_state` is `goal_reassessment` or `run_decision`
- `cycle_close_decision=commit`
- `plan_snapshot_id` is concrete
- `evidence_packet_ref` is concrete
- the resumed `verify` reuses the same `cycle_id` and `stage_id`

The same `verify` dispatch is also the only legal cold-start route when `resume_entry_state=cycle_decision` and concrete verify evidence later becomes stale.

### Seal And Resume Matrix

Only these controller points may seal a handoff:

| Seal Point | Allowed `resume_entry_state` |
| --- | --- |
| `integrate_plan` | `planning` |
| `integrate_plan` after `stop_planning_deliverable` | `planning` |
| `integrate_verify` | `cycle_decision` |
| `cycle_decision` after `rework` | `planning` |
| `cycle_decision` after `commit`, `rescope`, or `escalate` | `goal_reassessment` |
| `goal_reassessment` | `run_decision` |
| `run_decision` after `continue` | `research` |
| `run_decision` after `stop_goal_saturated` or `stop_escalation_halt` | `run_decision` |

No other controller point may seal a handoff.

If post-close invalidation is detected after a `goal_reassessment` or `run_decision` handoff was already sealed:

- the integrator may only supersede that handoff with the same stored `resume_entry_state`
- the successor handoff may change only `source_fingerprint`, `target_fingerprint`, and `post_close_invalidation`; every other `handoff_packet` field must be copied unchanged from the superseded handoff
- that successor handoff does not create a new seal point or a new dispatch target
- cold-start routing must still follow the mismatch matrix and dispatch to `verify`

If late invalidation voids a newborn-cycle `research` handoff after `run_decision=continue`:

- the latest handoff must be superseded back into the parent-cycle `run_decision` lineage named by `parent_run_decision_handoff_ref`
- the void child handoff may not remain the latest dispatch source
- cold-start routing must then follow the mismatch matrix from that restored parent-cycle lineage

These freshness-only restorative supersessions are legal integrator maintenance seals derived from the latest sealed lineage. They do not mint a new controller decision or a new dispatch target, and they are legal only while the latest sealed child handoff still carries the parent-lineage refs that keep the parent revalidation window open.

## Stage 3: Evidence And Verdict Kernel

### Evidence Precedence

Use this precedence when verdicts conflict:

1. actual source document or file content
2. actual diff or produced artifact
3. test or check result
4. logs and traces
5. compact execution metadata
6. narrative agent explanation

Lower-precedence evidence cannot overrule higher-precedence contradictory evidence on its own.

### Evidence Sufficiency Levels

- `S0 none`
  No meaningful evidence.
- `S1 narrative`
  Only explanations or unverified claims.
- `S2 trace`
  Logs, metadata, or partial traces without decisive artifact proof.
- `S3 artifact`
  Concrete file, diff, or generated output proof exists.
- `S4 artifact_plus_checks`
  Concrete artifact proof plus required checks or tests.
- `S5 decision_eligible`
  Artifact proof, required checks, blocker disposition, target fingerprint match, and current snapshot match all align before a decision is issued.

### Minimum Evidence By Decision

| Decision | Minimum Evidence | Disallowed If |
| --- | --- | --- |
| `rework` | `S2` | none |
| `rescope` | `S2` plus explicit gate mismatch or changed constraint | none |
| `escalate` | `S2` plus repeated blocker, unresolved conflict, or authority ambiguity | none |
| `commit` | `S5` | any unresolved blocking finding remains |
| `continue` | `S4` plus goal still has meaningful improvement path | stop conditions already proven |
| `stop` | `S5` plus explicit `stop_reason` | no legal `stop_reason` can be proven |

### Finding Lifecycle

Every finding must have:

- `finding_id`
- `origin_phase`
- `origin_snapshot_id`
- `normalized_scope_id`
- `root_cause_hash`
- `status`
- `blocking`
- `affected_scope`
- `closure_evidence_ref`
- `reopen_reason`
- `reopened_from_snapshot_id`
- `superseded_by`

Allowed `reopen_reason` values:

- `none`
- `snapshot_drift`
- `target_drift`

`post_close_invalidation=blocker_reopen` is the handoff-level effect of a ledger-backed reopen event for at least one blocking finding. The underlying finding `reopen_reason` stays `snapshot_drift` or `target_drift`; `blocker_reopen` means that such a reopen has propagated back to control routing.

Allowed `status` values:

- `open`
- `closed`
- `deferred`
- `superseded`

A blocking finding may stop propagating only when:

- it is explicitly marked `closed` with `closure_evidence_ref`
- or it is explicitly marked `superseded` with `superseded_by`

Omission never closes a finding.

### Blocking Closure Invariants

Every blocking closure must include:

- `closure_evidence_level`
- `closure_snapshot_id`
- `closure_target_fingerprint`

Blocking closure is legal only when:

- `closure_evidence_level >= S4`
- `closure_snapshot_id` equals the active `plan_snapshot_id`
- `closure_target_fingerprint` equals the active `target_fingerprint`

If snapshot or target fingerprint changes after closure:

- the blocking finding automatically reopens
- `status` must return to `open`
- `reopen_reason` must be set to `snapshot_drift` or `target_drift`
- `reopened_from_snapshot_id` must point to the closure snapshot that lost validity
- the integrator must append a `decision_ledger` reopen event naming `finding_id`, `reopen_reason`, and `reopened_from_snapshot_id`
- `commit` and `stop` become illegal until re-closed against the active snapshot and fingerprint

If that reopen affects a `blocking: true` finding after a `commit` close has already crossed into `goal_reassessment` or `run_decision`:

- the integrator must supersede the latest sealed `goal_reassessment|run_decision` handoff with `post_close_invalidation=blocker_reopen`
- `continue` and `stop` are suspended until `integrate_verify -> cycle_decision` re-closes the same cycle

### Finding Identity Rule

`finding_id` is minted by the integrator when a finding first enters `decision_ledger`.

Two observations are the same finding only when all of these match:

- same `root_cause_hash`
- same `normalized_scope_id`
- same blocking posture
- same `origin_phase`

Otherwise a new `finding_id` is required.

`superseded_by` is valid only if the successor finding:

- names the predecessor `finding_id`
- covers the same or broader affected scope
- carries equal or stronger evidence

Integrator mapping rule for a fresh observation:

1. compare against open findings with the same `root_cause_hash`
2. if `normalized_scope_id`, blocking posture, and `origin_phase` all match, reuse `finding_id`
3. else if the new observation changes scope on the same `root_cause_hash`, mint a new `finding_id` and mark the older finding `superseded`
4. else mint a new `finding_id`

### Blocker Propagation Rule

- one unresolved `blocking: true` finding forbids `commit`
- one unresolved `blocking: true` finding forbids `stop`
- conflicting blockers with insufficient evidence force `escalate` rather than optimistic pass

### Verify Verdict Merge Rule

The integrator owns final verdict issuance.

The merge algorithm is:

1. collect verifier outputs and three verify-challenge outputs
2. normalize each finding into:
   - `finding_id`
   - blocking
   - evidence class
   - affected scope
   - required plan change
3. dedupe by `finding_id` or explicit `superseded_by` linkage
4. drop any claim with no evidence stronger than `S1`
5. if any remaining blocking finding survives, `commit` is illegal
6. if evidence is conflicting and higher-precedence evidence does not resolve it, emit `escalate`
7. if gates fail but recovery is local, emit `rework`
8. if gates are no longer realistic for the same stage boundary, emit `rescope`
9. only emit `commit` when all quality gates pass and all blocking findings are explicitly closed

### Evidence Packet Minimum Fields

`evidence_packet` must contain at least:

- `plan_snapshot_id`
- `target_fingerprint`
- `artifact_refs`
- `check_results`
- `log_refs`
- `collected_at`
- `freshness_status`
- `stale_reason`

Allowed `freshness_status` values:

- `fresh`
- `stale`

Allowed `stale_reason` values for `evidence_packet`:

- `none`
- `target_drift`
- `snapshot_drift`

If `freshness_status` flips from `fresh` to `stale`, the integrator must append a `decision_ledger` stale-state event naming the affected `evidence_packet_ref`, `stale_reason`, active `plan_snapshot_id`, and active `target_fingerprint`.

If target state changes after evidence collection:

- `evidence_packet.freshness_status` becomes `stale` with `stale_reason=target_drift`
- `commit` becomes illegal until `verify` runs again against the new fingerprint
- if the affected `commit` close has already crossed into `goal_reassessment` or `run_decision`, the integrator must supersede the latest sealed handoff with `post_close_invalidation=target_drift`

If `plan_snapshot_id` changes after evidence collection:

- `evidence_packet.freshness_status` becomes `stale` with `stale_reason=snapshot_drift`
- all blocker closures tied to the old snapshot reopen
- `commit` becomes illegal until `verify` runs again against the new snapshot
- if the affected `commit` close has already crossed into `goal_reassessment` or `run_decision`, the integrator must supersede the latest sealed handoff with `post_close_invalidation=snapshot_drift`

### Cycle-Close Decision Table

`cycle_controller` may issue:

- `rework`
  Local fix is still possible inside the same stage.
- `rescope`
  The stage boundary or gates changed and a new executable snapshot must be published.
- `escalate`
  Human or higher-level arbitration is required.
- `commit`
  The current stage is closed and recorded.

`cycle_controller` may not issue:

- `continue`
- `stop`

Those belong only to `run_controller`.

### Pre-Verify Close Matrix

If `evidence_packet_ref=none_yet`, only these decisions are legal:

- `rescope`
- `escalate`

If `evidence_packet_ref=none_yet`, these decisions are illegal:

- `commit`
- `continue`
- `stop_goal_saturated`
- `stop_escalation_halt`

### Run-Termination Table

After a cycle closes, `run_controller` consumes fresh research and emits:

- `continue`
  At least one admissible improvement candidate remains for the original goal.
- `stop`
  No admissible improvement candidate remains and stop is evidence-legal.

Allowed `stop_reason` values:

- `goal_saturated`
- `escalation_halt`

`stop_reason` is not a separate packet field. It is represented only by `termination_posture=stop_goal_saturated|stop_escalation_halt`.

Live-invocation pause reasons are separate from `stop_reason` and never change `termination_posture`. They explain why control was yielded even though the latest sealed `handoff_packet` remains the only resume authority.

Allowed live-invocation pause reasons:

- unresolved `escalate`
- user-requested pause
- external approval or user decision required
- conflicting dirty changes
- recorded time or resource ceiling

Pause legality rules:

- a pause is legal only if the latest sealed `handoff_packet` already exposes a cold-start-legal resume path
- if the latest controller result is `continue`, the newborn-cycle `research` handoff must be sealed before the live invocation may pause
- a pause may not falsify stage status; unfinished stages remain unfinished in the latest authoritative `revised_plan`
- recorded time or resource ceiling is legal only when a concrete measured cap, quota, runtime limit, or user- or system-imposed limit already in force before the pause is recorded in the latest authoritative `decision_ledger` lineage together with current consumption
- user-visible pause close-out must name the latest current-stage status; if the latest handoff is newborn-cycle `research`, it must say that no current stage exists yet in the newborn cycle and name the most recently closed stage
- user-visible pause close-out must name the stored `resume_entry_state`, whether it is directly dispatchable or lineage-only, any `post_close_invalidation`, and the next mandatory dispatch after fresh preflight

Explicit planning-deliverable completion is not a `run_decision` stop reason. It is represented
only by a terminal `planning` handoff with `termination_posture=stop_planning_deliverable` after
the first challenge-reviewed `integrate_plan` seal when immutable
`request_intent=planning_deliverable_only`.

The required `counter-check` is a mandatory block inside `research_synthesis`, not a separate artifact.

`research_synthesis` must expose that block as `counter_check`, with evidence refs, an explicit
`admissible_candidate_result` verdict of `none` or `some`, and an explicit
`remaining_required_stage_result` verdict of `none` or `some`.

`research_synthesis` must also expose:

- `research_viewpoint_set={architecture_dependency,failure_verification,goal_efficiency}`
- concrete `lane_candidate_refs` showing exactly one merged input lane per viewpoint

`continue` is legal only when fresh exact-three-viewpoint research and its counter-check jointly show at least one
admissible improvement candidate remains, or the latest authoritative `revised_plan` still has at
least one incomplete stage with `stage_obligation=required_for_success`, with evidence refs that
justify keeping the run open.

`continue` is illegal while the latest terminal cycle decision remains unresolved `escalate`.

`continue` is also illegal while any post-close invalidation or fingerprint or snapshot mismatch still requires same-cycle revalidation.

`stop` is legal only when:

- an explicit `stop_reason` is recorded as either `goal_saturated` or `escalation_halt`
- no fingerprint mismatch forces revalidation

If `stop_reason=goal_saturated`, all of these must also hold:

- the latest cycle is fully closed
- no blocking findings remain open
- current success condition is satisfied
- fresh exact-three-viewpoint research finds zero admissible improvement candidates
- a counter-check finds zero additional admissible improvement candidates
- if the latest authoritative `revised_plan.run_intent=implementation_oriented`, no incomplete
  `current_stage` or `remaining_stage_queue` entry with `stage_obligation=required_for_success`
  remains
- if the latest authoritative `revised_plan.run_intent=implementation_oriented`,
  `research_synthesis.counter_check.remaining_required_stage_result=none`

If `stop_reason=escalation_halt`, the latest terminal cycle decision must still be unresolved `escalate`.

`stop_escalation_halt` is legal only inside `run_decision`, only after an unresolved `escalate` has already crossed `cycle_decision -> goal_reassessment -> run_decision`, and never as a generic pre-verify cycle-close token.

## Stage 4: Worker Ownership And Recovery

### Stage 4 Acceptance Target

Stage 4 is closed only if all of these hold:

- every dispatchable worker slice has exactly one open claim owner on one current executable snapshot
- safe parallelism is derived from declared scope before dispatch, not inferred after merge
- conflicting scope forces serialization, invalidation, supersession, or re-scope before further worker writes
- worker output becomes authoritative only through integrator adoption against the current executable snapshot
- cold-start recovery never resumes inside worker execution; it resumes through the latest sealed planning or mismatch-routed control state
- Stage 5 can falsify overlap, stale output, timeout, undeclared write, and recovery behavior without inventing new worker rules

### Ownership Unit Rule

`read_scope` and `write_scope` must be expressed in normalized ownership units chosen by the integrator for the current stage.

The kernel only requires that these units be comparable for overlap.

Typical unit families are:

- file paths
- exported symbols or module surfaces
- schema or contract objects
- generated artifact paths
- document or config sections

If two claims use scope units that cannot be compared for overlap, those claims are not legally dispatchable until the integrator narrows them or re-scopes the stage.

### Parallel Dispatch Rule

Two open claims on the same `plan_snapshot_id` are concurrently dispatchable only when all of these are empty:

- `claim_a.write_scope ∩ claim_b.write_scope`
- `claim_a.write_scope ∩ claim_b.read_scope`
- `claim_a.read_scope ∩ claim_b.write_scope`

`read_scope ∩ read_scope` overlap is legal.

Any non-empty intersection makes the pair non-parallel-safe.

Non-parallel-safe claims may not be concurrently dispatched against the same executable snapshot.

### Claim Admission Rule

The integrator may open a claim only when all of these hold:

- the claim belongs to the current stage
- the claim targets the current executable `plan_snapshot_id`
- `read_scope` and `write_scope` are comparable for overlap
- the claim is pairwise dispatch-safe against every other open claim in the same snapshot
- no other `status=open` claim in that snapshot already owns the same `slice_id`

Worker self-claim is illegal.

If a new claim would violate the parallel dispatch rule, the integrator must serialize, supersede, or re-scope before opening it.

### Worker Output Adoption Rule

Worker output is advisory until the integrator adopts it.

Adoption is legal only when all of these hold:

- the producing claim is still `open`
- the producing claim still targets the current executable `plan_snapshot_id`
- the output touches no ownership unit outside the declared `write_scope`
- no other open claim owns an overlapping `write_scope`
- required Stage 3 evidence exists for the merge decision

If output touches undeclared ownership units, the integrator must reject it or escalate; optimistic merge is illegal.

If output arrives from a stale or closed claim, it is stale evidence only. It may inform audit or replanning, but it may not be merged into the authoritative snapshot.

Any claim-state change that mutates the embedded open-claim set must appear in the next newly sealed authoritative snapshot.

### Conflict Detection And Forced Serialization

If undeclared overlap or incompatible ownership is discovered after claims were already opened:

- all affected claims become non-dispatchable immediately
- no further worker write may be accepted from those claims
- the next integration step must choose exactly one of:
  - invalidate one or more claims
  - supersede claims into disjoint slices on a new snapshot
  - re-scope the stage
  - escalate ownership ambiguity

Optimistic parallel merge across overlapping claims is illegal.

### Interruption And Timeout Recovery

Live worker interruption never resumes inside worker execution state.

On cold start, open claims may be resumed only from the latest sealed planning handoff and only after the integrator revalidates:

- the current executable snapshot
- claim openness
- scope legality
- mismatch status

Any worker-slice re-entry after interruption or cold start requires the integrator to seal a newer snapshot that supersedes the prior open claim with a replacement claim.

The prior open claim must close before the replacement claim dispatches, typically via `superseded`.

Worker disappearance or timeout does not close a claim automatically.

It leaves the claim open but non-running until the next sealed integrator action.

The integrator must then either supersede it with a replacement claim or explicitly transition it by sealing a snapshot that marks it:

- `invalidated`
- `superseded`
- `rejected`
- or `escalated`

Output that arrives after claim closure or snapshot supersession is stale and may not be merged.

Mismatch-routed `research` from `planning` makes any carried `open_write_claims` non-dispatchable until the next `integrate_plan` seal invalidates, supersedes, or republishes them.

Cold-start mismatch-routed `verify` must carry empty `open_write_claims`; any such handoff with carried claims is illegal.

### Worker Recovery Matrix

| Situation | Immediate Effect | Next Legal Action |
| --- | --- | --- |
| open claim, snapshot still current, cold-start at `planning` | claim stays open but non-running | integrator revalidates and seals a newer snapshot that supersedes the old claim with a replacement claim, or explicitly closes it |
| open claim, snapshot superseded | claim becomes stale and non-dispatchable | invalidate or supersede on the next sealed snapshot |
| worker output arrives after claim closed | output is stale evidence only | reject merge; optionally record audit finding |
| undeclared overlap discovered after publish | all affected claims become non-dispatchable | invalidate, supersede, re-scope, or escalate |
| worker timeout or disappearance | claim stays open but non-running | integrator supersedes with replacement claim or explicitly invalidates, rejects, or escalates |
| mismatch-routed `research` with carried claims | carried claims become non-dispatchable | next `integrate_plan` seal invalidates, supersedes, or republishes before further writes |

### Stage 5 Oracle Contract Preview

This kernel requires Stage 5 to define a falsifiable dry-run oracle per scenario.

Detailed Stage 5 coverage and scenario definitions live in [kernel-spec-stage5-oracle-draft.md](./kernel-spec-stage5-oracle-draft.md).

Each scenario must specify:

- `scenario_id`
- `preconditions`
- `injected_fault`
- `expected_transitions`
- `required_artifact_mutations`
- `minimum_evidence`
- `expected_decision`
- `forbidden_shortcuts`
- `exact_fail_conditions`

No dry-run may pass by narrative summary alone.

### Mandatory Stage 5 Coverage Matrix

Stage 5 must include at least one scenario for each of these:

- every mismatch class in the resume mismatch matrix
- the canonical resume contract row for every legal `resume_entry_state`
- every legal seal point in the seal and resume matrix
- executable activation switching only at handoff seal
- invalid-source intake
- run-close bridging for `commit`, `rescope`, and `escalate`
- terminal stop sealing for `stop_goal_saturated` and `stop_escalation_halt`
- post-cycle fresh research publication inside `goal_reassessment`
- blocking-finding close and auto-reopen on fingerprint drift
- blocking-finding close and auto-reopen on snapshot drift
- ledger-backed stale evidence mutation and ledger-backed blocker reopen mutation
- post-close invalidation from `goal_reassessment|run_decision` back to same-cycle `verify`
- stale evidence state transitions on fingerprint drift and snapshot drift
- finding supersession and dedupe lineage
- claim republish lineage and legal claim status transitions
- stale worker claim invalidation after snapshot supersession
- pairwise parallel-safe claims on the same snapshot
- write/write overlap forcing serialization
- write/read overlap forcing serialization
- undeclared out-of-scope worker write rejection
- worker timeout or disappearance without implicit auto-close
- stale worker output arriving after claim closure
- derived-artifact disagreement with the latest sealed `handoff_packet`
- legal and illegal pre-verify close decisions when `evidence_packet_ref=none_yet`
- every legal cycle decision token:
  - `rework`
  - `commit`
  - `rescope`
  - `escalate`
- every legal run decision token:
  - `continue`
  - `stop`

### No Speculative Packet Rule

Before Stage 5 passes:

- no worker packet content
- no challenger packet content
- no verifier packet content
- no public agent asset changes

Only placeholder packet questions are allowed before Stage 5 pass.
