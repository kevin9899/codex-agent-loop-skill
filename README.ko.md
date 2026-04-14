# codex-agent-loop-skill

`agent-loop` Codex 스킬을 설치하기 위한 공개 GitHub 저장소입니다.

영문 문서는 [README.md](./README.md)를 참고하세요.

## 설치 전 확인

`agent-loop`는 단순 프롬프트 스킬이 아닙니다. 다음 기능을 지원하는 Codex 런타임이 필요합니다.

- 위임형 `spawn_agent` 호출
- 위임 호출에서 명시적인 `model` 및 `reasoning_effort` 필드

이 조건을 만족하지 않으면 설치는 되더라도 실제 워크플로는 지원되지 않습니다.

## Codex에 설치하기

권장 설치 방식은 떠다니는 `main`이 아니라 고정된 Git ref를 사용하는 것입니다.

### Bash / zsh

```bash
REF=v0.1.2
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo kevin9899/codex-agent-loop-skill \
  --ref "$REF" \
  --path agent-loop
```

### PowerShell

```powershell
$ref = "v0.1.2"
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-installer/scripts/install-skill-from-github.py") `
  --repo kevin9899/codex-agent-loop-skill `
  --ref $ref `
  --path agent-loop
```

### GitHub URL 방식

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --url https://github.com/kevin9899/codex-agent-loop-skill/tree/v0.1.2/agent-loop
```

### 수동 복사 대안

설치 도우미 스크립트를 쓰고 싶지 않다면, 고정 태그를 다운로드하거나 clone한 뒤 `agent-loop/` 디렉터리를 `$CODEX_HOME/skills/agent-loop`로 복사하고 Codex를 재시작하세요.

설치 후에는 새 스킬을 인식할 수 있도록 Codex를 재시작하세요.

## 첫 실행

재시작 후 한 번 아래 절차를 써서 정상 설치인지, 아니면 지원되지 않는 런타임인지 구분할 수 있습니다.

1. `agent-loop-smoke.md` 같은 작은 로컬 마크다운 파일을 하나 만듭니다.
2. Codex에서 아래 중 하나를 실행합니다.

```text
$loop C:\Projects\notes\agent-loop-smoke.md
$loop [Plan](./docs/plan.md:12)
```

3. 기대 결과:
   Codex가 소스를 읽고 strongest-model pin 하나를 확정한 뒤, 계획 전에 세 개의 research lane을 엽니다.
4. 미지원 런타임 신호:
   Codex가 `spawn_agent` 지원 부족을 보고하거나 명시적인 `model`, `reasoning_effort` 필드를 보낼 수 없다고 나오면 이 스킬과 호환되지 않는 런타임입니다.

## 최신 스냅샷

일부러 최신 비고정 스냅샷을 쓰고 싶다면 ref를 `main`으로 바꾸면 됩니다. 다만 안정성은 떨어지고 권장 지원 경로도 아닙니다.

## 기존 설치 업데이트

공식 설치 스크립트는 기존 대상 디렉터리를 덮어쓰지 않습니다. 기존 스킬 폴더를 먼저 지운 뒤 고정 버전을 다시 설치하세요.

### Bash / zsh

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/agent-loop"
```

### PowerShell

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
Remove-Item -LiteralPath (Join-Path $codexHome "skills/agent-loop") -Recurse -Force
```

## 무엇이 기준 문서인가

- `agent-loop/SKILL.md`
  이 스킬의 공개 운영 계약 문서입니다.
- `agent-loop/references/*.md`
  투명성을 위해 공개한 보조 설계 문서입니다. 일부 파일이 `*-draft.md` 이름을 유지하는 이유는, 이것들이 1차 공개 계약이 아니라 더 깊은 설계 부록이기 때문입니다.

이 문서들은 maintainer용 비권위 부록입니다. 더 낮은 수준의 lifecycle이나 packet 세부를 설명할 수는 있지만, `SKILL.md`의 공개 운영 계약을 추가, 확장, 덮어쓰지 않습니다.

보조 문서와 `SKILL.md`가 다르면 `SKILL.md`를 따르세요.

## 릴리스 검증

이 저장소에는 저장소 형태, 로컬 설치 가능성, 공개 GitHub 설치 좌표, 문서화된 Windows 경로/업데이트 흐름을 확인하는 공개 릴리스 검증이 들어 있습니다.

```bash
python scripts/validate_public_repo.py
python scripts/smoke_install.py
python scripts/verify_public_install_paths.py
```

GitHub Actions는 Linux와 Windows에서 같은 검증을 실행합니다.

## 라이선스

이 저장소는 MIT License로 배포됩니다. 자세한 내용은 [LICENSE](./LICENSE)를 참고하세요.
