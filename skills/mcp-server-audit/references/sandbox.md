# How the audit sandbox works

`scripts/sandbox/run_sandbox.py` runs an untrusted MCP server in Docker and records what it does. This page explains each layer, so you can tell the person exactly what they are agreeing to, and what a clean result does and doesn't mean.

## Layers

| Layer | How | Why |
| --- | --- | --- |
| Build | The package is installed into an image from the registry. npm runs with `--ignore-scripts`; pip with `--only-binary=:all:` (no source builds). | Fetching needs the network; running install code doesn't. No fake credentials exist at build time. |
| Network | An `--internal` Docker network with gateway mode `isolated` (or `inhibit_ipv4` on older Docker), so the host has no address on it. | No route to the internet, and no way to reach services listening on your machine. |
| Isolation check | Before the server starts, a throwaway container tries to connect to the host's bridge address and to two public addresses. Any connection, or even a "refused", stops the run. | Proves the network is closed on this machine, today, rather than assuming it. |
| DNS and sink | The server's only resolver is a sink container that answers every name with its own address and listens on common ports (21, 22, 25, 80, 443, 465, 587, 993, 3306, 5432, 6379, 8000, 8080, 8443, 9200, 27017). | Every lookup, TLS server name, HTTP request and first bytes of any other connection are logged. Nothing is forwarded. |
| Container | Read-only root; 64 MB `/tmp` and 16 MB home on tmpfs; user 10001; `--cap-drop ALL`; `no-new-privileges`; 256 processes; 768 MB memory; one CPU; no bind mounts of your files. | Limits what the code can change or reach even inside the sandbox. |
| Canaries | Fake SSH key, cloud keys, GitHub, npm and Slack tokens, a `.env`, and fake Cursor and Claude Desktop MCP configs, plus fake API keys in the environment. Each contains a random secret canary. Tool arguments carry a separate argument canary. | If the secret canary reaches the sink, the server read credentials and sent them out. If the argument canary does, it copied your inputs somewhere. |
| Probe | Lists definitions twice, optionally calls each tool with canary arguments, then lists again. HTTP servers are probed from inside the server's own network namespace. | Catches definitions that change between looks or after use (rug pulls). |
| Clean-up | Containers, the network and images are removed unless `--keep`. | Nothing is left running. |

The report ends with every Docker command that ran (with the secret canary redacted), so the person can see exactly what happened.

## What it cannot see

- **Patience and cunning.** Code that waits hours, checks for a sandbox, or only misbehaves for particular inputs or dates won't show up in a few minutes.
- **Hard-coded IP addresses.** Connections straight to an IP are blocked (no route), but not logged. The server's stderr sometimes shows the error.
- **Remote servers' own behaviour.** For a hosted server, the sandbox isn't involved: only the probe from outside.
- **A container, not a virtual machine.** The server shares your machine's kernel. A flaw in Docker or the kernel could let hostile code out; none is needed for the checks here to be useful, but for a server you already believe is malicious, run the audit inside a throwaway VM or cloud development environment. `mcp-guide doctor` says which kind of Docker you have (Docker Desktop runs containers inside its own VM; a rootless daemon limits an escape; a root daemon on Linux is the weakest), and `--runtime runsc` uses gVisor if it is installed.
- **Install-time code, if you allow it.** With `--allow-install-scripts` or `--allow-sdist`, package code runs during the build, which has network access. There are no credentials then, but it could still phone home.
- **Other versions.** The run covers the version you named.

## Requirements and troubleshooting

- Docker 28 or later is best (isolated gateway mode). Older versions use `inhibit_ipv4`; if neither works, the script refuses to run.
- Default images are `node:22-slim` and `python:3.13-slim`. Override with `--node-image` and `--python-image`, for example to use an internal mirror.
- Behind a TLS-intercepting proxy, pass the proxy's CA bundle with `--ca-cert` so the build can fetch packages.
- **audit-incomplete** means the probe couldn't list the server's tools. Check `server-stderr.txt` in the output folder: usually a missing `--server-arg`, a required `--env` setting, or the wrong transport or port.
- A server that needs a real API key to start can be given a dummy one with `--env`. If it refuses to start without a working key, the sandbox can't exercise it: say so in the report.
