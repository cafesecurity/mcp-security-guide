# 8. Incident and retire

*As of 13 November 2026.* Previous: [7. Change](07-change.md) · Next: [Using a coding agent safely](coding-agents.md)

What do you do on a bad day, and how do you switch a server off at the end of its life without leaving credentials and data behind?

## What goes wrong

- **No clean way to switch off.** When Asana found its cross-tenant bug on 4 June 2025, it took the MCP server offline until 17 June. That was the right call, and it was possible because the server could be removed cleanly. Many teams find out during an incident that they can't.
- **Slow detection.** At WorkOS, five days passed between the first access and detection, by which time the bulk pull had finished. Detection is covered in [Deploy and operate](06-deploy-operate.md#alerts); this page is about what happens next.
- **Credentials that outlive the server.** A retired server's OAuth client, upstream API keys, refresh tokens and registry listing keep working until someone revokes them.

## What to do

### The bad-day runbook

Write this before you need it, keep it next to the code, and rehearse it once.

**1. Contain (minutes)**

- Use the kill switch: block the affected client, user or tool, or take the server offline.
- Revoke access tokens and refresh tokens issued for the server. If you can't revoke selectively, revoke them all.
- Rotate the server's own upstream credentials and signing keys if there's any chance they were exposed.
- If a release is suspected, deprecate the affected package versions and pull the release.

**2. Assess (hours)**

- From the tool-call logs: which users, tenants, clients and tools; what arguments; how much data was returned; over what period.
- From upstream logs: what the server's own credentials did.
- Decide whether personal data was involved and whether notification duties apply. Bring in your legal and data protection people early.

**3. Tell (as soon as you know enough)**

- Affected customers or users: what happened, what data, what you've done, what they should do.
- Clients and agent owners who connected the server: which versions or tools to stop using.
- The registry and package host, if a release or a lookalike is involved.
- Say what you don't know yet. Update when you do.

**4. Fix and return**

- Fix the cause, add a test that would have caught it, and update the threat model.
- Return in stages: one tenant or a small group first, with closer monitoring.
- Publish a short post-incident note: timeline, cause, fix.

### Retiring a server

| Step | Why |
| --- | --- |
| Announce a date; mark the registry entry and package as deprecated | Users and clients can move before it stops |
| Remove the server from your internal registry and agent allow-lists | Approved agents stop trying to connect |
| Delete or disable its OAuth client registration and revoke all tokens issued for it | Nothing can get a token for it afterwards |
| Revoke the server's own upstream credentials, service accounts and API keys | The usual leftover |
| Remove DNS records and the hosted endpoint | Nobody can stand up a lookalike at your old address |
| Delete caches, indexes and logs past their retention period | No stray copies of user data |
| Keep the registry name and package name reserved | Nobody else can claim them |
| Archive the threat model and runbook with the final version | Someone will ask later |

## Controls

- A written runbook, with named owners, rehearsed at least once.
- A kill switch and token revocation that work without a deploy.
- A retirement checklist that ends with credentials revoked and names kept.

> ### If a coding agent is doing this
>
> Include the coding agent in the revocation list. During an incident, revoke any tokens, API keys or sessions the agent used while working on the server, and check its configuration for MCP servers and credentials that shouldn't be there.
>
> An agent can help with the assessment (summarising logs, building a timeline), but a person makes the containment and notification decisions.

## Checklist

- [ ] A runbook covers contain, assess, tell, and fix and return, with named owners.
- [ ] The runbook has been rehearsed at least once.
- [ ] Tokens issued for the server can be revoked in bulk, and the server's own credentials can be rotated quickly.
- [ ] Logs are good enough to say which users, tenants, clients and tools were involved.
- [ ] Contacts for legal, data protection and the registry or package host are in the runbook.
- [ ] Retirement steps cover deprecation, allow-lists, OAuth clients, tokens, upstream credentials, DNS, data and name reservation.
- [ ] Coding-agent sessions and tokens are in the revocation list.
