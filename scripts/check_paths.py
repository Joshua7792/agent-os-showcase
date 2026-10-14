"""Check that every repo path referenced inside this repo resolves to a real file or folder.

What counts as a reference:
  - relative Markdown links: [text](path) in *.md (resolved against the linking file's folder)
  - `@file` imports in CLAUDE.md
  - backticked or quoted tokens that start with a repo top-level prefix (.claude/, tasks/, tools/, scripts/,
    .github/) or name a root file (AGENTS.md, CLAUDE.md, README.md, LICENSE, ...), in every text file
Tokens holding a placeholder or glob (<, >, *, {, }, $) are templates, not references, and are skipped, as are
Markdown links inside fenced code blocks (examples of other repos' layouts) and this script itself.
Exit 0 = every reference resolves; exit 1 = the broken ones are listed.

    python scripts/check_paths.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".md", ".sh", ".ps1", ".py", ".ts", ".tsx", ".json", ".yml", ".yaml", ".toml", ".txt", ".html"}
SKIP_DIRS = {".git", "node_modules", ".claude-plugin", "__pycache__", ".worktrees"}
PREFIXES = (".claude/", "tasks/", "tools/", "scripts/", ".github/")
ROOT_FILES = {"AGENTS.md", "CLAUDE.md", "README.md", "LICENSE", "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md",
              ".gitignore", ".gitleaks.toml"}
TEMPLATE = re.compile(r"[<>*{}$]")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
QUOTED = re.compile(r"[`'\"]([^`'\"\s]+)[`'\"]")
IMPORT = re.compile(r"^@(\S+)", re.M)
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
SELF = Path(__file__).resolve()


def files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*"):
        if (p.is_file() and p.suffix in TEXT and p.resolve() != SELF
                and not SKIP_DIRS.intersection(p.relative_to(ROOT).parts)):
            out.append(p)
    return sorted(out)


def exists(base: Path, ref: str) -> bool:
    ref = ref.split("#", 1)[0].rstrip("/")
    return bool(ref) and (base / ref).exists()


def check(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    bad: list[tuple[str, str]] = []
    if path.suffix == ".md":
        prose = FENCE.sub("", text)  # links inside fenced examples describe other repos
        for ref in MD_LINK.findall(prose):
            if re.match(r"^[a-z]+:", ref) or ref.startswith("#") or TEMPLATE.search(ref):
                continue
            if not exists(path.parent, ref):
                bad.append(("link", ref))
    if path.name == "CLAUDE.md":
        bad += [("import", ref) for ref in IMPORT.findall(text) if not exists(path.parent, ref)]
    for ref in QUOTED.findall(text):
        ref = ref.rstrip(".,;:)")
        if TEMPLATE.search(ref) or "://" in ref:
            continue
        if ref.startswith(PREFIXES) or ref in ROOT_FILES:
            if not exists(ROOT, ref):
                bad.append(("path", ref))
    return bad


def main() -> int:
    checked, broken = 0, 0
    for path in files():
        checked += 1
        for kind, ref in check(path):
            broken += 1
            print(f"BROKEN {kind:<6} {path.relative_to(ROOT).as_posix()}: {ref}")
    print(f"{checked} files checked, {broken} broken reference(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
