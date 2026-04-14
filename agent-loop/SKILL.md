---
name: agent-loop
description: "Use via `$loop` or `$agent-loop` inside Codex when you need to turn a local document path, markdown link, pasted backlog, or rough execution note into a highest-model multi-agent software-improvement loop. This is personal Codex automation first: ingest local sources, analyze the current codebase, run three viewpoint-separated research lanes, build a staged executable plan, challenge it with three challenger agents, execute stage by stage with bounded workers, verify with three fresh challengers, close each stage through commit when applicable or through rescope/escalate when not, refresh research, and keep looping until later run-level reassessment decides continue or stop for the original goal."
---

# Agent Loop

`agent-loop` is a personal Codex automation skill. Its primary job is not to add a `/loop` product feature to a repository. Its primary job is to help Codex read local source material, analyze the current target, reconstruct that material into an executable staged plan, attack the work through exact viewpoint-separated research and challenge lanes, execute one stage at a time, verify that stage through multiple challenge viewpoints again, close the stage through commit when applicable or through rescope / escalate when not, and keep improving the plan until later `goal_reassessment -> run_decision` decides continue or stop for the original goal. The validated kernel behind that flow now includes explicit lifecycle control, falsifiable dry-run oracles, canonical role packets, and reusable packet templates.

## Operator Surface

Within the reflected docs, `SKILL.md` is the canonical end-to-end operator procedure. Supporting references should explain mental model, invariants, and validated detail layers without reauthoring the full operator checklist.

Primary entrypoints:

- `$loop`
- `$agent-loop`

Accepted source forms:

- Windows local path
- POSIX local path
- markdown link
- `file://` URL
- pasted markdown
- pasted prose or backlog note
- goal line plus source body

Examples:

```text
$loop C:\Projects\notes\pending-improvements.md
```

```text
$loop [Plan](./docs/plan.md:12)
```

```text
$loop 학습 세션에서 오류나 버그를 찾고 개선점을 찾은 뒤 수정을 시작해줘
```

## Start

1. Read the host project's contract files first when the loop targets a repository or implementation surface:
   - `AGENTS.md`
   - `CLAUDE.md`
   - equivalent local engineering instructions
2. Resolve the `$loop` input before planning:
   - If the argument is a quoted local path, Windows path, POSIX path, markdown link, or `file://` URL, read that file directly from the local filesystem.
   - If the argument is pasted markdown or prose, treat that pasted content as the source document.
   - If both a goal line and a document body are present, keep the first line as the working goal candidate and treat the remainder as the source document.
   - Treat this as trusted Codex-side automation. Do not reinterpret local paths as product or application runtime features unless the user explicitly asks for that work.
   - Input form never changes the lifecycle. A prewritten plan, roadmap, authority note, or implementation checklist still enters the same initial `research -> planning -> challenge` path before any implementation-stage execution decision.
3. Normalize the source into a working objective and source packet:
   - extract the current objective
   - extract success conditions if present
   - derive explicit request intent from the user's ask rather than from source-document wording alone
   - preserve original priorities, constraints, and dependency hints
4. Analyze the current target before locking a plan:
   - inspect the current codebase or target artifacts
   - gather the current constraints, risks, and ownership surfaces
   - keep evidence compact and source-backed
   - resolve the delegated-lane model pin from the local Codex runtime before any lane dispatch
   - when the runtime exposes a concrete strongest model and max reasoning effort, hard-pin that exact pair for the full live invocation
   - in many current Codex runtimes this may resolve to `gpt-5.4` with `xhigh`, but the local runtime/catalog remains authoritative unless the user explicitly overrides it
   - every delegated `spawn_agent` call must pass `model=<resolved_model_slug>` and `reasoning_effort=<resolved_reasoning_effort>` explicitly; inherited or default selection is illegal
5. Run the initial research lane before plan lock:
   - run exactly three viewpoint-separated research agents in parallel on the resolved strongest hard pin:
     - `architecture_dependency`
     - `failure_verification`
     - `goal_efficiency`
   - synthesize the three lane outputs into one merged research candidate before planning starts
   - let research surface higher-leverage approaches, risks, and missing context
6. Draft a staged executable plan:
   - convert rough notes into explicit stages
   - keep the current stage narrow and execution-bounded
   - separate parallelizable worker lanes from the main stage frontier
   - define quality gates before implementation starts
7. Run three plan challengers in parallel on the resolved strongest hard pin:
   - `architecture_dependency`
   - `failure_verification`
   - `goal_efficiency`
8. Merge the three challenge outputs into a revised plan:
   - fix blockers
   - fix ordering mistakes
   - fix missing gates
   - fix drift from the original goal
9. If the user explicitly asked only for a planning, analysis, or loop-design deliverable, end the run only after the first challenge-reviewed authoritative `revised_plan` is sealed through the terminal `planning` handoff at `integrate_plan`.
   - Source form is never sufficient to change the lifecycle or skip the initial `research -> planning -> challenge` path.
   - A plan document remains source input to reconstruct and challenge, not executable authority by itself.
10. Otherwise start the stage loop:
    - select the current stage from the revised plan
    - decompose parallelizable slices into bounded worker tasks
    - keep the main CLI thread focused on orchestration, integration, and context minimization
11. Execute the current stage:
    - use the resolved strongest hard pin for every planning, research, execution, challenge, and verification agent
    - if any delegated lane runs without the explicit pin fields or on a weaker model/effort, discard that output and rerun the lane on the resolved hard pin
    - run parallel workers only on disjoint or safely coordinated slices
    - preserve compact evidence from files, diffs, tests, and logs
12. Verify the current stage:
    - run the target checks
    - run three fresh verify challengers in parallel on the resolved strongest hard pin
    - revise, `rework`, and re-verify until the stage can close through `commit|rescope|escalate`
13. Close the current stage:
    - commit when the stage passes its gates and the target is a repo with git available
    - rescope when verification shows the current stage boundary is wrong but the run should continue
    - escalate when the current stage / cycle path must stop and be handed to later reassessment
    - only the main run owner / orchestrator may classify live-invocation end state, authorize `final`, or choose a terminal stop posture; worker, challenger, and stage-integrator outputs may help close a stage but never stop the run
14. After any cycle closes through `commit|rescope|escalate`, run a fresh reassessment research lane:
    - enter `post_close_reassessment_pending` immediately after the non-terminal stage close
    - `post_close_reassessment_pending` is a non-yield state; while it remains active, only progress `commentary` is legal and any `final` close-out is illegal
    - `non_terminal_stage_close -> return control` is illegal until reassessment research and `goal_reassessment -> run_decision` have completed
    - `non_terminal_stage_close -> terminal run stop` is illegal unless later `goal_reassessment -> run_decision` explicitly sealed `stop_goal_saturated|stop_escalation_halt`
    - before any user-visible close-out, seal an explicit `closeout_classification`; if it is missing or ambiguous, default it to `continue_same_invocation`
    - rerun the same three viewpoints on the resolved strongest hard pin:
      - `architecture_dependency`
      - `failure_verification`
      - `goal_efficiency`
    - search for more efficient directions
    - search for missed implementation risks
    - search for higher-quality approaches aligned to the same goal
    - revise the remaining plan before starting the next stage
15. When the full plan is complete, run the same exact-three-viewpoint goal-level research sweep against the original objective and the current codebase.
16. If that sweep finds meaningful improvement opportunities, produce the next revised plan and repeat the stage loop.
17. Other than the explicit planning-deliverable completion in step 9, stop only through `goal_reassessment -> run_decision`, either because fresh research concludes that there is no worthwhile remaining improvement path for the original objective (`stop_goal_saturated`) or because an escalated lineage cannot be resolved (`stop_escalation_halt`).
   - For `run_intent=implementation_oriented`, `stop_goal_saturated` is illegal while the latest authoritative `revised_plan` still contains any incomplete `required_for_success` stage.
   - Before returning control to the user after any non-terminal stage close, run an explicit stop gate:
     - confirm whether the latest authoritative `revised_plan` still has any incomplete `required_for_success` stage
     - confirm whether `run_decision=continue`, a terminal stop posture, or only a live-invocation pause reason was actually established
     - run the termination classifier only after `goal_reassessment -> run_decision`; stage-close wording, a sealed handoff, or a completed commit may not satisfy it by themselves
     - classify the close-out explicitly as one of: `continue_same_invocation | live_pause | stop_planning_deliverable | stop_goal_saturated | stop_escalation_halt`
     - if no explicit classification is available, default to `continue_same_invocation`
     - `closeout_classification` is legal only after `post_close_reassessment_pending` has cleared through reassessment research and `goal_reassessment -> run_decision`
     - `stop_planning_deliverable` is legal only for `run_intent=planning_only`
     - treat `stop_goal_saturated|stop_escalation_halt` as the only terminal run stop postures
     - treat unresolved `escalate`, user-requested pause, external approval or user decision required, conflicting dirty changes, and recorded time or resource ceiling as live-invocation pause reasons only
     - `stage boundary`, `phase closed`, `handoff sealed`, or similar wording is not a legal stop or pause reason
     - if `run_decision=continue` and no explicit pause reason exists, do not end the turn, do not use `final`, and open the next cycle immediately
     - immediately after entering `post_close_reassessment_pending`, emit a transcript-visible `Reassessment Pending` commentary receipt
     - that `Reassessment Pending` receipt must include `receipt_id`, `stage_close_event_id`, `reassessment_state=post_close_reassessment_pending`, `most_recently_closed_stage`, `handoff_packet_id`, `revised_plan_version`, and `next_mandatory_dispatch=reassessment_research`
     - the termination classifier becomes transcript-visible only through its canonical immediate receipt; there is no hidden or retrospective classification step
     - when the next cycle opens in the same live invocation, the immediate next user-visible message must be a transcript-visible `Cycle Opened` commentary receipt
     - that receipt must include `receipt_id`, `prev_receipt_id`, `closeout_classification=continue_same_invocation`, `pause_reason=null`, `most_recently_closed_stage`, `next_current_stage`, `run_decision=continue`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`
     - after `Cycle Opened`, emit a transcript-visible `Dispatch Started` commentary receipt before any later yield or stop claim
     - that `Dispatch Started` receipt must include `receipt_id`, `prev_receipt_id`, `dispatch_started=next_mandatory_dispatch`, and `current_stage=next_current_stage`
     - if the close-out is a legal live pause, the immediate next and final user-visible message must be a transcript-visible `Pause Receipt`
     - that `Pause Receipt` must include `receipt_id`, `prev_receipt_id`, `closeout_classification=live_pause`, `run_decision=continue`, `pause_reason`, the latest authoritative current-stage status or `newborn_cycle_current_stage=null`, `most_recently_closed_stage` when applicable, `resume_entry_state`, `resume_dispatchability`, any `post_close_invalidation`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and `next_mandatory_dispatch`
     - if `pause_reason=unresolved escalate`, the `Pause Receipt` must also include the concrete `escalation_blocker`
     - if `pause_reason=user-requested pause`, the `Pause Receipt` must also include `user_pause_request_ref`
     - if `pause_reason=external approval or user decision required`, the `Pause Receipt` must also include `pending_decision_question` and `approval_or_option_set`
     - if `pause_reason=conflicting dirty changes`, the `Pause Receipt` must also include `conflicting_path_set`
     - if `pause_reason=recorded time or resource ceiling`, the `Pause Receipt` must also include `measured_cap`, `current_consumption`, and `limit_source`
     - if the close-out is a terminal run stop, the immediate next and final user-visible message must be a transcript-visible `Stop Receipt`
     - that `Stop Receipt` must include `receipt_id`, `prev_receipt_id`, `closeout_classification`, `termination_posture`, `run_decision=stop`, `goal_reassessment_completed=true`, `most_recently_closed_stage`, the latest authoritative current-stage status, `required_for_success_remaining_count`, `required_for_success_stage_ids_or_hash`, `handoff_packet_id`, `revised_plan_version`, `reassessment_receipt_ref`, and the concrete stop basis
     - in every `Stop Receipt`, `closeout_classification` must equal `termination_posture`, and both must be one of `stop_goal_saturated|stop_escalation_halt`
     - if `termination_posture=stop_goal_saturated`, `required_for_success_remaining_count` must equal `0`
     - if the close-out is terminal planning-deliverable closure, the immediate next and final user-visible message must be a transcript-visible `Planning Complete Receipt`
     - that `Planning Complete Receipt` must include `receipt_id`, `closeout_classification=stop_planning_deliverable`, `run_intent=planning_only`, `terminal_handoff_kind=planning`, `terminal_state=integrate_plan`, the latest authoritative stage status, `handoff_packet_id`, and `revised_plan_version`
     - a stage-close summary, handoff summary, or final close-out cannot substitute for any canonical receipt
     - if the pause reason is recorded time or resource ceiling, name the concrete measured ceiling, ensure that ceiling basis and current consumption are already recorded in the latest authoritative `decision_ledger` lineage, and ensure the latest sealed handoff already exposes the cold-start-legal resume path; if `run_decision=continue`, seal the newborn-cycle `research` handoff before yielding
     - if no legal stop posture and no legal pause reason can be named concretely, ending the turn is a loop failure
18. Read `references/process-architecture.md` for the end-to-end loop shape.
19. Read `references/contracts-and-rules.md` before changing role contracts, challenge rules, execution gating, verification rules, or evidence policy.
20. Read `references/kernel-spec-stage1-3-draft.md` before changing lifecycle control, authority boundaries, handoff rows, invalidation routing, claim recovery, or termination behavior.
21. Read `references/kernel-spec-stage5-oracle-draft.md` before changing dry-runs, conformance checks, mismatch routing expectations, or seal-point validation behavior.
22. Read `references/kernel-spec-stage6-packets-draft.md` before changing canonical role packet fields or role authority.
23. Read `references/kernel-spec-stage7-packet-templates-draft.md` before changing reusable packet skeletons, handoff row templates, or selector tables.
24. Read `references/project-adaptation.md` only when the revised plan needs to land inside a repository.
25. Read `references/profile-sync.md` only when you intentionally maintain a repo-local loop profile layer.

## Preserve These Invariants

- `$loop` and `$agent-loop` are the primary operator surfaces.
- This skill is Codex-side automation first, not a product command spec.
- Content matters more than original file format.
- Accept local documents and pasted notes as first-class inputs.
- Keep the main value in deep research, staged plan reconstruction, challenge-reviewed revision, and repeated improvement.
- Keep `run` larger than `cycle`, and keep each cycle bounded by one current stage.
- Run exactly three viewpoint-separated research agents for each research phase and require one merged research synthesis before planning or run-level stop/continue decisions.
- Keep challenge separate from execution.
- Keep verification separate from implementation self-reporting.
- Resolve the current strongest model once per live invocation and hard-pin that exact model plus max supported reasoning effort for every research, planning, execution, challenge, and verification agent. In many current Codex runtimes this may resolve to `gpt-5.4` with `xhigh`, but runtime discovery remains authoritative unless the user explicitly overrides it.
- Every delegated loop dispatch must carry explicit `model` and `reasoning_effort` fields equal to the resolved hard pin. Omitting either field and relying on inherited or default selection is a contract violation.
- Run exactly three challengers for plan review and exactly three challengers for verification review.
- Keep the main CLI thread focused on orchestration, evidence collection, integration, and plan updates.
- Keep worker context narrow and role-specific.
- Only the main run owner / orchestrator may classify live-invocation termination, emit `final`, or convert a closed stage into a legal pause or stop posture.
- Preserve original priorities and dependency edges unless challenge or research finds a concrete reason to reorder them.
- Freeze quality gates for the current stage before implementation and do not silently soften them mid-stage.
- Commit only after the current stage passes its verification bar.
- Run fresh reassessment research after every cycle closes through `commit|rescope|escalate`.
- Repeat the full loop until later `goal_reassessment -> run_decision` decides continue or stop for the original goal.
- Only discuss a product `/loop` surface if the user explicitly wants to embed this automation into an app or repo runtime.

## Kernel Discipline

- `run` owns the original goal and may span many bounded plan cycles.
- `cycle` owns one current stage plus its close / reassessment / run-decision path.
- `stage` is the smallest unit that may verify, challenge, and commit.
- `stage_closed` is cycle-local only; it never implies `run_stopped`.
- only the main run owner / orchestrator may convert cycle-local closure into a legal live-invocation yield, legal pause, or terminal stop.
- `worker_slice` is always snapshot-bound, claim-bound, and narrow.
- after any non-terminal stage close, the cycle must pass through `post_close_reassessment_pending` before any legal user-facing yield or next-cycle dispatch decision.
- `post_close_reassessment_pending` is never itself a legal yield, pause, or terminal posture.
- The only legal dispatch source is fresh bootstrap context or the latest sealed `handoff_packet` after fresh preflight.
- `revised_plan` is the only executable snapshot. It is the source of truth for work selection and claim publication.
- `decision_ledger` is audit-only. It records reasoning and accepted decisions but does not become executable authority.
- Research, challenge, worker, verification, and integration outputs are draft candidates until the integrator seals the next authoritative artifact.
- `dispatchable_slice_specs` are authoritative. `Parallel Worker Lanes` is a human-readable derived view only.
- Post-close invalidation is never bypassed. If a closed cycle later drifts or reopens a blocker, same-cycle `verify` must revalidate before any new cycle may proceed.
- Use the sealed handoff row templates and the successor selector from `references/kernel-spec-stage7-packet-templates-draft.md` rather than reconstructing resume legality from scratch.

## Default Revised Plan Shape

When reconstructing the authoritative `revised_plan` from rough, broad, or already-staged input, prefer this shape.

If the source already contains `Run Intent`, treat it as advisory source text only and re-derive the authoritative value from explicit request intent plus fresh research.

```md
## Working Goal
- What is the real objective this run is trying to satisfy?

## Run Intent
- `planning_only` or `implementation_oriented`
- `planning_only` is the revised-plan run intent corresponding to explicit `request_intent=planning_deliverable_only`

## Success Condition
- What outcome means the original goal is truly satisfied for now?

## Current Stage
1. The smallest active stage that should move now
2. Whether this stage is `required_for_success` or `optional_followup`
3. The required outputs for this stage
4. The gates that must pass before commit
5. The authoritative `dispatchable_slice_specs` for any worker slices

## Parallel Worker Lanes
- [ ] Human-readable view of the current stage's `dispatchable_slice_specs`

## Remaining Stage Queue
1. The next `required_for_success` or `optional_followup` stage after the current one closes
2. Later stages still blocked by dependencies or new research

## Quality Gates
- Required checks, tests, review bars, and acceptance criteria

## Research Hooks
- Questions to re-open after the stage completes

## Open Questions
- Explicit unknowns that could still change the path

## Progress Ledger
- Stage status
- Commit status
- Evidence summary
```

## Challenge Output Shape

Use the canonical Stage 6 / Stage 7 `challenge_result_candidate` and finding template rather than reauthoring a second local schema here.

Use these three viewpoints for research, plan challenge, and verify challenge:

- `architecture_dependency`
- `failure_verification`
- `goal_efficiency`

Challenge should not directly implement the fix. It should change the plan, the stage boundary, the gate set, or the verification bar.

## Execution Boundary

Planning-only completion point:

- after the first challenge-reviewed authoritative `revised_plan` is sealed through the terminal `planning` handoff at `integrate_plan`
- this is not a `goal_reassessment -> run_decision` stop path

Default execution path for implementation-oriented requests:

- execute one current stage at a time
- keep the main thread orchestration-focused
- use bounded workers for parallelizable slices
- verify the stage
- run three fresh verify challengers
- fix blockers
- re-verify
- close the stage through `commit|rescope|escalate`
- re-research and update the remaining plan
- move to the next stage
- treat `commit|rescope|escalate` as a transition into `post_close_reassessment_pending`, not as a user-visible end state by itself
- while `post_close_reassessment_pending` is active, only progress `commentary` is legal; a `final` close-out or terminal-looking wrap-up is a lifecycle violation
- if `run_decision=continue` and no explicit pause reason exists, open the next cycle in the same live invocation rather than returning control after a preparatory stage
- if `run_decision=continue` and no explicit pause reason exists, `final` is illegal and only `commentary` updates may be used until the next cycle has been opened
- immediately after any non-terminal stage close, emit a transcript-visible `Reassessment Pending` commentary receipt containing:
  - `receipt_id`
  - `stage_close_event_id`
  - `reassessment_state=post_close_reassessment_pending`
  - `most_recently_closed_stage`
  - `handoff_packet_id`
  - `revised_plan_version`
  - `next_mandatory_dispatch=reassessment_research`
- the termination classifier has no hidden transcript-external form; its chosen `closeout_classification` becomes valid only when the canonical immediate receipt for that classification is emitted
- once the next cycle is opened, emit a transcript-visible `Cycle Opened` commentary receipt containing:
  - `receipt_id`
  - `prev_receipt_id`
  - `most_recently_closed_stage`
  - `closeout_classification=continue_same_invocation`
  - `pause_reason=null`
  - `next_current_stage`
  - `run_decision=continue`
  - `handoff_packet_id`
  - `revised_plan_version`
  - `reassessment_receipt_ref`
  - `next_mandatory_dispatch`
- the `Cycle Opened` receipt must be the immediate next user-visible message after `continue_same_invocation` is established; any intervening `final`, stage-close wrap-up, or pseudo-stop summary is a `phase-close-as-run-stop` violation
- after `Cycle Opened`, emit a transcript-visible `Dispatch Started` commentary receipt containing:
  - `receipt_id`
  - `prev_receipt_id`
  - `dispatch_started=next_mandatory_dispatch`
  - `current_stage=next_current_stage`
- for any legal `live_pause`, the immediate next and final user-visible message must be a transcript-visible `Pause Receipt` containing:
  - `receipt_id`
  - `prev_receipt_id`
  - `closeout_classification=live_pause`
  - `run_decision=continue`
  - `pause_reason`
  - the latest authoritative current-stage status, or `newborn_cycle_current_stage=null` plus `most_recently_closed_stage`
  - `resume_entry_state`
  - `resume_dispatchability`
  - any `post_close_invalidation`
  - `handoff_packet_id`
  - `revised_plan_version`
  - `reassessment_receipt_ref`
  - `next_mandatory_dispatch`
- the `Pause Receipt` must also include reason-specific proof:
  - unresolved `escalate` -> `escalation_blocker`
  - user-requested pause -> `user_pause_request_ref`
  - external approval or user decision required -> `pending_decision_question` and `approval_or_option_set`
  - conflicting dirty changes -> `conflicting_path_set`
  - recorded time or resource ceiling -> `measured_cap`, `current_consumption`, and `limit_source`
- for any terminal run stop, the immediate next and final user-visible message must be a transcript-visible `Stop Receipt` containing:
  - `receipt_id`
  - `prev_receipt_id`
  - `closeout_classification`
  - `termination_posture`
  - `run_decision=stop`
  - `goal_reassessment_completed=true`
  - `most_recently_closed_stage`
  - the latest authoritative current-stage status
  - `required_for_success_remaining_count`
  - `required_for_success_stage_ids_or_hash`
  - `handoff_packet_id`
  - `revised_plan_version`
  - `reassessment_receipt_ref`
  - the concrete stop basis
- in every `Stop Receipt`, `closeout_classification` must equal `termination_posture`, and both must be one of `stop_goal_saturated|stop_escalation_halt`
- if `termination_posture=stop_goal_saturated`, `required_for_success_remaining_count` must be `0`
- for terminal planning-deliverable closure, the immediate next and final user-visible message must be a transcript-visible `Planning Complete Receipt` containing:
  - `receipt_id`
  - `closeout_classification=stop_planning_deliverable`
  - `run_intent=planning_only`
  - `terminal_handoff_kind=planning`
  - `terminal_state=integrate_plan`
  - the latest authoritative stage status
  - `handoff_packet_id`
  - `revised_plan_version`
- any intervening wrap-up, pseudo-stop summary, or delayed receipt for `live_pause`, terminal stop, or planning completion is an illegal exit
- if the live invocation resolved a concrete strongest model pin, any delegated output produced without that exact model/effort pair is inadmissible and must be rerun before the loop may continue
- before any final user-facing close-out, state whether the loop is ending through terminal planning-deliverable closure, a terminal run stop posture, or only yielding through a live-invocation pause:
  - `final` is legal only for:
    - `stop_planning_deliverable`
    - `stop_goal_saturated`
    - `stop_escalation_halt`
    - a legal `live_pause`
  - terminal planning-deliverable closure:
    - `stop_planning_deliverable`
  - terminal run stop postures:
    - `stop_goal_saturated`
    - `stop_escalation_halt`
  - live-invocation pause reasons:
    - unresolved `escalate`
    - user-requested pause
    - external approval or user decision required
    - conflicting dirty changes
    - recorded time or resource ceiling
  - for any live-invocation pause, also state the latest authoritative current-stage status; if the latest handoff is a newborn cycle with no current stage yet, say that explicitly and name the most recently closed stage
  - for any live-invocation pause, also state the latest sealed resume entry state, whether it is directly dispatchable or lineage-only, any `post_close_invalidation`, and the next mandatory dispatch after fresh preflight
  - for recorded time or resource ceiling, cite the concrete measured cap, current consumption, and the already-in-force user or system limit that created the cap; a vague ceiling claim is illegal
- if none of the above reasons applies, continue the loop

During goal-level reassessment, especially when the current plan appears exhausted:

- run the same exact-three-viewpoint goal-level research sweep
- if meaningful improvement remains, start the next plan cycle
- if no meaningful improvement remains, stop later through `goal_reassessment -> run_decision`
- if an escalated lineage cannot be resolved, stop later through `goal_reassessment -> run_decision`

## Working Style

- Prefer evidence from files, diffs, tests, and logs over agent self-reporting.
- Keep transformation noise low when converting notes into staged plans.
- If the source is already a good staged plan, preserve useful structure but still re-expand it against the normalized working goal, current codebase state, and any missing `required_for_success` stages.
- If the source is broad, separate the current stage from parallel worker lanes and later-stage queue.
- Treat research as a first-class exact-three-viewpoint stage before planning and after any cycle closes through `commit|rescope|escalate`.
- Keep verify challengers fresh rather than reusing planning challengers.
- Use compact handoff artifacts instead of dragging the whole transcript into every worker.
- When execution touches a repository, respect the repo contract, preserve unrelated dirty changes, and commit only verified stages.
- If the user only wants `$loop` fixed or refined, end after reconstructing and challenge-reviewing the plan through the same planning-deliverable closure rules.

## References

- `references/process-architecture.md`
- `references/contracts-and-rules.md`
- `references/kernel-spec-stage1-3-draft.md`
- `references/kernel-spec-stage5-oracle-draft.md`
- `references/kernel-spec-stage6-packets-draft.md`
- `references/kernel-spec-stage7-packet-templates-draft.md`
- `references/project-adaptation.md`
- `references/profile-sync.md`
