#!/usr/bin/env python3
"""Validate the skills in skills/ against the Agent Skills specification
(agentskills.io): name and description rules, directory names, SKILL.md length,
and that shared scripts are identical copies.

Run from the repository root: python3 scripts/check_skills.py
"""
import filecmp
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHARED = [("mcp-server-audit/scripts/scan_definitions.py", "mcp-security-review/scripts/scan_definitions.py")]


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z-]+:", line):
            k, _, v = line.partition(":")
            out[k] = v.strip().strip('"')
    return out


def main() -> int:
    errors = []
    dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
    for d in dirs:
        text = (d / "SKILL.md").read_text()
        fm = frontmatter(text)
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not NAME_RX.match(name) or len(name) > 64:
            errors.append(f"{d.name}: invalid name {name!r}")
        if name != d.name:
            errors.append(f"{d.name}: name {name!r} does not match its directory")
        if not 1 <= len(desc) <= 1024:
            errors.append(f"{d.name}: description must be 1-1024 characters (is {len(desc)})")
        if "<" in desc or ">" in desc:
            errors.append(f"{d.name}: description must not contain angle brackets")
        if len(fm.get("compatibility", "")) > 500:
            errors.append(f"{d.name}: compatibility over 500 characters")
        if "license" not in fm:
            errors.append(f"{d.name}: no license")
        lines = text.count("\n")
        if lines > 500:
            errors.append(f"{d.name}: SKILL.md is {lines} lines; keep it under 500 and move detail to references/")
    for a, b in SHARED:
        if not filecmp.cmp(SKILLS / a, SKILLS / b, shallow=False):
            errors.append(f"{b} differs from {a}; copy it again")
    for e in errors:
        print(e)
    print(f"{len(dirs)} skills checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
