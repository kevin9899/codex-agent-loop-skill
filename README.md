# codex-agent-loop-skill

Public GitHub repo for installing the `agent-loop` Codex skill.

한국어 문서는 [README.ko.md](./README.ko.md)를 참고하세요.

## What This Is

`agent-loop` is a Codex-side orchestration skill for turning a local note, path, markdown link, or rough goal into a disciplined software-improvement loop.

- It reads the local source material first.
- It runs research, builds a staged plan, challenges that plan, executes one bounded stage, verifies it, and reassesses what to do next.
- It is not a product feature, SDK, or repo runtime command. It is an operator workflow for Codex itself.

## Before You Install

`agent-loop` is not a generic prompt-only skill. It requires a Codex runtime that supports:

- delegated `spawn_agent` calls
- explicit `model` and `reasoning_effort` fields on delegated calls

If your runtime cannot satisfy those requirements, installation may succeed but the workflow itself is unsupported.

## Install In Codex

The recommended install path is a pinned Git ref instead of floating `main`.

### Bash / zsh

```bash
REF=v0.1.3
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo kevin9899/codex-agent-loop-skill \
  --ref "$REF" \
  --path agent-loop
```

### PowerShell

```powershell
$ref = "v0.1.3"
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-installer/scripts/install-skill-from-github.py") `
  --repo kevin9899/codex-agent-loop-skill `
  --ref $ref `
  --path agent-loop
```

### GitHub URL Form

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --url https://github.com/kevin9899/codex-agent-loop-skill/tree/v0.1.3/agent-loop
```

### Manual Copy Fallback

If you do not want to use the installer helper, download or clone the pinned tag, then copy the `agent-loop/` directory into `$CODEX_HOME/skills/agent-loop` and restart Codex.

Restart Codex after install so the new skill is discovered.

## First Run

Use this once after restart to distinguish a healthy install from an unsupported runtime.

1. Create a small local markdown note such as `agent-loop-smoke.md`.
2. Run one of these in Codex:

```text
$loop C:\Projects\notes\agent-loop-smoke.md
$loop [Plan](./docs/plan.md:12)
```
3. Expected result:
   Codex reads the source, resolves one strongest-model pin, and opens three research lanes before planning.
4. Unsupported-runtime signal:
   If Codex reports missing `spawn_agent` support or cannot send explicit `model` and `reasoning_effort` fields, the runtime is not compatible with this skill.

## Latest Snapshot

If you intentionally want the newest unpinned snapshot, replace the ref with `main`. That is less stable and not the recommended support path.

## Update An Existing Install

The installer will not overwrite an existing destination. Remove the existing skill folder first, then reinstall the pinned version.

### Bash / zsh

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/agent-loop"
```

### PowerShell

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
Remove-Item -LiteralPath (Join-Path $codexHome "skills/agent-loop") -Recurse -Force
```

## What Is Authoritative

- `agent-loop/SKILL.md`
  The public operator contract for this skill.
- `agent-loop/references/*.md`
  Supporting design references published for transparency. Some files intentionally keep `*-draft.md` names because they are deeper design appendices, not the primary public contract.

These references are non-authoritative maintainer appendices. They may explain lower-level lifecycle or packet detail, but they do not add, widen, or override the public operator contract in `SKILL.md`.

If a supporting reference and `SKILL.md` ever differ, follow `SKILL.md`.

## Release Checks

This repo includes public-release checks for repo shape, local installability, published GitHub install coordinates, and the documented Windows path/update flow:

```bash
python scripts/validate_public_repo.py
python scripts/smoke_install.py
python scripts/verify_public_install_paths.py
```

GitHub Actions runs the same checks on Linux and Windows.

## License

This repo is released under the MIT License. See [LICENSE](./LICENSE).
