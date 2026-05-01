# ideas.md Template

Use this artifact as a bounded candidate queue before Research. `ideas.md` is
not evidence and is not scope authority.

## Ideation Gate

- `ideation_status`: `completed|not_material|reopened`
- `viewpoint_count`: `0|3|5`
- `cap`: `timebox_minutes=<n> candidate_limit=<n> external_source_limit=<n>`
- `skip_or_reopen_reason`: `<ideation_not_material|remaining_gap|new_constraint|higher_leverage_candidate|high_impact_ambiguous|none>`

Use `viewpoint_count=3` by default. Use `0` only with `ideation_not_material`. Use
`5` only for high-impact ambiguous goals where missed alternatives are plausibly
costly. For the default 3-viewpoint pass, use `repo-local alternatives`,
`outside patterns`, and `risk hypotheses`. Caps are total merged-output caps,
not per-viewpoint caps: default `timebox_minutes=5 candidate_limit=5
external_source_limit=3`; reassessment default `timebox_minutes=3
candidate_limit=3 external_source_limit=2`.

Legacy `lane_count` may appear in old run artifacts and is accepted as a
validator alias, but new artifacts should write `viewpoint_count`.

## Candidate Format

Each candidate must use a stable `idea_id`.

```md
### IDEA-001

- `idea_id`: `IDEA-001`
- `cycle_id`: `<cycle id>`
- `source_requirement_ref`: `<source.md requirement or active gap>`
- `idea`: `<candidate approach>`
- `source_or_inspiration`: `<short source description>`
- `source_type`: `<official_primary|source_code_or_runtime|vendor_docs|paper_or_standard|secondary_expert|community_anecdote|example_only|ai_memory|unverified_web_lead>`
- `source_quality`: `<strong|medium|weak|memory_only>`
- `provenance_ref`: `<URL/path/ref or none>`
- `accessed_at`: `<YYYY-MM-DD or none>`
- `memory_only`: `<true|false>`
- `why_it_might_matter`: `<possible plan impact>`
- `existence_question`: `<how Research verifies the outside reference exists>`
- `applicability_question`: `<how Research verifies fit for this repo/goal>`
- `validation_required`: `<official_docs|primary_source|runtime_evidence|repo_inspection|not_material>`
- `currency_risk`: `<low|medium|high>`
- `blocking`: `<false|true>`
- `pending_reason`: `<not_material|deferred|awaiting_research|none>`
- `last_reviewed_stage`: `<ideation|research|planning|reassessment>`
- `next_review_trigger`: `<active gap that can reopen this candidate, or none>`
- `research_status`: `<pending|validated|rejected|stale>`
- `research_ref`: `<research.md section or none>`
- `evidence_ref`: `<evidence/receipt ref or none>`
- `decision_date`: `<YYYY-MM-DD or none>`
- `decision_summary`: `<why validated/rejected/stale, or none>`
- `validated_against`: `<source_digest/research_digest/repo_snapshot or none>`
```

## Transition Rules

- `pending` must be `blocking=false` before Plan, unless moved into Research.
- `validated` may add or alter plan actions only with `research_ref` and
  `evidence_ref`.
- `rejected` may affect Plan only as a ruled-out constraint or non-action.
- `stale` must be revalidated before it can affect Plan again.
