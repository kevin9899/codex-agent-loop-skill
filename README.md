# codex-agent-loop-skill

Public GitHub repo for installing the `agent-loop` Codex skill.

## Compatibility

`agent-loop` is not a generic prompt-only skill. It requires a Codex runtime that supports:

- delegated `spawn_agent` calls
- explicit `model` and `reasoning_effort` fields on delegated calls

If your runtime cannot satisfy those requirements, installation may succeed but the workflow itself is unsupported.

## Install In Codex

The recommended install path is a pinned Git ref instead of floating `main`.

### Bash / zsh

```bash
REF=v0.1.0
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo kevin9899/codex-agent-loop-skill \
  --ref "$REF" \
  --path agent-loop
```

### PowerShell

```powershell
$ref = "v0.1.0"
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-installer/scripts/install-skill-from-github.py") `
  --repo kevin9899/codex-agent-loop-skill `
  --ref $ref `
  --path agent-loop
```

### GitHub URL Form

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --url https://github.com/kevin9899/codex-agent-loop-skill/tree/v0.1.0/agent-loop
```

Restart Codex after install so the new skill is discovered.

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

If a supporting reference and `SKILL.md` ever differ, follow `SKILL.md`.

## Release Checks

This repo includes lightweight public-release checks:

```bash
python scripts/validate_public_repo.py
python scripts/smoke_install.py
```

GitHub Actions runs the same checks on pushes and pull requests.

## License

This repo is released under the MIT License. See [LICENSE](./LICENSE).
