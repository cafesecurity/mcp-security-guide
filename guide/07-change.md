# 7. Change

*As of 13 November 2026.* Previous: [6. Deploy and operate](06-deploy-operate.md) · Next: [8. Incident and retire](08-incident-retire.md)

Every approval of an MCP server is a snapshot. The server keeps changing: new tools, new wording, new scopes, new dependencies, new spec versions. Which changes should make clients, and the people who approved the server, look again?

## What goes wrong

- **The rug pull.** Invariant Labs [showed](https://invariantlabs.ai/blog/whatsapp-mcp-exploited) that a server can present a harmless tool description at approval time and change it later. Most clients approved a server once and never looked again. From the user's side, an unannounced description change by an honest maintainer looks exactly the same.
- **The one-line upgrade.** postmark-mcp's earlier versions behaved like Postmark's own server. Version 1.0.16 added one line that copied every email to an attacker. Anyone who upgraded without reading the diff got it.
- **The spec moved.** The 2026-07-28 revision removed protocol sessions and the initialize handshake, deprecated Dynamic Client Registration and added header validation on the HTTP transport. A server that hasn't migrated is either broken for new clients or carrying assumptions (session IDs as identity) that no longer hold.

## What to do

### Classify every change

| Change | Example | What it needs |
| --- | --- | --- |
| New tool | Adding `send_invoice` | Threat model update; human approval; version bump; release note. Clients should re-approve. |
| Tool name, description or parameter descriptions | Rewording "Search documents" | Human review of the exact text; snapshot update; version bump; release note quoting the change. Clients should re-approve. |
| Input or output schema | New optional parameter | Snapshot update; version bump; release note. Clients should re-approve. |
| Annotations | `readOnlyHint` changed to `false` | Treat as a new acting tool. |
| Scopes | New scope, or a scope's meaning changes | Threat model update; human approval; consent screen review; release note. Existing tokens keep only the old scopes. |
| Upstream system or permission | Reading a new mailbox type | Threat model update; human approval. |
| Dependency upgrade | SDK minor version | Read the changelog and diff; run the full test list; note it in the release. |
| Spec version | Moving to 2026-07-28 | Migration plan; spec checklist re-run; compatibility tests with the clients you support. |
| Internal refactor | No change to tools, scopes or behaviour | Normal review; the snapshot test proves the tool list didn't change. |

The snapshot test from [Test](04-test.md) is what makes this table enforceable: any change to what clients see fails the build until the snapshot, the version and the changelog are updated in the same pull request.

### Tell clients when tools change

- Bump the server version and say what changed in words.
- Send `notifications/tools/list_changed` to clients that subscribe to it, so they re-read the list.
- Publish the hash of the tool-definition snapshot with each release, so clients and gateways that pin definitions can compare.

### Upgrade dependencies deliberately

- Upgrade on purpose, not automatically into production: a bot can open the pull request, but a person reads the diff for anything that touches the network, the file system, processes or credentials.
- Keep the SDK current for security fixes; read its release notes for changes to defaults (DNS-rebinding protection, for example, has changed in several SDKs).

### Migrating to 2026-07-28

- Remove any use of session IDs as identity. Authenticate every request from its token.
- If you need state across requests, use handles bound to the user (see [Design](02-design.md#tenants-and-state)).
- Validate that HTTP headers match the request body.
- If you run an authorisation server, support Client ID Metadata Documents, emit `iss` in authorisation responses, and plan to retire Dynamic Client Registration.
- Re-run the [spec checklist](../reference/spec-checklist.md).

## Controls

- A change-classification rule in your contribution guide, matching the table.
- The snapshot test, failing the build on unannounced changes.
- Version bumps and release notes for every change clients can see.
- Dependency upgrades read by a person.

> ### If a coding agent is doing this
>
> The agent **must flag any change to a tool's name, description, parameters, schema or annotations** in the pull request description, quoting the old and new text. This rule is in [`AGENTS.md`](../AGENTS.md), and the snapshot test catches it if the agent forgets.
>
> Agents like to "improve" descriptions while doing something else. Small, helpful-looking rewording is still a change to every user's prompt. Reject description edits that weren't part of the task.

## Checklist

- [ ] The change-classification table (or your version of it) is in the contribution guide.
- [ ] The snapshot test fails the build on any change to tool names, descriptions, schemas or annotations.
- [ ] Every client-visible change bumps the version and is described in words in the release notes.
- [ ] New tools, new scopes and new upstream access update the threat model and need a person's approval.
- [ ] The server sends `notifications/tools/list_changed` when its tools change.
- [ ] The tool-definition hash is published with each release.
- [ ] Dependency upgrades are read by a person before they reach production.
- [ ] The server is migrated to the 2026-07-28 spec, or has a dated plan to be.
