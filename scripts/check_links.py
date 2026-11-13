#!/usr/bin/env python3
"""Check that relative links and #anchors in the Markdown files resolve.

Run from the repository root: python3 scripts/check_links.py
External links are not fetched here; check them before each release.
"""
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
REPO_BLOB = "https://github.com/cafesecurity/mcp-security-guide/blob/main/"
REPO_TREE = "https://github.com/cafesecurity/mcp-security-guide/tree/main/"
SKIP_DIRS = {"node_modules", "dist", ".git"}


def slug(heading: str) -> str:
    h = heading.strip().lower()
    h = re.sub(r"[`*_]", "", h)
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    out = []
    for ch in h:
        cat = unicodedata.category(ch)
        if ch in " -":
            out.append("-" if ch == " " else ch)
        elif cat[0] in "LN" or ch == "_":
            out.append(ch)
    return "".join(out)


def anchors(path: pathlib.Path) -> set[str]:
    seen: dict[str, int] = {}
    result = set()
    in_code = False
    for line in path.read_text().splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(?:>\s*)?(#{1,6})\s+(.*)$", line)
        if m:
            s = slug(m.group(2))
            n = seen.get(s, 0)
            result.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    return result


def main() -> None:
    errors = []
    files = [p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)]
    for f in files:
        text = f.read_text()
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in LINK.findall(text):
            for prefix in (REPO_BLOB, REPO_TREE):
                if target.startswith(prefix):
                    target = str(pathlib.Path(*([".."] * len(f.parent.relative_to(ROOT).parts)), target[len(prefix):]))
            if re.match(r"^[a-z]+:", target):
                continue
            path_part, _, frag = target.partition("#")
            dest = (f.parent / path_part).resolve() if path_part else f
            if not dest.exists():
                errors.append(f"{f.relative_to(ROOT)}: missing {target}")
                continue
            if frag and dest.is_file() and dest.suffix == ".md" and frag not in anchors(dest):
                errors.append(f"{f.relative_to(ROOT)}: no anchor #{frag} in {dest.relative_to(ROOT)}")
    for e in errors:
        print(e)
    print(f"{len(files)} files checked, {len(errors)} problems")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
