#!/usr/bin/env python3
"""Verify the published GitHub install coordinates in the README."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile

from public_release_manifest import OWNER, OWNER_REPO, REF, REPO, SKILL_PATH, URL


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def github_get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "codex-agent-loop-skill-verify"},
    )
    with urllib.request.urlopen(request) as response:
        return response.read()


def safe_extract(zip_file: zipfile.ZipFile, dest_dir: Path) -> None:
    dest_root = dest_dir.resolve()
    for info in zip_file.infolist():
        extracted_path = (dest_dir / info.filename).resolve()
        require(
            extracted_path == dest_root
            or str(extracted_path).startswith(str(dest_root) + os.sep),
            f"Archive entry escapes destination: {info.filename}",
        )
    zip_file.extractall(dest_dir)


def download_repo(ref: str) -> Path:
    payload = github_get(f"https://codeload.github.com/{OWNER}/{REPO}/zip/{ref}")
    tmp_dir = Path(tempfile.mkdtemp(prefix="agent-loop-public-install-"))
    with zipfile.ZipFile(BytesIO(payload)) as zip_file:
        safe_extract(zip_file, tmp_dir)
        top_levels = {name.split("/")[0] for name in zip_file.namelist() if name}
    require(len(top_levels) == 1, "Unexpected zip layout from GitHub codeload.")
    return tmp_dir / next(iter(top_levels))


def verify_installed_skill(repo_root: Path, skill_path: str) -> None:
    src = repo_root / skill_path
    require(src.is_dir(), f"Skill path missing in downloaded repo: {skill_path}")
    with tempfile.TemporaryDirectory(prefix="agent-loop-install-dest-") as tmp:
        dest = Path(tmp) / Path(skill_path).name
        shutil.copytree(src, dest)
        require((dest / "SKILL.md").is_file(), "Installed skill is missing SKILL.md")
        require((dest / "agents" / "openai.yaml").is_file(), "Installed skill is missing agents/openai.yaml")


def verify_repo_coordinates() -> None:
    repo_root = download_repo(REF)
    verify_installed_skill(repo_root, SKILL_PATH)


def verify_url_coordinates() -> None:
    parsed = urllib.parse.urlparse(URL)
    parts = [part for part in parsed.path.split("/") if part]
    require(parsed.scheme == "https", "Public URL must use https.")
    require(parsed.netloc == "github.com", "Public URL must target github.com.")
    require(parts[:2] == [OWNER, REPO], "Public URL owner/repo does not match manifest.")
    require(parts[2:4] == ["tree", REF], "Public URL ref does not match manifest.")
    require("/".join(parts[4:]) == SKILL_PATH, "Public URL skill path does not match manifest.")
    repo_root = download_repo(REF)
    verify_installed_skill(repo_root, SKILL_PATH)


def verify_readme_mentions() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(OWNER_REPO in readme, "README is missing the public owner/repo coordinate.")
    require(REF in readme, "README is missing the pinned public ref.")
    require(URL in readme, "README is missing the public GitHub URL install form.")


def main() -> int:
    verify_readme_mentions()
    verify_repo_coordinates()
    verify_url_coordinates()
    print("Public GitHub install coordinates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
