# 2. Design

*As of 13 November 2026.* Previous: [1. Threat model](01-threat-model.md) · Next: [3. Build](03-build.md)

Whose identity does the server use, which tokens does it accept, which scopes does it ask for, which tools read and which act, and how are tenants kept apart? These decisions are hard to change later, and most real incidents trace back to one of them.

The requirement levels quoted here come from the [spec checklist](../reference/spec-checklist.md).

## What to decide

### Whose identity does the server use?

| Model | How it works | Verdict |
| --- | --- | --- |
| Per-user delegated access | Each user signs in. The server gets a token that acts only as that user, and the upstream system checks access on every request. | **Recommended.** The agent sees only what that user can already see. |
| Service account with organisation-wide rights | One credential reads every mailbox, every repository or every record. | **Avoid.** Every user, and every successful prompt injection, gets the master key. |
| Pre-built search index | Content is copied into a store along with its access rules. | **Use with care.** Copied access rules go stale: someone removed from a folder last week may still find its contents. Check access again at query time. |

Two concrete traps:

- **Google Workspace.** Prefer the user granting your server read access through the normal consent screen. Domain-wide delegation lets a service account read every user's data without asking anyone; review existing grants under *Security > Access and data control > API controls > Manage Domain Wide Delegation*.
- **Microsoft 365.** The delegated permission `Mail.Read` reaches only the signed-in user's mail. The application permission with the same name reads every mailbox in the tenant. Check which one is on your app registration.

### Which tokens does the server accept?

A remote MCP server is an OAuth 2.1 resource server. Three rules matter most:

1. **Check the audience.** Servers MUST validate that each token was issued for them. Sending the `resource` parameter is the client's job, but it only binds the token if the authorisation server honours it. Your own audience check is what protects you.
2. **Never pass tokens through.** Servers MUST NOT forward the client's token to an upstream API. If you need to call one, get a separate token for it: Microsoft Entra's on-behalf-of flow, OAuth token exchange (RFC 8693) where your identity provider supports it, or a separate consent the user grants to your server.
3. **Keep tokens short-lived and narrow.** A token that lasts an hour and can only search is a small prize. A refresh token with every scope is a large one.

```ts
// never: the client's token, forwarded upstream
await fetch(MAIL_API, { headers: { Authorization: `Bearer ${clientToken}` } });

// instead: a new token, for the mail API, for this user
const mailToken = await exchangeOnBehalfOf(clientToken, { scope: "Mail.Read" });
await fetch(MAIL_API, { headers: { Authorization: `Bearer ${mailToken}` } });
```

### Which scopes?

Start small and step up. The spec's [Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices#scope-minimization) page recommends a minimal initial scope set for low-risk reads, with more requested through a `403 insufficient_scope` challenge when a privileged tool is first used.

- Keep `scopes_supported` to the minimal set needed for basic use. Clients fall back to requesting all of it if your 401 has no `scope`.
- Name the scopes each request needs in the `WWW-Authenticate` challenge, all at once.
- Separate scopes for reading, drafting, sending and anything that moves money.
- Avoid wildcard scopes (`*`, `all`, `full-access`), and don't change what a scope means without versioning it.

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope",
  scope="invoices:send",
  resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"
```

### Which agents may connect?

For an internal server, decide which clients may get a token at all. A perfectly built server still leaks if an employee connects it to an unmanaged agent with a shell and a chat channel: the token is valid and the user is right, but you can't see who is driving.

- If your authorisation server accepts Client ID Metadata Documents, the client ID is a URL. The spec lets the authorisation server apply trust policies, including an allow-list of approved client URLs.
- In Google Workspace and Microsoft 365, restrict which third-party apps users can authorise (see [For security leads](../reference/for-security-leads.md#controlling-the-agents-staff-connect)).

Approving apps is the strongest control an administrator has, not a guarantee: desktop clients can't keep a secret, so a client ID can sometimes be borrowed. Fixed redirect addresses narrow that.

### Reads and writes

- Put read tools and acting tools in **separate tools**, and preferably separate servers. A read-only server can be approved for far more agents.
- Anything that writes, sends, pays or deletes needs a **person's approval of the actual action**: the real message and recipients, the real amount and payee. Not a summary, and not a "yes" typed into the chat, because the model is in the chat. The spec's URL mode elicitation sends the user to a page on your own site to confirm, outside the agent's reach.
- Add the limits a bank would: per-connection caps per hour and per day, alerts on unusual volume, and an idempotency key on every write so a retry doesn't act twice.
- Mark acting tools with `destructiveHint: true` and read tools with `readOnlyHint: true`, so well-behaved clients ask before running them. Don't rely on these: annotations are hints, and clients are told not to trust them from servers they don't trust.

### Tool descriptions

Every description is text the model reads and may obey, in every user's session. Treat it as part of the prompt.

- Write plain documentation: what the tool does, its parameters, what it returns, and any limits.
- Never address the model ("you must", "always call this first", "ignore").
- Never mention other servers or their tools.
- No hidden text, invisible Unicode, HTML comments or long default values.
- Keep parameter names and defaults boring: they reach the model too.
- Freeze descriptions in a snapshot file, so any change is visible in review (see [Change](07-change.md)).

### Results

- **Tag every result with its source.** Mark content written by outsiders (external email senders, guests, customers' customers) as external, so clients and models can treat it as data.
- **Return plain text.** Strip hidden text, invisible characters and terminal escape codes.
- **Don't return links or images that a client might load automatically.** Loading a URL is a way to send data out.
- **Cap results** per call, and refuse bulk requests that look like extraction.
- **Never return secrets** (tokens, keys, connection strings) in a result.

### Tenants and state

- Take the tenant and the user from the **verified token**, never from the request or a tool argument.
- Put them in **every query** and **every cache key**.
- If the server keeps state between requests (a cart, a workflow), the 2026-07-28 spec has no sessions: you mint a handle and get it back as an argument. Generate handles from a secure random source, store state under `<user_id>:<handle>` with the user from the token, and never treat holding a handle as proof of identity.

### If your server fronts a third-party API

If your server signs in to someone else's API with one static client ID for all users, the spec's confused-deputy rules apply in full: keep a per-user list of approved client IDs, show your own consent page for each new client (naming it, its scopes and its redirect URI), match redirect URIs exactly, and set a single-use `state` only after consent. See [spec checklist section 5](../reference/spec-checklist.md#5-proxies-and-consent).

## A server for customers

An internal server like Ask Trevor can rely on an approved-agent list. A server for customers can't, because customers bring their own agents. Take the invoicing example from the second video, Quidsworth (invented; addresses use the reserved `.example` domain), with four tools: list invoices, create a draft, send an invoice, issue a refund. Three things change:

1. **Consent and scopes do the job the approved list did.** Every new agent meets your own consent screen, which shows the agent's web address as well as its name (anyone can call their agent "Finance Helper") and exactly what it asks for. Reading is the default; sending and refunds are asked for separately, by step-up. Each customer gets a page listing connected agents, with a button to disconnect each.
2. **Tenant isolation is entirely your job.** You are the system of record. The tenant comes from the token, goes into every query and cache key, and the isolation test runs on every build. Memo fields, customer names and payment references are written by your customers' customers, so they go back as plain text, tagged external.
3. **Writes cost money.** Drafts are free. Sending and refunds are confirmed by a person on your own page, with a second factor for refunds, within hourly and daily caps, with idempotency keys.

## What goes wrong

- **Static client ID, no per-client consent.** Obsidian Security found remote MCP servers, including Square's, that logged in to the upstream platform with one shared client ID, let anyone register a new client with any redirect, and relied on the platform's remembered consent. One click on a crafted link could hand an attacker an authorisation code. Fixed in September 2025 ([write-up](https://www.obsidiansecurity.com/blog/when-mcp-meets-oauth-common-pitfalls-leading-to-one-click-account-takeover)).
- **Ownership not checked.** Asana's MCP server had a logic flaw from launch that let some users see other organisations' projects, tasks and comments. About 1,000 customers were affected and the server was offline from 4 to 17 June 2025 ([BleepingComputer](https://www.bleepingcomputer.com/news/security/asana-warns-mcp-ai-feature-exposed-customer-data-to-other-orgs/)).
- **Master keys.** The Supabase demonstration used a key that bypasses row-level security; Supabase now recommends read-only mode, scoped to one project.
- **Account-wide tokens.** The GitHub toxic-flow demonstration needed nothing more than a token that covered every repository.

## Controls

The decisions above are the controls. In short: per-user identity, audience checks, no passthrough, minimal scopes with step-up, an approved-client list for internal servers and per-client consent for public ones, reads and writes separated with real approval for writes, descriptions written as documentation, results tagged and plain, tenant from the token everywhere.

> ### If a coding agent is doing this
>
> These are **human-owned decisions**: the identity model, which tokens are accepted, scopes, approval for writes, and the wording of every tool description. Make them yourself and give them to the agent as fixed requirements.
>
> Don't let an agent invent an authentication scheme. Agents produce plausible OAuth code that skips the audience check, accepts tokens from any issuer, or forwards the client's token upstream because that is the shortest path to a working demo. Point it at the [spec checklist](../reference/spec-checklist.md) and the [example server](../examples/ask-trevor/), and review every line of token handling yourself.

## Checklist

- [ ] The identity model is per-user delegated access, or the threat model explains why not.
- [ ] No service account with organisation-wide rights sits behind the server.
- [ ] The server checks every token's audience, issuer, expiry and scopes.
- [ ] The server never forwards a client's token upstream; upstream calls use a separate token.
- [ ] `scopes_supported` is minimal; privileged tools need a step-up scope; no wildcard scopes.
- [ ] For internal servers: only approved clients can get a token. For public servers: per-client consent, showing the client's URL, with a page to disconnect.
- [ ] If the server fronts a third-party API with a static client ID: per-client consent, exact redirect matching and single-use `state` set after consent.
- [ ] Read and acting tools are separate; every acting tool needs a person's approval of the actual action, outside the chat.
- [ ] Acting tools have caps, volume alerts and idempotency keys.
- [ ] Tool descriptions are plain documentation and are frozen in a snapshot file.
- [ ] Results are plain text, tagged by source, capped, and never include secrets or auto-loading links.
- [ ] Tenant and user come from the token and appear in every query and cache key.
- [ ] Any state handles are random, expiring and bound to the user from the token.
