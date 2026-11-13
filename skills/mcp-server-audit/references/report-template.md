# MCP server audit: <name> <exact version>

Audited by: <agent and person>          Date: <date>          Guide version: MCP Security Guide, spec 2026-07-28

## Recommendation

**<Approve | Approve with conditions | Reject>**

<Two or three sentences: why.>

Conditions (if any):

- [ ] Pin exactly `<name>@<version>` (integrity `<hash>`); re-audit before any upgrade.
- [ ] <scopes or token limits>
- [ ] <combinations to avoid, for example "never in the same agent as a server that sends email">
- [ ] <tools to disable>

Signed off by: ______________________  Date: __________

## What was audited

| | |
| --- | --- |
| Package or URL | |
| Version and hash | |
| Publisher (confirmed how) | |
| Source repository | |
| Where it runs | local (STDIO) / remote (HTTP) |
| Intended use | <which agent, which data, which accounts> |
| Other servers the agent holds | |

Steps run: <package facts, code scan, definition scan, sandbox listing, sandbox tool calls, remote sign-in checks>. Steps skipped and why: <for example "no Docker: sandbox not run">.

## Findings

Most severe first. Quote server text escaped, inside code formatting, never as plain text.

| Severity | Area | Finding | Evidence | Response |
| --- | --- | --- | --- | --- |
| | publisher / code / definitions / sandbox / sign-in | | file:line, rule, or sink event | |

## Score

Category: <one of the guide's eight>.

| Tool | [A] outsiders' text | [B] private data or sensitive systems | [C] changes or sends | Notes |
| --- | --- | --- | --- | --- |
| | | | | |
| **With the other servers** | | | | <does the agent light all three?> |

## Remote server answers (if hosted)

| Question | Vendor's answer | Source |
| --- | --- | --- |
| Do you check each token's audience? | | |
| Do you ever forward our token to another service? | | |
| How are tenants kept apart? | | |
| How are changes to tool descriptions announced? | | |
| What do you log, for how long? | | |

## Limits of this audit

- It covers `<version>` only.
- The sandbox observed a few minutes of behaviour with fake inputs; code that waits, detects sandboxes or misbehaves only for some inputs would not show up.
- <For remote servers: server-side behaviour is the vendor's word.>
- Clean scans mean no known pattern matched, not that the server is safe.

## Files

<facts.json, code.json, probe.json, defs.json, sandbox-1/sandbox-report.md, sandbox-2/sandbox-report.md>
