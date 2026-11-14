#!/usr/bin/env python3
"""Scan MCP tool, prompt and resource definitions for signs of poisoning.

Reads the JSON written by mcp_probe.py, a raw tools/list result, or a list of
tools, and reports text that a model would read and might obey: hidden
characters, instructions addressed to the model, references to secrets or to
other tools, encoded blobs, and definitions that changed between listings.

Heuristics, not proof. A clean result means none of these patterns matched;
it does not mean the server is safe. Every finding needs a person's judgement.

Usage:
  python3 scan_definitions.py probe.json [--known-tools other.json] [--json out.json]
Exit code: 0 no high findings, 1 high findings, 2 usage error.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


@dataclass
class Finding:
    severity: str
    rule: str
    item: str
    field: str
    message: str
    evidence: str = ""


def visible(text: str, limit: int = 240) -> str:
    """Make invisible and control characters visible, and shorten."""
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "\n\t":
            out.append(" ")
        elif cat in ("Cf", "Cc", "Co", "Cn") or 0xE0000 <= ord(ch) <= 0xE007F:
            out.append(f"\\u{{{ord(ch):04x}}}")
        else:
            out.append(ch)
    s = "".join(out)
    return s if len(s) <= limit else s[: limit - 1] + "…"


# --- patterns -----------------------------------------------------------------

ANSI = re.compile(r"\x1b[\[\]]")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
PSEUDO_TAGS = re.compile(
    r"</?\s*(important|instructions?|system|secret|hidden|admin|note|context|prompt|assistant)\b[^>]*>", re.I
)
MODEL_ADDRESS = [
    ("high", re.compile(r"\bignore\b.{0,30}\b(instructions?|previous|prior|above|rules)\b", re.I), "tells the model to ignore instructions"),
    ("high", re.compile(r"\b(do\s*not|don'?t|never)\b.{0,40}\b(tell|mention|inform|reveal|show|notify)\b.{0,30}\b(user|human)\b", re.I), "asks the model to hide something from the user"),
    ("high", re.compile(r"\b(before|after|whenever|every time)\b.{0,40}\b(using|calling|invoking|running)\b.{0,30}\b(this|any|other|the)\b.{0,20}\btool", re.I), "sets a rule about calling tools"),
    ("medium", re.compile(r"\b(always|must|required to|you need to|you should)\b.{0,40}\b(call|invoke|read|send|include|pass)\b", re.I), "gives the model an order"),
    ("high", re.compile(r"\b(you are|as an? (ai|assistant|model)|the (assistant|ai|model|llm) (must|should))\b", re.I), "addresses the model directly"),
    ("high", re.compile(r"\b(system prompt|chat history|conversation (history|so far)|previous messages)\b", re.I), "refers to the model's context"),
]
SECRETS = re.compile(
    r"(~/\.ssh|id_rsa|id_ed25519|\.env\b|\.aws/|credentials|mcp\.json|claude_desktop_config|\.cursor/|"
    r"api[_ -]?key|access[_ -]?token|secret[_ -]?key|private[_ -]?key|password|passwd|keychain|wallet|seed phrase)",
    re.I,
)
SECRETS_ACTION = re.compile(r"\b(read|open|cat|pass|include|send|upload|copy|attach|forward|post|provide|append)\b", re.I)
CONTENT_PASSING = re.compile(
    r"\b(include|pass|put|append|copy|send|attach)\b.{0,40}\b(full|entire|complete|contents? of|text of|body of|everything)\b", re.I
)
CROSS_TOOL_GENERIC = re.compile(r"\b(other|another|different)\s+(tools?|servers?|mcp)\b|\binstead of\b", re.I)
URL = re.compile(r"\b(?:https?|ftp|wss?)://[^\s\"'<>)]+", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
BASE64_BLOB = re.compile(r"[A-Za-z0-9+/]{48,}={0,2}")
HEX_BLOB = re.compile(r"\b[0-9a-fA-F]{64,}\b")
ACTING_NAME = re.compile(r"(send|delete|remove|write|create|update|post|exec|run|transfer|pay|refund|deploy|drop|purge|upload|move|rename|kill)", re.I)


def iter_strings(obj, path: str = ""):
    """Yield (path, string) for every string inside a JSON value, keys included.
    Icon sources are skipped here and checked separately by check_icons()."""
    if path.endswith("icons") or ".icons[" in path or path.startswith("icons["):
        return
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}(key)" if path else f"{k}(key)", k
            yield from iter_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]")


def check_icons(item: str, obj) -> list[Finding]:
    out = []
    for i, icon in enumerate((obj or {}).get("icons") or []):
        src = icon.get("src", "") if isinstance(icon, dict) else ""
        if src.startswith("data:") and not src.startswith(("data:image/png", "data:image/jpeg", "data:image/webp", "data:image/gif", "data:image/svg+xml")):
            out.append(Finding("medium", "icon-data", item, f"icons[{i}].src", "icon is a data URI that is not an image", visible(src, 80)))
        elif src.startswith("http:"):
            out.append(Finding("low", "icon-url", item, f"icons[{i}].src", "icon loaded over plain HTTP (clients may fetch it automatically)", visible(src, 120)))
        elif src.startswith("https:"):
            out.append(Finding("info", "icon-url", item, f"icons[{i}].src", "icon loaded from a URL (clients may fetch it automatically)", visible(src, 120)))
    return out


def scan_text(item: str, field: str, text: str, other_names: set[str], self_name: str, foreign: set[str] | None = None) -> list[Finding]:
    f: list[Finding] = []
    hidden = [ch for ch in text if unicodedata.category(ch) in ("Cf", "Co", "Cn") or 0xE0000 <= ord(ch) <= 0xE007F]
    controls = [ch for ch in text if unicodedata.category(ch) == "Cc" and ch not in "\n\t\r"]
    if hidden:
        f.append(Finding("high", "hidden-characters", item, field, f"{len(hidden)} invisible or format characters (zero-width, bidirectional or tag characters)", visible(text)))
    if controls or ANSI.search(text):
        f.append(Finding("high", "control-characters", item, field, "control characters or terminal escape sequences", visible(text)))
    for m in HTML_COMMENT.finditer(text):
        f.append(Finding("high", "html-comment", item, field, "HTML comment (hidden from most interfaces, visible to the model)", visible(m.group(0))))
    for m in PSEUDO_TAGS.finditer(text):
        f.append(Finding("high", "pseudo-tag", item, field, f"tag a model may treat as special: {m.group(0)}", visible(text)))
    for sev, rx, why in MODEL_ADDRESS:
        m = rx.search(text)
        if m:
            f.append(Finding(sev, "model-instruction", item, field, why, visible(context(text, m))))
    m = SECRETS.search(text)
    if m:
        near = context(text, m, 80)
        sev = "high" if SECRETS_ACTION.search(near) else "medium"
        f.append(Finding(sev, "secrets-reference", item, field, f"mentions secrets or credential files ({m.group(0)})" + (" next to an instruction to read or pass something" if sev == "high" else ""), visible(near)))
    m = CONTENT_PASSING.search(text)
    if m:
        f.append(Finding("medium", "content-passing", item, field, "asks for whole contents to be passed in", visible(context(text, m))))
    for name in foreign or set():
        if len(name) > 3 and re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text):
            f.append(Finding("high", "cross-server-reference", item, field, f"mentions a tool from another server ({name})", visible(text)))
    if self_name:
        own = [n for n in other_names - (foreign or set()) if n != self_name and len(n) > 3 and re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text)]
        if own:
            f.append(Finding("info", "same-server-reference", item, field, f"mentions this server's other tools ({', '.join(sorted(own)[:5])})"))
    m = CROSS_TOOL_GENERIC.search(text)
    if m:
        f.append(Finding("medium", "cross-tool-reference", item, field, "refers to other tools or servers", visible(context(text, m))))
    for m in URL.finditer(text):
        if re.match(r"https?://json-schema\.org/", m.group(0)):
            continue
        f.append(Finding("medium", "url", item, field, "contains a URL", visible(m.group(0))))
    for m in EMAIL.finditer(text):
        f.append(Finding("medium", "email-address", item, field, "contains an email address", visible(m.group(0))))
    for rx, label in ((BASE64_BLOB, "base64-like"), (HEX_BLOB, "hex")):
        m = rx.search(text)
        if m:
            f.append(Finding("medium", "encoded-blob", item, field, f"{label} blob that may hide text", visible(m.group(0), 80)))
    if len(text) > 1000:
        f.append(Finding("low", "long-text", item, field, f"{len(text)} characters; long descriptions are where instructions hide", visible(text, 120)))
    return f


def context(text: str, m: re.Match, pad: int = 60) -> str:
    return text[max(0, m.start() - pad): m.end() + pad]


def scan_listing(listing: dict, known: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    tools = listing.get("tools") or []
    names = {t.get("name", "") for t in tools if isinstance(t, dict)}
    for t in tools:
        if not isinstance(t, dict):
            continue
        name = t.get("name", "?")
        item = f"tool {name}"
        for path, s in iter_strings({k: v for k, v in t.items() if k != "annotations"}):
            if path == "name":
                continue
            findings += scan_text(item, path, s, names, name, known)
        findings += check_icons(item, t)
        schema = t.get("inputSchema") or {}
        for pname, pdef in (schema.get("properties") or {}).items():
            default = pdef.get("default") if isinstance(pdef, dict) else None
            if isinstance(default, str) and len(default) > 200:
                findings.append(Finding("medium", "long-default", item, f"inputSchema.properties.{pname}.default", "long default value", visible(default)))
        ann = t.get("annotations") or {}
        acting = bool(ACTING_NAME.search(name))
        if ann.get("readOnlyHint") is True and acting:
            findings.append(Finding("medium", "annotation-mismatch", item, "annotations", "marked read-only but the name suggests it acts", json.dumps(ann)))
        if acting and not ann:
            findings.append(Finding("info", "no-annotations", item, "annotations", "acting tool without annotations; clients may not ask before running it"))
        if known and name in known:
            findings.append(Finding("medium", "shadowing", item, "name", "same name as a tool from another server the agent holds"))
    for kind in ("prompts", "resources", "resourceTemplates"):
        for p in listing.get(kind) or []:
            if isinstance(p, dict):
                item = f"{kind[:-1]} {p.get('name') or p.get('uri') or p.get('uriTemplate')}"
                for path, s in iter_strings(p):
                    findings += scan_text(item, path, s, names, "", known)
                findings += check_icons(item, p)
    instr = listing.get("instructions")
    if isinstance(instr, str) and instr:
        findings += scan_text("server instructions", "instructions", instr, names, "", known)
    return findings


def drift(listings: list[dict]) -> list[Finding]:
    """Compare successive listings: a change is what a rug pull looks like."""
    out: list[Finding] = []
    if len(listings) < 2:
        return out
    def index(listing):
        return {t.get("name"): json.dumps(t, sort_keys=True) for t in listing.get("tools") or [] if isinstance(t, dict)}
    first = index(listings[0])
    for n, later in enumerate(listings[1:], start=2):
        cur = index(later)
        for name in sorted(set(first) | set(cur)):
            if name not in cur:
                out.append(Finding("high", "definition-drift", f"tool {name}", "listing", f"present in listing 1, missing from listing {n}"))
            elif name not in first:
                out.append(Finding("high", "definition-drift", f"tool {name}", "listing", f"not in listing 1, appeared in listing {n}"))
            elif first[name] != cur[name]:
                out.append(Finding("high", "definition-drift", f"tool {name}", "definition", f"definition changed between listing 1 and listing {n}", visible(cur[name], 400)))
    return out


def load(path: Path) -> tuple[list[dict], dict]:
    if not path.is_file():
        raise SystemExit(f"{path}: not found (did the probe or sandbox run finish?)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [{"tools": data}], {}
    if "listings" in data:
        listings = data["listings"]
        for l in listings:
            l.setdefault("instructions", data.get("instructions"))
        return listings, data
    if "result" in data and isinstance(data["result"], dict):
        data = data["result"]
    if "tools" in data:
        return [data], {}
    raise SystemExit(f"{path}: no tools found")


def run(path: Path, known_path: Path | None = None) -> list[Finding]:
    listings, _ = load(path)
    known: set[str] = set()
    if known_path:
        kl, _ = load(known_path)
        known = {t.get("name", "") for l in kl for t in l.get("tools") or []}
    # Scan every listing: a rug pull may only show its poisoned text the second time.
    findings = [f for l in listings for f in scan_listing(l, known)] + drift(listings)
    # De-duplicate identical findings.
    seen, unique = set(), []
    for f in findings:
        key = (f.severity, f.rule, f.item, f.field, f.message)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return sorted(unique, key=lambda f: (SEVERITY_ORDER[f.severity], f.item, f.rule))


def to_markdown(findings: list[Finding], source: str) -> str:
    lines = [f"## Definition scan: {source}", ""]
    if not findings:
        lines.append("No patterns matched. That is not proof of safety; read the definitions yourself.")
        return "\n".join(lines) + "\n"
    counts = {s: sum(f.severity == s for f in findings) for s in SEVERITY_ORDER}
    lines.append(", ".join(f"{n} {s}" for s, n in counts.items() if n))
    lines += ["", "| Severity | Rule | Where | Finding | Evidence (escaped) |", "| --- | --- | --- | --- | --- |"]
    for f in findings:
        ev = f.evidence.replace("|", "\\|").replace("`", "'")
        lines.append(f"| {f.severity} | {f.rule} | {f.item} `{f.field}` | {f.message} | `{ev}` |" if ev else f"| {f.severity} | {f.rule} | {f.item} `{f.field}` | {f.message} | |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("--known-tools", type=Path, help="tool list from the other servers the agent will hold, for shadowing checks")
    ap.add_argument("--json", type=Path, help="also write findings as JSON")
    args = ap.parse_args()
    findings = run(args.input, args.known_tools)
    sys.stdout.write(to_markdown(findings, args.input.name))
    if args.json:
        args.json.write_text(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=True))
    return 1 if any(f.severity == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
