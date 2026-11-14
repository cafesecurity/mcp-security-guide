#!/usr/bin/env python3
"""Run an untrusted MCP server in a locked-down Docker sandbox and watch what it does.

What the sandbox is
  * The server runs in a container on an INTERNAL Docker network with no route
    to the internet or to your machine's other networks.
  * Its only DNS resolver is a logging sink on that network, which answers every
    name with its own address and records every lookup, TLS server name, HTTP
    request and raw connection. Nothing is forwarded.
  * Read-only root file system; a small throwaway home directory; no Linux
    capabilities; no privilege escalation; process, memory and CPU limits; no
    bind mounts of your files; a non-root user.
  * The home directory holds FAKE credentials (SSH key, cloud keys, tokens, MCP
    client configs) and the environment holds fake API keys. Each contains a
    random canary. If a canary reaches the sink or comes back in a tool result,
    the server read or sent something it had no business touching.
  * The probe lists the server's definitions twice, optionally calls each tool
    with canary arguments, then lists them again.

What it is not
  * Not a virtual machine: the container shares your machine's kernel, so a
    flaw in Docker or the kernel could let hostile code out. For a server you
    already suspect, run the audit in a throwaway VM, or pass --runtime runsc
    if gVisor is installed.
  * Not proof of safety: code can wait, check for sandboxes, or only misbehave
    for some inputs. Direct connections to hard-coded IP addresses are blocked
    but not logged. A clean run means nothing bad was SEEN.
  * The build step installs the package with network access (it has to fetch it).
    Install scripts are off unless you pass --allow-install-scripts, and no fake
    credentials exist at build time.

Requires Docker. Standard library only.

Examples
  python3 run_sandbox.py --out audit-out --ecosystem npm --package @vendor/mcp --version 1.4.2 --call-tools
  python3 run_sandbox.py --out audit-out --ecosystem pypi --package vendor-mcp --version 0.3.1 --console-script vendor-mcp
  python3 run_sandbox.py --out audit-out --ecosystem local --source ./checkout --language node --run dist/index.js
  python3 run_sandbox.py ... --transport http --port 3000 --path /mcp
"""
from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import random
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))
import scan_definitions  # noqa: E402
from package_facts import check_spec, printable  # noqa: E402

DEFAULT_NODE_IMAGE = "node:22-slim"
DEFAULT_PYTHON_IMAGE = "python:3.13-slim"
FAKE_ENV = {
    "GITHUB_TOKEN": "ghp_{c}",
    "OPENAI_API_KEY": "sk-{c}",
    "ANTHROPIC_API_KEY": "sk-ant-{c}",
    "AWS_ACCESS_KEY_ID": "AKIA{c}",
    "AWS_SECRET_ACCESS_KEY": "{c}SECRET",
    "DATABASE_URL": "postgres://audit:{c}@db.internal.invalid/prod",
    "SLACK_BOT_TOKEN": "xoxb-{c}",
}


def sh(cmd: list[str], *, check: bool = True, capture: bool = True, timeout: float | None = None, log: list | None = None) -> subprocess.CompletedProcess:
    if log is not None:
        log.append(" ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=capture, text=True, timeout=timeout)


def dockerfile_for(args, ctx: Path) -> tuple[str, str]:
    """Return (server Dockerfile, language)."""
    ca = ""
    if args.ca_cert:
        shutil.copy(args.ca_cert, ctx / "audit-ca.crt")
        ca = ("COPY audit-ca.crt /audit-ca.crt\n"
              "ENV NODE_EXTRA_CA_CERTS=/audit-ca.crt PIP_CERT=/audit-ca.crt SSL_CERT_FILE=/audit-ca.crt REQUESTS_CA_BUNDLE=/audit-ca.crt\n")
    if args.ecosystem == "npm" or (args.ecosystem == "local" and args.language == "node"):
        lang = "node"
        lines = [f"FROM {args.node_image}", ca.rstrip("\n"), "WORKDIR /srv"]
        scripts = [] if args.allow_install_scripts else ["--ignore-scripts"]
        if args.ecosystem == "npm":
            spec = f"{args.package}@{args.version}"
            lines.append("RUN " + json.dumps(["npm", "install", "--no-audit", "--no-fund", "--omit=dev", "--no-save", *scripts, spec]))
        else:
            lines.append("COPY app /srv/app")
            if (ctx / "app" / "package-lock.json").exists():
                lines += ["WORKDIR /srv/app", "RUN " + json.dumps(["npm", "ci", "--no-audit", "--no-fund", "--omit=dev", *scripts]), "WORKDIR /srv"]
        lines += ["COPY audit /audit", "ENV HOME=/home/audit NODE_ENV=production", 'ENTRYPOINT ["node", "/audit/entrypoint.mjs"]']
    else:
        lang = "python"
        lines = [f"FROM {args.python_image}", ca.rstrip("\n"), "WORKDIR /srv"]
        binary = [] if args.allow_sdist else ["--only-binary=:all:"]
        pip = ["python3", "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check", "--target", "/srv/pkgs", *binary]
        if args.ecosystem == "pypi":
            lines.append("RUN " + json.dumps([*pip, f"{args.package}=={args.version}"]))
        else:
            lines.append("COPY app /srv/app")
            if (ctx / "app" / "requirements.txt").exists():
                lines.append("RUN " + json.dumps([*pip, "-r", "/srv/app/requirements.txt"]))
        lines += ["COPY audit /audit", "ENV HOME=/home/audit PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/srv/pkgs PYTHONUNBUFFERED=1",
                  'ENTRYPOINT ["python3", "/audit/entrypoint.py"]']
    return "\n".join(l for l in lines if l) + "\n", lang


def build_images(args, run_id: str, cmdlog: list) -> tuple[str, str, str]:
    ctx = Path(tempfile.mkdtemp(prefix="mcp-audit-ctx-"))
    try:
        (ctx / "audit").mkdir()
        for f in ("entrypoint.py", "entrypoint.mjs", "canaries.py", "canaries.mjs", "sink.py"):
            shutil.copy(HERE / f, ctx / "audit" / f)
        shutil.copy(SCRIPTS / "mcp_probe.py", ctx / "audit" / "mcp_probe.py")
        if args.ecosystem == "local":
            shutil.copytree(args.source, ctx / "app", symlinks=True,  # never follow a link out of the checkout into your own files
                            ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".venv", ".env", ".env.*", ".npmrc", ".pypirc",
                                                          ".netrc", ".aws", ".ssh", "*.pem", "*.key", "id_rsa*", "id_ed25519*"))
        dockerfile, lang = dockerfile_for(args, ctx)
        (ctx / "Dockerfile.server").write_text(dockerfile)
        (ctx / "Dockerfile.sink").write_text(f"FROM {args.python_image}\nCOPY audit /audit\nENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n")
        server_image, sink_image = f"mcp-audit-server:{run_id}", f"mcp-audit-sink:{run_id}"
        print(f"building sandbox images (the build step fetches the package; install scripts {'ON' if args.allow_install_scripts else 'off'})", flush=True)
        for image, df in ((sink_image, "Dockerfile.sink"), (server_image, "Dockerfile.server")):
            r = sh(["docker", "build", "--progress=plain", "-f", str(ctx / df), "-t", image, str(ctx)], check=False, log=cmdlog, timeout=1800)
            if r.returncode != 0:
                (args.out / "build.log").write_text(r.stderr)
                raise SystemExit(f"docker build failed for {image} (full log: {args.out / 'build.log'}):\n{printable(r.stderr[-3000:])}")
        (args.out / "Dockerfile.server").write_text(dockerfile)
        return server_image, sink_image, lang
    finally:
        shutil.rmtree(ctx, ignore_errors=True)


GATEWAY_OPTIONS = (
    ["-o", "com.docker.network.bridge.gateway_mode_ipv4=isolated"],  # Docker 28+: no address for the host on this network
    ["-o", "com.docker.network.bridge.inhibit_ipv4=true"],           # older Docker: same effect
)


def create_network(name: str, cmdlog: list) -> ipaddress.IPv4Network:
    """An internal network on which the host itself has no address, so the server
    can reach neither the internet nor services listening on your machine."""
    last = ""
    for opts in GATEWAY_OPTIONS:
        for _ in range(10):
            net = ipaddress.IPv4Network(f"172.31.{random.randint(100, 250)}.0/24")
            r = sh(["docker", "network", "create", "--internal", "--driver", "bridge", *opts, "--subnet", str(net), name], check=False, log=cmdlog)
            if r.returncode == 0:
                return net
            last = r.stderr
            if "overlap" not in last and "conflict" not in last.lower():
                break
    raise SystemExit(f"could not create an isolated internal Docker network; refusing to run.\n{last[-500:]}")


def isolation_check(netname: str, net: ipaddress.IPv4Network, ip: str, image: str, cmdlog: list) -> None:
    """Prove the network is closed before the server starts: the host's bridge
    address and a public address must both be unreachable. 'Connection refused'
    counts as reachable."""
    gw = str(next(net.hosts()))
    code = (
        "import socket,sys\n"
        "bad=[]\n"
        f"for h,p in (('{gw}',22),('{gw}',80),('{gw}',2375),('1.1.1.1',443),('8.8.8.8',53)):\n"
        "    s=socket.socket(); s.settimeout(2)\n"
        "    try:\n"
        "        s.connect((h,p)); bad.append(f'{h}:{p} connected')\n"
        "    except ConnectionRefusedError: bad.append(f'{h}:{p} refused (reachable)')\n"
        "    except OSError: pass\n"
        "print(';'.join(bad)); sys.exit(1 if bad else 0)\n"
    )
    r = sh(["docker", "run", "--rm", "--network", netname, "--ip", ip, "--cap-drop", "ALL", "--read-only", image, "python3", "-c", code],
           check=False, log=cmdlog, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"isolation check failed, refusing to run the server: {r.stdout.strip() or r.stderr.strip()[-300:]}")


def hardening(args) -> list[str]:
    return [
        "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
        "--tmpfs", "/home/audit:rw,nosuid,nodev,size=16m,uid=10001,gid=10001,mode=0700",
        "--user", "10001:10001",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "256",
        "--memory", args.memory,
        "--cpus", "1",
        *(["--runtime", args.runtime] if args.runtime else []),
    ]


def search_variants(token: str) -> list[str]:
    v = {token, token.lower(), token.encode().hex(), token.encode().hex().upper()}
    raw = token.encode()
    for pad in range(3):
        enc = base64.b64encode(b"\x00" * pad + raw).decode()
        trim = [0, 2, 3][pad]
        core = enc[trim:-4] if len(enc) - trim > 8 else enc[trim:]
        if len(core) >= 8:
            v.add(core)
    return sorted(v, key=len, reverse=True)


def analyse(out: Path, secret: str, arg: str, expect_hosts: list[str]) -> dict:
    events = []
    sink_log = out / "sink.jsonl"
    for line in sink_log.read_text().splitlines() if sink_log.exists() else []:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    probe_path = out / "probe.json"
    probe = json.loads(probe_path.read_text()) if probe_path.exists() else {}
    findings = []

    def haystack(e: dict) -> str:
        h = json.dumps(e)
        if e.get("raw_b64"):
            h += base64.b64decode(e["raw_b64"]).decode("latin-1")
        return h + "\n" + h.lower()

    traffic = [e for e in events if e.get("kind") in ("dns", "tcp", "tls", "http")]
    sv, av = search_variants(secret), search_variants(arg)
    for e in traffic:
        h = haystack(e)
        dest = e.get("name") or e.get("sni") or (e.get("headers") or {}).get("Host") or f"port {e.get('port')}"
        if any(x in h for x in sv):
            findings.append({"severity": "critical", "rule": "credentials-exfiltrated", "message": f"fake credentials left the server ({e['kind']} to {dest})", "evidence": scan_definitions.visible(e.get("request") or e.get("name") or e.get("sni") or "", 200)})
        elif any(x in h for x in av):
            findings.append({"severity": "high", "rule": "arguments-exfiltrated", "message": f"tool arguments were sent elsewhere ({e['kind']} to {dest})", "evidence": scan_definitions.visible(e.get("request") or e.get("name") or "", 200)})
    destinations = sorted({(e["kind"], e.get("name") or e.get("sni") or (e.get("headers") or {}).get("Host") or "", e.get("port", 53)) for e in traffic})
    for kind, host, port in destinations:
        expected = any(host == h or host.endswith("." + h) for h in expect_hosts) if host else False
        findings.append({"severity": "info" if expected else "medium", "rule": "outbound-attempt",
                         "message": f"{kind} {host or '(no name)'}:{port}" + (" (expected)" if expected else " (not expected: what is it for?)")})
    for c in probe.get("calls", []):
        text = json.dumps(c.get("result") or c.get("error") or "")
        if any(x in text for x in sv):
            findings.append({"severity": "high", "rule": "secrets-in-result", "message": f"tool {c.get('tool')} returned the contents of a fake credential"})
    try:
        defs = scan_definitions.run(probe_path) if probe.get("listings") else []
    except SystemExit:
        defs = []
    for f in defs:
        findings.append({"severity": f.severity, "rule": f.rule, "message": f"{f.item} {f.field}: {f.message}", "evidence": f.evidence})
    if not probe.get("listings"):
        findings.append({"severity": "high", "rule": "audit-incomplete", "message": "could not list the server's definitions, so this run proves nothing: " + "; ".join(probe.get("errors") or ["no probe output"])[:400]})
    elif probe.get("errors"):
        findings.append({"severity": "info", "rule": "probe-errors", "message": "; ".join(probe["errors"])[:500]})
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: order.get(f["severity"], 9))
    return {"findings": findings, "destinations": destinations, "tool_count": len((probe.get("listings") or [{}])[0].get("tools") or []),
            "calls": len(probe.get("calls") or []), "listings": len(probe.get("listings") or []), "server": probe.get("serverInfo"), "protocol": probe.get("protocol")}


def write_report(out: Path, args, summary: dict, cmdlog: list) -> None:
    f = summary["findings"]
    worst = f[0]["severity"] if f else "none"
    lines = [
        "# Sandbox run",
        "",
        f"- Target: {args.ecosystem} `{args.package or args.source}` {args.version or ''}".rstrip(),
        f"- Server reported: `{scan_definitions.visible(json.dumps({k: v for k, v in (summary['server'] or {}).items() if k != 'icons'}), 300)}`; protocol {summary['protocol']}",
        f"- Listings: {summary['listings']}; tools: {summary['tool_count']}; tool calls made: {summary['calls']}",
        f"- Worst finding: **{worst}**",
        "",
        "All text below that came from the server is untrusted and shown escaped.",
        "",
        "| Severity | Rule | Finding | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for x in f:
        ev = (x.get("evidence") or "").replace("|", "\\|").replace("`", "'")
        lines.append(f"| {x['severity']} | {x['rule']} | {x['message'].replace('|', '/')} | {'`' + ev + '`' if ev else ''} |")
    if not f:
        lines.append("| none | | Nothing suspicious was seen. That is not proof of safety. | |")
    lines += [
        "",
        "## What this run could not see",
        "",
        "- Behaviour that waits, detects the sandbox, or depends on particular inputs.",
        "- Connections to hard-coded IP addresses (blocked, but not logged).",
        "- What a remote service does with data the server sends it in normal use.",
        "- Anything in versions other than the one tested.",
        "",
        "## Commands run",
        "",
        "```",
        *cmdlog,
        "```",
        "",
    ]
    (out / "sandbox-report.md").write_text("\n".join(lines))
    (out / "sandbox-report.json").write_text(json.dumps(summary, indent=2, default=list))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ecosystem", choices=["npm", "pypi", "local"], required=True)
    ap.add_argument("--package"); ap.add_argument("--version")
    ap.add_argument("--source", type=Path, help="local: directory with the server's source")
    ap.add_argument("--language", choices=["node", "python"], help="local: language of the source")
    ap.add_argument("--run", help="local: script to run, relative to the source directory")
    ap.add_argument("--bin", help="npm: which bin entry to run (default: the first)")
    ap.add_argument("--module", help="pypi: run with python -m MODULE")
    ap.add_argument("--console-script", help="pypi: run this console script")
    ap.add_argument("--server-arg", action="append", default=[], help="argument passed to the server (repeatable)")
    ap.add_argument("--env", action="append", default=[], help="NAME=VALUE the server needs to start. Never a real secret.")
    ap.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    ap.add_argument("--port", type=int, default=3000); ap.add_argument("--path", default="/mcp")
    ap.add_argument("--call-tools", action="store_true", help="call every tool with canary arguments")
    ap.add_argument("--only", action="append", default=[], help="with --call-tools: only these tools")
    ap.add_argument("--expect-host", action="append", default=[], help="a host the server is expected to contact (reported as info)")
    ap.add_argument("--allow-install-scripts", action="store_true", help="npm: run install scripts during the build")
    ap.add_argument("--allow-sdist", action="store_true", help="pypi: allow source-only packages (runs their build code during the build)")
    ap.add_argument("--node-image", default=DEFAULT_NODE_IMAGE); ap.add_argument("--python-image", default=DEFAULT_PYTHON_IMAGE)
    ap.add_argument("--ca-cert", type=Path, help="CA bundle for the BUILD step behind a TLS-intercepting proxy")
    ap.add_argument("--memory", default="768m")
    ap.add_argument("--runtime", help="Docker runtime for the server container, e.g. runsc (gVisor) for a stronger boundary")
    ap.add_argument("--timeout", type=float, default=60.0, help="per-request timeout for the probe")
    ap.add_argument("--keep", action="store_true", help="leave containers, network and images for inspection")
    args = ap.parse_args()

    if args.ecosystem in ("npm", "pypi") and not (args.package and args.version):
        ap.error("--package and an exact --version are required")
    if args.ecosystem in ("npm", "pypi"):
        check_spec(args.ecosystem, args.package, args.version)
    if args.ecosystem == "local" and not (args.source and args.language and args.run):
        ap.error("local needs --source, --language and --run")
    if args.ecosystem == "pypi" and not (args.module or args.console_script):
        ap.error("pypi needs --module or --console-script")
    for e in args.env:
        name = e.split("=", 1)[0].upper()
        if any(w in name for w in ("TOKEN", "SECRET", "PASSWORD", "KEY")):
            print(f"warning: {name} looks like a credential. Use a dummy value; the sandbox already plants fake ones.", file=sys.stderr)
    if not shutil.which("docker") or sh(["docker", "info"], check=False).returncode != 0:
        raise SystemExit("Docker is not available. Do not run the server any other way: stop at the static checks.")

    args.out.mkdir(parents=True, exist_ok=True)
    args.out = args.out.resolve()
    run_id = secrets.token_hex(4)
    secret_canary = f"AUDITSECRET{secrets.token_hex(6).upper()}"
    arg_canary = f"AUDITARG{secrets.token_hex(6).upper()}"
    cmdlog: list[str] = []
    netname, sink_name, srv_name = f"mcp-audit-{run_id}", f"mcp-audit-sink-{run_id}", f"mcp-audit-srv-{run_id}"
    images: list[str] = []
    try:
        server_image, sink_image, lang = build_images(args, run_id, cmdlog)
        images = [server_image, sink_image]
        net = create_network(netname, cmdlog)
        hosts = list(net.hosts())
        sink_ip, srv_ip, probe_ip = str(hosts[1]), str(hosts[2]), str(hosts[3])
        isolation_check(netname, net, probe_ip, sink_image, cmdlog)
        resolv = args.out / "resolv.conf"
        resolv.write_text(f"nameserver {sink_ip}\noptions timeout:1 attempts:1\n")

        sh(["docker", "run", "-d", "--name", sink_name, "--network", netname, "--ip", sink_ip, "--read-only",
            "--cap-drop", "ALL", "--cap-add", "NET_BIND_SERVICE", "--security-opt", "no-new-privileges",
            "--pids-limit", "128", "--memory", "128m", "-e", f"SINK_IP={sink_ip}", sink_image, "python3", "/audit/sink.py"], log=cmdlog)
        for _ in range(50):
            if "sink-ready" in sh(["docker", "logs", sink_name], check=False).stdout:
                break
            time.sleep(0.2)

        env = {k: v.format(c=secret_canary) for k, v in FAKE_ENV.items()}
        env.update({"AUDIT_SECRET_CANARY": secret_canary, "AUDIT_MODE": args.ecosystem})
        if args.ecosystem == "npm":
            env["AUDIT_NPM_PACKAGE"] = args.package
            if args.bin:
                env["AUDIT_BIN"] = args.bin
        elif args.ecosystem == "pypi":
            env.update({"AUDIT_MODULE": args.module or "", "AUDIT_CONSOLE_SCRIPT": args.console_script or ""})
        else:
            env["AUDIT_RUN"] = args.run
        for e in args.env:
            k, _, v = e.partition("=")
            env[k] = v
        env_flags = [x for k, v in env.items() for x in ("-e", f"{k}={v}")]
        server_flags = ["--name", srv_name, "--network", netname, "--ip", srv_ip, "--dns", sink_ip,
                        "-v", f"{resolv}:/etc/resolv.conf:ro", *hardening(args), *env_flags]

        probe_opts = ["--canary", arg_canary, "--timeout", str(args.timeout), "--interval", "2"]
        if args.call_tools:
            probe_opts.append("--call-tools")
            for o in args.only:
                probe_opts += ["--only", o]

        if args.transport == "stdio":
            docker_cmd = ["docker", "run", "-i", "--rm", *server_flags, server_image, *args.server_arg]
            cmdlog.append(" ".join(docker_cmd).replace(secret_canary, "<secret-canary>"))
            r = subprocess.run([sys.executable, str(SCRIPTS / "mcp_probe.py"), "--out", str(args.out / "probe.json"),
                                "--stderr", str(args.out / "server-stderr.txt"), *probe_opts, "--stdio", "--", *docker_cmd],
                               capture_output=True, text=True, timeout=args.timeout * 20)
            print(printable(r.stdout.strip() or r.stderr.strip()[-500:]), flush=True)
        else:
            sh(["docker", "run", "-d", *server_flags, server_image, *args.server_arg], log=None)
            cmdlog.append(" ".join(["docker", "run", "-d", *server_flags, server_image, *args.server_arg]).replace(secret_canary, "<secret-canary>"))
            # Share the server's network namespace, so a server that (rightly) binds to
            # 127.0.0.1 can be reached, and the probe sits on the same closed network.
            url = f"http://127.0.0.1:{args.port}{args.path}"
            for attempt in range(15):
                time.sleep(1 if attempt else 2)
                r = sh(["docker", "run", "--rm", "--network", f"container:{srv_name}", "--read-only", "--cap-drop", "ALL",
                        "--security-opt", "no-new-privileges", "-v", f"{args.out}:/out", sink_image,
                        "python3", "/audit/mcp_probe.py", "--out", "/out/probe.json", "--url", url, "--auth-check", *probe_opts],
                       check=False, log=cmdlog if attempt == 0 else None, timeout=args.timeout * 20)
                probe = json.loads((args.out / "probe.json").read_text()) if (args.out / "probe.json").exists() else {}
                if probe.get("listings") or attempt == 14:
                    print(printable(r.stdout.strip() or r.stderr.strip()[-500:]), flush=True)
                    break
            (args.out / "server-stderr.txt").write_text(sh(["docker", "logs", srv_name], check=False).stdout[-200_000:] +
                                                        sh(["docker", "logs", srv_name], check=False).stderr[-200_000:])
        time.sleep(3)  # let late exfiltration attempts arrive
        (args.out / "sink.jsonl").write_text(sh(["docker", "logs", sink_name], check=False).stdout)
    finally:
        if not args.keep:
            for c in (srv_name, sink_name):
                sh(["docker", "rm", "-f", c], check=False)
            sh(["docker", "network", "rm", netname], check=False)
            for i in images:
                sh(["docker", "rmi", "-f", i], check=False)
        (args.out / "resolv.conf").unlink(missing_ok=True)

    summary = analyse(args.out, secret_canary, arg_canary, args.expect_host)
    summary["canaries"] = {"secret": "<redacted: fake credentials>", "argument": arg_canary}
    write_report(args.out, args, summary, cmdlog)
    worst = summary["findings"][0]["severity"] if summary["findings"] else "none"
    print(f"report: {args.out / 'sandbox-report.md'} (worst finding: {worst})")
    return 1 if worst in ("critical", "high") else 0


if __name__ == "__main__":
    sys.exit(main())
