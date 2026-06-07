# Work-Type And Authority Contract

Use this reference whenever `$loop` handles non-code work, cross-project
resume, delegated challenge cycles, or terminal completion proof.

## Work Type

Keep `run_intent` separate from `work_type`.

Allowed `work_type` values:

- `implementation`
- `research`
- `docs`
- `planning`
- `review`
- `mixed`

For `review`, record `review_kind` as one of:

- `plan_review`
- `artifact_review`
- `completion_challenge`
- `audit`

`mixed` means an explicit stage graph. It is not permission to pick one
dominant artifact and ignore the remaining required stages.

## Completion Subjects

Terminal proof must bind to a typed `completion_subject`, not to a generic
"done" claim.

Allowed `completion_subject_type` values:

- `repo_diff`
- `document_artifact`
- `research_packet`
- `plan_artifact`
- `plan_review`
- `artifact_review`
- `completion_challenge`
- `audit_packet`
- `operation_record`
- `composite_subject`

If the subject is not `repo_diff` and no code artifact is explicitly in scope,
code-review-shaped findings, missing-test demands, commit/diff requirements,
and file-line bug reports are invalid output unless the referenced artifact
itself supports them.

`work_type` constrains the subject:

- `implementation` -> `repo_diff` or `operation_record`
- `research` -> `research_packet`
- `docs` -> `document_artifact`
- `planning` -> `plan_artifact`
- `review` -> the matching review subject type
- `mixed` -> `composite_subject`

For `mixed`, create a `composite_subject` that lists every required stage's
subject and digest. Every required stage must either produce a subject or
declare `included_in_subject=<composite-subject-ref>`.

## Artifact References

Use canonical artifact refs:

- `run://...`
- `repo://...`
- `file://...`
- `url://...`

Each required artifact ref must carry:

- base/root binding
- normalized path or URL
- digest algorithm and value
- encoding or content type when relevant
- captured timestamp
- missing behavior: `deny`, `warn_nonterminal`, or `optional`

`source_digest` means SHA-256 over the raw `source.md` bytes. Do not include
the path name, newline normalization, or any other prefix in this digest.

Terminal proof cannot depend on a missing required artifact.

## Run Authority

Create or update a `run_authority_record` for every authoritative run.

Required identity fields:

- `run_id`
- stable `project_root_ref`
- stable project identity digest
- VCS identity when present
- cwd/root binding
- `goal_digest`
- `source_digest`
- `stage_graph_digest`
- `status`
- `supersedes` / `superseded_by`
- schema and policy versions
- `authority_revision`
- `authority_epoch`
- last writer id

Valid statuses:

- `active`
- `superseded`
- `completed`
- `blocked`
- `quarantined`

Select a live run in this order:

1. Explicit resume command with matching authority record.
2. Current project registry active run matching project identity and
   `goal_digest`.
3. No implicit selection.

Duplicate active runs, moved projects without matching identity, stale
handoffs, mismatched goal digests, and incompatible versions are quarantine
candidates. Quarantined runs cannot provide terminal stop authority.

## Fencing And Freshness

Creation, supersession, quarantine, forced-boundary output, and terminal
completion must use CAS-style writes. The expected `authority_revision`,
`authority_epoch`, selected run id, status, and relevant digest set must still
match. CAS failure means reread and re-evaluate.

Before terminal output, the final validator must:

1. Reread the selected authority record.
2. Recompute source, subject, composite, and stage-graph digests from canonical
   artifact refs.
3. Re-run conformance and version checks.
4. Compare the current snapshot against the accepted current challenge cycle.

Reject terminal completion if the authority revision/epoch, status, selected
run id, stage graph, source digest, subject digest, composite digest,
schema/policy/prompt/validator versions, or adapter effective config digest
changed after the accepted challenge cycle dispatch.

Successful terminal completion is a CAS transition from `active` to
`completed` against the same revision/epoch/digest set. The authority record
for terminal completion must persist `cas_transition=active_to_completed`,
`cas_result=success`, and `cas_transition_ref` pointing at an in-run
`authority_transition_receipt_version=v1` receipt. That receipt must bind the
selected authority record, revision, epoch, pre/post status, pre-authority
digest, and current post-authority digest so validators reject self-reported
best-effort completion.

## Challenge Cycles

Before first plan lock, record delegated research as `research_cycle[]` when
`spawn_agent` is available. A valid `research-cycle-v1` records a concrete
`cycle_id`, source digest, authority revision/epoch at dispatch, exactly the
five required research lanes (`architecture_dependency`,
`failure_verification`, `goal_efficiency`, `requirement_alignment`, and
`implementation_quality`), in-run lane artifacts with
`agent_role=research_agent`, explicit `gpt-5.5` model args with exactly three
`xhigh` lanes and two `high` lanes, `model_resolution_basis_ref`, source
digest, authority revision/epoch at dispatch, resolvable
`spawn_tool_call_ref` dispatch receipts with their own
`model_resolution_basis_ref`,
`dispatch_receipt_version=v1`, `agent_role=research_agent`, the same
`research_cycle_id`, and `all_lanes_merged=true`.

Record delegated review as `challenge_cycle[]`.

If a run binds to a repository root containing `AGENTS.md`, terminal
halt/completion route metadata must include `AGENTS.md#LoopCompletionGate` and
the SHA-256 digest of that section in the same aggregate proof, lane artifacts,
and dispatch receipts. If no bound `AGENTS.md` exists, omit both the token and
digest together; never mix an `AGENTS.md` digest with a policy-ref list that
does not name the token.

Each cycle records:

- concrete `cycle_id`
- `challenge_cycle_schema_version=challenge-cycle-v1`
- reviewed plan/artifact/composite refs
- reviewed digest set, including `source_digest`, `stage_graph_digest`,
  `adapter_manifest_ref`, `adapter_effective_config_digest`,
  `completion_subject_type`, `completion_subject_ref`, and
  `completion_subject_digest`
- lane names and verdicts
- goal-completion lane artifact refs in `lanes`
- autonomous-halt lane artifact refs in `stop_lanes` when stop authority is
  being proven
- blocking findings
- required and resolved changes
- rerun scope
- schema/policy/prompt/validator versions
- `authority_revision_at_dispatch`
- `authority_epoch_at_dispatch`
- `all_lanes_allow`

Acceptance can use only one current cycle where every required lane reviewed
the exact same digest set under the same schema, policy, prompt, validator,
authority revision, and authority epoch.

For final halt/completion proof, the cycle lane set must exactly cover
`architecture_dependency`, `failure_verification`, `goal_efficiency`,
`requirement_alignment`, and `implementation_quality`. Each lane must reference
an in-run lane artifact with `vote=allow`, the same `cycle_id`, and a
resolvable dispatch receipt whose phase, challenge mode, agent role, viewpoint,
agent id, model args, authority revision/epoch, source digest, and cycle id
match the lane artifact. For terminal completion, `goal_completion_evidence
refs=` must exactly match `lanes`; when autonomous stop is allowed,
`stop_consensus_evidence refs=` must exactly match `stop_lanes`.

Prior ALLOWs, partial reruns, and mixed-version lane outputs cannot be
aggregated into acceptance. A same-version rerun is valid only for
tool/runtime unavailability or lane-output schema defects; otherwise the plan
or artifact digest must change.

## Project Adapters And Overrides

A project adapter manifest may declare repo/VCS presence, writable roots,
read-only roots, verification commands by work type, quota limits, dev-server
policy, artifact roots, supported subject types, local instructions, and
fallback behavior.

Projects without a manifest use an explicit conservative default adapter.
Absence of a manifest is never a permission expansion.

`agent_loop_override` is valid only for this allowlist:

- local verification command mapping
- artifact root aliases
- quota limits
- dev-server policy
- extra nonterminal evidence requirements
- project-specific subject validators
- stricter output constraints

Overrides may not alter work-type resolution, lane roles, verdict meanings,
final proof semantics, model policy, stop gates, challenge aggregation,
artifact digest rules, authority fencing, or visible-output contracts.

Merge precedence:

1. Global invariant
2. Release schema
3. Validated override
4. Adapter manifest default
5. Inferred project hint

Conflicts fail closed for terminal proof and require repair for nonterminal
work.

## Cross-Project Promotion

Every project-discovered rule must pass portability classification before it
can change global behavior.

Classes:

- `global_invariant`
- `project_adapter_rule`
- `project_local_hint`
- `rejected_local_hack`

Only `global_invariant` candidates can alter global loop semantics.
`project_adapter_rule` ships behind manifest/override validation.
`project_local_hint` remains advisory. `rejected_local_hack` cannot promote.

## Visible Output Contracts

Controller-visible and user-visible outputs must use a state contract:

- `live_status`
- `challenge_result`
- `forced_boundary_continue`
- `blocked_external_gate`
- `terminal_completion`

Nonterminal outputs include selected authority id, revision/epoch, work type,
subject type, current cycle id when present, and next mandatory action. They
must not claim completion.

Forced-boundary continuation is CAS-bound and must say the loop is not stopped,
the boundary is visible-only, the auto-resume trigger, the resume command, and
the next mandatory action.

Terminal output is allowed only after active authority, project conformance,
freshness validation, current-cycle aggregation, and CAS completion all pass.
Its shape must match the subject type.
