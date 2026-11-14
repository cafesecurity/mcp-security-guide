#!/usr/bin/env python3
"""Collect publication facts about an npm or PyPI package, and optionally download
its files for review WITHOUT installing it or running any of its code.

Reports: versions and publish dates, maintainers, linked repository, provenance
(npm), install-time scripts, whether a PyPI release is source-only (which runs
code at install), and warning signs such as a brand-new package or a version
published in the last few days.

Usage:
  python3 package_facts.py npm  @scope/name 1.2.3 [--download DIR] [--json out.json]
  python3 package_facts.py pypi name 1.2.3       [--download DIR] [--json out.json]
  Add --expect-repo github.com/vendor/repo to check the package links where you expect.

Needs network access to the registry. npm facts use the `npm` CLI (`npm view` and
`npm pack --ignore-scripts`, neither of which runs package code). Standard library otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

NOW = dt.datetime.now(dt.timezone.utc)
NAME_RE = {"npm": re.compile(r"(@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*", re.I),
           "pypi": re.compile(r"[a-z0-9]([a-z0-9._-]*[a-z0-9])?", re.I)}
VERSION_RE = re.compile(r"[0-9][a-z0-9.+!_-]*", re.I)


def check_spec(ecosystem: str, name: str, version: str) -> None:
    """Only a registry name and one exact version. Anything else (a URL, a git
    address, a path, a range, an option) would make npm or pip fetch something
    other than what is being audited."""
    if not NAME_RE[ecosystem].fullmatch(name) or len(name) > 214:
        raise SystemExit(f"not a valid {ecosystem} package name: {name!r} (registry names only: no URLs, paths or options)")
    if not VERSION_RE.fullmatch(version) or len(version) > 64:
        raise SystemExit(f"not an exact version: {version!r} (for example 1.4.2; no ranges or tags)")


def printable(text: str) -> str:
    """Registry text is written by the publisher: keep it from driving the terminal."""
    return "".join(ch if ch.isprintable() or ch == "\n" else "?" for ch in text)


def age_days(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return round((NOW - t).total_seconds() / 86400, 1)


def safe_extract_tar(data: bytes, dest: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        try:
            tf.extractall(dest, filter="data")  # refuses links outside dest, devices, absolute paths
        except TypeError:  # Python without extraction filters: check by hand
            root = dest.resolve()
            for m in tf.getmembers():
                target = (dest / m.name).resolve()
                if not str(target).startswith(str(root)) or m.issym() or m.islnk() or m.isdev():
                    raise ValueError(f"unsafe entry in archive: {m.name}")
            tf.extractall(dest)


def safe_extract_zip(data: bytes, dest: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for m in zf.infolist():
            target = (dest / m.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError(f"unsafe path in archive: {m.filename}")
        zf.extractall(dest)


def npm_facts(name: str, version: str, download: Path | None) -> dict:
    if not shutil.which("npm"):
        raise SystemExit("npm is not installed")
    def view(spec: str, *fields: str):
        r = subprocess.run(["npm", "view", spec, *fields, "--json"], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise SystemExit(f"npm view {spec} failed: {r.stderr.strip()[:300]}")
        return json.loads(r.stdout or "null")
    v = view(f"{name}@{version}")
    if isinstance(v, list):
        v = v[-1]
    times = view(name, "time") or {}
    versions = view(name, "versions") or []
    versions = versions if isinstance(versions, list) else [versions]
    facts = {
        "ecosystem": "npm",
        "name": v.get("name"),
        "version": v.get("version"),
        "description": v.get("description"),
        "mcpName": v.get("mcpName"),
        "repository": (v.get("repository") or {}).get("url") if isinstance(v.get("repository"), dict) else v.get("repository"),
        "homepage": v.get("homepage"),
        "license": v.get("license"),
        "maintainers": [m if isinstance(m, str) else m.get("name") for m in v.get("maintainers") or []],
        "publisher": (v.get("_npmUser") or {}).get("name") if isinstance(v.get("_npmUser"), dict) else v.get("_npmUser"),
        "first_published": times.get("created"),
        "this_version_published": times.get(version),
        "version_count": len(versions),
        "latest_versions": versions[-5:],
        "provenance": bool(((v.get("dist") or {}).get("attestations") or {}).get("provenance")),
        "install_scripts": {k: s for k, s in (v.get("scripts") or {}).items() if k in ("preinstall", "install", "postinstall")},
        "has_install_script_flag": bool(v.get("hasInstallScript")),
        "dependencies": sorted((v.get("dependencies") or {}).keys()),
        "bin": v.get("bin"),
        "deprecated": v.get("deprecated"),
        "tarball": (v.get("dist") or {}).get("tarball"),
        "integrity": (v.get("dist") or {}).get("integrity"),
    }
    if download:
        download.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["npm", "pack", f"{name}@{version}", "--ignore-scripts", "--pack-destination", str(download), "--json"],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise SystemExit(f"npm pack failed: {r.stderr.strip()[:300]}")
        tgz = download / json.loads(r.stdout)[0]["filename"]
        dest = download / "package-files"
        dest.mkdir(exist_ok=True)
        safe_extract_tar(tgz.read_bytes(), dest)
        facts["downloaded_to"] = str(dest)
    return facts


def pypi_facts(name: str, version: str, download: Path | None) -> dict:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as r:
        rel = json.load(r)
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=60) as r:
        allrel = json.load(r)
    info = rel["info"]
    files = rel.get("urls") or []
    uploads = [f.get("upload_time_iso_8601") for vs in allrel.get("releases", {}).values() for f in vs if f.get("upload_time_iso_8601")]
    facts = {
        "ecosystem": "pypi",
        "name": info.get("name"),
        "version": info.get("version"),
        "summary": info.get("summary"),
        "author": info.get("author") or info.get("author_email"),
        "maintainer": info.get("maintainer") or info.get("maintainer_email"),
        "project_urls": info.get("project_urls"),
        "license": info.get("license_expression") or info.get("license"),
        "first_published": min(uploads) if uploads else None,
        "this_version_published": min((f.get("upload_time_iso_8601") for f in files), default=None),
        "version_count": len(allrel.get("releases", {})),
        "latest_versions": list(allrel.get("releases", {}).keys())[-5:],
        "files": [{"filename": f.get("filename"), "packagetype": f.get("packagetype"), "sha256": (f.get("digests") or {}).get("sha256")} for f in files],
        "source_only": bool(files) and all(f.get("packagetype") == "sdist" for f in files),
        "requires_dist": info.get("requires_dist"),
        "yanked": rel.get("info", {}).get("yanked"),
    }
    if download:
        download.mkdir(parents=True, exist_ok=True)
        pick = next((f for f in files if f.get("packagetype") == "bdist_wheel"), None) or next((f for f in files if f.get("packagetype") == "sdist"), None)
        if pick:
            with urllib.request.urlopen(pick["url"], timeout=300) as r:
                data = r.read()
            (download / pick["filename"]).write_bytes(data)
            dest = download / "package-files"
            dest.mkdir(exist_ok=True)
            if pick["filename"].endswith((".whl", ".zip")):
                safe_extract_zip(data, dest)
            else:
                safe_extract_tar(data, dest)  # extracting a source archive does not run it
            facts["downloaded_to"] = str(dest)
    return facts


def warnings(f: dict, expect_repo: str | None) -> list[tuple[str, str]]:
    w = []
    first, this = age_days(f.get("first_published")), age_days(f.get("this_version_published"))
    if first is not None and first < 90:
        w.append(("medium", f"package first published {first} days ago"))
    if this is not None and this < 7:
        w.append(("medium", f"this version published {this} days ago; wait, or read its diff"))
    if f.get("install_scripts") or f.get("has_install_script_flag"):
        w.append(("high", f"runs code at install: {json.dumps(f.get('install_scripts') or 'install script present')}"))
    if f.get("source_only"):
        w.append(("high", "source-only release: installing it runs its build code"))
    if f.get("ecosystem") == "npm" and not f.get("provenance"):
        w.append(("low", "no provenance attestation: can't confirm which source and build produced it"))
    repo = f.get("repository") or json.dumps(f.get("project_urls") or {})
    if not repo or repo == "{}":
        w.append(("medium", "no source repository linked"))
    if expect_repo and expect_repo.lower() not in (repo or "").lower():
        w.append(("high", f"repository does not match the expected {expect_repo}: {repo}"))
    if f.get("ecosystem") == "npm" and len(f.get("maintainers") or []) == 1:
        w.append(("info", "single maintainer"))
    if f.get("deprecated") or f.get("yanked"):
        w.append(("high", f"this version is deprecated or yanked: {f.get('deprecated') or f.get('yanked')}"))
    return w


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ecosystem", choices=["npm", "pypi"])
    ap.add_argument("name")
    ap.add_argument("version", help="an exact version; audits are of one version")
    ap.add_argument("--download", type=Path, help="download and unpack the package here, without running it")
    ap.add_argument("--expect-repo", help="the repository you expect, e.g. github.com/vendor/server")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    check_spec(args.ecosystem, args.name, args.version)
    facts = (npm_facts if args.ecosystem == "npm" else pypi_facts)(args.name, args.version, args.download)
    facts["warnings"] = [{"severity": s, "message": m} for s, m in warnings(facts, args.expect_repo)]
    print(printable(f"## Package facts: {facts['name']} {facts['version']} ({args.ecosystem})\n"))
    for k in ("repository", "project_urls", "homepage", "mcpName", "publisher", "maintainers", "author", "first_published",
              "this_version_published", "version_count", "provenance", "install_scripts", "source_only", "dependencies", "downloaded_to"):
        if k in facts and facts[k] not in (None, [], {}, ""):
            print(printable(f"- **{k}**: {json.dumps(facts[k]) if not isinstance(facts[k], str) else facts[k]}"))
    print("\n### Warnings\n")
    for x in facts["warnings"] or [{"severity": "info", "message": "none"}]:
        print(printable(f"- {x['severity']}: {x['message']}"))
    if args.json:
        args.json.write_text(json.dumps(facts, indent=2))
    return 1 if any(x["severity"] == "high" for x in facts["warnings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
