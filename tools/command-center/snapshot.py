"""Command Center snapshot.

Reads every project's todo.md "Resume here" block and tasks/lessons.md, and writes the two documents the
Command Center artifact shows: `snapshot.json` (outcome cards + improve loop) and `inbox.json` (items that
need Joshua). Read-only on the repo; stdlib only. A Claude session pushes the two documents to the
`dashboard.html` artifact's database (docs `cc/snapshot` and `cc/inbox`); projects are listed in projects.json.

    uv run --no-project python tools/command-center/snapshot.py [--out DIR]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name("projects.json")
DEFAULT_OUT = Path.home() / ".command-center"
STALE_DAYS = 14
TEXT_CAP = 320

CHECK = re.compile(r"^\s*[-*]\s+\[([ ~xX])\]\s*(.*)")
LABELLED = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*(.*)")
DATE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
ASK = re.compile(
    r"awaiting Joshua|waiting (?:on|for) Joshua|Joshua'?s (?:approval|review|decision|OK|call|check)\b"
    r"|^Joshua:|\bJoshua (?:updates|sends|checks|reviews|picks|decides|approves|signs|types|runs)\b",
    re.I,
)
# A checklist item is an ask only when it says so outright; "→ Joshua review" on a future roadmap stage is not.
ASK_ITEM = re.compile(r"^Joshua:|awaiting Joshua|waiting (?:on|for) Joshua", re.I)
DECISION = re.compile(r"\b(OK|approv\w*|decid\w*|decision|call|pick|choose|go/no-go|review)\b", re.I)
BLOCKER = re.compile(r"\b(blocked|until|only after|no live)\b", re.I)
SECRET = re.compile(r"\b(PK[A-Z0-9]{16,}|sk-[A-Za-z0-9_-]{20,}|vck_[A-Za-z0-9]{8,}|apik\w{8,})")

NEXT_KEYS = ("next", "next step", "next phase")
WHERE_KEYS = ("where", "stopped at", "status", "state")
NEEDS_KEYS = ("needs joshua", "waiting on joshua", "joshua")
BEFORE_KEYS = ("before starting", "before heavy gates", "blocked", "blockers", "blocker")


def plain(text: str) -> str:
    """Markdown → plain text the page renders as text; backticks are kept for <code> spans."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = SECRET.sub("[redacted]", text)
    return re.sub(r"\s+", " ", text).strip()


def clean(text: str) -> str:
    text = plain(text)
    return text if len(text) <= TEXT_CAP else text[: TEXT_CAP - 1].rstrip() + "…"


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z`(])", plain(text)) if s.strip()]


def resume_block(lines: list[str]) -> tuple[int, list[str]] | None:
    """Return (1-based heading line, body lines) of the first `## … Resume here …` section."""
    for i, line in enumerate(lines):
        if re.match(r"^#{1,3}\s.*resume here", line, re.I):
            body = []
            for nxt in lines[i + 1:]:
                if re.match(r"^#{1,3}\s", nxt):
                    break
                body.append(nxt)
            return i + 1, body
    return None


def parse_resume(start: int, body: list[str], heading: str = "") -> dict:
    """Labelled bullets (`- **Next:** …`, continuation lines joined) and the prose around them."""
    fields: list[tuple[str, str, int]] = []
    prose: list[tuple[str, int]] = []
    for offset, raw in enumerate(body, start=start + 1):
        if not raw.strip():
            continue
        m = LABELLED.match(raw)
        if m:
            label, rest = m.group(1).strip(), m.group(2)
            if label.endswith(":") or rest.lstrip().startswith(":"):
                fields.append((label.rstrip(":").lower(), rest.lstrip().lstrip(":"), offset))
            else:  # "**Next phase = S2 wave A** (…)": the bold text is part of the sentence
                fields.append((re.split(r"\s*[=—]\s*", label)[0].lower(), f"{label}{rest}", offset))
        elif re.match(r"^\s{2,}\S", raw) and fields and not CHECK.match(raw):
            key, text, line = fields[-1]
            fields[-1] = (key, f"{text} {raw.strip()}", line)
        elif not CHECK.match(raw):
            prose.append((raw, offset))

    def first(keys: tuple[str, ...]) -> tuple[str, int] | None:
        for key, text, line in fields:
            if key in keys or any(key.startswith(k) for k in keys):
                return clean(text), line
        return None

    prose_sents = [(clean(s), line) for raw, line in prose for s in sentences(raw)]
    where = first(WHERE_KEYS) or (prose_sents[0] if prose_sents else None)
    nxt = first(NEXT_KEYS) or next(((s, l) for s, l in prose_sents if re.match(r"next\b", s, re.I)), None) or next(
        ((s, l) for s, l in prose_sents
         if (s, l) != where and re.search(r"\b(next|waiting for|awaiting|before)\b", s, re.I)), None)
    blockers = [(clean(t), l) for k, t, l in fields if any(k.startswith(b) for b in BEFORE_KEYS)]
    blockers += [(s, l) for s, l in prose_sents if BLOCKER.search(s) and (s, l) != where and (s, l) != nxt]
    needs = [(clean(t), l) for k, t, l in fields if any(k.startswith(n) for n in NEEDS_KEYS)]
    updated = re.search(r"updated\s+(20\d\d-\d\d-\d\d)", heading, re.I)
    dates = [updated.group(1)] if updated else [
        d for d in DATE.findall(" ".join(body)) if d <= dt.date.today().isoformat()]
    return {
        "where": where[0] if where else None,
        "next": nxt[0] if nxt else None,
        "blockers": [b for b, _ in blockers[:4]],
        "_needs": needs,
        "_asks": [(s, l) for s, l in prose_sents if ASK.search(s)] + [
            (clean(s), l) for k, t, l in fields if not any(k.startswith(n) for n in NEEDS_KEYS)
            for s in sentences(t) if ASK.search(s)],
        "dated": max(dates) if dates else None,
    }


def item_id(project: str, text: str) -> str:
    norm = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha1(f"{project}|{norm}".encode()).hexdigest()[:12]


def project_status(proj: dict, today: dt.date) -> tuple[dict, list[dict]]:
    path = ROOT / proj["file"]
    out = {k: proj.get(k) for k in ("id", "label", "outcome", "file")}
    out["unassigned"] = proj.get("unassigned", False)
    if not path.is_file():
        out.update(state="missing", note="Status file not found")
        return out, []
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    lines = text.split("\n")
    saved = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    title = next((clean(l.lstrip("# ")) for l in lines if l.startswith("# ")), proj["label"])
    checks = [(m.group(1), clean(m.group(2)), n) for n, l in enumerate(lines, 1) if (m := CHECK.match(l))]
    open_items = [(t, n) for mark, t, n in checks if mark in " ~"]
    out.update(
        title=title,
        savedAt=saved.isoformat(timespec="seconds"),
        ageDays=(today - saved.date()).days,
        done=sum(1 for mark, _, _ in checks if mark in "xX"),
        open=len(open_items),
    )

    asks: list[tuple[str, int]] = []
    block = resume_block(lines)
    if block:
        res = parse_resume(*block, heading=lines[block[0] - 1])
        out.update(resume=True, resumeLine=block[0], where=res["where"], next=res["next"],
                   blockers=res["blockers"], dated=res["dated"])
        for text_, line in res["_needs"]:
            asks += [(clean(p), line) for p in re.split(r"\s+·\s+", text_) if p.strip()]
        asks += res["_asks"]
    else:
        out.update(resume=False, where=None, blockers=[], dated=None,
                   next=open_items[0][0] if open_items else None)
    asks += [(t, n) for t, n in open_items if ASK_ITEM.search(t)]

    items, seen = [], set()
    for text_, line in asks:
        iid = item_id(proj["id"], text_)
        if iid in seen:
            continue
        seen.add(iid)
        items.append({
            "id": iid, "text": text_, "kind": "decision" if DECISION.search(text_) else "action",
            "project": proj["id"], "projectLabel": proj["label"], "outcome": proj["outcome"],
            "file": proj["file"], "line": line,
        })

    if items:
        state = "waiting"
    elif not block and not checks:
        state = "unknown"
    elif not open_items and not out.get("next"):
        state = "done"
    elif out["ageDays"] > STALE_DAYS:
        state = "stale"
    else:
        state = "active"
    out.update(state=state, asks=len(items))
    return out, items


def discover(config: dict) -> list[dict]:
    """Configured projects, plus any root tasks/<x>/todo.md not yet given an outcome."""
    projects = list(config["projects"])
    known = {str((ROOT / p["file"]).resolve()).lower() for p in projects}
    for path in sorted((ROOT / "tasks").glob("*/todo.md")):
        if str(path.resolve()).lower() not in known:
            name = path.parent.name
            projects.append({"id": name, "label": name, "outcome": "O4", "unassigned": True,
                             "file": path.relative_to(ROOT).as_posix()})
    return projects


def iso_week(day: dt.date) -> str:
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def lessons(today: dt.date) -> dict:
    path = ROOT / "tasks" / "lessons.md"
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    entries = []
    for m in re.finditer(r"^## (20\d\d-\d\d-\d\d)\s+[—-]+\s+(.+)$", text, re.M):
        end = text.find("\n## ", m.end())
        entries.append({"date": m.group(1), "title": clean(m.group(2)),
                        "body": text[m.end(): end if end > 0 else len(text)]})

    skills = skills_added()
    for s in skills:
        hit = next((e for e in reversed(entries) if f"`{s['name']}`" in e["body"]), None)
        s["lesson"] = hit["title"] if hit else None

    weeks, monday = [], today - dt.timedelta(days=today.weekday())
    for back in range(11, -1, -1):
        start = monday - dt.timedelta(weeks=back)
        key = iso_week(start)
        weeks.append({
            "week": key, "start": start.isoformat(),
            "lessons": sum(1 for e in entries if iso_week(dt.date.fromisoformat(e["date"])) == key),
            "skills": sum(1 for s in skills if not s["baseline"] and s["date"]
                          and iso_week(dt.date.fromisoformat(s["date"])) == key),
        })
    return {
        "total": len(entries),
        "weeks": weeks,
        "newest": [{"date": e["date"], "title": e["title"]} for e in entries[::-1][:6]],
        "skills": [s for s in skills if not s["baseline"]][:12],
        "skillsTotal": len(skills),
        "skillsBaseline": sum(1 for s in skills if s["baseline"]),
        "baselineDate": next((s["date"] for s in skills if s["baseline"]), None),
    }


def skills_added() -> list[dict]:
    """First commit date of each .claude/skills/<name>/SKILL.md; uncommitted ones by save date."""
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                                  encoding="utf-8", timeout=30, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            return ""

    first: dict[str, str] = {}
    date = None
    log = git("log", "--diff-filter=A", "--format=@@%ad", "--date=short", "--name-only", "--",
              ".claude/skills/*/SKILL.md")
    for line in log.splitlines():
        if line.startswith("@@"):
            date = line[2:]
        elif line.strip() and date:
            first[line.split("/")[2]] = date  # log is newest first, so the oldest add wins
    baseline = min(first.values()) if first else None
    out = [{"name": n, "date": d, "baseline": d == baseline, "committed": True} for n, d in first.items()]
    for line in git("status", "--porcelain", "--", ".claude/skills").splitlines():
        if line.startswith("?? "):
            skill_md = ROOT / line[3:].strip().strip('"') / "SKILL.md"
            if skill_md.is_file():
                saved = dt.date.fromtimestamp(skill_md.stat().st_mtime).isoformat()
                out.append({"name": skill_md.parent.name, "date": saved, "baseline": False, "committed": False})
    return sorted(out, key=lambda s: (s["date"] or "", s["name"]), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    today = dt.date.today()
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    projects, inbox = [], []
    for proj in discover(config):
        status, items = project_status(proj, today)
        projects.append(status)
        inbox += items

    outcomes = []
    for oc in config["outcomes"]:
        mine = [p for p in projects if p["outcome"] == oc["id"]]
        primary = next((p for p in mine if any(c["id"] == p["id"] and c.get("primary") for c in config["projects"])),
                       mine[0] if mine else None)
        outcomes.append({**oc, "state": primary["state"] if primary else "unknown",
                         "primary": primary["id"] if primary else None,
                         "asks": sum(p.get("asks", 0) for p in mine),
                         "projects": [p["id"] for p in mine]})

    snapshot = {"generatedAt": now, "outcomes": outcomes, "projects": projects, "lessons": lessons(today)}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "snapshot.json").write_text(json.dumps(snapshot, indent=1, ensure_ascii=False), encoding="utf-8")
    (args.out / "inbox.json").write_text(json.dumps({"generatedAt": now, "items": inbox}, indent=1,
                                                    ensure_ascii=False), encoding="utf-8")
    print(f"{len(projects)} projects · {len(inbox)} inbox items · {snapshot['lessons']['total']} lessons → {args.out}")
    for p in projects:
        print(f"  {p['outcome']} {p['state']:<8} {p['label']:<24} asks={p.get('asks', 0)} next={(p.get('next') or '—')[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
