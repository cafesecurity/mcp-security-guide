#!/usr/bin/env python3
"""Static scan of an MCP server's source for risky code: shell and dynamic code
execution, credential and home-directory access, outbound network destinations,
install-time scripts, wide network binding, and token passthrough.

Reads files only. It never imports, builds or runs the code it scans.

Heuristics, not proof: it finds patterns worth a person's attention, and it
will miss obfuscated or unusual code. Read the flagged lines yourself.

Usage:
  python3 scan_code.py SOURCE_DIR [--include-deps] [--json out.json]
Exit code: 0 no high findings, 1 high findings, 2 usage error.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

CODE_EXT = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx", ".py"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "dist-tests", "coverage"}
MAX_FILE = 2_000_000
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


@dataclass
class Finding:
    severity: str
    rule: str
    file: str
    line: int
    message: str
    snippet: str


# (severity, rule, message, regex, languages: "js", "py" or "any")
RULES = [
    # Command and code execution
    ("high", "shell-exec", "runs a command through a shell", r"(?<![.\w])exec\s*\(|\b(child_process|childProcess|cp)\.exec\s*\(|\bexecSync\s*\(|shell\s*:\s*true|\bshell\s*=\s*True\b|\bos\.(system|popen)\s*\(|subprocess\.(getoutput|getstatusoutput)\s*\(", "any"),
    ("medium", "process-spawn", "starts a process (check where the command and arguments come from)", r"\b(spawn|spawnSync|execFile|execFileSync|fork)\s*\(|\bsubprocess\.(run|Popen|call|check_output|check_call)\s*\(", "any"),
    ("high", "dynamic-code", "evaluates code at run time", r"\beval\s*\(|\bnew\s+Function\s*\(|\bvm\.(runIn\w*|Script)\b|\bexec\s*\(\s*(compile|base64|codecs|bytes|marshal)|\b__import__\s*\(|\bpickle\.loads?\s*\(|\bmarshal\.loads\s*\(", "any"),
    ("high", "decode-and-run", "decodes data and runs or loads it", r"(atob|Buffer\.from\([^)]*base64[^)]*\)|b64decode\([^)]*\)|fromCharCode)[^\n]{0,80}(eval|Function|exec|require|import)", "any"),
    # Credentials and personal files
    ("high", "credential-paths", "touches credential or configuration files", r"\.ssh\b|id_rsa|id_ed25519|\.aws/|\.npmrc|\.pypirc|\.netrc|\.git-credentials|\.docker/config|\.kube/config|claude_desktop_config|\.cursor/|mcp\.json|Keychain|wallet\.dat|\.gnupg", "any"),
    ("medium", "home-directory", "reads from the user's home directory", r"\bos\.homedir\s*\(|\bhomedir\(\)|process\.env\.HOME\b|expanduser\s*\(\s*['\"]~|Path\.home\s*\(", "any"),
    ("high", "env-dump", "reads the whole environment", r"JSON\.stringify\s*\(\s*process\.env\b|\.\.\.\s*process\.env\b|Object\.(entries|keys|values)\s*\(\s*process\.env\b|dict\s*\(\s*os\.environ\s*\)|json\.dumps\s*\(\s*(dict\s*\()?os\.environ|os\.environ\.copy\s*\(\)\s*\)", "any"),
    # Network
    ("medium", "raw-network", "opens raw sockets or makes DNS lookups", r"\bnet\.(connect|createConnection)\b|\bdgram\b|\bdns\.(resolve\w*|lookup)\b|\bsocket\.(socket|create_connection|getaddrinfo|gethostbyname)\b|new\s+WebSocket\s*\(", "any"),
    ("high", "token-passthrough", "forwards the caller's Authorization header", r"headers?\s*[\[.]\s*['\"]?authorization['\"]?\s*\]?[^\n]{0,120}(fetch|axios|request|got|http|post|get)\s*\(|(fetch|axios|request|got)\s*\([^\n]{0,200}req(uest)?\.headers\.authorization", "any"),
    ("medium", "wide-binding", "listens on every interface", r"['\"]0\.0\.0\.0['\"]|host\s*[:=]\s*['\"]::['\"]", "any"),
    ("medium", "permissive-cors", "allows any origin", r"Access-Control-Allow-Origin['\"]?\s*[,:]\s*['\"]\*|origin\s*:\s*['\"]\*['\"]|allow_origins\s*=\s*\[\s*['\"]\*['\"]", "any"),
    ("low", "tls-disabled", "turns off TLS certificate checks", r"rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|verify\s*=\s*False", "any"),
    ("medium", "hidden-recipient", "adds copy recipients (check where the address comes from)", r"\bbcc\b|\bcc\s*:", "any"),
    ("low", "telemetry", "sends telemetry or analytics", r"telemetry|analytics|posthog|segment\.io|mixpanel|sentry", "any"),
    ("medium", "obfuscation", "long encoded string or heavy escaping", r"['\"][A-Za-z0-9+/=]{200,}['\"]|(\\x[0-9a-fA-F]{2}){20,}|(\\u[0-9a-fA-F]{4}){20,}", "any"),
]
COMPILED = [(sev, rule, msg, re.compile(rx, re.I if rule not in ("dynamic-code",) else 0), lang) for sev, rule, msg, rx, lang in RULES]
URL_RX = re.compile(r"\b(?:https?|wss?)://([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?::\d+)?", re.I)
EMAIL_RX = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
BENIGN_HOSTS = {"modelcontextprotocol.io", "json-schema.org", "www.w3.org", "example.com", "example.org", "localhost", "github.com", "nodejs.org", "npmjs.com", "www.npmjs.com", "python.org", "docs.python.org"}


def visible(text: str, limit: int = 200) -> str:
    """Escape invisible and control characters so they show up in the report."""
    out = "".join(
        f"\\u{{{ord(c):04x}}}" if unicodedata.category(c) in ("Cf", "Cc", "Co", "Cn") or 0xE0000 <= ord(c) <= 0xE007F else c
        for c in text
    )
    return out if len(out) <= limit else out[: limit - 1] + "…"


def lang_of(path: Path) -> str:
    return "py" if path.suffix == ".py" else "js"


def scan_file(path: Path, root: Path, findings: list[Finding], hosts: Counter, emails: Counter) -> None:
    try:
        if path.stat().st_size > MAX_FILE:
            findings.append(Finding("low", "large-file", str(path.relative_to(root)), 0, "file too large to scan; check it by hand", ""))
            return
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    rel = str(path.relative_to(root))
    lines = text.splitlines()
    if lines and max((len(l) for l in lines), default=0) > 5000 and path.suffix in {".js", ".mjs", ".cjs"}:
        findings.append(Finding("low", "minified", rel, 0, "minified or bundled code; static review is unreliable here", ""))
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if any(unicodedata.category(c) == "Cf" or 0xE0000 <= ord(c) <= 0xE007F for c in line):
            findings.append(Finding("high", "hidden-characters", rel, i, "invisible characters in source (can hide text from reviewers)", visible(stripped)))
        if stripped.startswith(("//", "#", "*", "/*")) and "http" not in stripped:
            continue
        for sev, rule, msg, rx, lang in COMPILED:
            if lang not in ("any", lang_of(path)):
                continue
            if rx.search(line):
                findings.append(Finding(sev, rule, rel, i, msg, visible(line.strip())))
        for m in URL_RX.finditer(line):
            hosts[m.group(1).lower()] += 1
        for m in EMAIL_RX.finditer(line):
            emails[m.group(0).lower()] += 1


def scan_manifests(root: Path, findings: list[Finding]) -> dict:
    facts: dict = {}
    for pj in root.rglob("package.json"):
        if "node_modules" in pj.parts and pj.parent != root:
            continue
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rel = str(pj.relative_to(root))
        scripts = data.get("scripts") or {}
        for hook in ("preinstall", "install", "postinstall", "prepare", "prepack", "postpack"):
            if hook in scripts:
                sev = "high" if hook in ("preinstall", "install", "postinstall") else "low"
                findings.append(Finding(sev, "install-script", rel, 0, f"runs code at install time ({hook})", f"{hook}: {scripts[hook]}"[:200]))
        if pj.parent == root:
            facts["package"] = {k: data.get(k) for k in ("name", "version", "mcpName", "bin", "main", "repository", "homepage")}
            facts["dependencies"] = sorted((data.get("dependencies") or {}).keys())
            for dep, ver in (data.get("dependencies") or {}).items():
                if isinstance(ver, str) and (ver.startswith(("git", "http", "file:")) or "/" in ver and not ver.startswith("npm:")):
                    findings.append(Finding("medium", "unusual-dependency", rel, 0, "dependency from a URL, git or local path", f"{dep}: {ver}"))
                elif ver in ("*", "latest", ""):
                    findings.append(Finding("medium", "unpinned-dependency", rel, 0, "dependency on any version", f"{dep}: {ver}"))
    for name in ("setup.py",):
        for f in root.rglob(name):
            findings.append(Finding("medium", "install-script", str(f.relative_to(root)), 0, "setup.py runs code when built or installed from source", ""))
    for pp in root.rglob("pyproject.toml"):
        try:
            text = pp.read_text(encoding="utf-8")
        except OSError:
            continue
        m = re.search(r"build-backend\s*=\s*['\"]([^'\"]+)", text)
        if m and m.group(1) not in ("hatchling.build", "setuptools.build_meta", "flit_core.buildapi", "poetry.core.masonry.api", "pdm.backend", "uv_build", "maturin", "scikit_build_core.build"):
            findings.append(Finding("medium", "unusual-build-backend", str(pp.relative_to(root)), 0, "custom build backend runs code at install", m.group(1)))
    return facts


def run(root: Path, include_deps: bool) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    hosts: Counter = Counter()
    emails: Counter = Counter()
    files = 0
    for path in sorted(root.rglob("*")):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS or (not include_deps and ("node_modules" in parts or "site-packages" in parts)):
            continue
        if path.is_file() and path.suffix in CODE_EXT and not path.name.endswith((".d.ts", ".map")):
            files += 1
            scan_file(path, root, findings, hosts, emails)
    facts = scan_manifests(root, findings)
    facts["files_scanned"] = files
    facts["outbound_hosts"] = {h: n for h, n in hosts.most_common() if h not in BENIGN_HOSTS}
    facts["email_addresses"] = dict(emails.most_common())
    if facts["outbound_hosts"]:
        findings.append(Finding("info", "outbound-hosts", ".", 0, "hard-coded hosts: check each one is expected", ", ".join(list(facts["outbound_hosts"])[:30])))
    if facts["email_addresses"]:
        findings.append(Finding("medium", "hard-coded-emails", ".", 0, "hard-coded email addresses", ", ".join(list(facts["email_addresses"])[:20])))
    if files == 0:
        findings.append(Finding("info", "no-code", ".", 0, "no source files found (compiled binary or remote-only server?)", ""))
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule, f.file, f.line)), facts


def to_markdown(findings: list[Finding], facts: dict, source: str) -> str:
    lines = [f"## Code scan: {source}", "", f"Files scanned: {facts.get('files_scanned', 0)}."]
    pkg = facts.get("package")
    if pkg:
        lines.append(f"Package: `{pkg.get('name')}` {pkg.get('version')}; mcpName `{pkg.get('mcpName')}`; repository {json.dumps(pkg.get('repository'))}.")
    lines.append("")
    if not findings:
        lines.append("No patterns matched. That is not proof of safety.")
        return "\n".join(lines) + "\n"
    lines += ["| Severity | Rule | Where | Finding | Line |", "| --- | --- | --- | --- | --- |"]
    for f in findings:
        snip = f.snippet.replace("|", "\\|").replace("`", "'")
        where = f"{f.file}:{f.line}" if f.line else f.file
        lines.append(f"| {f.severity} | {f.rule} | `{where}` | {f.message} | `{snip}` |" if snip else f"| {f.severity} | {f.rule} | `{where}` | {f.message} | |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("--include-deps", action="store_true", help="also scan node_modules and site-packages")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    if not args.source.is_dir():
        ap.error(f"{args.source} is not a directory")
    findings, facts = run(args.source.resolve(), args.include_deps)
    sys.stdout.write(to_markdown(findings, facts, args.source.name))
    if args.json:
        args.json.write_text(json.dumps({"facts": facts, "findings": [asdict(f) for f in findings]}, indent=2))
    return 1 if any(f.severity == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
