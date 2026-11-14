# Quick start for developers

Copy, paste, go. Each section gives the exact commands, and a prompt to paste into your coding agent. The rest of the guide explains the why.

*As of 14 November 2026. Commands are for macOS and Linux shells.*

**You'll need:** git; Python 3.10 or later (for the skills' scripts); Node 22.12 or later (for the example server); Docker (only for running an untrusted server in the audit sandbox).

## 0. Get the guide (once)

```bash
git clone --depth 1 https://github.com/cafesecurity/mcp-security-guide ~/mcp-security-guide
```

To update later: `git -C ~/mcp-security-guide pull`.

## 1. Add the rules and skills to your server's repository

Run these in the root of the repository where you are building (or will build) an MCP server.

```bash
# The skills. Claude Code reads .claude/skills/; many other agents read .agents/skills/.
mkdir -p .claude/skills
cp -r ~/mcp-security-guide/skills/mcp-* .claude/skills/

# The build rules, under their own name so they don't overwrite yours.
cp ~/mcp-security-guide/AGENTS.md MCP-SECURITY-RULES.md

# Point your agent at them.
echo "Follow the MCP security rules in MCP-SECURITY-RULES.md." >> AGENTS.md   # most agents
echo "@MCP-SECURITY-RULES.md" >> CLAUDE.md                                    # Claude Code imports it

git add .claude/skills MCP-SECURITY-RULES.md AGENTS.md CLAUDE.md
git commit -m "Add MCP security rules and skills"
```

Start a new agent session so it picks them up. In Claude Code, `/skills` lists what loaded.

**Read before you trust.** The skills are instructions your agent follows and scripts it runs. They are short, standard-library Python; skim them first, as you would any dependency.

## 2. Building a new server

**Step 1: decide and threat model.** Fill in the brackets, then paste:

```text
Use the mcp-threat-model skill. I want to build an MCP server.
- What it's for: [one sentence]
- Who calls it: [our staff through agents we approve / our customers through their own agents]
- Where it runs: [local (STDIO) / remote (HTTP)]
- What it reads: [systems and data]
- What it changes: [nothing / list the actions]
- It must never: [for example "send anything outside the company"]
Draft THREATMODEL.draft.md. Don't write any code yet. Show me the [A] [B] [C] table,
anything that lights all three letters, and your NEEDS HUMAN questions.
```

Answer its questions, edit the draft, and save it as `THREATMODEL.md`. That file is yours, not the agent's.

**Step 2: build.** Paste:

```text
Build the MCP server described in THREATMODEL.md, following MCP-SECURITY-RULES.md.
Use TypeScript and the official MCP SDK, targeting the 2026-07-28 spec. The example at
https://github.com/cafesecurity/mcp-security-guide/tree/main/examples/ask-trevor shows the
patterns: token checks, tenant isolation, plain-text results tagged by source, a tool-definition
snapshot and the security tests.
Stop and ask me before deciding anything on the "Stop and ask a person first" list.
Write the tests from THREATMODEL.md and the guide's minimum test list, not from your code.
```

Swap TypeScript for Python if you prefer; the rules are the same.

**Step 3: review every change, in a fresh session.** Paste:

```text
Use the mcp-security-review skill on the changes since main. Report only; don't fix anything.
```

**Step 4: before each release.** Paste:

```text
Use the mcp-release-check skill. Write RELEASE-CHECK.md and stop. Don't tag or publish.
```

Then you tag and publish.

## 3. You already have a server

Do sections 1 and 2's review step, but start with the threat model of what exists:

```text
Use the mcp-threat-model skill on this existing MCP server. Draft THREATMODEL.draft.md from
the code, mark every MISSING control and test, and list your NEEDS HUMAN questions.
```

Then:

```text
Use the mcp-security-review skill on the whole server, not just a diff: review every file
under [src/]. Report only. List the tests from the guide's minimum test list that are missing.
```

## 4. Vetting someone else's server

Before you install or approve a server you didn't write. You don't need to add anything to a repository for this: work in an empty folder.

**With your agent.** Install the audit skill where your agent will find it, then paste:

```bash
mkdir -p ~/.claude/skills && cp -r ~/mcp-security-guide/skills/mcp-server-audit ~/.claude/skills/
mkdir -p ~/mcp-audits/[name] && cd ~/mcp-audits/[name]
```

```text
Use the mcp-server-audit skill to audit [package name] version [exact version] from
[npm / PyPI / repository URL / remote URL] before I install it. We'd use it in [agent] alongside
[other MCP servers], with access to [data and accounts]. The publisher should be [vendor, where
their official docs live]. Ask me before running or contacting anything.
```

The agent will ask before it builds the sandbox or calls a remote server. Answer yes only if you've read what it's about to do.

**By hand, without an agent.** For an npm package (PyPI: swap `npm` for `pypi` and use `--console-script NAME` or `--module NAME` in the sandbox step):

```bash
S=~/mcp-security-guide/skills/mcp-server-audit/scripts
mkdir -p ~/mcp-audits/example && cd ~/mcp-audits/example

# 1. Who publishes it? Downloads the files without installing or running them.
python3 $S/package_facts.py npm @vendor/mcp-server 1.4.2 --download pkg --json facts.json

# 2. What does the code do?
python3 $S/scan_code.py pkg/package-files --json code.json

# 3. What does it do when run? Docker sandbox: no internet, fake credentials, everything logged.
python3 $S/sandbox/run_sandbox.py --out sandbox --ecosystem npm --package @vendor/mcp-server --version 1.4.2 --call-tools

# 4. What do its tool descriptions tell the model?
python3 $S/scan_definitions.py sandbox/probe.json
```

Read `sandbox/sandbox-report.md`, then fill in the [report template](skills/mcp-server-audit/references/report-template.md). If the sandbox report says **audit-incomplete**, the server didn't start: check `sandbox/server-stderr.txt` (often it needs `--server-arg` or a dummy `--env` setting).

For a server the vendor hosts:

```bash
python3 $S/mcp_probe.py --out probe.json --url https://mcp.vendor.example/mcp --auth-check
python3 $S/scan_definitions.py probe.json
```

A hosted server should refuse that request with a 401. If it answers without a token, find out why before going further.

## 5. Try the example server

```bash
cd ~/mcp-security-guide/examples/ask-trevor
npm ci
npm test        # 50 tests: auth, isolation, hostile content, transport, snapshot, operations
npm run dev     # local only: prints test tokens for three sample users
```

Then read [`src/auth.ts`](examples/ask-trevor/src/auth.ts) and [`test/auth.test.ts`](examples/ask-trevor/test/auth.test.ts) side by side: that's the audience check, and the test that proves it.

## Where next

- The lifecycle, phase by phase: [README](README.md#the-lifecycle).
- What the spec requires, as a checklist: [reference/spec-checklist.md](reference/spec-checklist.md).
- The agent itself as a risk: [guide/coding-agents.md](guide/coding-agents.md).
