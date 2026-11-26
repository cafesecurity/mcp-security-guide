# Quick start for developers

Three commands to set up, then short prompts for your coding agent. The agent does the writing and the legwork; you answer its questions and make the security decisions, and the set-up makes sure you are actually asked. The rest of the guide explains the why.

*As of 14 November 2026. Commands are for macOS and Linux shells.*

**You'll need:** git and Python 3.10 or later. Node 22.12 or later for the example server and npm audits; Docker only for running someone else's server in the audit sandbox. `mcp-guide doctor` checks all of these, and tells you how strong a boundary your Docker gives.

## 1. Set up (once per repository)

```bash
git clone --depth 1 https://github.com/cafesecurity/mcp-security-guide ~/mcp-security-guide
alias mcp-guide=~/mcp-security-guide/bin/mcp-guide     # add to your shell profile to keep it

cd path/to/your-server-repo
mcp-guide init --dry-run      # shows what it would write; writes nothing
mcp-guide init
git add -A && git commit -m "Add MCP security rules and skills"
```

`init` is one standard-library Python file: [read it](bin/mcp-guide) before you run it. It:

- copies the four skills to `.claude/skills/` (Claude Code) or `.agents/skills/` (most other agents; pick with `--agent`);
- adds the build rules as `MCP-SECURITY-RULES.md`, and one marked pointer line to your `AGENTS.md` (and `CLAUDE.md`);
- for Claude Code, adds **guardrails** to `.claude/settings.json` (on by default; your existing settings are kept; skip with `--no-guardrails`):

  | The agent must ask you before it | The agent can't |
  | --- | --- |
  | saves `THREATMODEL.md` | publish a package or push an image (`npm publish`, `twine upload`, `docker push` and the like): you run those |
  | edits the rules, the tool snapshot, these guardrails, the installed skills or `CODEOWNERS` | read `.env` files, `.npmrc`, `.pypirc`, `*.pem` or SSH keys, in any folder (this includes `.env.example`) |
  | adds a dependency (`npm install NAME`, `pip install`, `uv add` and the like; `npm ci` is unaffected) | |
  | adds an MCP server to itself (`.mcp.json`) | |
  | creates a tag or a release, pushes tags, or force-pushes | |
  | runs an audit, or `mcp-guide init`, `update`, `remove`, `protect` or `snapshot update` | |

To see the guardrails work before you rely on them, run `python3 ~/mcp-security-guide/scripts/check_guardrails_live.py`: it sets up a scratch repository, has Claude Code attempt 27 actions, and prints which were stopped (one short session of your Claude usage).

It never overwrites a file it didn't put there, never writes outside the repository, and running it twice is harmless. Then **start a new agent session** so it picks the skills up. In Claude Code, `/skills` lists what loaded.

**Recommended:** make changes to the security files need a named person's review.

```bash
mcp-guide protect --owner @your-github-name     # or @your-org/security-team
```

That adds code owners for the threat model, the rules, the tool snapshot and the agent's own instructions. It only *blocks* merges once you turn on "Require review from Code Owners" in your branch protection; that switch is yours.

| Later | Command |
| --- | --- |
| What's installed, and what has changed | `mcp-guide status` |
| Fail CI if someone edited the rules, skills or guardrails | `mcp-guide status --strict` |
| Get newer rules and skills (keeps your edits) | `git -C ~/mcp-security-guide pull`, read what changed, then `mcp-guide update` |
| Take it all out again | `mcp-guide remove` |

Nothing updates itself: you choose when to pull, and `git diff` shows what `update` changed.

### Who decides what

| The agent does | You decide |
| --- | --- |
| Interviews you and writes the threat model | Whether it's right: you reply **approve**, and (with guardrails) OK the save |
| Writes the code and the tests | Identity, scopes, token checks, new tools that act, network exposure: it stops and asks |
| Reviews each change and lists findings | What to fix |
| Records what your tools tell the model, and spots changes | Whether a changed tool definition ships |
| Prepares the release check and notes | Tagging and publishing |
| Runs the audit steps and drafts the report | Each risk the audit takes (by name), and approve or reject |

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

**Freeze what your tools tell the model.** Once it runs:

```bash
mcp-guide snapshot update -- node dist/index.js      # the command that starts YOUR server; writes mcp-tools.snapshot.json
git add mcp-tools.snapshot.json && git commit -m "Tool definition snapshot"
```

and in CI, after the build (clone the guide there at the commit you reviewed, the one `mcp-guide status` shows):

```bash
git clone https://github.com/cafesecurity/mcp-security-guide /tmp/guide && git -C /tmp/guide checkout <commit>
/tmp/guide/bin/mcp-guide snapshot check -- node dist/index.js
/tmp/guide/bin/mcp-guide status --strict
```

From then on, any change to a tool's name, description, parameters or annotations fails the build and lists what changed, until a person has looked at it and re-run `snapshot update`. It also warns about wording in your own descriptions that an auditor would flag. For an HTTP server that's already running locally: `--url http://127.0.0.1:3000/mcp` instead of the command.

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

It drafts from the code, so expect fewer questions and a list of MISSING controls and tests. Once you've approved it, take the snapshot (section 2), then:

```text
Use the mcp-security-review skill on the whole server, not just a diff.
```

## 4. Vetting someone else's server

Before you install or approve a server you didn't write. No repository needed.

```bash
mcp-guide audit npm  @vendor/mcp-server 1.4.2       # or: pypi NAME VERSION
mcp-guide audit remote https://mcp.vendor.example/mcp
```

By default this is safe to run on anything: it reads the registry's facts about the package (publisher, age, install scripts) and scans the downloaded files **without running any of the package's code**. Everything beyond that is a named risk. At a terminal it explains each one and asks; anywhere else (a script, an agent) it's declined unless you pass `--accept NAME`:

| Risk | What you'd be allowing | What could go wrong |
| --- | --- | --- |
| `sandbox` | The server's code is built and run in Docker: no network, read-only, fake credentials, none of your files | A container isn't a VM: a Docker or kernel flaw could let hostile code out. For a server you already suspect, use a throwaway VM |
| `call-tools` | Its tools are called inside the sandbox with dummy arguments | More of its code runs (still sandboxed). This is what shows what the tools really do |
| `install-scripts`, `sdist` | Its install or build code runs during the build, with internet access | It can fetch and run anything in the build container. Only if it won't start otherwise |
| `remote` | Requests go from your machine to the server's URL, with no credentials | Its operator sees your IP address |
| `token` | A bearer token (`--token-env VAR`) is sent to the server | The operator can use it as you until it expires. Test accounts only |
| `remote-calls` | Tools you name (`-- --only TOOL`) are called on the live server | Real effects on that account |

`mcp-guide risks` prints the same list. A typical run for a package you have no reason to distrust:

```bash
mcp-guide audit npm @vendor/mcp-server 1.4.2 --accept sandbox,call-tools --expect-repo github.com/vendor/mcp-server
```

Each run writes to a fresh folder, `~/mcp-audits/NAME-VERSION/`, with `SUMMARY.md` on top: the worst finding, what was **not covered**, which risks you accepted, and a `REPORT.md` template. It never offers: real credentials in the sandbox, running the server outside it, a token over plain http or across a redirect, or calling every tool on a live server.

**With your agent.** To have it check the findings and draft the report, start it in the audit folder and paste the line `mcp-guide audit` prints at the end. Or to have it drive the audit:

```text
Read ~/mcp-security-guide/skills/mcp-server-audit/SKILL.md and use it to audit [package] [version]
before I install it. We'd use it in [agent] alongside [other servers], with access to [data and accounts].
```

The skill tells the agent to run the safe steps, show you what they found, and ask you about each risk by name; it must not add `--accept` on its own, and with the guardrails from section 1, Claude Code shows you every audit command before it runs. The text an audited server produces is written to steer AI agents: the summary marks it as untrusted, and the agent is told to treat any instruction in it as a finding. Approving or rejecting the server is your call.

If the summary says **audit-incomplete**, the server didn't start in the sandbox: see `sandbox/server-stderr.txt` (it often needs an argument or a dummy setting: `-- --server-arg stdio` or `-- --env API_KEY=dummy`; never a real key).

## 5. Try the example server

```bash
cd ~/mcp-security-guide/examples/ask-trevor
npm ci
npm test        # 54 tests: auth, isolation, hostile content, transport, snapshot, operations
npm run dev     # local only: prints test tokens for three sample users
```

Then read [`src/auth.ts`](examples/ask-trevor/src/auth.ts) and [`test/auth.test.ts`](examples/ask-trevor/test/auth.test.ts) side by side: that's the audience check, and the test that proves it.

## What this set-up can't do

- The guardrails are Claude Code permission rules: they cover the agent's own file and shell tools, and anyone who can edit the repository can remove them (`status --strict` and code owners make that visible). They match command text, so they are a prompt at the usual door rather than a wall: the secrets block stops the agent's file reader, not `cat .env` in a shell, and a tag pushed by name alone isn't caught (creating the tag is). Keep real secrets off the machine the agent works on. For other agents, `init` installs instructions only; use that agent's own permission settings.
- Code owners do nothing until branch protection requires their review.
- The audit shows what a server did in one run of one version. A clean result is not proof of safety, and it can't see what a remote server does with your data.
- `mcp-guide` installs whatever is in your copy of the guide. Pull deliberately, and read what changed: these files instruct your agent.

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
python3 $S/sandbox/run_sandbox.py --out sandbox --ecosystem npm --package @vendor/mcp-server --version 1.4.2 --call-tools   # RUNS it, sandboxed
python3 $S/scan_definitions.py sandbox/probe.json                                           # what it tells the model
python3 $S/mcp_probe.py --out probe.json --url https://mcp.vendor.example/mcp --auth-check  # a hosted server: contacts it
```

## Where next

- The lifecycle, phase by phase: [README](README.md#the-lifecycle).
- What the spec requires, as a checklist: [reference/spec-checklist.md](reference/spec-checklist.md).
- The agent itself as a risk, and how the guardrail layers fit: [guide/coding-agents.md](guide/coding-agents.md).
