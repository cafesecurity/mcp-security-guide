# Changelog

## 1.0.1 — 27 November 2026

Fixes for GitHub code scanning (CodeQL) alerts.

- Ask Trevor: `plainText` removed HTML tags and comments in one pass, so input such as `<<b>script>` left a tag behind once the inner one was removed. Tags and comments are now replaced with a space, repeatedly, so the pieces can't join up again, and any `<` still left becomes `‹`, so nothing can open markup (an unclosed `<!--` or `<script`, say). Tests cover each case.
- Audit sandbox: the logging sink listened on every interface of its container. It now listens only on its own address on the sandbox's closed network.
- Not changed: the alert on `sandbox/canaries.py` ("clear-text storage of sensitive information") is about the deliberately fake credentials the sandbox plants so it can tell if a server steals them. It is dismissed as a false positive.

## 1.0 — 24 November 2026

All sources in `reference/sources.md` re-checked on 24 November 2026; see its corrections table.

- MITRE ATLAS: poisoned agent tools are now AML.T0115.002, Publish Poisoned AI Artifacts: AI Agent Tools (ATLAS release 2026.07 replaced AML.T0104). The framework map and the Release stage use the new ID, checked against ATLAS data release 2026.10.
- Release stage: OX Security's marketplace test used a harmless proof-of-concept server; the text no longer calls it malicious.
- Deploy and operate: the NCSC point about noisy AI-driven activity is limited to frontier models released before March 2026, as the NCSC put it.
- Sources: OWASP's Agentic Top 10 and LLM Top 10 2026 are now checked against OWASP's own pages; the package-hallucination figures cite the USENIX paper rather than a secondary note; NIST's overlay project link follows its rename to COSIS; the GitHub allow-list changelog link uses its 6 August date.

## 0.9 — 24 November 2026

First tagged version. The sources in `reference/sources.md` were last checked on 13–14 November 2026; they will all be re-checked before 1.0.

- Skills: `mcp-threat-model`, `mcp-security-review`, `mcp-release-check` (replacing `prompts/`), and `mcp-server-audit` for vetting third-party servers, with a Docker sandbox, fake-credential canaries, a logging network sink and tested fixtures.
- README links the "MCP Security: Zero to Hero" playlist.
- QUICKSTART.md: exact commands and paste-in prompts for adding the rules and skills, building, reviewing, releasing, and auditing someone else's server.
- `bin/mcp-guide`, a standard-library setup script: `init`, `status`, `update` and `remove` add and maintain the rules and skills in a repository (keeping local edits, never updating itself), `doctor` checks prerequisites, and `audit` runs the audit scripts in order, asking before the sandbox, and writes `SUMMARY.md`.
- `mcp-threat-model` 1.1.0: the agent interviews the person, drafts, asks about the gaps, and saves `THREATMODEL.md` on explicit approval. Prompts in the quick start are now one line.
- The audit sandbox saves the full Docker build log when a build fails.
- Security pass on `mcp-guide` and the audit scripts (14 Nov):
  - Audits are secure by default. Each step that runs or contacts someone else's code is a named risk (`sandbox`, `call-tools`, `install-scripts`, `sdist`, `remote`, `token`, `remote-calls`), explained at a prompt or accepted with `--accept NAME`, and recorded in `SUMMARY.md` and `run.json`. The blanket `--yes` is gone; risky options can no longer be passed through after `--`. `mcp-guide risks` lists them.
  - Fixed: a doctored `.mcp-security-guide.json` or a link in a repository could make `update --force` or `remove --force` write or delete files outside it. The manifest is now validated and links out of the repository are refused.
  - Fixed: package names were passed to npm and pip unchecked, so a URL, git address or option could be audited in place of a registry package. Names and exact versions only.
  - Fixed: the probe followed redirects, which could pass a bearer token to another host. Redirects are never followed; a token is never sent over plain http; tools on a live server are called only when named.
  - Fixed: a local checkout's links were followed when copying it into the sandbox build, and `.npmrc`-style credential files were copied.
  - Text from packages and servers is escaped before it reaches the terminal or `SUMMARY.md`, which now marks it as untrusted for any agent that reads it. Every audit run gets a fresh folder. `SUMMARY.md` lists what was not covered.
  - `doctor` reports how strong Docker's boundary is here (Docker Desktop VM, rootless, or shared kernel); the sandbox accepts `--runtime runsc`.
- Guardrails: `mcp-guide init` adds Claude Code permission rules so the agent must ask before saving `THREATMODEL.md`, editing the rules or the tool snapshot, publishing, or running an audit, and can't read `.env` (`--no-guardrails` to skip, `--dry-run` to preview). `mcp-guide protect --owner` adds code owners for the security files. `mcp-guide status --strict` fails when rules, skills or guardrails were changed.
- Guardrail list settled (14 Nov): publishing is blocked rather than asked; the agent must ask before editing its own guardrails, the installed skills, `CODEOWNERS` or `.mcp.json`, before adding a dependency, and before creating or pushing tags or force-pushing; the secrets block covers every `.env*` file and common key files in any folder. `update` replaces the earlier rules.
- `mcp-guide snapshot update|check` records and checks any server's tool definitions, so a change to what a tool tells the model fails the build until a person approves it.
- `mcp-server-audit` 1.1.0 and `mcp-threat-model` 1.2.0: the agent never accepts a risk on the person's behalf; the threat model is saved through the agent's file tool, so the permission prompt is the approval.

- First public version: nine lifecycle pages, coding-agent guidance, reference pages, checklists and the Ask Trevor example server. Follows the MCP specification of 2026-07-28.
