# Profile Sync

## Purpose

Profile sync is optional. Use it only when you intentionally maintain repo-local `$loop` support files that should refresh before a stage starts or before a new plan cycle starts.

It is not required for normal local-document mode.

## When It Is Useful

Use profile sync when all of these are true:

- `$loop` is operating against a repository
- that repository keeps loop-specific reference files
- you want those files refreshed before execution starts

Skip it when the operator is simply:

- feeding a local markdown note
- asking for plan reconstruction
- asking for challenge review
- stopping at the revised plan

## Suggested Repo-Local Files

- `.agents/agent-loop/profile.yaml` or `.agents/agent-loop/profile.json`
- `.agents/agent-loop/watch-map.yaml` or `.agents/agent-loop/watch-map.json`
- `.agents/agent-loop/profile.generated.md`
- `.agents/agent-loop/profile.lock.json`

Meaning:

- `profile.yaml` or `profile.json`
  Human-maintained repo-specific configuration.
- `watch-map.yaml` or `watch-map.json`
  Which files or directories should trigger regeneration.
- `profile.generated.md`
  Compact repo-specific execution brief.
- `profile.lock.json`
  The last applied hash snapshot and generation metadata.

## Execution-Time Preflight

Run this before `$loop` starts execution against a repo, before a new stage begins, or before a fresh plan cycle resumes:

1. Find the repo root.
2. Load `profile.yaml` or `profile.json`.
3. Load `watch-map.yaml` or `watch-map.json`.
4. Resolve watched files.
5. Hash the current watched files.
6. Compare hashes to `profile.lock.json`.
7. If nothing changed, keep the existing `profile.generated.md`.
8. If anything changed, regenerate `profile.generated.md`.
9. Validate the regenerated profile.
10. Update `profile.lock.json`.
11. Continue into repo execution.

## Cycle Boundary Rule

Do not replace profile assumptions in the middle of an active stage.

Apply refreshed profile data:

- before execution starts
- before a new stage starts
- before execution resumes
- at the next cycle boundary after a detected change

## What The Generated Profile Should Contain

Keep `profile.generated.md` compact and execution-focused:

- project contract summary
- source-of-truth paths
- verification commands
- repo-specific exceptions
- quality gate reminders

Do not dump whole source files into it.

## Validation

After regeneration, validate at least:

- required fields exist
- referenced paths still exist
- watched paths resolve correctly
- generated profile does not contradict the global `$loop` invariants
- generated profile is fresh relative to the lock snapshot
