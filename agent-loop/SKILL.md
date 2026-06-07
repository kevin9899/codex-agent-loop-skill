---
name: agent-loop
description: "Use via `$loop` or `$agent-loop` inside Codex to turn a local document, backlog, or execution note into a resumable software-improvement loop that keeps working until the real final goal is complete. `$loop` authorizes useful delegated agents without a second permission prompt. Default profile is pragmatic file-backed automation with persisted handoff state, mandatory initial 5-lane Codex research for material non-fast-path/non-self-check work before the first plan lock, nonstop continuation for implementation work, immediate resume after forced host-boundary pauses, live-state status briefings instead of completion prose, no free-form final recaps while `run_decision=continue` or `completionStopAllowed=false`, and mandatory fresh 5-lane completion proof before any terminal goal-satisfied stop claim."
---

# Agent Loop

Use `agent-loop` to turn a local source into a resumable execution loop with
explicit plan state, explicit evidence, and explicit stop gates.

Default to the pragmatic file-backed profile. Use the higher-rigor packet and
runtime references only when the environment actually needs them.

Plain-language operator meaning: `$loop` already carries both "keep working
until the real goal is done" and "use delegated Codex agents when useful and
available." Do not wait for a second user sentence to unlock delegation.

## Non-Negotiable Invariants

- Treat the `$loop` / `$agent-loop` operator token itself as an affirmative
  grant to use delegated `spawn_agent` lanes when the tool exists and
  delegation materially helps. Do not wait for a second user message that
  separately says "use agents"; the loop invocation already carries that
  authority.
- Read the operator literally: `$loop` semantically means "continue toward the
  goal and use agents when they help." If that implication is not visible in
  the current plan, receipts, or docs, repair those artifacts instead of
  treating delegation as unapproved.
- Interpret user follow-ups such as `계속`, `계속 진행해`, or `마무리해` inside an
  active `$loop` run as continuation under that same delegation grant, not as a
  fresh permission checkpoint for agent use.
- Treat bare implementation-oriented `$loop` as `continuation_mode=nonstop`.
- Treat `$loop` / `$agent-loop` as standing authorization to use delegated
  `spawn_agent` lanes when delegation materially helps and the host exposes the
  tool. Do not ask a separate "open agents?" / "use agents?" permission
  question inside a `$loop` run; dispatch them with the resolved model pin, or
  record the concrete runtime blocker.
- Treat commit execution as withheld by default. A normal `$loop`, `$agent-loop`,
  `계속`, `계속 진행해`, "resume", or "finish the remaining work" instruction
  authorizes implementation and verification, but does not authorize any actual
  commit operation. Do not run `git add`, `git commit`, `git commit -a`,
  `npm run loop:commit:auto`, or any other commit broker/commit command unless
  the user gives a fresh explicit commit instruction containing `$loop 커밋`.
  Until then, keep verified changes in the working tree and report them as
  pending commit-broker work instead of starting the broker.
- Cap delegated Codex challenge/proof panels at the phase-required lane count:
  five lanes for material initial research and final halt/completion proof;
  five lanes for planning, pre/post implementation challenge, and verification
  challenge panels; two lanes for mandatory mini plan validation. Do not expand beyond
  the phase contract for difficulty, convenience, or retry pressure.
- Treat the first accepted working goal as standing authority to continue; do
  not ask whether to keep going, whether to resume after a progress report, or
  whether to open the next cycle unless a real external approval gate blocks
  execution.
- Keep working until a real blocker, explicit external authority, or forced host
  turn boundary exists.
- Define "real blocker" narrowly. Missing stop/completion proof, incomplete or
  timed-out challenge lanes, manual commit/index ownership, approval-needed-only
  states, and self-assessed no-bounded-action claims are continuation states
  until a fresh stop-authorization challenge attempt, concrete tool/runtime
  blocker, or direct explicit user stop proves otherwise.
- In `same_turn_only` hosts, a visible final reply with `run_decision=continue`
  is bookkeeping for a forced boundary, not semantic stop. `$loop` only stops
  semantically after the required fresh 5-lane final proof or a direct explicit
  user stop.
- Treat `auto_resume_any_followup` as a forced-boundary recovery fallback, not
  as an acceptable nonstop user experience. If the user says that waiting for a
  follow-up message itself is the defect, classify the event as
  `host_boundary_wait_defect`, repair the loop-control contract or run
  artifacts, and immediately run the next tool-backed action. Do not answer
  with another receipt-only message while tools remain available.
- A controller must not voluntarily end a turn because a future follow-up could
  resume the run. While tool calls are still available, continue the current
  bounded implementation, verification, inspection, or artifact-repair action.
  Reserve a visible `run_decision=continue` receipt for a concrete host/API
  boundary after recording the boundary evidence.
- Repeat `ideation -> research -> plan -> execute -> verify -> reassess` until
  fresh unanimous 5-lane completion proof exists or a direct explicit user
  stop overrides.
- Treat initial Research and Plan lock as mandatory gates for material or
  uncertain work. A tier0/tier1 deterministic fast path may skip delegated
  initial research only when the source request is exact, the change is local
  and reversible, no external/API/DB/security behavior is touched, and the run
  records `fast_path_reason`, a minimal `revised-plan.md`, requirement trace,
  and local verification. An ordinary `tier1_local` self-check may also skip
  delegated initial research only when it records `tier1_self_check=pass`,
  `risk_expanded=false`, implementation summary, verification plan, requirement
  trace, local verification result/ref, scoped files, and explicit no
  external/API/DB/security/shared-boundary scope. These paths accept the local
  implementation batch; they do not by themselves authorize a semantic `$loop`
  terminal stop. When an exact tier0/tier1 goal has no remaining stages after
  local verification, dispatch the final source-first completion proof
  immediately against the compact source/plan/evidence packet instead of
  inventing extra research or implementation work.
- Treat `handoff.md` as continuation state, not as stop permission.
- Treat `npm run loop:handoff`, a refreshed handoff, or a verified local batch
  as a reassessment checkpoint only. If the live state reports
  `run_decision=continue` or `completionStopAllowed=false`, the next controller
  transition must be one of: start a concrete bounded action, dispatch the
  required stop/completion challenge, record a canonical no-bounded-action
  blocker, or emit validated forced-boundary gate output. A normal final recap
  is not one of the allowed transitions.
- If the controller feels ready to send `final` because "the current batch is
  verified", first classify that impulse as `pre_final_reassessment_required`.
  Re-open `handoff.md`; when any remaining required stage exists, immediately
  start the next stage or record why it cannot be started with concrete tool
  evidence.
- If `completionStopAllowed=false`, any free-form `final` response is a
  `voluntary_turn_close` unless it is exactly the canonical forced-boundary
  gate output. A summary that lists remaining work is still an illegal semantic
  stop because it makes the next action future-tense instead of in-flight.
- Treat any failed `loop-final-guard`, `closeout_gate.py`,
  `validate_continue_reply.py`, handoff validation, or explicit
  `completionStopAllowed=false` check as a continuation/repair trigger, not as
  user-visible status material. Do not emit a normal `final` answer that says a
  guard blocked completion "as expected" or lists remaining stages as a recap.
  The next transition must start a bounded tool-backed action, repair the loop
  controller/artifacts, dispatch a required challenge, or record a canonical
  no-bounded-action blocker with evidence.
- Keep one authoritative `revised-plan.md` and one authoritative `handoff.md`.
- Keep exactly one working goal per run. If a later user turn opens a
  materially different `$loop` / `$agent-loop` goal, create or resume a new
  authoritative sibling run immediately instead of silently keeping the older
  run as the live authority.
- Resolve every run's `work_type` separately from `run_intent`. Valid work
  types are `implementation`, `research`, `docs`, `planning`, `review`, and
  `mixed`; non-code work must use a typed completion subject instead of being
  forced through `repo_diff` semantics.
- Bind terminal completion to a current `completion_subject` and selected
  `run_authority_record`. For mixed work, require a `composite_subject` that
  covers every required stage subject and digest.
- Select the live run through the authority record, not through stale
  conversation memory or a convenient `handoff.md`. Ambiguous, duplicate,
  moved, mismatched, or incompatible runs are quarantine candidates and cannot
  authorize terminal stop.
- Treat authority revision/epoch and digest freshness as stop gates. Terminal
  completion must reread the authority record, recompute current source,
  subject, composite, and stage-graph digests, pass conformance/version checks,
  and complete with a CAS-style state transition backed by a separate
  `authority_transition_receipt_version=v1` pre/post digest receipt.
- Aggregate challenge results only from one current cycle where every required
  lane reviewed the exact same digest set under the same schema, policy,
  prompt, validator, authority revision, and authority epoch. Do not combine
  old ALLOWs, partial reruns, mixed-version lane results, or dispatch receipts
  that do not bind the same phase, challenge mode, source digest,
  authority revision/epoch, and cycle id.
- Project manifests and `agent_loop_override` entries are adapters, not global
  semantics. Overrides are allowlist-only and may not alter work-type
  resolution, lane roles, verdict meanings, final proof semantics, model
  policy, stop gates, challenge aggregation, artifact digest rules, authority
  fencing, or visible-output contracts.
- A project-discovered `$loop` improvement must pass portability
  classification before promotion: `global_invariant`,
  `project_adapter_rule`, `project_local_hint`, or `rejected_local_hack`.
  Only `global_invariant` may change global loop semantics.
- Expand explicit sequential user objectives into required stages and do not stop
  after only the first one.
- Treat status requests as live-state reporting, not as pause or stop
  authorization.
- Treat interruption-style requests such as "잠깐만 지금 하는 것만 하고 먼저
  브리핑해줘", "what remains?", "status first", or "brief me on X" as
  checkpoint interrupts, not loop termination. Finish any already-started safe
  command or patch batch, provide the requested live briefing in commentary, then
  either continue the next bounded local action in the same turn or, if the user
  immediately redirects, follow the newest instruction without requiring fresh
  `$loop` permission.
- Treat "what remains?", "why did you stop?", "you should not have stopped",
  and similar correction/status turns inside an active `$loop` as immediate
  continuation triggers. Give at most one short live-state sentence in
  commentary, then run the next concrete tool-backed action in the same turn.
  Do not answer these turns in `final` unless a canonical forced-boundary
  closeout receipt has already proved no bounded local action remains.
- Use canonical scripts for any turn-ending closeout; do not hand-write closeout
  prose.
- Do not hand-write a `run_decision=continue` receipt. If a visible turn end is
  truly unavoidable, record the boundary receipt first, then emit only the
  validated `closeout_gate.py` output.
- Do not summarize, trim, translate, reorder, or selectively copy
  `closeout_gate.py` stdout. A visible continue receipt is a low-freedom
  protocol message; the final-channel answer must reproduce the gate output
  verbatim. If you abridge it, record that as
  `abridged_closeout_gate_output_perceived_stop`, repair the loop contract, and
  continue tool-backed work before any further visible receipt.
- In `same_turn_only` hosts, a turn-ending `continue` receipt must surface
  `stop_status=not_stopped`,
  `user_visible_note=사용자 표시용: 멈춘 게 아니라 호스트가 보이는 답변만 한 번 끊은 상태입니다. 다음 메시지는 같은 run 자동 재개 신호입니다.`,
  `final_copy_policy=copy_closeout_gate_stdout_verbatim_no_summary_no_omission`,
  `forced_boundary_note=호스트가 백그라운드 실행을 이어주지 않아 final 채널로 경계 영수증을 남긴 것입니다. 루프는 목표 완료/정지로 처리되지 않았고, 아무 후속 메시지나 보내면 같은 run을 즉시 이어갑니다.`,
  `host_boundary_effect=visible_turn_only_not_goal_stop`,
  `auto_resume_trigger=any_followup_message`,
  `followup_resume_policy=auto_resume_any_followup`, and an exact
  `resume_command=$loop <run-dir>` so any ordinary follow-up can be treated as
  an immediate continuation rather than a fresh permission checkpoint.
- A `blocked_during_attempt` continue receipt must also surface Korean
  user-facing blocker fields before `stop_status`:
  `user_visible_status_ko=...`, `blocked_action_ko=...`,
  `needed_condition_ko=...`, and `human_readable_reason=...`. These fields must
  name the concrete blocked action and the concrete external/user condition.
  English-only or vague blocker prose is inadmissible.
- If the blocker is not a retryable tool/runtime/quota blocker but an
  external-gate-only state where no bounded local action remains, do not emit an
  auto-resume `continue` receipt. Run the required completion/stop proof when
  the source allows external/user-only leftovers as completion; otherwise encode
  a truthful external-gate pause.
- In `same_turn_only` hosts, a turn-ending `continue` receipt is illegal unless
  `turn_exit_evidence` also carries
  `host_boundary_ref=<authority-receipt-path>` bound to the same
  `closeout_round_id` and latest `attempt_ref`; do not claim a forced visible
  host boundary without a fresh authority receipt.
- If any ordinary follow-up arrives after such a `continue` receipt, treat it
  as that auto-resume trigger, run
  `scripts/record_resume_event.py <run-dir> --trigger any_followup_message`,
  and immediately continue `next_mandatory_action`; do not debate whether the
  previous turn "really" stopped and do not ask for permission to resume.
- If the follow-up says the loop stopped after a syntactically valid
  same-turn-only `continue` receipt, classify it as
  `receipt_only_final_boundary_perceived_stop`, not as a permission question.
  Preserve the latest receipt/handoff evidence, record the resume event, patch
  or validate the loop-control contract that allowed the perception gap, then
  run at least one tool-backed repair, verification, or next mandatory action
  before any further turn-ending receipt. If another receipt is later
  unavoidable, its user-visible note must explicitly name the final-channel
  host boundary and the automatic same-run resume trigger instead of relying on
  machine-readable `run_decision=continue` alone. A second receipt-only answer
  in that resumed turn is forbidden while tools are available.
- A `receipt_only_final_boundary_perceived_stop` is especially inadmissible when
  delegated agents are quota-blocked or source-wide gates are resource-busy but
  any smaller local action remains possible. Quota blockers defer that specific
  delegated action only; resource preflight blockers defer high-memory commands
  only. They do not justify a visible `final` closeout while the controller can
  still do read-only inspection, loop-control repair, targeted tests, scoped
  lint/type checks, small UI/UX hardening, artifact updates, or plan/evidence
  cleanup. After such a user correction, first record the resume event, then
  patch the loop-control rule or artifact that permitted the premature receipt,
  and immediately run a bounded local action. Do not emit another
  `closeout_gate.py` receipt in that resumed turn merely because the same
  delegated quota or high-memory blocker still exists.
- Record bottleneck/resource telemetry only when the observation changes
  controller behavior: a high-memory or source-wide command is deferred, shrunk,
  skipped, retried later, or replaced with a smaller local action; a delegated,
  quota, or tool blocker delays a specific lane; or a closeout/resume defect
  investigation depends on that blocker. If the run can proceed normally, do
  not add telemetry merely for completeness.
- Bottleneck/resource telemetry is scheduling evidence, not stop authority. Its
  presence, absence, or staleness must not create a new completion gate,
  required stage, closeout prerequisite, pause basis, or terminal-stop
  condition. Do not set `next_mandatory_action` to telemetry collection alone
  unless the same record is needed to preserve a concrete blocker for an action
  already attempted in this turn.
- Keep telemetry lightweight and local to the existing run artifacts. The
  canonical path is `run://telemetry/resource-events.jsonl`, surfaced in
  `resource_telemetry_ref`. Each JSONL event uses
  `telemetry_schema_version=resource-telemetry-v1` and records `event_id`,
  `observed_at`, `event_type`, `affected_action`, `decision_impact`, and
  `next_action`. When resource/quota/tool-limit evidence changes controller
  behavior, the handoff must cite this telemetry ref.
- If delegated challenge/proof quota is blocked but local work remains,
  `next_mandatory_action` must name the immediate local action first and the
  delegated retry only as a deferred action. A `next_mandatory_action` that
  contains only "retry challenge when quota is available" is invalid in nonstop
  mode unless a fresh artifact proves no read-only scan, small hardening,
  focused verification, artifact repair, or runbook repair can be started.
  Repair the handoff before any visible closeout attempt.
- A resumed `$loop` turn after a `continue` receipt must not emit another
  receipt-only or explanation-only visible answer while tools are available.
  The first substantive move must be a tool-backed resume action or the next
  concrete bounded implementation/verification step. If `record_resume_event.py`
  cannot be run, record that concrete runtime blocker in the run artifacts and
  continue with the next bounded local action rather than stopping on prose.
- Treat "host clipped the visible answer and only a continue receipt remained"
  as a loop-control defect to burn down, not as an acceptable pause state. The
  controller must either execute more work in the resumed turn or persist a
  fresh blocker proving that no tool-backed continuation is possible.
- When the user asks for an N-agent stop-cause analysis, dispatch those
  analysis lanes as requested when `spawn_agent` is available, but keep the
  controller on the repair critical path. If the host rejects
  `fork_context=true` with explicit model overrides, retry with a narrow
  source packet and explicit `model=gpt-5.5` plus high-or-stronger reasoning;
  do not omit the model pin or downgrade the lane.
- Delegated-agent use is not a separate external approval gate in a `$loop`
  invocation. Ask only for authority that is genuinely outside the current
  runtime contract, such as new paid third-party credentials, irreversible
  production-side effects, or access to a system the user has not already made
  available.
- In every authoritative `$loop` run artifact, `capability_mode` must record
  that grant explicitly with `delegated_agents_authorized_by_loop`. Tool
  availability belongs in the suffix, for example
  `delegated_agents_authorized_by_loop_tool_available`,
  `delegated_agents_authorized_by_loop_tool_unavailable`, or
  `delegated_agents_authorized_by_loop_tool_state_unknown`. Missing tool
  support is a runtime constraint, not a missing permission grant.
- Require a fresh unanimous five-lane completion challenge before any
  goal-satisfied autonomous `stop`.
- Final halt/completion challenge lanes must be viewpoint-separated: dispatch
  exactly one fresh Codex agent for each required lane
  (`architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, `implementation_quality`).
  Each agent must judge from its assigned perspective, not from a
  generic all-purpose review prompt; duplicate, missing, or uncovered scope
  makes the five-lane proof inadmissible even when all returned votes are
  `allow`.
- Treat `source.md` as the sole authority for the original user request during
  final halt/completion proof. Final stop lanes must run from a clean,
  source-first packet: no full-history fork, no prior loop transcript as scope,
  and no trust in `ideas.md`, `research.md`, `revised-plan.md`, `evidence.md`,
  or `handoff.md` except as implementation claims to inspect against
  requirements reconstructed from `source.md`.
- Final halt/completion lanes are challenge agents, not workers, explorers, or
  completion summarizers. Each final lane prompt must assign
  `agent_role=challenge_agent`, must attack the stop/completion claim from its
  single viewpoint, and must forbid implementation, cleanup, scope expansion,
  and controller-state edits. Record `agent_role=challenge_agent` plus the
  phase-specific `challenge_review_mode` in the aggregate proof evidence, each
  lane artifact, and each dispatch receipt:
  `autonomous_stop_challenge` for `phase=stop_authorization`, and
  `goal_completion_challenge` for `phase=goal_completion`.
- Final halt/completion proof must record `source_ref=source.md`,
  `source_digest=<sha256(raw source.md bytes)>`, `context_mode=clean_source_first`,
  `authority_basis=source_md_original_user_prompt`,
  `source_requirements_reconstructed=yes`,
  `claim_files_trust=untrusted_ideas_research_revised_plan_evidence_handoff`,
  `repo_inspection=fresh`, `audit_gap_count=0`, and
  `scope_verdict=original_request_satisfied` in both aggregate proof evidence
  and each lane artifact. Goal-completion lanes must additionally record
  `source_alignment_verdict=all_source_requirements_satisfied`.
- During that fresh halt/completion challenge, do not deny solely because the
  current round's canonical proof artifacts have not been written yet. The
  controller may synthesize those artifacts from the lane outputs after all
  required lanes return. Same-round artifact absence before synthesis is not,
  by itself, a blocker.
- For the same reason, do not deny solely because the current round's lane
  verdict set is not already present in the run directory. That verdict set is
  being generated by the live challenge itself.
- Use the versioned capability class `frontier_loop_authority_v1` with explicit
  `high` or `xhigh` reasoning for every delegated `$loop` research, worker,
  verifier, halt, and completion lane. In the current local catalog that class
  resolves to `gpt-5.5`; `gpt-5.4`, `gpt-5.3`, `gpt-5.3-codex`,
  `gpt-5.3-codex-spark`, Spark variants, and mini variants are inadmissible
  because they do not satisfy the class. Cost, speed, convenience, retry
  pressure, separate usage buckets, or thread-limit recovery are not valid
  reasons to downshift the class.
- Reasoning effort must be `high` or `xhigh` for every delegated `$loop` lane.
  `low` and `medium` are inadmissible even when paired with an allowed model.
- Use role-specific model authority:
  - Plan and final acceptance ratification must include the strongest available
    Codex model; in the current local catalog this means `model=gpt-5.5` with
    `reasoning_effort=xhigh`.
  - Material initial research and final halt/completion panels use three
    `gpt-5.5/xhigh` lanes and two `gpt-5.5/high` lanes.
  - Multi-agent planning, implementation-strategy, pre-implementation
    challenge and post-implementation verification challenge panels use three
    `gpt-5.5/xhigh` lanes and two `gpt-5.5/high` lanes.
  - Mandatory mini pre/post implementation plan validation uses one
    `gpt-5.5/xhigh` lane and one `gpt-5.5/high` lane.
  - Bounded implementation workers also use at least `model=gpt-5.5` with
    `reasoning_effort=high`; weaker draft-worker lanes are inadmissible.
  Do not produce an authoritative `revised-plan.md`, implementation strategy,
  post-implementation acceptance, or completion proof from weaker evidence.
- For the mandatory five-lane halt/completion proof, all five lanes must use
  `gpt-5.5` with `high` or `xhigh` effort, and exactly three of the five lanes
  must use `gpt-5.5/xhigh`. The required mix is three `gpt-5.5/xhigh` lanes and two
  `gpt-5.5/high` lanes. If this mix is unavailable, the run cannot claim
  terminal stop/completion proof.
- Every delegated `spawn_agent` call in a `$loop` lane must pass the lane model
  explicitly as tool arguments: `model=<resolved_model_slug>` and
  `reasoning_effort=<resolved_reasoning_effort>`. Inherited, omitted, default,
  or "probably strong enough" model selection is inadmissible for `$loop`, even
  when the parent invocation appears to be running on the same model.
- For halt/completion challenge proof, every lane artifact must record
  `agent_role=challenge_agent`,
  `challenge_review_mode=<autonomous_stop_challenge|goal_completion_challenge>`,
  `model_policy=gpt_5_5_high_minimum_explicit`, `resolved_model_slug=<pin>`,
  `resolved_reasoning_effort=<pin>`, `model_resolution_basis_ref=<source>`,
  `spawn_model_binding=explicit_tool_args`,
  `spawn_tool_args_model=<pin>`,
  `spawn_tool_args_reasoning_effort=<pin>`, and
  `spawn_tool_call_ref=<dispatch receipt>`. The dispatch receipt must resolve
  inside the run directory and prove clean source-first context with
  `full_history_fork=false`, `agent_role=challenge_agent`, the same
  phase-specific `challenge_review_mode`, the same `source_digest`, explicit
  model args, the same `challenge_round_id` / `closeout_round_id`, and for
  cycle-bound terminal proof the same `challenge_cycle_id`,
  `authority_record_ref`, `authority_revision_at_dispatch`, and
  `authority_epoch_at_dispatch`.
  Aggregate proof, each lane artifact, and each dispatch receipt must also
  record `route_context=final_halt_completion`, `loaded_policy_refs` including
  the global refs `SKILL.md#NonNegotiableInvariants` and
  `handoff-template.md#FinalProof`, plus `AGENTS.md#LoopCompletionGate`
  whenever a bound repo root contains `AGENTS.md`, plus any project policy refs
  declared by the adapter, `policy_ref_digests` with SHA-256 digests for
  exactly those refs, and
  `policy_coverage_verdict=route_required_refs_loaded`. The handoff validator
  rejects unanimous proof that omits these fields, uses a non-challenge role,
  uses a weaker-than-5.5/high lane, omits required coverage metadata, or fails
  the required five-lane model mix.
- If `spawn_agent` rejects combining full-history fork with explicit model
  overrides, do not drop the lane model and do not fall back to inherited
  selection. Spawn with a narrow explicit packet and pass
  `model=<resolved_model_slug>` plus
  `reasoning_effort=<resolved_reasoning_effort>` on the tool call.
- If every required delegated lane is blocked by usage limits, quotas, credits,
  or rate limits after explicit `frontier_loop_authority_v1/high` or stronger dispatch, treat that as
  `continue_exit_status=blocked_during_attempt`, not as pause or stop
  authority. Do not downshift below that capability class, do not substitute
  5.4/Spark/5.3/mini models, do not reduce the required five lanes, and do not count
  errored/skipped lanes as consensus proof. Persist the dispatch blocker
  artifact and make the next mandatory action retrying explicit
  `frontier_loop_authority_v1/high` or stronger challenge lanes with the
  required five-lane model mix after the quota clears.
- Use mixed-model five-lane panels for halt/completion challenge proof when
  delegated agents are available; do not silently downgrade to fewer lanes or
  models below the required capability class for convenience.
- Bind autonomous stop proof to the current authority snapshot rather than a
  reusable old challenge round.
- Do not emit a terminal `stop` for an older run as the visible answer to a
  newer `$loop` goal. Older-run proof may be preserved as context evidence, but
  it cannot satisfy or terminate the newer goal.
- When a user turns a finished research/roadmap artifact into an
  implementation request, for example "proceed with this plan", immediately
  create or update a live implementation-scope authority artifact that expands
  every required plan item into trackable stages. The prior roadmap-generation
  completion proof is historical evidence only; it cannot authorize stopping an
  implementation loop unless the new implementation authority says all required
  stages are complete, explicitly out of scope, or externally blocked with no
  bounded local action remaining.
- A batch-level success, commit-ledger intent, focused test pass, or roadmap
  status update is not goal completion for an implementation-oriented `$loop`.
  After each batch, compare the live source/plan authority against completed
  stages and either start the next bounded action or record a canonical
  no-bounded-action blocker. A normal visible recap that lists remaining work is
  prima facie evidence of premature controller stop.
- A claim that only approval-required work, manual commit/index ownership,
  production/external receipts, or other no-bounded-local-action blockers remain
  is not stop or pause authority by itself. Before yielding a visible
  blocked/continue/pause/stop state on that basis, dispatch a fresh five-lane
  `stop_authorization` challenge against the current authority snapshot using
  the required `$loop` model mix. Record the aggregate and lane artifacts even
  when the verdict is `deny` or `ambiguous`; if the challenge lanes themselves
  are quota/tool blocked, record that dispatch blocker and make retrying the
  five-lane challenge the next mandatory action.
- Bind `subject_digest` to the live authority state, not the proof text itself.
  The validator redacts self-referential proof evidence fields from `handoff.md`
  before hashing so challenge proof can reference the digest without creating an
  impossible fixed point.
- Bind every turn-ending closeout to a concrete `closeout_round_id`; do not let
  old proof or old attempt evidence authorize a later visible closeout.
- For turn-ending `continue` states and `host_turn_boundary` pauses, keep the
  latest `attempt_ref` fresh relative to `handoff.md`; stale attempt receipts
  are evidence of `voluntary_turn_close`.
- For `host_turn_boundary` pauses, require `host_boundary_ref` to resolve to a
  receipt bound to the same `closeout_round_id` and `attempt_ref`; do not reuse
  a generic boundary note across closeouts.
- If another bounded local action is available now, do that action now instead
  of narrating progress.
- When a deploy, release, legal, credential, quota, or external receipt gate
  fails closed, record the exact blocker and immediately scan for the next
  non-destructive local improvement, validation, documentation hardening, or
  blocker-receipt action. Do not stop merely because one promotion gate needs
  real production authority or third-party evidence.
- In `durable_runtime`, a turn-ending `run_decision=continue` receipt is illegal
  while any bounded local action remains. A commit broker blocker, missing
  final proof, or manual index-owner gate is not by itself a visible turn
  boundary when the loop can still execute another scoped code/research/test
  action. Only use `closeout_gate.py` for durable-runtime continue after
  recording `AGENT_LOOP_NO_BOUNDED_LOCAL_ACTIONS_REMAIN=1` and concrete
  `AGENT_LOOP_NO_BOUNDED_LOCAL_ACTIONS_EVIDENCE` echoed in `turn_exit_evidence`.
- Before any `final`-channel answer in an active `$loop` run, reopen the live
  `handoff.md`. If it says `run_decision=continue`, `goal_completion_status` is
  anything other than `verified_complete_5lane`, or
  `remaining_required_stages` is non-empty, a normal final summary is illegal.
  The next visible action must be a commentary update followed by a concrete
  tool-backed implementation, verification, or blocker-recording step. Only a
  host-forced boundary may reach `final`, and that path must go through the
  canonical closeout gate with a valid host-boundary receipt.
- Treat a final-channel completion recap after a verified batch as a
  controller defect when the handoff still says `continue`. The correct repair
  is not to explain the recap; it is to record the defect, harden the loop
  instructions, and immediately execute the next bounded stage.
- Treat a final-channel "remaining work" recap in a `$loop` run the same way
  when any bounded implementation, investigation, verification, or
  blocker-recording action remains. The recap may be useful content, but it is
  not a legal stop state. Convert it into the next action by updating the live
  plan/handoff and starting the highest-leverage remaining slice immediately.
- Do not invoke `closeout_gate.py` merely because a verified batch finished.
  In nonstop mode, a verified batch is a reassessment point, not a turn-ending
  checkpoint. Immediately start the next highest-leverage bounded action unless
  the host actually forces a visible turn end.
- Do not invoke `closeout_gate.py` while the live `next_mandatory_action` is
  still only triage, sweep, scan, route classification, or candidate
  selection. Those are not legal `next_action_started` turn-end states; keep
  working until a concrete bounded patch, validation batch, or blocker is
  actually in flight.
- Do not invoke `closeout_gate.py` after a local code edit batch unless the
  smallest relevant validation already traveled with that batch. An
  `apply_patch`-only state without matching test/lint/type/build evidence is an
  in-flight execution gap, not a legal turn-ending `continue`.
- In nonstop mode, a partial latest-snapshot closeout challenge such as `4/5`
  cleared with `1/5` timed out is not a handoff boundary when tools are still
  available. Immediately replace, shrink, or otherwise re-run the timed-out
  lane in the same turn instead of pausing on partial consensus.
- Treat a timed-out final closeout lane as a live execution gap, not as
  implicit permission to end the turn. Only carry that gap into a continue
  receipt when a real host/tool boundary prevents launching the replacement
  lane in the current turn, and record that replacement attempt as the
  `next_mandatory_action`.
- When a user challenges an apparent `$loop` stop, perform a stop-forensics
  triage before answering: `explicit_user_stop_received`,
  `fresh_5lane_stop_proof_passed`, `external_no-action_blocker_recorded`,
  or `controller_defect_premature_visible_final`. If none of the first three is
  backed by current artifacts, classify it as
  `controller_defect_premature_visible_final`, record the missing gate or
  agent-use evidence, harden the applicable skill/runbook when the instructions
  allowed the mistake, and resume the next bounded action rather than defending
  the prior final.
- If the user challenges a `run_decision=continue` final-channel receipt as a
  stop, classify the perception itself as a loop-control defect unless a
  terminal `run_decision=stop` proof was emitted. Do not emit another visible
  durable-runtime continue receipt in the same run while tools are available.
  Record the cause in the run artifacts, harden the gate or instructions that
  allowed the perception gap, and continue tool-backed work until a terminal
  stop, explicit user stop, or true host/tool boundary exists.
- In `durable_runtime`, do not use `closeout_gate.py` to surface a
  final-channel `continue` receipt solely because commit authority is missing,
  even after a no-bounded-action challenge. Commit permission blockers are too
  easy to read as semantic stop. Keep executing non-commit bounded work, or if
  the user has explicitly forbidden continue-style visible turns, keep the run
  in commentary/tool execution until a valid terminal stop can be produced.

## Operator Surface

- `$loop`
- `$agent-loop`

Accept these source forms:

- local path
- existing `.agents/agent-loop/runs/<run-name>/` directory or its `handoff.md`
- markdown link
- `file://` URL
- pasted markdown
- pasted prose or backlog note

## Quick Start

1. Read the host contract first when the loop targets a repository or an
   implementation surface:
   - `AGENTS.md`
   - `CLAUDE.md`
   - equivalent local engineering instructions
2. Resolve the source:
   - if the path already points at an existing run directory, treat it as a
     resume request and reload `source.md`, `ideas.md`, `research.md`,
     `revised-plan.md`, `handoff.md`, and `evidence.md` before taking any new
     action
   - read readable local paths directly
   - preserve pasted structure
   - keep the first line as the working-goal candidate when both goal and body
     exist
3. Normalize the request into:
   - `working_goal`
   - `success_conditions` when present
   - `request_intent`
   - explicit constraints, priorities, and dependency hints
   - sequential markers such as `first`, `then`, `먼저`, `그 다음`
   - whether this request materially differs from any currently active or
     recently resumed `$loop` run in the same conversation
4. Set `continuation_mode` early:
   - bare implementation-oriented `$loop` => `nonstop`
   - explicit "멈추지 마" / "don't stop" => `nonstop`
   - planning-only requests may stay `default`
   - once the working goal is accepted, treat continuation as already
     authorized; do not create later permission checkpoints just to keep
     executing or to decide whether delegated agents may be used
5. Create or resume a stable run directory under
   `.agents/agent-loop/runs/<run-name>/`.
   - if the normalized working goal materially differs from an older run still
     visible in the conversation, open a sibling run for the new goal instead
     of reusing the old run's authority snapshot
   - record the older run only as supporting evidence when it matters
   - create or select the run through the `run_authority_record`; if selection
     is ambiguous, quarantine stale candidates instead of borrowing their stop
     authority
   - for projects without an adapter manifest, use the explicit conservative
     default adapter rather than inferring expanded permissions
   - resolve `work_type`, `completion_subject_type`, and any `review_kind`
     before Research; use
     [worktype-authority-contract.md](references/worktype-authority-contract.md)
     for the exact schema
6. Record capability choices before ideation/research starts:
   - `capability_mode` must include `delegated_agents_authorized_by_loop` plus
     a concrete availability suffix such as `tool_available`,
     `tool_unavailable`, or `tool_state_unknown`
   - delegated agents are authorized by the `$loop` token itself whether the
     host currently exposes `spawn_agent` or not
   - resolved lane model policy, including concrete model slug and reasoning
     effort for each delegated role; every lane must be `gpt-5.5/high` or
     stronger, with no 5.4, Spark, 5.3, mini-model, low-effort, or medium-effort
     fallback
    - model mix policy: bounded implementation workers and material pre/post
      implementation challenge panels use at least `gpt-5.5/high`; material
      initial research and final halt/completion panels use three
      `gpt-5.5/xhigh` lanes and two `gpt-5.5/high` lanes
   - whether the user explicitly asked for Claude participation

## Default Run Artifacts

Persist loop state to disk:

- `source.md`
- `ideas.md`
- `research.md`
- `revised-plan.md`
- `implementation-log.md`
- `commit-ledger.json`
- `handoff.md`
- `evidence.md`
- `run-authority.json` or `authority/run-authority.json`
- `challenge-cycles/<cycle-id>.json`
- `completion-subjects/<subject-id>.json`

`ideas.md` is a candidate inventory, not evidence and not scope authority. Only
Research-validated candidates may add or alter plan actions. Rejected
candidates may shape `revised-plan.md` only as ruled-out constraints or
non-actions with cited evidence in `research.md`.

`implementation-log.md` is the compact per-batch implementation record. Keep it
append-only by batch and prefer one-screen tables over prose. For each material
batch record `batch_id`, `tier`, `req_ids`, files, implementation strategy,
verification plan, pre/post challenge status, verification result, and repair
cause when applicable.

`commit-ledger.json` is the authoritative commit-intent and commit-status ledger
for agent-owned batches. Workers must record commit intent immediately after a
bounded implementation batch, before leaving dirty files for later cleanup. The
ledger, not a later dirty-tree guess, is the authority for semantic labels,
owned paths, verification evidence, and commit eligibility.

Use only the canonical bullet-form handoff shape from
[handoff-template.md](references/handoff-template.md). If a run still has a
legacy or mixed handoff, refresh it before trusting it:

```bash
python <skill-dir>/scripts/refresh_legacy_handoffs.py <run-dir> --write --continue-exit-status <next_action_started|blocked_during_attempt> --continue-exit-evidence "<latest-attempt-proof>" --turn-exit-evidence "<forced-host-boundary-proof>"
```

Keep these handoff fields live and explicit:

- `work_type`
- `review_kind`
- `completion_subject_type`
- `completion_subject_digest`
- `composite_subject_digest`
- `authority_record_ref`
- `run_authority_status`
- `run_authority_revision`
- `run_authority_epoch`
- `source_digest`
- `stage_graph_digest`
- `adapter_manifest_ref`
- `adapter_effective_config_digest`
- `research_cycle_ref`
- `research_cycle_status`
- `research_cycle_digest_set`
- `challenge_cycle_status`
- `current_or_next_stage`
- `remaining_required_stages`
- `goal_completion_status`
- `next_mandatory_action`
- `run_decision`
- `pause_reason`
- `resume_instructions`

Read the full field contract in
[worktype-authority-contract.md](references/worktype-authority-contract.md),
[closeout-and-resume.md](references/closeout-and-resume.md), and
[handoff-template.md](references/handoff-template.md) when editing
`handoff.md`.

## Stage Loop

Before choosing a stage path, resolve `work_type`:

- `implementation`: repo or file changes; use implementation risk tiers below.
- `research`: question framing, source/evidence gathering, synthesis, and
  contradiction check; final subject is `research_packet`.
- `docs`: audience/scope, draft or rewrite, factual/style check; final subject
  is `document_artifact`.
- `planning`: requirement trace, alternatives, revised plan, challenge; final
  subject is `plan_artifact`.
- `review`: bind the target, run review/challenge lanes, aggregate verdicts,
  and record required changes; final subject is the matching review/audit
  subject.
- `mixed`: create a stage graph and a `composite_subject` that includes every
  required stage contribution.

### 0. Risk Tier / Requirement Trace

- Classify every implementation batch before Research. The tier determines the
  required strategy, challenge, verification, and commit evidence:
  - `tier0_trivial`: typo, copy, no-behavior local style, or mechanical
    single-surface cleanup. No pre/post challenge; record a verification note.
  - `tier1_local`: single feature, local component/service change, or a small
    file set with bounded behavior. Record implementation summary and
    verification plan; post self-check is enough unless risk expands.
  - `tier2_material`: API, DB, auth, state flow, server action, shared domain
    logic, user-facing workflow, or multi-file behavior change. Require
    implementation strategy, verification plan, pre 5-lane challenge, planned
    verification, and post 5-lane challenge.
  - `tier3_high_risk`: migration, payment, entitlement, permission boundary,
    production/deployment path, workflow/config/package script, or architecture
    change. Require all tier2 gates plus rollback/compatibility notes and
    commit-owner review for shared/high-risk files.
- Seed a compact requirement trace before implementation work:
  `REQ | implementation claim | verification | status`. Keep this in
  `implementation-log.md` or `revised-plan.md`; do not create a sprawling trace
  document unless the source is large enough to need it.
- Record explicit skip states instead of silently omitting gates. Valid skip
  codes are `tier0_trivial`, `single_file_local_fix`,
  `user_specified_exact_change`, and `no_behavior_change`. For an accepted
  `tier1_local` gate, a skip is valid only when `implementation_gate_evidence`
  records `mini_plan_validation_skip=<skip-code>`, concrete
  `local_verification=<evidence>`, and `skip_scope_evidence=<why the skip
  applies>`. For an accepted `tier0_trivial` gate, the same evidence shape is
  valid with `mini_plan_validation_skip=tier0_trivial` or another exact
  deterministic skip code. Ordinary `tier1_local` work may also close the
  implementation batch with `tier1_self_check=pass`, `risk_expanded=false`,
  implementation summary, verification plan, requirement trace, local
  verification result/ref, scoped files, and explicit no
  external/API/DB/security/shared-boundary scope. Tier2/tier3 accepted gates
  cannot use waiver/skip/self-check instead of the required 5-lane pre/post
  challenge artifacts.
- For bug fixes or regressions, capture a baseline/repro note before strategy:
  failing command, log, screenshot, route, file reference, or direct code
  evidence. If no baseline is possible, record why before editing.

### 1. Ideation / Discovery

- Run a bounded divergent pass before Research to collect candidate approaches,
  outside methods, prior art, product patterns, research leads, alternative
  architectures, UX patterns, and risky hypotheses that the repo-local view may
  miss.
- First classify the Ideation need: known next action or deterministic local
  work => `0` with `ideation_not_material`; material ambiguity => `3`;
  high-impact ambiguity where missed alternatives are plausibly costly => `5`.
  The default three Ideation viewpoints are `repo-local alternatives`, `outside
  patterns`, and `risk hypotheses`; run them controller-internally unless
  delegation materially helps. Reserve "delegated lanes" for `spawn_agent`
  dispatches, and do not inherit the final halt or completion proof rule
  into Ideation.
- Write candidates to `ideas.md`, not `research.md`. Follow
  [ideas-template.md](references/ideas-template.md): every candidate needs a
  stable `idea_id`, `cycle_id`, `source_requirement_ref`, provenance/source
  quality fields, `validation_required`, `currency_risk`, `blocking`, and
  `research_status=pending|validated|rejected|stale`.
- Treat ideation output as unverified hypotheses. It may propose what Research
  should check, but it must not directly authorize Plan, code edits, or stop
  proof.
- For deterministic local work, record `ideation_not_material` and go straight
  to Research. This includes named failing tests, specific files, regressions,
  typos, localized UI copy fixes, lint/type errors, deterministic stack traces,
  user-prescribed implementations, resumed runs with a concrete next action,
  and emergency or surgical fixes.
- Broad inspiration sources are allowed in Ideation, but source quality must be
  labeled. Third-party posts, memory, examples, and prior art are leads only
  until Research validates them with repo inspection, official docs, primary
  sources, or direct runtime evidence.
- Keep Ideation finite: one pass, no recursive source chasing, and a total
  merged-output cap of 5 minutes, 5 candidates, and 3 external sources.
  Reassessment Ideation is capped at 3 minutes, 3 candidates, and 2 external
  sources tied to the remaining gap.
- Pending ideas are non-blocking by default, must not expand
  `remaining_required_stages`, and may be revisited only when their
  `next_review_trigger` matches an active gap. A pending idea with
  `blocking=true` must move into Research before Plan or be downgraded to
  non-blocking with a rationale.
- On reassessment cycles, revisit `ideas.md` only for remaining gaps,
  higher-leverage alternatives, or newly visible constraints; do not reopen
  broad brainstorming by default when the next action is already determined.

### 2. Research

- Inspect the current target state before locking a plan. At minimum, record the
  source authority, existing run artifacts when resuming, relevant repo files,
  tests/configs, dirty-worktree constraints, runtime/tool availability, and any
  external systems the goal may touch.
- Consult official docs first when model, runtime, tool, MCP, Codex, or Claude
  behavior materially affects the plan. Record an `official_docs_decision`:
  `consulted` with refs, or `not_material` with a one-sentence rationale.
- Use an explicit `frontier_loop_authority_v1/high` or stronger model for
  Codex research/challenge lanes when delegated agents are available. A lane launched without explicit
  `model=<pin>` and `reasoning_effort=<pin>` is inadmissible.
- For each delegated research/challenge lane, preserve proof of the resolved
  model slug, reasoning effort, resolution basis, explicit spawn args, and the
  dispatch receipt. Missing, default/inherited, Spark, 5.3, mini-model, `low`,
  or `medium` selection is inadmissible evidence, not a weaker-but-usable lane.
- Do not defer research/challenge lanes to ask whether agents may be opened;
  `$loop` already grants that delegation authority when the tool is available.
- Before research starts, record
  `capability_mode=delegated_agents_authorized_by_loop_<tool_available|tool_unavailable|tool_state_unknown>`.
- Before the first plan lock in every material non-fast-path/non-self-check `$loop` run, dispatch exactly five Codex
  research lanes when `spawn_agent` is available:
  `architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, and `implementation_quality`. Local controller
  inspection is still required, but it cannot replace these initial five
  research lanes.
- Planning may consume initial Research only after all five lane artifacts are
  merged into one synthesis with concrete refs for every lane. Missing, skipped,
  inherited-model, default-model, timed-out, or blocked initial research lanes
  are blockers; record the concrete runtime blocker and make retrying the
  mandatory 5-lane research dispatch the next action. Do not use
  `delegated_research_not_material` as a bypass before the first plan lock.
  The validator-recognized exceptions are the tier0/tier1 deterministic fast
  path described above, which must record `fast_path_reason`, minimal plan,
  requirement trace, local verification, no external/API/DB/security scope, and
  reversibility evidence, and the ordinary `tier1_local` self-check path, which
  must record `tier1_self_check=pass`, `risk_expanded=false`, implementation
  summary, verification plan, requirement trace, local verification result/ref,
  scoped files, and no external/API/DB/security/shared-boundary scope.
  Each research lane artifact must bind `source_digest`,
  `authority_revision_at_dispatch`, `authority_epoch_at_dispatch`,
  `agent_role=research_agent`, explicit model args, and a resolvable
  `dispatch_receipt_version=v1` spawn receipt with the same research cycle id.
- Record decision-relevant evidence in `research.md` as
  `evidence -> plan impact`. Include negative evidence when it rules out an
  approach or proves a constraint does not apply. Keep raw command output,
  dispatch receipts, and broad scan notes in evidence/receipt files and cite
  them from `research.md`.
- Consume `ideas.md` as a validation queue: mark relevant candidates
  `validated`, `rejected`, or `stale` only through cited Research evidence.
  Every non-`pending` transition must include `research_ref`, `evidence_ref`,
  `decision_date`, and `decision_summary`. Leave irrelevant candidates as
  non-blocking `pending` rather than smuggling them into Plan.
- Separate source authority from inspected-state constraints. Repo findings may
  constrain the plan, but they must not silently redefine the user's goal.
- Classify open questions before Plan as `blocking`,
  `plan-shaping but bounded`, or `non-blocking`; Research may hand off only with
  zero `blocking` questions.
- Research is sufficient only when the controller can defensibly state: given
  the inspected current state and official/delegated evidence, no known
  unresolved fact would change the next bounded plan action or invalidate the
  selected approach. If that sentence needs an uncited assumption, continue
  Research or record a blocker.

### 3. Implementation Strategy And Plan

- Reconstruct the source into one authoritative `revised-plan.md`.
- Plan lock is mandatory before any code edit, worker dispatch, migration,
  test-fix batch, or verification-only repair that changes files. Even a
  deterministic or surgical run needs a compact plan row that states the
  requirement, target files, patch order, verification command, and stop/next
  reassessment criteria.
- The authoritative plan must be produced or ratified by the strongest available
  Codex model. A controller may draft locally, but before execution the plan
  must record `plan_model_policy=strongest_model_required`,
  `plan_model_slug=gpt-5.5`, `plan_reasoning_effort=xhigh`, and the dispatch or
  controller evidence that made it authoritative. If the strongest model is
  quota-blocked, record a blocker instead of accepting a 5.4 plan.
- A missing, stale, unratified, or weaker-model plan is a blocker, not an
  optimization to skip. Set `next_mandatory_action` to create/ratify the plan
  lock before implementation resumes.
- Exception: validator-recognized `tier0_trivial` and deterministic
  `tier1_local` fast paths may use a compact local minimal plan before editing
  instead of strongest-model plan ratification when they record
  `fast_path_reason`, requirement trace, local verification, scoped files,
  reversibility, and explicit no external/API/DB/security scope. Ordinary
  `tier1_local` self-check may do the same when it records
  `tier1_self_check=pass`, `risk_expanded=false`, implementation summary,
  verification plan, requirement trace, local verification result/ref, scoped
  files, and no external/API/DB/security/shared-boundary scope. These evidence
  shapes accept the local implementation batch; they still do not authorize a
  semantic terminal `$loop` stop without the required final completion proof.
- After plan lock and before implementation, run a mandatory mini 2-lane plan
  validation for file-changing implementation batches unless a validator-
  recognized tier1 skip applies or the accepted gate explicitly proves
  `file_changing_batch=false`. Required practical viewpoints are
  `operator_execution_fit` (patch order, ownership boundaries, shared-state
  risk, rollback/conflict handling) and `verification_evidence_fit` (smallest
  useful checks, failure interpretation, edge cases, and evidence refs). Use
  one `gpt-5.5/xhigh` lane and one `gpt-5.5/high` lane with explicit tool args.
  Missing or blocked mini plan validation is a blocker when no valid skip or
  non-file-changing proof exists.
- Expand sequential objectives into explicit required stages.
- Keep the current stage bounded and execution-ready.
- For every non-fast-path `tier1_local` or higher batch, record an implementation strategy and
  verification plan before editing. This strategy/verification plan must be
  authored or ratified by a mixed model panel when delegation materially helps,
  with `gpt-5.5/xhigh` carrying final ratification. The strategy must state the
  chosen approach, target files/modules, data/API/state flow changes, existing
  local patterns to follow, rejected alternatives, risk notes, and the smallest
  relevant verification command set.
- If a batch touches a core write path, shared workflow gate, security/release
  policy, migration, billing, auth, AI/provider lane, or cross-module boundary,
  treat delegation as materially helpful unless the tool is unavailable or the
  change is demonstrably mechanical. A no-agent shortcut for those areas must
  be recorded as a waiver with risk tier, reason, and compensating verification;
  otherwise the missing research/plan/verification lanes are a loop-process
  defect to repair before accepting the batch.
- For `tier2_material` and `tier3_high_risk`, run a pre-implementation 5-lane
  challenge before execution. Required viewpoints are:
  `architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, and `implementation_quality`.
  A material implementation may start only after PASS/ALLOW consensus, a
  recorded blocker, or an explicit external override.
- The pre-challenge reviews strategy and verification together. It is not a
  final completion proof and must not expand scope beyond the current batch.
- Keep the execution plan separate from the implementation strategy: strategy
  says how the design works; execution plan says the next concrete patch order,
  ownership, and verification commands.
- Treat source plans as evidence, not as final authority.

### 4. Execute

- Work one bounded stage at a time.
- Prefer the next concrete local action over recap.
- Keep worker scope narrow when delegation helps, and dispatch delegated
  workers without a separate permission check inside `$loop`.
- Preserve evidence with direct file refs, tests, logs, and diffs.
- Update `revised-plan.md`, `implementation-log.md`, `evidence.md`, and
  `handoff.md` as the live source of truth.

### 5. Verify And Reassess

- Run the smallest relevant validation for the changed area before claiming
  progress.
- Treat `apply_patch -> smallest relevant validation -> evidence/handoff
  refresh` as one atomic bounded batch. Do not leave a fresh local edit sitting
  between those steps and then blame a same-turn boundary for the pause shape.
- Re-research after each closed stage when the remaining plan may change.
- After implementation and planned verification, run the mini 2-lane plan
  validation before marking a file-changing batch as accepted when the batch is
  tier2/tier3, the risk expanded, or a delegated mini gate was part of the
  chosen strategy. For ordinary `tier1_local` work, a recorded self-check is
  sufficient when it includes implementation summary, verification plan,
  requirement trace, local verification result/ref, scoped files, `risk_expanded=false`,
  and no external/API/DB/security/shared-boundary scope. The post lanes judge
  practical plan conformance, whether verification evidence actually supports
  the claim, and whether the next action/stop posture follows from the evidence.
  This mini gate does not replace the tier2/tier3 5-lane post-implementation
  challenge.
- For file-changing accepted gates that do not use a validator-recognized
  deterministic fast path or tier1 self-check path and do use delegated mini
  validation, record a distinct `verification_agent_ref` before the post lanes.
  That artifact must be produced by `agent_role=verification_agent` with
  `verification_agent_mode=current_stage_verification`, bind the current
  authority/source/stage digests, name the verification command/result/evidence
  refs, and carry explicit delegated model dispatch evidence. Challenge lanes
  may judge verification quality, but they are not the verification agent.
- For `tier2_material` and `tier3_high_risk`, run a post-implementation 5-lane
  challenge after planned verification and before marking the batch as accepted
  progress. These verification/acceptance lanes must use the mixed panel policy
  with `gpt-5.5/xhigh` final ratification. Required viewpoints are:
  `architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, and `implementation_quality`.
- If verification or post-challenge fails, record a repair cause before the next
  patch: `wrong_requirement_interpretation`, `wrong_architecture_choice`,
  `incomplete_implementation`, `missing_edge_case`,
  `insufficient_verification`, or `unrelated_existing_failure`.
- Continue into the next required stage whenever meaningful work remains.
- After each verified batch, immediately reopen the next cycle on the remaining
  highest-leverage gap unless fresh unanimous 5-lane halt/completion proof
  already exists.
- If the clean final audit or completion challenge finds any unmet original
  prompt requirement, residual gap, narrowed-scope plan error, or denying lane,
  treat that as failed completion proof. Update `revised-plan.md` and
  `handoff.md`, set `run_decision=continue`,
  `goal_completion_status=not_reached`, put the gap in
  `remaining_required_stages`, and immediately start the first bounded
  repair/verification action without asking whether to continue.
- Before autonomous `stop`, confirm this run still matches the latest active
  `$loop` working goal in the conversation; if the user has since opened a
  materially different `$loop` goal, this run may no longer be the visible
  answer authority.
- Before terminal output, atomically reread the selected authority record,
  recompute source/subject/composite/stage-graph digests from canonical
  artifact refs, rerun adapter conformance/version checks, and compare against
  the accepted current challenge cycle. If any revision, epoch, status, digest,
  version, or adapter effective config changed, reject completion and continue.
- Default to `continue` whenever halt proof is missing, stale, ambiguous, or
  denied.

### 6. Commit Intent And User-Authorized Curator

- Every bounded implementation batch that leaves local file changes must record
  commit intent before handoff or the next unrelated batch. Use `commit-ledger`
  state rather than relying on a future agent to infer meaning from dirty files.
- A commit intent must include `batch_id`, `owner_agent`, `source_run`,
  `semantic_label`, `change_type`, `owned_paths`, `base_head`, `diff_hash`,
  `verification_command`, `verification_result`, `risk_level`,
  `commit_status`, and `blocker` when present.
- Use a constrained `semantic_label` taxonomy. Prefer labels such as
  `loop-process`, `commit-broker`, `dev-server`, `ui-study`, `api-auth`,
  `tests`, `docs`, `config`, and `release` over free-form labels.
- Commit curation has only three queue outcomes:
  `ready_to_commit`, `needs_commit_owner`, and `orphan_or_conflicted`.
  Do not let the curator invent a semantic batch from dirty-tree guessing when
  no matching intent exists.
- `ready_to_commit` requires unchanged `base_head`, unchanged `diff_hash`,
  owned paths only, no foreign staged paths, verification after the latest diff,
  no unresolved overlap, and a message matching the semantic label.
- Shared/high-risk files such as package manifests, lockfiles, workflow files,
  migrations, loop/dev-server/build scripts, and config files go to
  `needs_commit_owner` unless the designated commit owner explicitly approves
  and records the review.
- Actual commit execution is user-gated. Recording commit intent, verification
  evidence, or `needs_commit_owner` blockers is not permission to run the commit
  broker. Do not execute `npm run loop:commit:auto`, `git add`, or any `git
  commit` path until the latest user instruction explicitly contains
  `$loop 커밋`. If that token is absent, leave eligible batches queued as
  `ready_to_commit` or `needs_commit_owner` and continue with non-commit
  implementation, verification, or status work.
- After any user-authorized broker or commit-owner attempt, immediately reconcile the ledger:
  committed SHA, included batch ids, remaining dirty files, owner/blocked reason
  for each remaining file, and next action. A committed or blocked request file
  is execution evidence, not the authoritative batch inventory.

## Status Requests

When the user asks for the current state mid-run:

- Answer from live state, not from completion prose.
- Use the canonical live-state gate whenever a run directory already exists:

```bash
python <skill-dir>/scripts/emit_status_reply.py <run-dir> [--blocking-or-risk "..."]
```

- Keep the status reply inside short live-state fields such as:
  - `loop_state=...`
  - `current_or_next_stage=...`
  - `next_mandatory_action=...`
  - `blocking_or_risk=...` when needed
- Treat the status answer as commentary inside the active invocation; do not
  reinterpret it as permission to pause or stop.
- If the status request arrives while a tool command, dev server diagnosis, DB
  diagnosis, or verification batch is in progress, finish only the in-flight
  safe action needed to avoid leaving shared state ambiguous, report the live
  result, and make the next action explicit. A requested briefing is not a final
  answer unless the user directly says to stop.
- Do not append consent-seeking language such as `continue?`, `want me to keep
  going?`, `open agents?`, `진행할까요`, `에이전트 열까요`, or equivalent
  check-in phrasing; `$loop` already carries standing continuation and
  delegated-agent authority.
- If the user says the loop "stopped" or explicitly reminds that `$loop` must
  not stop, treat that as evidence to tighten execution/closeout behavior and
  keep going under the same delegated-agent authority rather than asking for a
  new agent-use permission.
- If the host then forces a visible turn end, record a truthful pause without
  changing the goal state.

Use [closeout-and-resume.md](references/closeout-and-resume.md) for the detailed
status-vs-closeout rules.

## Closeout Discipline

### Pre-Final Guard

The `final` channel is a stop-like surface for the user. In an active `$loop`
run, do this guard immediately before using it:

1. Re-read the current run's `handoff.md`.
2. If `run_decision=continue`, `goal_completion_status!=verified_complete_5lane`,
   or `remaining_required_stages` contains any work, do not emit a normal final
   answer. Continue with the next concrete tool-backed action.
3. If `completionStopAllowed=false`, do not convert `npm run loop:handoff`
   output, test results, or a work summary into `final`. Choose an allowed
   transition: `next_bounded_action_started`, `stop_or_completion_challenge_dispatched`,
   `canonical_no_bounded_action_blocker_recorded`, or
   `validated_forced_boundary_gate_output`.
4. If a visible turn end is unavoidable because the host forces it, first update
   the handoff with a fresh attempt receipt and host-boundary receipt, validate
   it, and emit only `closeout_gate.py` output.
5. If a previous turn violated this guard, treat the next user follow-up as an
   auto-resume/control-defect repair: document the root cause, patch the loop
   control text if needed, and continue the run. Do not ask whether to resume.

Before any unavoidable user-visible turn end:

1. Refresh `ideas.md`, `research.md`, `revised-plan.md`, and `handoff.md`
   before final proof starts; do not mutate `ideas.md` after proof dispatch.
2. Keep `handoff.md` canonical bullet-form; v2 is valid for compatibility and
   nonterminal/explicit-user-stop paths, while verified autonomous terminal
   stops use v3 work-type authority fields.
3. Classify goal state correctly:
   - `not_reached`
   - `completion_candidate`
   - `verified_complete_5lane`
4. Run:

```bash
python <skill-dir>/scripts/validate_handoff.py <run-dir> --require-consensus
```

5. Emit the turn-ending reply only through:

```bash
python <skill-dir>/scripts/closeout_gate.py <run-dir> [--active-delta "..." --blocking-or-risk "..."]
```

6. Do not append free-form wrap-up prose after the gate output.
7. For terminal `run_decision=stop`, keep the public receipt compact but richer than the base status fields:
   - include the canonical stop fields
   - include a derived `work_process=` line synthesized from the authoritative run plan
   - include a derived `work_summary=` line synthesized from authoritative evidence/handoff summary
   - include a derived `verification_summary=` line synthesized from validation evidence and stop/completion proof status
   - include a derived `need_to_know=` line synthesized from blocking findings, residual risks, or unverified-stop caveats; use `none` when there is nothing material
   - keep those lines gate-produced and validator-enforced rather than hand-written
   - never add this full briefing shape to `run_decision=continue` or `run_decision=pause`; those states must stay low-freedom live-state receipts so they cannot read as completion

In `continuation_mode=nonstop`, do not treat closeout as part of the normal
loop cycle. Closeout is only for a real external boundary. If the next
mandatory action is known and tools are still available, continue executing
instead of emitting a pause receipt.

Before any user-visible turn end, if the only missing stop proof is one or more
timed-out closeout lanes and a deterministic replacement/shrunk lane can still
be launched now, launch it now. Do not convert partial closeout consensus into
handoff state merely because the proof set is incomplete.

For a live handoff update while tools are still available, validate with
`validate_handoff.py <run-dir> --require-consensus --live-state`. Do not force
`turn_exit_cause=host_turn_boundary_pause` merely to satisfy closeout-style
validation when no visible turn end is being emitted.

When resuming an already-emitted continue/pause receipt, validate the stored
state with `validate_handoff.py <run-dir> --require-consensus --resume-state`
before editing. This allows the last `closeout_round_id` to appear in its own
closeout receipt while still requiring a fresh `closeout_round_id` for the next
turn-ending reply.

Treat these scripts as gate-only internals:

- `emit_continue_reply.py`
- `emit_pause_reply.py`
- `emit_terminal_reply.py`

They reject direct invocation outside the gate.

## Same-Turn-Only Hosts

If the host cannot continue execution across visible user turns:

- Do not preemptively manufacture a same-turn-only boundary. The boundary exists
  only when the host requires a visible final reply before more tool work can
  happen. If tool work is still available in the current turn, continue.
- Prefer a live `run_decision=continue` receipt when live remaining work exists
  and the next user follow-up can auto-resume the same run directory. Record
  `turn_exit_cause=host_turn_boundary_pause` and concrete `continue_exit_*`
  proof instead of writing `loop_state=paused`.
- For same-turn-only quota-blocked delegated dispatches, prefer the same live
  `run_decision=continue` shape: `continue_exit_status=blocked_during_attempt`
  proves the quota blocker, while `turn_exit_cause=host_turn_boundary_pause`
  separately proves why a visible reply is unavoidable. Do not encode a
  delegated quota blocker as `external_authority_basis=host_turn_boundary`
  unless the safe auto-resume continue shape truly cannot be encoded.
- For that live `run_decision=continue` shape, keep
  `stop_authorization_status=not_applicable`,
  `stop_consensus_status=not_applicable`, and
  `external_authority_basis=none`. The host boundary is a turn-exit cause, not
  pause authority, unless the fallback `run_decision=pause` shape is used.
- Use `run_decision=pause` for a host boundary only when the environment cannot
  encode a safe auto-resume path, or when another real external pause basis is
  present.
- Treat any host-boundary pause as forced bookkeeping only; never justify it as
  a reporting checkpoint, user check-in, or optional handoff.
- For host-boundary pauses, record `stop_authorization_status=external_authority`
  and `stop_consensus_status=waived_external_authority`.
- Use `external_authority_basis=host_turn_boundary` for pauses only when
  `turn_exit_cause=host_turn_boundary_pause`, `turn_exit_evidence` proves the
  forced visible boundary, `continue_exit_*` proves the latest attempted
  bounded action, and `host_boundary_ref` is a fresh receipt bound to the same
  `closeout_round_id` and `attempt_ref`.
- Never let a host-boundary pause imply completion; keep
  `goal_completion_status` truthful.
- Do not let `same_turn_only` block a lawful autonomous terminal `stop` when
  both fresh unanimous 5-lane halt proof and fresh unanimous 5-lane
  goal-completion proof already exist for the current authority snapshot.
- Emit a pause receipt that makes the ceiling explicit with
  `host_resume_mode=same_turn_only`, `pause_scope=host_boundary_only`,
  `continuation_authority=standing`, `semantic_state=incomplete_forced_boundary`,
  `followup_resume_policy=auto_resume_any_followup`, `turn_exit_cause=...`, and
  `resume_command=$loop <run-dir>`.
- On the next user turn, treat any ordinary follow-up message as an implicit
  resume when `followup_resume_policy=auto_resume_any_followup`; reopen the
  existing run directory from disk first, then execute the recorded
  `next_mandatory_action`.
- Keep `resume_command` as the canonical shorthand/workaround surface for users
  who want an explicit resume token or for hosts that strip surrounding context.
- Resume the recorded `next_mandatory_action` first on the next turn without
  asking whether to continue.
- If the user says the loop "stopped" after a host-boundary pause, treat that
  as pause-shape UX defect evidence first: tighten the pause receipt or
  validator so the pause reads as bookkeeping instead of semantic completion,
  then continue the run.
- If the user still says the loop "stopped" after a valid auto-resume continue
  receipt, record `receipt_only_final_boundary_perceived_stop`, run the
  resume-event recorder, and perform a tool-backed controller repair or
  validation before another visible receipt. Do not defend the prior receipt as
  sufficient; use the complaint as regression evidence.
- Same-turn-only `continue` receipts must include a Korean
  `user_visible_note=` immediately after `stop_status=not_stopped`. This is a
  user-facing guardrail, not authority: it makes the visible final-channel
  receipt read as a forced turn boundary instead of a completed or stopped run.

### Nonstop Regression Guard

When a same-turn-only host-boundary pause is truly unavoidable in nonstop mode,
`AGENT_LOOP_CONFIRMED_HOST_TURN_END=1` is not sufficient by itself. The public
gate also requires `AGENT_LOOP_FORCED_TURN_END_REASON` to be one of
`blocked_during_attempt`, `context_budget_exhausted`,
`host_turn_boundary_pause`, `tool_timeout_after_batch_shrink`, or `user_interrupt`, plus
`AGENT_LOOP_FORCED_TURN_END_EVIDENCE` echoed in `turn_exit_evidence`. The
evidence must match the selected reason: blocker/error evidence for
`blocked_during_attempt`, context/token/budget/limit evidence for
`context_budget_exhausted`, same-turn-only visible host-boundary evidence for
`host_turn_boundary_pause`, timeout or batch-shrink evidence for
`tool_timeout_after_batch_shrink`, and user-interrupt evidence for
`user_interrupt`. A self-issued phrase such as "host ceiling" is not proof unless
it names the concrete same-turn-only visible host boundary and is echoed in
`turn_exit_evidence`.
This is deliberately awkward: it prevents routine verified-batch closeouts and
self-asserted host-boundary pauses from becoming accidental semantic stops while
still allowing live `continue` receipts at a real same-turn-only host boundary.
If this guard blocks a closeout and tools are still available, resume the
recorded `next_mandatory_action` instead of weakening the guard.

Treat `AGENT_LOOP_CONFIRMED_HOST_TURN_END=1` without the hard reason and echoed
evidence as `forced_boundary_override_misuse`. Repair the skill or artifacts
and continue the run; do not rerun the closeout with only a stronger wording of
the same self-issued boundary.

For `durable_runtime`, `AGENT_LOOP_CONFIRMED_HOST_TURN_END=1` plus a hard
reason is still insufficient for a visible continue receipt. The gate also
requires `AGENT_LOOP_NO_BOUNDED_LOCAL_ACTIONS_REMAIN=1` and
`AGENT_LOOP_NO_BOUNDED_LOCAL_ACTIONS_EVIDENCE` echoed in `turn_exit_evidence`.
This prevents a proof/commit blocker from being mistaken for loop stop while
other local improvement work remains.
When that no-bounded-local-action claim depends on approval, manual ownership,
external authority, production receipts, or a self-assessed blocker, the gate
also requires a fresh five-lane `stop_authorization` challenge attempt in
`stop_consensus_evidence`. The controller may not substitute its own blocker
judgment for the five-lane challenge; if the challenge cannot be dispatched, the
visible state remains `continue` with the dispatch blocker recorded.

A host-boundary turn end is bookkeeping, not semantic completion. Prefer the
live continue receipt when available; never make the user re-authorize the loop.

## Autonomous Stop Rules

- Do not emit autonomous `stop` without fresh unanimous 5-lane halt proof.
- Do not emit goal-satisfied autonomous `stop` without fresh unanimous 5-lane
  completion proof.
- The final five challenge agents must cover the required lane set exactly once,
  with one agent assigned to one distinct perspective.
  Five `allow` votes from duplicate lanes, missing lanes, uncovered scope
  viewpoints, or generic challenge prompts are not unanimous five-lane proof.
- Those five agents must be role-bound challengers: aggregate evidence, lane
  artifacts, and dispatch receipts must all record `agent_role=challenge_agent`
  and the matching `challenge_review_mode`. A final lane that behaves as a
  worker, explorer, summarizer, or generic reviewer is inadmissible even if it
  returns `allow`.
- Bind both proofs to the current `subject_digest` for freshness and to
  `source_digest=<sha256(raw source.md bytes)>` for original-prompt authority.
- For schema v3 authority runs, bind both proofs to the selected
  `run_authority_record`, `authority_revision`, `authority_epoch`,
  `completion_subject_type`, `completion_subject_digest`,
  `stage_graph_digest`, and accepted current `challenge_cycle`. The
  `goal_completion_evidence refs=` must match the cycle `lanes`, and
  `stop_consensus_evidence refs=` must match the cycle `stop_lanes`.
  Completion is legal only after the CAS completion transition receipt
  succeeds.
- Treat `subject_digest` as freshness binding only; it includes loop-local plan
  and evidence files and cannot prove that the original prompt was used as the
  completion scope.
- Treat any missing, ambiguous, stale, or denying lane as `continue`.
- Treat a timed-out completion lane as `continue-and-replace-now` when tools are
  still available in the same turn; do not let timeout alone justify a visible
  boundary or partial-consensus handoff.
- Treat approval-needed-only, human-decision-required, and no-bounded-local-action
  blocker states as stop-authorization questions. They still require a fresh
  five-lane `stop_authorization` challenge attempt before any visible blocked
  closeout; a controller-written blocker note without that challenge is invalid.
- Allow external-authority `stop` only for a direct explicit user stop.
- In the default local file-backed profile, direct current-turn
  `explicit_user_stop` is the only supported human stop override. Record it with
  `scripts/record_user_stop_receipt.py <run-dir> --excerpt "<direct stop>"`
  and cite `user_stop_ref=<receipt>` in `stop_authorization_evidence`.
  `explicit_user_pause`, `explicit_user_redirect`, and
  `human_decision_required` still require host-produced immutable authority and
  are otherwise unsupported.
- Treat `planning_complete` as a planning-only external-authority close, never
  as an implementation stop.

Read the exact proof shape and invalid patterns in
[closeout-and-resume.md](references/closeout-and-resume.md).

## Official Docs First

When loop design depends on tool or model behavior:

- Prefer OpenAI official docs for Codex/OpenAI behavior.
- Prefer Anthropic official docs for Claude-specific behavior.
- Record any official-doc dependency in `research.md` when it materially affects
  the plan.

Preferred official sources:

- `https://developers.openai.com/`
- `https://developers.openai.com/mcp`
- `https://code.claude.com/docs/`
- `https://platform.claude.com/docs/`

## Project Adaptation

If the loop moves into a repository:

- Treat the repository as the execution target, not as the definition of the
  loop itself.
- Preserve dirty-worktree boundaries.
- Map the current stage into repo-local files, checks, and evidence.
- Load or synthesize a `project_adapter_manifest`. Missing manifests use the
  conservative default adapter and must not broaden permissions.
- Validate any `agent_loop_override` against the global allowlist before using
  it. Reject or quarantine terminal proof when project hints conflict with
  global loop semantics.
- Modify the skill itself when the user asked to improve `$loop`; do not
  productize it inside the repo unless explicitly asked.

Use [project-adaptation.md](references/project-adaptation.md) and
[worktype-authority-contract.md](references/worktype-authority-contract.md)
when execution lands inside a repository.

## High-Rigor References

These references are non-authoritative maintainer appendices. They may explain lower-level lifecycle or packet detail, but they do not add, widen, or override the public operator contract in `SKILL.md`.

Use the higher-rigor references only when the user explicitly asks for strict
packet/receipt behavior or when the environment actually provides durable
runtime support:

Bundled reference appendices: `references/worktype-authority-contract.md`,
`references/contracts-and-rules.md`, `references/process-architecture.md`,
`references/profile-sync.md`, `references/kernel-spec-stage1-3-draft.md`,
`references/kernel-spec-stage5-oracle-draft.md`,
`references/kernel-spec-stage6-packets-draft.md`,
`references/kernel-spec-stage7-packet-templates-draft.md`.

- [worktype-authority-contract.md](references/worktype-authority-contract.md)
- [contracts-and-rules.md](references/contracts-and-rules.md)
- [process-architecture.md](references/process-architecture.md)
- [profile-sync.md](references/profile-sync.md)
- `kernel-spec-stage1-3-draft.md`
- `kernel-spec-stage5-oracle-draft.md`
- `kernel-spec-stage6-packets-draft.md`
- `kernel-spec-stage7-packet-templates-draft.md`

## Script Surface

Public scripts:

- `scripts/closeout_gate.py`
- `scripts/emit_status_reply.py`
- `scripts/refresh_legacy_handoffs.py`
- `scripts/record_user_stop_receipt.py`
- `scripts/validate_handoff.py`
- `scripts/validate_status_reply.py`
- `scripts/run-claude-research.mjs`

Internal closeout scripts:

- `scripts/emit_continue_reply.py`
- `scripts/emit_pause_reply.py`
- `scripts/emit_terminal_reply.py`
- `scripts/validate_continue_reply.py`
- `scripts/validate_pause_reply.py`
- `scripts/validate_terminal_reply.py`

If a new nonstop invariant matters in practice, move it into both the written
contract and validator code rather than leaving it as run-local prose.
