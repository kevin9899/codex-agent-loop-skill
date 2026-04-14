$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$tmpRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$env:CODEX_HOME = Join-Path $tmpRoot "codex-home"

$installerDir = Join-Path $env:CODEX_HOME "skills/.system/skill-installer/scripts"
New-Item -ItemType Directory -Force -Path $installerDir | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $installerDir "install-skill-from-github.py") | Out-Null

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$installerPath = Join-Path $codexHome "skills/.system/skill-installer/scripts/install-skill-from-github.py"
if (-not (Test-Path -LiteralPath $installerPath)) {
  throw "README PowerShell install-path expression does not resolve to the expected installer path."
}

$skillPath = Join-Path $codexHome "skills/agent-loop"
New-Item -ItemType Directory -Force -Path $skillPath | Out-Null
Remove-Item -LiteralPath $skillPath -Recurse -Force
if (Test-Path -LiteralPath $skillPath) {
  throw "README PowerShell update path failed to remove the installed skill directory."
}

Write-Output "Windows README path check passed."
