# Project Adaptation

## Goal

Map the generic `$loop` automation into a host repository only when the revised plan actually needs to become code or project documentation.

The repository is the execution target, not the definition of the loop itself.

## When To Use This Reference

Use this file only when:

- the revised `$loop` plan is moving into implementation
- the work depends on repo contracts
- execution needs repo-local validation or commits

Do not use this file when the user only wants:

- local document intake
- plan reconstruction
- challenge review
- revised plan output

## Repo Handoff Checklist

### 1. Read the project contract

Identify the host repo's operating contract:

- `AGENTS.md`
- `CLAUDE.md`
- internal runbook
- platform-specific safety notes

Make every delegated agent inherit that contract.

### 2. Preserve the boundary

Keep these concepts separate:

- `$loop` automation
- repo implementation
- product command surfaces

If the user did not ask for a product command, do not invent one.

### 3. Map the revised plan into repo work

Translate the revised plan into repo-local execution terms:

- current stage
- target files
- parallel worker slices
- dependency edges
- quality gates
- verification commands
- commit boundary

Do not throw away the revised plan and restart from scratch.

### 4. Keep the main thread thin

- let the main CLI thread orchestrate
- keep worker context narrow
- integrate results back into the stage plan
- do not let the main thread absorb the full context of every subtask if bounded workers can carry it

### 5. Respect the dirty worktree

- preserve unrelated changes
- do not revert user work
- stop if conflicting dirty changes make the current path ambiguous

### 6. Keep execution stage-bounded

Even inside a repo, execute only the current stage.

Do not let a broad backlog note turn into broad code churn.

### 7. Verify before commit

When repo execution happens:

- run the planned checks
- collect direct evidence
- run three fresh verify challengers
- close blocking findings before commit

### 8. Commit at the stage boundary

When the current stage passes:

- commit that stage
- update the progress ledger
- revise the remaining stage queue

### 9. Re-research after every stage

After each verified stage commit:

- run fresh research
- search for better sequencing
- search for more efficient approaches
- search for higher-quality implementation opportunities tied to the same goal
- revise the remaining plan before starting the next stage

### 10. Productization is downstream

If the user later wants a product `/loop` or runtime embedding:

- treat that as a separate project
- define its command surface explicitly
- define its persistence and operator feedback explicitly
- do not confuse it with the personal `$loop` skill

## Fit Check

The adaptation is correct when:

- `$loop` still begins from local or pasted source material
- the revised plan still controls execution
- repo work is bounded by the current stage
- verified stages commit cleanly
- fresh research can still revise the remaining plan
- the repository did not become the source of truth for the loop itself
