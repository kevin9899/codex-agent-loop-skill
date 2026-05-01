---
name: agent-loop
description: "Use via `$loop` or `$agent-loop` inside Codex when you need to turn a local document path, markdown link, pasted backlog, or rough execution note into an end-to-end software-improvement loop that keeps working until the real final goal is complete. Invoking `$loop` already means 'keep going and use delegated Codex agents when they materially help'; no second permission message is required. Default profile is pragmatic file-backed automation with persisted handoff state, standing authorization to use delegated Codex agents where available, the `$loop` token itself acting as the affirmative delegation grant, strongest-model research/challenge where available, implementation-oriented `$loop` runs defaulting to nonstop continuation, immediate resume after any forced host-boundary pause, live-state status briefings instead of completion prose, and a mandatory fresh 5-agent completion challenge before any terminal goal-satisfied stop claim."
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
- Cap delegated Codex agents at five lanes per `$loop` dispatch, including
  research, challenge, verification, halt, and completion proof rounds. Do not
  expand to a sixth lane for difficulty, convenience, or retry
  pressure.
- Treat the first accepted working goal as standing authority to continue; do
  not ask whether to keep going, whether to resume after a progress report, or
  whether to open the next cycle unless a real external approval gate blocks
  execution.
- Keep working until a real blocker, explicit external authority, or forced host
  turn boundary exists.
- In `same_turn_only` hosts, a visible final reply with `run_decision=continue`
  is bookkeeping for a forced boundary, not semantic stop. `$loop` only stops
  semantically after the required fresh `5 Codex` proof or a direct explicit
  user stop.
- Repeat `ideation -> research -> plan -> execute -> verify -> reassess` until
  fresh unanimous `5 Codex` completion proof exists or a direct explicit user
  stop overrides.
- Treat `handoff.md` as continuation state, not as stop permission.
- Keep one authoritative `revised-plan.md` and one authoritative `handoff.md`.
- Keep exactly one working goal per run. If a later user turn opens a
  materially different `$loop` / `$agent-loop` goal, create or resume a new
  authoritative sibling run immediately instead of silently keeping the older
  run as the live authority.
- Expand explicit sequential user objectives into required stages and do not stop
  after only the first one.
- Treat status requests as live-state reporting, not as pause or stop
  authorization.
- Use canonical scripts for any turn-ending closeout; do not hand-write closeout
  prose.
- Do not hand-write a `run_decision=continue` receipt. If a visible turn end is
  truly unavoidable, record the boundary receipt first, then emit only the
  validated `closeout_gate.py` output.
- In `same_turn_only` hosts, a turn-ending `continue` receipt must surface
  `stop_status=not_stopped`,
  `forced_boundary_note=호스트 때문에 보이는 답변만 한번 끊겼고 루프는 멈추지 않았습니다. 아무 후속 메시지나 보내면 같은 run을 즉시 이어갑니다.`,
  `host_boundary_effect=visible_turn_only_not_goal_stop`,
  `auto_resume_trigger=any_followup_message`,
  `followup_resume_policy=auto_resume_any_followup`, and an exact
  `resume_command=$loop <run-dir>` so any ordinary follow-up can be treated as
  an immediate continuation rather than a fresh permission checkpoint.
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
- Require a fresh unanimous `5 Codex` completion challenge before any
  goal-satisfied autonomous `stop`.
- Final halt/completion challenge lanes must be viewpoint-separated: dispatch
  exactly one fresh Codex agent for each required viewpoint
  (`architecture_dependency`, `failure_verification`, `goal_efficiency`,
  `requirement_alignment`, `implementation_quality`). Each agent must judge
  from its assigned perspective, not from a generic all-purpose review prompt;
  duplicate, missing, or blended viewpoints make the five-agent proof
  inadmissible even when all returned votes are `allow`.
- Treat `source.md` as the sole authority for the original user request during
  final halt/completion proof. Final stop lanes must run from a clean,
  source-first packet: no full-history fork, no prior loop transcript as scope,
  and no trust in `ideas.md`, `research.md`, `revised-plan.md`, `evidence.md`,
  or `handoff.md` except as implementation claims to inspect against
  requirements reconstructed from `source.md`.
- Final halt/completion proof must record `source_ref=source.md`,
  `source_digest=<sha256(source.md)>`, `context_mode=clean_source_first`,
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
- Use the resolved strongest hard-pinned model for every delegated `$loop`
  research, worker, verifier, halt, and completion lane. In the current local
  Codex model catalog this resolves to `model=gpt-5.5` with
  `reasoning_effort=xhigh`; update the resolved pin only when the runtime model
  catalog changes. Cost, speed, convenience, retry pressure, or thread-limit
  recovery are not valid reasons to downshift.
- Every delegated `spawn_agent` call in a `$loop` lane must pass the resolved
  pin explicitly as tool arguments: `model=<resolved_model_slug>` and
  `reasoning_effort=<resolved_reasoning_effort>`. Inherited, omitted, default,
  or "probably strongest" model selection is inadmissible for `$loop`, even when
  the parent invocation appears to be running on the same model.
- For halt/completion challenge proof, every lane artifact must record
  `model_policy=resolved_strongest_hard_pin`, `resolved_model_slug=<pin>`,
  `resolved_reasoning_effort=<pin>`, `model_resolution_basis_ref=<source>`,
  `spawn_model_binding=explicit_tool_args`,
  `spawn_tool_args_model=<pin>`,
  `spawn_tool_args_reasoning_effort=<pin>`, and
  `spawn_tool_call_ref=<dispatch receipt>`. The dispatch receipt must resolve
  inside the run directory and prove clean source-first context with
  `full_history_fork=false`, the same `source_digest`, explicit model args, and
  the same `challenge_round_id` / `closeout_round_id`. The handoff validator
  rejects unanimous proof that omits these fields or uses a
  weaker/default/inherited model.
- If `spawn_agent` rejects combining full-history fork with explicit model
  overrides, do not drop the model pin and do not fall back to inherited
  selection. Spawn with a narrow explicit packet and pass
  `model=<resolved_model_slug>` plus
  `reasoning_effort=<resolved_reasoning_effort>` on the tool call.
- If every required delegated lane is blocked by usage limits, quotas, credits,
  or rate limits after explicit strongest-model dispatch, treat that as
  `continue_exit_status=blocked_during_attempt`, not as pause or stop
  authority. Do not downshift models, do not reduce the required five lanes, and
  do not count errored/skipped lanes as consensus proof. Persist the dispatch
  blocker artifact and make the next mandatory action retrying the same
  explicit `gpt-5.5/xhigh` challenge after the quota clears.
- Use the strongest available `5 Codex` lanes for halt/completion challenge
  proof when delegated agents are available; do not silently downgrade to fewer
  lanes or weaker models for convenience.
- Bind autonomous stop proof to the current authority snapshot rather than a
  reusable old challenge round.
- Do not emit a terminal `stop` for an older run as the visible answer to a
  newer `$loop` goal. Older-run proof may be preserved as context evidence, but
  it cannot satisfy or terminate the newer goal.
- Bind `subject_digest` to the live authority state, not the proof text itself.
  The validator redacts self-referential proof evidence fields from `handoff.md`
  before hashing so 5-agent proof can reference the digest without creating an
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
- Before any `final`-channel answer in an active `$loop` run, reopen the live
  `handoff.md`. If it says `run_decision=continue`, `goal_completion_status` is
  anything other than `verified_complete_5agent`, or
  `remaining_required_stages` is non-empty, a normal final summary is illegal.
  The next visible action must be a commentary update followed by a concrete
  tool-backed implementation, verification, or blocker-recording step. Only a
  host-forced boundary may reach `final`, and that path must go through the
  canonical closeout gate with a valid host-boundary receipt.
- Treat a final-channel completion recap after a verified batch as a
  controller defect when the handoff still says `continue`. The correct repair
  is not to explain the recap; it is to record the defect, harden the loop
  instructions, and immediately execute the next bounded stage.
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
6. Record capability choices before ideation/research starts:
   - `capability_mode` must include `delegated_agents_authorized_by_loop` plus
     a concrete availability suffix such as `tool_available`,
     `tool_unavailable`, or `tool_state_unknown`
   - delegated agents are authorized by the `$loop` token itself whether the
     host currently exposes `spawn_agent` or not
   - resolved strongest-model hard pin, including concrete model slug and
     reasoning effort
   - whether the user explicitly asked for Claude participation

## Default Run Artifacts

Persist loop state to disk:

- `source.md`
- `ideas.md`
- `research.md`
- `revised-plan.md`
- `handoff.md`
- `evidence.md`

`ideas.md` is a candidate inventory, not evidence and not scope authority. Only
Research-validated candidates may add or alter plan actions. Rejected
candidates may shape `revised-plan.md` only as ruled-out constraints or
non-actions with cited evidence in `research.md`.

Use only the canonical bullet-form v2 handoff shape from
[handoff-template.md](references/handoff-template.md). If a run still has a
legacy or mixed handoff, refresh it before trusting it:

```bash
python <agent-loop-skill-dir>/scripts/refresh_legacy_handoffs.py <run-dir> --write --continue-exit-status <next_action_started|blocked_during_attempt> --continue-exit-evidence "<latest-attempt-proof>" --turn-exit-evidence "<forced-host-boundary-proof>"
```

Keep these handoff fields live and explicit:

- `current_or_next_stage`
- `remaining_required_stages`
- `goal_completion_status`
- `next_mandatory_action`
- `run_decision`
- `pause_reason`
- `resume_instructions`

Read the full field contract in
[closeout-and-resume.md](references/closeout-and-resume.md) and
[handoff-template.md](references/handoff-template.md) when editing `handoff.md`.

## Stage Loop

### 0. Ideation / Discovery

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
  dispatches, and do not inherit the five-lane halt or completion proof rule
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

### 1. Research

- Inspect the current target state before locking a plan. At minimum, record the
  source authority, existing run artifacts when resuming, relevant repo files,
  tests/configs, dirty-worktree constraints, runtime/tool availability, and any
  external systems the goal may touch.
- Consult official docs first when model, runtime, tool, MCP, Codex, or Claude
  behavior materially affects the plan. Record an `official_docs_decision`:
  `consulted` with refs, or `not_material` with a one-sentence rationale.
- Use the resolved strongest hard pin for Codex research/challenge lanes when
  delegated agents are available. A lane launched without explicit
  `model=<pin>` and `reasoning_effort=<pin>` is inadmissible.
- For each delegated research/challenge lane, preserve proof of the resolved
  model slug, reasoning effort, resolution basis, explicit spawn args, and the
  dispatch receipt. Missing or default/inherited model selection is inadmissible
  evidence, not a weaker-but-usable lane.
- Do not defer research/challenge lanes to ask whether agents may be opened;
  `$loop` already grants that delegation authority when the tool is available.
- Before research starts, record
  `capability_mode=delegated_agents_authorized_by_loop_<tool_available|tool_unavailable|tool_state_unknown>`.
  If delegated lanes are not useful for the current research uncertainty, record
  `delegated_research_not_material` with a short rationale. If they are useful
  but blocked, record the concrete runtime blocker, not a permission gap.
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

### 2. Plan

- Reconstruct the source into one authoritative `revised-plan.md`.
- Expand sequential objectives into explicit required stages.
- Keep the current stage bounded and execution-ready.
- Challenge the plan before execution.
- Treat source plans as evidence, not as final authority.

### 3. Execute

- Work one bounded stage at a time.
- Prefer the next concrete local action over recap.
- Keep worker scope narrow when delegation helps, and dispatch delegated
  workers without a separate permission check inside `$loop`.
- Preserve evidence with direct file refs, tests, logs, and diffs.
- Update `revised-plan.md`, `evidence.md`, and `handoff.md` as the live source
  of truth.

### 4. Verify And Reassess

- Run the smallest relevant validation for the changed area before claiming
  progress.
- Treat `apply_patch -> smallest relevant validation -> evidence/handoff
  refresh` as one atomic bounded batch. Do not leave a fresh local edit sitting
  between those steps and then blame a same-turn boundary for the pause shape.
- Re-research after each closed stage when the remaining plan may change.
- Continue into the next required stage whenever meaningful work remains.
- After each verified batch, immediately reopen the next cycle on the remaining
  highest-leverage gap unless fresh unanimous `5 Codex` halt/completion proof
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
- Default to `continue` whenever halt proof is missing, stale, ambiguous, or
  denied.

## Status Requests

When the user asks for the current state mid-run:

- Answer from live state, not from completion prose.
- Use the canonical live-state gate whenever a run directory already exists:

```bash
python <agent-loop-skill-dir>/scripts/emit_status_reply.py <run-dir> [--blocking-or-risk "..."]
```

- Keep the status reply inside short live-state fields such as:
  - `loop_state=...`
  - `current_or_next_stage=...`
  - `next_mandatory_action=...`
  - `blocking_or_risk=...` when needed
- Treat the status answer as commentary inside the active invocation; do not
  reinterpret it as permission to pause or stop.
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
2. If `run_decision=continue`, `goal_completion_status!=verified_complete_5agent`,
   or `remaining_required_stages` contains any work, do not emit a normal final
   answer. Continue with the next concrete tool-backed action.
3. If a visible turn end is unavoidable because the host forces it, first update
   the handoff with a fresh attempt receipt and host-boundary receipt, validate
   it, and emit only `closeout_gate.py` output.
4. If a previous turn violated this guard, treat the next user follow-up as an
   auto-resume/control-defect repair: document the root cause, patch the loop
   control text if needed, and continue the run. Do not ask whether to resume.

Before any unavoidable user-visible turn end:

1. Refresh `ideas.md`, `research.md`, `revised-plan.md`, and `handoff.md`
   before final proof starts; do not mutate `ideas.md` after proof dispatch.
2. Keep `handoff.md` canonical bullet-form v2 only.
3. Classify goal state correctly:
   - `not_reached`
   - `completion_candidate`
   - `verified_complete_5agent`
4. Run:

```bash
python <agent-loop-skill-dir>/scripts/validate_handoff.py <run-dir> --require-consensus
```

5. Emit the turn-ending reply only through:

```bash
python <agent-loop-skill-dir>/scripts/closeout_gate.py <run-dir> [--active-delta "..." --blocking-or-risk "..."]
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
  both fresh unanimous `5 Codex` halt proof and fresh unanimous `5 Codex`
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

A host-boundary turn end is bookkeeping, not semantic completion. Prefer the
live continue receipt when available; never make the user re-authorize the loop.

## Autonomous Stop Rules

- Do not emit autonomous `stop` without fresh unanimous `5 Codex` halt proof.
- Do not emit goal-satisfied autonomous `stop` without fresh unanimous `5 Codex`
  completion proof.
- The final five challenge agents must cover the required viewpoint set exactly
  once, with one agent assigned to one distinct perspective. Five `allow`
  votes from duplicate viewpoints, missing viewpoints, or generic challenge
  prompts are not unanimous five-agent proof.
- Bind both proofs to the current `subject_digest` for freshness and to
  `source_digest=<sha256(source.md)>` for original-prompt authority.
- Treat `subject_digest` as freshness binding only; it includes loop-local plan
  and evidence files and cannot prove that the original prompt was used as the
  completion scope.
- Treat any missing, ambiguous, stale, or denying lane as `continue`.
- Treat a timed-out completion lane as `continue-and-replace-now` when tools are
  still available in the same turn; do not let timeout alone justify a visible
  boundary or partial-consensus handoff.
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
- Modify the skill itself when the user asked to improve `$loop`; do not
  productize it inside the repo unless explicitly asked.

Use [project-adaptation.md](references/project-adaptation.md) when execution
lands inside a repository.

## High-Rigor References

These references are non-authoritative maintainer appendices. They may explain lower-level lifecycle or packet detail, but they do not add, widen, or override the public operator contract in `SKILL.md`.

Use the higher-rigor references only when the user explicitly asks for strict
packet/receipt behavior or when the environment actually provides durable
runtime support:

- `references/closeout-and-resume.md`
- `references/contracts-and-rules.md`
- `references/handoff-template.md`
- `references/ideas-template.md`
- `references/process-architecture.md`
- `references/profile-sync.md`
- `references/kernel-spec-stage1-3-draft.md`
- `references/kernel-spec-stage5-oracle-draft.md`
- `references/kernel-spec-stage6-packets-draft.md`
- `references/kernel-spec-stage7-packet-templates-draft.md`

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
