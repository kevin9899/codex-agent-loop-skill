#!/usr/bin/env python3
"""Validate the public release shape of the repo."""

from __future__ import annotations

from pathlib import Path
import re

from public_release_manifest import OWNER_REPO, REF, SKILL_PATH, URL


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_BANNER = (
    "These references are non-authoritative maintainer appendices. "
    "They may explain lower-level lifecycle or packet detail, but they do not add, widen, or override the public operator contract in `SKILL.md`."
)
REQUIRED_FILES = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "agent-loop" / "SKILL.md",
    ROOT / "agent-loop" / "agents" / "openai.yaml",
]
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml"}
BANNED_PATTERNS = [
    r"C:/Users/",
    r"\\Users\\",
    r"Obsidian",
    r"gho_[A-Za-z0-9_]+",
    r"ghp_[A-Za-z0-9_]+",
    r"github_pat_[A-Za-z0-9_]+",
    r"BEGIN [A-Z ]+PRIVATE KEY",
    r"Authorization: Bearer",
    r"PAPERCLIP_API_KEY",
    r"PAPERCLIP_RUN_ID",
    r"PAPERCLIP_API_URL",
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_required_files() -> None:
    for path in REQUIRED_FILES:
        require(path.exists(), f"Missing required file: {path.relative_to(ROOT)}")


def validate_skill_frontmatter() -> None:
    skill_md = read_text(ROOT / "agent-loop" / "SKILL.md")
    match = FRONTMATTER_RE.match(skill_md)
    require(match is not None, "SKILL.md is missing YAML frontmatter.")
    frontmatter = match.group(1)
    require(
        re.search(r"(?m)^name:\s*agent-loop\s*$", frontmatter) is not None,
        "SKILL.md frontmatter is missing name.",
    )
    require(
        re.search(r"(?m)^description:\s*.+$", frontmatter) is not None,
        "SKILL.md frontmatter is missing description.",
    )


def validate_openai_yaml() -> None:
    openai_yaml = read_text(ROOT / "agent-loop" / "agents" / "openai.yaml")
    for key in ("display_name:", "short_description:", "default_prompt:"):
        require(key in openai_yaml, f"agents/openai.yaml is missing {key}")


def validate_readme_contract() -> None:
    readme = read_text(ROOT / "README.md")
    require("spawn_agent" in readme, "README.md must document spawn_agent compatibility.")
    require("--ref" in readme, "README.md must include a pinned --ref install example.")
    require("SKILL.md" in readme, "README.md must state the public authority surface.")
    require("First Run" in readme, "README.md must include a post-install smoke test.")
    require("$loop" in readme, "README.md must include a concrete $loop usage example.")
    require("Manual Copy Fallback" in readme, "README.md must include a manual copy install fallback.")
    require(OWNER_REPO in readme, "README.md must include the public owner/repo coordinate.")
    require(REF in readme, "README.md must include the pinned release ref.")
    require(URL in readme, "README.md must include the public GitHub URL install form.")
    require(SKILL_PATH in readme, "README.md must include the public skill path.")
    require(AUTHORITY_BANNER in readme, "README.md must include the non-authoritative appendix banner.")


def validate_skill_reference_files() -> None:
    skill_md = read_text(ROOT / "agent-loop" / "SKILL.md")
    require(AUTHORITY_BANNER in skill_md, "SKILL.md must include the non-authoritative appendix banner.")
    refs = sorted(
        {
            ref
            for ref in re.findall(r"`(references/[^`]+\.md)`", skill_md)
            if "*" not in ref
        }
    )
    require(refs, "SKILL.md must mention the bundled reference appendices.")
    for ref in refs:
        require((ROOT / "agent-loop" / ref).is_file(), f"SKILL.md references a missing file: {ref}")
    for draft_name in (
        "kernel-spec-stage1-3-draft.md",
        "kernel-spec-stage5-oracle-draft.md",
        "kernel-spec-stage6-packets-draft.md",
        "kernel-spec-stage7-packet-templates-draft.md",
    ):
        draft_text = read_text(ROOT / "agent-loop" / "references" / draft_name)
        require(
            AUTHORITY_BANNER in draft_text,
            f"{draft_name} must include the non-authoritative appendix banner.",
        )


def validate_banned_patterns() -> None:
    for path in iter_text_files():
        if path.resolve() == Path(__file__).resolve():
            continue
        text = read_text(path)
        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text):
                raise SystemExit(
                    f"Banned public pattern matched in {path.relative_to(ROOT)}: {pattern}"
                )


def validate_relative_links() -> None:
    for path in iter_text_files():
        text = FENCED_CODE_RE.sub("", read_text(path))
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split(":", 1)[0] if ".md:" in target else target
            target = target.split("#", 1)[0]
            if not target or target.startswith("file://"):
                continue
            resolved = (path.parent / target).resolve()
            require(resolved.exists(), f"Broken relative link in {path.relative_to(ROOT)}: {raw_target}")


def main() -> int:
    validate_required_files()
    validate_skill_frontmatter()
    validate_openai_yaml()
    validate_readme_contract()
    validate_skill_reference_files()
    validate_banned_patterns()
    validate_relative_links()
    print("Public repo validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
