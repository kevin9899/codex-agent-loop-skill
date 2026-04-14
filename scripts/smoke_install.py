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
    print("Smoke install passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
