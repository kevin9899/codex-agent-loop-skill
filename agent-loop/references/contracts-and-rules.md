# Contracts And Rules

## Core Invariants

- Keep the loop bounded by explicit stages, explicit next actions, and explicit quality gates.
- Keep the run resumable across many bounded stage cycles.
- Keep source intake content-first.
- Keep research, planning, challenge, execution, and verification as distinct role lanes.
- Keep evidence grounded in files, tests, logs, diffs, and direct source references.
- Keep the repo contract visible whenever execution lands inside a repository.
- Keep the main value in staged plan reconstruction and repeated improvement, not in decorative summarization.
- Keep compact handoff artifacts when the loop spans multiple stages or multiple plan cycles.
- Keep the main CLI thread focused on orchestration and context control rather than broad direct execution.
- Keep `revised_plan` as the only executable snapshot.
- Keep `decision_ledger` audit-only.
- Keep `dispatchable_slice_specs` authoritative and treat `parallel_worker_lanes` as a derived human view.
- Keep the latest sealed `handoff_packet` plus fresh preflight as the only legal resume authority.
- Keep post-close invalidation on the same cycle until fresh `verify` clears it.

## Canonical Contract Layers

Use this file for the operating rules. Use the validated kernel docs when the question is about exact lifecycle or packet shape:

- `kernel-spec-stage1-3-draft.md`
  Lifecycle control, handoff legality, claim recovery, post-close invalidation, and termination behavior. The filename is legacy, but it now carries the validated Stage 1-4 kernel.
- `kernel-spec-stage5-oracle-draft.md`
  Dry-run oracle and conformance scenarios.
- `kernel-spec-stage6-packets-draft.md`
  Canonical role packet fields and role authority.
- `kernel-spec-stage7-packet-templates-draft.md`
  Reusable packet templates, sealed handoff row templates, and the successor handoff selector.

## Agent Model Rules

- Before any delegated lane dispatch, resolve one concrete model pin from the local runtime config plus the current local model catalog.
- If that resolution succeeds, every loop lane in the live invocation must use the same exact `resolved_model_slug` and `resolved_reasoning_effort`.
- In many current Codex runtimes, the resolved hard pin may be `gpt-5.4` with `xhigh`, but the local runtime config and catalog remain authoritative unless the user explicitly overrides them before dispatch.
- `strongest available` is a single pre-dispatch resolution step, not a per-lane heuristic.
- Every delegated loop lane must pass that pin explicitly on the actual `spawn_agent` tool call through `model=<resolved_model_slug>` and `reasoning_effort=<resolved_reasoning_effort>`.
- Omitting either tool-call field is illegal because inherited or default selection may silently downshift.
- Never downshift any loop lane for latency, cost, convenience, hidden defaults, or per-lane heuristics.
- Treat any delegated output produced without the resolved hard pin, or with a weaker model/effort pair, as inadmissible and rerun that lane.

## Source Intake Rules

Accept all of these as valid source inputs:

- Windows path
- POSIX path
- markdown link
- `file://` URL
- pasted markdown
- pasted prose
- goal line plus source body

Required rules:

- if the source is a readable local file, read it directly
- if the source is pasted content, preserve its actual structure
- if both goal and body exist, keep the first line as the working goal candidate
- do not reinterpret a local path as a product runtime feature unless explicitly asked
- source form never changes lifecycle: a plan document, roadmap, authority note, or implementation checklist still enters the same initial `research -> planning -> challenge` path
- prewritten plans are source evidence, not executable authority; only the loop-produced authoritative `revised_plan` may drive execution
- derive request intent from the explicit user ask, not from source-document wording alone
- if the source contains `Run Intent`, delivery mode, or similar control text, treat it as advisory source evidence rather than authority

## Research Rules

Before the first plan lock:

- inspect the current target state
- run deep research for current behavior, constraints, alternatives, and leverage
- run exactly three viewpoint-separated research agents in parallel:
  - `architecture_dependency`
  - `failure_verification`
  - `goal_efficiency`
- planning may consume fresh research only after those three lane outputs are merged into one research synthesis with concrete refs for all three viewpoints

After any cycle closes through `commit|rescope|escalate`:

- run a fresh research pass
- run the same exact three viewpoint-separated research lanes again
- search for a better next ordering
- search for higher-quality implementation paths
- search for newly visible debt or missing work related to the same goal

During goal-level reassessment, including when the current plan appears exhausted:

- run a goal-level research sweep
- run the same exact three viewpoint-separated research lanes again
- compare the original objective with the current codebase state
- continue into a new plan cycle if meaningful improvement remains
- for implementation-oriented runs, stop only later through `goal_reassessment -> run_decision`, either because research concludes that no meaningful improvement remains or because an escalated lineage ends in `stop_escalation_halt`; planning-deliverable-only runs remain the separate terminal `planning` closure path

## Plan Reconstruction Rules

During plan reconstruction, regardless of whether the source already looks executable:

- preserve the original priority structure
- preserve dependency edges unless challenge or research finds a real reason to reorder
- convert broad work into explicit stages
- keep the current stage narrow and execution-bounded
- separate safe parallel worker lanes from the main stage
- convert prose into explicit outputs and explicit gates
- re-expand the plan against the normalized working goal and current target state before accepting it as executable
- add any missing `required_for_success` stages that fresh research reveals
- do not preserve a preparatory endpoint, authority lock, or narrowed success condition as final merely because the source document stops there

Minimum sections for reconstructed revised plans:

- `Run Intent`
- `Working Goal`
- `Success Condition`
- `Current Stage`
- `Parallel Worker Lanes`
- `Remaining Stage Queue`
- `Quality Gates`
- `Research Hooks`
- `Open Questions`
- `Progress Ledger`

## Plan Challenge Contract

Every plan challenge phase must run exactly three challengers in parallel:

- `architecture_dependency`
- `failure_verification`
- `goal_efficiency`

Those challengers must all use the same resolved hard pin for the live invocation.

Required rules:

- use the canonical Stage 6 / Stage 7 `challenge_result_candidate` shape rather than reauthoring a local schema here
- `blocking_findings` must be explicit rather than implied
- `execution_ready: true` requires no unresolved blocking findings
- challengers attack the plan; they do not silently implement the fix
- the revised plan must merge all accepted findings before execution starts

## Execution Rules

Default behavior depends on the request:

- if the user explicitly asked only for a planning or analysis deliverable, stop only after the first challenge-reviewed authoritative `revised_plan` is sealed
- if the user asked for implementation or clearly wants end-to-end progress, enter the stage loop

Execution should then:

- work one current stage at a time
- decompose safe parallel worker slices
- keep worker scope narrow
- preserve evidence
- update the revised plan as the source of truth
- avoid drifting back into broad backlog mode
- keep the same lifecycle regardless of input shape; a source that already looks like a plan still goes through fresh research, plan reconstruction, and plan challenge before execution
- for `run_intent=implementation_oriented`, do not treat completion of a preparatory or authority-lock stage as a user-visible stop while any incomplete `required_for_success` stage remains in the latest authoritative `revised_plan`
- for `run_intent=implementation_oriented`, a legal `continue` is a keep-going directive for the live invocation unless an explicit pause reason is recorded
- `stage_closed` is cycle-local and `run_stopped` is run-level; a non-terminal stage close never grants stop authority by itself
- only the main run owner / orchestrator may classify live-invocation termination, authorize `final`, or convert a closed stage into a legal pause or terminal stop posture
- after any non-terminal `commit|rescope|escalate`, the lifecycle must enter `post_close_reassessment_pending` before any legal yield or next-cycle-open decision
- `post_close_reassessment_pending` is not itself a legal yield, pause, or terminal posture; it must clear through reassessment research and `goal_reassessment -> run_decision` before any valid close-out classification exists
- before ending the live invocation, the orchestrator must perform a stop checklist:
  - identify the latest authoritative `Current Stage`
  - identify whether any incomplete `required_for_success` stage remains
  - identify whether the loop has terminal planning-deliverable closure, a terminal `run_decision` stop posture, or only an explicit live-invocation pause reason
  - run the termination classifier only after `goal_reassessment -> run_decision`; stage-close language, handoff sealing, or a completed commit cannot pre-authorize it
  - emit an explicit `closeout_classification` chosen from `continue_same_invocation | live_pause | stop_planning_deliverable | stop_goal_saturated | stop_escalation_halt`
  - any `closeout_classification` emitted while `post_close_reassessment_pending` is still active is invalid
  - if classification is missing or ambiguous, default to `continue_same_invocation`
  - `stop_planning_deliverable` is legal only for `run_intent=planning_only`
  - if `run_decision=continue` and no explicit pause reason exists, continuing the loop is mandatory
  - `stage boundary`, `phase closed`, `handoff sealed`, or similar wording is never a legal stop or pause reason
  - immediately after entering `post_close_reassessment_pending`, emit a transcript-visible `Reassessment Pending` commentary receipt
  - that `Reassessment Pending` receipt must include `receipt_id`, `stage_close_event_id`, `reassessment_state=post_close_reassessment_pending`, `most_recently_closed_stage`, `handoff_packet_id`, `revised_plan_version`, and `next_mandatory_dispatch=reassessment_research`
  - the termination classifier has no hidden transcript-external form; its chosen `closeout_classification` becomes authoritative only through the canonical immediate receipt for that classification
  - if `run_decision=continue` and no explicit pause reason exists, `final` is illegal and the immediate next user-visible message must be a `Cycle Opened` commentary receipt
  - that `Cycle Opened` receipt must include `receipt_id`, `prev_receipt_id`, `closeout_classification=continue_same_invocation`, `pause_reason=null`, `most_recently_closed_stage`, `next_current_stage`, `run_decision=continue`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`
  - after `Cycle Opened`, emit a transcript-visible `Dispatch Started` commentary receipt before any later yield or stop claim
  - that `Dispatch Started` receipt must include `receipt_id`, `prev_receipt_id`, `dispatch_started=next_mandatory_dispatch`, and `current_stage=next_current_stage`
  - if the loop yields through `live_pause`, the immediate next and final user-visible message must be a transcript-visible `Pause Receipt`
  - that `Pause Receipt` must include `receipt_id`, `prev_receipt_id`, `closeout_classification=live_pause`, `run_decision=continue`, `pause_reason`, the latest authoritative current-stage status or `newborn_cycle_current_stage=null`, `most_recently_closed_stage` when applicable, `resume_entry_state`, `resume_dispatchability`, any `post_close_invalidation`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`
  - if `pause_reason=unresolved escalate`, the `Pause Receipt` must also include `escalation_blocker`
  - if `pause_reason=user-requested pause`, the `Pause Receipt` must also include `user_pause_request_ref`
  - if `pause_reason=external approval or user decision required`, the `Pause Receipt` must also include `pending_decision_question` and `approval_or_option_set`
  - if `pause_reason=conflicting dirty changes`, the `Pause Receipt` must also include `conflicting_path_set`
  - if `pause_reason=recorded time or resource ceiling`, the `Pause Receipt` must also include `measured_cap`, `current_consumption`, and `limit_source`
  - if the loop ends through terminal run stop, the immediate next and final user-visible message must be a transcript-visible `Stop Receipt`
  - that `Stop Receipt` must include `receipt_id`, `prev_receipt_id`, `closeout_classification`, `termination_posture`, `run_decision=stop`, `goal_reassessment_completed=true`, `most_recently_closed_stage`, the latest authoritative current-stage status, `required_for_success_remaining_count`, `required_for_success_stage_ids_or_hash`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and the concrete stop basis
  - in every `Stop Receipt`, `closeout_classification` must equal `termination_posture`, and both must be one of `stop_goal_saturated|stop_escalation_halt`
  - if `termination_posture=stop_goal_saturated`, `required_for_success_remaining_count` must equal `0`
  - if the loop ends through terminal planning-deliverable closure, the immediate next and final user-visible message must be a transcript-visible `Planning Complete Receipt`
  - that `Planning Complete Receipt` must include `receipt_id`, `closeout_classification=stop_planning_deliverable`, `run_intent=planning_only`, `terminal_handoff_kind=planning`, `terminal_state=integrate_plan`, the latest authoritative stage status, `handoff_packet_id`, and `revised_plan_version`
  - a stage-close summary, handoff summary, or any other wrap-up message cannot substitute for any canonical receipt
  - if the loop is only pausing, the latest sealed `handoff_packet` must already encode the authoritative resume path; if `run_decision=continue`, that means the newborn-cycle `research` handoff is already sealed before control returns to the user
  - if the pause reason is recorded time or resource ceiling, the measured cap must be named concretely and must already be backed by the latest authoritative `decision_ledger` lineage; vague ceiling language is illegal
  - if the agent cannot name a legal stop posture or legal pause reason, user-visible termination is illegal

Terminal end categories are:

- terminal planning-deliverable closure through dedicated `closeout_classification=stop_planning_deliverable`
- terminal run stop postures listed below

Planning-deliverable closure is not a terminal run stop posture and may not be emitted through a `Stop Receipt`.

Terminal run stop postures are limited to:

- `stop_goal_saturated`
- `stop_escalation_halt`

Live-invocation pause reasons are limited to:
- unresolved `escalate`
- user-requested pause
- external approval or user decision required
- conflicting dirty changes
- recorded time or resource ceiling

Pause legality rules:

- a pause reason never changes `termination_posture`; it only explains why the live invocation yielded while the latest sealed handoff remained authoritative
- before yielding, the orchestrator must preserve the latest authoritative `Current Stage` truthfully; it may not mark a stage closed unless the cycle actually closed through `commit|rescope|escalate`
- user-visible close-out for any pause must identify:
  - whether the latest authoritative current stage is closed or still open; if the latest handoff is a newborn cycle with no current stage yet, say that explicitly and name the most recently closed stage
  - the latest sealed `resume_entry_state`
  - whether that `resume_entry_state` is directly dispatchable or lineage-only
  - any carried or fresh `post_close_invalidation`
  - the next mandatory dispatch after fresh preflight, including any conditional reroute if invalidation is present
  - the concrete pause reason
- recorded time or resource ceiling is legal only when a concrete measured budget, quota, runtime cap, or user- or system-imposed limit already in force before the pause was actually reached or would be exceeded by continuing
- recorded time or resource ceiling is legal only when the latest authoritative `decision_ledger` lineage records the pause basis, concrete cap, current consumption, and the specific next mandatory dispatch expected to cross the limit if continuing
- recorded time or resource ceiling may not be used as a soft fallback immediately after a successful stage close if the loop can still cheaply complete the required successor seal for the current authoritative state

Illegal exit signatures:

- incomplete `required_for_success` work remains, yet the live invocation ends without terminal stop posture or legal pause reason
- the live invocation yields or terminates while `post_close_reassessment_pending` is still active
- a non-terminal stage close occurs without the immediate transcript-visible `Reassessment Pending` receipt
- the canonical receipt chain is broken: missing `receipt_id`, invalid `prev_receipt_id`, or a `reassessment_receipt_ref` that does not resolve to the transcript-visible `Reassessment Pending` receipt
- `run_decision=continue` and no pause reason exists, yet the agent uses `final`
- a non-terminal stage close is presented as sufficient reason to stop or yield
- any worker, challenger, or stage-integrator output is treated as if it could authorize `final`, a legal pause, or a terminal run stop without the orchestrator's post-reassessment classifier
- `closeout_classification` is missing, ambiguous, or uses any value outside the canonical set
- `run_decision=continue` yields without the immediate transcript-visible `Cycle Opened` commentary receipt or, for legal pauses, without the required pause payload
- `Cycle Opened` is the terminal message of the invocation without a later `Dispatch Started` receipt
- the `Cycle Opened` receipt is missing any required field: `receipt_id`, `prev_receipt_id`, `closeout_classification=continue_same_invocation`, `pause_reason=null`, `most_recently_closed_stage`, `next_current_stage`, `run_decision=continue`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, or `next_mandatory_dispatch`
- a `Dispatch Started` receipt is missing any required field: `receipt_id`, `prev_receipt_id`, `dispatch_started=next_mandatory_dispatch`, or `current_stage=next_current_stage`
- a `Pause Receipt` is missing any required field: `receipt_id`, `prev_receipt_id`, `closeout_classification=live_pause`, `run_decision=continue`, `pause_reason`, authoritative stage status or newborn-cycle marker, `resume_entry_state`, `resume_dispatchability`, `post_close_invalidation`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, or `next_mandatory_dispatch`
- a `Pause Receipt` is missing required reason-specific evidence for its chosen `pause_reason`
- a `Stop Receipt` is missing any required field: `receipt_id`, `prev_receipt_id`, `closeout_classification`, `termination_posture`, `run_decision=stop`, `goal_reassessment_completed=true`, `most_recently_closed_stage`, authoritative stage status, `required_for_success_remaining_count`, `required_for_success_stage_ids_or_hash`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, or concrete stop basis
- a `Stop Receipt` has mismatched `closeout_classification` and `termination_posture`, or either value falls outside `stop_goal_saturated|stop_escalation_halt`
- a `Stop Receipt` claims `termination_posture=stop_goal_saturated` while `required_for_success_remaining_count` is nonzero
- any canonical receipt omits lineage binding or contradicts the latest sealed `handoff_packet` / authoritative `revised_plan`
- a `Planning Complete Receipt` is missing any required field: `receipt_id`, `closeout_classification=stop_planning_deliverable`, `run_intent=planning_only`, `terminal_handoff_kind=planning`, `terminal_state=integrate_plan`, authoritative stage status, `handoff_packet_id`, or `revised_plan_version`
- a `Planning Complete Receipt` is emitted through a `Stop Receipt` path or claims any `termination_posture`
- any user-visible wrap-up appears between non-terminal stage close classification and the required canonical receipt
- `phase-close-as-run-stop` is a violation class; default recovery is `resume/reassess`, not acceptance of the exit

## Verification Rules

Before a stage may close:

- run the defined checks
- collect direct evidence
- run exactly three fresh verify challengers in parallel:
  - `architecture_dependency`
  - `failure_verification`
  - `goal_efficiency`

Those verify challengers must all use the same resolved hard pin for the live invocation.

Required rules:

- verify challengers must be fresh rather than reused from plan challenge
- a stage is not verification-complete while blocking findings remain
- challenge findings after verification must feed back into implementation or explicit re-scope
- do not commit a stage with unresolved blocking findings
- post-close invalidation routes back through same-cycle `verify` before any new cycle may proceed

## Commit Rules

When execution lands inside a git repository:

- commit each stage only after it passes its quality gates and verify challenge
- keep commits aligned to the current stage boundary
- do not roll broad multi-stage churn into one commit

## Retry Rules

Use local retry for:

- a narrow evidence gap
- a specific blocked worker step
- one failed check
- one integration seam
- one verify challenge finding set tied to the current stage

Do not restart the whole run for:

- one bad implementation attempt
- one failing test
- one better-but-optional alternative
- one incomplete note in the source document

## Escalation Rules

Escalate when:

- the same blocker repeats
- a user decision is required
- the repo has conflicting dirty changes
- retries produce no meaningful delta
- the current stage cannot satisfy its quality gates without re-scoping
- fresh research invalidates the current stage assumptions

Escalation is a deliberate stop of the current stage / cycle path, not a softer retry. Direct run termination, if it happens, is later decided in `goal_reassessment -> run_decision`.

## Quality Gate Rules

Before execution of a stage begins, make the gates explicit:

- required checks
- acceptance criteria
- must-pass blockers
- verification bar
- commit bar

After that:

- do not silently soften the bar
- do not claim success while blockers remain
- do require explicit re-scoping if the bar is no longer realistic

## Evidence Hierarchy

Prefer evidence in this order:

1. actual source document or file content
2. actual diff or artifact
3. test results
4. logs and traces
5. compact execution metadata
6. narrative agent explanation

The later an item appears in this list, the less it should be trusted on its own.

## Context Control Rules

- keep the main CLI thread focused on orchestration, evidence integration, and plan updates
- give workers only the context they need for their own stage slice
- give challengers the plan or verification packet, not the whole transcript
- prefer compact handoff artifacts over replaying long history

## Informational Re-Entry Summary

If the loop continues across stages or plan cycles, it can still help to preserve a compact human-readable summary such as:

- working goal
- success condition
- current stage status
- remaining stage queue
- unresolved blockers
- accepted challenge findings
- quality gates
- progress ledger
- evidence summary

This summary is informational only. It does not replace the validated resume authority.

The next dispatch must still come only from the latest sealed `handoff_packet` after fresh preflight against current target state. `revised_plan`, claim state, and evidence remain handoff-referenced authoritative state consulted through that sealed lineage. Use the summary to help the operator reason, not to define a second resume protocol.
