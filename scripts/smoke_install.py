#!/usr/bin/env python3
"""Smoke-test that the published skill directory is installable by copy."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agent-loop"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="agent-loop-smoke-") as tmp:
        dest = Path(tmp) / "agent-loop"
        shutil.copytree(SRC, dest)
        assert (dest / "SKILL.md").is_file()
        assert (dest / "agents" / "openai.yaml").is_file()
        assert (dest / "references").is_dir()
        for required_ref in (
            "process-architecture.md",
            "contracts-and-rules.md",
            "kernel-spec-stage1-3-draft.md",
            "kernel-spec-stage5-oracle-draft.md",
            "kernel-spec-stage6-packets-draft.md",
            "kernel-spec-stage7-packet-templates-draft.md",
            "project-adaptation.md",
            "profile-sync.md",
        ):
            assert (dest / "references" / required_ref).is_file()
    print("Smoke install passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
