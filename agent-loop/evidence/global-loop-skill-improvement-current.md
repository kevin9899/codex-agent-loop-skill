# Global Loop Skill Improvement Evidence

- `scope`: `global_codex_skill`
- `target`: `<skill-dir>`
- `not_target`: `C:/Projects/study-platform production app`
- `batch_status`: `implementation_verified_waiting_for_fresh_5lane_allow`
- `challenge_policy`: `discard_any_round_with_any_DENY; do_not_reuse_old_ALLOWs`

## Owned Files

- `scripts/validate_handoff.py`
- `scripts/closeout_gate.py`
- `scripts/smoke_same_turn_blocked_continue.py`
- `scripts/smoke_worktype_subjects.py`
- `evidence/global-loop-skill-improvement-current.md`

## Unowned Moneta Worktree State

The following dirty files were observed under `C:/Projects/study-platform` by `git status --short` after the user said a pull changed code state. They are unrelated to this global skill batch and were not intentionally edited, staged, reverted, or used as this batch's implementation surface:

- `M src/app/api/hosted-generation/deck-create/route.ts`
- `M src/app/local/LocalDeckWorkbench.tsx`
- `M src/components/study/create-deck/CreateDeckBackgroundProgressCard.tsx`
- `M src/components/study/create-deck/background-progress.ts`
- `M src/components/study/create-deck/generation-request.ts`
- `M src/components/study/create-deck/use-create-deck-background-sync.ts`
- `M src/lib/deck-workspace/ai-run-receipts.ts`
- `M src/lib/deck-workspace/file-system-access.ts`
- `M tests/self-discovery/history/DedicatedHistoryContent.test.tsx`
- `M tests/unit/api/self-discovery-profile-route.test.ts`
- `M tests/unit/app/hosted-generation-route-create-import-paid-hosted-completion-authority-route-handler.test.ts`
- `M tests/unit/app/hosted-generation-route-create-import-paid-hosted-completion-evidence-route-handler.test.ts`
- `M tests/unit/app/hosted-generation-route-create-import-paid-hosted-generation-completion-authority-real-success-response-integration.test.ts`
- `M tests/unit/app/hosted-generation-route-create-import-paid-hosted-generation-completion-authority-runtime-adapter.test.ts`
- `M tests/unit/app/hosted-generation-route-create-import-route-completion-actual-completion-guard-runtime-adapter.test.ts`
- `M tests/unit/app/hosted-generation-route-job-provider-generated-deck-local-install-new-deck-create-import-free-local-plan-contract.test.ts`
- `M tests/unit/app/hosted-generation-route-job-provider-generated-deck-local-install-new-deck-create-import-route-local-file-write-authority-route-handler.test.ts`
- `M tests/unit/app/local-deck-workbench.test.tsx`
- `M tests/unit/app/local-install-commercial-entitlement-packaging-policy.test.ts`
- `M tests/unit/components/study/interaction-guide-cards.test.tsx`
- `M tests/unit/content/document-list.test.tsx`
- `M tests/unit/content/unified-dropzone.test.tsx`
- `M tests/unit/deck-contract/deck-workspace-ai-run-receipts.test.ts`
- `M tests/unit/deck-contract/deck-workspace-file-system-access.test.ts`
- `M tests/unit/study/card-dnd-sensors.test.tsx`
- `M tests/unit/study/create-deck-background-progress-card.test.tsx`
- `M tests/unit/study/create-deck-background-progress.test.ts`
- `M tests/unit/study/create-deck-generation-request.test.ts`
- `M tests/unit/study/create-deck-manual-form.test.tsx`
- `M tsconfig.build.json`
- `M tsconfig.json`
- `?? src/app/api/hosted-generation/deck-create/route-local-install-file-write-execution-evidence-resolver.ts`

## Verification

Latest local verification passed for the global skill batch:

```powershell
$base='<skill-dir>/scripts'
python -m py_compile "$base/validate_handoff.py" "$base/closeout_gate.py" "$base/canonicalize_handoff.py" "$base/refresh_legacy_handoffs.py" "$base/smoke_same_turn_blocked_continue.py" "$base/smoke_worktype_subjects.py" "$base/smoke_terminal_stop_briefing.py" "$base/smoke_plan_execution_stop_guard.py" "$base/smoke_explicit_user_stop.py" "$base/smoke_host_boundary_receipt.py" "$base/smoke_ideas_validation.py"
node --check "$base/run-claude-research.mjs"
python -B smoke_same_turn_blocked_continue.py
python -B smoke_worktype_subjects.py
python -B smoke_terminal_stop_briefing.py
python -B smoke_plan_execution_stop_guard.py
python -B smoke_explicit_user_stop.py
python -B smoke_host_boundary_receipt.py
python -B smoke_ideas_validation.py
```

Result:

- `[OK] same-turn blocked continue smoke passed`
- `[OK] worktype subject smoke passed`
- `[OK] terminal stop briefing smoke passed`
- `[OK] plan execution stop guard smoke passed`
- `[OK] explicit user stop smoke passed`
- `[OK] host-boundary receipt recorder smoke passed`
- `[OK] ideas validation smoke passed`

## Current Behavior Covered

- UI, Storybook, Korean UI, and documentation copy about quota/limits does not trigger resource telemetry or delegated quota closeout handling.
- Real delegated quota/resource blockers are detected across comma, colon, semicolon, pipe/list, newline, and common connector boundaries.
- Real same-segment quota exhaustion/reached/hit/exceeded wording such as `spawn_agent quota exhausted during challenge dispatch` requires telemetry.
- Real credit exhaustion wording such as `spawn_agent dispatch failed: credits exhausted` requires telemetry.
- Documentation/copy prefixes such as `docs: spawn_agent quota limit reached`, `Korean copy: 에이전트 사용량 한도`, and `한국어 문구: 에이전트 사용량 한도` do not trigger blocker handling.
- Documentation/copy prefixes suppress only the labeled example segment when introduced by `:`, `=`, or a spaced `-`, so `docs: spawn_agent quota limit reached; delegated dispatch blocked by quota` still triggers telemetry and delegated quota handling for the later real blocker.
- Semicolon and newline boundaries after a standalone docs/copy word are not treated as label prefixes, so `docs; delegated dispatch blocked by quota` and `docs\ndelegated dispatch blocked by quota` still trigger real blocker handling.
- Benign retry wording such as `agent will try again after review` does not trigger delegated quota handling.
- Parsed list items are evaluated independently, so copy context in one item cannot suppress a real blocker in another item.
- Adjacent actor/failure and quota-condition segments are detected in both directions.
- Negated quota/usage/rate/tool-limit wording, including `not reached`, `wasn't/weren't reached`, `has not been reached`, `haven't been reached`, and `ruled out`, does not trigger blocker handling.
- `closeout_gate.py` delegates quota pause detection through the shared validator classifier to avoid drift.
- Subject digest redacts indented proof-evidence payloads but still hashes unrelated unindented handoff text after a proof field.
