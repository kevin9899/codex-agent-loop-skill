# Process Architecture

## What This Skill Actually Does

This skill defines a reusable personal `$loop` process for software work. The core idea is:

- accept local source material through `$loop` or `$agent-loop`
- normalize it into a working goal plus source packet
- analyze the current target and run deep research
- reconstruct the source into a staged executable plan
- challenge and revise that plan before execution
- execute one bounded stage at a time with fresh verify challenge
- close the stage by commit when applicable, or by explicit re-scope / escalate when not
- decide continue vs stop only after later goal reassessment and run decision
- run fresh research and keep routing through later goal reassessment and run decision while meaningful improvement remains

The loop is not "let one giant agent keep thinking forever," and it is not "add a `/loop` runtime feature to the repo." It is a controlled Codex-side automation workflow with explicit inputs, explicit role lanes, explicit challenge gates, explicit verification, stage commits, and repeated improvement cycles until later `goal_reassessment -> run_decision` decides continue or stop for the goal.

`SKILL.md` remains the canonical reflected operator procedure. This file is the mental-model layer.

## Canonical Detail Layers

Use this file for the high-level story of the loop. Use the validated detail layers when the work depends on exact lifecycle or packet rules:

- `kernel-spec-stage1-3-draft.md`
  Lifecycle control, authority boundaries, handoff rows, invalidation, recovery, and termination. The filename is legacy, but it now carries the validated Stage 1-4 kernel.
- `kernel-spec-stage5-oracle-draft.md`
  Falsifiable dry-run scenarios and conformance expectations.
- `kernel-spec-stage6-packets-draft.md`
  Canonical role packet contracts.
- `kernel-spec-stage7-packet-templates-draft.md`
  Reusable packet skeletons, sealed handoff row templates, and successor selector tables.

## Source Intake Flow

The operator surface is simple:

- `$loop`
- `$agent-loop`

Accepted inputs:

- Windows local path
- POSIX local path
- markdown link
- `file://` URL
- pasted markdown
- pasted prose
- goal line plus document body

Source intake exists to turn raw local material into a working goal plus source packet before any planning or execution begins. Use `SKILL.md` for the operator checklist; this layer only defines the intake surface and why it exists.

## Run Versus Cycle

- `run`
  The larger improvement effort bound to the original goal.
- `cycle`
  One bounded stage-execution loop inside that run.

This distinction matters because:

- one cycle should stay finite
- one cycle should close through verify and challenge, then either commit when applicable or rescope / escalate explicitly
- a run can continue across many cycles and many plan revisions
- the next cycle should resume from compact plan artifacts, not from raw transcript replay

## Role Lanes

The loop is orchestrated through explicit role lanes:

- `research`
  Finds current state, risks, alternatives, higher-leverage directions, and late improvement opportunities.
- `planning`
  Builds or revises the staged executable plan from source plus research.
- `challenge`
  Runs three parallel viewpoints against the plan or the verification artifacts.
- `execution`
  Implements the current stage through bounded workers.
- `verification`
  Runs checks, interprets artifacts, and prepares evidence for verify challenge.
- `orchestration`
  Lives in the main CLI thread and keeps context small, state explicit, and stage boundaries clean.

All of these lanes should use the same resolved strongest hard pin for the live invocation. In many current Codex runtimes this may resolve to `gpt-5.4` with `xhigh`, but the local runtime config and catalog remain authoritative unless the user explicitly overrides them before dispatch. The operator must pass that pair explicitly on every delegated `spawn_agent` call rather than relying on inherited defaults. This loop is not designed to save cost by downshifting research, planning, challenge, verification, or execution judgment.

## Challenge Viewpoints

Run exactly three challengers for each challenge phase:

1. `architecture_dependency`
   Focus on structure, dependency order, ownership seams, and hidden coupling.
2. `failure_verification`
   Focus on bugs, regressions, missing gates, observability gaps, and weak verification.
3. `goal_efficiency`
   Focus on drift from source intent, overscope, inefficient sequencing, and better leverage.

These three viewpoints run:

- once before implementation to attack the plan
- once after implementation and verification artifacts exist to attack the current stage result

Fresh challengers are required for verification so they are not anchored to their earlier plan judgments.

## End-To-End Flow

Conceptually, the loop moves through:

- intake and normalization
- target analysis and research
- staged plan reconstruction
- three-viewpoint challenge and revision
- one bounded stage of execution
- verification plus three fresh verify challengers
- stage close through commit when applicable, or explicit rescope / escalate when not
- later goal reassessment and run decision for continue vs stop
- fresh research and next-cycle reassessment

The crucial property is that the system should be able to preserve resumability at a stage boundary, with a compact plan artifact and evidence ledger, and resume later without replaying a huge conversation history. This is a resume-legality statement, not default permission to yield after any non-terminal stage close.

In the validated kernel, that resumability comes from the latest sealed `handoff_packet` after fresh preflight. `revised_plan`, evidence, and claim state are only the handoff-referenced authoritative state consulted through that sealed lineage, not parallel resume authority.

Operationally, the loop must distinguish three end categories: terminal planning-deliverable closure, terminal run stop, and live-invocation pause. Only `stop_goal_saturated|stop_escalation_halt` are terminal run stop postures; `stop_planning_deliverable` remains the separate planning-only terminal planning closure. Reasons such as user pause, approval wait, dirty-change conflict, or recorded time/resource ceiling are non-terminal pauses and are legal only after the latest sealed `handoff_packet` already exposes the authoritative cold-start resume path. A ceiling pause must also name the concrete measured cap, current consumption, whether the stored resume state is directly dispatchable or lineage-only, and the next mandatory dispatch after fresh preflight.

That planning-deliverable terminal path is legal only for `run_intent=planning_only`; an implementation-oriented run may not relabel itself as planning-complete to escape the post-close reassessment and termination-classifier path.

For implementation-oriented runs, every non-terminal `commit|rescope|escalate` first enters `post_close_reassessment_pending`. The only legal path out of that state is:

`post_close_reassessment_pending` is a non-yield state. While it remains active, the loop may emit progress `commentary`, but it may not emit `final`, pause, or any terminal-looking wrap-up.
The immediate transcript-visible marker for entering that state is a `Reassessment Pending` commentary receipt containing `receipt_id`, `stage_close_event_id`, `reassessment_state=post_close_reassessment_pending`, `most_recently_closed_stage`, `handoff_packet_id`, `revised_plan_version`, and `next_mandatory_dispatch=reassessment_research`.

- `stage_close`
- `reassessment research`
- `goal_reassessment -> run_decision`
- `termination classifier`
- one of:
  - `open next cycle`
  - `legal live pause`
  - `terminal run stop`

That means `non_terminal_stage_close -> return control` and `non_terminal_stage_close -> run stop` are both illegal transitions.

The termination classifier belongs to the main run owner / orchestrator. Workers, challengers, and stage integrators may supply evidence to it, but they may not authorize `final`, declare a legal pause, or turn a cycle-local close into a terminal run stop on their own.
The termination classifier has no hidden transcript-external form; it becomes authoritative only through the canonical immediate receipt for the chosen close-out class.

If the classifier resolves `continue_same_invocation`, the immediate next user-visible message must be the transcript-visible `Cycle Opened` commentary receipt. Any intervening wrap-up, pseudo-stop summary, or `final` message is an illegal-exit signature rather than a softer form of continuation.
If the classifier resolves `continue_same_invocation`, the immediate next user-visible message must be a `Cycle Opened` commentary receipt containing `receipt_id`, `prev_receipt_id`, `closeout_classification=continue_same_invocation`, `pause_reason=null`, `most_recently_closed_stage`, `next_current_stage`, `run_decision=continue`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`. A stage-close summary or `final` close-out cannot stand in for that receipt. It must then be followed by a `Dispatch Started` commentary receipt containing `receipt_id`, `prev_receipt_id`, `dispatch_started=next_mandatory_dispatch`, and `current_stage=next_current_stage`.
If the classifier resolves `live_pause`, the immediate next and final user-visible message must be a transcript-visible `Pause Receipt` containing `receipt_id`, `prev_receipt_id`, `closeout_classification=live_pause`, `run_decision=continue`, `pause_reason`, the latest authoritative current-stage status or `newborn_cycle_current_stage=null`, `most_recently_closed_stage` when applicable, `resume_entry_state`, `resume_dispatchability`, any `post_close_invalidation`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`. The `Pause Receipt` must also carry reason-specific proof: `escalation_blocker`, `user_pause_request_ref`, `pending_decision_question` plus `approval_or_option_set`, `conflicting_path_set`, or `measured_cap` plus `current_consumption` plus `limit_source`, depending on `pause_reason`.
If the classifier resolves `stop_goal_saturated|stop_escalation_halt`, the immediate next and final user-visible message must be a transcript-visible `Stop Receipt` containing `receipt_id`, `prev_receipt_id`, `closeout_classification`, `termination_posture`, `run_decision=stop`, `goal_reassessment_completed=true`, `most_recently_closed_stage`, the latest authoritative current-stage status, `required_for_success_remaining_count`, `required_for_success_stage_ids_or_hash`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and the concrete stop basis. In every `Stop Receipt`, `closeout_classification` must equal `termination_posture`, and both must be one of `stop_goal_saturated|stop_escalation_halt`. `stop_goal_saturated` is legal only when `required_for_success_remaining_count=0`.
If the loop ends through `stop_planning_deliverable`, the immediate next and final user-visible message must be a transcript-visible `Planning Complete Receipt` containing `receipt_id`, `closeout_classification=stop_planning_deliverable`, `run_intent=planning_only`, `terminal_handoff_kind=planning`, `terminal_state=integrate_plan`, the latest authoritative stage status, `handoff_packet_id`, and `revised_plan_version`. Planning-deliverable closure is a separate terminal planning path, not a `Stop Receipt` variant and not a terminal run stop posture.

## Plan Reconstruction

When the source is broad, reconstruct it into explicit sections:

- `Working Goal`
- `Success Condition`
- `Current Stage`
- `Parallel Worker Lanes`
- `Remaining Stage Queue`
- `Quality Gates`
- `Research Hooks`
- `Open Questions`
- `Progress Ledger`

The point is not to paraphrase the source note. The point is to recover the real execution structure of the work and make later cycles resumable.

## Stage Loop

Every stage loop should preserve this structure:

- one current stage at a time
- bounded worker slices only where safe
- direct evidence before closure
- verification plus three fresh verify challengers
- close by commit when applicable, otherwise by explicit rescope or escalate
- use later goal reassessment and run decision for continue vs stop
- fresh research before the next stage or next cycle
- the required transcript-visible `Cycle Opened` receipt when the run stays live across stage boundaries

## Goal-Level Reassessment

Plan completion is not automatic termination.

Goal-level reassessment is not only for full-plan exhaustion. It should run after any cycle closes through `commit|rescope|escalate`, with plan exhaustion being the most common saturation case.

During goal-level reassessment:

- re-open the original goal
- inspect the current codebase again
- run fresh research for higher quality, better leverage, missing improvements, or structural refinement
- if worthwhile improvement remains, issue the next revised plan and continue

For `run_intent=implementation_oriented`, a legal `continue` is not a default user-visible stop.
If no explicit pause reason exists, the live invocation should open the next cycle immediately
rather than returning control merely because one preparatory stage closed cleanly.

If that next cycle is opened in the same live invocation, the agent should emit a transcript-visible `Cycle Opened` commentary receipt naming the most recently closed stage, the next current stage, and the next mandatory dispatch. If a legal pause is taken instead, that receipt is replaced by the required `Pause Receipt`; if the run stops, it is replaced by the required `Stop Receipt` or `Planning Complete Receipt`. `final` is therefore reserved for canonical pause and stop receipts only.
Those receipts are the transcript-visible audit markers for every close-out classification: the correct immediate receipt must appear right after the termination classifier resolves, it must carry lineage binding back to the latest sealed handoff and revised-plan version, it must participate in a valid `receipt_id` / `prev_receipt_id` chain anchored by `Reassessment Pending`, and its absence, field mismatch, delayed emission, broken chaining, or contradiction against authoritative lineage should be treated as `phase-close-as-run-stop`, whose default recovery is `resume/reassess`.

For implementation-oriented runs, run termination happens only later through `goal_reassessment -> run_decision`: either `stop_goal_saturated` when fresh research says there is no meaningful improvement left for the original goal, or `stop_escalation_halt` when an escalated lineage cannot be resolved. Planning-deliverable-only runs remain the separate terminal `planning` closure path.

## Optional Repo Handoff

If the revised plan needs to land inside a repository:

- read the repo contract first
- respect the dirty worktree
- work from the revised plan, not from vague backlog prose
- treat the repository as the execution target, not the definition of the loop itself

Productizing this into a repo runtime or a slash-command surface is a separate, downstream task. It is not the default architecture of this skill.
