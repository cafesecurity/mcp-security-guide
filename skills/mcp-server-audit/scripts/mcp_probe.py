#!/usr/bin/env python3
"""A minimal MCP client for audits: list what a server exposes, twice, and
optionally call its tools with harmless canary arguments.

It never interprets what the server returns; it records it. Treat every string
in the output as untrusted data written by the server.

Transports
  --stdio -- CMD [ARGS...]   start a local server (use the sandbox for anything untrusted)
  --url URL                  a Streamable HTTP endpoint

Protocols
  Tries the 2025-era handshake (initialize) first, then the 2026-07-28 stateless
  form, so it works with most servers in use today.

Safety
  * --call-tools sends schema-valid dummy arguments containing a canary string to
    EVERY tool unless --only is given. Against a real remote service that can have
    real effects. Use it only inside the sandbox, or against a test account.
  * A bearer token is read from the environment variable named by --bearer-env,
    never from the command line, and is never written to the output. It is sent
    only over https (or to this machine), and redirects are never followed, so
    the token can't be passed on to another host.

Usage examples
  python3 mcp_probe.py --out probe.json --stdio -- node dist/index.js
  python3 mcp_probe.py --out probe.json --url https://mcp.example.com/mcp --auth-check
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

LEGACY_VERSION = "2025-11-25"
STATELESS_VERSION = "2026-07-28"
CLIENT_INFO = {"name": "mcp-security-guide-probe", "version": "1.0.0"}
MAX_TEXT = 8000


def clip(value, limit: int = MAX_TEXT):
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return s if len(s) <= limit else s[:limit] + f"…[{len(s) - limit} more characters]"


class RpcError(Exception):
    def __init__(self, payload):
        super().__init__(json.dumps(payload)[:500])
        self.payload = payload


# --- transports ---------------------------------------------------------------

class StdioTransport:
    def __init__(self, cmd: list[str], timeout: float, stderr_path: Path | None):
        self.timeout = timeout
        self.stderr_file = open(stderr_path, "wb") if stderr_path else subprocess.DEVNULL
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr_file)
        self.q: queue.Queue = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.notifications: list = []

    def _reader(self):
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.q.put(json.loads(line))
            except json.JSONDecodeError:
                self.q.put({"_unparsed": line[:2000].decode("utf-8", "replace")})
        self.q.put(None)

    def request(self, msg: dict, headers: dict | None = None) -> dict:
        self.proc.stdin.write((json.dumps(msg) + "\n").encode())
        self.proc.stdin.flush()
        deadline = time.time() + self.timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(f"no response to {msg.get('method')}")
            try:
                item = self.q.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"no response to {msg.get('method')}")
            if item is None:
                raise ConnectionError("server exited")
            if item.get("id") == msg.get("id") and ("result" in item or "error" in item):
                return item
            if "method" in item and "id" in item:
                # A request from the server (sampling, elicitation, roots): refuse it.
                self.notifications.append({"server_request": item.get("method")})
                self.proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": item["id"], "error": {"code": -32601, "message": "not supported by audit probe"}}) + "\n").encode())
                self.proc.stdin.flush()
            else:
                self.notifications.append(item)

    def notify(self, msg: dict, headers: dict | None = None):
        self.proc.stdin.write((json.dumps(msg) + "\n").encode())
        self.proc.stdin.flush()

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects: urllib would resend our headers, token included, to wherever the server points."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(_NoRedirect)
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def check_url(url: str, with_token: bool) -> str | None:
    """Return a reason to refuse this URL, or None."""
    u = urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return "the URL must start with https:// (or http:// for this machine)"
    if u.username or u.password:
        return "don't put credentials in the URL"
    if u.scheme == "http" and u.hostname not in LOOPBACK:
        return ("refusing to send a token over plain http to another machine" if with_token
                else "plain http to another machine: anyone on the path can read and change the answers. Use https")
    return None


class HttpTransport:
    def __init__(self, url: str, timeout: float, token: str | None, extra_headers: dict):
        self.url = url
        self.timeout = timeout
        self.token = token
        self.extra = extra_headers
        self.session_id: str | None = None
        self.notifications: list = []
        self.last_status: int | None = None

    def _post(self, msg: dict, headers: dict | None) -> tuple[int, dict, bytes]:
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **self.extra, **(headers or {})}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode(), headers=h, method="POST")
        try:
            with OPENER.open(req, timeout=self.timeout) as r:
                return r.status, dict(r.headers), r.read(4_000_000)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read(200_000)

    def request(self, msg: dict, headers: dict | None = None) -> dict:
        status, hdrs, body = self._post(msg, headers)
        self.last_status = status
        if 300 <= status < 400:
            raise ConnectionError(f"HTTP {status}: the server redirected to {clip(hdrs.get('Location') or hdrs.get('location') or '?', 200)}; not followed")
        sid = hdrs.get("Mcp-Session-Id") or hdrs.get("mcp-session-id")
        if sid:
            self.session_id = sid
        ctype = (hdrs.get("Content-Type") or hdrs.get("content-type") or "").lower()
        if "text/event-stream" in ctype:
            for block in body.decode("utf-8", "replace").split("\n\n"):
                data = "\n".join(l[5:].lstrip() for l in block.splitlines() if l.startswith("data:"))
                if not data:
                    continue
                try:
                    item = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if item.get("id") == msg.get("id"):
                    return item
                self.notifications.append(item)
            raise ConnectionError(f"HTTP {status}: no response in event stream")
        try:
            item = json.loads(body or b"{}")
        except json.JSONDecodeError:
            raise ConnectionError(f"HTTP {status}: {body[:200]!r}")
        if status >= 400 and "error" not in item:
            raise ConnectionError(f"HTTP {status}: {clip(item, 300)}")
        return item

    def notify(self, msg: dict, headers: dict | None = None):
        self._post(msg, headers)

    def close(self):
        pass


# --- client -------------------------------------------------------------------

class Client:
    def __init__(self, transport):
        self.t = transport
        self.next_id = 1
        self.mode = None
        self.protocol = None
        self.server_info = None
        self.instructions = None
        self.capabilities = {}

    def _msg(self, method: str, params: dict | None = None) -> dict:
        m = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        self.next_id += 1
        params = dict(params or {})
        if self.mode == "stateless":
            params["_meta"] = {
                "io.modelcontextprotocol/protocolVersion": STATELESS_VERSION,
                "io.modelcontextprotocol/clientInfo": CLIENT_INFO,
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        m["params"] = params
        return m

    def _headers(self, method: str, params: dict | None) -> dict:
        if self.mode != "stateless":
            return {"MCP-Protocol-Version": self.protocol} if self.protocol else {}
        h = {"MCP-Protocol-Version": STATELESS_VERSION, "Mcp-Method": method}
        name = (params or {}).get("name") or (params or {}).get("uri")
        if name:
            h["Mcp-Name"] = name
        return h

    def call(self, method: str, params: dict | None = None) -> dict:
        msg = self._msg(method, params)
        resp = self.t.request(msg, self._headers(method, params))
        if "error" in resp:
            raise RpcError(resp["error"])
        return resp.get("result", {})

    def connect(self) -> None:
        errors = []
        try:
            self.mode = "legacy"
            res = self.call("initialize", {"protocolVersion": LEGACY_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO})
            self.protocol = res.get("protocolVersion")
            self.server_info = res.get("serverInfo")
            self.instructions = res.get("instructions")
            self.capabilities = res.get("capabilities") or {}
            self.t.notify({"jsonrpc": "2.0", "method": "notifications/initialized"}, self._headers("notifications/initialized", None))
            return
        except (RpcError, ConnectionError, TimeoutError) as e:
            errors.append(f"initialize: {e}")
        self.mode = "stateless"
        self.protocol = STATELESS_VERSION
        try:
            self.call("tools/list")
            return
        except (RpcError, ConnectionError, TimeoutError) as e:
            errors.append(f"stateless tools/list: {e}")
        raise ConnectionError("could not talk to the server: " + "; ".join(errors))

    def list_all(self, method: str, key: str) -> list:
        items, cursor = [], None
        for _ in range(50):
            res = self.call(method, {"cursor": cursor} if cursor else {})
            items += res.get(key) or []
            cursor = res.get("nextCursor")
            if not cursor:
                break
        return items

    def listing(self) -> dict:
        out = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        for method, key in (("tools/list", "tools"), ("prompts/list", "prompts"), ("resources/list", "resources"), ("resources/templates/list", "resourceTemplates")):
            try:
                out[key] = self.list_all(method, key)
            except (RpcError, ConnectionError, TimeoutError) as e:
                out[key] = []
                out.setdefault("errors", {})[method] = clip(str(e), 300)
        return out


# --- canary arguments -------------------------------------------------------------

def dummy_for(schema: dict, canary: str, depth: int = 0):
    if depth > 4 or not isinstance(schema, dict):
        return canary
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    if "const" in schema:
        return schema["const"]
    if "default" in schema:
        return schema["default"]
    for key in ("anyOf", "oneOf"):
        if schema.get(key):
            return dummy_for(schema[key][0], canary, depth + 1)
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if t == "string":
        fmt = schema.get("format")
        if fmt == "email":
            return f"{canary.lower()}@audit.invalid"
        if fmt in ("uri", "url"):
            return f"https://audit.invalid/{canary}"
        if fmt == "date":
            return "2026-01-01"
        if fmt == "date-time":
            return "2026-01-01T00:00:00Z"
        s = canary
        mx = schema.get("maxLength")
        return s[:mx] if isinstance(mx, int) else s
    if t in ("integer", "number"):
        lo = schema.get("minimum", schema.get("exclusiveMinimum", 0))
        return int(lo) + (1 if "exclusiveMinimum" in schema else 0) if t == "integer" else float(lo)
    if t == "boolean":
        return False
    if t == "array":
        return [dummy_for(schema.get("items") or {"type": "string"}, canary, depth + 1)] if schema.get("minItems", 0) > 0 else []
    if t == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        req = schema.get("required") or list(props)[:1]
        return {k: dummy_for(props.get(k, {}), canary, depth + 1) for k in req if k in props}
    return canary


# --- auth check for remote servers ---------------------------------------------------

def auth_check(url: str, timeout: float) -> dict:
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    out: dict = {}
    for candidate in (f"/.well-known/oauth-protected-resource{path}", "/.well-known/oauth-protected-resource"):
        u = urlunsplit((parts.scheme, parts.netloc, candidate, "", ""))
        try:
            with OPENER.open(u, timeout=timeout) as r:
                out["protected_resource_metadata"] = {"url": u, "status": r.status, "body": json.loads(r.read(200_000) or b"{}")}
                break
        except Exception as e:  # noqa: BLE001
            out.setdefault("prm_attempts", []).append({"url": u, "error": clip(str(e), 200)})
    req = urllib.request.Request(url, data=b'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}',
                                 headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}, method="POST")
    try:
        with OPENER.open(req, timeout=timeout) as r:
            out["unauthenticated_request"] = {"status": r.status, "note": "server answered WITHOUT a token", "body": clip(r.read(20_000).decode("utf-8", "replace"), 2000)}
    except urllib.error.HTTPError as e:
        out["unauthenticated_request"] = {"status": e.code, "www_authenticate": e.headers.get("WWW-Authenticate")}
    except Exception as e:  # noqa: BLE001
        out["unauthenticated_request"] = {"error": clip(str(e), 300)}
    return out


# --- main --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--url")
    ap.add_argument("--bearer-env", help="name of an environment variable holding a TEST-account bearer token")
    ap.add_argument("--header", action="append", default=[], help="extra HTTP header, NAME:VALUE (not for secrets)")
    ap.add_argument("--auth-check", action="store_true", help="HTTP only: fetch protected resource metadata and try a request without a token")
    ap.add_argument("--repeat", type=int, default=2, help="how many times to list definitions (default 2)")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between listings")
    ap.add_argument("--call-tools", action="store_true", help="call tools with canary arguments (sandbox or test account only)")
    ap.add_argument("--only", action="append", default=[], help="call only these tools")
    ap.add_argument("--canary", default=None, help="canary string to put in arguments (default: random)")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--stderr", type=Path, help="stdio only: save the server's stderr here")
    ap.add_argument("--stdio", action="store_true", help="start a local server: the command follows --")
    argv = sys.argv[1:]
    cmd: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, cmd = argv[:i], argv[i + 1:]
    args = ap.parse_args(argv)

    if bool(args.url) == bool(args.stdio) or (args.stdio and not cmd):
        ap.error("give exactly one of --url URL or --stdio -- CMD [ARGS...]")
    canary = args.canary or f"AUDITCANARY{secrets.token_hex(6).upper()}"
    record: dict = {"target": args.url or " ".join(cmd),
                    "canary": canary, "listings": [], "calls": [], "errors": []}

    if args.url:
        token = os.environ.get(args.bearer_env) if args.bearer_env else None
        if args.bearer_env and not token:
            ap.error(f"environment variable {args.bearer_env} is empty")
        problem = check_url(args.url, bool(token))
        if problem:
            ap.error(problem)
        if args.call_tools and not args.only and urlsplit(args.url).hostname not in LOOPBACK:
            ap.error("calling tools on a live server can have real effects: name each tool to call with --only")
        headers = dict(h.split(":", 1) for h in args.header)
        if args.auth_check:
            record["auth_check"] = auth_check(args.url, args.timeout)
        transport = HttpTransport(args.url, args.timeout, token, {k.strip(): v.strip() for k, v in headers.items()})
    else:
        transport = StdioTransport(cmd, args.timeout, args.stderr)

    client = Client(transport)
    try:
        client.connect()
        record.update({"answered_without_token": bool(args.url) and not args.bearer_env,
                       "mode": client.mode, "protocol": client.protocol, "serverInfo": client.server_info,
                       "instructions": client.instructions, "capabilities": client.capabilities})
        for i in range(max(1, args.repeat)):
            if i:
                time.sleep(args.interval)
            record["listings"].append(client.listing())
        if args.call_tools:
            tools = record["listings"][-1].get("tools") or []
            for t in tools:
                name = t.get("name")
                if args.only and name not in args.only:
                    continue
                arguments = dummy_for(t.get("inputSchema") or {"type": "object"}, canary)
                entry = {"tool": name, "arguments": arguments}
                try:
                    res = client.call("tools/call", {"name": name, "arguments": arguments})
                    entry["result"] = clip(res)
                except (RpcError, ConnectionError, TimeoutError) as e:
                    entry["error"] = clip(str(e), 1000)
                record["calls"].append(entry)
            # List again: some servers change their definitions only after being used.
            record["listings"].append(client.listing())
    except (ConnectionError, TimeoutError, OSError) as e:
        record["errors"].append(clip(str(e), 1000))
    finally:
        record["notifications"] = [clip(n, 1000) for n in transport.notifications[:50]]
        transport.close()

    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=True))
    print(f"wrote {args.out}: {len(record['listings'])} listings, {len(record['calls'])} calls, {len(record['errors'])} errors")
    return 0 if not record["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
