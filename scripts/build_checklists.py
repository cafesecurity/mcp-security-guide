#!/usr/bin/env python3
"""Build checklists/ from the '## Checklist' section of each guide page.

Run from the repository root: python3 scripts/build_checklists.py
CI runs it with --check and fails if checklists/ is out of date.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE = ROOT / "guide"
OUT = ROOT / "checklists"
PAGES = sorted(GUIDE.glob("0*.md")) + [GUIDE / "coding-agents.md"]
SCORECARD = """
## Scorecard (one per agent that will hold this server)

| Server or tool | [A] Reads content outsiders can write | [B] Reaches private data or sensitive systems | [C] Changes state or sends data out |
| --- | --- | --- | --- |
| | | | |
| | | | |
| **Agent total** | | | |

All three lit: redesign, split the agent, or require a person's approval. See [the model](../reference/model.md#scorecard).
"""


def section(text: str) -> tuple[str, str]:
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    m = re.search(r"^## Checklist\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"no checklist in {title}")
    return title, m.group(1).strip()


def build() -> dict[pathlib.Path, str]:
    files: dict[pathlib.Path, str] = {}
    combined = [
        "# All checklists",
        "",
        "*Generated from the guide pages by `scripts/build_checklists.py`. Edit the pages, not this file.*",
        "",
    ]
    for page in PAGES:
        title, items = section(page.read_text())
        body = [
            f"# Checklist: {title}",
            "",
            f"*Generated from [{page.name}](../guide/{page.name}). Edit the page, not this file.*",
            "",
            items,
            "",
        ]
        if page.name.startswith("01-"):
            body.append(SCORECARD.strip() + "\n")
        files[OUT / page.name] = "\n".join(body)
        combined += [f"## {title}", "", f"From [{page.name}](../guide/{page.name}).", "", items, ""]
    files[OUT / "all-in-one.md"] = "\n".join(combined)
    return files


def main() -> None:
    files = build()
    if "--check" in sys.argv:
        stale = [p for p, c in files.items() if not p.exists() or p.read_text() != c]
        if stale:
            print("checklists/ is out of date; run scripts/build_checklists.py:")
            for p in stale:
                print("  ", p.relative_to(ROOT))
            sys.exit(1)
        print("checklists/ is up to date")
        return
    OUT.mkdir(exist_ok=True)
    for p, c in files.items():
        p.write_text(c)
        print("wrote", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
