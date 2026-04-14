# codex-agent-loop-skill

Public Codex skill repo for installing `agent-loop` with a one-line GitHub command.

## Install In Codex

Use the built-in GitHub skill installer and point it at the `agent-loop/` folder in this repo.

### Bash / zsh

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo kevin9899/codex-agent-loop-skill \
  --path agent-loop
```

### PowerShell

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo kevin9899/codex-agent-loop-skill `
  --path agent-loop
```

### GitHub URL Form

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --url https://github.com/kevin9899/codex-agent-loop-skill/tree/main/agent-loop
```

Restart Codex after install so the new skill is discovered.

## Repository Layout

- `agent-loop/`
  Installable Codex skill directory containing `SKILL.md`, `agents/openai.yaml`, and supporting references.

## Public Release Sanitization

This public split removes local-only references that should not ship in a public repo:

- personal local file examples
- absolute home-directory links
- local commit email exposure in new git history
