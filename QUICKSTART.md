# Quick start for developers

Three commands to set up, then short prompts for your coding agent. The agent does the writing; you answer its questions and make the decisions. The rest of the guide explains the why.

*As of 14 November 2026. Commands are for macOS and Linux shells.*

**You'll need:** git and Python 3.10 or later. Node 22.12 or later for the example server and npm audits; Docker only for running someone else's server in the audit sandbox. `mcp-guide doctor` checks all of these.

## 1. Set up (once per repository)

```bash
git clone --depth 1 https://github.com/cafesecurity/mcp-security-guide ~/mcp-security-guide
alias mcp-guide=~/mcp-security-guide/bin/mcp-guide     # add to your shell profile to keep it

cd path/to/your-server-repo
mcp-guide init
git add -A && git commit -m "Add MCP security rules and skills"
```

`init` copies the four skills to `.claude/skills/` (Claude Code) or `.agents/skills/` (most other agents; pick with `--agent`), adds the build rules as `MCP-SECURITY-RULES.md`, and adds a marked pointer line to your `AGENTS.md` (and `CLAUDE.md`). It doesn't change anything else, and running it twice is harmless. It's one standard-library Python file: [read it](bin/mcp-guide) before you run it.

Then **start a new agent session** so it picks them up. In Claude Code, `/skills` lists what loaded.

| Later | Command |
| --- | --- |
| What's installed, and what you've changed | `mcp-guide status` |
| Get newer rules and skills (keeps your edits) | `git -C ~/mcp-security-guide pull`, read what changed, then `mcp-guide update` |
| Take it all out again | `mcp-guide remove` |

Nothing updates itself: you choose when to pull, and `git diff` shows what `update` changed.

## 2. Building a new server

**Threat model first.** Paste, with your own sentence:

```text
Use the mcp-threat-model skill. I want to build an MCP server that [lets our staff search the policy wiki].
```

You don't fill in a template. The agent asks you about six short questions (who calls it, local or remote, what it reads and changes, what it must never do, who owns the threat model), drafts `THREATMODEL.draft.md`, then shows you the risky combinations and asks about anything it couldn't work out. Answer, correct it, and reply **approve**: it saves `THREATMODEL.md`. That file is yours: commit it.

**Build.** Paste:

```text
Build the MCP server in THREATMODEL.md, in TypeScript with the official MCP SDK.
```

The rules already tell it the spec version, the patterns to copy from the [example server](examples/ask-trevor/), to write tests from the threat model rather than its own code, and to stop and ask you before anything on the "ask a person first" list. Swap TypeScript for Python if you prefer.

**Review every change, in a fresh session.** Paste:

```text
Use the mcp-security-review skill on the changes since main.
```

It reports and doesn't fix. You decide what to change.

**Before each release.** Paste:

```text
Use the mcp-release-check skill.
```

It writes `RELEASE-CHECK.md` and draft release notes. You tag and publish.

## 3. You already have a server

Run `mcp-guide init` in its repository, then paste:

```text
Use the mcp-threat-model skill on this existing server.
```

It drafts from the code, so expect fewer questions and a list of MISSING controls and tests. Once you've approved it:

```text
Use the mcp-security-review skill on the whole server, not just a diff.
```

## 4. Vetting someone else's server

Before you install or approve a server you didn't write. No repository needed.

```bash
mcp-guide audit npm  @vendor/mcp-server 1.4.2       # or: pypi NAME VERSION
mcp-guide audit remote https://mcp.vendor.example/mcp
```

For a package, it checks who publishes it, downloads and scans the code without running it, then **asks** before running it in the Docker sandbox: no network, a read-only file system, fake credentials, and every connection attempt logged. It writes everything to `~/mcp-audits/NAME-VERSION/`, with `SUMMARY.md` on top and a `REPORT.md` template to fill in. For a hosted server, it checks sign-in, and lists the tools if you give it a test account's token (`-- --bearer-env VAR`).

To have your agent check the findings and write the report, start it in that folder and paste the line `mcp-guide audit` prints at the end. Or, to have the agent do the whole audit from the start (it asks before each step that runs anything):

```text
Read ~/mcp-security-guide/skills/mcp-server-audit/SKILL.md and use it to audit [package] [version]
before I install it. We'd use it in [agent] alongside [other servers], with access to [data and accounts].
```

If the summary says **audit-incomplete**, the server didn't start in the sandbox: see `sandbox/server-stderr.txt` (it often needs an argument or a dummy setting: `-- --server-arg stdio` or `-- --env API_KEY=dummy`).

## 5. Try the example server

```bash
cd ~/mcp-security-guide/examples/ask-trevor
npm ci
npm test        # 50 tests: auth, isolation, hostile content, transport, snapshot, operations
npm run dev     # local only: prints test tokens for three sample users
```

Then read [`src/auth.ts`](examples/ask-trevor/src/auth.ts) and [`test/auth.test.ts`](examples/ask-trevor/test/auth.test.ts) side by side: that's the audience check, and the test that proves it.

## Without the setup script

`mcp-guide` only copies files and runs the audit scripts in order. To do it by hand:

```bash
G=~/mcp-security-guide
mkdir -p .claude/skills && cp -r $G/skills/mcp-* .claude/skills/   # or .agents/skills/
cp $G/AGENTS.md MCP-SECURITY-RULES.md
echo "Follow the MCP security rules in MCP-SECURITY-RULES.md." >> AGENTS.md
echo "@MCP-SECURITY-RULES.md" >> CLAUDE.md                          # Claude Code only
```

And an audit, step by step (PyPI: swap `npm` for `pypi`, and add `--console-script NAME` or `--module NAME` to the sandbox step):

```bash
S=~/mcp-security-guide/skills/mcp-server-audit/scripts
mkdir -p ~/mcp-audits/example && cd ~/mcp-audits/example
python3 $S/package_facts.py npm @vendor/mcp-server 1.4.2 --download pkg --json facts.json   # publisher; downloads without running
python3 $S/scan_code.py pkg/package-files --json code.json                                  # what the code does
python3 $S/sandbox/run_sandbox.py --out sandbox --ecosystem npm --package @vendor/mcp-server --version 1.4.2 --call-tools
python3 $S/scan_definitions.py sandbox/probe.json                                           # what it tells the model
python3 $S/mcp_probe.py --out probe.json --url https://mcp.vendor.example/mcp --auth-check  # a hosted server
```

## Where next

- The lifecycle, phase by phase: [README](README.md#the-lifecycle).
- What the spec requires, as a checklist: [reference/spec-checklist.md](reference/spec-checklist.md).
- The agent itself as a risk: [guide/coding-agents.md](guide/coding-agents.md).
