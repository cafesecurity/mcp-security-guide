# 6. Deploy and operate

*As of 13 November 2026.* Previous: [5. Release](05-release.md) · Next: [7. Change](07-change.md)

Where does the server run, what can it reach from there, and how will you notice when something is wrong? A server that is well built but deployed with an open network path and no logs will still become a case study.

## What goes wrong

This page's main lesson comes from an incident that didn't involve MCP at all, because its gaps are the ones an MCP server can have.

- **WorkOS, October 2026.** A security researcher's autonomous penetration-testing agent escaped its test environment and, by the researcher's account unintentionally, reached an internal WorkOS sales tool. WorkOS's [update of 6 November](https://workos.com/security/bulletins/update-for-october-30th-2026-data-security-incident) names four gaps: the tool's API was reachable from the internet; a predictable development credential was accepted in production; there was no rate limit; and the first access, on 25 October, wasn't noticed until 30 October, after the agent had pulled records in bulk. WorkOS cut access the same day it noticed, and now tests its internet-facing systems with the same agent.
- **MCP Inspector, 2025.** The debugging tool listened on every interface with no authentication. A local tool that is reachable from the network is a remote tool.
- **Asana, 2025.** When the cross-tenant bug was found, Asana took the MCP server offline for nearly two weeks. That only works if you can switch the server off quickly and cleanly.

## What to do

### Where it runs

**Remote servers**

- Run behind a gateway or reverse proxy that terminates TLS, enforces request size limits and can block a client or a tool without a redeploy.
- Expose only the MCP endpoint and the protected resource metadata. Admin, debug and health endpoints stay on an internal network.
- Restrict outbound traffic to the upstream systems the server needs (an egress allow-list). A server that can reach anything can be made to fetch anything.
- Run as a non-root user, in a container or sandbox with a read-only file system where possible.

**Local servers**

- Prefer STDIO, so only the launching client can talk to the server.
- If you ship a local HTTP server, bind it to 127.0.0.1, validate `Origin`, and require a token.
- Document a sandboxed way to run it (a container, or the client's own sandbox), with the folders and network access it needs and nothing more.

### Credentials

- Keep secrets in a vault or the platform's secret store, injected at start-up.
- Use short-lived credentials for upstream systems, and a separate set per environment. A development credential that works in production is exactly WorkOS's second gap.
- Never put production credentials on developer machines or in CI jobs that run untrusted code.

### Rate limits and caps

- Limit requests per user and per client, and cap results per call.
- Put a separate, lower limit on bulk-shaped calls (wide searches, exports, list-everything tools).
- For acting tools, hourly and daily caps per connection (see [Design](02-design.md#reads-and-writes)).

### Logs

Log every tool call as a structured event. Record who did what, not what they saw.

| Field | Example | Why |
| --- | --- | --- |
| time | `2026-11-13T10:42:07Z` | Timeline |
| user | token `sub` | Who |
| tenant | from the token | Whose data |
| client | client ID from the token | Which agent; spots unapproved clients |
| tool | `search_docs` | What |
| arguments | `{"query":"supplier contract","limit":10}`, with sensitive values masked | What was asked |
| result size | `7 results, 6.2 kB` | Spots bulk extraction |
| outcome | `ok`, `denied`, `error` | Spots probing |
| request ID | per request | Correlate with upstream logs |
| token ID | `jti` | Revoke the right token |

Don't log access tokens, document bodies, email content or personal data beyond what's needed to investigate. Send the events to your SIEM, and keep them tamper-evident.

### Alerts

Start with these and tune them:

- One user or client suddenly reading far more than its usual volume.
- Many `denied` or `not found` results in a short time (someone probing IDs or tenants).
- A client ID that isn't on your approved list getting tokens (internal servers).
- Calls from unusual networks or at unusual times for that user.
- Any change in the tool list the server returns, outside a release.
- Rate limits being hit repeatedly.

The UK's NCSC [notes](https://www.ncsc.gov.uk/blogs/why-cyber-defenders-need-to-be-ready-for-frontier-ai) that AI-driven attacks have so far tended to set off alarms. That helps only if someone is watching them.

### A kill switch

Be able to, within minutes and without a deploy:

- block one client, one user or one tool;
- revoke every token issued for the server;
- take the whole server offline.

Write these steps down in the runbook (see [Incident and retire](08-incident-retire.md)) and rehearse them.

### Test yourself

Point an automated scanner, or an AI testing agent you control, at your own internet-facing surface on a schedule, scoped to your own systems. If an agent wandering the internet would find a door, you want to find it first.

## Controls

- Only the MCP endpoint and metadata exposed; egress allow-listed; non-root, sandboxed.
- Per-environment, short-lived credentials from a vault.
- Rate limits, result caps and bulk limits.
- Structured tool-call logs in the SIEM, with masking.
- Alerts on volume, probing, unknown clients and tool-list changes.
- A tested kill switch.

For the organisation-wide controls around which agents may connect, see [For security leads](../reference/for-security-leads.md).

> ### If a coding agent is doing this
>
> Infrastructure changes written by an agent go through the same review as any other change: network rules, gateway configuration, IAM policies and secrets handling especially. A one-word change from `127.0.0.1` to `0.0.0.0`, or a wildcard in a security group, is easy to miss in a large diff.
>
> **No production credentials on the machine the agent runs on**, and no standing access from the agent's environment to production. If the agent needs to test against a deployed server, give it a separate environment with its own data and credentials.

## Checklist

- [ ] Only the MCP endpoint and protected resource metadata are reachable from outside; admin and debug endpoints are internal.
- [ ] Outbound traffic is restricted to named upstream systems.
- [ ] The server runs as non-root, in a container or sandbox.
- [ ] Local HTTP servers bind to 127.0.0.1, validate `Origin` and require a token; STDIO is preferred.
- [ ] Secrets come from a vault; credentials are short-lived and separate per environment; development credentials fail in production.
- [ ] Rate limits, result caps and lower limits for bulk-shaped calls are in place.
- [ ] Every tool call is logged with the fields above, with sensitive values masked, and sent to the SIEM.
- [ ] Alerts exist for volume spikes, probing, unknown clients and tool-list changes, and someone receives them.
- [ ] The kill switch can block a client, user or tool, revoke all tokens and take the server offline, and has been rehearsed.
- [ ] The internet-facing surface is scanned on a schedule.
- [ ] No production credentials are reachable from where a coding agent runs.
