# Skills

Four [Agent Skills](https://agentskills.io/) that put this guide to work inside a coding agent. Each is a folder with a `SKILL.md`; agents that support the format load a skill when your request matches its description.

*As of 13 November 2026. Licence: MIT.*

| Skill | When | What it does | Needs |
| --- | --- | --- | --- |
| [`mcp-threat-model`](mcp-threat-model/SKILL.md) | Before you build; whenever tools, scopes or upstream systems change | Drafts `THREATMODEL.draft.md`: tools, [A] [B] [C] letters, what outsiders can write, what it reaches, missing controls and tests | Nothing |
| [`mcp-security-review`](mcp-security-review/SKILL.md) | On every change, ideally in a fresh session | Reviews a diff against the checklists and the spec; flags tool-definition changes and missing tests | git; Python for the definition scan |
| [`mcp-release-check`](mcp-release-check/SKILL.md) | Before you tag a release | Compares tool definitions with the last release, checks the version, changelog and release workflow, drafts release notes | git |
| [`mcp-server-audit`](mcp-server-audit/SKILL.md) | Before anyone installs or approves someone else's server | Publisher checks, code and definition scans, remote sign-in checks, and an optional run in a locked-down Docker sandbox with fake credentials. Writes a report with a recommendation | Python; npm for npm packages; Docker for the sandbox |

None of them publishes, pushes, or approves anything. Each produces a file that a person reviews.

## Install

Copy the folders you want into your agent's skills directory. For Claude Code that is `.claude/skills/` in the project, or `~/.claude/skills/` for all projects. Many other agents read `.agents/skills/`; check your agent's documentation.

```bash
git clone https://github.com/cafesecurity/mcp-security-guide
mkdir -p .claude/skills
cp -r mcp-security-guide/skills/mcp-* .claude/skills/
```

**Read a skill before you install it.** A skill is instructions your agent will follow and scripts it may run, which makes it part of your supply chain, just like an MCP server. These are short, standard-library Python, and have no dependencies.

## The audit sandbox

`mcp-server-audit` can run an untrusted server in Docker on an internal network where the host has no address, with a read-only file system, no capabilities, fake credentials, and a sink that logs every DNS lookup and connection. It checks the network is closed before starting the server. See [how the sandbox works](mcp-server-audit/references/sandbox.md), including what it can't see.

Tested with these fixtures, which CI runs on every change:

- [`tests/fixtures/evil-server`](tests/fixtures/evil-server/server.py): a deliberately malicious server (a poisoned description, a rug pull, and stealing credentials by DNS and HTTP to `.example` hosts). The sandbox reports the stolen fake credentials as critical.
- [`tests/fixtures/plain-server`](tests/fixtures/plain-server/server.py): a well-behaved server. The sandbox reports nothing.

## Tests

```bash
python3 -m unittest discover -s skills/tests -v                    # scanners and probe
AUDIT_SANDBOX_TEST=1 python3 -m unittest discover -s skills/tests  # plus the Docker sandbox
python3 scripts/check_skills.py                                     # SKILL.md format
```
